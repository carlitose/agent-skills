"""Disposable bounded-leaf protocol model for ticket-autopilot."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


LEDGER_SCHEMA = 2
LEAF_RESULT_SCHEMA = 3
MANDATORY_STAGES = ("qa-execute", "verify")
LEAF_PHASE_CONTRACTS = {
    "implement": (
        "context-loaded",
        "diff-inspected",
        "handoff-ready",
    ),
    "simplify": (
        "context-loaded",
        "diff-inspected",
        "findings-normalized",
        "handoff-ready",
    ),
    "review": (
        "context-loaded",
        "diff-inspected",
        "findings-normalized",
        "handoff-ready",
    ),
    "qa-plan": (
        "context-loaded",
        "diff-inspected",
        "qa-plan-built",
        "handoff-ready",
    ),
    "qa-execute": (
        "context-loaded",
        "qa-executed",
        "handoff-ready",
    ),
    "verify": (
        "context-loaded",
        "bundle-built",
        "bundle-validated",
        "bundle-reduced",
        "handoff-ready",
    ),
}


def _validate_phase_contract(stage: Any, phase_contract: Any) -> None:
    if not isinstance(stage, str) or stage not in LEAF_PHASE_CONTRACTS:
        raise PrototypeError("unknown leaf stage contract")
    if not isinstance(phase_contract, tuple) or any(
        not isinstance(phase, str) or not phase
        for phase in phase_contract
    ):
        raise PrototypeError("phase_contract must contain non-empty strings")
    if phase_contract != LEAF_PHASE_CONTRACTS[stage]:
        raise PrototypeError(
            "phase_contract must equal the canonical contract for stage"
        )


class PrototypeError(RuntimeError):
    """Base class for a fail-closed protocol error."""


class BudgetExhausted(PrototypeError):
    """A resource budget cannot admit another leaf."""


class QualityFailureLimit(PrototypeError):
    """The candidate reached its independent quality-failure limit."""


class StaleCandidate(PrototypeError):
    """A semantic artifact belongs to another CandidateRef."""


class LedgerVersionError(PrototypeError):
    """A persisted ledger uses an unsupported schema."""


@dataclass(frozen=True)
class CandidateRef:
    base_sha: str
    tree_oid: str
    ticket_digest: str
    contract_version: int = 1

    def validate(self) -> None:
        if type(self.contract_version) is not int or self.contract_version != 1:
            raise PrototypeError("unsupported CandidateRef contract version")
        for name in ("base_sha", "tree_oid", "ticket_digest"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise PrototypeError(f"CandidateRef {name} must be non-empty")

    def to_document(self) -> dict[str, Any]:
        self.validate()
        return {
            "contract_version": self.contract_version,
            "base_sha": self.base_sha,
            "tree_oid": self.tree_oid,
            "ticket_digest": self.ticket_digest,
        }

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> CandidateRef:
        expected = {"contract_version", "base_sha", "tree_oid", "ticket_digest"}
        if not isinstance(document, dict) or set(document) != expected:
            raise PrototypeError("invalid CandidateRef document")
        candidate = cls(
            contract_version=document["contract_version"],
            base_sha=document["base_sha"],
            tree_oid=document["tree_oid"],
            ticket_digest=document["ticket_digest"],
        )
        candidate.validate()
        return candidate


def _require_candidate(expected: CandidateRef, actual: CandidateRef) -> None:
    expected.validate()
    actual.validate()
    if actual != expected:
        raise StaleCandidate("artifact is stale for the current CandidateRef")


@dataclass(frozen=True)
class BudgetConfig:
    max_quality_failures: int = 3
    max_leaf_interactions: int = 10
    max_leaf_tool_calls: int | None = None
    max_leaf_wall_time_ms: int | None = None
    reservations: tuple[tuple[str, int], ...] = (
        ("qa-execute", 1),
        ("verify", 1),
    )

    def validate(self) -> None:
        if (
            type(self.max_quality_failures) is not int
            or not 1 <= self.max_quality_failures <= 100
        ):
            raise PrototypeError("max_quality_failures must be in 1..100")
        if (
            type(self.max_leaf_interactions) is not int
            or not 3 <= self.max_leaf_interactions <= 100
        ):
            raise PrototypeError("max_leaf_interactions must be in 3..100")
        for name in ("max_leaf_tool_calls", "max_leaf_wall_time_ms"):
            value = getattr(self, name)
            if value is not None and (type(value) is not int or value < 1):
                raise PrototypeError(f"{name} must be null or a positive integer")

        if self.reservations != (("qa-execute", 1), ("verify", 1)) or any(
            not isinstance(stage, str) or type(amount) is not int
            for stage, amount in self.reservations
        ):
            raise PrototypeError(
                "reservations must contain exactly one qa-execute and one verify slot"
            )
        if sum(amount for _, amount in self.reservations) >= self.max_leaf_interactions:
            raise PrototypeError("reservations leave no capacity for earlier leaves")

    def reservation_for(self, stage: str) -> int:
        return dict(self.reservations).get(stage, 0)


@dataclass
class BudgetState:
    config: BudgetConfig
    candidate_ref: CandidateRef
    interactions: list[str] = field(default_factory=list)
    quality_failures: int = 0
    tool_calls: int = 0
    wall_time_ms: int = 0
    reserved_consumed: dict[str, int] = field(default_factory=dict)
    mandatory_completed: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        self.config.validate()
        self.candidate_ref.validate()
        if not self.reserved_consumed:
            self.reserved_consumed = {stage: 0 for stage in MANDATORY_STAGES}

    @property
    def remaining_interactions(self) -> int:
        return self.config.max_leaf_interactions - len(self.interactions)

    def outstanding_reservations(self) -> int:
        return sum(
            self.config.reservation_for(stage) - self.reserved_consumed[stage]
            for stage in MANDATORY_STAGES
            if stage not in self.mandatory_completed
        )

    def validate_candidate(self, current_candidate: CandidateRef) -> None:
        _require_candidate(self.candidate_ref, current_candidate)

    def consume_leaf(
        self,
        stage: str,
        *,
        candidate_ref: CandidateRef,
        tool_calls: int = 0,
        wall_time_ms: int = 0,
    ) -> None:
        self.validate_candidate(candidate_ref)
        if self.quality_failures >= self.config.max_quality_failures:
            raise QualityFailureLimit("quality-failure-limit")
        if not isinstance(stage, str) or not stage:
            raise PrototypeError("leaf stage must be non-empty")
        if type(tool_calls) is not int or type(wall_time_ms) is not int:
            raise PrototypeError("resource consumption must use exact integers")
        if tool_calls < 0 or wall_time_ms < 0:
            raise PrototypeError("resource consumption cannot be negative")

        projected_interactions = len(self.interactions) + 1
        if projected_interactions > self.config.max_leaf_interactions:
            raise BudgetExhausted("leaf-interaction-budget")

        projected_tools = self.tool_calls + tool_calls
        if (
            self.config.max_leaf_tool_calls is not None
            and projected_tools > self.config.max_leaf_tool_calls
        ):
            raise BudgetExhausted("tool-call-budget")

        projected_wall_time = self.wall_time_ms + wall_time_ms
        if (
            self.config.max_leaf_wall_time_ms is not None
            and projected_wall_time > self.config.max_leaf_wall_time_ms
        ):
            raise BudgetExhausted("wall-time-budget")

        uses_reservation = (
            stage in MANDATORY_STAGES
            and self.reserved_consumed[stage] < self.config.reservation_for(stage)
        )
        outstanding_after = self.outstanding_reservations() - int(uses_reservation)
        if self.config.max_leaf_interactions - projected_interactions < outstanding_after:
            raise BudgetExhausted("reserved-capacity")

        self.interactions.append(stage)
        self.tool_calls = projected_tools
        self.wall_time_ms = projected_wall_time
        if uses_reservation:
            self.reserved_consumed[stage] += 1

    def complete_mandatory(
        self, stage: str, *, candidate_ref: CandidateRef
    ) -> None:
        self.validate_candidate(candidate_ref)
        if stage not in MANDATORY_STAGES:
            raise PrototypeError(f"{stage} is not a mandatory stage")
        if self.reserved_consumed[stage] < 1:
            raise PrototypeError(f"{stage} has not consumed its reserved leaf")
        self.mandatory_completed.add(stage)

    def record_quality_failure(self, *, candidate_ref: CandidateRef) -> None:
        self.validate_candidate(candidate_ref)
        if self.quality_failures >= self.config.max_quality_failures:
            raise QualityFailureLimit("quality-failure-limit")
        self.quality_failures += 1
        if self.quality_failures >= self.config.max_quality_failures:
            raise QualityFailureLimit("quality-failure-limit")

    def report(self) -> dict[str, Any]:
        return {
            "schema": LEDGER_SCHEMA,
            "candidate_ref": self.candidate_ref.to_document(),
            "leaf_interactions": {
                "used": len(self.interactions),
                "limit": self.config.max_leaf_interactions,
                "remaining": self.remaining_interactions,
            },
            "quality_failures": {
                "used": self.quality_failures,
                "limit": self.config.max_quality_failures,
            },
            "tool_calls": {
                "used": self.tool_calls,
                "limit": self.config.max_leaf_tool_calls,
                "enforcement": (
                    "hard"
                    if self.config.max_leaf_tool_calls is not None
                    else "unavailable"
                ),
            },
            "wall_time_ms": {
                "used": self.wall_time_ms,
                "limit": self.config.max_leaf_wall_time_ms,
                "enforcement": (
                    "hard"
                    if self.config.max_leaf_wall_time_ms is not None
                    else "unavailable"
                ),
            },
            "reservations": {
                stage: {
                    "reserved": self.config.reservation_for(stage),
                    "consumed": self.reserved_consumed[stage],
                    "completed": stage in self.mandatory_completed,
                }
                for stage in MANDATORY_STAGES
            },
        }

    def to_document(self) -> dict[str, Any]:
        return {
            "candidate_ref": self.candidate_ref.to_document(),
            "interactions": list(self.interactions),
            "quality_failures": self.quality_failures,
            "tool_calls": self.tool_calls,
            "wall_time_ms": self.wall_time_ms,
            "reserved_consumed": dict(self.reserved_consumed),
            "mandatory_completed": sorted(self.mandatory_completed),
        }

    @classmethod
    def from_document(
        cls,
        config: BudgetConfig,
        document: dict[str, Any],
        current_candidate: CandidateRef,
    ) -> BudgetState:
        expected = {
            "candidate_ref",
            "interactions",
            "quality_failures",
            "tool_calls",
            "wall_time_ms",
            "reserved_consumed",
            "mandatory_completed",
        }
        if not isinstance(document, dict) or set(document) != expected:
            raise PrototypeError("invalid persisted budget state")
        if not isinstance(document["interactions"], list):
            raise PrototypeError("persisted interactions must be a list")
        if (
            not isinstance(document["reserved_consumed"], dict)
            or set(document["reserved_consumed"]) != set(MANDATORY_STAGES)
        ):
            raise PrototypeError("persisted reservation stages are incomplete")
        if not isinstance(document["mandatory_completed"], list):
            raise PrototypeError("persisted mandatory completion must be a list")
        candidate = CandidateRef.from_document(document["candidate_ref"])
        _require_candidate(candidate, current_candidate)
        state = cls(
            config=config,
            candidate_ref=candidate,
            interactions=list(document["interactions"]),
            quality_failures=document["quality_failures"],
            tool_calls=document["tool_calls"],
            wall_time_ms=document["wall_time_ms"],
            reserved_consumed=dict(document["reserved_consumed"]),
            mandatory_completed=set(document["mandatory_completed"]),
        )
        state.validate_persisted()
        return state

    def validate_persisted(self) -> None:
        if any(not isinstance(stage, str) or not stage for stage in self.interactions):
            raise PrototypeError("persisted interactions must be non-empty strings")
        if len(self.interactions) > self.config.max_leaf_interactions:
            raise PrototypeError("persisted interactions exceed configured limit")
        replay = BudgetState(self.config, self.candidate_ref)
        try:
            for stage in self.interactions:
                replay.consume_leaf(stage, candidate_ref=self.candidate_ref)
        except BudgetExhausted as error:
            raise PrototypeError(
                "persisted history violates mandatory capacity"
            ) from error
        if (
            type(self.quality_failures) is not int
            or not 0 <= self.quality_failures <= self.config.max_quality_failures
        ):
            raise PrototypeError("persisted quality failures are out of bounds")
        for name, used, limit in (
            ("tool calls", self.tool_calls, self.config.max_leaf_tool_calls),
            ("wall time", self.wall_time_ms, self.config.max_leaf_wall_time_ms),
        ):
            if type(used) is not int or used < 0:
                raise PrototypeError(f"persisted {name} must be non-negative")
            if limit is not None and used > limit:
                raise PrototypeError(f"persisted {name} exceeds configured limit")

        for stage in MANDATORY_STAGES:
            if type(self.reserved_consumed[stage]) is not int:
                raise PrototypeError(
                    "persisted reservation counters must be integers"
                )
            if self.reserved_consumed[stage] != replay.reserved_consumed[stage]:
                raise PrototypeError("persisted reservation accounting is inconsistent")
        if not self.mandatory_completed.issubset(MANDATORY_STAGES):
            raise PrototypeError("persisted mandatory completion is invalid")
        if any(
            self.reserved_consumed[stage] < 1
            for stage in self.mandatory_completed
        ):
            raise PrototypeError("completed mandatory stage lacks a consumed reservation")


@dataclass(frozen=True)
class ProgressEvent:
    phase: str
    completed: int
    total: int
    candidate_ref: CandidateRef
    stage: str
    phase_contract: tuple[str, ...]

    def validate(self) -> None:
        self.candidate_ref.validate()
        _validate_phase_contract(self.stage, self.phase_contract)
        if (
            not isinstance(self.phase, str)
            or self.phase not in self.phase_contract
        ):
            raise PrototypeError(
                f"progress phase is outside the progress stage: {self.phase}"
            )
        if (
            type(self.completed) is not int
            or type(self.total) is not int
            or self.total < 1
            or not 0 <= self.completed <= self.total
        ):
            raise PrototypeError("invalid progress bounds")

    def to_document(self) -> dict[str, Any]:
        self.validate()
        return {
            "phase": self.phase,
            "completed": self.completed,
            "total": self.total,
            "candidate_ref": self.candidate_ref.to_document(),
            "stage": self.stage,
            "phase_contract": list(self.phase_contract),
        }

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> ProgressEvent:
        expected = {
            "phase",
            "completed",
            "total",
            "candidate_ref",
            "stage",
            "phase_contract",
        }
        if not isinstance(document, dict) or set(document) != expected:
            raise PrototypeError("invalid progress event document")
        event = cls(
            phase=document["phase"],
            completed=document["completed"],
            total=document["total"],
            candidate_ref=CandidateRef.from_document(document["candidate_ref"]),
            stage=document["stage"],
            phase_contract=_string_array(
                document["phase_contract"], "progress phase_contract"
            ),
        )
        event.validate()
        return event


@dataclass
class ProgressLog:
    candidate_ref: CandidateRef
    stage: str
    phase_contract: tuple[str, ...]
    events: list[ProgressEvent] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.candidate_ref.validate()
        _validate_phase_contract(self.stage, self.phase_contract)

    def record(self, event: ProgressEvent) -> None:
        event.validate()
        _require_candidate(self.candidate_ref, event.candidate_ref)
        if (
            event.stage != self.stage
            or event.phase_contract != self.phase_contract
        ):
            raise PrototypeError("progress event belongs to another stage contract")
        if event in self.events:
            return
        if self.events:
            previous = self.events[-1]
            previous_phase = self.phase_contract.index(previous.phase)
            current_phase = self.phase_contract.index(event.phase)
            if current_phase < previous_phase:
                raise PrototypeError("progress cannot regress")
            if current_phase == previous_phase:
                if event.total != previous.total or event.completed < previous.completed:
                    raise PrototypeError("progress cannot regress")
        self.events.append(event)

    def validate_candidate(self, current_candidate: CandidateRef) -> None:
        _require_candidate(self.candidate_ref, current_candidate)

    def validate(self) -> None:
        replay = ProgressLog(
            self.candidate_ref,
            self.stage,
            self.phase_contract,
        )
        for event in self.events:
            replay.record(event)
        if replay.events != self.events:
            raise PrototypeError("persisted progress contains duplicate events")

    def to_document(self) -> dict[str, Any]:
        self.validate()
        return {
            "candidate_ref": self.candidate_ref.to_document(),
            "stage": self.stage,
            "phase_contract": list(self.phase_contract),
            "events": [event.to_document() for event in self.events],
        }

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> ProgressLog:
        if not isinstance(document, dict) or set(document) != {
            "candidate_ref",
            "stage",
            "phase_contract",
            "events",
        }:
            raise PrototypeError("invalid progress log document")
        if not isinstance(document["events"], list):
            raise PrototypeError("progress events must be an array")
        result = cls(
            CandidateRef.from_document(document["candidate_ref"]),
            document["stage"],
            _string_array(
                document["phase_contract"], "progress phase_contract"
            ),
        )
        for raw_event in document["events"]:
            event = ProgressEvent.from_document(raw_event)
            if event in result.events:
                raise PrototypeError("persisted progress contains duplicate events")
            result.record(event)
        return result


def _string_array(value: Any, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise PrototypeError(f"{field_name} must be an array")
    if any(not isinstance(item, str) or not item for item in value):
        raise PrototypeError(f"{field_name} must contain non-empty strings")
    return tuple(value)


@dataclass(frozen=True)
class LeafHandoff:
    candidate_ref: CandidateRef
    complete: bool
    stage: str
    phase_contract: tuple[str, ...]
    files_expected: tuple[str, ...]
    files_inspected: tuple[str, ...]
    files_remaining: tuple[str, ...]
    phases_remaining: tuple[str, ...]
    commands_run: tuple[str, ...]
    findings: tuple[str, ...]
    progress_phase: str
    stop_reason: str | None
    schema: int = LEAF_RESULT_SCHEMA

    def validate(self) -> None:
        self.candidate_ref.validate()
        if type(self.schema) is not int or self.schema != LEAF_RESULT_SCHEMA:
            raise PrototypeError("unsupported leaf-result schema")
        if type(self.complete) is not bool:
            raise PrototypeError("handoff complete must be a boolean")
        _validate_phase_contract(self.stage, self.phase_contract)
        for name, values in (
            ("files_expected", self.files_expected),
            ("files_inspected", self.files_inspected),
            ("files_remaining", self.files_remaining),
            ("phases_remaining", self.phases_remaining),
            ("commands_run", self.commands_run),
            ("findings", self.findings),
        ):
            if not isinstance(values, tuple) or any(
                not isinstance(value, str) or not value for value in values
            ):
                raise PrototypeError(
                    f"{name} must contain non-empty strings"
                )
        if self.progress_phase not in self.phase_contract:
            raise PrototypeError("progress phase is outside the leaf stage contract")
        if self.stop_reason is not None and (
            not isinstance(self.stop_reason, str) or not self.stop_reason
        ):
            raise PrototypeError("stop_reason must be null or a non-empty string")
        if len(set(self.files_expected)) != len(self.files_expected):
            raise PrototypeError("expected files must be unique")
        if len(set(self.files_inspected)) != len(self.files_inspected):
            raise PrototypeError("inspected files must be unique")
        if not set(self.files_inspected).issubset(self.files_expected):
            raise PrototypeError("inspected files must belong to expected scope")

        inspected = set(self.files_inspected)
        expected_remaining = tuple(
            path for path in self.files_expected if path not in inspected
        )
        if self.files_remaining != expected_remaining:
            raise PrototypeError(
                "files_remaining must equal expected scope minus inspected scope"
            )
        phase_index = self.phase_contract.index(self.progress_phase)
        expected_phases = self.phase_contract[phase_index + 1 :]
        if self.phases_remaining != expected_phases:
            raise PrototypeError(
                "phases_remaining must equal the ordered phases after progress_phase"
            )

        if self.complete:
            if self.files_remaining:
                raise PrototypeError("complete handoff still has remaining scope")
            if self.phases_remaining:
                raise PrototypeError("complete handoff still has remaining phases")
            if self.progress_phase != "handoff-ready":
                raise PrototypeError("complete handoff must be handoff-ready")
            if self.stop_reason is not None:
                raise PrototypeError("complete handoff cannot have a stop reason")
        else:
            if not self.files_remaining and not self.phases_remaining:
                raise PrototypeError("partial handoff must carry remaining work")
            if self.progress_phase == "handoff-ready":
                raise PrototypeError("partial handoff cannot be handoff-ready")
            if not self.stop_reason:
                raise PrototypeError("partial handoff must state a stop reason")

    def continuation(self, current_candidate: CandidateRef) -> tuple[str, ...]:
        self.validate()
        _require_candidate(self.candidate_ref, current_candidate)
        return (
            *(f"inspect {path}" for path in self.files_remaining),
            *(f"advance {phase}" for phase in self.phases_remaining),
        )

    def to_document(self) -> dict[str, Any]:
        self.validate()
        return {
            "schema": self.schema,
            "candidate_ref": self.candidate_ref.to_document(),
            "complete": self.complete,
            "stage": self.stage,
            "phase_contract": list(self.phase_contract),
            "scope": {
                "files_expected": list(self.files_expected),
                "files_inspected": list(self.files_inspected),
                "files_remaining": list(self.files_remaining),
            },
            "phases_remaining": list(self.phases_remaining),
            "commands_run": list(self.commands_run),
            "findings": list(self.findings),
            "progress_phase": self.progress_phase,
            "stop_reason": self.stop_reason,
        }

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> LeafHandoff:
        expected = {
            "schema",
            "candidate_ref",
            "complete",
            "stage",
            "phase_contract",
            "scope",
            "phases_remaining",
            "commands_run",
            "findings",
            "progress_phase",
            "stop_reason",
        }
        if not isinstance(document, dict) or set(document) != expected:
            raise PrototypeError("unknown or missing leaf-result fields")
        scope = document["scope"]
        if not isinstance(scope, dict) or set(scope) != {
            "files_expected",
            "files_inspected",
            "files_remaining",
        }:
            raise PrototypeError("unknown or missing leaf-result scope fields")
        if type(document["schema"]) is not int:
            raise PrototypeError("leaf-result schema must be an integer")
        if type(document["complete"]) is not bool:
            raise PrototypeError("handoff complete must be a boolean")
        if not isinstance(document["stage"], str):
            raise PrototypeError("handoff stage must be a string")
        if not isinstance(document["progress_phase"], str):
            raise PrototypeError("progress_phase must be a string")
        if document["stop_reason"] is not None and (
            not isinstance(document["stop_reason"], str)
            or not document["stop_reason"]
        ):
            raise PrototypeError("stop_reason must be null or a non-empty string")
        handoff = cls(
            schema=document["schema"],
            candidate_ref=CandidateRef.from_document(document["candidate_ref"]),
            complete=document["complete"],
            stage=document["stage"],
            phase_contract=_string_array(
                document["phase_contract"], "phase_contract"
            ),
            files_expected=_string_array(
                scope["files_expected"], "scope.files_expected"
            ),
            files_inspected=_string_array(
                scope["files_inspected"], "scope.files_inspected"
            ),
            files_remaining=_string_array(
                scope["files_remaining"], "scope.files_remaining"
            ),
            phases_remaining=_string_array(
                document["phases_remaining"], "phases_remaining"
            ),
            commands_run=_string_array(
                document["commands_run"], "commands_run"
            ),
            findings=_string_array(document["findings"], "findings"),
            progress_phase=document["progress_phase"],
            stop_reason=document["stop_reason"],
        )
        handoff.validate()
        return handoff


@dataclass
class LedgerSnapshot:
    budget: BudgetState
    progress: ProgressLog
    handoff: LeafHandoff | None


def _config_document(config: BudgetConfig) -> dict[str, Any]:
    config.validate()
    return {
        "max_quality_failures": config.max_quality_failures,
        "max_leaf_interactions": config.max_leaf_interactions,
        "max_leaf_tool_calls": config.max_leaf_tool_calls,
        "max_leaf_wall_time_ms": config.max_leaf_wall_time_ms,
        "reservations": [list(item) for item in config.reservations],
    }


def _config_from_document(document: dict[str, Any]) -> BudgetConfig:
    expected = {
        "max_quality_failures",
        "max_leaf_interactions",
        "max_leaf_tool_calls",
        "max_leaf_wall_time_ms",
        "reservations",
    }
    if not isinstance(document, dict) or set(document) != expected:
        raise PrototypeError("invalid ledger config")
    if not isinstance(document["reservations"], list) or any(
        not isinstance(item, list) or len(item) != 2
        for item in document["reservations"]
    ):
        raise PrototypeError("ledger reservations must be two-item arrays")
    config = BudgetConfig(
        max_quality_failures=document["max_quality_failures"],
        max_leaf_interactions=document["max_leaf_interactions"],
        max_leaf_tool_calls=document["max_leaf_tool_calls"],
        max_leaf_wall_time_ms=document["max_leaf_wall_time_ms"],
        reservations=tuple(tuple(item) for item in document["reservations"]),
    )
    config.validate()
    return config


def _validate_snapshot_alignment(
    budget: BudgetState,
    progress: ProgressLog,
    handoff: LeafHandoff | None,
) -> None:
    progress.validate()
    if handoff is not None:
        handoff.validate()
        _require_candidate(progress.candidate_ref, handoff.candidate_ref)
        if (
            progress.stage != handoff.stage
            or progress.phase_contract != handoff.phase_contract
        ):
            raise PrototypeError(
                "persisted progress and handoff stage contracts differ"
            )
        if not progress.events:
            raise PrototypeError("persisted handoff requires progress")
        if progress.events[-1].phase != handoff.progress_phase:
            raise PrototypeError(
                "persisted handoff phase differs from latest progress"
            )
        if (
            handoff.complete
            and handoff.stage in MANDATORY_STAGES
            and handoff.stage not in budget.mandatory_completed
        ):
            raise PrototypeError(
                "complete handoff requires its completed mandatory reservation"
            )
    if progress.events and (
        not budget.interactions
        or budget.interactions[-1] != progress.stage
    ):
        raise PrototypeError(
            "latest budget interaction differs from progress stage"
        )


def new_ledger(
    budget: BudgetState,
    progress: ProgressLog,
    handoff: LeafHandoff | None = None,
) -> dict[str, Any]:
    budget.validate_persisted()
    _require_candidate(budget.candidate_ref, progress.candidate_ref)
    progress.validate_candidate(budget.candidate_ref)
    _validate_snapshot_alignment(budget, progress, handoff)
    return {
        "schema": LEDGER_SCHEMA,
        "candidate_ref": budget.candidate_ref.to_document(),
        "config": _config_document(budget.config),
        "budget": budget.to_document(),
        "progress": progress.to_document(),
        "handoff": handoff.to_document() if handoff is not None else None,
    }


def validate_ledger(
    document: dict[str, Any], current_candidate: CandidateRef
) -> LedgerSnapshot:
    if not isinstance(document, dict):
        raise LedgerVersionError("ledger must be an object")
    if document.get("schema") == 1:
        raise LedgerVersionError(
            "ledger schema 1 requires explicit migration or a new run"
        )
    if document.get("schema") != LEDGER_SCHEMA:
        raise LedgerVersionError("unsupported or missing ledger schema")
    if set(document) != {
        "schema",
        "candidate_ref",
        "config",
        "budget",
        "progress",
        "handoff",
    }:
        raise PrototypeError("unknown or missing ledger fields")

    candidate = CandidateRef.from_document(document["candidate_ref"])
    _require_candidate(candidate, current_candidate)
    config = _config_from_document(document["config"])
    budget = BudgetState.from_document(
        config, document["budget"], current_candidate
    )
    progress = ProgressLog.from_document(document["progress"])
    progress.validate_candidate(current_candidate)
    handoff = (
        None
        if document["handoff"] is None
        else LeafHandoff.from_document(document["handoff"])
    )
    if handoff is not None:
        _require_candidate(candidate, handoff.candidate_ref)
    _validate_snapshot_alignment(budget, progress, handoff)
    return LedgerSnapshot(budget=budget, progress=progress, handoff=handoff)


def sample_candidate(suffix: str = "a") -> CandidateRef:
    return CandidateRef(
        base_sha=f"base-{suffix}",
        tree_oid=f"tree-{suffix}",
        ticket_digest=f"ticket-{suffix}",
    )


def issue_nine_shape() -> dict[str, Any]:
    """Model the two independent tickets from issue #9 under pressure."""
    candidate_a = sample_candidate("issue-9-a")
    ticket_a = BudgetState(BudgetConfig(), candidate_a)
    for stage in (
        "implement",
        "simplify",
        "review",
        "review",
        "review",
        "review",
        "review",
        "qa-execute",
        "verify",
    ):
        ticket_a.consume_leaf(stage, candidate_ref=candidate_a)
    ticket_a.complete_mandatory("qa-execute", candidate_ref=candidate_a)
    ticket_a.complete_mandatory("verify", candidate_ref=candidate_a)

    candidate_b = sample_candidate("issue-9-b")
    ticket_b = BudgetState(BudgetConfig(), candidate_b)
    for stage in (
        "implement",
        "simplify",
        "review",
        "review",
        "review",
        "review",
        "review",
        "review",
        "qa-execute",
        "verify",
    ):
        ticket_b.consume_leaf(stage, candidate_ref=candidate_b)
    ticket_b.record_quality_failure(candidate_ref=candidate_b)
    ticket_b.complete_mandatory("qa-execute", candidate_ref=candidate_b)
    ticket_b.complete_mandatory("verify", candidate_ref=candidate_b)

    return {
        "name": "issue-9-two-ticket-pressure",
        "tickets": {
            "A": {"budget": ticket_a.report(), "findings": []},
            "B": {
                "budget": ticket_b.report(),
                "findings": [
                    "expired state blocker",
                    "kill-switch should-fix",
                ],
            },
        },
        "cross_ticket_blocker_preserved": True,
    }
