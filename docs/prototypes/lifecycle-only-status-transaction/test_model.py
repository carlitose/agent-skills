from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "ticket-autopilot" / "scripts"))

from model import (  # noqa: E402
    IGNORED_ORDER,
    TRACKED_ORDER,
    FakeProvider,
    OwnerRecord,
    PrototypeError,
    SimulatedCrash,
    Transaction,
    advance,
    expected_tracked_paths,
    freeze_candidate,
    resolve_owner,
    status_boundary,
    validate_request,
)
from autopilot.kernel import Kernel, TransitionError  # noqa: E402
from autopilot.ticket_contract import parse_ticket_folder  # noqa: E402
from autopilot.ticket_lifecycle import transition_ticket_source  # noqa: E402


def ticket_text(ticket_id: str = "01") -> str:
    return f'''---
ticket_schema: 1
ticket_id: "{ticket_id}"
execution_mode: AFK
blocked_by: []
---

# Ticket {ticket_id}

Prototype fixture.
'''


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()


def init_repo(repo: Path) -> None:
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.email", "prototype@example.invalid")
    git(repo, "config", "user.name", "Prototype")


class OwnerAndStateMatrixTests(unittest.TestCase):
    def test_repository_transaction_owner_covers_usable_missing_and_retired_runs(self) -> None:
        digest = "a" * 64
        usable = resolve_owner(digest, [OwnerRecord("live", "usable", digest)])
        self.assertEqual("repository-lifecycle", usable.transaction_owner)
        self.assertEqual("live", usable.projection_run_id)

        missing = resolve_owner(digest, [])
        self.assertIsNone(missing.projection_run_id)
        self.assertEqual((), missing.historical_run_ids)

        retired = resolve_owner(
            digest,
            [OwnerRecord("old-b", "retired", digest), OwnerRecord("old-a", "retired", digest)],
        )
        self.assertIsNone(retired.projection_run_id)
        self.assertEqual(("old-a", "old-b"), retired.historical_run_ids)

    def test_ambiguous_usable_run_ownership_fails_closed(self) -> None:
        digest = "b" * 64
        records = [
            OwnerRecord("one", "usable", digest),
            OwnerRecord("two", "usable", digest),
        ]
        with self.assertRaisesRegex(PrototypeError, "ambiguous"):
            resolve_owner(digest, records)

    def test_public_inputs_accept_only_administrative_dispositions(self) -> None:
        common = {
            "ticket_id": "01",
            "actor": "user:alice",
            "reason": "stop this work",
            "authority_ref": "decision:01",
            "reopen_gate_id": None,
        }
        for target in ("on-hold", "canceled"):
            validate_request(target_disposition=target, **common)
        for target in ("blocked", "paused", "stopped", "completed", "waiting"):
            with self.assertRaises(PrototypeError):
                validate_request(target_disposition=target, **common)
        with self.assertRaisesRegex(PrototypeError, "passed human gate"):
            validate_request(target_disposition="open", **common)
        validate_request(
            target_disposition="open", **{**common, "reopen_gate_id": "gate:01:reopen:1"}
        )

    def test_existing_kernel_matrix_and_decision_safe_boundary_are_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "tickets"
            folder.mkdir()
            (folder / "01.md").write_text(ticket_text(), encoding="utf-8")
            graph = parse_ticket_folder(folder)
            accepted: dict[str, bool] = {}
            for state in ("pending", "active", "gated", "waiting"):
                kernel = Kernel.new("matrix", graph, worktree=tmp, repo=tmp)
                kernel.ledger["tickets"]["01"]["state"] = state
                try:
                    kernel.preflight_disposition_transition(
                        "01",
                        "canceled",
                        actor="user:alice",
                        reason="administrative cancellation",
                        authority_ref="decision:matrix",
                    )
                except TransitionError:
                    accepted[state] = False
                else:
                    accepted[state] = True
            self.assertEqual(
                {"pending": True, "active": True, "gated": False, "waiting": False},
                accepted,
            )

        self.assertEqual("apply-inactive", status_boundary("pending", atomic_effect_in_flight=False).action)
        self.assertEqual(
            "stop-active-at-safe-boundary",
            status_boundary("active", atomic_effect_in_flight=False).action,
        )
        for state in ("gated", "waiting"):
            self.assertEqual(
                "preserve-settled-attempt-and-apply",
                status_boundary(state, atomic_effect_in_flight=False).action,
            )
        with self.assertRaisesRegex(PrototypeError, "must settle"):
            status_boundary("active", atomic_effect_in_flight=True)


class ExistingPrimitiveAndIsolationTests(unittest.TestCase):
    def test_tracked_move_uses_clean_admin_worktree_and_exact_path_allowlist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            init_repo(root)
            family = root / "docs" / "tickets" / "family"
            family.mkdir(parents=True)
            (family / "01.md").write_text(ticket_text(), encoding="utf-8")
            spec = root / "docs" / "specs" / "map.md"
            spec.parent.mkdir(parents=True)
            spec.write_text("[ticket](../tickets/family/01.md)\n", encoding="utf-8")
            (root / "unrelated.txt").write_text("base\n", encoding="utf-8")
            git(root, "add", ".")
            git(root, "commit", "-m", "base")

            # Dirt belongs only to the target checkout and must never be scanned into the
            # administrative candidate.
            (root / "unrelated.txt").write_text("dirty worktree\n", encoding="utf-8")
            (root / "target-index-only.txt").write_text("dirty index\n", encoding="utf-8")
            git(root, "add", "target-index-only.txt")

            admin = Path(tmp) / "admin"
            git(root, "worktree", "add", "--detach", str(admin), "HEAD")
            admin_folder = admin / "docs" / "tickets" / "family"
            graph = parse_ticket_folder(admin_folder)
            receipt = transition_ticket_source(
                admin_folder,
                Path(tmp) / "repository-lifecycle",
                "01",
                "canceled",
                actor="user:alice",
                reason="prototype cancellation",
                authority_ref="decision:prototype",
                expected_digest=graph.tickets["01"].digest,
            )
            admin_spec = admin / "docs" / "specs" / "map.md"
            admin_spec.write_text(
                admin_spec.read_text(encoding="utf-8").replace(
                    "../tickets/family/01.md",
                    "../tickets/family/canceled/01.md",
                ),
                encoding="utf-8",
            )
            git(admin, "add", "-A", "--", "docs/tickets/family", "docs/specs/map.md")
            observed = git(admin, "diff", "--cached", "--name-only", "--no-renames").splitlines()
            allowed = expected_tracked_paths(
                ticket_root="docs/tickets/family",
                source_relative_path=receipt["source_relative_path"],
                destination_relative_path=receipt["destination_relative_path"],
                inbound_repoints=["docs/specs/map.md"],
            )
            self.assertIsNotNone(
                freeze_candidate(
                    source_mode="tracked",
                    observed_paths=observed,
                    allowed_paths=allowed,
                )
            )
            self.assertEqual(allowed, frozenset(observed))
            self.assertNotIn("unrelated.txt", observed)
            self.assertNotIn("target-index-only.txt", observed)
            self.assertIn("unrelated.txt", git(root, "status", "--short"))
            self.assertIn("target-index-only.txt", git(root, "status", "--short"))

            (admin / "rogue.txt").write_text("not allowed\n", encoding="utf-8")
            git(admin, "add", "rogue.txt")
            contaminated = git(admin, "diff", "--cached", "--name-only", "--no-renames").splitlines()
            with self.assertRaisesRegex(PrototypeError, "allowlist"):
                freeze_candidate(
                    source_mode="tracked",
                    observed_paths=contaminated,
                    allowed_paths=allowed,
                )

    def test_ignored_source_receipt_has_no_git_or_provider_publication(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_repo(repo)
            (repo / ".gitignore").write_text("external-tickets/\n", encoding="utf-8")
            git(repo, "add", ".gitignore")
            git(repo, "commit", "-m", "ignore external tickets")
            folder = repo / "external-tickets"
            folder.mkdir()
            (folder / "01.md").write_text(ticket_text(), encoding="utf-8")
            graph = parse_ticket_folder(folder)
            receipt = transition_ticket_source(
                folder,
                repo / ".git" / "prototype-lifecycle",
                "01",
                "on-hold",
                actor="user:alice",
                reason="external hold",
                authority_ref="decision:external-hold",
                expected_digest=graph.tickets["01"].digest,
            )
            self.assertEqual("applied", receipt["state"])
            self.assertEqual("", git(repo, "status", "--short"))
            self.assertIsNone(
                freeze_candidate(source_mode="ignored", observed_paths=[], allowed_paths=[])
            )

            provider = FakeProvider()
            transaction = Transaction("ignored", resolve_owner(graph.tickets["01"].digest, []))
            self.assertEqual("external-unpublished", advance(transaction, provider))
            self.assertEqual(list(IGNORED_ORDER), transaction.durable_steps)
            self.assertEqual(0, provider.dispatch_calls)
            self.assertEqual(0, provider.merge_calls)
            self.assertEqual(0, transaction.commit_effects)
            self.assertEqual(0, transaction.run_projection_effects)

    def test_existing_source_primitive_recovers_before_and_after_the_move(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "tickets"
            folder.mkdir()
            (folder / "01.md").write_text(ticket_text(), encoding="utf-8")
            digest = parse_ticket_folder(folder).tickets["01"].digest
            state_dir = Path(tmp) / "state"
            import autopilot.ticket_lifecycle as lifecycle

            with mock.patch.object(
                lifecycle,
                "_move_no_replace",
                side_effect=RuntimeError("crash before move"),
            ):
                with self.assertRaisesRegex(RuntimeError, "before move"):
                    transition_ticket_source(
                        folder,
                        state_dir,
                        "01",
                        "canceled",
                        actor="user:alice",
                        reason="crash test",
                        authority_ref="decision:crash",
                        expected_digest=digest,
                    )
            self.assertTrue((folder / "01.md").is_file())
            recovered = transition_ticket_source(
                folder,
                state_dir,
                "01",
                "canceled",
                actor="user:alice",
                reason="crash test",
                authority_ref="decision:crash",
                expected_digest=digest,
            )
            replayed = transition_ticket_source(
                folder,
                state_dir,
                "01",
                "canceled",
                actor="user:alice",
                reason="crash test",
                authority_ref="decision:crash",
                expected_digest=digest,
            )
            self.assertEqual(recovered, replayed)
            self.assertTrue((folder / "canceled" / "01.md").is_file())

        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "tickets"
            folder.mkdir()
            (folder / "01.md").write_text(ticket_text(), encoding="utf-8")
            digest = parse_ticket_folder(folder).tickets["01"].digest
            state_dir = Path(tmp) / "state"
            import autopilot.ticket_lifecycle as lifecycle

            real_write = lifecycle._atomic_write
            writes = 0

            def crash_second_write(path: Path, document: dict) -> None:
                nonlocal writes
                writes += 1
                if writes == 2:
                    raise RuntimeError("crash after move")
                real_write(path, document)

            with mock.patch.object(lifecycle, "_atomic_write", side_effect=crash_second_write):
                with self.assertRaisesRegex(RuntimeError, "after move"):
                    transition_ticket_source(
                        folder,
                        state_dir,
                        "01",
                        "on-hold",
                        actor="user:alice",
                        reason="post-move crash test",
                        authority_ref="decision:post-move",
                        expected_digest=digest,
                    )
            self.assertFalse((folder / "01.md").exists())
            self.assertTrue((folder / "hold" / "01.md").is_file())
            recovered = transition_ticket_source(
                folder,
                state_dir,
                "01",
                "on-hold",
                actor="user:alice",
                reason="post-move crash test",
                authority_ref="decision:post-move",
                expected_digest=digest,
            )
            self.assertEqual("applied", recovered["state"])


class ReplayOrderingTests(unittest.TestCase):
    def owner(self, usable: bool = True):
        digest = "c" * 64
        records = [OwnerRecord("run-1", "usable", digest)] if usable else []
        return resolve_owner(digest, records)

    def test_known_nonmutation_and_post_effect_crashes_replay_exactly_once(self) -> None:
        transaction = Transaction("tracked", self.owner())
        provider = FakeProvider(pr_state="open")
        with self.assertRaisesRegex(SimulatedCrash, "lifecycle-intent"):
            advance(
                transaction,
                provider,
                merge_authorized=True,
                terminal_reachable=True,
                crash_after="lifecycle-intent",
            )
        self.assertEqual(0, transaction.source_effects)
        self.assertEqual(
            "complete",
            advance(
                transaction,
                provider,
                merge_authorized=True,
                terminal_reachable=True,
            ),
        )
        self.assertEqual(list(TRACKED_ORDER), transaction.durable_steps)
        self.assertEqual(1, transaction.source_effects)
        self.assertEqual(1, transaction.commit_effects)
        self.assertEqual(1, transaction.projection_effects)
        self.assertEqual(1, transaction.run_projection_effects)
        self.assertEqual(1, provider.dispatch_calls)
        self.assertEqual(1, provider.merge_calls)

        advance(
            transaction,
            provider,
            merge_authorized=True,
            terminal_reachable=True,
        )
        self.assertEqual(1, transaction.source_effects)
        self.assertEqual(1, transaction.commit_effects)
        self.assertEqual(1, transaction.projection_effects)
        self.assertEqual(1, provider.dispatch_calls)
        self.assertEqual(1, provider.merge_calls)

    def test_ambiguous_provider_dispatch_never_redispatches(self) -> None:
        transaction = Transaction("tracked", self.owner())
        provider = FakeProvider(pr_state="open")
        with self.assertRaisesRegex(SimulatedCrash, "provider-dispatch-started"):
            advance(
                transaction,
                provider,
                merge_authorized=True,
                terminal_reachable=True,
                crash_after="provider-dispatch-started",
            )
        self.assertEqual(1, provider.dispatch_calls)
        self.assertEqual(
            "merge-authority-required",
            advance(transaction, provider, merge_authorized=False),
        )
        self.assertEqual(1, provider.dispatch_calls)
        self.assertEqual(
            "complete",
            advance(
                transaction,
                provider,
                merge_authorized=True,
                terminal_reachable=True,
            ),
        )
        self.assertEqual(1, provider.dispatch_calls)

    def test_unknown_provider_outcome_and_merged_without_terminal_proof_gate(self) -> None:
        transaction = Transaction("tracked", self.owner(False))
        provider = FakeProvider()
        self.assertEqual("provider-outcome-ambiguous", advance(transaction, provider))
        self.assertEqual("provider-outcome-ambiguous", advance(transaction, provider))
        self.assertEqual(1, provider.dispatch_calls)
        self.assertEqual(0, transaction.projection_effects)

        provider.pr_state = "merged"
        self.assertEqual(
            "terminal-proof-required",
            advance(transaction, provider, terminal_reachable=False),
        )
        self.assertEqual(0, provider.merge_calls)
        self.assertEqual(0, transaction.projection_effects)
        self.assertEqual(
            "complete",
            advance(transaction, provider, terminal_reachable=True),
        )
        self.assertEqual(1, transaction.projection_effects)
        self.assertEqual(0, transaction.run_projection_effects)

    def test_candidate_contamination_stops_before_commit_or_provider(self) -> None:
        transaction = Transaction("tracked", self.owner())
        provider = FakeProvider(pr_state="open")
        with self.assertRaisesRegex(PrototypeError, "allowlist"):
            advance(transaction, provider, candidate_paths_exact=False)
        self.assertEqual(["request-validated", "lifecycle-intent", "source-applied"], transaction.durable_steps)
        self.assertEqual(0, transaction.commit_effects)
        self.assertEqual(0, provider.dispatch_calls)


if __name__ == "__main__":
    unittest.main()
