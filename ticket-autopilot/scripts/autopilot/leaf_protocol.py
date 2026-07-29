from __future__ import annotations

import copy
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence


LEAF_RESULT_SCHEMA = 3
MIN_LEAF_INTERACTIONS = 3
MAX_LEAF_INTERACTIONS = 100
MANDATORY_RESERVATIONS = {"qa-execute": 1, "verify": 1}
QUALITY_LEAF_STAGES = frozenset({"qa-plan", "qa-execute", "verify"})
LEAF_PHASE_CONTRACTS: dict[str, tuple[str, ...]] = {
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


class LeafProtocolError(ValueError):
    pass


def _exact_int(value: Any, field: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise LeafProtocolError(f"{field} must be an integer >= {minimum}")
    return value


def normalize_resource_usage(tool_calls: Any, wall_time: Any) -> tuple[int, int]:
    return (
        _exact_int(tool_calls, "tool_calls"),
        _exact_int(wall_time, "wall_time"),
    )


def normalize_file_manifest(files: Any) -> list[str]:
    return _string_array(files, "expected_files")


def _optional_positive_int(value: Any, field: str) -> int | None:
    if value is None:
        return None
    return _exact_int(value, field, minimum=1)


def _string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise LeafProtocolError(f"{field} must be a non-empty string")
    return value


def _string_array(value: Any, field: str) -> list[str]:
    if not isinstance(value, list):
        raise LeafProtocolError(f"{field} must be an array")
    result: list[str] = []
    for index, item in enumerate(value):
        result.append(_string(item, f"{field}[{index}]"))
    if len(result) != len(set(result)):
        raise LeafProtocolError(f"{field} must not contain duplicates")
    return result


def _candidate_ref(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise LeafProtocolError("candidate_ref must be an object")
    required = {"contract_version", "base_sha", "tree_oid", "ticket_digest"}
    if set(value) != required:
        raise LeafProtocolError("candidate_ref fields are invalid")
    contract_version = _exact_int(
        value["contract_version"], "candidate_ref.contract_version", minimum=1
    )
    if contract_version != 1:
        raise LeafProtocolError("candidate_ref contract_version must be 1")
    return {
        "contract_version": contract_version,
        "base_sha": _string(value["base_sha"], "candidate_ref.base_sha"),
        "tree_oid": _string(value["tree_oid"], "candidate_ref.tree_oid"),
        "ticket_digest": _string(
            value["ticket_digest"], "candidate_ref.ticket_digest"
        ),
    }


@dataclass(frozen=True)
class BudgetConfig:
    max_quality_failures: int = 3
    max_leaf_interactions: int = 10
    max_leaf_tool_calls: int | None = None
    max_leaf_wall_time: int | None = None
    reservations: Mapping[str, int] | None = None

    def normalized(self) -> dict[str, Any]:
        quality = _exact_int(
            self.max_quality_failures, "max_quality_failures", minimum=1
        )
        interactions = _exact_int(
            self.max_leaf_interactions, "max_leaf_interactions", minimum=1
        )
        if not MIN_LEAF_INTERACTIONS <= interactions <= MAX_LEAF_INTERACTIONS:
            raise LeafProtocolError(
                "max_leaf_interactions must be between "
                f"{MIN_LEAF_INTERACTIONS} and {MAX_LEAF_INTERACTIONS}"
            )
        tool_calls = _optional_positive_int(
            self.max_leaf_tool_calls, "max_leaf_tool_calls"
        )
        wall_time = _optional_positive_int(
            self.max_leaf_wall_time, "max_leaf_wall_time"
        )
        raw_reservations: dict[str, Any] = (
            MANDATORY_RESERVATIONS
            if self.reservations is None
            else dict(self.reservations)
        )
        if set(raw_reservations) != set(MANDATORY_RESERVATIONS) or any(
            _exact_int(raw_reservations[stage], f"reservations.{stage}", minimum=1)
            != reserved
            for stage, reserved in MANDATORY_RESERVATIONS.items()
        ):
            raise LeafProtocolError(
                "reservations must contain exactly qa-execute=1 and verify=1"
            )
        if interactions <= sum(raw_reservations.values()):
            raise LeafProtocolError(
                "max_leaf_interactions must leave capacity before mandatory reservations"
            )
        return {
            "max_quality_failures": quality,
            "max_leaf_interactions": interactions,
            "max_leaf_tool_calls": tool_calls,
            "max_leaf_wall_time": wall_time,
            "reservations": copy.deepcopy(raw_reservations),
        }


def normalize_budget_config(config: Mapping[str, Any]) -> dict[str, Any]:
    return BudgetConfig(
        max_quality_failures=config["max_quality_failures"],
        max_leaf_interactions=config["max_leaf_interactions"],
        max_leaf_tool_calls=config.get("max_leaf_tool_calls"),
        max_leaf_wall_time=config.get("max_leaf_wall_time"),
        reservations=config.get("reservations"),
    ).normalized()


def new_leaf_budget(config: Mapping[str, Any]) -> dict[str, Any]:
    normalized = normalize_budget_config(config)
    return {
        "interactions_consumed": 0,
        "tool_calls_consumed": 0,
        "wall_time_consumed": 0,
        "reservations": {
            stage: {"reserved": count, "consumed": 0, "complete": False}
            for stage, count in normalized["reservations"].items()
        },
    }


def validate_leaf_budget(
    config: Mapping[str, Any], budget: Any
) -> dict[str, Any]:
    normalized = normalize_budget_config(config)
    if not isinstance(budget, Mapping):
        raise LeafProtocolError("leaf_budget must be an object")
    required = {
        "interactions_consumed",
        "tool_calls_consumed",
        "wall_time_consumed",
        "reservations",
    }
    if set(budget) != required:
        raise LeafProtocolError("leaf_budget fields are invalid")
    interactions = _exact_int(
        budget["interactions_consumed"], "interactions_consumed"
    )
    tool_calls = _exact_int(budget["tool_calls_consumed"], "tool_calls_consumed")
    wall_time = _exact_int(budget["wall_time_consumed"], "wall_time_consumed")
    if interactions > normalized["max_leaf_interactions"]:
        raise LeafProtocolError("leaf interaction budget is over-consumed")
    if (
        normalized["max_leaf_tool_calls"] is not None
        and tool_calls > normalized["max_leaf_tool_calls"]
    ):
        raise LeafProtocolError("leaf tool-call budget is over-consumed")
    if (
        normalized["max_leaf_wall_time"] is not None
        and wall_time > normalized["max_leaf_wall_time"]
    ):
        raise LeafProtocolError("leaf wall-time budget is over-consumed")
    reservations = budget["reservations"]
    if not isinstance(reservations, Mapping) or set(reservations) != set(
        MANDATORY_RESERVATIONS
    ):
        raise LeafProtocolError("leaf reservation state is invalid")
    normalized_reservations: dict[str, dict[str, Any]] = {}
    for stage, reserved in MANDATORY_RESERVATIONS.items():
        state = reservations[stage]
        if not isinstance(state, Mapping) or set(state) != {
            "reserved",
            "consumed",
            "complete",
        }:
            raise LeafProtocolError(f"{stage} reservation state is invalid")
        consumed = _exact_int(state["consumed"], f"{stage}.consumed")
        if state["reserved"] != reserved or consumed > reserved:
            raise LeafProtocolError(f"{stage} reservation accounting is invalid")
        if not isinstance(state["complete"], bool):
            raise LeafProtocolError(f"{stage}.complete must be a boolean")
        if state["complete"] and consumed != reserved:
            raise LeafProtocolError(f"{stage} reservation completion is inconsistent")
        normalized_reservations[stage] = {
            "reserved": reserved,
            "consumed": consumed,
            "complete": state["complete"],
        }
    return {
        "interactions_consumed": interactions,
        "tool_calls_consumed": tool_calls,
        "wall_time_consumed": wall_time,
        "reservations": normalized_reservations,
    }


def budget_status(
    config: Mapping[str, Any], budget: Mapping[str, Any]
) -> dict[str, Any]:
    normalized = normalize_budget_config(config)
    current = validate_leaf_budget(normalized, budget)
    outstanding = sum(
        item["reserved"] - item["consumed"]
        for item in current["reservations"].values()
    )

    def dimension(maximum: int | None, consumed: int) -> dict[str, Any]:
        return {
            "configured": maximum,
            "consumed": consumed,
            "remaining": None if maximum is None else maximum - consumed,
            "enforcement": "unavailable" if maximum is None else "hard",
        }

    return {
        "quality_failures": {
            "configured": normalized["max_quality_failures"],
        },
        "leaf_interactions": {
            **dimension(
                normalized["max_leaf_interactions"],
                current["interactions_consumed"],
            ),
            "reserved_remaining": outstanding,
            "unreserved_remaining": (
                normalized["max_leaf_interactions"]
                - current["interactions_consumed"]
                - outstanding
            ),
        },
        "leaf_tool_calls": dimension(
            normalized["max_leaf_tool_calls"], current["tool_calls_consumed"]
        ),
        "leaf_wall_time": dimension(
            normalized["max_leaf_wall_time"], current["wall_time_consumed"]
        ),
        "reservations": copy.deepcopy(current["reservations"]),
    }


def _admit_resources(
    config: Mapping[str, Any],
    budget: Mapping[str, Any],
    *,
    stage: str,
    handoff_complete: bool,
    tool_calls: Any,
    wall_time: Any,
) -> dict[str, Any]:
    normalized_config = normalize_budget_config(config)
    current = validate_leaf_budget(normalized_config, budget)
    calls, elapsed = normalize_resource_usage(tool_calls, wall_time)
    mandatory = stage in MANDATORY_RESERVATIONS
    outstanding = sum(
        item["reserved"] - item["consumed"]
        for item in current["reservations"].values()
    )
    remaining = (
        normalized_config["max_leaf_interactions"]
        - current["interactions_consumed"]
    )
    if not isinstance(handoff_complete, bool):
        raise LeafProtocolError("handoff_complete must be a boolean")
    uses_reservation = False
    if mandatory:
        reservation = current["reservations"][stage]
        if reservation["complete"]:
            raise LeafProtocolError(f"{stage} reservation is already complete")
        uses_reservation = reservation["consumed"] < reservation["reserved"]
        if uses_reservation and remaining < 1:
            raise LeafProtocolError("leaf interaction budget is exhausted")
        if not uses_reservation and remaining - outstanding < 1:
            raise LeafProtocolError(
                "leaf interaction budget is reserved for mandatory stages"
            )
    elif remaining - outstanding < 1:
        raise LeafProtocolError(
            "leaf interaction budget is reserved for mandatory stages"
        )
    next_tool_calls = current["tool_calls_consumed"] + calls
    maximum_calls = normalized_config["max_leaf_tool_calls"]
    if maximum_calls is not None and next_tool_calls > maximum_calls:
        raise LeafProtocolError("leaf tool-call budget is exhausted")
    next_wall_time = current["wall_time_consumed"] + elapsed
    maximum_wall_time = normalized_config["max_leaf_wall_time"]
    if maximum_wall_time is not None and next_wall_time > maximum_wall_time:
        raise LeafProtocolError("leaf wall-time budget is exhausted")
    updated = copy.deepcopy(current)
    updated["interactions_consumed"] += 1
    updated["tool_calls_consumed"] = next_tool_calls
    updated["wall_time_consumed"] = next_wall_time
    if mandatory:
        reservation = updated["reservations"][stage]
        if uses_reservation:
            reservation["consumed"] += 1
        reservation["complete"] = handoff_complete
    return updated


def _quality_payload(
    value: Any,
    *,
    candidate_ref: Mapping[str, Any],
) -> dict[str, Any]:
    required = {
        "schema",
        "causal_scope",
        "evidence",
        "limitations",
    }
    if not isinstance(value, Mapping) or set(value) != required:
        raise LeafProtocolError("quality fields are invalid")
    schema = _exact_int(value["schema"], "quality.schema", minimum=1)
    if schema != 1:
        raise LeafProtocolError("quality schema must be 1")
    causal_scope = _string_array(value["causal_scope"], "quality.causal_scope")
    if not causal_scope:
        raise LeafProtocolError("quality.causal_scope cannot be empty")
    limitations = _string_array(value["limitations"], "quality.limitations")
    evidence_value = value["evidence"]
    if not isinstance(evidence_value, list):
        raise LeafProtocolError("quality.evidence must be an array")
    evidence: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, item in enumerate(evidence_value):
        fields = {
            "id",
            "artifact",
            "sha256",
            "result",
            "candidate_ref",
        }
        if not isinstance(item, Mapping) or set(item) != fields:
            raise LeafProtocolError(
                f"quality.evidence[{index}] fields are invalid"
            )
        evidence_id = _string(item["id"], f"quality.evidence[{index}].id")
        if evidence_id in seen_ids:
            raise LeafProtocolError("quality evidence ids must be unique")
        seen_ids.add(evidence_id)
        digest = _string(item["sha256"], f"quality.evidence[{index}].sha256")
        if len(digest) != 64 or any(
            character not in "0123456789abcdef" for character in digest
        ):
            raise LeafProtocolError("quality evidence sha256 must be lowercase hex")
        result = _string(item["result"], f"quality.evidence[{index}].result")
        if result not in {"planned", "pass", "fail", "skipped", "unavailable"}:
            raise LeafProtocolError("quality evidence result is invalid")
        evidence_candidate = _candidate_ref(item["candidate_ref"])
        if evidence_candidate != candidate_ref:
            raise LeafProtocolError("quality evidence CandidateRef is stale")
        evidence.append(
            {
                "id": evidence_id,
                "artifact": _string(
                    item["artifact"],
                    f"quality.evidence[{index}].artifact",
                ),
                "sha256": digest,
                "result": result,
                "candidate_ref": evidence_candidate,
            }
        )
    return {
        "schema": 1,
        "causal_scope": causal_scope,
        "evidence": evidence,
        "limitations": limitations,
    }


def verification_checkpoint_identity(value: Any) -> str | None:
    """Return the content identity that binds one verify handoff to its inputs."""

    if not isinstance(value, Mapping) or value.get("stage") != "verify":
        return None
    quality = value.get("quality")
    if not isinstance(quality, Mapping):
        return None
    evidence = quality.get("evidence")
    if not isinstance(evidence, list):
        return None
    for item in evidence:
        if (
            isinstance(item, Mapping)
            and item.get("id") == "verification-checkpoint:context-loaded"
            and isinstance(item.get("sha256"), str)
        ):
            return item["sha256"]
    return None


def validate_leaf_result(
    document: Any,
    *,
    expected_candidate_ref: Mapping[str, Any] | None = None,
    expected_stage: str | None = None,
) -> dict[str, Any]:
    if not isinstance(document, Mapping):
        raise LeafProtocolError("leaf result must be an object")
    required = {
        "schema",
        "complete",
        "candidate_ref",
        "stage",
        "phase_contract",
        "scope",
        "phases_remaining",
        "commands_run",
        "findings",
        "progress_phase",
        "stop_reason",
    }
    stage_hint = document.get("stage")
    if isinstance(stage_hint, str) and stage_hint in QUALITY_LEAF_STAGES:
        if "quality" not in document:
            raise LeafProtocolError(
                "quality leaf result requires structured quality evidence"
            )
        required.add("quality")
    if set(document) != required:
        raise LeafProtocolError("leaf result fields are invalid")
    schema = _exact_int(document["schema"], "schema")
    if schema != LEAF_RESULT_SCHEMA:
        raise LeafProtocolError(
            f"leaf result schema must be {LEAF_RESULT_SCHEMA}"
        )
    if not isinstance(document["complete"], bool):
        raise LeafProtocolError("complete must be a boolean")
    candidate = _candidate_ref(document["candidate_ref"])
    if expected_candidate_ref is not None and candidate != _candidate_ref(
        expected_candidate_ref
    ):
        raise LeafProtocolError("leaf result CandidateRef is stale")
    stage = _string(document["stage"], "stage")
    if expected_stage is not None and stage != expected_stage:
        raise LeafProtocolError("leaf result stage differs from the active stage")
    contract = LEAF_PHASE_CONTRACTS.get(stage)
    if contract is None:
        raise LeafProtocolError(f"unsupported leaf stage {stage!r}")
    quality = (
        _quality_payload(document["quality"], candidate_ref=candidate)
        if stage in QUALITY_LEAF_STAGES
        else None
    )
    phase_contract = _string_array(document["phase_contract"], "phase_contract")
    if tuple(phase_contract) != contract:
        raise LeafProtocolError("phase_contract differs from the canonical stage contract")
    progress_phase = _string(document["progress_phase"], "progress_phase")
    if progress_phase not in contract:
        raise LeafProtocolError("progress_phase is outside the stage contract")
    phases_remaining = _string_array(
        document["phases_remaining"], "phases_remaining"
    )
    phase_index = contract.index(progress_phase)
    if tuple(phases_remaining) != contract[phase_index + 1 :]:
        raise LeafProtocolError(
            "phases_remaining must be the canonical suffix after progress_phase"
        )
    scope = document["scope"]
    if not isinstance(scope, Mapping) or set(scope) != {
        "files_expected",
        "files_inspected",
        "files_remaining",
    }:
        raise LeafProtocolError("scope fields are invalid")
    expected = _string_array(scope["files_expected"], "scope.files_expected")
    inspected = _string_array(scope["files_inspected"], "scope.files_inspected")
    remaining = _string_array(scope["files_remaining"], "scope.files_remaining")
    inspected_set = set(inspected)
    if any(item not in expected for item in inspected):
        raise LeafProtocolError("files_inspected must be a subset of files_expected")
    if inspected != [item for item in expected if item in inspected_set]:
        raise LeafProtocolError(
            "files_inspected must preserve canonical expected-file order"
        )
    derived_remaining = [item for item in expected if item not in inspected_set]
    if remaining != derived_remaining:
        raise LeafProtocolError(
            "files_remaining must equal ordered expected minus inspected scope"
        )
    commands = _string_array(document["commands_run"], "commands_run")
    findings = _string_array(document["findings"], "findings")
    stop_reason = document["stop_reason"]
    if stop_reason is not None:
        stop_reason = _string(stop_reason, "stop_reason")
    if document["complete"]:
        if quality is not None and not quality["evidence"]:
            raise LeafProtocolError(
                "complete quality leaf result requires evidence"
            )
        if remaining or phases_remaining:
            raise LeafProtocolError("complete leaf result retains remaining work")
        if progress_phase != contract[-1]:
            raise LeafProtocolError(
                "complete leaf result must finish at handoff-ready"
            )
        if stop_reason is not None:
            raise LeafProtocolError("complete leaf result cannot have stop_reason")
    else:
        if stop_reason is None:
            raise LeafProtocolError("partial leaf result requires stop_reason")
        if progress_phase == contract[-1] or not (remaining or phases_remaining):
            raise LeafProtocolError(
                "partial leaf result requires resumable work"
            )
    normalized = {
        "schema": LEAF_RESULT_SCHEMA,
        "complete": document["complete"],
        "candidate_ref": candidate,
        "stage": stage,
        "phase_contract": list(contract),
        "scope": {
            "files_expected": expected,
            "files_inspected": inspected,
            "files_remaining": remaining,
        },
        "phases_remaining": phases_remaining,
        "commands_run": commands,
        "findings": findings,
        "progress_phase": progress_phase,
        "stop_reason": stop_reason,
    }
    if quality is not None:
        normalized["quality"] = quality
    return normalized


def validate_handoff_progression(
    previous: Mapping[str, Any],
    current: Mapping[str, Any],
) -> str:
    before = validate_leaf_result(previous)
    after = validate_leaf_result(
        current,
        expected_candidate_ref=before["candidate_ref"],
        expected_stage=before["stage"],
    )
    if before == after:
        return "duplicate"
    if before["complete"]:
        raise LeafProtocolError("complete leaf handoff cannot be replaced")
    if (
        before["phase_contract"] != after["phase_contract"]
        or before["scope"]["files_expected"]
        != after["scope"]["files_expected"]
    ):
        raise LeafProtocolError("leaf continuation changed its immutable scope")
    before_inspected = before["scope"]["files_inspected"]
    after_inspected = after["scope"]["files_inspected"]
    if not set(before_inspected) <= set(after_inspected):
        raise LeafProtocolError("leaf continuation regressed inspected scope")
    contract = before["phase_contract"]
    if contract.index(after["progress_phase"]) < contract.index(
        before["progress_phase"]
    ):
        raise LeafProtocolError("leaf continuation regressed progress phase")
    for field in ("commands_run", "findings"):
        prior = before[field]
        if after[field][: len(prior)] != prior:
            raise LeafProtocolError(
                f"leaf continuation rewrote prior {field}"
            )
    return "advance"


def record_leaf_result(
    config: Mapping[str, Any],
    budget: Mapping[str, Any],
    result: Mapping[str, Any],
    *,
    expected_candidate_ref: Mapping[str, Any],
    expected_stage: str,
    tool_calls: Any = 0,
    wall_time: Any = 0,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    normalized_result = validate_leaf_result(
        result,
        expected_candidate_ref=expected_candidate_ref,
        expected_stage=expected_stage,
    )
    updated_budget = _admit_resources(
        config,
        budget,
        stage=expected_stage,
        handoff_complete=normalized_result["complete"],
        tool_calls=tool_calls,
        wall_time=wall_time,
    )
    progress = {
        "schema": LEAF_RESULT_SCHEMA,
        "candidate_ref": copy.deepcopy(normalized_result["candidate_ref"]),
        "stage": expected_stage,
        "phase_contract": list(LEAF_PHASE_CONTRACTS[expected_stage]),
        "phase": normalized_result["progress_phase"],
        "complete": normalized_result["complete"],
        "stop_reason": normalized_result["stop_reason"],
        "resource_delta": {
            "interactions": 1,
            "tool_calls": _exact_int(tool_calls, "tool_calls"),
            "wall_time": _exact_int(wall_time, "wall_time"),
        },
    }
    return updated_budget, normalized_result, progress


def continuation_context(
    handoff: Mapping[str, Any],
    *,
    candidate_ref: Mapping[str, Any],
    stage: str = "review",
) -> dict[str, Any]:
    normalized = validate_leaf_result(
        handoff,
        expected_candidate_ref=candidate_ref,
        expected_stage=stage,
    )
    if normalized["complete"]:
        raise LeafProtocolError("complete leaf result has no continuation")
    return {
        "schema": LEAF_RESULT_SCHEMA,
        "candidate_ref": copy.deepcopy(normalized["candidate_ref"]),
        "stage": stage,
        "phase_contract": list(normalized["phase_contract"]),
        "files_expected": list(normalized["scope"]["files_expected"]),
        "files_already_inspected": list(normalized["scope"]["files_inspected"]),
        "files_remaining": list(normalized["scope"]["files_remaining"]),
        "phases_remaining": list(normalized["phases_remaining"]),
        "prior_commands": list(normalized["commands_run"]),
        "prior_findings": list(normalized["findings"]),
    }


def leaf_health(handoff: Mapping[str, Any] | None) -> str:
    if handoff is None:
        return "waiting"
    normalized = validate_leaf_result(handoff)
    if normalized["complete"]:
        return "complete"
    reason = normalized["stop_reason"]
    if reason in {
        "wall-time-budget",
        "tool-call-budget",
        "interaction-budget",
        "timeout",
        "interrupted",
    }:
        return "timed-out"
    return "partial"


def candidate_dict(candidate: Any) -> dict[str, Any]:
    if hasattr(candidate, "__dataclass_fields__"):
        return _candidate_ref(asdict(candidate))
    return _candidate_ref(candidate)
