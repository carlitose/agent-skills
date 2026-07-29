from __future__ import annotations

import json
import unittest

from model import (
    BudgetConfig,
    BudgetExhausted,
    BudgetState,
    CandidateRef,
    LEAF_PHASE_CONTRACTS,
    LeafHandoff,
    LedgerVersionError,
    ProgressEvent,
    ProgressLog,
    PrototypeError,
    QualityFailureLimit,
    StaleCandidate,
    issue_nine_shape,
    new_ledger,
    sample_candidate,
    validate_ledger,
)


def stage_progress(
    candidate: CandidateRef, stage: str = "review"
) -> ProgressLog:
    return ProgressLog(
        candidate,
        stage=stage,
        phase_contract=LEAF_PHASE_CONTRACTS[stage],
    )


def stage_event(
    phase: str,
    completed: int,
    total: int,
    candidate: CandidateRef,
    stage: str = "review",
) -> ProgressEvent:
    return ProgressEvent(
        phase,
        completed,
        total,
        candidate,
        stage=stage,
        phase_contract=LEAF_PHASE_CONTRACTS[stage],
    )


class BudgetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.candidate = sample_candidate()

    def test_quality_failures_and_interactions_are_orthogonal(self) -> None:
        state = BudgetState(BudgetConfig(max_quality_failures=2), self.candidate)
        state.consume_leaf(
            "review", candidate_ref=self.candidate, tool_calls=3, wall_time_ms=20
        )
        state.record_quality_failure(candidate_ref=self.candidate)

        report = state.report()
        self.assertEqual(1, report["leaf_interactions"]["used"])
        self.assertEqual(1, report["quality_failures"]["used"])
        self.assertEqual(3, report["tool_calls"]["used"])

    def test_quality_limit_becomes_terminal_at_threshold(self) -> None:
        state = BudgetState(BudgetConfig(max_quality_failures=2), self.candidate)
        state.record_quality_failure(candidate_ref=self.candidate)
        with self.assertRaisesRegex(QualityFailureLimit, "quality-failure-limit"):
            state.record_quality_failure(candidate_ref=self.candidate)
        self.assertEqual(2, state.quality_failures)

    def test_restored_quality_terminal_state_rejects_more_leaves(self) -> None:
        state = BudgetState(
            BudgetConfig(max_quality_failures=1), self.candidate
        )
        with self.assertRaises(QualityFailureLimit):
            state.record_quality_failure(candidate_ref=self.candidate)
        restored = validate_ledger(
            json.loads(
                json.dumps(
                    new_ledger(state, stage_progress(self.candidate))
                )
            ),
            self.candidate,
        )
        with self.assertRaises(QualityFailureLimit):
            restored.budget.consume_leaf(
                "review", candidate_ref=self.candidate
            )
        self.assertEqual([], restored.budget.interactions)

    def test_reservations_protect_qa_and_verification(self) -> None:
        state = BudgetState(
            BudgetConfig(max_leaf_interactions=4), self.candidate
        )
        state.consume_leaf("implement", candidate_ref=self.candidate)
        state.consume_leaf("review", candidate_ref=self.candidate)
        with self.assertRaisesRegex(BudgetExhausted, "reserved-capacity"):
            state.consume_leaf("review", candidate_ref=self.candidate)

        state.consume_leaf("qa-execute", candidate_ref=self.candidate)
        state.complete_mandatory("qa-execute", candidate_ref=self.candidate)
        state.consume_leaf("verify", candidate_ref=self.candidate)
        state.complete_mandatory("verify", candidate_ref=self.candidate)
        self.assertEqual(4, state.report()["leaf_interactions"]["used"])

    def test_both_mandatory_reservations_are_required_exactly_once(self) -> None:
        invalid = (
            (),
            (("qa-execute", 1),),
            (("verify", 1),),
            (("qa-execute", 1), ("verify", 2)),
            (("verify", 1), ("qa-execute", 1)),
        )
        for reservations in invalid:
            with self.subTest(reservations=reservations):
                with self.assertRaisesRegex(
                    PrototypeError, "exactly one qa-execute and one verify"
                ):
                    BudgetConfig(reservations=reservations).validate()

    def test_configuration_must_leave_capacity_before_reservations(self) -> None:
        with self.assertRaisesRegex(PrototypeError, "3..100"):
            BudgetConfig(max_leaf_interactions=2).validate()

    def test_optional_tool_and_wall_budgets_are_hard_when_configured(self) -> None:
        unavailable = BudgetState(BudgetConfig(), self.candidate).report()
        self.assertEqual("unavailable", unavailable["tool_calls"]["enforcement"])
        self.assertEqual("unavailable", unavailable["wall_time_ms"]["enforcement"])

        tool_limited = BudgetState(
            BudgetConfig(max_leaf_tool_calls=2), self.candidate
        )
        self.assertEqual("hard", tool_limited.report()["tool_calls"]["enforcement"])
        with self.assertRaisesRegex(BudgetExhausted, "tool-call-budget"):
            tool_limited.consume_leaf(
                "review", candidate_ref=self.candidate, tool_calls=3
            )

        wall_limited = BudgetState(
            BudgetConfig(max_leaf_wall_time_ms=10), self.candidate
        )
        self.assertEqual(
            "hard", wall_limited.report()["wall_time_ms"]["enforcement"]
        )
        with self.assertRaisesRegex(BudgetExhausted, "wall-time-budget"):
            wall_limited.consume_leaf(
                "review", candidate_ref=self.candidate, wall_time_ms=11
            )

    def test_live_resource_deltas_require_non_negative_exact_integers(
        self,
    ) -> None:
        invalid = (
            {"tool_calls": True},
            {"tool_calls": 1.5},
            {"wall_time_ms": True},
            {"wall_time_ms": 0.5},
            {"tool_calls": -1},
            {"wall_time_ms": -1},
        )
        for values in invalid:
            state = BudgetState(BudgetConfig(), self.candidate)
            with self.subTest(values=values):
                with self.assertRaisesRegex(
                    PrototypeError, "exact integers|cannot be negative"
                ):
                    state.consume_leaf(
                        "review",
                        candidate_ref=self.candidate,
                        **values,
                    )
                self.assertEqual([], state.interactions)
                self.assertEqual(0, state.tool_calls)
                self.assertEqual(0, state.wall_time_ms)

    def test_wall_time_exhaustion_is_caused_by_limit_transition(self) -> None:
        state = BudgetState(
            BudgetConfig(max_leaf_wall_time_ms=500), self.candidate
        )
        state.consume_leaf(
            "implement", candidate_ref=self.candidate, wall_time_ms=450
        )
        state.consume_leaf(
            "review", candidate_ref=self.candidate, wall_time_ms=50
        )
        with self.assertRaisesRegex(BudgetExhausted, "wall-time-budget"):
            state.consume_leaf(
                "review", candidate_ref=self.candidate, wall_time_ms=1
            )
        self.assertEqual(500, state.wall_time_ms)

    def test_candidate_drift_rejects_ledger_mutation(self) -> None:
        state = BudgetState(BudgetConfig(), self.candidate)
        with self.assertRaises(StaleCandidate):
            state.consume_leaf("review", candidate_ref=sample_candidate("b"))
        self.assertEqual([], state.interactions)


class HandoffTests(unittest.TestCase):
    def partial(self) -> LeafHandoff:
        return LeafHandoff(
            candidate_ref=sample_candidate(),
            complete=False,
            stage="review",
            phase_contract=(
                "context-loaded",
                "diff-inspected",
                "findings-normalized",
                "handoff-ready",
            ),
            files_expected=("a.py", "b.py", "c.py"),
            files_inspected=("a.py", "b.py"),
            files_remaining=("c.py",),
            phases_remaining=(
                "findings-normalized",
                "handoff-ready",
            ),
            commands_run=("python -m unittest test_a",),
            findings=(),
            progress_phase="diff-inspected",
            stop_reason="wall-time-budget",
        )

    def test_partial_handoff_round_trips_and_derives_remaining_work(self) -> None:
        restored = LeafHandoff.from_document(
            json.loads(json.dumps(self.partial().to_document()))
        )
        self.assertEqual(
            (
                "inspect c.py",
                "advance findings-normalized",
                "advance handoff-ready",
            ),
            restored.continuation(sample_candidate()),
        )
        self.assertEqual(("c.py",), restored.files_remaining)

    def test_remaining_scope_must_equal_expected_minus_inspected(self) -> None:
        with self.assertRaisesRegex(PrototypeError, "expected scope minus"):
            LeafHandoff(
                candidate_ref=sample_candidate(),
                complete=False,
                stage="review",
                phase_contract=(
                    "context-loaded",
                    "diff-inspected",
                    "findings-normalized",
                    "handoff-ready",
                ),
                files_expected=("a.py", "b.py"),
                files_inspected=("a.py",),
                files_remaining=("a.py",),
                phases_remaining=(
                    "findings-normalized",
                    "handoff-ready",
                ),
                commands_run=(),
                findings=(),
                progress_phase="diff-inspected",
                stop_reason="interaction-budget",
            ).validate()

    def test_candidate_change_invalidates_partial_handoff(self) -> None:
        with self.assertRaises(StaleCandidate):
            self.partial().continuation(sample_candidate("changed"))

    def test_complete_handoff_requires_complete_scope(self) -> None:
        handoff = LeafHandoff(
            candidate_ref=sample_candidate(),
            complete=True,
            stage="review",
            phase_contract=(
                "context-loaded",
                "diff-inspected",
                "findings-normalized",
                "handoff-ready",
            ),
            files_expected=("a.py", "b.py"),
            files_inspected=("a.py", "b.py"),
            files_remaining=(),
            phases_remaining=(),
            commands_run=("python -m unittest",),
            findings=(),
            progress_phase="handoff-ready",
            stop_reason=None,
        )
        handoff.validate()
        self.assertEqual((), handoff.continuation(sample_candidate()))

    def test_late_phase_partial_handoff_carries_deterministic_phase_work(
        self,
    ) -> None:
        handoff = LeafHandoff(
            candidate_ref=sample_candidate(),
            complete=False,
            stage="verify",
            phase_contract=(
                "context-loaded",
                "bundle-built",
                "bundle-validated",
                "bundle-reduced",
                "handoff-ready",
            ),
            files_expected=("a.py",),
            files_inspected=("a.py",),
            files_remaining=(),
            phases_remaining=("bundle-reduced", "handoff-ready"),
            commands_run=("python -m unittest",),
            findings=("one normalized finding",),
            progress_phase="bundle-validated",
            stop_reason="interaction-budget",
        )
        restored = LeafHandoff.from_document(
            json.loads(json.dumps(handoff.to_document()))
        )
        self.assertEqual(
            ("advance bundle-reduced", "advance handoff-ready"),
            restored.continuation(sample_candidate()),
        )

    def test_remaining_phases_must_match_progress_suffix(self) -> None:
        document = self.partial().to_document()
        document["phases_remaining"] = ["handoff-ready"]
        with self.assertRaisesRegex(PrototypeError, "ordered phases after"):
            LeafHandoff.from_document(document)

    def test_review_handoff_uses_only_its_persisted_stage_contract(self) -> None:
        handoff = LeafHandoff(
            candidate_ref=sample_candidate(),
            complete=False,
            stage="review",
            phase_contract=(
                "context-loaded",
                "diff-inspected",
                "findings-normalized",
                "handoff-ready",
            ),
            files_expected=("a.py",),
            files_inspected=("a.py",),
            files_remaining=(),
            phases_remaining=("findings-normalized", "handoff-ready"),
            commands_run=(),
            findings=(),
            progress_phase="diff-inspected",
            stop_reason="interaction-budget",
        )
        handoff.validate()
        self.assertEqual(
            (
                "advance findings-normalized",
                "advance handoff-ready",
            ),
            handoff.continuation(sample_candidate()),
        )

    def test_stage_contract_cannot_claim_another_leaf_phase(self) -> None:
        document = self.partial().to_document()
        document["phase_contract"].insert(-1, "qa-plan-built")
        document["phases_remaining"].insert(-1, "qa-plan-built")
        with self.assertRaisesRegex(PrototypeError, "canonical contract for stage"):
            LeafHandoff.from_document(document)

    def test_unknown_handoff_fields_fail_closed(self) -> None:
        document = self.partial().to_document()
        document["surprise"] = True
        with self.assertRaisesRegex(PrototypeError, "unknown or missing"):
            LeafHandoff.from_document(document)

    def test_malformed_handoff_field_types_fail_closed(self) -> None:
        mutations = (
            lambda document: document["scope"].__setitem__(
                "files_expected", "a.py"
            ),
            lambda document: document.__setitem__(
                "commands_run", "python -m unittest"
            ),
            lambda document: document.__setitem__(
                "phases_remaining", "handoff-ready"
            ),
            lambda document: document.__setitem__("findings", [1]),
            lambda document: document.__setitem__("complete", 1),
            lambda document: document.__setitem__("stop_reason", 7),
        )
        for mutate in mutations:
            document = self.partial().to_document()
            mutate(document)
            with self.subTest(document=document):
                with self.assertRaises(PrototypeError):
                    LeafHandoff.from_document(document)


class ProgressTests(unittest.TestCase):
    def setUp(self) -> None:
        self.candidate = sample_candidate()

    def test_progress_is_idempotent_and_monotonic(self) -> None:
        log = stage_progress(self.candidate)
        first = stage_event("context-loaded", 1, 1, self.candidate)
        second = stage_event("diff-inspected", 1, 2, self.candidate)
        log.record(first)
        log.record(first)
        log.record(second)
        log.record(stage_event("diff-inspected", 2, 2, self.candidate))
        self.assertEqual(3, len(log.events))

        restored = ProgressLog.from_document(
            json.loads(json.dumps(log.to_document()))
        )
        restored.validate_candidate(self.candidate)
        self.assertEqual(log.events, restored.events)

    def test_progress_regression_fails(self) -> None:
        log = stage_progress(self.candidate)
        log.record(stage_event("diff-inspected", 1, 1, self.candidate))
        with self.assertRaisesRegex(PrototypeError, "cannot regress"):
            log.record(stage_event("context-loaded", 1, 1, self.candidate))

    def test_candidate_drift_invalidates_progress(self) -> None:
        log = stage_progress(self.candidate)
        with self.assertRaises(StaleCandidate):
            log.record(
                stage_event(
                    "context-loaded", 1, 1, sample_candidate("changed")
                )
            )
        self.assertEqual([], log.events)

    def test_review_progress_rejects_another_stage_phase(self) -> None:
        review_contract = (
            "context-loaded",
            "diff-inspected",
            "findings-normalized",
            "handoff-ready",
        )
        log = stage_progress(self.candidate)
        with self.assertRaisesRegex(PrototypeError, "outside the progress stage"):
            log.record(
                ProgressEvent(
                    "bundle-built",
                    1,
                    1,
                    self.candidate,
                    stage="review",
                    phase_contract=review_contract,
                )
            )


class LedgerTests(unittest.TestCase):
    def test_schema_two_persists_evolved_accounting_progress_and_handoff(
        self,
    ) -> None:
        candidate = sample_candidate()
        budget = BudgetState(BudgetConfig(), candidate)
        budget.consume_leaf(
            "review", candidate_ref=candidate, tool_calls=2, wall_time_ms=20
        )
        budget.record_quality_failure(candidate_ref=candidate)
        progress = stage_progress(candidate)
        progress.record(stage_event("context-loaded", 1, 1, candidate))
        progress.record(stage_event("diff-inspected", 1, 2, candidate))
        handoff = LeafHandoff(
            candidate_ref=candidate,
            complete=False,
            stage="review",
            phase_contract=(
                "context-loaded",
                "diff-inspected",
                "findings-normalized",
                "handoff-ready",
            ),
            files_expected=("a.py", "b.py"),
            files_inspected=("a.py",),
            files_remaining=("b.py",),
            phases_remaining=(
                "findings-normalized",
                "handoff-ready",
            ),
            commands_run=("python -m unittest",),
            findings=("one should-fix",),
            progress_phase="diff-inspected",
            stop_reason="wall-time-budget",
        )
        ledger = new_ledger(budget, progress, handoff)
        restored = validate_ledger(
            json.loads(json.dumps(ledger)), candidate
        )
        self.assertEqual(["review"], restored.budget.interactions)
        self.assertEqual(1, restored.budget.quality_failures)
        self.assertEqual(2, restored.budget.tool_calls)
        self.assertEqual(20, restored.budget.wall_time_ms)
        self.assertEqual(2, len(restored.progress.events))
        self.assertIsNotNone(restored.handoff)
        assert restored.handoff is not None
        self.assertEqual(
            (
                "inspect b.py",
                "advance findings-normalized",
                "advance handoff-ready",
            ),
            restored.handoff.continuation(candidate),
        )

    def test_schema_one_requires_explicit_migration_or_new_run(self) -> None:
        with self.assertRaisesRegex(
            LedgerVersionError, "explicit migration or a new run"
        ):
            validate_ledger({"schema": 1}, sample_candidate())

    def test_candidate_change_invalidates_ledger(self) -> None:
        candidate = sample_candidate()
        ledger = new_ledger(
            BudgetState(BudgetConfig(), candidate),
            stage_progress(candidate),
        )
        with self.assertRaises(StaleCandidate):
            validate_ledger(ledger, sample_candidate("changed"))

    def test_schema_two_rejects_inconsistent_persisted_accounting(self) -> None:
        candidate = sample_candidate()
        ledger = new_ledger(
            BudgetState(BudgetConfig(), candidate),
            stage_progress(candidate),
        )
        ledger["budget"]["reserved_consumed"]["qa-execute"] = 1
        with self.assertRaisesRegex(PrototypeError, "accounting is inconsistent"):
            validate_ledger(ledger, candidate)

    def test_schema_two_rejects_empty_persisted_reservation_mapping(self) -> None:
        candidate = sample_candidate()
        ledger = new_ledger(
            BudgetState(BudgetConfig(), candidate),
            stage_progress(candidate),
        )
        ledger["budget"]["reserved_consumed"] = {}
        with self.assertRaisesRegex(PrototypeError, "stages are incomplete"):
            validate_ledger(ledger, candidate)

    def test_schema_two_rejects_history_that_spends_mandatory_capacity(
        self,
    ) -> None:
        candidate = sample_candidate()
        budget = BudgetState(
            BudgetConfig(max_leaf_interactions=4), candidate
        )
        ledger = new_ledger(budget, stage_progress(candidate))
        ledger["budget"]["interactions"] = ["review", "review", "review"]
        with self.assertRaisesRegex(PrototypeError, "mandatory capacity"):
            validate_ledger(ledger, candidate)

    def test_schema_two_reconciles_handoff_with_latest_progress(self) -> None:
        candidate = sample_candidate()
        progress = stage_progress(candidate)
        progress.record(stage_event("context-loaded", 1, 1, candidate))
        handoff = LeafHandoff(
            candidate_ref=candidate,
            complete=False,
            stage="review",
            phase_contract=(
                "context-loaded",
                "diff-inspected",
                "findings-normalized",
                "handoff-ready",
            ),
            files_expected=("a.py",),
            files_inspected=(),
            files_remaining=("a.py",),
            phases_remaining=(
                "findings-normalized",
                "handoff-ready",
            ),
            commands_run=(),
            findings=(),
            progress_phase="diff-inspected",
            stop_reason="wall-time-budget",
        )
        with self.assertRaisesRegex(
            PrototypeError, "differs from latest progress"
        ):
            new_ledger(
                BudgetState(BudgetConfig(), candidate), progress, handoff
            )

    def test_snapshot_rejects_progress_from_another_stage(self) -> None:
        candidate = sample_candidate()
        progress = stage_progress(candidate, "verify")
        progress.record(stage_event("context-loaded", 1, 1, candidate, "verify"))
        handoff = LeafHandoff(
            candidate_ref=candidate,
            complete=False,
            stage="review",
            phase_contract=LEAF_PHASE_CONTRACTS["review"],
            files_expected=("a.py",),
            files_inspected=(),
            files_remaining=("a.py",),
            phases_remaining=(
                "diff-inspected",
                "findings-normalized",
                "handoff-ready",
            ),
            commands_run=(),
            findings=(),
            progress_phase="context-loaded",
            stop_reason="interaction-budget",
        )
        with self.assertRaisesRegex(PrototypeError, "stage contracts differ"):
            new_ledger(
                BudgetState(BudgetConfig(), candidate), progress, handoff
            )

    def test_complete_verify_handoff_requires_completed_reservation(self) -> None:
        candidate = sample_candidate()
        progress = stage_progress(candidate, "verify")
        progress.record(stage_event("context-loaded", 1, 1, candidate, "verify"))
        progress.record(stage_event("handoff-ready", 1, 1, candidate, "verify"))
        handoff = LeafHandoff(
            candidate_ref=candidate,
            complete=True,
            stage="verify",
            phase_contract=LEAF_PHASE_CONTRACTS["verify"],
            files_expected=("a.py",),
            files_inspected=("a.py",),
            files_remaining=(),
            phases_remaining=(),
            commands_run=(),
            findings=(),
            progress_phase="handoff-ready",
            stop_reason=None,
        )
        with self.assertRaisesRegex(
            PrototypeError, "completed mandatory reservation"
        ):
            new_ledger(
                BudgetState(BudgetConfig(), candidate), progress, handoff
            )

    def test_schema_two_rejects_duplicate_persisted_progress(self) -> None:
        candidate = sample_candidate()
        progress = stage_progress(candidate)
        progress.record(stage_event("context-loaded", 1, 1, candidate))
        budget = BudgetState(BudgetConfig(), candidate)
        budget.consume_leaf("review", candidate_ref=candidate)
        ledger = new_ledger(budget, progress)
        ledger["progress"]["events"].append(
            json.loads(json.dumps(ledger["progress"]["events"][0]))
        )
        with self.assertRaisesRegex(PrototypeError, "duplicate events"):
            validate_ledger(ledger, candidate)

    def test_candidate_contract_stays_version_one(self) -> None:
        candidate = CandidateRef("base", "tree", "ticket")
        candidate.validate()
        with self.assertRaisesRegex(PrototypeError, "unsupported CandidateRef"):
            CandidateRef(
                "base", "tree", "ticket", contract_version=2
            ).validate()

    def test_issue_nine_fixture_models_two_independent_tickets(self) -> None:
        scenario = issue_nine_shape()
        ticket_a = scenario["tickets"]["A"]
        ticket_b = scenario["tickets"]["B"]
        self.assertEqual(9, ticket_a["budget"]["leaf_interactions"]["used"])
        self.assertEqual(0, ticket_a["budget"]["quality_failures"]["used"])
        self.assertEqual(10, ticket_b["budget"]["leaf_interactions"]["used"])
        self.assertEqual(1, ticket_b["budget"]["quality_failures"]["used"])
        self.assertEqual(
            ["expired state blocker", "kill-switch should-fix"],
            ticket_b["findings"],
        )
        self.assertTrue(scenario["cross_ticket_blocker_preserved"])


if __name__ == "__main__":
    unittest.main()
