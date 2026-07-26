from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT / "tests" / "fixtures"
sys.path.insert(0, str(SCRIPTS))

from verification_contract import (  # noqa: E402
    ContractError,
    reduce_claims,
    validate_bundle,
    validate_pr_body,
)


def candidate(tree_oid: str = "tree-123") -> dict[str, object]:
    return {
        "contract_version": 1,
        "base_sha": "base-123",
        "tree_oid": tree_oid,
        "ticket_digest": "ticket-123",
    }


def complete_bundle() -> dict[str, object]:
    ref = candidate()
    return {
        "contract_version": 1,
        "artifact_type": "verification-bundle",
        "ticket_id": "05",
        "candidate_ref": ref,
        "stage_results": [
            {
                "id": "stage-verify",
                "stage": "verify",
                "result": "pass",
                "candidate_ref": ref,
                "artifact": "artifacts/verification.json",
                "evidence_ids": ["e-live"],
                "invariant_ids": ["inv-no-overclaim"],
                "boundary_delta_ids": ["boundary-provider"],
                "gate_ids": ["gate-merge"],
                "provider_record_ids": ["provider-pr"],
                "limitations": [],
            },
            {
                "id": "stage-implement",
                "stage": "implement",
                "result": "pass",
                "candidate_ref": ref,
                "artifact": "artifacts/implementation.json",
                "evidence_ids": ["e-live"],
                "invariant_ids": ["inv-no-overclaim"],
                "boundary_delta_ids": ["boundary-provider"],
                "gate_ids": [],
                "provider_record_ids": [],
                "limitations": [],
            },
            {
                "id": "stage-review",
                "stage": "review",
                "result": "pass",
                "candidate_ref": ref,
                "artifact": "artifacts/review.json",
                "evidence_ids": ["e-live"],
                "invariant_ids": ["inv-no-overclaim"],
                "boundary_delta_ids": ["boundary-provider"],
                "gate_ids": [],
                "provider_record_ids": [],
                "limitations": [],
            },
            {
                "id": "stage-qa-plan",
                "stage": "qa-plan",
                "result": "pass",
                "candidate_ref": ref,
                "artifact": "artifacts/qa-plan.json",
                "evidence_ids": ["e-live"],
                "invariant_ids": ["inv-no-overclaim"],
                "boundary_delta_ids": ["boundary-provider"],
                "gate_ids": [],
                "provider_record_ids": [],
                "limitations": [],
            },
            {
                "id": "stage-qa-execute",
                "stage": "qa-execute",
                "result": "pass",
                "candidate_ref": ref,
                "artifact": "artifacts/qa-execute.json",
                "evidence_ids": ["e-live"],
                "invariant_ids": ["inv-no-overclaim"],
                "boundary_delta_ids": ["boundary-provider"],
                "gate_ids": [],
                "provider_record_ids": [],
                "limitations": [],
            },
        ],
        "evidence": [
            {
                "id": "e-live",
                "candidate_ref": ref,
                "class": "live",
                "environment": "production-eu",
                "environment_scope": "production",
                "boundary_scope": "live-external",
                "result": "pass",
                "critical": True,
                "supports_claim": "production-ready",
                "causal_coverage": "complete",
                "injection_point": "provider merge dry-run",
                "observed_segment": "expected-head through policy result",
                "artifact": "artifacts/live-provider.json",
                "limitations": [],
            }
        ],
        "invariants": [
            {
                "id": "inv-no-overclaim",
                "candidate_ref": ref,
                "description": "No claim exceeds classified evidence.",
                "status": "preserved",
                "impact": "high",
                "evidence_ids": ["e-live"],
                "authorization_ref": None,
            }
        ],
        "external_boundary_delta": [
            {
                "id": "boundary-provider",
                "candidate_ref": ref,
                "boundary": "RemoteProvider normalized record",
                "controller": "external-provider",
                "baseline_source": "architecture:D7",
                "before_contract": "No normalized provider verification record.",
                "after_contract": "Provider facts use the v1 normalized record.",
                "items": [
                    {
                        "path": "provider_record.contract_version",
                        "change": "added",
                        "impact": "high",
                        "authorization": "authorized",
                        "requirement_ref": "architecture:D7",
                        "evidence_ids": ["e-live"],
                        "qa_refs": ["stage-qa-execute"],
                        "gate_ids": [],
                        "invariant_ids": ["inv-no-overclaim"],
                        "claim_ids": ["claim-production"],
                    }
                ],
            }
        ],
        "gates": [
            {
                "id": "gate-merge",
                "candidate_ref": ref,
                "scope": "ticket",
                "kind": "merge-authorization",
                "critical": True,
                "status": "passed",
                "owner": "maintainer",
                "required_evidence": "Approval for exact PR head",
                "actor": "human:maintainer",
                "resolution_evidence": "approval-record-1",
                "pr_head_sha": "head-123",
            }
        ],
        "provider_records": [
            {
                "id": "provider-pr",
                "contract_version": 1,
                "provider": "github",
                "candidate_ref": ref,
                "pr_id": "42",
                "head_sha": "head-123",
                "state": "open",
                "capabilities": {
                    "create_or_update_pr": True,
                    "get_pr_state": True,
                    "retarget_pr": True,
                    "get_checks_and_policies": True,
                    "get_approvals": True,
                    "merge_with_expected_head": True,
                },
                "policy_checks": [
                    {"id": "ci", "required": True, "status": "passed"}
                ],
                "approvals": [
                    {
                        "actor": "human:maintainer",
                        "head_sha": "head-123",
                        "status": "approved",
                    }
                ],
                "required_policies_passed": True,
                "limitations": [],
                "merge_result": {
                    "status": "not-requested",
                    "expected_head_sha": None,
                    "observed_head_sha": "head-123",
                    "provider_result_ref": None,
                },
            }
        ],
        "claims": [
            {
                "id": "claim-production",
                "candidate_ref": ref,
                "text": "Production readiness for the normalized provider record.",
                "kind": "release",
                "criticality": "critical",
                "environment_scope": "production",
                "boundary_scope": "live-external",
                "causal_chain": [
                    {
                        "step": "validate normalized provider record",
                        "controller": "codebase",
                        "observed": True,
                    },
                    {
                        "step": "observe provider policy and head",
                        "controller": "external-provider",
                        "observed": True,
                    },
                ],
                "uncovered_segments": [],
                "status": "supported",
                "requested_claim": "production-ready",
                "evidence_ids": ["e-live"],
                "gate_ids": ["gate-merge"],
            }
        ],
        "verification": {
            "candidate_ref": ref,
            "implementation_status": "complete",
            "max_claim": "production-ready",
            "release_status": "eligible",
            "final_disposition": "production-ready",
            "evidence_ids": ["e-live"],
            "invariant_ids": ["inv-no-overclaim"],
            "boundary_delta_ids": ["boundary-provider"],
            "gate_ids": ["gate-merge"],
            "provider_record_ids": ["provider-pr"],
            "claim_ids": ["claim-production"],
            "blocking_gaps": [],
            "forbidden_claims": ["works everywhere"],
            "requested_operation": "open-pr",
        },
        "merge_authorization": {
            "candidate_ref": ref,
            "gate_id": "gate-merge",
            "provider_record_id": "provider-pr",
            "pr_head_sha": "head-123",
        },
    }


def bundle_for_reduction_case(case: dict[str, object]) -> dict[str, object]:
    raw = complete_bundle()
    mode = case["mode"]
    evidence = raw["evidence"][0]  # type: ignore[index]
    if mode == "partial":
        evidence.update(
            {
                "class": "unit",
                "environment_scope": "local",
                "boundary_scope": "internal",
                "supports_claim": "behavior-verified",
                "causal_coverage": "partial",
            }
        )
        raw["claims"][0]["requested_claim"] = "deployable-for-test"  # type: ignore[index]
    elif mode == "contradictory":
        contradiction = copy.deepcopy(evidence)
        contradiction.update(
            {
                "id": "e-contradiction",
                "result": "fail",
                "supports_claim": "behavior-verified",
                "artifact": "artifacts/contradiction.json",
            }
        )
        raw["evidence"].append(contradiction)  # type: ignore[index]
        raw["verification"]["evidence_ids"].append("e-contradiction")  # type: ignore[index]
        raw["claims"][0]["evidence_ids"].append("e-contradiction")  # type: ignore[index]
    elif mode == "gated":
        gate = raw["gates"][0]  # type: ignore[index]
        gate["status"] = "open"
        gate.pop("actor")
        gate.pop("resolution_evidence")
        gate.pop("pr_head_sha")
        raw.pop("merge_authorization")
    elif mode == "unsupported":
        boundary_item = raw["external_boundary_delta"][0]["items"][0]  # type: ignore[index]
        boundary_item["authorization"] = "unresolved"
        boundary_item["requirement_ref"] = None
        boundary_item["gate_ids"] = ["gate-merge"]
    elif mode == "implementation-only":
        evidence.update(
            {
                "class": "static",
                "environment_scope": "local",
                "boundary_scope": "internal",
                "supports_claim": "implementation-complete",
                "causal_coverage": "none",
            }
        )
        raw["claims"][0]["requested_claim"] = "implementation-complete"  # type: ignore[index]
    elif mode == "behavior":
        evidence.update(
            {
                "class": "integration",
                "environment_scope": "staging",
                "boundary_scope": "internal",
                "supports_claim": "behavior-verified",
                "causal_coverage": "complete",
            }
        )
        raw["claims"][0]["requested_claim"] = "behavior-verified"  # type: ignore[index]
    elif mode != "complete":
        raise AssertionError(f"unknown fixture mode {mode}")
    raw["verification"].update(case["expected"])  # type: ignore[index]
    return raw


def bundle_without_provider(operation: str) -> dict[str, object]:
    raw = complete_bundle()
    raw["provider_records"] = []
    raw.pop("merge_authorization")
    for stage in raw["stage_results"]:  # type: ignore[union-attr]
        stage["provider_record_ids"] = []
    raw["verification"]["provider_record_ids"] = []  # type: ignore[index]
    raw["verification"]["requested_operation"] = operation  # type: ignore[index]
    return raw


class BundleValidationTests(unittest.TestCase):
    def test_valid_bundle_is_accepted_and_copied(self) -> None:
        raw = complete_bundle()
        validated = validate_bundle(raw, current_candidate=candidate())
        self.assertEqual(validated, raw)
        self.assertIsNot(validated, raw)

    def test_missing_required_field_is_rejected(self) -> None:
        raw = complete_bundle()
        del raw["verification"]["release_status"]  # type: ignore[index]
        with self.assertRaisesRegex(ContractError, "release_status"):
            validate_bundle(raw)

    def test_invalid_enum_is_rejected(self) -> None:
        raw = complete_bundle()
        raw["evidence"][0]["class"] = "probably-live"  # type: ignore[index]
        with self.assertRaisesRegex(ContractError, "evidence\\[0\\]\\.class"):
            validate_bundle(raw)

    def test_dangling_reference_is_rejected(self) -> None:
        raw = complete_bundle()
        raw["stage_results"][0]["evidence_ids"] = ["missing"]  # type: ignore[index]
        with self.assertRaisesRegex(ContractError, "dangling evidence id missing"):
            validate_bundle(raw)

    def test_duplicate_ids_are_rejected(self) -> None:
        raw = complete_bundle()
        raw["evidence"].append(copy.deepcopy(raw["evidence"][0]))  # type: ignore[index]
        with self.assertRaisesRegex(ContractError, "duplicate evidence id e-live"):
            validate_bundle(raw)

    def test_blocked_stage_requires_open_gate(self) -> None:
        raw = complete_bundle()
        raw["stage_results"][0]["result"] = "blocked"  # type: ignore[index]
        with self.assertRaisesRegex(ContractError, "blocked stage result"):
            validate_bundle(raw)

    def test_resolved_gate_requires_actor_and_evidence(self) -> None:
        raw = complete_bundle()
        del raw["gates"][0]["resolution_evidence"]  # type: ignore[index]
        with self.assertRaisesRegex(ContractError, "resolution_evidence"):
            validate_bundle(raw)

    def test_open_gate_rejects_resolution_fields(self) -> None:
        raw = complete_bundle()
        gate = raw["gates"][0]  # type: ignore[index]
        gate["status"] = "open"
        with self.assertRaisesRegex(ContractError, "open gate"):
            validate_bundle(raw)

    def test_modified_boundary_requires_complete_mapping(self) -> None:
        raw = complete_bundle()
        boundary_item = raw["external_boundary_delta"][0]["items"][0]  # type: ignore[index]
        boundary_item["qa_refs"] = []
        with self.assertRaisesRegex(ContractError, "qa_refs or gate_ids"):
            validate_bundle(raw)

    def test_stale_candidate_is_rejected(self) -> None:
        with self.assertRaisesRegex(ContractError, "stale candidate"):
            validate_bundle(complete_bundle(), current_candidate=candidate("tree-new"))

    def test_nested_artifact_for_different_candidate_is_rejected(self) -> None:
        raw = complete_bundle()
        raw["evidence"][0]["candidate_ref"] = candidate("tree-old")  # type: ignore[index]
        with self.assertRaisesRegex(ContractError, "does not match bundle candidate"):
            validate_bundle(raw)

    def test_merge_authorization_is_bound_to_provider_pr_head(self) -> None:
        raw = complete_bundle()
        raw["merge_authorization"]["pr_head_sha"] = "different-head"  # type: ignore[index]
        with self.assertRaisesRegex(ContractError, "PR head SHA"):
            validate_bundle(raw)

    def test_applied_merge_requires_exact_authorization(self) -> None:
        raw = complete_bundle()
        merge_result = raw["provider_records"][0]["merge_result"]  # type: ignore[index]
        merge_result["status"] = "applied"
        merge_result["expected_head_sha"] = "head-123"
        merge_result["provider_result_ref"] = "provider-merge-result"
        raw["provider_records"][0]["state"] = "merged"  # type: ignore[index]
        validate_bundle(raw)
        del raw["merge_authorization"]
        with self.assertRaisesRegex(ContractError, "merge_authorization"):
            validate_bundle(raw)

    def test_provider_limitations_are_required(self) -> None:
        raw = complete_bundle()
        del raw["provider_records"][0]["limitations"]  # type: ignore[index]
        with self.assertRaisesRegex(ContractError, "limitations"):
            validate_bundle(raw)

    def test_github_and_azure_devops_use_same_normalized_shape(self) -> None:
        github = complete_bundle()
        azure = complete_bundle()
        azure["provider_records"][0]["provider"] = "azure-devops"  # type: ignore[index]
        validate_bundle(github)
        validate_bundle(azure)

    def test_boundary_requires_controller_and_complete_contracts(self) -> None:
        for missing_field in (
            "controller",
            "baseline_source",
            "before_contract",
            "after_contract",
        ):
            with self.subTest(field=missing_field):
                raw = complete_bundle()
                del raw["external_boundary_delta"][0][missing_field]  # type: ignore[index]
                with self.assertRaisesRegex(ContractError, missing_field):
                    validate_bundle(raw)

    def test_boundary_item_requires_path_change_and_complete_references(self) -> None:
        raw = complete_bundle()
        item = raw["external_boundary_delta"][0]["items"][0]  # type: ignore[index]
        item["invariant_ids"] = ["missing-invariant"]
        with self.assertRaisesRegex(ContractError, "dangling invariant id"):
            validate_bundle(raw)

    def test_boundary_item_rejects_dangling_qa_reference(self) -> None:
        raw = complete_bundle()
        item = raw["external_boundary_delta"][0]["items"][0]  # type: ignore[index]
        item["qa_refs"] = ["missing-qa-stage"]
        with self.assertRaisesRegex(ContractError, "dangling QA stage result id"):
            validate_bundle(raw)

    def test_added_boundary_item_is_a_supported_change_kind(self) -> None:
        validate_bundle(complete_bundle())

    def test_claim_requires_classification_and_causal_mapping(self) -> None:
        for missing_field in (
            "criticality",
            "environment_scope",
            "boundary_scope",
            "causal_chain",
            "uncovered_segments",
            "status",
        ):
            with self.subTest(field=missing_field):
                raw = complete_bundle()
                del raw["claims"][0][missing_field]  # type: ignore[index]
                with self.assertRaisesRegex(ContractError, missing_field):
                    validate_bundle(raw)

    def test_causal_step_requires_observed_boolean(self) -> None:
        raw = complete_bundle()
        del raw["claims"][0]["causal_chain"][0]["observed"]  # type: ignore[index]
        with self.assertRaisesRegex(ContractError, "observed"):
            validate_bundle(raw)

    def test_changed_boundary_item_cannot_orphan_invariant_or_claim(self) -> None:
        for field in ("invariant_ids", "claim_ids"):
            with self.subTest(field=field):
                raw = complete_bundle()
                item = raw["external_boundary_delta"][0]["items"][0]  # type: ignore[index]
                item[field] = []
                with self.assertRaisesRegex(ContractError, field):
                    validate_bundle(raw)

    def test_boolean_contract_version_is_rejected(self) -> None:
        raw = complete_bundle()
        raw["contract_version"] = True
        with self.assertRaisesRegex(ContractError, "contract_version"):
            validate_bundle(raw)

    def test_required_policy_summary_must_match_policy_entries(self) -> None:
        raw = complete_bundle()
        raw["provider_records"][0]["policy_checks"][0]["status"] = "failed"  # type: ignore[index]
        with self.assertRaisesRegex(ContractError, "required_policies_passed"):
            validate_bundle(raw)

    def test_provider_approval_must_bind_current_head(self) -> None:
        raw = complete_bundle()
        raw["provider_records"][0]["approvals"][0]["head_sha"] = "old-head"  # type: ignore[index]
        with self.assertRaisesRegex(ContractError, "current provider head"):
            validate_bundle(raw)

    def test_applied_merge_requires_capability_and_merged_pr_state(self) -> None:
        raw = complete_bundle()
        provider = raw["provider_records"][0]  # type: ignore[index]
        provider["capabilities"]["merge_with_expected_head"] = False
        provider["limitations"] = ["Expected-head merge is unavailable."]
        provider["merge_result"].update(
            {
                "status": "applied",
                "expected_head_sha": "head-123",
                "provider_result_ref": "merge-result",
            }
        )
        with self.assertRaisesRegex(ContractError, "merge_with_expected_head"):
            validate_bundle(raw)

    def test_merged_pr_state_requires_applied_merge_result(self) -> None:
        raw = complete_bundle()
        raw["provider_records"][0]["state"] = "merged"  # type: ignore[index]
        with self.assertRaisesRegex(ContractError, "merged PR state"):
            validate_bundle(raw)

    def test_false_approval_capability_rejects_returned_approvals(self) -> None:
        raw = complete_bundle()
        provider = raw["provider_records"][0]  # type: ignore[index]
        provider["capabilities"]["get_approvals"] = False
        provider["limitations"] = ["Approval reads are unavailable."]
        with self.assertRaisesRegex(ContractError, "get_approvals"):
            validate_bundle(raw)

    def test_available_pr_state_capability_cannot_return_unknown_state(self) -> None:
        raw = complete_bundle()
        raw["provider_records"][0]["state"] = "unknown"  # type: ignore[index]
        with self.assertRaisesRegex(ContractError, "get_pr_state.*unknown"):
            validate_bundle(raw)

    def test_required_provider_capability_requires_explicit_gate(self) -> None:
        raw = complete_bundle()
        provider = raw["provider_records"][0]  # type: ignore[index]
        provider["capabilities"]["create_or_update_pr"] = False
        provider["limitations"] = ["PR mutation is unavailable."]
        with self.assertRaisesRegex(ContractError, "provider-capability gate"):
            validate_bundle(raw)

    def test_provider_capability_gate_is_structural_and_release_blocking(self) -> None:
        raw = complete_bundle()
        provider = raw["provider_records"][0]  # type: ignore[index]
        provider["capabilities"]["create_or_update_pr"] = False
        provider["limitations"] = ["PR mutation is unavailable."]
        raw["gates"].append(  # type: ignore[union-attr]
            {
                "id": "gate-provider-create",
                "candidate_ref": candidate(),
                "scope": "ticket",
                "kind": "provider-capability",
                "critical": True,
                "status": "open",
                "owner": "repository administrator",
                "required_evidence": "Provider supports PR mutation.",
                "provider_record_id": "provider-pr",
                "capability": "create_or_update_pr",
            }
        )
        raw["verification"]["gate_ids"].append("gate-provider-create")  # type: ignore[index]
        raw["verification"].update(  # type: ignore[index]
            {
                "release_status": "blocked",
                "final_disposition": "release-blocked",
            }
        )
        validate_bundle(raw)
        self.assertEqual(reduce_claims(raw)["release_status"], "blocked")

    def test_open_pr_operation_requires_normalized_provider_record(self) -> None:
        with self.assertRaises(ContractError) as raised:
            validate_bundle(bundle_without_provider("open-pr"))
        self.assertEqual(raised.exception.path, "verification.requested_operation")
        self.assertIn(
            "open-pr requires at least one normalized provider record",
            str(raised.exception),
        )

    def test_report_operation_allows_empty_provider_records(self) -> None:
        validate_bundle(bundle_without_provider("report"))

    def test_unknown_bundle_and_nested_fields_are_rejected(self) -> None:
        raw = complete_bundle()
        raw["surprise"] = True
        with self.assertRaisesRegex(ContractError, "unknown field"):
            validate_bundle(raw)

        raw = complete_bundle()
        raw["evidence"][0]["surprise"] = True  # type: ignore[index]
        with self.assertRaisesRegex(ContractError, "unknown field"):
            validate_bundle(raw)


class ClaimReductionTests(unittest.TestCase):
    def test_normalized_reduction_fixtures(self) -> None:
        cases = json.loads(
            (FIXTURES / "claim-reduction-cases.json").read_text(encoding="utf-8")
        )
        for case in cases:
            with self.subTest(case=case["name"]):
                raw = bundle_for_reduction_case(case)
                self.assertEqual(reduce_claims(raw), case["expected"])
                validate_bundle(raw)

    def test_complete_fixture_reduces_to_production_ready(self) -> None:
        result = reduce_claims(complete_bundle())
        self.assertEqual(
            result,
            {
                "implementation_status": "complete",
                "max_claim": "production-ready",
                "release_status": "eligible",
                "final_disposition": "production-ready",
            },
        )

    def test_open_critical_gate_blocks_release_not_supported_claim(self) -> None:
        raw = complete_bundle()
        gate = raw["gates"][0]  # type: ignore[index]
        gate["status"] = "open"
        gate.pop("actor")
        gate.pop("resolution_evidence")
        gate.pop("pr_head_sha")
        raw.pop("merge_authorization")
        raw["verification"].update(  # type: ignore[index]
            {
                "release_status": "blocked",
                "final_disposition": "release-blocked",
            }
        )
        result = reduce_claims(raw)
        self.assertEqual(result["implementation_status"], "complete")
        self.assertEqual(result["max_claim"], "production-ready")
        self.assertEqual(result["release_status"], "blocked")
        self.assertEqual(result["final_disposition"], "release-blocked")

    def test_unresolved_high_impact_boundary_prevents_completion(self) -> None:
        raw = complete_bundle()
        boundary_item = raw["external_boundary_delta"][0]["items"][0]  # type: ignore[index]
        boundary_item["authorization"] = "unresolved"
        boundary_item["requirement_ref"] = None
        boundary_item["gate_ids"] = ["gate-merge"]
        raw["verification"].update(  # type: ignore[index]
            {
                "implementation_status": "incomplete",
                "max_claim": "none",
                "release_status": "blocked",
                "final_disposition": "unsupported",
            }
        )
        result = reduce_claims(raw)
        self.assertEqual(result["implementation_status"], "incomplete")
        self.assertEqual(result["max_claim"], "none")
        self.assertEqual(result["final_disposition"], "unsupported")

    def test_simulated_evidence_cannot_support_production_ready(self) -> None:
        raw = complete_bundle()
        evidence = raw["evidence"][0]  # type: ignore[index]
        evidence["class"] = "simulated"
        evidence["environment_scope"] = "test"
        evidence["boundary_scope"] = "simulated-external"
        raw["verification"].update(  # type: ignore[index]
            {
                "max_claim": "behavior-verified",
                "release_status": "blocked",
                "final_disposition": "release-blocked",
            }
        )
        self.assertEqual(reduce_claims(raw)["max_claim"], "behavior-verified")

    def test_critical_contradictory_evidence_blocks_release(self) -> None:
        raw = complete_bundle()
        contradiction = copy.deepcopy(raw["evidence"][0])  # type: ignore[index]
        contradiction.update(
            {
                "id": "e-contradiction",
                "result": "fail",
                "supports_claim": "behavior-verified",
                "artifact": "artifacts/contradiction.json",
            }
        )
        raw["evidence"].append(contradiction)  # type: ignore[index]
        raw["verification"]["evidence_ids"].append("e-contradiction")  # type: ignore[index]
        raw["claims"][0]["evidence_ids"].append("e-contradiction")  # type: ignore[index]
        raw["verification"].update(  # type: ignore[index]
            {
                "max_claim": "deployable-for-test",
                "release_status": "blocked",
                "final_disposition": "release-blocked",
            }
        )
        result = reduce_claims(raw)
        self.assertEqual(result["max_claim"], "deployable-for-test")
        self.assertEqual(result["release_status"], "blocked")

    def test_declared_disposition_must_equal_reducer(self) -> None:
        raw = complete_bundle()
        raw["verification"]["max_claim"] = "behavior-verified"  # type: ignore[index]
        with self.assertRaisesRegex(ContractError, "does not match deterministic reduction"):
            validate_bundle(raw)

    def test_claim_uses_only_its_referenced_evidence(self) -> None:
        raw = complete_bundle()
        unit = copy.deepcopy(raw["evidence"][0])  # type: ignore[index]
        unit.update(
            {
                "id": "e-unit",
                "class": "unit",
                "environment_scope": "local",
                "boundary_scope": "internal",
                "supports_claim": "deployable-for-test",
                "artifact": "artifacts/unit.json",
            }
        )
        raw["evidence"].append(unit)  # type: ignore[index]
        raw["claims"][0]["evidence_ids"] = ["e-unit"]  # type: ignore[index]
        result = reduce_claims(raw)
        self.assertEqual(result["max_claim"], "deployable-for-test")

    def test_evidence_less_claim_cannot_be_production_ready(self) -> None:
        raw = complete_bundle()
        raw["claims"][0]["evidence_ids"] = []  # type: ignore[index]
        result = reduce_claims(raw)
        self.assertEqual(result["max_claim"], "implementation-complete")

    def test_zero_claims_cannot_be_production_ready(self) -> None:
        raw = complete_bundle()
        raw["claims"] = []
        self.assertEqual(
            reduce_claims(raw)["max_claim"],
            "implementation-complete",
        )

    def test_failed_qa_execution_caps_claim_and_blocks_release(self) -> None:
        raw = complete_bundle()
        qa = next(
            stage
            for stage in raw["stage_results"]  # type: ignore[union-attr]
            if stage["stage"] == "qa-execute"
        )
        qa["result"] = "fail"
        result = reduce_claims(raw)
        self.assertEqual(result["max_claim"], "deployable-for-test")
        self.assertEqual(result["release_status"], "blocked")

    def test_skipped_verification_cannot_be_production_ready(self) -> None:
        raw = complete_bundle()
        verify = next(
            stage
            for stage in raw["stage_results"]  # type: ignore[union-attr]
            if stage["stage"] == "verify"
        )
        verify["result"] = "skipped"
        result = reduce_claims(raw)
        self.assertLess(
            {
                "none": 0,
                "implementation-complete": 1,
                "deployable-for-test": 2,
                "behavior-verified": 3,
                "production-ready": 4,
            }[result["max_claim"]],
            4,
        )
        self.assertEqual(result["release_status"], "blocked")

    def test_claim_target_scope_caps_higher_evidence(self) -> None:
        raw = complete_bundle()
        claim = raw["claims"][0]  # type: ignore[index]
        claim["environment_scope"] = "staging"
        claim["boundary_scope"] = "simulated-external"
        result = reduce_claims(raw)
        self.assertEqual(result["max_claim"], "behavior-verified")

    def test_lower_referenced_evidence_cannot_satisfy_live_production_target(self) -> None:
        raw = complete_bundle()
        evidence = raw["evidence"][0]  # type: ignore[index]
        evidence["environment_scope"] = "staging"
        evidence["boundary_scope"] = "simulated-external"
        result = reduce_claims(raw)
        self.assertEqual(result["max_claim"], "behavior-verified")
        self.assertEqual(result["release_status"], "blocked")

    def test_failed_qa_plan_blocks_release(self) -> None:
        raw = complete_bundle()
        qa_plan = next(
            stage
            for stage in raw["stage_results"]  # type: ignore[union-attr]
            if stage["stage"] == "qa-plan"
        )
        qa_plan["result"] = "fail"
        result = reduce_claims(raw)
        self.assertEqual(result["release_status"], "blocked")
        self.assertEqual(result["final_disposition"], "release-blocked")

    def test_blocked_finalize_stage_blocks_release(self) -> None:
        raw = complete_bundle()
        finalize = copy.deepcopy(raw["stage_results"][0])  # type: ignore[index]
        finalize.update(
            {
                "id": "stage-finalize",
                "stage": "finalize",
                "result": "blocked",
                "gate_ids": ["gate-finalize"],
            }
        )
        raw["stage_results"].append(finalize)  # type: ignore[union-attr]
        raw["gates"].append(  # type: ignore[union-attr]
            {
                "id": "gate-finalize",
                "candidate_ref": candidate(),
                "scope": "ticket",
                "kind": "human",
                "critical": False,
                "status": "open",
                "owner": "maintainer",
                "required_evidence": "Finalize the ticket.",
            }
        )
        result = reduce_claims(raw)
        self.assertEqual(result["release_status"], "blocked")
        self.assertEqual(result["final_disposition"], "release-blocked")

    def test_skipped_required_qa_plan_caps_claim_from_policy(self) -> None:
        raw = complete_bundle()
        qa_plan = next(
            stage
            for stage in raw["stage_results"]  # type: ignore[union-attr]
            if stage["stage"] == "qa-plan"
        )
        qa_plan["result"] = "skipped"
        result = reduce_claims(raw)
        self.assertEqual(result["max_claim"], "implementation-complete")


class PrBodyValidationTests(unittest.TestCase):
    def valid_body(self) -> str:
        return """## Summary
Production readiness for the normalized provider record.

## Behavior
The versioned validator checks the normalized bundle.

## Verification
e-live: live pass in production-eu.

## Risks and gates
gate-merge passed with approval-record-1.

## Reviewer checks
Review boundary-provider and inv-no-overclaim.

```mermaid
flowchart LR
    Bundle --> Validator --> Disposition
```
"""

    def test_valid_pr_body_is_accepted(self) -> None:
        validate_pr_body(
            self.valid_body(),
            complete_bundle(),
            pr_head_sha="head-123",
        )

    def test_required_headings_are_checked(self) -> None:
        with self.assertRaisesRegex(ContractError, "missing required heading"):
            validate_pr_body("```mermaid\\nflowchart LR\\n```", complete_bundle())

    def test_exactly_one_mermaid_is_required(self) -> None:
        body = self.valid_body() + "\n```mermaid\nflowchart LR\n```\n"
        with self.assertRaisesRegex(ContractError, "exactly one Mermaid"):
            validate_pr_body(body, complete_bundle())

    def test_unclosed_mermaid_is_rejected(self) -> None:
        body = self.valid_body().replace(
            "```mermaid\nflowchart LR\n    Bundle --> Validator --> Disposition\n```",
            "```mermaid\nflowchart LR\n    Bundle --> Validator --> Disposition",
        )
        with self.assertRaisesRegex(ContractError, "exactly one Mermaid"):
            validate_pr_body(body, complete_bundle())

    def test_headings_inside_generic_fence_do_not_satisfy_structure(self) -> None:
        fenced_headings = """```text
## Summary
## Behavior
## Verification
## Risks and gates
## Reviewer checks
```

```mermaid
flowchart LR
    Bundle --> Validator
```
"""
        with self.assertRaisesRegex(ContractError, "missing required heading"):
            validate_pr_body(
                fenced_headings,
                complete_bundle(),
                pr_head_sha="head-123",
            )

    def test_headings_inside_mermaid_do_not_satisfy_structure(self) -> None:
        mermaid_headings = """```mermaid
flowchart LR
## Summary
## Behavior
## Verification
## Risks and gates
## Reviewer checks
```
"""
        with self.assertRaisesRegex(ContractError, "missing required heading"):
            validate_pr_body(
                mermaid_headings,
                complete_bundle(),
                pr_head_sha="head-123",
            )

    def test_mixed_fences_preserve_real_outside_headings(self) -> None:
        body = self.valid_body() + """
~~~text
## Summary
This fenced heading is ignored without hiding the real one.
~~~
"""
        validate_pr_body(body, complete_bundle(), pr_head_sha="head-123")

    def test_open_gate_must_be_visible(self) -> None:
        raw = complete_bundle()
        gate = raw["gates"][0]  # type: ignore[index]
        gate["status"] = "open"
        gate.pop("actor")
        gate.pop("resolution_evidence")
        gate.pop("pr_head_sha")
        raw.pop("merge_authorization")
        raw["verification"].update(  # type: ignore[index]
            {
                "release_status": "blocked",
                "final_disposition": "release-blocked",
            }
        )
        body = self.valid_body().replace("gate-merge", "unmentioned-gate")
        with self.assertRaisesRegex(ContractError, "open gate gate-merge"):
            validate_pr_body(body, raw)

    def test_open_gate_status_must_not_be_described_as_passed(self) -> None:
        raw = bundle_for_reduction_case(
            {
                "mode": "gated",
                "expected": {
                    "implementation_status": "complete",
                    "max_claim": "production-ready",
                    "release_status": "blocked",
                    "final_disposition": "release-blocked",
                },
            }
        )
        with self.assertRaisesRegex(ContractError, "must declare status open"):
            validate_pr_body(self.valid_body(), raw)

    def test_simulated_live_and_skipped_evidence_must_be_declared(self) -> None:
        raw = complete_bundle()
        raw["evidence"][0]["class"] = "simulated"  # type: ignore[index]
        raw["verification"].update(  # type: ignore[index]
            {
                "max_claim": "behavior-verified",
                "release_status": "blocked",
                "final_disposition": "release-blocked",
            }
        )
        body = self.valid_body().replace("live pass", "pass")
        with self.assertRaisesRegex(ContractError, "e-live must declare simulated"):
            validate_pr_body(body, raw)

    def test_skipped_evidence_must_be_declared_on_its_evidence_line(self) -> None:
        raw = complete_bundle()
        evidence = raw["evidence"][0]  # type: ignore[index]
        evidence.update(
            {
                "class": "unit",
                "result": "skipped",
                "critical": False,
                "supports_claim": "implementation-complete",
            }
        )
        raw["verification"].update(  # type: ignore[index]
            {
                "max_claim": "none",
                "final_disposition": "unsupported",
            }
        )
        raw["claims"][0]["requested_claim"] = "none"  # type: ignore[index]
        raw["claims"][0]["criticality"] = "low"  # type: ignore[index]
        body = self.valid_body().replace("e-live: live pass", "e-live: unit pass")
        body += "\nAnother check was skipped.\n"
        with self.assertRaisesRegex(ContractError, "e-live must declare skipped"):
            validate_pr_body(body, raw)

    def test_forbidden_wording_is_rejected(self) -> None:
        with self.assertRaisesRegex(ContractError, "forbidden wording"):
            validate_pr_body(
                self.valid_body() + "\nWorks everywhere.\n",
                complete_bundle(),
            )

    def test_pr_body_head_must_match_authorized_head(self) -> None:
        with self.assertRaisesRegex(ContractError, "PR head SHA"):
            validate_pr_body(
                self.valid_body(),
                complete_bundle(),
                pr_head_sha="head-new",
            )

    def test_provider_record_requires_observed_pr_head(self) -> None:
        with self.assertRaisesRegex(ContractError, "observed PR head SHA is required"):
            validate_pr_body(self.valid_body(), complete_bundle())

    def test_observed_pr_head_must_match_provider_without_authorization(self) -> None:
        raw = complete_bundle()
        raw.pop("merge_authorization")
        with self.assertRaisesRegex(ContractError, "normalized provider head"):
            validate_pr_body(
                self.valid_body(),
                raw,
                pr_head_sha="head-other",
            )

    def test_merge_operation_requires_sha_bound_human_authorization(self) -> None:
        raw = complete_bundle()
        raw.pop("merge_authorization")
        raw["verification"]["requested_operation"] = "merge-pr"  # type: ignore[index]
        raw["verification"].update(  # type: ignore[index]
            {
                "release_status": "blocked",
                "final_disposition": "release-blocked",
            }
        )
        with self.assertRaisesRegex(ContractError, "merge authorization"):
            validate_pr_body(
                self.valid_body(),
                raw,
                pr_head_sha="head-123",
            )

    def test_failed_gate_must_be_rendered_as_failed(self) -> None:
        raw = complete_bundle()
        gate = raw["gates"][0]  # type: ignore[index]
        gate["status"] = "failed"
        gate.pop("pr_head_sha")
        raw.pop("merge_authorization")
        raw["verification"].update(  # type: ignore[index]
            {
                "release_status": "blocked",
                "final_disposition": "release-blocked",
            }
        )
        body = self.valid_body().replace(
            "gate-merge passed",
            "gate-merge failed",
        )
        validate_pr_body(body, raw, pr_head_sha="head-123")

    def test_noncritical_open_gate_must_be_visible(self) -> None:
        raw = complete_bundle()
        raw["gates"].append(  # type: ignore[union-attr]
            {
                "id": "gate-noncritical",
                "candidate_ref": candidate(),
                "scope": "ticket",
                "kind": "human",
                "critical": False,
                "status": "open",
                "owner": "reviewer",
                "required_evidence": "Optional observation.",
            }
        )
        with self.assertRaisesRegex(ContractError, "gate-noncritical"):
            validate_pr_body(
                self.valid_body(),
                raw,
                pr_head_sha="head-123",
            )

    def test_gate_status_line_rejects_contradictory_tokens(self) -> None:
        raw = complete_bundle()
        gate = raw["gates"][0]  # type: ignore[index]
        gate["status"] = "failed"
        gate.pop("pr_head_sha")
        raw.pop("merge_authorization")
        raw["verification"].update(  # type: ignore[index]
            {
                "release_status": "blocked",
                "final_disposition": "release-blocked",
            }
        )
        body = self.valid_body().replace(
            "gate-merge passed",
            "gate-merge failed then passed",
        )
        with self.assertRaisesRegex(ContractError, "unambiguous status failed"):
            validate_pr_body(body, raw, pr_head_sha="head-123")


class CliTests(unittest.TestCase):
    def test_validate_command_emits_normalized_json(self) -> None:
        script = SCRIPTS / "verification_contract.py"
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_path = Path(temp_dir) / "bundle.json"
            bundle_path.write_text(json.dumps(complete_bundle()), encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "validate",
                    str(bundle_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["verification"]["final_disposition"], "production-ready")

    def test_invalid_cli_input_returns_machine_readable_diagnostic(self) -> None:
        script = SCRIPTS / "verification_contract.py"
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_path = Path(temp_dir) / "bundle.json"
            bundle_path.write_text("{}", encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "validate",
                    str(bundle_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(completed.returncode, 2)
        payload = json.loads(completed.stderr)
        self.assertEqual(payload["error"], "contract-invalid")
        self.assertTrue(payload["diagnostics"])

    def test_validate_ticket_parses_canonical_front_matter(self) -> None:
        script = SCRIPTS / "verification_contract.py"
        completed = subprocess.run(
            [
                sys.executable,
                str(script),
                "validate-ticket",
                str(FIXTURES / "valid-ticket.md"),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(
            json.loads(completed.stdout),
            {
                "blocked_by": ["01", "02"],
                "execution_mode": "AFK",
                "ticket_id": "03",
                "ticket_schema": 1,
            },
        )

    def test_validate_ticket_rejects_legacy_ticket(self) -> None:
        script = SCRIPTS / "verification_contract.py"
        completed = subprocess.run(
            [
                sys.executable,
                str(script),
                "validate-ticket",
                str(FIXTURES / "legacy-ticket.md"),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 2)
        payload = json.loads(completed.stderr)
        self.assertEqual(payload["error"], "contract-invalid")
        self.assertIn("front matter", payload["diagnostics"][0]["message"])

    def test_validate_ticket_rejects_unknown_front_matter_field(self) -> None:
        script = SCRIPTS / "verification_contract.py"
        completed = subprocess.run(
            [
                sys.executable,
                str(script),
                "validate-ticket",
                str(FIXTURES / "invalid-ticket-unknown-field.md"),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("unknown", completed.stderr)

    def test_open_pr_without_provider_has_machine_readable_diagnostic(self) -> None:
        script = SCRIPTS / "verification_contract.py"
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_path = Path(temp_dir) / "bundle.json"
            bundle_path.write_text(
                json.dumps(bundle_without_provider("open-pr")),
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "validate",
                    str(bundle_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(completed.returncode, 2)
        payload = json.loads(completed.stderr)
        self.assertEqual(payload["error"], "contract-invalid")
        self.assertEqual(
            payload["diagnostics"][0]["path"],
            "verification.requested_operation",
        )
        self.assertIn(
            "open-pr requires at least one normalized provider record",
            payload["diagnostics"][0]["message"],
        )


if __name__ == "__main__":
    unittest.main()
