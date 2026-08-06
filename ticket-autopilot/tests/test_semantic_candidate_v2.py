from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
import copy
import json
from dataclasses import asdict, replace
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from autopilot.candidate_contract import (  # noqa: E402
    CANDIDATE_CONTRACT_VERSION,
    CandidateContractError,
    DeliveryLineage,
    SemanticCandidateRef,
)
from autopilot.cli import _autonomous_eligibility, _reconciliation_gate  # noqa: E402
from autopilot.git_ops import CommandResult, semantic_candidate_ref  # noqa: E402
from autopilot.kernel import Kernel  # noqa: E402
from autopilot.ledger import AtomicLedger, LedgerError  # noqa: E402
from autopilot.leaf_protocol import LEAF_PHASE_CONTRACTS  # noqa: E402
from autopilot.providers import ProviderError  # noqa: E402
from autopilot.ticket_contract import Ticket, TicketGraph  # noqa: E402


def git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        capture_output=True,
        check=True,
    )
    return completed.stdout.strip()


class EligibilityRunner:
    def __init__(self, *, pr_id: str, head_sha: str) -> None:
        self.pr_id = pr_id
        self.head_sha = head_sha
        self.commands: list[list[str]] = []

    def run(self, command: list[str], *, cwd: Path) -> CommandResult:
        self.commands.append(command)
        if (
            command[:2] == ["gh", "api"]
            and "/rules/branches/" in command[2]
        ):
            return CommandResult("[]", "", 0)
        if command[:3] == ["gh", "pr", "view"]:
            return CommandResult(
                json.dumps(
                    {
                        "number": self.pr_id,
                        "url": f"https://github.example/pr/{self.pr_id}",
                        "state": "OPEN",
                        "mergedAt": None,
                        "headRefName": f"ticket/{self.pr_id}",
                        "headRefOid": self.head_sha,
                        "baseRefName": "main",
                        "body": "validated body",
                        "reviewDecision": "APPROVED",
                        "reviews": [],
                        "mergeable": "MERGEABLE",
                        "mergeStateStatus": "CLEAN",
                        "statusCheckRollup": [],
                    }
                ),
                "",
                0,
            )
        return CommandResult("", f"unexpected command: {command}", 1)


class SemanticCandidateContractTests(unittest.TestCase):
    def test_v2_identity_excludes_mutable_commit_lineage(self) -> None:
        candidate = SemanticCandidateRef(
            base_tree_oid="base-tree",
            candidate_tree_oid="candidate-tree",
            ticket_digest="ticket-digest",
            contract_version=2,
        )
        lineage = DeliveryLineage(
            provider="github",
            pr_id="42",
            branch="ticket/05",
            base_branch="main",
            base_sha="base-sha",
            head_sha="head-sha",
            contract_version=1,
        )

        self.assertEqual(2, CANDIDATE_CONTRACT_VERSION)
        self.assertNotIn("sha", candidate.as_dict())
        self.assertEqual("head-sha", lineage.as_dict()["head_sha"])
        candidate.validate()
        lineage.validate()

    def test_git_derives_semantic_identity_from_trees_not_lineage_claims(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init")
            git(repo, "config", "user.name", "Tests")
            git(repo, "config", "user.email", "tests@example.com")
            (repo / "base.txt").write_text("base\n", encoding="utf-8")
            git(repo, "add", "base.txt")
            git(repo, "commit", "-m", "base")
            base_tree = git(repo, "rev-parse", "HEAD^{tree}")
            (repo / "child.txt").write_text("child\n", encoding="utf-8")
            git(repo, "add", "child.txt")

            candidate = semantic_candidate_ref(
                repo,
                "ticket-digest",
                base_ref="HEAD",
            )

            self.assertEqual(base_tree, candidate.base_tree_oid)
            self.assertEqual(git(repo, "write-tree"), candidate.candidate_tree_oid)
            self.assertEqual(2, candidate.contract_version)


class SemanticReconciliationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        root = Path(self.directory.name)
        ticket = Ticket("05", "AFK", (), root / "05.md", "ticket-digest")
        graph = TicketGraph(
            folder=root,
            tickets={"05": ticket},
            order=("05",),
            completed_ids=frozenset(),
        )
        self.candidate = SemanticCandidateRef(
            "base-tree", "candidate-tree", "ticket-digest", 2
        )
        self.kernel = Kernel.new(
            "semantic-reconciliation",
            graph,
            provider="github",
            repo="/repo",
            worktree="/tmp",
            merge_policy="autonomous",
            merge_actor="release-operator",
            merge_evidence="artifact://run-merge-grant",
        )
        self.kernel.activate("05", self.candidate)
        for stage in (
            "implement",
            "simplify",
            "review",
            "qa-plan",
            "qa-execute",
            "verify",
            "finalize",
        ):
            if stage in LEAF_PHASE_CONTRACTS and stage not in {
                "implement",
                "simplify",
            }:
                phases = list(LEAF_PHASE_CONTRACTS[stage])
                result = {
                        "schema": 3,
                        "complete": True,
                        "candidate_ref": asdict(self.candidate),
                        "stage": stage,
                        "phase_contract": phases,
                        "scope": {
                            "files_expected": ["change.py"],
                            "files_inspected": ["change.py"],
                            "files_remaining": [],
                        },
                        "phases_remaining": [],
                        "commands_run": [f"test:{stage}"],
                        "findings": [],
                        "progress_phase": phases[-1],
                        "stop_reason": None,
                    }
                if stage in {"qa-plan", "qa-execute", "verify"}:
                    result["quality"] = {
                        "schema": 1,
                        "causal_scope": [stage],
                        "evidence": [
                            {
                                "id": f"evidence:{stage}",
                                "artifact": f"{stage}.json",
                                "sha256": "a" * 64,
                                "result": "pass",
                                "candidate_ref": asdict(self.candidate),
                            }
                        ],
                        "limitations": ["local-only"],
                    }
                self.kernel.record_leaf_result(
                    "05",
                    result,
                    self.candidate,
                    expected_files=["change.py"],
                )
            self.kernel.record_stage("05", stage, "pass", self.candidate)
        self.kernel.record_pr(
            "05",
            provider="github",
            pr_id="42",
            branch="ticket/05",
            base_branch="parent/04",
            base_sha="parent-head",
            head_sha="old-head",
        )

    def prepare(self, candidate: SemanticCandidateRef) -> bool:
        return self.kernel.prepare_reconciliation(
            "05",
            candidate,
            old_head="old-head",
            new_head="rebased-head",
            base_branch="main",
            base_sha="merged-parent-head",
            base_tree_oid=candidate.base_tree_oid,
            expected_remote_sha="old-head",
        )

    def test_exact_semantic_equality_preserves_all_validated_artifacts(self) -> None:
        before = self.kernel.ledger["tickets"]["05"]
        leaf_results = before["leaf_results"].copy()
        generation = before["artifact_generation"]
        self.kernel.authorize_merge(
            "05",
            actor="release-operator",
            head_sha="old-head",
            evidence="artifact://run-merge-grant",
            mode="autonomous",
        )
        grant = copy.deepcopy(self.kernel.ledger["autonomous_merge_grant"])

        self.assertTrue(self.prepare(self.candidate))

        ticket = self.kernel.ledger["tickets"]["05"]
        self.assertEqual("verified", ticket["state"])
        self.assertEqual(leaf_results, ticket["leaf_results"])
        self.assertEqual(generation, ticket["artifact_generation"])
        self.assertIsNone(ticket["merge_authorization"])
        self.assertEqual(grant, self.kernel.ledger["autonomous_merge_grant"])
        self.assertEqual(
            list(("implement", "simplify", "review", "qa-plan", "qa-execute", "verify", "finalize")),
            ticket["validated_stages"],
        )
        receipt = ticket["delivery"]["reconcile-prepare"]
        self.assertEqual("equivalent", receipt["result"])
        self.assertEqual(asdict(self.candidate), receipt["old_semantic_ref"])
        self.assertEqual(asdict(self.candidate), receipt["new_semantic_ref"])

    def test_each_semantic_field_drift_requires_complete_revalidation(self) -> None:
        drifted_candidates = {
            "base": replace(self.candidate, base_tree_oid="different-base"),
            "child": replace(
                self.candidate, candidate_tree_oid="different-candidate"
            ),
            "ticket": replace(self.candidate, ticket_digest="different-ticket"),
        }
        for label, candidate in drifted_candidates.items():
            with self.subTest(label=label):
                self.setUp()
                self.assertFalse(self.prepare(candidate))
                ticket = self.kernel.ledger["tickets"]["05"]
                self.assertEqual("active", ticket["state"])
                self.assertEqual("review", ticket["stage"])
                self.assertEqual({}, ticket["leaf_results"])
                self.assertEqual(1, ticket["artifact_generation"])
                self.assertEqual(
                    "invalidated",
                    ticket["delivery"]["reconcile-prepare"]["result"],
                )
                phases = list(LEAF_PHASE_CONTRACTS["review"])
                self.kernel.record_leaf_result(
                    "05",
                    {
                        "schema": 3,
                        "complete": True,
                        "candidate_ref": asdict(candidate),
                        "stage": "review",
                        "phase_contract": phases,
                        "scope": {
                            "files_expected": ["change.py"],
                            "files_inspected": ["change.py"],
                            "files_remaining": [],
                        },
                        "phases_remaining": [],
                        "commands_run": [f"review:{label}"],
                        "findings": [
                            f"blocker:{label}: planted semantic drift rediscovered"
                        ],
                        "progress_phase": "handoff-ready",
                        "stop_reason": None,
                    },
                    candidate,
                    expected_files=["change.py"],
                )
                self.kernel.record_stage("05", "review", "fail", candidate)
                self.assertEqual(
                    1,
                    self.kernel.ledger["tickets"]["05"]["quality_failures"],
                )
                self.assertEqual(
                    "implement",
                    self.kernel.ledger["tickets"]["05"]["stage"],
                )
                self.assertEqual(
                    "autonomous", self.kernel.ledger["merge_policy"]
                )
                self.assertIsNone(self.kernel.pending_autonomous_merge_id())
                with self.assertRaisesRegex(
                    ProviderError,
                    "exact semantic candidate to be fully validated",
                ):
                    _autonomous_eligibility(
                        self.kernel,
                        "05",
                        runner=EligibilityRunner(pr_id="42", head_sha="rebased-head"),
                    )

    def test_contract_version_drift_fails_with_actionable_new_run_error(self) -> None:
        incompatible = replace(self.candidate, contract_version=1)

        with self.assertRaisesRegex(
            CandidateContractError,
            "start a new run with CandidateRef v2",
        ):
            self.prepare(incompatible)

    def test_active_legacy_ledger_is_rejected_without_silent_interpretation(self) -> None:
        legacy = copy.deepcopy(self.kernel.ledger)
        legacy["schema"] = 2

        with self.assertRaisesRegex(
            LedgerError,
            "incompatible with semantic CandidateRef v2",
        ):
            AtomicLedger._validate(legacy)

    def test_reconciliation_failure_is_persisted_as_a_durable_gate(self) -> None:
        ledger_path = Path(self.directory.name) / "gate-ledger.json"
        store = AtomicLedger(ledger_path)
        store.save(self.kernel.ledger)

        result = _reconciliation_gate(
            store,
            self.kernel,
            "05",
            category="stack-reconciliation",
            reason="remote branch diverged before stack reconciliation",
        )

        restored = AtomicLedger(ledger_path).load()
        gate = restored["gates"][result["gate_id"]]
        self.assertEqual("gated", result["result"])
        self.assertEqual("open", gate["state"])
        self.assertEqual("stack-reconciliation", gate["category"])
        self.assertEqual(
            "remote branch diverged before stack reconciliation",
            gate["reason"],
        )

    def test_three_ticket_stack_preserves_downstream_review_counts(self) -> None:
        root = Path(self.directory.name) / "stack"
        root.mkdir()
        tickets = {
            "01": Ticket("01", "AFK", (), root / "01.md", "ticket-01"),
            "02": Ticket("02", "AFK", ("01",), root / "02.md", "ticket-02"),
            "03": Ticket("03", "AFK", ("02",), root / "03.md", "ticket-03"),
        }
        kernel = Kernel.new(
            "three-ticket-stack",
            TicketGraph(
                folder=root,
                tickets=tickets,
                order=("01", "02", "03"),
                completed_ids=frozenset(),
            ),
            provider="github",
            repo="/repo",
            worktree="/tmp",
            merge_policy="autonomous",
            merge_actor="release-operator",
            merge_evidence="artifact://stack-grant",
        )
        candidates = {
            "01": SemanticCandidateRef("base", "tree-01", "ticket-01", 2),
            "02": SemanticCandidateRef("tree-01", "tree-02", "ticket-02", 2),
            "03": SemanticCandidateRef("tree-02", "tree-03", "ticket-03", 2),
        }

        def advance(ticket_id: str) -> None:
            fixed = candidates[ticket_id]
            kernel.activate(ticket_id, fixed)
            for stage in (
                "implement",
                "simplify",
                "review",
                "qa-plan",
                "qa-execute",
                "verify",
                "finalize",
            ):
                if stage in {"review", "qa-plan", "qa-execute", "verify"}:
                    phases = list(LEAF_PHASE_CONTRACTS[stage])
                    result = {
                        "schema": 3,
                        "complete": True,
                        "candidate_ref": asdict(fixed),
                        "stage": stage,
                        "phase_contract": phases,
                        "scope": {
                            "files_expected": [],
                            "files_inspected": [],
                            "files_remaining": [],
                        },
                        "phases_remaining": [],
                        "commands_run": [f"invoke:{ticket_id}:{stage}"],
                        "findings": [],
                        "progress_phase": "handoff-ready",
                        "stop_reason": None,
                    }
                    if stage in {"qa-plan", "qa-execute", "verify"}:
                        result["quality"] = {
                            "schema": 1,
                            "causal_scope": [stage],
                            "evidence": [
                                {
                                    "id": f"evidence:{ticket_id}:{stage}",
                                    "artifact": f"{ticket_id}-{stage}.json",
                                    "sha256": "b" * 64,
                                    "result": "pass",
                                    "candidate_ref": asdict(fixed),
                                }
                            ],
                            "limitations": ["local-only"],
                        }
                    kernel.record_leaf_result(
                        ticket_id,
                        result,
                        fixed,
                        expected_files=[],
                    )
                kernel.record_stage(ticket_id, stage, "pass", fixed)
            kernel.record_pr(
                ticket_id,
                provider="github",
                pr_id=ticket_id,
                branch=f"ticket/{ticket_id}",
                base_branch=("main" if ticket_id == "01" else f"ticket/{int(ticket_id) - 1:02d}"),
                base_sha=f"base-head-{ticket_id}",
                head_sha=f"head-{ticket_id}",
            )

        advance("01")
        advance("02")
        advance("03")
        before = {
            ticket_id: kernel.report()["tickets"][ticket_id]["budgets"][
                "leaf_interactions"
            ]["consumed"]
            for ticket_id in ("02", "03")
        }
        grant = copy.deepcopy(kernel.ledger["autonomous_merge_grant"])

        kernel.authorize_merge(
            "01", actor="human", head_sha="head-01", evidence="approval-01"
        )
        kernel.record_integration("01", expected_head_sha="head-01")
        kernel.authorize_merge(
            "02",
            actor="release-operator",
            head_sha="head-02",
            evidence="artifact://stack-grant",
            mode="autonomous",
        )
        self.assertTrue(
            kernel.prepare_reconciliation(
                "02",
                candidates["02"],
                old_head="head-02",
                new_head="rebased-head-02",
                base_branch="main",
                base_sha="merged-head-01",
                base_tree_oid="tree-01",
                expected_remote_sha="head-02",
            )
        )
        kernel.complete_reconciliation(
            "02",
            expected_old="head-02",
            new_head="rebased-head-02",
            base_branch="main",
        )
        self.assertIsNone(
            kernel.ledger["tickets"]["02"]["merge_authorization"]
        )
        eligibility = _autonomous_eligibility(
            kernel,
            "02",
            runner=EligibilityRunner(pr_id="02", head_sha="rebased-head-02"),
        )
        self.assertEqual("eligible", eligibility["status"])
        self.assertEqual("rebased-head-02", eligibility["head_sha"])
        self.assertEqual(grant, kernel.ledger["autonomous_merge_grant"])
        kernel.authorize_merge(
            "02",
            actor="human",
            head_sha="rebased-head-02",
            evidence="approval-02",
        )
        kernel.record_integration("02", expected_head_sha="rebased-head-02")
        self.assertTrue(
            kernel.prepare_reconciliation(
                "03",
                candidates["03"],
                old_head="head-03",
                new_head="rebased-head-03",
                base_branch="main",
                base_sha="merged-head-02",
                base_tree_oid="tree-02",
                expected_remote_sha="head-03",
            )
        )

        after = {
            ticket_id: kernel.report()["tickets"][ticket_id]["budgets"][
                "leaf_interactions"
            ]["consumed"]
            for ticket_id in ("02", "03")
        }
        self.assertEqual(before, after)
        self.assertEqual(
            ["reconciliation-equivalent", "reconciliation-equivalent"],
            [
                event["event"]
                for event in kernel.ledger["history"]
                if event["event"] == "reconciliation-equivalent"
            ],
        )


if __name__ == "__main__":
    unittest.main()
