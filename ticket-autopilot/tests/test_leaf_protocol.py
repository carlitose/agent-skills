from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from autopilot.leaf_protocol import (  # noqa: E402
    BudgetConfig,
    LEAF_PHASE_CONTRACTS,
    LeafProtocolError,
    budget_status,
    continuation_context,
    leaf_health,
    new_leaf_budget,
    record_leaf_result,
    validate_leaf_result,
)


CANDIDATE = {
    "contract_version": 1,
    "base_sha": "base-a",
    "tree_oid": "tree-a",
    "ticket_digest": "ticket-a",
}


def review_result(
    *,
    complete: bool,
    inspected: list[str],
    progress_phase: str,
    stop_reason: str | None,
    candidate: dict[str, object] | None = None,
    findings: list[str] | None = None,
) -> dict[str, object]:
    expected = ["a.py", "b.py"]
    contract = list(LEAF_PHASE_CONTRACTS["review"])
    return {
        "schema": 3,
        "complete": complete,
        "candidate_ref": candidate or CANDIDATE,
        "stage": "review",
        "phase_contract": contract,
        "scope": {
            "files_expected": expected,
            "files_inspected": inspected,
            "files_remaining": [path for path in expected if path not in inspected],
        },
        "phases_remaining": contract[contract.index(progress_phase) + 1 :],
        "commands_run": ["git diff --check"],
        "findings": findings or [],
        "progress_phase": progress_phase,
        "stop_reason": stop_reason,
    }


def qa_execute_result(*, complete: bool, phase: str) -> dict[str, object]:
    contract = list(LEAF_PHASE_CONTRACTS["qa-execute"])
    return {
        "schema": 3,
        "complete": complete,
        "candidate_ref": CANDIDATE,
        "stage": "qa-execute",
        "phase_contract": contract,
        "scope": {
            "files_expected": [],
            "files_inspected": [],
            "files_remaining": [],
        },
        "phases_remaining": contract[contract.index(phase) + 1 :],
        "commands_run": [],
        "findings": [],
        "progress_phase": phase,
        "stop_reason": None if complete else "interrupted",
    }


class BudgetConfigTests(unittest.TestCase):
    def test_defaults_preserve_quality_and_reserve_mandatory_stages(self) -> None:
        config = BudgetConfig().normalized()

        self.assertEqual(3, config["max_quality_failures"])
        self.assertEqual(10, config["max_leaf_interactions"])
        self.assertEqual({"qa-execute": 1, "verify": 1}, config["reservations"])

    def test_interaction_range_is_fail_closed(self) -> None:
        for value in (2, 101, True):
            with self.subTest(value=value):
                with self.assertRaises(LeafProtocolError):
                    BudgetConfig(max_leaf_interactions=value).normalized()

    def test_optional_resource_limits_require_positive_exact_integers(self) -> None:
        for value in (0, -1, True, 1.5):
            with self.subTest(value=value):
                with self.assertRaises(LeafProtocolError):
                    BudgetConfig(max_leaf_tool_calls=value).normalized()
                with self.assertRaises(LeafProtocolError):
                    BudgetConfig(max_leaf_wall_time=value).normalized()

    def test_reservations_are_exact_and_order_independent(self) -> None:
        accepted = BudgetConfig(
            reservations={"verify": 1, "qa-execute": 1}
        ).normalized()
        self.assertEqual({"verify": 1, "qa-execute": 1}, accepted["reservations"])
        for reservations in (
            {},
            {"qa-execute": 1},
            {"qa-execute": 1, "verify": 2},
            {"qa-execute": True, "verify": 1},
            {"qa-execute": 1.0, "verify": 1},
            {"qa-execute": 1, "verify": 1, "review": 1},
        ):
            with self.subTest(reservations=reservations):
                with self.assertRaises(LeafProtocolError):
                    BudgetConfig(reservations=reservations).normalized()

    def test_unconfigured_resource_dimensions_are_reported_unavailable(self) -> None:
        config = BudgetConfig().normalized()
        status = budget_status(config, new_leaf_budget(config))

        self.assertEqual("unavailable", status["leaf_tool_calls"]["enforcement"])
        self.assertEqual("unavailable", status["leaf_wall_time"]["enforcement"])
        self.assertEqual(2, status["leaf_interactions"]["reserved_remaining"])
        self.assertEqual(8, status["leaf_interactions"]["unreserved_remaining"])

    def test_review_retries_cannot_consume_mandatory_reservations(self) -> None:
        config = BudgetConfig(max_leaf_interactions=3).normalized()
        budget = new_leaf_budget(config)
        partial = review_result(
            complete=False,
            inspected=["a.py"],
            progress_phase="diff-inspected",
            stop_reason="interrupted",
        )

        budget, _, _ = record_leaf_result(
            config,
            budget,
            partial,
            expected_candidate_ref=CANDIDATE,
            expected_stage="review",
        )
        with self.assertRaisesRegex(
            LeafProtocolError, "reserved for mandatory stages"
        ):
            record_leaf_result(
                config,
                budget,
                partial,
                expected_candidate_ref=CANDIDATE,
                expected_stage="review",
            )
        status = budget_status(config, budget)
        self.assertEqual(2, status["leaf_interactions"]["reserved_remaining"])

    def test_partial_mandatory_stage_can_resume_from_unreserved_capacity(self) -> None:
        config = BudgetConfig(max_leaf_interactions=5).normalized()
        budget = new_leaf_budget(config)

        budget, _, _ = record_leaf_result(
            config,
            budget,
            qa_execute_result(complete=False, phase="context-loaded"),
            expected_candidate_ref=CANDIDATE,
            expected_stage="qa-execute",
        )
        self.assertEqual(
            {"reserved": 1, "consumed": 1, "complete": False},
            budget["reservations"]["qa-execute"],
        )

        budget, _, _ = record_leaf_result(
            config,
            budget,
            qa_execute_result(complete=True, phase="handoff-ready"),
            expected_candidate_ref=CANDIDATE,
            expected_stage="qa-execute",
        )

        self.assertEqual(2, budget["interactions_consumed"])
        self.assertEqual(
            {"reserved": 1, "consumed": 1, "complete": True},
            budget["reservations"]["qa-execute"],
        )
        self.assertEqual(0, budget["reservations"]["verify"]["consumed"])

    def test_partial_mandatory_stage_cannot_spend_another_reservation(self) -> None:
        config = BudgetConfig(max_leaf_interactions=3).normalized()
        budget = new_leaf_budget(config)
        budget, _, _ = record_leaf_result(
            config,
            budget,
            review_result(
                complete=True,
                inspected=["a.py", "b.py"],
                progress_phase="handoff-ready",
                stop_reason=None,
            ),
            expected_candidate_ref=CANDIDATE,
            expected_stage="review",
        )
        budget, _, _ = record_leaf_result(
            config,
            budget,
            qa_execute_result(complete=False, phase="context-loaded"),
            expected_candidate_ref=CANDIDATE,
            expected_stage="qa-execute",
        )
        before = copy.deepcopy(budget)

        with self.assertRaisesRegex(
            LeafProtocolError, "reserved for mandatory stages"
        ):
            record_leaf_result(
                config,
                budget,
                qa_execute_result(complete=True, phase="handoff-ready"),
                expected_candidate_ref=CANDIDATE,
                expected_stage="qa-execute",
            )

        self.assertEqual(before, budget)


class LeafResultTests(unittest.TestCase):
    def test_complete_review_requires_complete_scope_and_phase_contract(self) -> None:
        result = review_result(
            complete=True,
            inspected=["a.py", "b.py"],
            progress_phase="handoff-ready",
            stop_reason=None,
        )

        self.assertEqual(result, validate_leaf_result(result))

    def test_partial_review_round_trips_remaining_scope(self) -> None:
        result = review_result(
            complete=False,
            inspected=["a.py"],
            progress_phase="diff-inspected",
            stop_reason="wall-time-budget",
        )

        continuation = continuation_context(
            result, candidate_ref=CANDIDATE
        )

        self.assertEqual(["b.py"], continuation["files_remaining"])
        self.assertEqual(["a.py"], continuation["files_already_inspected"])
        self.assertEqual(
            ["findings-normalized", "handoff-ready"],
            continuation["phases_remaining"],
        )
        self.assertEqual("timed-out", leaf_health(result))

    def test_candidate_drift_invalidates_partial_handoff(self) -> None:
        result = review_result(
            complete=False,
            inspected=["a.py"],
            progress_phase="diff-inspected",
            stop_reason="interrupted",
        )
        drifted = {**CANDIDATE, "tree_oid": "tree-b"}

        with self.assertRaisesRegex(LeafProtocolError, "stale"):
            continuation_context(result, candidate_ref=drifted)

    def test_remaining_files_are_derived_not_trusted(self) -> None:
        result = review_result(
            complete=False,
            inspected=["a.py"],
            progress_phase="diff-inspected",
            stop_reason="interrupted",
        )
        result["scope"]["files_remaining"] = []

        with self.assertRaisesRegex(LeafProtocolError, "ordered expected"):
            validate_leaf_result(result)

    def test_inspected_files_preserve_manifest_order(self) -> None:
        result = review_result(
            complete=True,
            inspected=["b.py", "a.py"],
            progress_phase="handoff-ready",
            stop_reason=None,
        )

        with self.assertRaisesRegex(LeafProtocolError, "canonical expected-file"):
            validate_leaf_result(result)

    def test_remaining_phases_must_be_exact_suffix(self) -> None:
        result = review_result(
            complete=False,
            inspected=["a.py", "b.py"],
            progress_phase="diff-inspected",
            stop_reason="interrupted",
        )
        result["phases_remaining"] = ["handoff-ready"]

        with self.assertRaisesRegex(LeafProtocolError, "canonical suffix"):
            validate_leaf_result(result)

    def test_partial_handoff_requires_resumable_work(self) -> None:
        result = review_result(
            complete=False,
            inspected=["a.py", "b.py"],
            progress_phase="handoff-ready",
            stop_reason="interaction-budget",
        )

        with self.assertRaisesRegex(LeafProtocolError, "resumable work"):
            validate_leaf_result(result)

    def test_schema_requires_an_exact_supported_integer(self) -> None:
        result = review_result(
            complete=True,
            inspected=["a.py", "b.py"],
            progress_phase="handoff-ready",
            stop_reason=None,
        )

        for malformed_schema in (3.0, True, "3", None, [], 4):
            malformed = copy.deepcopy(result)
            malformed["schema"] = malformed_schema
            with self.subTest(schema=malformed_schema):
                with self.assertRaisesRegex(
                    LeafProtocolError, "schema must be an integer|must be 3"
                ):
                    validate_leaf_result(malformed)

    def test_json_types_fail_closed(self) -> None:
        result = review_result(
            complete=True,
            inspected=["a.py", "b.py"],
            progress_phase="handoff-ready",
            stop_reason=None,
        )
        for field, value in (
            ("complete", 1),
            ("commands_run", "git diff"),
            ("findings", None),
        ):
            malformed = copy.deepcopy(result)
            malformed[field] = value
            with self.subTest(field=field):
                with self.assertRaises(LeafProtocolError):
                    validate_leaf_result(malformed)

    def test_resource_deltas_are_admitted_atomically(self) -> None:
        config = BudgetConfig(
            max_leaf_tool_calls=3,
            max_leaf_wall_time=20,
        ).normalized()
        budget = new_leaf_budget(config)
        complete = review_result(
            complete=True,
            inspected=["a.py", "b.py"],
            progress_phase="handoff-ready",
            stop_reason=None,
        )

        updated, normalized, progress = record_leaf_result(
            config,
            budget,
            complete,
            expected_candidate_ref=CANDIDATE,
            expected_stage="review",
            tool_calls=2,
            wall_time=12,
        )

        self.assertEqual(0, budget["interactions_consumed"])
        self.assertEqual(1, updated["interactions_consumed"])
        self.assertEqual(2, updated["tool_calls_consumed"])
        self.assertEqual(12, updated["wall_time_consumed"])
        self.assertTrue(normalized["complete"])
        self.assertEqual("handoff-ready", progress["phase"])

    def test_failed_resource_admission_does_not_mutate_budget(self) -> None:
        config = BudgetConfig(max_leaf_tool_calls=1).normalized()
        budget = new_leaf_budget(config)
        before = copy.deepcopy(budget)
        partial = review_result(
            complete=False,
            inspected=["a.py"],
            progress_phase="diff-inspected",
            stop_reason="tool-call-budget",
        )

        with self.assertRaisesRegex(LeafProtocolError, "tool-call budget"):
            record_leaf_result(
                config,
                budget,
                partial,
                expected_candidate_ref=CANDIDATE,
                expected_stage="review",
                tool_calls=2,
            )
        self.assertEqual(before, budget)


if __name__ == "__main__":
    unittest.main()
