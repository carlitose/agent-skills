from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from autopilot.kernel import CandidateRef, Kernel, TransitionError  # noqa: E402
from autopilot.leaf_protocol import LEAF_PHASE_CONTRACTS  # noqa: E402
from autopilot.ticket_contract import Ticket, TicketGraph  # noqa: E402


def graph(root: Path) -> TicketGraph:
    return TicketGraph(
        folder=root,
        tickets={
            "01": Ticket(
                ticket_id="01",
                path=root / "01.md",
                blocked_by=(),
                execution_mode="AFK",
                digest="ticket",
            )
        },
        order=("01",),
        completed_ids=frozenset(),
    )


def candidate(suffix: str = "a") -> CandidateRef:
    return CandidateRef(
        base_tree_oid=f"base-{suffix}",
        candidate_tree_oid=f"tree-{suffix}",
        ticket_digest="ticket",
        contract_version=2,
    )


def leaf_result(
    fixed: CandidateRef,
    stage: str,
    *,
    complete: bool,
    phase: str,
) -> dict[str, object]:
    contract = list(LEAF_PHASE_CONTRACTS[stage])
    document: dict[str, object] = {
        "schema": 3,
        "complete": complete,
        "candidate_ref": {
            "base_tree_oid": fixed.base_tree_oid,
            "candidate_tree_oid": fixed.candidate_tree_oid,
            "ticket_digest": fixed.ticket_digest,
            "contract_version": fixed.contract_version,
        },
        "stage": stage,
        "phase_contract": contract,
        "scope": {
            "files_expected": [],
            "files_inspected": [],
            "files_remaining": [],
        },
        "phases_remaining": contract[contract.index(phase) + 1 :],
        "commands_run": [f"run:{stage}"],
        "findings": [],
        "progress_phase": phase,
        "stop_reason": None if complete else "interrupted",
    }
    if stage in {"qa-plan", "qa-execute", "verify"}:
        document["quality"] = {
            "schema": 1,
            "causal_scope": [f"scope:{stage}"],
            "evidence": [
                {
                    "id": f"evidence:{stage}",
                    "artifact": f"artifacts/{stage}.json",
                    "sha256": "a" * 64,
                    "result": "pass" if complete else "planned",
                    "candidate_ref": document["candidate_ref"],
                }
            ],
            "limitations": ["local-only"],
        }
    return document


class CheckpointQaVerificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.fixed = candidate()
        self.kernel = Kernel.new("checkpoint-qa", graph(Path(self.directory.name)))
        self.kernel.activate("01", self.fixed)
        self.kernel.record_stage("01", "implement", "pass", self.fixed)
        self.kernel.record_stage("01", "simplify", "pass", self.fixed)

    def record_complete(self, stage: str) -> None:
        self.kernel.record_leaf_result(
            "01",
            leaf_result(
                self.fixed,
                stage,
                complete=True,
                phase="handoff-ready",
            ),
            self.fixed,
            expected_files=[],
        )
        self.kernel.record_stage("01", stage, "pass", self.fixed)

    def test_quality_stages_require_structured_causal_evidence(self) -> None:
        self.record_complete("review")
        malformed = leaf_result(
            self.fixed,
            "qa-plan",
            complete=True,
            phase="handoff-ready",
        )
        del malformed["quality"]

        with self.assertRaisesRegex(TransitionError, "quality"):
            self.kernel.record_leaf_result(
                "01",
                malformed,
                self.fixed,
                expected_files=[],
            )

    def test_qa_and_verify_resume_preserve_mandatory_reservations(self) -> None:
        self.record_complete("review")
        partial_plan = leaf_result(
            self.fixed,
            "qa-plan",
            complete=False,
            phase="context-loaded",
        )
        self.kernel.record_leaf_result(
            "01",
            partial_plan,
            self.fixed,
            expected_files=[],
        )
        with self.assertRaisesRegex(TransitionError, "partial"):
            self.kernel.record_stage("01", "qa-plan", "pass", self.fixed)
        self.record_complete("qa-plan")

        partial_qa = leaf_result(
            self.fixed,
            "qa-execute",
            complete=False,
            phase="context-loaded",
        )
        self.kernel.record_leaf_result(
            "01",
            partial_qa,
            self.fixed,
            expected_files=[],
        )
        reservation = self.kernel.ledger["tickets"]["01"]["leaf_budget"][
            "reservations"
        ]["qa-execute"]
        self.assertEqual(
            {"reserved": 1, "consumed": 1, "complete": False},
            reservation,
        )
        self.record_complete("qa-execute")
        self.record_complete("verify")

        reservations = self.kernel.ledger["tickets"]["01"]["leaf_budget"][
            "reservations"
        ]
        self.assertTrue(reservations["qa-execute"]["complete"])
        self.assertTrue(reservations["verify"]["complete"])
        self.assertEqual(
            {"review", "qa-plan", "qa-execute", "verify"},
            set(self.kernel.ledger["tickets"]["01"]["leaf_results"]),
        )

    def test_candidate_drift_clears_all_semantic_leaf_artifacts(self) -> None:
        self.record_complete("review")
        self.record_complete("qa-plan")
        self.kernel.record_leaf_result(
            "01",
            leaf_result(
                self.fixed,
                "qa-execute",
                complete=False,
                phase="context-loaded",
            ),
            self.fixed,
            expected_files=[],
        )

        self.kernel.invalidate_for_candidate_drift("01", candidate("b"))

        ticket = self.kernel.ledger["tickets"]["01"]
        self.assertEqual({}, ticket["leaf_results"])
        self.assertIsNone(ticket["leaf_handoff"])
        self.assertEqual([], ticket["leaf_progress_events"])


if __name__ == "__main__":
    unittest.main()
