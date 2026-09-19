"""Fresh target and runner-owned candidate coherence is mandatory before review."""
from __future__ import annotations

import copy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from autopilot.git_ops import run_git  # noqa: E402
from autopilot.candidate_contract import CandidateRef  # noqa: E402
from autopilot.kernel import Kernel, TransitionError  # noqa: E402
from autopilot.ledger import AtomicLedger  # noqa: E402
from autopilot.ticket_contract import parse_ticket_folder  # noqa: E402
from autopilot.pre_qa_coherence import (  # noqa: E402
    PreQaCoherenceError,
    build_receipt,
    observe_target,
    validate_bound_receipt,
    validate_receipt,
    require_current_receipt,
)
from git_test_support import GitIsolatedTestCase  # noqa: E402


class PreQaCoherenceTests(GitIsolatedTestCase):
    def setUp(self) -> None:
        owner = tempfile.TemporaryDirectory(prefix="pre-qa-coherence-")
        self.addCleanup(owner.cleanup)
        self.root = Path(owner.name)
        self.remote = self.root / "remote.git"
        self.repo = self.root / "repo"
        self.other = self.root / "other"
        self.worktree = self.root / "candidate"
        self._git(self.root, "init", "--bare", "--initial-branch=main", str(self.remote))
        self._git(self.root, "clone", str(self.remote), str(self.repo))
        self._identity(self.repo)
        public = "https://github.com/example/pre-qa-coherence.git"
        self._git(self.repo, "config", f"url.{self.remote.as_posix()}.insteadOf", public)
        self._git(self.repo, "remote", "set-url", "origin", public)
        (self.repo / "value.txt").write_text("one\n", encoding="utf-8")
        self._git(self.repo, "add", "value.txt")
        self._git(self.repo, "commit", "-m", "base")
        self._git(self.repo, "push", "-u", "origin", "main")
        self.target = observe_target(self.repo, "main")
        self._git(self.repo, "worktree", "add", "--detach", str(self.worktree), self.target["sha"])
        self.candidate = {
            "contract_version": 2,
            "base_tree_oid": self.target["tree_oid"],
            "candidate_tree_oid": run_git(self.worktree, "write-tree"),
            "ticket_digest": "a" * 64,
        }

    def _git(self, cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args], cwd=cwd, text=True, capture_output=True,
            check=True, timeout=30,
        )

    def _identity(self, repo: Path) -> None:
        self._git(repo, "config", "user.name", "pre-qa")
        self._git(repo, "config", "user.email", "pre-qa@example.invalid")

    def _ledger(self, *, repo: Path | None = None, worktree: Path | None = None) -> dict:
        return {
            "run_id": "guard-run",
            "provider": "github",
            "gates": {},
            "repo": str(repo or self.repo),
            "worktree": str(worktree or self.worktree),
            "target_identity": self.target,
            "tickets": {"PCG-01": {
                "artifact_generation": 1,
                "blocked_by": [],
                "candidate_ref": self.candidate,
            }},
        }

    def _advance_remote(self) -> str:
        self._git(self.root, "clone", str(self.remote), str(self.other))
        self._identity(self.other)
        (self.other / "value.txt").write_text("two\n", encoding="utf-8")
        self._git(self.other, "add", "value.txt")
        self._git(self.other, "commit", "-m", "advance")
        self._git(self.other, "push", "origin", "main")
        return run_git(self.other, "rev-parse", "HEAD")

    def _quality_kernel(self, *, legacy: bool = False) -> tuple[Kernel, CandidateRef]:
        folder = self.repo / "tickets"
        folder.mkdir()
        (folder / "01.md").write_text(
            "---\nticket_schema: 1\nticket_id: PCG-01\nexecution_mode: AFK\nblocked_by: []\n---\n\n# Coherence fixture\n",
            encoding="utf-8",
        )
        kernel = Kernel.new(
            "guard-run", parse_ticket_folder(folder), provider="github",
            repo=str(self.repo), worktree=str(self.worktree),
            base_sha=self.target["sha"],
            target_identity=None if legacy else self.target,
        )
        candidate = CandidateRef(
            self.candidate["base_tree_oid"], self.candidate["candidate_tree_oid"],
            kernel.ledger["tickets"]["PCG-01"]["ticket_digest"],
        )
        kernel.activate("PCG-01", candidate)
        for stage in ("implement", "simplify"):
            kernel.record_stage("PCG-01", stage, "pass", candidate)
        return kernel, candidate

    def test_legacy_target_adoption_is_persisted_once_and_replayed(self) -> None:
        kernel, candidate = self._quality_kernel(legacy=True)
        receipt = build_receipt(
            ledger=kernel.ledger, ticket_id="PCG-01", candidate_ref=candidate.as_dict(),
        )
        store = AtomicLedger(self.root / "ledger.json")
        store.save(kernel.ledger)
        self.assertTrue(kernel.record_pre_qa_coherence("PCG-01", receipt))
        store.save(kernel.ledger)
        replayed = Kernel(store.load())
        self.assertEqual(self.target, replayed.ledger["target_identity"])
        before = copy.deepcopy(replayed.ledger)
        again = build_receipt(
            ledger=replayed.ledger, ticket_id="PCG-01", candidate_ref=candidate.as_dict(),
        )
        self.assertEqual(receipt, again)
        self.assertFalse(replayed.record_pre_qa_coherence("PCG-01", again))
        self.assertEqual(before, replayed.ledger)
        require_current_receipt(replayed.ledger, "PCG-01")

    def test_kernel_rejects_leaf_without_a_current_passing_receipt(self) -> None:
        kernel, candidate = self._quality_kernel()
        before = copy.deepcopy(kernel.ledger)
        with self.assertRaisesRegex(TransitionError, "pre-QA"):
            kernel.record_leaf_result("PCG-01", {}, candidate, expected_files=[])
        self.assertEqual(before, kernel.ledger)

    def test_fresh_target_passes_without_moving_local_main(self) -> None:
        local_before = run_git(self.repo, "rev-parse", "main")
        receipt = build_receipt(
            ledger=self._ledger(), ticket_id="PCG-01",
            candidate_ref=self.candidate,
        )
        self.assertEqual(receipt["status"], "pass")
        self.assertIsNone(receipt["reason"])
        self.assertEqual(run_git(self.repo, "rev-parse", "main"), local_before)

    def test_local_transport_identity_is_observed_without_provider_guessing(self) -> None:
        self._git(self.repo, "remote", "set-url", "origin", str(self.remote))
        target = observe_target(self.repo, "main")
        self.assertEqual("local-or-unsupported", target["provider"])
        self.assertRegex(target["normalized_remote"], r"^sha256:[0-9a-f]{64}$")
        self.assertEqual(self.target["sha"], target["sha"])

    def test_remote_advance_blocks_stale_candidate_and_keeps_local_main(self) -> None:
        local_before = run_git(self.repo, "rev-parse", "main")
        remote_head = self._advance_remote()
        receipt = build_receipt(
            ledger=self._ledger(), ticket_id="PCG-01",
            candidate_ref=self.candidate,
        )
        self.assertEqual(receipt["status"], "blocked")
        self.assertEqual(receipt["reason"], "target-advanced-before-qa")
        self.assertEqual(receipt["target"]["sha"], remote_head)
        self.assertEqual(run_git(self.repo, "rev-parse", "main"), local_before)

    def test_index_drift_keeps_existing_candidate_classification(self) -> None:
        (self.worktree / "value.txt").write_text("candidate\n", encoding="utf-8")
        self._git(self.worktree, "add", "value.txt")
        receipt = build_receipt(
            ledger=self._ledger(), ticket_id="PCG-01",
            candidate_ref=self.candidate,
        )
        self.assertEqual(receipt["reason"], "candidate-index-drift")

    def test_wrong_git_common_directory_is_rejected(self) -> None:
        foreign = self.root / "foreign"
        self._git(self.root, "clone", str(self.remote), str(foreign))
        receipt = build_receipt(
            ledger=self._ledger(worktree=foreign), ticket_id="PCG-01",
            candidate_ref=self.candidate,
        )
        self.assertEqual(receipt["reason"], "repository-identity-mismatch")

    def test_legacy_run_adopts_only_an_exact_current_target(self) -> None:
        ledger = self._ledger()
        ledger.pop("target_identity")
        receipt = build_receipt(
            ledger=ledger, ticket_id="PCG-01",
            candidate_ref=self.candidate,
        )
        self.assertTrue(receipt["legacy_adoption"])
        self.assertEqual(receipt["status"], "pass")

    def test_pass_receipt_rejects_contradictory_observations(self) -> None:
        receipt = build_receipt(
            ledger=self._ledger(), ticket_id="PCG-01",
            candidate_ref=self.candidate,
        )
        mutations = (
            ("head_tree_oid", "e" * 40),
            ("index_tree_oid", "e" * 40),
            ("git_common_dir", "/unrelated/.git"),
            ("candidate_ref", {}),
        )
        for key, value in mutations:
            with self.subTest(field=key):
                forged = copy.deepcopy(receipt)
                forged[key] = value
                with self.assertRaises(PreQaCoherenceError):
                    validate_receipt(forged)
        forged = copy.deepcopy(receipt)
        forged["target"]["tree_oid"] = "e" * 40
        with self.assertRaises(PreQaCoherenceError):
            validate_receipt(forged)

    def test_missing_worktree_is_typed_and_does_not_invent_observations(self) -> None:
        receipt = build_receipt(
            ledger=self._ledger(worktree=self.root / "missing"),
            ticket_id="PCG-01", candidate_ref=self.candidate,
        )
        self.assertEqual("blocked", receipt["status"])
        self.assertEqual("worktree-identity-mismatch", receipt["reason"])
        self.assertIsNone(receipt["head_sha"])
        self.assertIsNone(receipt["head_tree_oid"])
        self.assertIsNone(receipt["index_tree_oid"])

    def test_target_aware_quality_requires_bound_current_pass(self) -> None:
        ledger = self._ledger()
        with self.assertRaises(PreQaCoherenceError):
            require_current_receipt(ledger, "PCG-01")
        receipt = build_receipt(
            ledger=ledger, ticket_id="PCG-01", candidate_ref=self.candidate,
        )
        ledger["tickets"]["PCG-01"]["pre_qa_coherence"] = receipt
        require_current_receipt(ledger, "PCG-01")
        ledger["tickets"]["PCG-01"]["artifact_generation"] += 1
        with self.assertRaises(PreQaCoherenceError):
            require_current_receipt(ledger, "PCG-01")

    def test_forged_delivery_proof_does_not_replace_ledger_lineage(self) -> None:
        ledger = self._ledger()
        receipt = build_receipt(
            ledger=ledger, ticket_id="PCG-01", candidate_ref=self.candidate,
        )
        receipt["head_tree_oid"] = "d" * 40
        receipt["head_binding"] = {
            "kind": "delivery", "source": "commit", "branch": "forged",
            "head_sha": receipt["head_sha"], "base_sha": self.target["sha"],
            "base_tree_oid": self.target["tree_oid"], "record_digest": "e" * 64,
        }
        with self.assertRaisesRegex(PreQaCoherenceError, "ledger lineage"):
            validate_bound_receipt(receipt, ledger, "PCG-01")

    def test_fetch_failure_has_no_cached_pass_or_sensitive_output(self) -> None:
        from autopilot.git_ops import GitError

        with mock.patch(
            "autopilot.pre_qa_coherence.observe_target",
            side_effect=GitError("private transport diagnostic"),
        ):
            receipt = build_receipt(
                ledger=self._ledger(), ticket_id="PCG-01", candidate_ref=self.candidate,
            )
        self.assertEqual("target-fetch-failed", receipt["reason"])
        self.assertIsNone(receipt["target"])
        self.assertNotIn("private transport diagnostic", repr(receipt))

    def test_legacy_run_without_remote_default_does_not_guess_main(self) -> None:
        ledger = self._ledger()
        ledger.pop("target_identity")
        self._git(self.remote, "symbolic-ref", "HEAD", "refs/heads/missing")
        receipt = build_receipt(
            ledger=ledger, ticket_id="PCG-01", candidate_ref=self.candidate,
        )
        self.assertEqual("coherence-receipt-malformed", receipt["reason"])
        self.assertIsNone(receipt["target"])

    def test_foreign_ledger_worktree_path_cannot_reuse_a_valid_receipt(self) -> None:
        ledger = self._ledger()
        receipt = build_receipt(
            ledger=ledger, ticket_id="PCG-01", candidate_ref=self.candidate,
        )
        ledger["worktree"] = str(self.repo)
        with self.assertRaises(PreQaCoherenceError):
            validate_bound_receipt(receipt, ledger, "PCG-01")

    def test_unrecorded_commit_cannot_claim_a_recorded_delivery_exception(self) -> None:
        (self.worktree / "value.txt").write_text("unrecorded\n", encoding="utf-8")
        self._git(self.worktree, "commit", "-am", "not owned by this ticket")
        candidate = dict(self.candidate)
        candidate["candidate_tree_oid"] = run_git(self.worktree, "write-tree")
        receipt = build_receipt(
            ledger=self._ledger(), ticket_id="PCG-01", candidate_ref=candidate,
        )
        self.assertEqual("candidate-base-drift", receipt["reason"])
        self.assertIsNone(receipt["head_binding"])

    def test_malformed_receipt_fails_closed(self) -> None:
        receipt = build_receipt(
            ledger=self._ledger(), ticket_id="PCG-01",
            candidate_ref=self.candidate,
        )
        receipt["target"]["tree_oid"] = "not-an-oid"
        with self.assertRaisesRegex(PreQaCoherenceError, "tree_oid"):
            validate_receipt(receipt)


if __name__ == "__main__":
    unittest.main()
