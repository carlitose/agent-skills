"""Run seven deterministic, simulated protocol scenarios."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from model import (
    BudgetConfig,
    BudgetExhausted,
    BudgetState,
    CandidateRef,
    LEAF_PHASE_CONTRACTS,
    LeafHandoff,
    ProgressEvent,
    ProgressLog,
    QualityFailureLimit,
    StaleCandidate,
    issue_nine_shape,
    new_ledger,
    sample_candidate,
    validate_ledger,
)


def stage_progress(candidate: CandidateRef, stage: str) -> ProgressLog:
    return ProgressLog(
        candidate,
        stage=stage,
        phase_contract=LEAF_PHASE_CONTRACTS[stage],
    )


def stage_event(
    phase: str,
    candidate: CandidateRef,
    stage: str,
    *,
    completed: int = 1,
    total: int = 1,
) -> ProgressEvent:
    return ProgressEvent(
        phase,
        completed,
        total,
        candidate,
        stage=stage,
        phase_contract=LEAF_PHASE_CONTRACTS[stage],
    )


def bounded_success() -> dict[str, Any]:
    candidate = sample_candidate("success")
    state = BudgetState(BudgetConfig(), candidate)
    for stage in ("implement", "simplify", "review", "qa-execute", "verify"):
        state.consume_leaf(stage, candidate_ref=candidate)
    state.complete_mandatory("qa-execute", candidate_ref=candidate)
    state.complete_mandatory("verify", candidate_ref=candidate)

    progress = stage_progress(candidate, "verify")
    progress.record(stage_event("context-loaded", candidate, "verify"))
    progress.record(stage_event("handoff-ready", candidate, "verify"))
    handoff = LeafHandoff(
        candidate_ref=candidate,
        complete=True,
        stage="verify",
        phase_contract=(
            "context-loaded",
            "bundle-built",
            "bundle-validated",
            "bundle-reduced",
            "handoff-ready",
        ),
        files_expected=("model.py",),
        files_inspected=("model.py",),
        files_remaining=(),
        phases_remaining=(),
        commands_run=("python -m unittest",),
        findings=(),
        progress_phase="handoff-ready",
        stop_reason=None,
    )
    ledger = new_ledger(state, progress, handoff)
    restored = validate_ledger(json.loads(json.dumps(ledger)), candidate)
    return {
        "result": "pass",
        "ledger_schema": ledger["schema"],
        "persisted_interactions": restored.budget.interactions,
        "persisted_progress_events": len(restored.progress.events),
        "budget": restored.budget.report(),
    }


def reservation_pressure() -> dict[str, Any]:
    candidate = sample_candidate("reserve")
    state = BudgetState(BudgetConfig(max_leaf_interactions=4), candidate)
    state.consume_leaf("implement", candidate_ref=candidate)
    state.consume_leaf("review", candidate_ref=candidate)
    try:
        state.consume_leaf("review", candidate_ref=candidate)
    except BudgetExhausted as error:
        blocked = str(error)
    else:
        raise AssertionError("review consumed mandatory reservations")

    state.consume_leaf("qa-execute", candidate_ref=candidate)
    state.complete_mandatory("qa-execute", candidate_ref=candidate)
    state.consume_leaf("verify", candidate_ref=candidate)
    state.complete_mandatory("verify", candidate_ref=candidate)
    return {
        "result": "pass",
        "blocked_cause": blocked,
        "reservations": state.report()["reservations"],
    }


def distinct_failure_causes() -> dict[str, Any]:
    candidate = sample_candidate("causes")
    quality = BudgetState(BudgetConfig(max_quality_failures=1), candidate)
    try:
        quality.record_quality_failure(candidate_ref=candidate)
    except QualityFailureLimit as error:
        quality_cause = str(error)
    else:
        raise AssertionError("quality threshold was not terminal")

    resource = BudgetState(
        BudgetConfig(max_leaf_wall_time_ms=10), candidate
    )
    try:
        resource.consume_leaf(
            "review", candidate_ref=candidate, wall_time_ms=11
        )
    except BudgetExhausted as error:
        resource_cause = str(error)
    else:
        raise AssertionError("resource limit admitted an over-budget leaf")

    if quality_cause == resource_cause:
        raise AssertionError("quality and resource causes were conflated")
    return {
        "result": "pass",
        "quality_cause": quality_cause,
        "resource_cause": resource_cause,
    }


def timeout_resume() -> dict[str, Any]:
    candidate = sample_candidate("timeout")
    state = BudgetState(
        BudgetConfig(max_leaf_wall_time_ms=500), candidate
    )
    state.consume_leaf(
        "review", candidate_ref=candidate, wall_time_ms=450
    )
    state.consume_leaf(
        "review", candidate_ref=candidate, wall_time_ms=50
    )
    try:
        state.consume_leaf(
            "review", candidate_ref=candidate, wall_time_ms=1
        )
    except BudgetExhausted as error:
        stop_reason = str(error)
    else:
        raise AssertionError("wall-time transition did not exhaust the budget")

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
        files_expected=("a.py", "b.py", "c.py"),
        files_inspected=("a.py", "b.py"),
        files_remaining=("c.py",),
        phases_remaining=(
            "findings-normalized",
            "handoff-ready",
        ),
        commands_run=("python -m unittest",),
        findings=(),
        progress_phase="diff-inspected",
        stop_reason=stop_reason,
    )
    progress = stage_progress(candidate, "review")
    progress.record(stage_event("context-loaded", candidate, "review"))
    progress.record(
        stage_event(
            "diff-inspected",
            candidate,
            "review",
            completed=2,
            total=3,
        )
    )
    restored = validate_ledger(
        json.loads(json.dumps(new_ledger(state, progress, handoff))),
        candidate,
    )
    if restored.handoff is None:
        raise AssertionError("partial continuation state was not persisted")
    return {
        "result": "pass",
        "observed_wall_time_ms": state.wall_time_ms,
        "rejected_increment_ms": 1,
        "stop_reason": stop_reason,
        "continuation": list(restored.handoff.continuation(candidate)),
        "persisted_interactions": list(restored.budget.interactions),
        "persisted_progress_events": len(restored.progress.events),
    }


def late_phase_resume() -> dict[str, Any]:
    candidate = sample_candidate("late-phase")
    state = BudgetState(
        BudgetConfig(max_leaf_tool_calls=2), candidate
    )
    state.consume_leaf(
        "verify", candidate_ref=candidate, tool_calls=1
    )
    try:
        state.consume_leaf(
            "verify", candidate_ref=candidate, tool_calls=2
        )
    except BudgetExhausted as error:
        stop_reason = str(error)
    else:
        raise AssertionError("late-phase tool budget did not stop the leaf")
    progress = stage_progress(candidate, "verify")
    for phase in (
        "context-loaded",
        "bundle-built",
        "bundle-validated",
    ):
        progress.record(stage_event(phase, candidate, "verify"))
    handoff = LeafHandoff(
        candidate_ref=candidate,
        complete=False,
        stage="verify",
        phase_contract=(
            "context-loaded",
            "bundle-built",
            "bundle-validated",
            "bundle-reduced",
            "handoff-ready",
        ),
        files_expected=("model.py",),
        files_inspected=("model.py",),
        files_remaining=(),
        phases_remaining=("bundle-reduced", "handoff-ready"),
        commands_run=("python -m unittest",),
        findings=("one normalized finding",),
        progress_phase="bundle-validated",
        stop_reason=stop_reason,
    )
    restored = validate_ledger(
        json.loads(json.dumps(new_ledger(state, progress, handoff))),
        candidate,
    )
    if restored.handoff is None:
        raise AssertionError("late-phase continuation state was not persisted")
    continuation = restored.handoff.continuation(candidate)
    restored.budget.consume_leaf(
        "verify", candidate_ref=candidate, tool_calls=1
    )
    restored.budget.complete_mandatory(
        "verify", candidate_ref=candidate
    )
    restored.progress.record(
        stage_event("bundle-reduced", candidate, "verify")
    )
    restored.progress.record(
        stage_event("handoff-ready", candidate, "verify")
    )
    completed = LeafHandoff(
        candidate_ref=candidate,
        complete=True,
        stage="verify",
        phase_contract=(
            "context-loaded",
            "bundle-built",
            "bundle-validated",
            "bundle-reduced",
            "handoff-ready",
        ),
        files_expected=("model.py",),
        files_inspected=("model.py",),
        files_remaining=(),
        phases_remaining=(),
        commands_run=("python -m unittest",),
        findings=("one normalized finding",),
        progress_phase="handoff-ready",
        stop_reason=None,
    )
    validate_ledger(
        json.loads(
            json.dumps(new_ledger(restored.budget, restored.progress, completed))
        ),
        candidate,
    )
    return {
        "result": "pass",
        "continuation": list(continuation),
        "completed": True,
        "stop_reason": stop_reason,
        "resumed_interactions": list(restored.budget.interactions),
        "tool_calls": restored.budget.tool_calls,
    }


def candidate_drift() -> dict[str, Any]:
    candidate = sample_candidate("frozen")
    changed = sample_candidate("changed")
    stale_artifacts: list[str] = []

    state = BudgetState(BudgetConfig(), candidate)
    try:
        state.consume_leaf("review", candidate_ref=changed)
    except StaleCandidate:
        stale_artifacts.append("ledger")

    progress = stage_progress(candidate, "review")
    try:
        progress.record(stage_event("context-loaded", changed, "review"))
    except StaleCandidate:
        stale_artifacts.append("progress")

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
            "diff-inspected",
            "findings-normalized",
            "handoff-ready",
        ),
        commands_run=(),
        findings=(),
        progress_phase="context-loaded",
        stop_reason="interaction-budget",
    )
    try:
        handoff.continuation(changed)
    except StaleCandidate:
        stale_artifacts.append("handoff")

    if stale_artifacts != ["ledger", "progress", "handoff"]:
        raise AssertionError("candidate drift did not invalidate every artifact")
    return {"result": "pass", "stale_artifacts": stale_artifacts}


def issue_nine_pressure() -> dict[str, Any]:
    result = issue_nine_shape()
    result["result"] = "pass"
    return result


SCENARIOS: tuple[tuple[str, Callable[[], dict[str, Any]]], ...] = (
    ("bounded-success", bounded_success),
    ("reservation-pressure", reservation_pressure),
    ("distinct-failure-causes", distinct_failure_causes),
    ("timeout-resume", timeout_resume),
    ("late-phase-resume", late_phase_resume),
    ("candidate-drift", candidate_drift),
    ("issue-9-pressure", issue_nine_pressure),
)


def main() -> int:
    results = [
        {"scenario": name, **run()}
        for name, run in SCENARIOS
    ]
    overall = "pass" if all(item["result"] == "pass" for item in results) else "fail"
    print(
        json.dumps(
            {
                "evidence_class": "simulated",
                "scenario_count": len(results),
                "overall": overall,
                "scenarios": results,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if overall == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
