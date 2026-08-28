#!/usr/bin/env python3
"""Run the accepted ticket-autopilot forward-test matrix with retained evidence."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCHEMA = 1
ROOT = Path(__file__).resolve().parents[2]
AUTOPILOT_TESTS = ROOT / "ticket-autopilot" / "tests"
VERIFICATION_TESTS = ROOT / "verification-audit" / "tests"
RETAINED_EVIDENCE = ("artifact", "command", "final_report", "ledger")


@dataclass(frozen=True, order=True)
class TestRef:
    suite: str
    pattern: str
    method: str

    @property
    def test_root(self) -> Path:
        if self.suite == "autopilot":
            return AUTOPILOT_TESTS
        if self.suite == "verification":
            return VERIFICATION_TESTS
        raise ValueError(f"unknown suite: {self.suite}")

    @property
    def key(self) -> str:
        return f"{self.suite}:{self.pattern}:{self.method}"

    def command(self) -> list[str]:
        return [
            sys.executable,
            "-B",
            "-m",
            "unittest",
            "discover",
            "-s",
            str(self.test_root),
            "-p",
            self.pattern,
            "-k",
            self.method,
        ]


def ref(pattern: str, method: str, *, suite: str = "autopilot") -> TestRef:
    return TestRef(suite=suite, pattern=pattern, method=method)


def scenario(
    prompt: str,
    *tests: TestRef,
    limitations: str,
) -> dict[str, Any]:
    return {
        "prompt": prompt,
        "tests": tests,
        "retained_evidence": RETAINED_EVIDENCE,
        "limitations": limitations,
    }


SCENARIOS: dict[str, dict[str, Any]] = {
    "agenttool-optional": scenario(
        "Run an AFK ticket on a host with no AgentTool or subagent primitive while preserving serial review, QA, audit, and truthful isolation records.",
        ref(
            "test_skill_graph.py",
            "test_autopilot_defaults_to_portable_inline_composition",
        ),
        ref(
            "test_skill_graph.py",
            "test_delegation_authority_and_isolation_claims_fail_closed",
        ),
        ref(
            "test_skill_graph.py",
            "test_agenttool_optional_workflows_have_inline_fallback_or_gate",
        ),
        ref(
            "test_leaf_protocol.py",
            "test_missing_execution_normalizes_to_unknown",
        ),
        ref(
            "test_leaf_protocol.py",
            "test_valid_execution_matrix_normalizes",
        ),
        ref(
            "test_leaf_protocol.py",
            "test_invalid_execution_matrix_fails_closed",
        ),
        limitations=(
            "Static skill contracts and local schema normalization; no live host "
            "delegation is exercised."
        ),
    ),
    "audit-evidence-gap": scenario(
        "Resume a ticket whose verification evidence is skipped or incomplete.",
        ref(
            "test_verification_contract.py",
            "test_skipped_verification_cannot_be_production_ready",
            suite="verification",
        ),
        limitations="Uses a normalized local bundle; no live verifier is invoked.",
    ),
    "azure-devops-adapter": scenario(
        "Drive an Azure DevOps pull request through capability and exact-SHA gates.",
        ref(
            "test_cli.py",
            "test_azure_external_merge_requires_exact_sha_and_live_observation",
        ),
        ref(
            "test_verification_contract.py",
            "test_github_and_azure_devops_use_same_normalized_shape",
            suite="verification",
        ),
        limitations="Azure command responses are simulated; credentials are not used.",
    ),
    "autonomous-merge-grant": scenario(
        "Grant one run autonomous merge authority and exercise eligibility, gates, and replay.",
        ref(
            "test_cli.py",
            "test_autonomous_grant_merges_an_eligible_exact_head_without_a_prompt",
        ),
        ref(
            "test_cli.py",
            "test_autonomous_merge_gates_pending_and_failed_checks_then_retries",
        ),
        ref(
            "test_cli.py",
            "test_autonomous_merge_gates_a_malformed_checks_receipt",
        ),
        ref(
            "test_cli.py",
            "test_autonomous_head_race_gates_without_adopting_unvalidated_lineage",
        ),
        ref(
            "test_cli.py",
            "test_autonomous_retry_rechecks_policies_before_a_second_mutation",
        ),
        ref(
            "test_cli.py",
            "test_autonomous_merge_recovers_a_lost_mutation_response_once",
        ),
        ref(
            "test_kernel.py",
            "test_live_github_queue_recovers_a_zero_exit_malformed_response_once",
        ),
        ref(
            "test_cli.py",
            "test_autonomous_merge_accepts_github_has_hooks_success_state",
        ),
        ref(
            "test_cli.py",
            "test_autonomous_merge_queue_waits_and_replays_without_reenqueue",
        ),
        ref(
            "test_cli.py",
            "test_autonomous_queue_replay_never_reenqueues_a_missing_entry",
        ),
        ref(
            "test_cli.py",
            "test_autonomous_queue_crash_never_falls_back_to_direct_merge",
        ),
        ref(
            "test_cli.py",
            "test_autonomous_queue_crash_before_mutation_gates_ambiguous_dispatch",
        ),
        ref(
            "test_cli.py",
            "test_autonomous_queue_crash_with_missing_entry_never_reenqueues",
        ),
        ref(
            "test_cli.py",
            "test_autonomous_first_mutation_gates_if_merge_mode_changes_after_eligibility",
        ),
        ref(
            "test_cli.py",
            "test_autonomous_first_mutation_gates_if_queue_requirement_disappears",
        ),
        ref(
            "test_cli.py",
            "test_manual_merge_retries_after_a_pre_mutation_failure",
        ),
        ref(
            "test_cli.py",
            "test_manual_queue_crash_with_missing_entry_never_reenqueues",
        ),
        ref(
            "test_cli.py",
            "test_manual_queue_crash_never_falls_back_to_direct_merge",
        ),
        ref(
            "test_kernel.py",
            "test_replay_rejects_forged_pr_body_lineage_rebinds",
        ),
        ref(
            "test_kernel.py",
            "test_fresh_bundle_rebind_closes_over_current_verified_handoff",
        ),
        ref(
            "test_cli.py",
            "test_autonomous_merge_gates_a_provider_without_atomic_expected_head",
        ),
        ref(
            "test_cli.py",
            "test_autonomous_stack_reconciles_new_head_and_merges_child_without_revalidation",
        ),
        ref(
            "test_cli.py",
            "test_semantic_stack_reconciliation_rebinds_the_fresh_verified_bundle",
        ),
        ref(
            "test_semantic_candidate_v2.py",
            "test_three_ticket_stack_preserves_downstream_review_counts",
        ),
        limitations=(
            "Provider behavior is exercised through a stateful fake against a real local "
            "Git remote. Prior-candidate live GitHub findings shaped these cases, but this "
            "new candidate has not been independently re-run against a disposable provider."
        ),
    ),
    "child-rebase-retarget": scenario(
        "Integrate a three-ticket stack, preserve exact semantic evidence across lineage-only rebases, and invalidate planted semantic drift.",
        ref(
            "test_cli.py",
            "test_delivery_is_crash_resumable_idempotent_and_never_auto_merges",
        ),
        ref(
            "test_semantic_candidate_v2.py",
            "test_three_ticket_stack_preserves_downstream_review_counts",
        ),
        ref(
            "test_semantic_candidate_v2.py",
            "test_each_semantic_field_drift_requires_complete_revalidation",
        ),
        limitations=(
            "Provider readback is simulated against a real local bare Git remote; "
            "the three-ticket invocation-count and planted-drift matrix is deterministic local evidence."
        ),
    ),
    "cycle": scenario(
        "Plan a ticket folder containing a dependency cycle.",
        ref(
            "test_kernel.py",
            "test_rejects_unknown_version_duplicate_missing_dependency_and_cycle",
        ),
        limitations="Exercises fail-closed parsing before a run is created.",
    ),
    "dependency-chain": scenario(
        "Run a two-ticket dependency chain with one ticket per delivery branch.",
        ref(
            "test_kernel.py",
            "test_single_parent_stacks_but_multi_parent_join_waits_for_integration",
        ),
        limitations="DAG readiness is local; provider mutation is covered separately.",
    ),
    "dirty-caller-worktree": scenario(
        "Run, wait, resume, and clean up without changing the caller's dirty files.",
        ref("test_cli.py", "test_run_uses_isolated_worktree_and_common_dir_ledger"),
        ref("test_cli.py", "test_cleanup_never_discards_dirty_isolated_worktree"),
        limitations="Uses disposable local repositories and no remote provider.",
    ),
    "explicit-hitl": scenario(
        "Start a HITL ticket only after a ticket-scoped human approval.",
        ref("test_cli.py", "test_approve_resolves_hitl_start_gate"),
        limitations="Approval is an explicit test event, not a fabricated live decision.",
    ),
    "full-new-schema-pipeline": scenario(
        "Route canonical tickets through producer, parser, runner, and verifier ownership.",
        ref(
            "test_skill_graph.py",
            "test_producers_and_consumers_reference_canonical_contracts",
        ),
        ref(
            "test_skill_graph.py",
            "test_router_parses_canonical_single_ticket_before_execute_ticket",
        ),
        limitations="Validates the repository contract graph; agent prose is not executed.",
    ),
    "git-finalization-failure": scenario(
        "Fail a ticket during Git finalization and preserve its classified terminal state.",
        ref(
            "test_kernel.py",
            "test_implementation_and_finalization_failures_are_distinct",
        ),
        limitations="The failure is injected at the finalization stage boundary.",
    ),
    "github-adapter": scenario(
        "Observe GitHub pull-request state, checks, approvals, and current head.",
        ref("test_kernel.py", "test_live_github_executor_mints_receipt_from_readback"),
        ref(
            "test_kernel.py",
            "test_provider_operations_are_normalized_and_capability_checked",
        ),
        limitations="The command runner is simulated; normalized live receipts are exercised.",
    ),
    "independent-ticket-set": scenario(
        "Continue an unrelated AFK ticket while another ticket is gated.",
        ref(
            "test_kernel.py",
            "test_ticket_gate_does_not_block_unrelated_afk_work",
        ),
        limitations="Exercises the deterministic scheduler in memory.",
    ),
    "interruption-resume": scenario(
        "Resume delivery after interruption without repeating completed side effects.",
        ref(
            "test_cli.py",
            "test_delivery_is_crash_resumable_idempotent_and_never_auto_merges",
        ),
        limitations="Uses fresh CLI subprocesses and a simulated provider.",
    ),
    "invalid-pr-body": scenario(
        "Validate a pull-request body with missing sections or malformed diagrams.",
        ref(
            "test_verification_contract.py",
            "test_required_headings_are_checked",
            suite="verification",
        ),
        ref(
            "test_verification_contract.py",
            "test_exactly_one_mermaid_is_required",
            suite="verification",
        ),
        limitations="Validates literal Markdown locally; no pull request is mutated.",
    ),
    "merge-authorization-invalidation": scenario(
        "Change a pull-request head after approval and attempt integration.",
        ref(
            "test_kernel.py",
            "test_pr_head_change_invalidates_merge_authorization",
        ),
        limitations="Uses deterministic kernel events and no provider mutation.",
    ),
    "merge-gated-multi-blocker-join": scenario(
        "Keep a multi-parent join blocked until every parent is integrated.",
        ref(
            "test_kernel.py",
            "test_single_parent_stacks_but_multi_parent_join_waits_for_integration",
        ),
        limitations="Exercises the accepted join policy in the scheduler.",
    ),
    "missing-dependency": scenario(
        "Plan a ticket folder whose blocker does not exist.",
        ref(
            "test_kernel.py",
            "test_rejects_unknown_version_duplicate_missing_dependency_and_cycle",
        ),
        limitations="Exercises fail-closed parsing before a run is created.",
    ),
    "parent-merge": scenario(
        "Observe a parent merge and unlock only ancestry-valid dependent work.",
        ref(
            "test_cli.py",
            "test_delivery_is_crash_resumable_idempotent_and_never_auto_merges",
        ),
        ref(
            "test_cli.py",
            "test_runner_merge_recovers_lost_response_without_second_merge",
        ),
        ref(
            "test_kernel.py",
            "test_pending_runner_merge_has_priority_over_unrelated_ticket",
        ),
        limitations="Uses a local bare Git remote and simulated provider state.",
    ),
    "qa-implementation-failure": scenario(
        "Fail QA execution and resume from implementation with stale evidence removed.",
        ref(
            "test_forward_gaps.py",
            "test_qa_implementation_failure_restarts_the_quality_pipeline",
        ),
        ref(
            "test_verification_contract.py",
            "test_failed_qa_execution_caps_claim_and_blocks_release",
            suite="verification",
        ),
        limitations="QA failure is injected at the normalized stage boundary.",
    ),
    "remote-divergence": scenario(
        "Reconcile a child after its remote branch changes out of band.",
        ref(
            "test_forward_gaps.py",
            "test_remote_divergence_guard_accepts_only_explicit_heads",
        ),
        limitations="Exercises the shared fail-closed guard without a live remote race.",
    ),
    "review-fix-loop": scenario(
        "Fix a reviewed candidate and rerun invalidated downstream quality stages.",
        ref(
            "test_cli.py",
            "test_resume_drives_stages_and_invalidates_stale_downstream_evidence",
        ),
        limitations="Candidate changes occur in a real isolated Git worktree.",
    ),
    "safe-force-with-lease": scenario(
        "Publish a reconciled child only with a SHA-bound force-with-lease.",
        ref("test_kernel.py", "test_reconcile_commands_use_force_with_lease"),
        limitations="Validates command construction; no live force push is performed.",
    ),
    "stacked-single-parent-pr": scenario(
        "Open a child pull request against its one unmerged parent branch.",
        ref(
            "test_kernel.py",
            "test_delivery_plan_stacks_single_parent_and_gates_multi_parent_join",
        ),
        limitations="Provider delivery planning is deterministic and local.",
    ),
    "unavailable-credentials": scenario(
        "Pause a run when provider credentials are unavailable and retain the gate.",
        ref("test_kernel.py", "test_run_scoped_gate_stops_all_ready_work"),
        limitations="Credentials remain unavailable; the test supplies only an explicit gate event.",
    ),
    "waiting-vs-completed": scenario(
        "Report waiting with an open pull request and completed only after integration.",
        ref(
            "test_forward_gaps.py",
            "test_open_pr_waits_and_only_integration_completes_the_run",
        ),
        limitations="Uses local kernel events; provider state is covered by adapter scenarios.",
    ),
    "wayfinder-clear-destination": scenario(
        "Map the open issues in this repository; the destination and repository scope are already explicit.",
        ref(
            "test_skill_graph.py",
            "test_wayfinder_clear_destination_skips_ceremonial_grilling",
        ),
        limitations="static skill contract; no live model execution",
    ),
    "wayfinder-ambiguous-destination": scenario(
        "Chart a payment modernization effort where it is unclear whether preserving the public API or accepting a breaking redesign defines the destination.",
        ref(
            "test_skill_graph.py",
            "test_wayfinder_material_ambiguity_invokes_grilling_and_waits_before_artifacts",
        ),
        limitations="static skill contract; no live model execution",
    ),
    "wayfinder-maintenance": scenario(
        "Refresh an existing Wayfinder map after a research ticket completed without changing its persisted Destination or scope.",
        ref(
            "test_skill_graph.py",
            "test_wayfinder_maintenance_reuses_destination_until_scope_changes",
        ),
        limitations="static skill contract; no live model execution",
    ),
    "wayfinder-hitl-decision": scenario(
        "Keep a mapped retention-policy decision on the frontier as a human interview ticket without running the interview during charting.",
        ref(
            "test_skill_graph.py",
            "test_wayfinder_unresolved_decision_emits_hitl_grilling_ticket",
        ),
        limitations="static skill contract; no live model execution",
    ),
}


def _run_command(test_ref: TestRef) -> dict[str, Any]:
    command = test_ref.command()
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "test_ref": test_ref.key,
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "result": "pass" if completed.returncode == 0 else "fail",
        "evidence_class": "integration" if test_ref.pattern == "test_cli.py" else "unit",
        "environment": "isolated local repository",
        "injection_point": f"unittest:{test_ref.method}",
        "observed_segment": test_ref.method,
        "limitations": "No live provider behavior is inferred from this command.",
    }


def _source_head() -> str | None:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return completed.stdout.strip() if completed.returncode == 0 else None


def _serializable_scenario(value: dict[str, Any]) -> dict[str, Any]:
    return {
        "prompt": value["prompt"],
        "tests": [test_ref.key for test_ref in value["tests"]],
        "retained_evidence": list(value["retained_evidence"]),
        "limitations": value["limitations"],
    }


def list_payload() -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "scenario_ids": sorted(SCENARIOS),
        "scenarios": {
            scenario_id: _serializable_scenario(SCENARIOS[scenario_id])
            for scenario_id in sorted(SCENARIOS)
        },
    }


def run_payload(scenario_ids: list[str], artifact: str) -> dict[str, Any]:
    selected = {
        scenario_id: SCENARIOS[scenario_id]
        for scenario_id in sorted(scenario_ids)
    }
    test_refs = sorted(
        {
            test_ref
            for scenario_value in selected.values()
            for test_ref in scenario_value["tests"]
        }
    )
    command_results = {
        test_ref.key: _run_command(test_ref)
        for test_ref in test_refs
    }
    scenarios: dict[str, Any] = {}
    for scenario_id, scenario_value in selected.items():
        keys = [test_ref.key for test_ref in scenario_value["tests"]]
        result = (
            "pass"
            if all(command_results[key]["result"] == "pass" for key in keys)
            else "fail"
        )
        scenarios[scenario_id] = {
            **_serializable_scenario(scenario_value),
            "result": result,
            "commands": [command_results[key]["command"] for key in keys],
            "ledger_assertions": keys,
            "artifact": artifact,
            "final_report": {
                "result": result,
                "limitations": scenario_value["limitations"],
            },
        }
    return {
        "schema": SCHEMA,
        "source_head": _source_head(),
        "result": (
            "pass"
            if all(value["result"] == "pass" for value in scenarios.values())
            else "fail"
        ),
        "scenarios": scenarios,
        "command_results": command_results,
    }


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
    )
    try:
        with os.fdopen(descriptor, "w") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="list the scenario matrix")
    parser.add_argument(
        "--scenario",
        action="append",
        choices=sorted(SCENARIOS),
        help="run one scenario; repeat to select more than one",
    )
    parser.add_argument("--output", type=Path, help="retain the normalized JSON report")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.list:
        payload = list_payload()
    else:
        selected = args.scenario or sorted(SCENARIOS)
        artifact = str(args.output) if args.output else "stdout://forward-test"
        payload = run_payload(selected, artifact)
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output:
        _atomic_write(args.output, rendered)
    sys.stdout.write(rendered)
    return 0 if args.list or payload["result"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
