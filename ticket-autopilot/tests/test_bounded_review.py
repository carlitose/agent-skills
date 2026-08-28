from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from autopilot.cli import build_parser  # noqa: E402
from autopilot.kernel import CandidateRef, Kernel, TransitionError  # noqa: E402
from autopilot.leaf_protocol import LEAF_PHASE_CONTRACTS  # noqa: E402
from autopilot.ledger import AtomicLedger, LedgerError  # noqa: E402
from autopilot.ticket_contract import Ticket, TicketGraph  # noqa: E402


def graph(root: Path) -> TicketGraph:
    ticket = Ticket(
        ticket_id="01",
        execution_mode="AFK",
        blocked_by=(),
        path=root / "01.md",
        digest="ticket-a",
    )
    return TicketGraph(
        folder=root,
        tickets={"01": ticket},
        order=("01",),
        completed_ids=frozenset(),
    )


def candidate(suffix: str = "a") -> CandidateRef:
    return CandidateRef(
        base_tree_oid=f"base-{suffix}",
        candidate_tree_oid=f"tree-{suffix}",
        ticket_digest=f"ticket-{suffix}",
        contract_version=2,
    )


def review_result(
    fixed: CandidateRef,
    *,
    complete: bool,
    inspected: list[str],
    phase: str,
    stop_reason: str | None,
    findings: list[str] | None = None,
) -> dict[str, object]:
    expected = ["a.py", "b.py"]
    contract = list(LEAF_PHASE_CONTRACTS["review"])
    return {
        "schema": 3,
        "complete": complete,
        "candidate_ref": asdict(fixed),
        "stage": "review",
        "phase_contract": contract,
        "scope": {
            "files_expected": expected,
            "files_inspected": inspected,
            "files_remaining": [path for path in expected if path not in inspected],
        },
        "phases_remaining": contract[contract.index(phase) + 1 :],
        "commands_run": [],
        "findings": findings or [],
        "progress_phase": phase,
        "stop_reason": stop_reason,
    }


class BoundedReviewKernelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.fixed = candidate()
        self.kernel = Kernel.new("bounded-review", graph(self.root))
        self.kernel.activate("01", self.fixed)
        self.kernel.record_stage("01", "implement", "pass", self.fixed)
        self.kernel.record_stage("01", "simplify", "pass", self.fixed)

    def test_review_pass_requires_structured_complete_handoff(self) -> None:
        with self.assertRaisesRegex(TransitionError, "structured leaf handoff"):
            self.kernel.record_stage("01", "review", "pass", self.fixed)

        self.kernel.record_leaf_result(
            "01",
            review_result(
                self.fixed,
                complete=True,
                inspected=["a.py", "b.py"],
                phase="handoff-ready",
                stop_reason=None,
            ),
            self.fixed,
            expected_files=["a.py", "b.py"],
            tool_calls=2,
            wall_time=7,
        )
        self.kernel.record_stage("01", "review", "pass", self.fixed)

        self.assertEqual(
            ["implement", "simplify", "review"],
            self.kernel.ledger["tickets"]["01"]["validated_stages"],
        )
        report = self.kernel.report()["tickets"]["01"]
        self.assertEqual(1, report["budgets"]["leaf_interactions"]["consumed"])
        self.assertEqual(2, report["budgets"]["leaf_tool_calls"]["consumed"])
        self.assertEqual("complete", report["leaf_progress"]["health"])

    def test_review_scope_must_match_the_authoritative_manifest(self) -> None:
        result = review_result(
            self.fixed,
            complete=True,
            inspected=[],
            phase="handoff-ready",
            stop_reason=None,
        )
        result["scope"] = {
            "files_expected": [],
            "files_inspected": [],
            "files_remaining": [],
        }
        with self.assertRaisesRegex(TransitionError, "diff manifest"):
            self.kernel.record_leaf_result(
                "01",
                result,
                self.fixed,
                expected_files=["a.py"],
            )

    def test_partial_review_is_non_passing_and_resumable(self) -> None:
        self.kernel.record_leaf_result(
            "01",
            review_result(
                self.fixed,
                complete=False,
                inspected=["a.py"],
                phase="diff-inspected",
                stop_reason="interrupted",
            ),
            self.fixed,
            expected_files=["a.py", "b.py"],
        )

        ticket = self.kernel.ledger["tickets"]["01"]
        self.assertEqual("review", ticket["stage"])
        self.assertEqual(0, ticket["quality_failures"])
        self.assertEqual(
            ["b.py"],
            self.kernel.review_continuation("01", self.fixed)["files_remaining"],
        )
        with self.assertRaisesRegex(TransitionError, "partial scope"):
            self.kernel.record_stage("01", "review", "pass", self.fixed)

    def test_real_finding_is_separate_from_resource_exhaustion(self) -> None:
        self.kernel.record_leaf_result(
            "01",
            review_result(
                self.fixed,
                complete=False,
                inspected=["a.py"],
                phase="diff-inspected",
                stop_reason="wall-time-budget",
            ),
            self.fixed,
            expected_files=["a.py", "b.py"],
        )
        self.assertEqual(0, self.kernel.ledger["tickets"]["01"]["quality_failures"])

        self.kernel.record_leaf_result(
            "01",
            review_result(
                self.fixed,
                complete=True,
                inspected=["a.py", "b.py"],
                phase="handoff-ready",
                stop_reason=None,
                findings=["blocker:a.py: unsafe transition"],
            ),
            self.fixed,
            expected_files=["a.py", "b.py"],
        )
        self.kernel.record_stage("01", "review", "fail", self.fixed)

        ticket = self.kernel.ledger["tickets"]["01"]
        self.assertEqual(1, ticket["quality_failures"])
        self.assertEqual("implement", ticket["stage"])

    def test_candidate_drift_starts_fresh_budget_and_keeps_lifetime_usage(self) -> None:
        self.kernel.record_leaf_result(
            "01",
            review_result(
                self.fixed,
                complete=False,
                inspected=["a.py"],
                phase="diff-inspected",
                stop_reason="interrupted",
            ),
            self.fixed,
            expected_files=["a.py", "b.py"],
        )
        drifted = candidate("b")

        self.kernel.invalidate_for_candidate_drift("01", drifted)

        ticket = self.kernel.ledger["tickets"]["01"]
        self.assertIsNone(ticket["leaf_handoff"])
        self.assertEqual([], ticket["leaf_progress_events"])
        self.assertEqual(0, ticket["leaf_budget"]["interactions_consumed"])
        self.assertIsNone(self.kernel.review_continuation("01", drifted))

        self.kernel.adopt_implementation_candidate("01", candidate("c"))
        verbosity = self.kernel.report()["tickets"]["01"]["verbosity"]
        self.assertEqual(1, verbosity["candidate_invalidations"])
        self.assertEqual(1, verbosity["leaf_interactions"])

    def test_mandatory_reservations_remain_after_review_retry(self) -> None:
        self.kernel.record_leaf_result(
            "01",
            review_result(
                self.fixed,
                complete=False,
                inspected=[],
                phase="context-loaded",
                stop_reason="interrupted",
            ),
            self.fixed,
            expected_files=["a.py", "b.py"],
        )

        reservations = self.kernel.report()["tickets"]["01"]["budgets"][
            "reservations"
        ]
        self.assertEqual(
            {
                "qa-execute": {"reserved": 1, "consumed": 0, "complete": False},
                "verify": {"reserved": 1, "consumed": 0, "complete": False},
            },
            reservations,
        )

    def test_history_replay_preserves_partial_handoff_and_budget(self) -> None:
        self.kernel.record_leaf_result(
            "01",
            review_result(
                self.fixed,
                complete=False,
                inspected=["a.py"],
                phase="diff-inspected",
                stop_reason="timeout",
            ),
            self.fixed,
            expected_files=["a.py", "b.py"],
            tool_calls=1,
            wall_time=5,
        )
        ledger_path = self.root / "ledger.json"
        store = AtomicLedger(ledger_path)

        store.save(self.kernel.ledger)
        restored = Kernel(store.load())

        self.assertEqual(self.kernel.report(), restored.report())
        self.assertEqual(
            ["b.py"],
            restored.review_continuation("01", self.fixed)["files_remaining"],
        )

    def test_report_is_deterministic_and_does_not_append_progress(self) -> None:
        self.kernel.record_leaf_result(
            "01",
            review_result(
                self.fixed,
                complete=False,
                inspected=["a.py"],
                phase="diff-inspected",
                stop_reason="interrupted",
            ),
            self.fixed,
            expected_files=["a.py", "b.py"],
        )
        before = copy.deepcopy(self.kernel.ledger)

        first = self.kernel.report()
        second = self.kernel.report()

        self.assertEqual(first, second)
        self.assertEqual(before, self.kernel.ledger)
        self.assertEqual(1, first["tickets"]["01"]["leaf_progress"]["events"])

    def test_identical_handoff_replay_is_idempotent(self) -> None:
        partial = review_result(
            self.fixed,
            complete=False,
            inspected=["a.py"],
            phase="diff-inspected",
            stop_reason="interrupted",
        )
        self.kernel.record_leaf_result(
            "01",
            partial,
            self.fixed,
            expected_files=["a.py", "b.py"],
            tool_calls=1,
            wall_time=3,
        )
        before = copy.deepcopy(self.kernel.ledger)

        replayed = self.kernel.record_leaf_result(
            "01",
            partial,
            self.fixed,
            expected_files=["a.py", "b.py"],
            tool_calls=1,
            wall_time=3,
        )

        self.assertEqual(partial, replayed)
        self.assertEqual(before, self.kernel.ledger)

    def test_duplicate_handoff_still_validates_exact_resource_types(self) -> None:
        partial = review_result(
            self.fixed,
            complete=False,
            inspected=["a.py"],
            phase="diff-inspected",
            stop_reason="interrupted",
        )
        self.kernel.record_leaf_result(
            "01",
            partial,
            self.fixed,
            expected_files=["a.py", "b.py"],
            tool_calls=1,
            wall_time=3,
        )
        before = copy.deepcopy(self.kernel.ledger)

        for tool_calls, wall_time in ((True, 3), (1, 3.0)):
            with self.subTest(tool_calls=tool_calls, wall_time=wall_time):
                with self.assertRaisesRegex(TransitionError, "must be an integer"):
                    self.kernel.record_leaf_result(
                        "01",
                        partial,
                        self.fixed,
                        expected_files=["a.py", "b.py"],
                        tool_calls=tool_calls,
                        wall_time=wall_time,
                    )
                self.assertEqual(before, self.kernel.ledger)

    def test_follow_up_cannot_regress_scope_or_progress(self) -> None:
        self.kernel.record_leaf_result(
            "01",
            review_result(
                self.fixed,
                complete=False,
                inspected=["a.py"],
                phase="diff-inspected",
                stop_reason="interrupted",
            ),
            self.fixed,
            expected_files=["a.py", "b.py"],
        )
        before = copy.deepcopy(self.kernel.ledger)
        regressed = review_result(
            self.fixed,
            complete=False,
            inspected=[],
            phase="context-loaded",
            stop_reason="interrupted",
        )

        with self.assertRaisesRegex(TransitionError, "regressed inspected"):
            self.kernel.record_leaf_result(
                "01",
                regressed,
                self.fixed,
                expected_files=["a.py", "b.py"],
            )
        self.assertEqual(before, self.kernel.ledger)

    def test_schema_one_requires_new_run_or_explicit_migration(self) -> None:
        legacy = copy.deepcopy(self.kernel.ledger)
        legacy["schema"] = 1

        with self.assertRaisesRegex(
            TransitionError, "new run or use an explicit validated migration"
        ):
            Kernel(legacy)

    def test_ledger_and_envelope_schemas_require_exact_integers(self) -> None:
        malformed_payload = copy.deepcopy(self.kernel.ledger)
        malformed_payload["schema"] = 2.0
        with self.assertRaisesRegex(LedgerError, "ledger schema is incompatible"):
            AtomicLedger._validate(malformed_payload)

        path = self.root / "schema-ledger.json"
        AtomicLedger(path).save(self.kernel.ledger)
        envelope = json.loads(path.read_text())
        envelope["envelope_schema"] = 1.0
        path.write_text(json.dumps(envelope))
        with self.assertRaisesRegex(LedgerError, "integrity envelope is invalid"):
            AtomicLedger(path).load()


class BoundedReviewCliTests(unittest.TestCase):
    def test_run_accepts_orthogonal_resource_budgets(self) -> None:
        args = build_parser().parse_args(
            [
                "run",
                "tickets",
                "--max-quality-failures",
                "4",
                "--max-leaf-interactions",
                "12",
                "--max-leaf-tool-calls",
                "30",
                "--max-leaf-wall-time",
                "600",
            ]
        )

        self.assertEqual(4, args.max_quality_failures)
        self.assertEqual(12, args.max_leaf_interactions)
        self.assertEqual(30, args.max_leaf_tool_calls)
        self.assertEqual(600, args.max_leaf_wall_time)

    def test_invalid_budget_fails_before_a_ledger_can_be_constructed(self) -> None:
        with self.assertRaisesRegex(TransitionError, "between 3 and 100"):
            Kernel.new(
                "invalid-budget",
                graph(self.root if hasattr(self, "root") else Path(".")),
                max_leaf_interactions=2,
            )


if __name__ == "__main__":
    unittest.main()
