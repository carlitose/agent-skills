from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "ticket-autopilot" / "scripts" / "ticket-autopilot.py"
sys.path.insert(0, str(CLI.parent))

from autopilot.kernel import CandidateRef, Kernel
from autopilot.ledger import AtomicLedger
from autopilot.legacy_recovery import RetirementStore
from autopilot.status_transaction import (
    OwnerResolution,
    StatusChangeRequest,
    StatusTransactionError,
    _gate_for_owner,
    execute_status_transaction,
)
from autopilot.ticket_contract import parse_ticket_folder, ticket_source_digest


def git(repo: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=repo,
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout.strip()


def ticket_text(ticket_id: str, artifact_id: str) -> str:
    return (
        "---\n"
        "ticket_schema: 1\n"
        f'ticket_id: "{ticket_id}"\n'
        "execution_mode: AFK\n"
        "blocked_by: []\n"
        "---\n\n"
        f"# Ticket {ticket_id}\n\n"
        "## Artifact Graph\n\n"
        f"- Artifact ID: `{artifact_id}`\n"
        "- Role: `ticket`\n\n"
        "## What to Build\n\nFixture only.\n"
    )


def canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def write_envelope(path: Path, payload: dict[str, object]) -> None:
    body = canonical(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        canonical(
            {
                "envelope_schema": 1,
                "integrity": hashlib.sha256(body).hexdigest(),
                "payload": payload,
            }
        )
        + b"\n"
    )


class Crash(RuntimeError):
    pass


class StatusTransactionTests(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.repo = Path(directory.name) / "repo"
        self.repo.mkdir()
        self.repo = self.repo.resolve()
        git(self.repo, "init", "-b", "main")
        git(self.repo, "config", "user.name", "Status Tests")
        git(self.repo, "config", "user.email", "status@example.invalid")
        (self.repo / "README.md").write_text("fixture\n", encoding="utf-8")
        git(self.repo, "add", "README.md")
        git(self.repo, "commit", "-m", "baseline")
        self.ticket_id = "ST-01"
        self.artifact_id = "artifact:status-transaction-fixture"

    def make_ticket(self, *, tracked: bool) -> Path:
        folder = self.repo / "tickets"
        folder.mkdir(exist_ok=True)
        source = folder / "01.md"
        source.write_text(
            ticket_text(self.ticket_id, self.artifact_id), encoding="utf-8"
        )
        if tracked:
            git(self.repo, "add", "tickets/01.md")
            git(self.repo, "commit", "-m", "tracked ticket")
        else:
            (self.repo / ".gitignore").write_text("tickets/\n", encoding="utf-8")
            git(self.repo, "add", ".gitignore")
            git(self.repo, "commit", "-m", "ignore ticket source")
        return source

    def request(
        self,
        source: Path,
        *,
        source_mode: str,
        prior: str = "open",
        target: str = "canceled",
        actor: str = "user:alice",
        reason: str = "remove obsolete fixture",
        authority: str = "decision:status-fixture",
        gate: str | None = None,
    ) -> StatusChangeRequest:
        return StatusChangeRequest(
            ticket_source=source,
            ticket_id=self.ticket_id,
            artifact_id=self.artifact_id,
            ticket_digest=ticket_source_digest(source),
            from_disposition=prior,
            to_disposition=target,
            source_mode=source_mode,
            actor=actor,
            reason=reason,
            authority_ref=authority,
            reopen_gate_id=gate,
        )

    def save_run(
        self,
        source: Path,
        run_id: str,
        *,
        source_mode: str = "ignored",
        active: bool = False,
    ) -> Path:
        kernel = Kernel.new(
            run_id,
            parse_ticket_folder(source.parent),
            repo=str(self.repo.resolve()),
            worktree=str(self.repo.resolve()),
            source_mode=source_mode,
            base_sha=git(self.repo, "rev-parse", "HEAD"),
        )
        if active:
            digest = kernel.ledger["tickets"][self.ticket_id]["ticket_digest"]
            kernel.activate(
                self.ticket_id,
                CandidateRef("base-fixture", "tree-fixture", digest, 2),
            )
        ledger = (
            self.repo
            / ".git"
            / "ticket-autopilot"
            / "runs"
            / run_id
            / "ledger.json"
        )
        store = AtomicLedger(ledger)
        with store.run_locked():
            store.save(kernel.ledger)
        return ledger.resolve()

    def test_pending_ignored_cancel_is_external_unpublished_and_replays(self) -> None:
        source = self.make_ticket(tracked=False)
        request = self.request(source, source_mode="ignored")

        result = execute_status_transaction(self.repo, request)

        self.assertEqual(result["status"], "external-unpublished")
        self.assertEqual(result["owner"]["transaction_owner"], "repository-lifecycle")
        self.assertIsNone(result["owner"]["projection_run_id"])
        self.assertFalse(source.exists())
        destination = self.repo / "tickets" / "canceled" / "01.md"
        self.assertTrue(destination.is_file())
        self.assertEqual(ticket_source_digest(destination), request.ticket_digest)
        self.assertIn("merge", result["non_authorities"])
        self.assertEqual(git(self.repo, "status", "--porcelain"), "")

        replay = execute_status_transaction(self.repo, request)
        self.assertEqual(replay["transaction_id"], result["transaction_id"])
        self.assertEqual(replay["status"], "already-applied")
        self.assertTrue(replay["replayed"])

    def test_pending_ignored_projects_to_one_run_without_owning_transaction(self) -> None:
        source = self.make_ticket(tracked=False)
        ledger = self.save_run(source, "projection-run")
        request = self.request(
            source,
            source_mode="ignored",
            target="on-hold",
            reason="wait for a decision",
        )

        result = execute_status_transaction(self.repo, request)

        self.assertEqual(result["status"], "external-unpublished")
        self.assertEqual(result["owner"]["projection_run_id"], "projection-run")
        store = AtomicLedger(ledger)
        with store.run_locked():
            document = store.load()
        ticket = document["tickets"][self.ticket_id]
        self.assertEqual(ticket["disposition"], "on-hold")
        self.assertEqual(ticket["state"], "pending")
        self.assertEqual(ticket["current_source_relative_path"], "hold/01.md")
        replay = execute_status_transaction(self.repo, request)
        self.assertEqual(replay["status"], "already-applied")
        ledger.unlink()
        with self.assertRaisesRegex(StatusTransactionError, "readback"):
            execute_status_transaction(self.repo, request)

    def test_crashes_before_and_after_move_resume_exactly(self) -> None:
        source = self.make_ticket(tracked=False)
        request = self.request(source, source_mode="ignored")

        with self.assertRaises(Crash):
            execute_status_transaction(
                self.repo,
                request,
                checkpoint=lambda phase: (_ for _ in ()).throw(Crash(phase))
                if phase == "before-intent"
                else None,
            )
        transaction_root = (
            self.repo / ".git" / "ticket-autopilot" / "status-transactions"
        )
        self.assertEqual(list(transaction_root.glob("*.json")), [])
        self.assertTrue(source.is_file())

        with self.assertRaises(Crash):
            execute_status_transaction(
                self.repo,
                request,
                checkpoint=lambda phase: (_ for _ in ()).throw(Crash(phase))
                if phase == "lifecycle-intent"
                else None,
            )
        self.assertTrue(source.is_file())
        resumed = execute_status_transaction(self.repo, request)
        self.assertEqual(resumed["status"], "external-unpublished")

        second_source = self.repo / "tickets" / "02.md"
        second_source.write_text(
            ticket_text("ST-02", "artifact:status-transaction-fixture-2"),
            encoding="utf-8",
        )
        second_request = StatusChangeRequest(
            ticket_source=second_source,
            ticket_id="ST-02",
            artifact_id="artifact:status-transaction-fixture-2",
            ticket_digest=ticket_source_digest(second_source),
            from_disposition="open",
            to_disposition="canceled",
            source_mode="ignored",
            actor="user:alice",
            reason="remove second fixture",
            authority_ref="decision:status-fixture-2",
        )
        with self.assertRaises(Crash):
            execute_status_transaction(
                self.repo,
                second_request,
                checkpoint=lambda phase: (_ for _ in ()).throw(Crash(phase))
                if phase == "source-effect-applied"
                else None,
            )
        self.assertFalse(second_source.exists())
        recovered = execute_status_transaction(self.repo, second_request)
        self.assertEqual(recovered["status"], "external-unpublished")
        self.assertTrue(
            (self.repo / "tickets" / "canceled" / "02.md").is_file()
        )

    def test_owner_activation_after_intent_becomes_a_gate_before_source_effect(self) -> None:
        source = self.make_ticket(tracked=False)
        ledger = self.save_run(source, "activation-race")
        request = self.request(source, source_mode="ignored", target="on-hold")

        def activate_after_intent(phase: str) -> None:
            if phase != "lifecycle-intent":
                return
            store = AtomicLedger(ledger)
            with store.run_locked():
                kernel = Kernel(store.load())
                digest = kernel.ledger["tickets"][self.ticket_id]["ticket_digest"]
                kernel.activate(
                    self.ticket_id,
                    CandidateRef("race-base", "race-tree", digest, 2),
                )
                store.save(kernel.ledger)

        result = execute_status_transaction(
            self.repo, request, checkpoint=activate_after_intent
        )

        self.assertEqual(result["status"], "gated")
        self.assertEqual(result["gate"], "safe-boundary-projection-unavailable")
        self.assertTrue(source.is_file())
        self.assertFalse((self.repo / "tickets" / "hold" / "01.md").exists())

    def test_crash_after_projected_source_effect_replays_run_receipt(self) -> None:
        source = self.make_ticket(tracked=False)
        ledger = self.save_run(source, "projected-crash")
        request = self.request(source, source_mode="ignored", target="on-hold")

        with self.assertRaises(Crash):
            execute_status_transaction(
                self.repo,
                request,
                checkpoint=lambda phase: (_ for _ in ()).throw(Crash(phase))
                if phase == "source-effect-applied"
                else None,
            )
        recovered = execute_status_transaction(self.repo, request)
        self.assertEqual(recovered["status"], "external-unpublished")
        store = AtomicLedger(ledger)
        with store.run_locked():
            ticket = store.load()["tickets"][self.ticket_id]
        self.assertEqual(ticket["disposition"], "on-hold")

    def test_tracked_source_stops_at_clean_handoff(self) -> None:
        source = self.make_ticket(tracked=True)
        request = self.request(source, source_mode="tracked", target="on-hold")
        before = git(self.repo, "rev-parse", "HEAD")
        dirty_bytes = b"pre-existing unrelated worktree state\r\n"
        (self.repo / "README.md").write_bytes(dirty_bytes)
        dirty_status = git(self.repo, "status", "--porcelain")

        result = execute_status_transaction(self.repo, request)

        self.assertEqual(result["status"], "tracked-handoff")
        self.assertEqual(result["phase"], "tracked-handoff")
        self.assertTrue(source.is_file())
        self.assertEqual(git(self.repo, "rev-parse", "HEAD"), before)
        self.assertEqual((self.repo / "README.md").read_bytes(), dirty_bytes)
        self.assertEqual(git(self.repo, "status", "--porcelain"), dirty_status)
        self.assertIsNone(result["source_receipt"])
        source.write_text(source.read_text(encoding="utf-8") + "drift\n", encoding="utf-8")
        with self.assertRaisesRegex(StatusTransactionError, "drift"):
            execute_status_transaction(self.repo, request)

    def test_active_and_ambiguous_owners_return_named_gates_without_mutation(self) -> None:
        source = self.make_ticket(tracked=False)
        self.save_run(source, "active-owner", active=True)
        request = self.request(source, source_mode="ignored", target="on-hold")

        active = execute_status_transaction(self.repo, request)
        self.assertEqual(active["status"], "gated")
        self.assertEqual(active["gate"], "safe-boundary-projection-unavailable")
        self.assertEqual(active["owner"]["execution_lifecycle"], "running")
        self.assertEqual(active["owner"]["readiness"], "not-schedulable")
        self.assertIsNone(active["owner"]["stop_reason"])
        self.assertTrue(source.is_file())

        other = self.repo / "tickets" / "02.md"
        other.write_text(
            ticket_text("ST-02", "artifact:status-transaction-fixture-2"),
            encoding="utf-8",
        )
        self.ticket_id = "ST-02"
        self.artifact_id = "artifact:status-transaction-fixture-2"
        self.save_run(other, "owner-a")
        self.save_run(other, "owner-b")
        ambiguous_request = self.request(
            other, source_mode="ignored", target="on-hold"
        )
        ambiguous = execute_status_transaction(self.repo, ambiguous_request)
        self.assertEqual(ambiguous["status"], "gated")
        self.assertEqual(ambiguous["gate"], "ambiguous-run-ownership")
        self.assertEqual(
            ambiguous["owner"]["ambiguous_run_ids"], ["owner-a", "owner-b"]
        )
        replay = execute_status_transaction(self.repo, ambiguous_request)
        self.assertEqual(replay["transaction_id"], ambiguous["transaction_id"])
        self.assertEqual(replay["owner"], ambiguous["owner"])
        self.assertTrue(other.is_file())

    def test_execution_states_have_stable_safe_boundary_gates(self) -> None:
        for state in ("active", "gated", "waiting"):
            with self.subTest(state=state):
                owner = OwnerResolution("run", Path("ledger"), state, ())
                self.assertEqual(
                    _gate_for_owner(owner, "canceled"),
                    "safe-boundary-projection-unavailable",
                )
        for state in ("pr-open", "verified", "integrated", "in-flight-atomic"):
            with self.subTest(state=state):
                owner = OwnerResolution("run", Path("ledger"), state, ())
                self.assertEqual(
                    _gate_for_owner(owner, "on-hold"),
                    f"execution-state-unsupported:{state}",
                )

    def test_owner_source_contradiction_fails_before_the_source_effect(self) -> None:
        source = self.make_ticket(tracked=False)
        self.save_run(source, "contradictory-owner", source_mode="tracked")
        request = self.request(source, source_mode="ignored", target="on-hold")

        result = execute_status_transaction(self.repo, request)

        self.assertEqual(result["status"], "gated")
        self.assertEqual(result["gate"], "run-source-drift")
        self.assertTrue(source.is_file())
        self.assertFalse((self.repo / "tickets" / "hold" / "01.md").exists())

    def test_owner_digest_contradiction_is_a_named_gate(self) -> None:
        source = self.make_ticket(tracked=False)
        self.save_run(source, "stale-digest-owner")
        source.write_text(
            source.read_text(encoding="utf-8") + "\nAuthorized fixture revision.\n",
            encoding="utf-8",
        )
        request = self.request(source, source_mode="ignored", target="on-hold")

        result = execute_status_transaction(self.repo, request)

        self.assertEqual(result["status"], "gated")
        self.assertEqual(result["gate"], "run-source-drift")
        self.assertEqual(
            result["owner"]["conflicting_run_ids"], ["stale-digest-owner"]
        )
        self.assertTrue(source.is_file())
        self.assertFalse((self.repo / "tickets" / "hold" / "01.md").exists())

    def test_retired_owner_proceeds_without_projection(self) -> None:
        source = self.make_ticket(tracked=False)
        ledger = self.save_run(source, "retired-owner")
        ledger_store = AtomicLedger(ledger)
        with ledger_store.run_locked():
            legacy = ledger_store.load()
        legacy["schema"] = 2
        write_envelope(ledger, legacy)
        binding = {
            "repository_identity": str(self.repo.resolve()),
            "git_common_dir": str((self.repo / ".git").resolve()),
        }
        RetirementStore(ledger, binding).retire(
            ledger_sha256=hashlib.sha256(ledger.read_bytes()).hexdigest(),
            ledger_schema=2,
            actor="user:retirement-admin",
            evidence="decision:retire-fixture-owner",
            reason="fixture run is retired",
            successor_run_id=None,
            manifest_digest="b" * 64,
            action_sequence=1,
        )

        result = execute_status_transaction(
            self.repo, self.request(source, source_mode="ignored")
        )

        self.assertEqual(result["status"], "external-unpublished")
        self.assertIsNone(result["owner"]["projection_run_id"])
        self.assertEqual(result["owner"]["retired_run_ids"], ["retired-owner"])

    def test_reopen_consumes_exact_passed_gate_and_rejects_drift(self) -> None:
        source = self.make_ticket(tracked=False)
        ledger = self.save_run(source, "reopen-owner")
        hold = self.request(
            source,
            source_mode="ignored",
            target="on-hold",
            reason="wait for review",
        )
        execute_status_transaction(self.repo, hold)
        held = self.repo / "tickets" / "hold" / "01.md"

        store = AtomicLedger(ledger)
        with store.run_locked():
            kernel = Kernel(store.load())
            gate = kernel.request_reopen(
                self.ticket_id,
                requested_by="agent:planner",
                reason="review completed",
            )
            kernel.approve_gate(
                gate,
                actor="user:bob",
                evidence="decision:resume-fixture",
            )
            store.save(kernel.ledger)
        digest = ticket_source_digest(held)
        drifted = StatusChangeRequest(
            ticket_source=held,
            ticket_id=self.ticket_id,
            artifact_id=self.artifact_id,
            ticket_digest=digest,
            from_disposition="on-hold",
            to_disposition="open",
            source_mode="ignored",
            actor="user:bob",
            reason="different reason",
            authority_ref="decision:resume-fixture",
            reopen_gate_id=gate,
        )
        with self.assertRaisesRegex(StatusTransactionError, "differs"):
            execute_status_transaction(self.repo, drifted)
        self.assertTrue(held.is_file())

        exact = StatusChangeRequest(
            ticket_source=held,
            ticket_id=self.ticket_id,
            artifact_id=self.artifact_id,
            ticket_digest=digest,
            from_disposition="on-hold",
            to_disposition="open",
            source_mode="ignored",
            actor="user:bob",
            reason="review completed",
            authority_ref="decision:resume-fixture",
            reopen_gate_id=gate,
        )
        result = execute_status_transaction(self.repo, exact)
        self.assertEqual(result["status"], "external-unpublished")
        self.assertTrue(source.is_file())

    def test_duplicate_short_or_artifact_identity_rejects_before_intent(self) -> None:
        source = self.make_ticket(tracked=False)
        duplicate = self.repo / "tickets" / "02.md"
        duplicate.write_text(
            ticket_text(self.ticket_id, "artifact:other-ticket"), encoding="utf-8"
        )
        request = self.request(source, source_mode="ignored")

        with self.assertRaisesRegex(StatusTransactionError, "not globally unique"):
            execute_status_transaction(self.repo, request)

        duplicate.write_text(
            ticket_text("ST-02", self.artifact_id), encoding="utf-8"
        )
        with self.assertRaisesRegex(StatusTransactionError, "Artifact ID"):
            execute_status_transaction(self.repo, request)
        journals = (
            self.repo / ".git" / "ticket-autopilot" / "status-transactions"
        ).glob("*.json")
        self.assertEqual(list(journals), [])
        self.assertTrue(source.is_file())

    def test_invalid_vocabulary_completed_and_unpublished_source_fail_before_journal(self) -> None:
        source = self.make_ticket(tracked=False)
        valid = self.request(source, source_mode="ignored")
        for target in ("completed", "blocked", "paused", "waiting", "active"):
            with self.subTest(target=target):
                invalid = StatusChangeRequest(
                    **{**valid.__dict__, "to_disposition": target}
                )
                with self.assertRaises(StatusTransactionError):
                    execute_status_transaction(self.repo, invalid)
        completed = StatusChangeRequest(
            **{**valid.__dict__, "from_disposition": "completed"}
        )
        with self.assertRaisesRegex(StatusTransactionError, "completed"):
            execute_status_transaction(self.repo, completed)
        secret = StatusChangeRequest(
            **{**valid.__dict__, "authority_ref": "token=ghp_not-for-a-journal"}
        )
        with self.assertRaisesRegex(StatusTransactionError, "secret-shaped"):
            execute_status_transaction(self.repo, secret)
        missing_actor = StatusChangeRequest(
            **{**valid.__dict__, "actor": " "}
        )
        with self.assertRaisesRegex(StatusTransactionError, "actor"):
            execute_status_transaction(self.repo, missing_actor)
        self.assertFalse(
            (self.repo / ".git" / "ticket-autopilot" / "status-transactions").exists()
        )

        untracked = self.repo / "unpublished" / "02.md"
        untracked.parent.mkdir()
        untracked.write_text(
            ticket_text("ST-02", "artifact:unpublished-status-fixture"),
            encoding="utf-8",
        )
        request = StatusChangeRequest(
            ticket_source=untracked,
            ticket_id="ST-02",
            artifact_id="artifact:unpublished-status-fixture",
            ticket_digest=ticket_source_digest(untracked),
            from_disposition="open",
            to_disposition="canceled",
            source_mode="ignored",
            actor="user:alice",
            reason="remove unpublished fixture",
            authority_ref="decision:unpublished",
        )
        with self.assertRaisesRegex(StatusTransactionError, "tracked or explicitly ignored"):
            execute_status_transaction(self.repo, request)

    def test_git_common_state_symlinks_fail_closed(self) -> None:
        source = self.make_ticket(tracked=False)
        request = self.request(source, source_mode="ignored")
        state_parent = self.repo / ".git" / "ticket-autopilot"
        state_parent.mkdir(parents=True)
        external = self.repo.parent / "external-status-state"
        external.mkdir()
        try:
            (state_parent / "status-transactions").symlink_to(
                external, target_is_directory=True
            )
        except OSError:
            self.skipTest("directory symlinks are unavailable")

        with self.assertRaisesRegex(StatusTransactionError, "Git common state"):
            execute_status_transaction(self.repo, request)

        self.assertEqual(list(external.iterdir()), [])
        self.assertTrue(source.is_file())

    def test_journal_contradiction_and_linked_worktree_fail_closed(self) -> None:
        source = self.make_ticket(tracked=True)
        request = self.request(source, source_mode="tracked", target="on-hold")
        result = execute_status_transaction(self.repo, request)
        alias = self.repo.parent / "repository-alias"
        try:
            alias.symlink_to(self.repo, target_is_directory=True)
        except OSError:
            alias = None
        if alias is not None:
            with self.assertRaisesRegex(StatusTransactionError, "aliases"):
                execute_status_transaction(
                    alias,
                    StatusChangeRequest(
                        **{
                            **request.__dict__,
                            "ticket_source": alias / "tickets" / "01.md",
                        }
                    ),
                )
        journal = (
            self.repo
            / ".git"
            / "ticket-autopilot"
            / "status-transactions"
            / f"{result['transaction_id']}.json"
        )
        document = json.loads(journal.read_text(encoding="utf-8"))
        document["history"][-1]["details"]["provider_effect_applied"] = True
        journal.write_text(json.dumps(document), encoding="utf-8")
        with self.assertRaisesRegex(StatusTransactionError, "history"):
            execute_status_transaction(self.repo, request)

        linked = self.repo.parent / "linked"
        git(self.repo, "worktree", "add", "--detach", str(linked), "HEAD")
        linked_source = linked / "tickets" / "01.md"
        with self.assertRaisesRegex(StatusTransactionError, "primary worktree"):
            execute_status_transaction(
                linked,
                StatusChangeRequest(
                    **{**request.__dict__, "ticket_source": linked_source}
                ),
            )

    def test_cli_exposes_the_internal_transaction_without_provider_effects(self) -> None:
        source = self.make_ticket(tracked=False)
        request = self.request(source, source_mode="ignored")
        result = subprocess.run(
            [
                sys.executable,
                "-B",
                str(CLI),
                "status-change-transaction",
                str(source),
                "--repo",
                str(self.repo),
                "--ticket-id",
                request.ticket_id,
                "--artifact-id",
                request.artifact_id,
                "--ticket-digest",
                request.ticket_digest,
                "--from-disposition",
                request.from_disposition,
                "--to-disposition",
                request.to_disposition,
                "--source-mode",
                request.source_mode,
                "--actor",
                request.actor,
                "--reason",
                request.reason,
                "--authority-ref",
                request.authority_ref,
            ],
            cwd=self.repo,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["command"], "status-change-transaction")
        self.assertEqual(payload["data"]["status"], "external-unpublished")
        self.assertIn("tracked-provider-delivery", payload["data"]["non_authorities"])


if __name__ == "__main__":
    unittest.main()
