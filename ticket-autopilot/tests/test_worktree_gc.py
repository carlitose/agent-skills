from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "ticket-autopilot" / "scripts" / "ticket-autopilot.py"
sys.path.insert(0, str(CLI.parent))

from autopilot.kernel import CandidateRef, Kernel  # type: ignore[import-not-found]
from autopilot.leaf_protocol import LEAF_PHASE_CONTRACTS  # type: ignore[import-not-found]
from autopilot.ledger import AtomicLedger  # type: ignore[import-not-found]
from autopilot.terminal_integration import canonical_digest  # type: ignore[import-not-found]
from autopilot.worktree_gc import (  # type: ignore[import-not-found]
    WorktreeGCError,
    apply_worktree_gc,
    classify_operational_state,
    load_owner_manifest,
)


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, text=True, capture_output=True, check=True
    ).stdout.strip()


def ticket_text() -> str:
    return """---
ticket_schema: 1
ticket_id: "GC-01"
execution_mode: AFK
blocked_by: []
---

# Garbage collection fixture
"""


class WorktreeGCTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.repo = Path(self.temporary.name) / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-b", "main")
        git(self.repo, "config", "user.email", "tests@example.invalid")
        git(self.repo, "config", "user.name", "Worktree GC Tests")
        git(
            self.repo,
            "remote",
            "add",
            "origin",
            "https://github.com/example/worktree-gc-fixture.git",
        )
        tickets = self.repo / "tickets"
        tickets.mkdir()
        (tickets / "01.md").write_text(ticket_text(), encoding="utf-8")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-m", "fixture")

    def cli(self, *args: str, check: bool = True) -> dict[str, object]:
        result = subprocess.run(
            [sys.executable, "-B", str(CLI), *args],
            cwd=self.repo,
            text=True,
            capture_output=True,
            check=False,
        )
        if check and result.returncode:
            self.fail(f"CLI failed: {result.stderr}\n{result.stdout}")
        return json.loads(result.stdout)

    def make_completed_run(self, run_id: str) -> dict[str, object]:
        result = self.cli(
            "run",
            str(self.repo / "tickets"),
            "--repo",
            str(self.repo),
            "--run-id",
            run_id,
            "--final-tree-mode",
            "off",
        )["data"]
        worktree = Path(result["worktree"])
        ledger_path = Path(result["ledger"])
        branch = f"cleanup-{run_id}"
        git(worktree, "switch", "-c", branch)
        head = git(worktree, "rev-parse", "HEAD")
        tree = git(worktree, "rev-parse", "HEAD^{tree}")
        store = AtomicLedger(ledger_path)
        kernel = Kernel(store.load())
        ticket = kernel.ledger["tickets"]["GC-01"]
        candidate = CandidateRef(
            base_tree_oid=tree,
            candidate_tree_oid=tree,
            ticket_digest=ticket["ticket_digest"],
            contract_version=2,
        )
        kernel.activate("GC-01", candidate)
        for stage in (
            "implement",
            "simplify",
            "review",
            "qa-plan",
            "qa-execute",
            "verify",
        ):
            if stage in {"review", "qa-plan", "qa-execute", "verify"}:
                candidate_payload = {
                    "base_tree_oid": tree,
                    "candidate_tree_oid": tree,
                    "ticket_digest": ticket["ticket_digest"],
                    "contract_version": 2,
                }
                leaf: dict[str, object] = {
                    "schema": 3,
                    "complete": True,
                    "candidate_ref": candidate_payload,
                    "stage": stage,
                    "phase_contract": list(LEAF_PHASE_CONTRACTS[stage]),
                    "scope": {
                        "files_expected": [],
                        "files_inspected": [],
                        "files_remaining": [],
                    },
                    "phases_remaining": [],
                    "commands_run": [],
                    "findings": [],
                    "progress_phase": "handoff-ready",
                    "stop_reason": None,
                }
                if stage in {"qa-plan", "qa-execute", "verify"}:
                    leaf["quality"] = {
                        "schema": 1,
                        "causal_scope": [stage],
                        "evidence": [
                            {
                                "id": f"evidence:{stage}",
                                "artifact": f"{stage}.json",
                                "sha256": "a" * 64,
                                "result": "pass",
                                "candidate_ref": candidate_payload,
                            }
                        ],
                        "limitations": ["test fixture"],
                    }
                kernel.record_leaf_result(
                    "GC-01", leaf, candidate, expected_files=[]
                )
            kernel.record_stage("GC-01", stage, "pass", candidate)
        kernel.record_stage("GC-01", "finalize", "pass", candidate)
        kernel.record_pr(
            "GC-01",
            provider="github",
            pr_id=f"pr-{run_id}",
            head_sha=head,
            base_branch="main",
            base_sha=head,
            branch=branch,
        )
        kernel.authorize_merge(
            "GC-01",
            actor="human:test",
            head_sha=head,
            evidence="test://terminal",
        )
        observation = {
            "schema": 1,
            "provider": "github",
            "operation": "get-pr-state",
            "evidence_class": "live",
            "observed": True,
            "pr_id": f"pr-{run_id}",
            "head_sha": head,
            "state": "merged",
            "base": "main",
            "merge_commit_sha": head,
        }
        lineage = kernel.ledger["tickets"]["GC-01"]["delivery_lineage"]
        terminal_proof = {
            "schema": 1,
            "repository_identity": kernel.ledger["repo"],
            "provider": "github",
            "pr_id": f"pr-{run_id}",
            "head_sha": head,
            "pr_base": "main",
            "terminal_branch": "main",
            "terminal_sha": head,
            "terminal_tree_oid": tree,
            "merge_commit_sha": head,
            "reachable_kind": "head",
            "reachable_sha": head,
            "provider_observation_digest": canonical_digest(observation),
            "delivery_lineage_digest": canonical_digest(lineage),
            "provenance": "runner-merge",
        }
        kernel.record_delivery_metadata("GC-01", "integration", observation)
        kernel.record_integration(
            "GC-01",
            expected_head_sha=head,
            terminal_proof=terminal_proof,
        )
        store.save(kernel.ledger)
        self.assertEqual("completed", kernel.ledger["run_state"])
        result["base_sha"] = head
        return result

    def plan(self) -> dict[str, object]:
        return self.cli(
            "worktree-gc-plan", "--repo", str(self.repo)
        )["data"]

    def test_run_persists_exact_owner_and_plan_protects_running_run(self) -> None:
        result = self.cli(
            "run",
            str(self.repo / "tickets"),
            "--repo",
            str(self.repo),
            "--run-id",
            "gc-running",
            "--final-tree-mode",
            "off",
        )
        data = result["data"]
        owner_path = (
            self.repo
            / ".git"
            / "ticket-autopilot"
            / "runs"
            / "gc-running"
            / "worktree-owner.json"
        )
        self.assertTrue(owner_path.is_file())
        owner = load_owner_manifest(owner_path)
        self.assertEqual("created-by-run", owner["origin"]["kind"])
        self.assertEqual(data["worktree"], owner["worktree_path"])
        self.assertEqual(git(self.repo, "rev-parse", "HEAD"), owner["base_sha"])

        planned = self.cli(
            "worktree-gc-plan",
            "--repo",
            str(self.repo),
        )["data"]
        self.assertEqual("worktree-gc-plan-v1", planned["contract_version"])
        self.assertRegex(planned["plan_sha256"], r"^[0-9a-f]{64}$")
        self.assertTrue(Path(planned["plan_path"]).is_file())
        [entry] = planned["entries"]
        self.assertEqual("protected", entry["disposition"])
        self.assertIn("run-not-completed", entry["reasons"])

        replay = self.cli(
            "worktree-gc-plan",
            "--repo",
            str(self.repo),
        )["data"]
        self.assertEqual(planned["plan_sha256"], replay["plan_sha256"])
        self.assertEqual(
            Path(planned["plan_path"]).read_bytes(),
            Path(replay["plan_path"]).read_bytes(),
        )
        empty_apply = self.cli(
            "worktree-gc-apply",
            planned["plan_path"],
            "--repo",
            str(self.repo),
            "--expected-plan-sha256",
            planned["plan_sha256"],
            "--actor",
            "human:test",
            "--evidence",
            "test://empty-plan",
        )["data"]
        self.assertEqual([], empty_apply["confirmed_absent"])
        self.assertEqual([], empty_apply["removed_this_invocation"])
        self.assertFalse(empty_apply["replayed"])

    def test_exact_plan_removes_without_force_and_replays_idempotently(self) -> None:
        completed = self.make_completed_run("gc-complete")
        worktree = Path(completed["worktree"])
        owner_path = Path(completed["ledger"]).parent / "worktree-owner.json"
        branch = "cleanup-gc-complete"
        remote_before = git(self.repo, "remote", "get-url", "origin")
        plan = self.plan()
        [eligible] = [
            entry for entry in plan["entries"] if entry["disposition"] == "eligible"
        ]
        self.assertEqual("gc-complete", eligible["run_id"])

        with mock.patch(
            "autopilot.worktree_gc.remove_isolated_worktree",
            wraps=__import__(
                "autopilot.worktree_gc", fromlist=["remove_isolated_worktree"]
            ).remove_isolated_worktree,
        ) as remove:
            applied = apply_worktree_gc(
                self.repo,
                Path(plan["plan_path"]),
                expected_plan_sha256=plan["plan_sha256"],
                actor="human:test",
                evidence="test://exact-cleanup",
                invocation_path=self.repo,
            )
        remove.assert_called_once_with(self.repo.resolve(), worktree)
        self.assertFalse(worktree.exists())
        self.assertTrue(owner_path.is_file())
        self.assertEqual(remote_before, git(self.repo, "remote", "get-url", "origin"))
        self.assertEqual(
            git(self.repo, "rev-parse", f"refs/heads/{branch}"),
            completed["base_sha"],
        )
        ledger = AtomicLedger(Path(completed["ledger"])).load()
        self.assertEqual(
            {
                "recorded": True,
                "worktree": str(worktree),
                "worktree_removed": True,
                "resume_abandoned": False,
                "remote_state_deleted": False,
            },
            ledger["cleanup"],
        )
        replay = apply_worktree_gc(
            self.repo,
            Path(plan["plan_path"]),
            expected_plan_sha256=plan["plan_sha256"],
            actor="human:test",
            evidence="test://exact-cleanup",
            invocation_path=self.repo,
        )
        self.assertTrue(replay["replayed"])
        self.assertEqual(applied["completion_sha256"], replay["completion_sha256"])

    def test_apply_from_sibling_checkout_uses_the_manifest_owner_root(self) -> None:
        completed = self.make_completed_run("gc-cross-checkout")
        observer = Path(self.temporary.name) / "observer"
        git(self.repo, "worktree", "add", "-b", "gc-observer", str(observer), "HEAD")
        plan = self.cli(
            "worktree-gc-plan", "--repo", str(observer)
        )["data"]
        [eligible] = [
            entry for entry in plan["entries"] if entry["disposition"] == "eligible"
        ]
        self.assertEqual("gc-cross-checkout", eligible["run_id"])

        applied = apply_worktree_gc(
            observer,
            Path(plan["plan_path"]),
            expected_plan_sha256=plan["plan_sha256"],
            actor="human:test",
            evidence="test://cross-checkout-cleanup",
            invocation_path=observer,
        )
        self.assertFalse(applied["replayed"])
        self.assertFalse(Path(completed["worktree"]).exists())
        self.assertTrue(observer.exists())
        self.assertTrue(Path(completed["ledger"]).is_file())

    def test_stale_plan_rejects_the_complete_set_before_intent(self) -> None:
        first = self.make_completed_run("gc-stale-a")
        second = self.make_completed_run("gc-stale-b")
        plan = self.plan()
        Path(second["worktree"], "drift.txt").write_text("dirty\n", encoding="utf-8")

        rejected = self.cli(
            "worktree-gc-apply",
            plan["plan_path"],
            "--repo",
            str(self.repo),
            "--expected-plan-sha256",
            plan["plan_sha256"],
            "--actor",
            "human:test",
            "--evidence",
            "test://stale-plan",
            check=False,
        )
        self.assertFalse(rejected["ok"])
        self.assertIn("stale", rejected["error"]["message"])
        self.assertTrue(Path(first["worktree"]).exists())
        self.assertTrue(Path(second["worktree"]).exists())
        application = (
            self.repo
            / ".git"
            / "ticket-autopilot"
            / "worktree-gc"
            / "applications"
            / plan["plan_sha256"]
        )
        self.assertFalse((application / "intent.json").exists())

        Path(second["worktree"], "drift.txt").unlink()
        with AtomicLedger(Path(first["ledger"])).run_locked():
            locked = self.cli(
                "worktree-gc-apply",
                plan["plan_path"],
                "--repo",
                str(self.repo),
                "--expected-plan-sha256",
                plan["plan_sha256"],
                "--actor",
                "human:test",
                "--evidence",
                "test://stale-plan",
                check=False,
            )
        self.assertFalse(locked["ok"])
        self.assertIn("stale", locked["error"]["message"])
        self.assertTrue(Path(first["worktree"]).exists())
        self.assertTrue(Path(second["worktree"]).exists())
        self.assertFalse((application / "intent.json").exists())

    def test_interruption_after_removal_replays_from_preserved_intent(self) -> None:
        completed = self.make_completed_run("gc-interrupted")
        plan = self.plan()

        def interrupt(phase: str, _context: object) -> None:
            if phase == "after-remove":
                raise RuntimeError("injected interruption")

        with self.assertRaisesRegex(RuntimeError, "injected interruption"):
            apply_worktree_gc(
                self.repo,
                Path(plan["plan_path"]),
                expected_plan_sha256=plan["plan_sha256"],
                actor="human:test",
                evidence="test://interrupted-cleanup",
                invocation_path=self.repo,
                fault_hook=interrupt,
            )
        self.assertFalse(Path(completed["worktree"]).exists())
        self.assertIsNone(AtomicLedger(Path(completed["ledger"])).load()["cleanup"])

        resumed = apply_worktree_gc(
            self.repo,
            Path(plan["plan_path"]),
            expected_plan_sha256=plan["plan_sha256"],
            actor="human:test",
            evidence="test://interrupted-cleanup",
            invocation_path=self.repo,
        )
        self.assertTrue(resumed["replayed"])
        self.assertTrue(Path(resumed["completion_path"]).is_file())
        self.assertTrue(AtomicLedger(Path(completed["ledger"])).load()["cleanup"]["recorded"])

    def test_post_intent_contradiction_stops_before_next_removal(self) -> None:
        first = self.make_completed_run("gc-replay-a")
        second = self.make_completed_run("gc-replay-b")
        plan = self.plan()

        def interrupt(phase: str, context: object) -> None:
            if phase == "after-entry-receipt" and context["run_id"] == "gc-replay-a":
                raise RuntimeError("injected receipt interruption")

        with self.assertRaisesRegex(RuntimeError, "receipt interruption"):
            apply_worktree_gc(
                self.repo,
                Path(plan["plan_path"]),
                expected_plan_sha256=plan["plan_sha256"],
                actor="human:test",
                evidence="test://contradiction",
                invocation_path=self.repo,
                fault_hook=interrupt,
            )
        self.assertFalse(Path(first["worktree"]).exists())
        self.assertTrue(Path(second["worktree"]).exists())
        Path(second["worktree"], "new-drift.txt").write_text("dirty\n", encoding="utf-8")
        with self.assertRaisesRegex(WorktreeGCError, "dirty"):
            apply_worktree_gc(
                self.repo,
                Path(plan["plan_path"]),
                expected_plan_sha256=plan["plan_sha256"],
                actor="human:test",
                evidence="test://contradiction",
                invocation_path=self.repo,
            )
        self.assertTrue(Path(second["worktree"]).exists())

    def test_readback_ledger_and_completion_boundary_interruptions_replay(self) -> None:
        for sequence, phase in enumerate(
            ("after-readback", "after-ledger-save", "before-completion"), start=1
        ):
            with self.subTest(phase=phase):
                completed = self.make_completed_run(f"gc-phase-{sequence}")
                plan = self.plan()

                def interrupt(current: str, _context: object) -> None:
                    if current == phase:
                        raise RuntimeError(f"injected {phase}")

                with self.assertRaisesRegex(RuntimeError, phase):
                    apply_worktree_gc(
                        self.repo,
                        Path(plan["plan_path"]),
                        expected_plan_sha256=plan["plan_sha256"],
                        actor="human:test",
                        evidence=f"test://{phase}",
                        invocation_path=self.repo,
                        fault_hook=interrupt,
                    )
                resumed = apply_worktree_gc(
                    self.repo,
                    Path(plan["plan_path"]),
                    expected_plan_sha256=plan["plan_sha256"],
                    actor="human:test",
                    evidence=f"test://{phase}",
                    invocation_path=self.repo,
                )
                self.assertTrue(resumed["replayed"])
                self.assertFalse(Path(completed["worktree"]).exists())
                self.assertTrue(Path(resumed["completion_path"]).is_file())

    def test_intent_and_completion_unknown_fields_fail_closed(self) -> None:
        completed = self.make_completed_run("gc-strict-apply")
        plan = self.plan()
        plan_document = json.loads(Path(plan["plan_path"]).read_text(encoding="utf-8"))
        plan_document["payload"]["unexpected"] = True
        plan_document["integrity"] = hashlib.sha256(
            json.dumps(
                plan_document["payload"], sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
        ).hexdigest()
        plan_bytes = (
            json.dumps(plan_document, sort_keys=True, separators=(",", ":")) + "\n"
        ).encode("utf-8")
        malformed_sha = hashlib.sha256(plan_bytes).hexdigest()
        malformed_path = Path(plan["plan_path"]).parent / f"{malformed_sha}.json"
        malformed_path.write_bytes(plan_bytes)
        with self.assertRaisesRegex(WorktreeGCError, "plan fields"):
            apply_worktree_gc(
                self.repo,
                malformed_path,
                expected_plan_sha256=malformed_sha,
                actor="human:test",
                evidence="test://strict-apply",
                invocation_path=self.repo,
            )
        self.assertTrue(Path(completed["worktree"]).exists())

        def interrupt(phase: str, _context: object) -> None:
            if phase == "after-intent":
                raise RuntimeError("intent persisted")

        with self.assertRaisesRegex(RuntimeError, "intent persisted"):
            apply_worktree_gc(
                self.repo,
                Path(plan["plan_path"]),
                expected_plan_sha256=plan["plan_sha256"],
                actor="human:test",
                evidence="test://strict-apply",
                invocation_path=self.repo,
                fault_hook=interrupt,
            )
        application = (
            self.repo
            / ".git"
            / "ticket-autopilot"
            / "worktree-gc"
            / "applications"
            / plan["plan_sha256"]
        )
        intent_path = application / "intent.json"
        original_intent = intent_path.read_bytes()
        changed_inventory = json.loads(original_intent)
        changed_inventory["payload"]["inventory"] = changed_inventory["payload"][
            "inventory"
        ][1:]
        changed_inventory["integrity"] = hashlib.sha256(
            json.dumps(
                changed_inventory["payload"], sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
        ).hexdigest()
        intent_path.write_text(
            json.dumps(changed_inventory, sort_keys=True, separators=(",", ":"))
            + "\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(WorktreeGCError, "inventory differs"):
            apply_worktree_gc(
                self.repo,
                Path(plan["plan_path"]),
                expected_plan_sha256=plan["plan_sha256"],
                actor="human:test",
                evidence="test://strict-apply",
                invocation_path=self.repo,
            )
        self.assertTrue(Path(completed["worktree"]).exists())

        intent = json.loads(original_intent)
        intent["payload"]["unexpected"] = True
        intent["integrity"] = hashlib.sha256(
            json.dumps(
                intent["payload"], sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
        ).hexdigest()
        intent_path.write_text(
            json.dumps(intent, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(WorktreeGCError, "intent fields"):
            apply_worktree_gc(
                self.repo,
                Path(plan["plan_path"]),
                expected_plan_sha256=plan["plan_sha256"],
                actor="human:test",
                evidence="test://strict-apply",
                invocation_path=self.repo,
            )
        self.assertTrue(Path(completed["worktree"]).exists())
        intent_path.write_bytes(original_intent)
        with self.assertRaisesRegex(WorktreeGCError, "intent differs"):
            apply_worktree_gc(
                self.repo,
                Path(plan["plan_path"]),
                expected_plan_sha256=plan["plan_sha256"],
                actor="human:other",
                evidence="test://strict-apply",
                invocation_path=self.repo,
            )
        self.assertTrue(Path(completed["worktree"]).exists())
        applied = apply_worktree_gc(
            self.repo,
            Path(plan["plan_path"]),
            expected_plan_sha256=plan["plan_sha256"],
            actor="human:test",
            evidence="test://strict-apply",
            invocation_path=self.repo,
        )
        completion_path = Path(applied["completion_path"])
        entry_path = next((application / "entries").glob("*.json"))
        original_entry = entry_path.read_bytes()
        entry_receipt = json.loads(original_entry)
        entry_receipt["payload"]["unexpected"] = True
        entry_receipt["integrity"] = hashlib.sha256(
            json.dumps(
                entry_receipt["payload"], sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
        ).hexdigest()
        entry_path.write_text(
            json.dumps(entry_receipt, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(WorktreeGCError, "entry receipt fields"):
            apply_worktree_gc(
                self.repo,
                Path(plan["plan_path"]),
                expected_plan_sha256=plan["plan_sha256"],
                actor="human:test",
                evidence="test://strict-apply",
                invocation_path=self.repo,
            )
        entry_path.write_bytes(original_entry)

        completion = json.loads(completion_path.read_text(encoding="utf-8"))
        completion["payload"]["unexpected"] = True
        completion["integrity"] = hashlib.sha256(
            json.dumps(
                completion["payload"], sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
        ).hexdigest()
        completion_path.write_text(
            json.dumps(completion, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(WorktreeGCError, "completion receipt fields"):
            apply_worktree_gc(
                self.repo,
                Path(plan["plan_path"]),
                expected_plan_sha256=plan["plan_sha256"],
                actor="human:test",
                evidence="test://strict-apply",
                invocation_path=self.repo,
            )

    def test_unsupported_remote_is_hashed_but_credentials_are_rejected(self) -> None:
        git(
            self.repo,
            "remote",
            "set-url",
            "origin",
            "https://example.invalid/repo.git",
        )
        result = self.cli(
            "run",
            str(self.repo / "tickets"),
            "--repo",
            str(self.repo),
            "--provider",
            "github",
            "--run-id",
            "gc-unsupported-remote",
            "--final-tree-mode",
            "off",
        )["data"]
        owner = load_owner_manifest(
            Path(result["ledger"]).parent / "worktree-owner.json"
        )
        self.assertEqual("local-or-unsupported", owner["provider"])
        self.assertRegex(owner["normalized_remote"], r"^sha256:[0-9a-f]{64}$")

        git(
            self.repo,
            "remote",
            "set-url",
            "origin",
            "https://secret@example.invalid/repo.git",
        )
        rejected = self.cli(
            "run",
            str(self.repo / "tickets"),
            "--repo",
            str(self.repo),
            "--provider",
            "github",
            "--run-id",
            "gc-credential-remote",
            "--final-tree-mode",
            "off",
            check=False,
        )
        self.assertFalse(rejected["ok"])
        self.assertIn("credentials or parameters", rejected["error"]["message"])

    def test_manifest_loader_rejects_unknown_fields_and_digest_tampering(self) -> None:
        self.cli(
            "run",
            str(self.repo / "tickets"),
            "--repo",
            str(self.repo),
            "--run-id",
            "gc-strict",
            "--final-tree-mode",
            "off",
        )
        owner_path = (
            self.repo
            / ".git"
            / "ticket-autopilot"
            / "runs"
            / "gc-strict"
            / "worktree-owner.json"
        )
        document = json.loads(owner_path.read_text(encoding="utf-8"))
        document["unexpected"] = True
        owner_path.write_text(json.dumps(document), encoding="utf-8")
        with self.assertRaisesRegex(WorktreeGCError, "fields"):
            load_owner_manifest(owner_path)

        del document["unexpected"]
        document["payload"]["base_sha"] = "f" * 40
        owner_path.write_text(json.dumps(document), encoding="utf-8")
        with self.assertRaisesRegex(WorktreeGCError, "integrity"):
            load_owner_manifest(owner_path)

    def test_invalid_ownership_inventory_protects_other_owned_worktrees(self) -> None:
        completed = self.make_completed_run("gc-valid-neighbor")
        running = self.cli(
            "run",
            str(self.repo / "tickets"),
            "--repo",
            str(self.repo),
            "--run-id",
            "gc-invalid-neighbor",
            "--final-tree-mode",
            "off",
        )["data"]
        invalid_path = Path(running["ledger"]).parent / "worktree-owner.json"
        invalid = json.loads(invalid_path.read_text(encoding="utf-8"))
        invalid["unexpected"] = True
        invalid_path.write_text(json.dumps(invalid), encoding="utf-8")

        plan = self.plan()
        [valid] = [
            entry for entry in plan["entries"] if entry["run_id"] == "gc-valid-neighbor"
        ]
        self.assertEqual("protected", valid["disposition"])
        self.assertIn("ownership-inventory-invalid", valid["reasons"])
        self.assertTrue(plan["invalid_manifests"])
        self.assertTrue(Path(completed["worktree"]).exists())

    def test_operational_state_protects_open_wiki_and_incomplete_pi_sync(self) -> None:
        ledger = {
            "run_state": "completed",
            "cleanup": None,
            "gates": {},
            "tickets": {
                "WDT-01": {
                    "state": "integrated",
                    "delivery_lineage": {"head_sha": "a" * 40},
                    "delivery": {
                        "terminal-integration": {
                            "head_sha": "a" * 40,
                            "terminal_sha": "b" * 40,
                        },
                        "wiki-sync": {
                            "result": {"status": "candidate-created"},
                            "delivery": {"status": "pr-open"},
                        },
                    },
                }
            },
            "ticket_order": ["WDT-01"],
        }
        reasons = classify_operational_state(
            ledger,
            pi_sync_states=[{"phases": ["intent-persisted"], "receipt": None}],
        )
        self.assertIn("wiki-delivery-nonterminal", reasons)
        self.assertIn("pi-sync-incomplete", reasons)

    def test_terminal_operational_state_has_no_protection_reason(self) -> None:
        head = "a" * 40
        ledger = {
            "run_state": "completed",
            "cleanup": None,
            "gates": {"gate:GC-01:test:1": {"state": "passed"}},
            "tickets": {
                "GC-01": {
                    "state": "integrated",
                    "delivery_lineage": {"head_sha": head},
                    "delivery": {
                        "terminal-integration": {
                            "head_sha": head,
                            "terminal_sha": "b" * 40,
                        }
                    },
                }
            },
            "ticket_order": ["GC-01"],
        }
        self.assertEqual([], classify_operational_state(ledger))

    def test_adoption_requires_exact_ledger_digest_and_explicit_authority(self) -> None:
        result = self.cli(
            "run",
            str(self.repo / "tickets"),
            "--repo",
            str(self.repo),
            "--run-id",
            "gc-adopt",
            "--final-tree-mode",
            "off",
        )["data"]
        owner_path = Path(result["ledger"]).parent / "worktree-owner.json"
        owner_path.unlink()
        ledger_path = Path(result["ledger"])
        ledger_sha = hashlib.sha256(ledger_path.read_bytes()).hexdigest()

        mismatch = self.cli(
            "worktree-owner-adopt",
            "gc-adopt",
            "--repo",
            str(self.repo),
            "--expected-ledger-sha256",
            "0" * 64,
            "--actor",
            "human:test",
            "--evidence",
            "test://exact-adoption",
            check=False,
        )
        self.assertFalse(mismatch["ok"])
        self.assertFalse(owner_path.exists())

        adopted = self.cli(
            "worktree-owner-adopt",
            "gc-adopt",
            "--repo",
            str(self.repo),
            "--expected-ledger-sha256",
            ledger_sha,
            "--actor",
            "human:test",
            "--evidence",
            "test://exact-adoption",
        )["data"]
        self.assertEqual("legacy-adoption", adopted["manifest"]["origin"]["kind"])
        self.assertEqual(ledger_sha, adopted["manifest"]["origin"]["ledger_sha256"])
        self.assertTrue(owner_path.is_file())
        replay = self.cli(
            "worktree-owner-adopt",
            "gc-adopt",
            "--repo",
            str(self.repo),
            "--expected-ledger-sha256",
            ledger_sha,
            "--actor",
            "human:test",
            "--evidence",
            "test://exact-adoption",
        )["data"]
        self.assertTrue(replay["replayed"])


if __name__ == "__main__":
    unittest.main()
