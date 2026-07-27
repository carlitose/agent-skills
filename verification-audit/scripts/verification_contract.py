#!/usr/bin/env python3
"""Validate and reduce verification-audit contract v1 artifacts."""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable


CONTRACT_PATH = (
    Path(__file__).resolve().parents[1]
    / "references"
    / "verification-contract-v1.json"
)


class ContractError(ValueError):
    """Raised when an artifact violates the versioned verification contract."""

    def __init__(self, message: str, *, path: str | None = None) -> None:
        self.path = path
        super().__init__(f"{path}: {message}" if path else message)


def _load_contract() -> dict[str, Any]:
    with CONTRACT_PATH.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise RuntimeError("verification contract must be a JSON object")
    return value


CONTRACT = _load_contract()
CONTRACT_VERSION = CONTRACT["contract_version"]
CLAIM_RANK: dict[str, int] = CONTRACT["claim_rank"]
CLAIM_BY_RANK = {rank: claim for claim, rank in CLAIM_RANK.items()}


def _mapping(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError("must be an object", path=path)
    return value


def _list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise ContractError("must be a list", path=path)
    return value


def _required(value: dict[str, Any], kind: str, path: str) -> None:
    required = set(CONTRACT["required"][kind])
    missing = sorted(required - value.keys())
    if missing:
        raise ContractError(
            f"missing required field: {', '.join(missing)}",
            path=path,
        )
    allowed = required | set(CONTRACT.get("optional", {}).get(kind, []))
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise ContractError(
            f"unknown field: {', '.join(unknown)}",
            path=path,
        )


def _text(value: Any, path: str, *, nullable: bool = False) -> None:
    if nullable and value is None:
        return
    if not isinstance(value, str) or not value.strip():
        raise ContractError("must be non-empty text", path=path)


def _text_list(value: Any, path: str, *, nonempty: bool = False) -> list[str]:
    items = _list(value, path)
    if nonempty and not items:
        raise ContractError("must not be empty", path=path)
    if not all(isinstance(item, str) and item.strip() for item in items):
        raise ContractError("must contain only non-empty strings", path=path)
    return items


def _enum(value: Any, enum_name: str, path: str) -> None:
    allowed = CONTRACT["enums"][enum_name]
    if not isinstance(value, str) or value not in allowed:
        raise ContractError(
            f"must be one of: {', '.join(allowed)}",
            path=path,
        )


def _boolean(value: Any, path: str) -> None:
    if not isinstance(value, bool):
        raise ContractError("must be a boolean", path=path)


def _version(value: Any, path: str) -> None:
    if type(value) is not int or value != CONTRACT_VERSION:
        raise ContractError(
            f"must be {CONTRACT_VERSION}, got {value!r}",
            path=path,
        )


def _candidate_ref(value: Any, path: str) -> dict[str, Any]:
    ref = _mapping(value, path)
    _required(ref, "candidate_ref", path)
    _version(ref["contract_version"], f"{path}.contract_version")
    for field in ("base_sha", "tree_oid", "ticket_digest"):
        _text(ref[field], f"{path}.{field}")
    return ref


def _same_candidate(
    value: Any,
    expected: dict[str, Any],
    path: str,
    *,
    stale_message: bool = False,
) -> dict[str, Any]:
    actual = _candidate_ref(value, path)
    if actual != expected:
        message = (
            "stale candidate: does not match current CandidateRef"
            if stale_message
            else "does not match bundle candidate"
        )
        raise ContractError(message, path=path)
    return actual


def _unique_id(
    value: dict[str, Any],
    seen: set[str],
    label: str,
    path: str,
) -> str:
    _text(value.get("id"), f"{path}.id")
    item_id = value["id"]
    if item_id in seen:
        raise ContractError(f"duplicate {label} id {item_id}", path=f"{path}.id")
    seen.add(item_id)
    return item_id


def _references(
    ids: Iterable[str],
    known: set[str],
    label: str,
    path: str,
) -> None:
    for item_id in ids:
        if item_id not in known:
            raise ContractError(f"dangling {label} id {item_id}", path=path)


def _validate_stages(
    values: Any,
    candidate: dict[str, Any],
) -> list[dict[str, Any]]:
    stages: list[dict[str, Any]] = []
    stage_ids: set[str] = set()
    stage_names: set[str] = set()
    for index, raw in enumerate(_list(values, "stage_results")):
        path = f"stage_results[{index}]"
        item = _mapping(raw, path)
        _required(item, "stage_result", path)
        _unique_id(item, stage_ids, "stage result", path)
        _enum(item["stage"], "stage", f"{path}.stage")
        if item["stage"] in stage_names:
            raise ContractError(
                f"duplicate stage {item['stage']}",
                path=f"{path}.stage",
            )
        stage_names.add(item["stage"])
        _enum(item["result"], "stage_result", f"{path}.result")
        _same_candidate(item["candidate_ref"], candidate, f"{path}.candidate_ref")
        _text(item["artifact"], f"{path}.artifact")
        for field in (
            "evidence_ids",
            "invariant_ids",
            "boundary_delta_ids",
            "gate_ids",
            "provider_record_ids",
            "limitations",
        ):
            _text_list(item[field], f"{path}.{field}")
        if item["result"] == "blocked" and not item["gate_ids"]:
            raise ContractError(
                "blocked stage result must reference an open gate",
                path=f"{path}.gate_ids",
            )
        stages.append(item)
    if not stages:
        raise ContractError("must include at least one stage result", path="stage_results")
    return stages


def _validate_evidence(
    values: Any,
    candidate: dict[str, Any],
) -> tuple[list[dict[str, Any]], set[str]]:
    evidence: list[dict[str, Any]] = []
    evidence_ids: set[str] = set()
    for index, raw in enumerate(_list(values, "evidence")):
        path = f"evidence[{index}]"
        item = _mapping(raw, path)
        _required(item, "evidence", path)
        _unique_id(item, evidence_ids, "evidence", path)
        _same_candidate(item["candidate_ref"], candidate, f"{path}.candidate_ref")
        _enum(item["class"], "evidence_class", f"{path}.class")
        _enum(item["environment_scope"], "environment_scope", f"{path}.environment_scope")
        _enum(item["boundary_scope"], "boundary_scope", f"{path}.boundary_scope")
        _enum(item["result"], "evidence_result", f"{path}.result")
        _boolean(item["critical"], f"{path}.critical")
        _enum(item["supports_claim"], "max_claim", f"{path}.supports_claim")
        _enum(item["causal_coverage"], "causal_coverage", f"{path}.causal_coverage")
        for field in (
            "environment",
            "injection_point",
            "observed_segment",
            "artifact",
        ):
            _text(item[field], f"{path}.{field}")
        _text_list(item["limitations"], f"{path}.limitations")
        evidence.append(item)
    return evidence, evidence_ids


def _validate_invariants(
    values: Any,
    candidate: dict[str, Any],
) -> tuple[list[dict[str, Any]], set[str]]:
    invariants: list[dict[str, Any]] = []
    invariant_ids: set[str] = set()
    for index, raw in enumerate(_list(values, "invariants")):
        path = f"invariants[{index}]"
        item = _mapping(raw, path)
        _required(item, "invariant", path)
        _unique_id(item, invariant_ids, "invariant", path)
        _same_candidate(item["candidate_ref"], candidate, f"{path}.candidate_ref")
        _text(item["description"], f"{path}.description")
        _enum(item["status"], "invariant_status", f"{path}.status")
        _enum(item["impact"], "impact", f"{path}.impact")
        _text_list(item["evidence_ids"], f"{path}.evidence_ids")
        _text(item["authorization_ref"], f"{path}.authorization_ref", nullable=True)
        if item["status"] in {"modified", "removed"} and not item["authorization_ref"]:
            raise ContractError(
                "modified or removed invariant requires authorization_ref",
                path=f"{path}.authorization_ref",
            )
        invariants.append(item)
    return invariants, invariant_ids


def _validate_boundaries(
    values: Any,
    candidate: dict[str, Any],
) -> tuple[list[dict[str, Any]], set[str]]:
    boundaries: list[dict[str, Any]] = []
    boundary_ids: set[str] = set()
    for index, raw in enumerate(_list(values, "external_boundary_delta")):
        path = f"external_boundary_delta[{index}]"
        item = _mapping(raw, path)
        _required(item, "boundary_delta", path)
        _unique_id(item, boundary_ids, "boundary delta", path)
        _same_candidate(item["candidate_ref"], candidate, f"{path}.candidate_ref")
        _text(item["boundary"], f"{path}.boundary")
        _enum(item["controller"], "controller", f"{path}.controller")
        for field in ("baseline_source", "before_contract", "after_contract"):
            _text(item[field], f"{path}.{field}")

        boundary_items = _list(item["items"], f"{path}.items")
        if not boundary_items:
            raise ContractError("must not be empty", path=f"{path}.items")
        item_paths: set[str] = set()
        for item_index, raw_boundary_item in enumerate(boundary_items):
            item_path = f"{path}.items[{item_index}]"
            boundary_item = _mapping(raw_boundary_item, item_path)
            _required(boundary_item, "boundary_item", item_path)
            _text(boundary_item["path"], f"{item_path}.path")
            if boundary_item["path"] in item_paths:
                raise ContractError(
                    f"duplicate boundary item path {boundary_item['path']}",
                    path=f"{item_path}.path",
                )
            item_paths.add(boundary_item["path"])
            _enum(
                boundary_item["change"],
                "boundary_change",
                f"{item_path}.change",
            )
            _enum(boundary_item["impact"], "impact", f"{item_path}.impact")
            _enum(
                boundary_item["authorization"],
                "boundary_authorization",
                f"{item_path}.authorization",
            )
            _text(
                boundary_item["requirement_ref"],
                f"{item_path}.requirement_ref",
                nullable=True,
            )
            for field in (
                "evidence_ids",
                "qa_refs",
                "gate_ids",
                "invariant_ids",
                "claim_ids",
            ):
                _text_list(boundary_item[field], f"{item_path}.{field}")

            changed = boundary_item["change"] != "preserved"
            if changed and boundary_item["authorization"] == "not-required":
                raise ContractError(
                    "changed boundary item cannot use not-required authorization",
                    path=f"{item_path}.authorization",
                )
            if (
                boundary_item["authorization"] == "authorized"
                and not boundary_item["requirement_ref"]
            ):
                raise ContractError(
                    "authorized boundary item requires requirement_ref",
                    path=f"{item_path}.requirement_ref",
                )
            if (
                changed
                and not boundary_item["qa_refs"]
                and not boundary_item["gate_ids"]
            ):
                raise ContractError(
                    "changed boundary item must map to qa_refs or gate_ids",
                    path=item_path,
                )
            if changed:
                for field in ("invariant_ids", "claim_ids"):
                    if not boundary_item[field]:
                        raise ContractError(
                            f"changed boundary item requires {field}",
                            path=f"{item_path}.{field}",
                        )
        boundaries.append(item)
    return boundaries, boundary_ids


def _validate_gates(
    values: Any,
    candidate: dict[str, Any],
) -> tuple[list[dict[str, Any]], set[str]]:
    gates: list[dict[str, Any]] = []
    gate_ids: set[str] = set()
    resolution_fields = {
        "actor",
        "resolution_evidence",
        "waiver_authority",
        "pr_head_sha",
    }
    for index, raw in enumerate(_list(values, "gates")):
        path = f"gates[{index}]"
        item = _mapping(raw, path)
        _required(item, "gate", path)
        _unique_id(item, gate_ids, "gate", path)
        _same_candidate(item["candidate_ref"], candidate, f"{path}.candidate_ref")
        _enum(item["scope"], "gate_scope", f"{path}.scope")
        _enum(item["kind"], "gate_kind", f"{path}.kind")
        _enum(item["status"], "gate_status", f"{path}.status")
        _boolean(item["critical"], f"{path}.critical")
        _text(item["owner"], f"{path}.owner")
        _text(item["required_evidence"], f"{path}.required_evidence")
        provider_fields = {"provider_record_id", "capability"}
        if item["kind"] == "provider-capability":
            for field in provider_fields:
                _text(item.get(field), f"{path}.{field}")
            if item["capability"] not in CONTRACT["provider_capabilities"]:
                raise ContractError(
                    "must name a declared provider capability",
                    path=f"{path}.capability",
                )
            if not item["critical"]:
                raise ContractError(
                    "provider-capability gate must be critical",
                    path=f"{path}.critical",
                )
            if item["status"] not in {"open", "failed"}:
                raise ContractError(
                    "unavailable provider capability gate must be open or failed",
                    path=f"{path}.status",
                )
        elif provider_fields & item.keys():
            raise ContractError(
                "provider capability fields require provider-capability kind",
                path=path,
            )

        if item["status"] == "open":
            present = sorted(resolution_fields & item.keys())
            if present:
                raise ContractError(
                    f"open gate cannot contain resolution fields: {', '.join(present)}",
                    path=path,
                )
        else:
            for field in ("actor", "resolution_evidence"):
                _text(item.get(field), f"{path}.{field}")
            if item["status"] == "waived":
                _text(item.get("waiver_authority"), f"{path}.waiver_authority")
            if item["kind"] == "merge-authorization" and item["status"] == "passed":
                _text(item.get("pr_head_sha"), f"{path}.pr_head_sha")
        gates.append(item)
    return gates, gate_ids


def _validate_provider_records(
    values: Any,
    candidate: dict[str, Any],
) -> tuple[list[dict[str, Any]], set[str]]:
    records: list[dict[str, Any]] = []
    record_ids: set[str] = set()
    required_capabilities = set(CONTRACT["provider_capabilities"])
    for index, raw in enumerate(_list(values, "provider_records")):
        path = f"provider_records[{index}]"
        item = _mapping(raw, path)
        _required(item, "provider_record", path)
        _unique_id(item, record_ids, "provider record", path)
        _version(item["contract_version"], f"{path}.contract_version")
        _enum(item["provider"], "provider", f"{path}.provider")
        _same_candidate(item["candidate_ref"], candidate, f"{path}.candidate_ref")
        _text(item["pr_id"], f"{path}.pr_id")
        _text(item["head_sha"], f"{path}.head_sha")
        _enum(item["state"], "pr_state", f"{path}.state")

        capabilities = _mapping(item["capabilities"], f"{path}.capabilities")
        if set(capabilities) != required_capabilities:
            missing = sorted(required_capabilities - set(capabilities))
            extra = sorted(set(capabilities) - required_capabilities)
            details = []
            if missing:
                details.append(f"missing {', '.join(missing)}")
            if extra:
                details.append(f"unknown {', '.join(extra)}")
            raise ContractError("; ".join(details), path=f"{path}.capabilities")
        for name, supported in capabilities.items():
            _boolean(supported, f"{path}.capabilities.{name}")

        policy_checks = _list(item["policy_checks"], f"{path}.policy_checks")
        policy_ids: set[str] = set()
        for policy_index, raw_policy in enumerate(policy_checks):
            policy_path = f"{path}.policy_checks[{policy_index}]"
            policy = _mapping(raw_policy, policy_path)
            _required(policy, "policy_check", policy_path)
            _unique_id(policy, policy_ids, "policy", policy_path)
            _boolean(policy["required"], f"{policy_path}.required")
            _enum(policy["status"], "policy_status", f"{policy_path}.status")

        for approval_index, raw_approval in enumerate(
            _list(item["approvals"], f"{path}.approvals")
        ):
            approval_path = f"{path}.approvals[{approval_index}]"
            approval = _mapping(raw_approval, approval_path)
            _required(approval, "approval", approval_path)
            _text(approval["actor"], f"{approval_path}.actor")
            _text(approval["head_sha"], f"{approval_path}.head_sha")
            if approval["head_sha"] != item["head_sha"]:
                raise ContractError(
                    "approval head_sha must equal current provider head",
                    path=f"{approval_path}.head_sha",
                )
            _enum(approval["status"], "approval_status", f"{approval_path}.status")
        if capabilities["get_checks_and_policies"]:
            _boolean(
                item["required_policies_passed"],
                f"{path}.required_policies_passed",
            )
            required_policies_passed = all(
                not policy["required"] or policy["status"] == "passed"
                for policy in policy_checks
            )
            if item["required_policies_passed"] != required_policies_passed:
                raise ContractError(
                    "required_policies_passed must match required policy entries",
                    path=f"{path}.required_policies_passed",
                )
        elif policy_checks or item["required_policies_passed"] is not None:
            raise ContractError(
                "get_checks_and_policies is false but policy data was returned",
                path=f"{path}.policy_checks",
            )
        if not capabilities["get_approvals"] and item["approvals"]:
            raise ContractError(
                "get_approvals is false but approval data was returned",
                path=f"{path}.approvals",
            )
        if capabilities["get_pr_state"]:
            if item["state"] == "unknown":
                raise ContractError(
                    "get_pr_state is true but state is unknown",
                    path=f"{path}.state",
                )
        elif item["state"] != "unknown":
            raise ContractError(
                "get_pr_state is false but PR state data was returned",
                path=f"{path}.state",
            )
        limitations = _text_list(item["limitations"], f"{path}.limitations")
        if any(not supported for supported in capabilities.values()) and not limitations:
            raise ContractError(
                "unsupported capabilities require a declared limitation",
                path=f"{path}.limitations",
            )

        merge = _mapping(item["merge_result"], f"{path}.merge_result")
        _required(merge, "merge_result", f"{path}.merge_result")
        _enum(merge["status"], "merge_status", f"{path}.merge_result.status")
        for field in ("expected_head_sha", "provider_result_ref"):
            _text(merge[field], f"{path}.merge_result.{field}", nullable=True)
        _text(merge["observed_head_sha"], f"{path}.merge_result.observed_head_sha")
        if merge["observed_head_sha"] != item["head_sha"]:
            raise ContractError(
                "observed_head_sha must equal provider head_sha",
                path=f"{path}.merge_result.observed_head_sha",
            )
        if merge["status"] == "not-requested":
            if (
                merge["expected_head_sha"] is not None
                or merge["provider_result_ref"] is not None
            ):
                raise ContractError(
                    "not-requested merge cannot contain an expected head or result",
                    path=f"{path}.merge_result",
                )
        else:
            if not capabilities["merge_with_expected_head"]:
                raise ContractError(
                    "merge_with_expected_head is false but a merge result was returned",
                    path=f"{path}.merge_result.status",
                )
            if merge["expected_head_sha"] != item["head_sha"]:
                raise ContractError(
                    "merge expected_head_sha must equal provider head_sha",
                    path=f"{path}.merge_result.expected_head_sha",
                )
            if not merge["provider_result_ref"]:
                raise ContractError(
                    "observed merge result requires provider_result_ref",
                    path=f"{path}.merge_result.provider_result_ref",
                )
        if merge["status"] == "applied":
            if item["state"] != "merged":
                raise ContractError(
                    "applied merge result requires merged PR state",
                    path=f"{path}.state",
                )
        elif item["state"] == "merged":
            raise ContractError(
                "merged PR state requires applied merge result",
                path=f"{path}.merge_result.status",
            )
        records.append(item)
    return records, record_ids


def _validate_claims(
    values: Any,
    candidate: dict[str, Any],
) -> tuple[list[dict[str, Any]], set[str]]:
    claims: list[dict[str, Any]] = []
    claim_ids: set[str] = set()
    for index, raw in enumerate(_list(values, "claims")):
        path = f"claims[{index}]"
        item = _mapping(raw, path)
        _required(item, "claim", path)
        _unique_id(item, claim_ids, "claim", path)
        _same_candidate(item["candidate_ref"], candidate, f"{path}.candidate_ref")
        _text(item["text"], f"{path}.text")
        _enum(item["kind"], "claim_kind", f"{path}.kind")
        _enum(item["criticality"], "claim_criticality", f"{path}.criticality")
        _enum(
            item["environment_scope"],
            "environment_scope",
            f"{path}.environment_scope",
        )
        _enum(
            item["boundary_scope"],
            "boundary_scope",
            f"{path}.boundary_scope",
        )
        _enum(item["status"], "claim_status", f"{path}.status")
        causal_chain = _list(item["causal_chain"], f"{path}.causal_chain")
        if not causal_chain:
            raise ContractError("must not be empty", path=f"{path}.causal_chain")
        for step_index, raw_step in enumerate(causal_chain):
            step_path = f"{path}.causal_chain[{step_index}]"
            step = _mapping(raw_step, step_path)
            _required(step, "causal_step", step_path)
            _text(step["step"], f"{step_path}.step")
            _enum(step["controller"], "controller", f"{step_path}.controller")
            _boolean(step["observed"], f"{step_path}.observed")
        _text_list(item["uncovered_segments"], f"{path}.uncovered_segments")
        _enum(item["requested_claim"], "max_claim", f"{path}.requested_claim")
        _text_list(item["evidence_ids"], f"{path}.evidence_ids")
        _text_list(item["gate_ids"], f"{path}.gate_ids")
        claims.append(item)
    return claims, claim_ids


def _validated_verification(
    raw: Any,
    candidate: dict[str, Any],
) -> dict[str, Any]:
    path = "verification"
    verification = _mapping(raw, path)
    _required(verification, "verification", path)
    _same_candidate(
        verification["candidate_ref"],
        candidate,
        f"{path}.candidate_ref",
    )
    _enum(
        verification["implementation_status"],
        "implementation_status",
        f"{path}.implementation_status",
    )
    _enum(verification["max_claim"], "max_claim", f"{path}.max_claim")
    _enum(
        verification["release_status"],
        "release_status",
        f"{path}.release_status",
    )
    _enum(
        verification["final_disposition"],
        "final_disposition",
        f"{path}.final_disposition",
    )
    _enum(
        verification["requested_operation"],
        "requested_operation",
        f"{path}.requested_operation",
    )
    for field in (
        "evidence_ids",
        "invariant_ids",
        "boundary_delta_ids",
        "gate_ids",
        "provider_record_ids",
        "claim_ids",
        "blocking_gaps",
        "forbidden_claims",
    ):
        _text_list(verification[field], f"{path}.{field}")
    return verification


def _validate_merge_authorization(
    raw: Any,
    candidate: dict[str, Any],
    gates_by_id: dict[str, dict[str, Any]],
    providers_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    path = "merge_authorization"
    authorization = _mapping(raw, path)
    _required(authorization, "merge_authorization", path)
    _same_candidate(
        authorization["candidate_ref"],
        candidate,
        f"{path}.candidate_ref",
    )
    for field in ("gate_id", "provider_record_id", "pr_head_sha"):
        _text(authorization[field], f"{path}.{field}")
    gate = gates_by_id.get(authorization["gate_id"])
    if gate is None:
        raise ContractError(
            f"dangling gate id {authorization['gate_id']}",
            path=f"{path}.gate_id",
        )
    if gate["kind"] != "merge-authorization" or gate["status"] != "passed":
        raise ContractError(
            "must reference a passed merge-authorization gate",
            path=f"{path}.gate_id",
        )
    provider = providers_by_id.get(authorization["provider_record_id"])
    if provider is None:
        raise ContractError(
            f"dangling provider record id {authorization['provider_record_id']}",
            path=f"{path}.provider_record_id",
        )
    expected = provider["head_sha"]
    if (
        authorization["pr_head_sha"] != expected
        or gate.get("pr_head_sha") != expected
    ):
        raise ContractError(
            "merge authorization, gate, and provider PR head SHA must match",
            path=f"{path}.pr_head_sha",
        )
    return authorization


def _critical_gate_unresolved(gate: dict[str, Any]) -> bool:
    return bool(gate["critical"]) and gate["status"] not in {"passed", "waived"}


def _implementation_complete(bundle: dict[str, Any]) -> bool:
    stage_ceiling = _stage_ceiling_rank(bundle)
    high_impact_boundary_blocker = any(
        boundary_item["impact"] == "high"
        and boundary_item["change"] != "preserved"
        and boundary_item["authorization"] != "authorized"
        for boundary in bundle["external_boundary_delta"]
        for boundary_item in boundary["items"]
    )
    high_impact_invariant_blocker = any(
        invariant["impact"] == "high"
        and invariant["status"] == "unknown"
        for invariant in bundle["invariants"]
    )
    return (
        stage_ceiling >= CLAIM_RANK["implementation-complete"]
        and not high_impact_boundary_blocker
        and not high_impact_invariant_blocker
    )


def _stage_ceiling_rank(bundle: dict[str, Any]) -> int:
    stages = {stage["stage"]: stage["result"] for stage in bundle["stage_results"]}
    ceiling = CLAIM_RANK["none"]
    required_outcomes = CONTRACT["reduction_policy"]["required_stage_outcomes"]
    for claim, rank in sorted(CLAIM_RANK.items(), key=lambda item: item[1]):
        if claim == "none":
            continue
        requirements = required_outcomes[claim]
        if all(stages.get(stage) in allowed for stage, allowed in requirements.items()):
            ceiling = rank
    return ceiling


def _evidence_ceiling_rank(evidence_items: list[dict[str, Any]]) -> int:
    if not evidence_items:
        return CLAIM_RANK[
            CONTRACT["reduction_policy"]["evidence_less_claim_ceiling"]
        ]

    ceilings = CONTRACT["evidence_ceilings"]
    best_rank = CLAIM_RANK["none"]
    contradictory_rank = CLAIM_RANK["production-ready"]
    for evidence in evidence_items:
        supported_rank = CLAIM_RANK[evidence["supports_claim"]]
        if evidence["result"] != "pass":
            if evidence["result"] == "fail":
                contradictory_rank = min(
                    contradictory_rank,
                    max(0, supported_rank - 1),
                )
            continue
        best_rank = max(
            best_rank,
            min(
                supported_rank,
                ceilings["class"][evidence["class"]],
                ceilings["environment_scope"][evidence["environment_scope"]],
                ceilings["boundary_scope"][evidence["boundary_scope"]],
                ceilings["causal_coverage"][evidence["causal_coverage"]],
            ),
        )
    return min(best_rank, contradictory_rank)


def _claim_supported_rank(
    claim: dict[str, Any],
    evidence_by_id: dict[str, dict[str, Any]],
) -> int:
    policy = CONTRACT["reduction_policy"]
    evidence_items = [evidence_by_id[item_id] for item_id in claim["evidence_ids"]]
    target_ranks = policy["claim_target_scope_rank"]
    rank = min(
        CLAIM_RANK[claim["requested_claim"]],
        CLAIM_RANK[policy["claim_status_ceiling"][claim["status"]]],
        target_ranks["environment_scope"][claim["environment_scope"]],
        target_ranks["boundary_scope"][claim["boundary_scope"]],
        _evidence_ceiling_rank(evidence_items),
    )
    causal_incomplete = bool(claim["uncovered_segments"]) or any(
        not step["observed"] for step in claim["causal_chain"]
    )
    if causal_incomplete:
        rank = min(
            rank,
            CLAIM_RANK[policy["incomplete_causal_ceiling"]],
        )
    return rank


def _claim_ceiling(bundle: dict[str, Any], implementation_complete: bool) -> str:
    if not implementation_complete:
        return "none"

    if not bundle["claims"]:
        return "implementation-complete"
    evidence_by_id = {item["id"]: item for item in bundle["evidence"]}
    claim_rank = min(
        _claim_supported_rank(claim, evidence_by_id)
        for claim in bundle["claims"]
    )
    claim_rank = max(claim_rank, CLAIM_RANK["none"])
    return CLAIM_BY_RANK[min(claim_rank, _stage_ceiling_rank(bundle))]


def reduce_claims(value: Any) -> dict[str, str]:
    """Derive disposition solely from already classified bundle facts."""

    bundle = _mapping(value, "bundle")
    complete = _implementation_complete(bundle)
    max_claim = _claim_ceiling(bundle, complete)
    policy = CONTRACT["reduction_policy"]
    stages = {stage["stage"]: stage["result"] for stage in bundle["stage_results"]}
    evidence_by_id = {item["id"]: item for item in bundle["evidence"]}
    stage_ceiling_rank = _stage_ceiling_rank(bundle)
    release_critical_claim_gap = any(
        claim["criticality"] in policy["release_criticalities"]
        and min(
            _claim_supported_rank(claim, evidence_by_id),
            stage_ceiling_rank,
        )
        < CLAIM_RANK[claim["requested_claim"]]
        for claim in bundle["claims"]
    )
    release_blocked = (
        not complete
        or any(_critical_gate_unresolved(gate) for gate in bundle["gates"])
        or any(
            evidence["critical"] and evidence["result"] != "pass"
            for evidence in bundle["evidence"]
        )
        or any(
            not provider["required_policies_passed"]
            for provider in bundle["provider_records"]
        )
        or any(
            result in policy["release_blocking_stage_results"]
            for result in stages.values()
        )
        or release_critical_claim_gap
        or (
            bundle["verification"]["requested_operation"]
            in policy["merge_authorization_required_for_operations"]
            and "merge_authorization" not in bundle
        )
    )
    release_status = "blocked" if release_blocked else "eligible"
    if not complete:
        final_disposition = "unsupported"
    elif release_blocked:
        final_disposition = "release-blocked"
    elif max_claim == "none":
        final_disposition = "unsupported"
    else:
        final_disposition = max_claim
    return {
        "implementation_status": "complete" if complete else "incomplete",
        "max_claim": max_claim,
        "release_status": release_status,
        "final_disposition": final_disposition,
    }


def validate_bundle(
    value: Any,
    *,
    current_candidate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate a complete v1 bundle and reject stale or contradictory artifacts."""

    bundle = _mapping(value, "bundle")
    _required(bundle, "bundle", "bundle")
    _version(bundle["contract_version"], "bundle.contract_version")
    if bundle["artifact_type"] != CONTRACT["artifact_type"]:
        raise ContractError(
            f"must be {CONTRACT['artifact_type']}",
            path="bundle.artifact_type",
        )
    _text(bundle["ticket_id"], "bundle.ticket_id")
    _text(bundle["ticket_envelope_ref"], "bundle.ticket_envelope_ref")
    candidate = _candidate_ref(bundle["candidate_ref"], "bundle.candidate_ref")
    if current_candidate is not None:
        _same_candidate(
            candidate,
            _candidate_ref(current_candidate, "current_candidate"),
            "bundle.candidate_ref",
            stale_message=True,
        )

    stages = _validate_stages(bundle["stage_results"], candidate)
    qa_stage_ids = {
        stage["id"]
        for stage in stages
        if stage["stage"] in {"qa-plan", "qa-execute"}
    }
    evidence, evidence_ids = _validate_evidence(bundle["evidence"], candidate)
    invariants, invariant_ids = _validate_invariants(bundle["invariants"], candidate)
    boundaries, boundary_ids = _validate_boundaries(
        bundle["external_boundary_delta"],
        candidate,
    )
    gates, gate_ids = _validate_gates(bundle["gates"], candidate)
    providers, provider_ids = _validate_provider_records(
        bundle["provider_records"],
        candidate,
    )
    claims, claim_ids = _validate_claims(bundle["claims"], candidate)
    verification = _validated_verification(bundle["verification"], candidate)

    gates_by_id = {item["id"]: item for item in gates}
    providers_by_id = {item["id"]: item for item in providers}
    provider_capability_gates: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for gate in gates:
        if gate["kind"] != "provider-capability":
            continue
        provider = providers_by_id.get(gate["provider_record_id"])
        if provider is None:
            raise ContractError(
                f"dangling provider record id {gate['provider_record_id']}",
                path=f"gates[{gate['id']}].provider_record_id",
            )
        capability = gate["capability"]
        if provider["capabilities"][capability]:
            raise ContractError(
                "provider-capability gate contradicts an available capability",
                path=f"gates[{gate['id']}].capability",
            )
        key = (provider["id"], capability)
        provider_capability_gates.setdefault(key, []).append(gate)

    capability_policy = CONTRACT["reduction_policy"][
        "required_provider_capabilities"
    ]
    operation_capabilities = set(
        capability_policy["requested_operation"][
            verification["requested_operation"]
        ]
    )
    if operation_capabilities and not providers:
        raise ContractError(
            f"{verification['requested_operation']} requires at least one "
            "normalized provider record",
            path="verification.requested_operation",
        )
    required_capabilities = set(operation_capabilities)
    for claim in claims:
        if claim["boundary_scope"] == "internal":
            continue
        required_capabilities.update(
            capability_policy["max_claim"][claim["requested_claim"]]
        )
    for provider in providers:
        for capability in sorted(required_capabilities):
            if provider["capabilities"][capability]:
                continue
            matching_gates = provider_capability_gates.get(
                (provider["id"], capability),
                [],
            )
            if len(matching_gates) != 1:
                raise ContractError(
                    f"unavailable required capability {capability} requires exactly "
                    "one explicit provider-capability gate",
                    path=f"provider_records[{provider['id']}].capabilities.{capability}",
                )

    for index, stage in enumerate(stages):
        path = f"stage_results[{index}]"
        _references(stage["evidence_ids"], evidence_ids, "evidence", f"{path}.evidence_ids")
        _references(
            stage["invariant_ids"],
            invariant_ids,
            "invariant",
            f"{path}.invariant_ids",
        )
        _references(
            stage["boundary_delta_ids"],
            boundary_ids,
            "boundary delta",
            f"{path}.boundary_delta_ids",
        )
        _references(stage["gate_ids"], gate_ids, "gate", f"{path}.gate_ids")
        _references(
            stage["provider_record_ids"],
            provider_ids,
            "provider record",
            f"{path}.provider_record_ids",
        )
        if stage["result"] == "blocked" and not any(
            gates_by_id[gate_id]["status"] == "open"
            for gate_id in stage["gate_ids"]
        ):
            raise ContractError(
                "blocked stage result must reference an open gate",
                path=f"{path}.gate_ids",
            )

    for index, invariant in enumerate(invariants):
        _references(
            invariant["evidence_ids"],
            evidence_ids,
            "evidence",
            f"invariants[{index}].evidence_ids",
        )
    for index, boundary in enumerate(boundaries):
        for item_index, boundary_item in enumerate(boundary["items"]):
            path = f"external_boundary_delta[{index}].items[{item_index}]"
            for field, known, label in (
                ("evidence_ids", evidence_ids, "evidence"),
                ("qa_refs", qa_stage_ids, "QA stage result"),
                ("gate_ids", gate_ids, "gate"),
                ("invariant_ids", invariant_ids, "invariant"),
                ("claim_ids", claim_ids, "claim"),
            ):
                _references(
                    boundary_item[field],
                    known,
                    label,
                    f"{path}.{field}",
                )
    for index, claim in enumerate(claims):
        _references(
            claim["evidence_ids"],
            evidence_ids,
            "evidence",
            f"claims[{index}].evidence_ids",
        )
        _references(
            claim["gate_ids"],
            gate_ids,
            "gate",
            f"claims[{index}].gate_ids",
        )

    verification_reference_sets = {
        "evidence_ids": (evidence_ids, "evidence"),
        "invariant_ids": (invariant_ids, "invariant"),
        "boundary_delta_ids": (boundary_ids, "boundary delta"),
        "gate_ids": (gate_ids, "gate"),
        "provider_record_ids": (provider_ids, "provider record"),
        "claim_ids": (claim_ids, "claim"),
    }
    for field, (known, label) in verification_reference_sets.items():
        _references(
            verification[field],
            known,
            label,
            f"verification.{field}",
        )

    authorization = None
    if "merge_authorization" in bundle:
        authorization = _validate_merge_authorization(
            bundle["merge_authorization"],
            candidate,
            gates_by_id,
            providers_by_id,
        )
    if any(
        provider["merge_result"]["status"] == "applied" for provider in providers
    ) and authorization is None:
        raise ContractError(
            "applied provider merge requires merge_authorization",
            path="bundle.merge_authorization",
        )

    reduced = reduce_claims(bundle)
    declared = {
        field: verification[field]
        for field in (
            "implementation_status",
            "max_claim",
            "release_status",
            "final_disposition",
        )
    }
    if declared != reduced:
        raise ContractError(
            f"declared verification does not match deterministic reduction: "
            f"expected {json.dumps(reduced, sort_keys=True)}",
            path="verification",
        )
    return copy.deepcopy(bundle)


def _markdown_outside_fences(body: str) -> tuple[str, int, int]:
    outside_lines: list[str] = []
    active_fence: tuple[str, int, bool] | None = None
    mermaid_openings = 0
    complete_mermaid_blocks = 0

    for line in body.splitlines():
        if active_fence is None:
            opening = re.fullmatch(r" {0,3}(`{3,}|~{3,})(.*)", line)
            if opening is None:
                outside_lines.append(line)
                continue
            fence, raw_info = opening.groups()
            info_tokens = raw_info.strip().split()
            is_mermaid = bool(info_tokens) and info_tokens[0].casefold() == "mermaid"
            if is_mermaid:
                mermaid_openings += 1
            active_fence = (fence[0], len(fence), is_mermaid)
            outside_lines.append("")
            continue

        fence_character, minimum_length, is_mermaid = active_fence
        closing = re.fullmatch(
            rf" {{0,3}}{re.escape(fence_character)}{{{minimum_length},}}[ \t]*",
            line,
        )
        if closing is not None:
            if is_mermaid:
                complete_mermaid_blocks += 1
            active_fence = None
        outside_lines.append("")

    return "\n".join(outside_lines), mermaid_openings, complete_mermaid_blocks


def validate_pr_body(
    body: str,
    value: Any,
    *,
    pr_head_sha: str | None = None,
) -> None:
    """Validate literal PR-body structure against a validated bundle."""

    if not isinstance(body, str):
        raise ContractError("must be text", path="pr_body")
    bundle = validate_bundle(value)
    outside_fences, mermaid_openings, mermaid_count = _markdown_outside_fences(
        body
    )
    required_headings = CONTRACT["pr_body"]["required_headings"]
    for heading in required_headings:
        if not re.search(
            rf"(?m)^## {re.escape(heading)}\s*$",
            outside_fences,
        ):
            raise ContractError(
                f"missing required heading ## {heading}",
                path="pr_body",
            )
    expected_mermaid = CONTRACT["pr_body"]["mermaid_blocks"]
    if mermaid_openings != expected_mermaid or mermaid_count != expected_mermaid:
        raise ContractError(
            f"must contain exactly one Mermaid block, found {mermaid_count}",
            path="pr_body",
        )

    lowered = body.casefold()
    lowered_lines = lowered.splitlines()
    for evidence in bundle["evidence"]:
        requires_declaration = (
            evidence["class"] in {"simulated", "live"}
            or evidence["result"] == "skipped"
        )
        if not requires_declaration:
            continue
        evidence_id = evidence["id"]
        evidence_lines = [
            line for line in lowered_lines if evidence_id.casefold() in line
        ]
        if not evidence_lines:
            raise ContractError(
                f"evidence {evidence_id} must be visible",
                path="pr_body",
            )
        for field in ("class", "result"):
            literal = evidence[field]
            if not any(literal.casefold() in line for line in evidence_lines):
                raise ContractError(
                    f"evidence {evidence_id} must declare {literal}",
                    path="pr_body",
                )

    for gate in bundle["gates"]:
        if gate["status"] in {"open", "failed"}:
            gate_id = gate["id"]
            gate_lines = [
                line for line in lowered_lines if gate_id.casefold() in line
            ]
            if not gate_lines:
                raise ContractError(
                    f"{gate['status']} gate {gate_id} must be visible",
                    path="pr_body",
                )
            status_tokens = [
                status
                for line in gate_lines
                for status in CONTRACT["enums"]["gate_status"]
                for _ in re.findall(rf"\b{re.escape(status)}\b", line)
            ]
            if status_tokens != [gate["status"]]:
                raise ContractError(
                    f"{gate['status']} gate {gate_id} must declare status "
                    f"{gate['status']}; expected one unambiguous status "
                    f"{gate['status']} token",
                    path="pr_body",
                )

    for wording in bundle["verification"]["forbidden_claims"]:
        if wording.casefold() in lowered:
            raise ContractError(
                f"contains forbidden wording: {wording}",
                path="pr_body",
            )

    providers = bundle["provider_records"]
    head_sensitive = bool(providers) or bundle["verification"]["release_status"] == "eligible"
    if head_sensitive and pr_head_sha is None:
        raise ContractError(
            "observed PR head SHA is required",
            path="pr_head_sha",
        )
    if providers and any(provider["head_sha"] != pr_head_sha for provider in providers):
        raise ContractError(
            "observed PR head SHA must match normalized provider head",
            path="pr_head_sha",
        )

    authorization = bundle.get("merge_authorization")
    operation_requires_authorization = (
        bundle["verification"]["requested_operation"]
        in CONTRACT["reduction_policy"][
            "merge_authorization_required_for_operations"
        ]
        or any(
            provider["merge_result"]["status"] == "applied"
            for provider in providers
        )
    )
    if operation_requires_authorization and authorization is None:
        raise ContractError(
            "merge authorization is required for this operation",
            path="merge_authorization",
        )
    if authorization is not None and pr_head_sha is not None:
        if pr_head_sha != authorization["pr_head_sha"]:
            raise ContractError(
                "PR head SHA does not match merge authorization",
                path="pr_head_sha",
            )


def _read_json(path: str) -> Any:
    try:
        with Path(path).open(encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError) as error:
        raise ContractError(str(error), path=path) from error


def _read_text(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError as error:
        raise ContractError(str(error), path=path) from error


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate verification-audit contract v1 artifacts."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate")
    validate.add_argument("bundle")
    validate.add_argument("--current-candidate")

    reduce_parser = subparsers.add_parser("reduce")
    reduce_parser.add_argument("bundle")

    pr_body = subparsers.add_parser("validate-pr")
    pr_body.add_argument("bundle")
    pr_body.add_argument("body")
    pr_body.add_argument("--pr-head-sha")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        bundle = _read_json(args.bundle)
        if args.command == "validate":
            current = (
                _read_json(args.current_candidate)
                if args.current_candidate is not None
                else None
            )
            result = validate_bundle(bundle, current_candidate=current)
        elif args.command == "reduce":
            validate_bundle(bundle)
            result = reduce_claims(bundle)
        elif args.command == "validate-pr":
            body = _read_text(args.body)
            validate_pr_body(
                body,
                bundle,
                pr_head_sha=args.pr_head_sha,
            )
            result = {"status": "valid"}
    except ContractError as error:
        json.dump(
            {
                "error": "contract-invalid",
                "diagnostics": [
                    {
                        "path": getattr(error, "path", None),
                        "message": str(error),
                    }
                ],
            },
            sys.stderr,
            sort_keys=True,
        )
        sys.stderr.write("\n")
        return 2
    json.dump(result, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
