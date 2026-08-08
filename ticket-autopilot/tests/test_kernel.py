from __future__ import annotations

import ast
import copy
import hashlib
import inspect
import json
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
sys.path.insert(0, str(SCRIPTS))

from autopilot.ticket_contract import (
    ContractError,
    migrate_ticket_text,
    parse_ticket_folder,
)
from autopilot.finalizer import finalize_done
from autopilot.git_ops import assert_candidate, candidate_ref
from autopilot.kernel import CandidateRef, Kernel, TransitionError
from autopilot.leaf_protocol import LEAF_PHASE_CONTRACTS
from autopilot.git_ops import CommandResult
from autopilot.ledger import KNOWN_LEDGER_EVENTS
from autopilot.providers import (
    CREATE_OR_UPDATE_PR,
    GET_APPROVALS,
    GET_CHECKS_AND_POLICIES,
    GET_PR_STATE,
    MERGE_WITH_EXPECTED_HEAD,
    ProviderExecutor,
    RETARGET_PR,
)
from autopilot.ticket_lifecycle import transition_ticket_source
from autopilot.ledger import AtomicLedger, LedgerError
from autopilot.providers import (
    AzureDevOpsProvider,
    build_delivery_plan,
    GitHubProvider,
    MergeAuthorization,
    ProviderError,
    detect_provider,
)

PIPELINE = (
    "implement",
    "simplify",
    "review",
    "qa-plan",
    "qa-execute",
    "verify",
    "finalize",
)
STAGES_BEFORE = {
    stage: PIPELINE[:index] for index, stage in enumerate(PIPELINE)
}


def ticket_text(ticket_id: str, blocked_by: tuple[str, ...] = (), mode: str = "AFK") -> str:
    blockers = "\n".join(f'  - "{item}"' for item in blocked_by)
    blocker_field = (
        f"blocked_by:\n{blockers}\n" if blockers else "blocked_by: []\n"
    )
    return (
        "---\n"
        "ticket_schema: 1\n"
        f'ticket_id: "{ticket_id}"\n'
        f"execution_mode: {mode}\n"
        f"{blocker_field}"
        "---\n\n"
        f"# Ticket {ticket_id}\n"
    )


class TicketContractTests(unittest.TestCase):
    def test_bundled_happy_cycle_and_gate_fixtures(self) -> None:
        graph = parse_ticket_folder(FIXTURES / "happy")
        self.assertEqual(("01", "02"), graph.order)
        gate_kernel = Kernel.new("fixture-gate", parse_ticket_folder(FIXTURES / "gate"))
        self.assertEqual(1, len(gate_kernel.human_gated_ids()))
        with self.assertRaises(ContractError):
            parse_ticket_folder(FIXTURES / "cycle")

    def test_parses_versioned_contract_and_deterministic_dag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "20-second.md").write_text(ticket_text("20", ("10",)))
            (folder / "10-first.md").write_text(ticket_text("10"))

            graph = parse_ticket_folder(folder)

            self.assertEqual(("10", "20"), graph.order)
            self.assertEqual(("10",), graph.tickets["20"].blocked_by)

    def test_rejects_unknown_version_duplicate_missing_dependency_and_cycle(self) -> None:
        cases = {
            "version": (ticket_text("01").replace("ticket_schema: 1", "ticket_schema: 9"),),
            "duplicate": (ticket_text("01"), ticket_text("01")),
            "missing": (ticket_text("01", ("99",)),),
            "cycle": (ticket_text("01", ("02",)), ticket_text("02", ("01",))),
        }
        for label, documents in cases.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as tmp:
                folder = Path(tmp)
                for index, document in enumerate(documents):
                    (folder / f"{index}.md").write_text(document)
                with self.assertRaises(ContractError):
                    parse_ticket_folder(folder)

    def test_migrates_only_explicit_legacy_sections(self) -> None:
        legacy = (
            "## Ticket ID\n\n04\n\n"
            "## Execution Mode\n\nHITL\n\n"
            "## Blocked By\n\n- 02\n- 03\n\n"
            "## Outcome\n\nKeep this prose unchanged.\n"
        )

        migrated = migrate_ticket_text(legacy)

        self.assertTrue(migrated.startswith("---\nticket_schema: 1\n"))
        self.assertIn('ticket_id: "04"', migrated)
        self.assertIn('  - "02"\n  - "03"', migrated)
        self.assertIn("## Outcome\n\nKeep this prose unchanged.", migrated)

    def test_dependency_already_in_done_is_integrated_at_initialization(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            done = folder / "done"
            done.mkdir()
            (done / "01.md").write_text(ticket_text("01"))
            (folder / "02.md").write_text(ticket_text("02", ("01",)))

            graph = parse_ticket_folder(folder)
            kernel = Kernel.new("existing-done", graph)

            self.assertEqual("integrated", kernel.ledger["tickets"]["01"]["state"])
            self.assertEqual("02", kernel.next_ready_id())

    def test_autonomous_merge_requires_an_explicit_run_bound_grant(self) -> None:
        graph = parse_ticket_folder(FIXTURES / "happy")
        with self.assertRaisesRegex(
            TransitionError,
            "autonomous merge policy requires actor and durable evidence",
        ):
            Kernel.new(
                "grant-run",
                graph,
                provider="github",
                repo="/repo",
                merge_policy="autonomous",
            )
        with self.assertRaisesRegex(
            TransitionError,
            "manual merge policy cannot carry an autonomous grant",
        ):
            Kernel.new(
                "grant-run",
                graph,
                provider="github",
                repo="/repo",
                merge_actor="operator",
                merge_evidence="artifact://grant",
            )

        kernel = Kernel.new(
            "grant-run",
            graph,
            provider="github",
            repo="/repo",
            snapshot_manifest_digest="a" * 64,
            merge_policy="autonomous",
            merge_actor="operator",
            merge_evidence="artifact://grant",
        )

        self.assertEqual("autonomous", kernel.ledger["merge_policy"])
        self.assertEqual(
            {
                "schema": 1,
                "policy_version": 1,
                "repository_identity": "/repo",
                "run_id": "grant-run",
                "ticket_set_digest": "a" * 64,
                "provider": "github",
                "policy": "autonomous",
                "actor": "operator",
                "evidence": "artifact://grant",
            },
            kernel.ledger["autonomous_merge_grant"],
        )
        self.assertEqual(
            kernel.ledger["autonomous_merge_grant"],
            kernel.report()["merge_grant"],
        )
        for field, forged_value in (
            ("run_id", "another-run"),
            ("ticket_set_digest", "b" * 64),
            ("repository_identity", "/another-repo"),
            ("provider", "azure-devops"),
        ):
            forged = json.loads(json.dumps(kernel.ledger))
            forged["autonomous_merge_grant"][field] = forged_value
            with self.subTest(field=field), self.assertRaisesRegex(
                TransitionError,
                "autonomous merge grant contradicts its run binding",
            ):
                Kernel(forged)
        kernel.ledger["tickets"]["01"]["state"] = "gated"
        kernel.ledger["tickets"]["01"]["pr"] = {"pr_id": "1"}
        kernel.ledger["tickets"]["02"]["state"] = "pr-open"
        kernel.ledger["tickets"]["02"]["pr"] = {"pr_id": "2"}
        self.assertIsNone(kernel.pending_autonomous_merge_id())
        kernel.ledger["tickets"]["01"]["state"] = "integrated"
        kernel.ledger["tickets"]["01"]["delivery_lineage"] = {
            "base_branch": "main"
        }
        kernel.ledger["tickets"]["02"]["delivery_lineage"] = {
            "base_branch": "main"
        }
        self.assertEqual("02", kernel.pending_autonomous_merge_id())


def record_review_handoff(
    kernel: Kernel,
    ticket_id: str,
    candidate: CandidateRef,
    *,
    stage: str = "review",
    findings: list[str] | None = None,
) -> None:
    contract = list(LEAF_PHASE_CONTRACTS[stage])
    result: dict[str, object] = {
        "schema": 3,
        "complete": True,
        "candidate_ref": {
            "base_tree_oid": candidate.base_tree_oid,
            "candidate_tree_oid": candidate.candidate_tree_oid,
            "ticket_digest": candidate.ticket_digest,
            "contract_version": candidate.contract_version,
        },
        "stage": stage,
        "phase_contract": contract,
        "scope": {
            "files_expected": [],
            "files_inspected": [],
            "files_remaining": [],
        },
        "phases_remaining": [],
        "commands_run": [],
        "findings": findings or [],
        "progress_phase": "handoff-ready",
        "stop_reason": None,
    }
    if stage in {"qa-plan", "qa-execute", "verify"}:
        result["quality"] = {
            "schema": 1,
            "causal_scope": [stage],
            "evidence": [
                {
                    "id": f"evidence:{stage}",
                    "artifact": f"{stage}.json",
                    "sha256": "a" * 64,
                    "result": "pass",
                    "candidate_ref": result["candidate_ref"],
                }
            ],
            "limitations": ["local-only"],
        }
    kernel.record_leaf_result(
        ticket_id,
        result,
        candidate,
        expected_files=[],
    )


class KernelTests(unittest.TestCase):
    def make_kernel(
        self,
        graph_documents: tuple[str, ...],
        max_failures: int = 2,
        *,
        provider: str | None = None,
    ) -> Kernel:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        folder = Path(directory.name)
        for index, document in enumerate(graph_documents):
            (folder / f"{index}.md").write_text(document)
        graph = parse_ticket_folder(folder)
        return Kernel.new(
            "run-1",
            graph,
            max_quality_failures=max_failures,
            provider=provider,
        )

    @staticmethod
    def candidate(suffix: str = "a") -> CandidateRef:
        return CandidateRef(
            base_tree_oid=f"base-{suffix}",
            candidate_tree_oid=f"tree-{suffix}",
            ticket_digest=f"ticket-{suffix}",
            contract_version=2,
        )

    def pass_through_verify(self, kernel: Kernel, ticket_id: str, candidate: CandidateRef) -> None:
        kernel.activate(ticket_id, candidate)
        for stage in ("implement", "simplify", "review", "qa-plan", "qa-execute", "verify"):
            if stage in {"review", "qa-plan", "qa-execute", "verify"}:
                record_review_handoff(
                    kernel,
                    ticket_id,
                    candidate,
                    stage=stage,
                )
            kernel.record_stage(ticket_id, stage, "pass", candidate)

    def test_single_parent_stacks_but_multi_parent_join_waits_for_integration(self) -> None:
        kernel = self.make_kernel(
            (
                ticket_text("01"),
                ticket_text("02"),
                ticket_text("03", ("01", "02")),
                ticket_text("04", ("01",)),
            )
        )
        self.assertEqual("01", kernel.next_ready_id())
        kernel.ledger["tickets"]["01"]["state"] = "pr-open"

        self.assertEqual("02", kernel.next_ready_id())
        self.assertIn("04", kernel.ready_ids())
        self.assertIn("03", kernel.dependency_blocked_ids())

    def test_one_mutator_and_candidate_drift_rejected_without_mutation(self) -> None:
        kernel = self.make_kernel((ticket_text("01"), ticket_text("02")))
        candidate = self.candidate()
        kernel.activate("01", candidate)
        with self.assertRaises(TransitionError):
            kernel.activate("02", candidate)

        before = json.loads(json.dumps(kernel.ledger))
        with self.assertRaises(TransitionError):
            kernel.record_stage("01", "implement", "pass", self.candidate("changed"))
        self.assertEqual(before, kernel.ledger)
        self.assertTrue(
            all("snapshot" in event for event in kernel.ledger["history"])
        )

    def test_quality_failure_retries_exactly_then_fails(self) -> None:
        kernel = self.make_kernel((ticket_text("01"),), max_failures=2)
        candidate = self.candidate()
        kernel.activate("01", candidate)
        kernel.record_stage("01", "implement", "pass", candidate)
        kernel.record_stage("01", "simplify", "pass", candidate)
        record_review_handoff(
            kernel,
            "01",
            candidate,
            findings=["blocker:test: quality failure fixture"],
        )
        kernel.record_stage("01", "review", "fail", candidate)
        self.assertEqual("implement", kernel.ledger["tickets"]["01"]["stage"])
        self.assertEqual(1, kernel.ledger["tickets"]["01"]["quality_failures"])
        kernel.record_stage("01", "implement", "pass", candidate)
        kernel.record_stage("01", "simplify", "pass", candidate)
        record_review_handoff(
            kernel,
            "01",
            candidate,
            findings=["blocker:test: repeated quality failure fixture"],
        )
        kernel.record_stage("01", "review", "fail", candidate)
        self.assertEqual("failed", kernel.ledger["tickets"]["01"]["state"])
        self.assertEqual("quality", kernel.ledger["tickets"]["01"]["failure_kind"])

    def test_implementation_and_finalization_failures_are_distinct(self) -> None:
        for failing_stage, expected_kind in (
            ("implement", "implementation"),
            ("finalize", "finalization"),
        ):
            with self.subTest(stage=failing_stage):
                kernel = self.make_kernel((ticket_text("01"),))
                candidate = self.candidate(failing_stage)
                kernel.activate("01", candidate)
                for stage in STAGES_BEFORE[failing_stage]:
                    if stage in {"review", "qa-plan", "qa-execute", "verify"}:
                        record_review_handoff(
                            kernel,
                            "01",
                            candidate,
                            stage=stage,
                        )
                    kernel.record_stage("01", stage, "pass", candidate)
                kernel.record_stage("01", failing_stage, "fail", candidate)
                ticket = kernel.ledger["tickets"]["01"]
                self.assertEqual("failed", ticket["state"])
                self.assertEqual(expected_kind, ticket["failure_kind"])

    def test_failed_ticket_with_only_dependency_blocked_descendants_fails_run(self) -> None:
        kernel = self.make_kernel(
            (ticket_text("01"), ticket_text("02", ("01",)))
        )
        candidate = self.candidate()
        kernel.activate("01", candidate)
        kernel.record_stage("01", "implement", "fail", candidate)
        self.assertEqual("failed", kernel.ledger["run_state"])
        self.assertEqual(["02"], kernel.dependency_blocked_ids())

    def test_ticket_gate_does_not_block_unrelated_afk_work(self) -> None:
        kernel = self.make_kernel((ticket_text("01"), ticket_text("02")))
        candidate = self.candidate()
        kernel.activate("01", candidate)
        gate_id = kernel.open_gate("01", "environment", scope="ticket", reason="needs staging")

        self.assertEqual("02", kernel.next_ready_id())
        kernel.approve_gate(gate_id, actor="human", evidence="artifact://approval")
        self.assertEqual("active", kernel.ledger["tickets"]["01"]["state"])

    def test_gate_approval_while_another_ticket_is_active_defers_resume(self) -> None:
        kernel = self.make_kernel((ticket_text("01"), ticket_text("02")))
        first_candidate = self.candidate("first")
        kernel.activate("01", first_candidate)
        gate_id = kernel.open_gate(
            "01", "environment", scope="ticket", reason="needs staging"
        )
        kernel.activate("02", self.candidate("second"))

        kernel.approve_gate(gate_id, actor="human", evidence="artifact://approval")

        self.assertEqual("pending", kernel.ledger["tickets"]["01"]["state"])
        self.assertEqual("active", kernel.ledger["tickets"]["02"]["state"])
        self.assertEqual("implement", kernel.ledger["tickets"]["01"]["stage"])

    def test_run_scoped_gate_stops_all_ready_work(self) -> None:
        kernel = self.make_kernel((ticket_text("01"), ticket_text("02")))
        gate_id = kernel.open_gate(
            None, "credentials", scope="run", reason="provider credentials missing"
        )
        self.assertEqual([], kernel.ready_ids())
        self.assertEqual("waiting", kernel.ledger["run_state"])
        kernel.approve_gate(gate_id, actor="human", evidence="artifact://credentials")
        self.assertEqual(["01", "02"], kernel.ready_ids())

    def test_hitl_ticket_opens_start_gate_and_merge_requires_current_head(self) -> None:
        kernel = self.make_kernel((ticket_text("01", mode="HITL"),))
        self.assertIsNone(kernel.next_ready_id())
        gate_id = kernel.human_gated_ids()[0]
        kernel.approve_gate(gate_id, actor="reviewer", evidence="artifact://go")
        self.assertEqual("01", kernel.next_ready_id())

        candidate = self.candidate()
        self.pass_through_verify(kernel, "01", candidate)
        kernel.record_stage("01", "finalize", "pass", candidate)
        kernel.record_pr(
            "01", provider="github", pr_id="7", head_sha="sha-1",
            base_branch="main", base_sha="base-sha"
        )
        self.assertEqual("waiting", kernel.ledger["run_state"])
        with self.assertRaises(TransitionError):
            kernel.authorize_merge("01", actor="reviewer", head_sha="sha-old", evidence="approval")
        kernel.authorize_merge("01", actor="reviewer", head_sha="sha-1", evidence="approval")
        kernel.record_integration("01", expected_head_sha="sha-1")
        self.assertEqual("integrated", kernel.ledger["tickets"]["01"]["state"])
        self.assertEqual("completed", kernel.ledger["run_state"])

    def test_envelope_execution_mode_controls_start_gate_and_resume(self) -> None:
        kernel = self.make_kernel(
            (
                ticket_text("01", mode="AFK"),
                ticket_text("02", mode="HITL"),
            ),
            max_failures=2,
        )
        self.assertNotIn("supervision", inspect.signature(Kernel.new).parameters)
        afk = kernel.ledger["tickets"]["01"]
        hitl = kernel.ledger["tickets"]["02"]
        self.assertEqual("AFK", afk["execution_mode"])
        self.assertEqual("HITL", hitl["execution_mode"])
        self.assertNotIn("effective_mode", afk)
        self.assertNotIn("effective_mode", hitl)
        start_gates = [
            gate
            for gate in kernel.ledger["gates"].values()
            if gate["kind"] == "start"
        ]
        self.assertEqual(1, len(start_gates))
        self.assertEqual("02", start_gates[0]["ticket_id"])
        self.assertEqual("ticket", start_gates[0]["scope"])
        self.assertEqual("human", start_gates[0]["category"])
        self.assertEqual(["01"], kernel.ready_ids())

        before = json.loads(json.dumps(kernel.ledger))
        with self.assertRaisesRegex(TransitionError, "not ready"):
            kernel.activate("02", self.candidate("hitl-before-approval"))
        self.assertEqual(before, kernel.ledger)

        afk_candidate = self.candidate("afk")
        kernel.activate("01", afk_candidate)
        kernel.record_stage("01", "implement", "fail", afk_candidate)
        restored = Kernel(json.loads(json.dumps(kernel.ledger)))
        self.assertEqual(0, restored.ledger["tickets"]["02"]["quality_failures"])
        restored.approve_gate(
            start_gates[0]["gate_id"],
            actor="operator",
            evidence="artifact://start",
        )
        self.assertEqual(["02"], restored.ready_ids())

        hitl_candidate = self.candidate("hitl-after-approval")
        restored.activate("02", hitl_candidate)
        restored.record_stage("02", "implement", "pass", hitl_candidate)
        restored.record_stage("02", "simplify", "pass", hitl_candidate)
        record_review_handoff(
            restored,
            "02",
            hitl_candidate,
            findings=["blocker:test: HITL review failure fixture"],
        )
        restored.record_stage("02", "review", "fail", hitl_candidate)
        self.assertEqual(1, restored.ledger["tickets"]["02"]["quality_failures"])
        self.assertEqual("implement", restored.ledger["tickets"]["02"]["stage"])

    def test_external_integration_is_one_validated_idempotent_transaction(self) -> None:
        kernel = self.make_kernel(
            (ticket_text("01"), ticket_text("02", ("01",))),
            provider="github",
        )
        candidate = self.candidate()
        self.pass_through_verify(kernel, "01", candidate)
        kernel.record_stage("01", "finalize", "pass", candidate)
        kernel.record_pr(
            "01", provider="github", pr_id="7", head_sha="sha-1",
            base_branch="main", base_sha="base-sha"
        )
        observation = {
            "schema": 1,
            "provider": "github",
            "operation": "get-pr-state",
            "evidence_class": "live",
            "observed": True,
            "pr_id": "7",
            "head_sha": "sha-1",
            "state": "merged",
        }
        kernel.ledger["tickets"]["01"]["pr"]["provider"] = "azure-devops"
        wrong_provider = json.loads(json.dumps(kernel.ledger))
        with self.assertRaises(TransitionError):
            kernel.record_external_integration(
                "01",
                actor="reviewer",
                head_sha="sha-1",
                evidence="artifact://approval",
                provider_observation=observation,
            )
        self.assertEqual(wrong_provider, kernel.ledger)
        kernel.ledger["tickets"]["01"]["pr"]["provider"] = "github"
        before = json.loads(json.dumps(kernel.ledger))
        for field, value in (
            ("provider", "azure-devops"),
            ("pr_id", "8"),
            ("head_sha", "sha-2"),
            ("evidence_class", "simulated"),
            ("observed", False),
            ("state", "open"),
        ):
            contradictory = {**observation, field: value}
            with self.subTest(field=field), self.assertRaises(TransitionError):
                kernel.record_external_integration(
                    "01",
                    actor="reviewer",
                    head_sha="sha-1",
                    evidence="artifact://approval",
                    provider_observation=contradictory,
                )
            self.assertEqual(before, kernel.ledger)
        with self.assertRaises(TransitionError):
            kernel.record_external_integration(
                "01",
                actor="reviewer",
                head_sha="sha-1",
                evidence="",
                provider_observation=observation,
            )
        self.assertEqual(before, kernel.ledger)

        receipt, replayed = kernel.record_external_integration(
            "01",
            actor="reviewer",
            head_sha="sha-1",
            evidence="artifact://approval",
            provider_observation=observation,
        )

        self.assertFalse(replayed)
        self.assertEqual("external", receipt["mode"])
        self.assertEqual("integrated", kernel.ledger["tickets"]["01"]["state"])
        self.assertEqual(["02"], kernel.ready_ids())
        self.assertEqual("running", kernel.ledger["run_state"])
        self.assertEqual(
            "external-merge-integrated", kernel.ledger["history"][-1]["event"]
        )
        integrated = json.loads(json.dumps(kernel.ledger))
        replay_receipt, replayed = kernel.record_external_integration(
            "01",
            actor="reviewer",
            head_sha="sha-1",
            evidence="artifact://approval",
            provider_observation=observation,
        )
        self.assertTrue(replayed)
        self.assertEqual(receipt, replay_receipt)
        self.assertEqual(integrated, kernel.ledger)

    def test_pr_head_change_invalidates_merge_authorization(self) -> None:
        kernel = self.make_kernel((ticket_text("01"), ticket_text("02")))
        candidate = self.candidate()
        self.pass_through_verify(kernel, "01", candidate)
        kernel.record_stage("01", "finalize", "pass", candidate)
        kernel.record_pr(
            "01", provider="github", pr_id="7", head_sha="sha-1",
            base_branch="main", base_sha="base-sha"
        )
        kernel.authorize_merge(
            "01", actor="reviewer", head_sha="sha-1", evidence="approval"
        )

        kernel.update_pr_head("01", expected_old="sha-1", new="sha-2")

        self.assertIsNone(
            kernel.ledger["tickets"]["01"]["merge_authorization"]
        )
        with self.assertRaises(TransitionError):
            kernel.record_integration("01", expected_head_sha="sha-2")

    def test_pending_runner_merge_has_priority_over_unrelated_ticket(self) -> None:
        kernel = self.make_kernel((ticket_text("01"), ticket_text("02")))
        candidate = self.candidate()
        self.pass_through_verify(kernel, "01", candidate)
        kernel.record_stage("01", "finalize", "pass", candidate)
        kernel.record_pr(
            "01", provider="github", pr_id="7", head_sha="sha-1",
            base_branch="main", base_sha="base-sha"
        )
        self.assertEqual(["02"], kernel.ready_ids())

        kernel.authorize_merge(
            "01",
            actor="reviewer",
            head_sha="sha-1",
            evidence="artifact://approval",
        )

        self.assertEqual("01", kernel.pending_runner_merge_id())
        self.assertEqual([], kernel.ready_ids())
        with self.assertRaisesRegex(TransitionError, "not ready"):
            kernel.activate("02", self.candidate("unrelated"))

    def test_finalization_is_terminal_guarded_and_idempotent(self) -> None:
        kernel = self.make_kernel((ticket_text("01"),))
        candidate = self.candidate()
        kernel.activate("01", candidate)
        with self.assertRaises(TransitionError):
            kernel.record_finalization_effect("01", "move-done")
        for stage in ("implement", "simplify", "review", "qa-plan", "qa-execute", "verify"):
            if stage in {"review", "qa-plan", "qa-execute", "verify"}:
                record_review_handoff(kernel, "01", candidate, stage=stage)
            kernel.record_stage("01", stage, "pass", candidate)
        kernel.record_stage("01", "finalize", "pass", candidate)

        first = kernel.record_finalization_effect("01", "move-done")
        second = kernel.record_finalization_effect("01", "move-done")

        self.assertTrue(first)
        self.assertFalse(second)

    def test_hold_stops_active_ticket_and_blocks_descendants_with_cause(self) -> None:
        kernel = self.make_kernel((ticket_text("01"), ticket_text("02", ("01",))))
        candidate = self.candidate()
        kernel.activate("01", candidate)
        digest = kernel.ledger["tickets"]["01"]["ticket_digest"]

        kernel.record_disposition_transition(
            "01",
            {
                "schema": 1,
                "transition_id": "hold-01",
                "ticket_id": "01",
                "from_disposition": "open",
                "to_disposition": "on-hold",
                "actor": "user:alice",
                "reason": "await product decision",
                "authority_ref": "decision:hold-01",
                "expected_digest": digest,
                "authority_gate_id": None,
                "source_relative_path": kernel.ledger["tickets"]["01"][
                    "current_source_relative_path"
                ],
                "destination_relative_path": "hold/0.md",
                "state": "applied",
            },
        )

        ticket = kernel.ledger["tickets"]["01"]
        self.assertEqual("on-hold", ticket["disposition"])
        self.assertNotIn("lifecycle", ticket)
        self.assertEqual("stopped", ticket["attempt_outcome"])
        self.assertEqual("administrative-on-hold", ticket["stop_reason"])
        self.assertEqual([], kernel.ready_ids())
        report = kernel.report()
        self.assertEqual(2, report["schema"])
        self.assertEqual("blocked", report["tickets"]["02"]["readiness"])
        self.assertEqual(
            [{"ticket_id": "01", "reason": "dependency-on-hold"}],
            report["tickets"]["02"]["readiness_causes"],
        )
        AtomicLedger._validate(json.loads(json.dumps(kernel.ledger)))
        before_replay = copy.deepcopy(kernel.ledger)
        kernel.record_disposition_transition(
            "01", kernel.ledger["tickets"]["01"]["disposition_receipt"]
        )
        self.assertEqual(before_replay, kernel.ledger)

    def test_gate_authorized_reopen_invalidates_current_candidate_and_evidence(self) -> None:
        kernel = self.make_kernel((ticket_text("01"), ticket_text("02")))
        candidate = self.candidate()
        kernel.activate("01", candidate)
        digest = kernel.ledger["tickets"]["01"]["ticket_digest"]
        held = {
            "schema": 1,
            "transition_id": "hold-01",
            "ticket_id": "01",
            "from_disposition": "open",
            "to_disposition": "on-hold",
            "actor": "user:alice",
            "reason": "await product decision",
            "authority_ref": "decision:hold-01",
            "expected_digest": digest,
            "authority_gate_id": None,
            "source_relative_path": kernel.ledger["tickets"]["01"][
                "current_source_relative_path"
            ],
            "destination_relative_path": "hold/0.md",
            "state": "applied",
        }
        kernel.record_disposition_transition("01", held)

        gate_id = kernel.request_reopen(
            "01", requested_by="agent:planner", reason="decision resolved"
        )
        kernel.approve_gate(
            gate_id,
            actor="user:alice",
            evidence="decision:reopen-01",
        )
        with self.assertRaisesRegex(TransitionError, "differs"):
            kernel.preflight_disposition_transition(
                "01",
                "open",
                actor="user:alice",
                reason="wrong reason",
                authority_ref="decision:reopen-01",
                authority_gate_id=gate_id,
            )
        with self.assertRaisesRegex(TransitionError, "reopen requires"):
            kernel.preflight_disposition_transition(
                "02", "open", authority_gate_id=gate_id
            )

        reopened = {
            **held,
            "transition_id": "reopen-01",
            "from_disposition": "on-hold",
            "to_disposition": "open",
            "actor": "user:alice",
            "reason": "decision resolved",
            "authority_ref": "decision:reopen-01",
            "authority_gate_id": gate_id,
            "source_relative_path": "hold/0.md",
            "destination_relative_path": "0.md",
        }
        kernel.record_disposition_transition("01", reopened)

        ticket = kernel.ledger["tickets"]["01"]
        self.assertEqual("open", ticket["disposition"])
        self.assertNotIn("lifecycle", ticket)
        self.assertIsNone(ticket["attempt_outcome"])
        self.assertEqual("pending", ticket["state"])
        self.assertIsNone(ticket["stage"])
        self.assertIsNone(ticket["candidate_ref"])
        self.assertEqual([], ticket["validated_stages"])
        self.assertEqual({}, ticket["delivery"])
        self.assertIsNone(ticket["pr"])
        self.assertIsNone(ticket["merge_authorization"])
        self.assertEqual("01", kernel.next_ready_id())
        AtomicLedger._validate(json.loads(json.dumps(kernel.ledger)))
        after = copy.deepcopy(kernel.ledger)
        kernel.record_disposition_transition("01", reopened)
        self.assertEqual(after, kernel.ledger)
        with self.assertRaisesRegex(TransitionError, "reopen requires"):
            kernel.preflight_disposition_transition(
                "01", "open", authority_gate_id=gate_id
            )

    def test_pause_is_run_scoped_and_unicode_history_is_replayable(self) -> None:
        kernel = self.make_kernel((ticket_text("01"),))

        kernel.pause_run(actor="user:josé", reason="attesa ñandú")

        self.assertEqual([], kernel.ready_ids())
        self.assertEqual("paused", kernel.report()["execution_lifecycle"])
        with tempfile.TemporaryDirectory() as temporary:
            store = AtomicLedger(Path(temporary) / "ledger.json")
            store.save(kernel.ledger)
            loaded = store.load()
        self.assertEqual("user:josé", loaded["pause"]["actor"])

        kernel.unpause_run(actor="user:josé", reason="riprendi")
        self.assertEqual("01", kernel.next_ready_id())


    def test_report_projects_lifecycle_from_authoritative_state_only(self) -> None:
        kernel = self.make_kernel((ticket_text("01"),))
        ticket = kernel.ledger["tickets"]["01"]
        self.assertNotIn("lifecycle", ticket)
        self.assertIsNone(ticket["attempt_outcome"])
        self.assertEqual(
            "not-started", kernel.report()["tickets"]["01"]["lifecycle"]
        )

        kernel.activate("01", self.candidate())
        self.assertEqual("running", kernel.report()["tickets"]["01"]["lifecycle"])
        for state in ("gated", "failed", "verified", "pr-open"):
            ticket["state"] = state
            self.assertEqual(state, kernel.report()["tickets"]["01"]["lifecycle"])
        ticket["state"] = "integrated"
        self.assertEqual(
            "completed", kernel.report()["tickets"]["01"]["lifecycle"]
        )


class LedgerTests(unittest.TestCase):
    @staticmethod
    def write_legacy(path: Path, document: dict[str, object]) -> None:
        payload = json.dumps(
            document,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        path.write_text(
            json.dumps(
                {
                    "envelope_schema": 1,
                    "integrity": hashlib.sha256(payload).hexdigest(),
                    "payload": document,
                },
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

    def test_schema3_history_requires_and_supports_explicit_lifecycle_migration(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            tickets = root / "tickets"
            tickets.mkdir()
            (tickets / "01.md").write_text(ticket_text("01"), encoding="utf-8")
            legacy_kernel = Kernel.new(
                "legacy-v3", parse_ticket_folder(tickets)
            )
            legacy_kernel.activate(
                "01",
                CandidateRef("base-legacy", "tree-legacy", "ticket-legacy", 2),
            )
            legacy = as_schema_three(legacy_kernel.ledger)
            original_history = copy.deepcopy(legacy["history"])
            payload = json.dumps(
                legacy,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode("utf-8")
            envelope = {
                "envelope_schema": 1,
                "integrity": hashlib.sha256(payload).hexdigest(),
                "payload": legacy,
            }
            path = root / "ledger.json"
            path.write_text(
                json.dumps(
                    envelope,
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            store = AtomicLedger(path)

            with self.assertRaisesRegex(LedgerError, "migrate-run-lifecycle"):
                store.load()

            migrated = store.migrate_lifecycle_v3()

            self.assertEqual(4, migrated["schema"])
            self.assertEqual(original_history, migrated["history"][:-1])
            self.assertEqual(
                "ledger-v3-lifecycle-migrated", migrated["history"][-1]["event"]
            )
            self.assertEqual(
                original_history[-1]["hash"],
                migrated["history"][-1]["previous_hash"],
            )
            self.assertEqual("open", migrated["tickets"]["01"]["disposition"])
            self.assertNotIn("lifecycle", migrated["tickets"]["01"])
            self.assertIsNone(migrated["tickets"]["01"]["attempt_outcome"])
            self.assertEqual(migrated, AtomicLedger(path).load())
            self.assertEqual(migrated, store.migrate_lifecycle_v3())
            self.assertEqual(len(original_history) + 1, len(migrated["history"]))

    def test_schema3_migration_accepts_only_missing_unknown_leaf_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            tickets = root / "tickets"
            tickets.mkdir()
            (tickets / "01.md").write_text(ticket_text("01"), encoding="utf-8")
            kernel = Kernel.new("legacy-leaf", parse_ticket_folder(tickets))
            candidate = CandidateRef("base", "tree", "ticket", 2)
            kernel.activate("01", candidate)
            kernel.record_stage("01", "implement", "pass", candidate)
            kernel.record_stage("01", "simplify", "pass", candidate)
            record_review_handoff(kernel, "01", candidate)
            legacy = as_schema_three(kernel.ledger)

            snapshots = [legacy, *(event["snapshot"] for event in legacy["history"])]
            for snapshot in snapshots:
                ticket = snapshot["tickets"]["01"]
                handoff = ticket.get("leaf_handoff")
                if handoff is not None:
                    handoff.pop("execution", None)
                for progress in ticket.get("leaf_progress_events", []):
                    progress.pop("execution", None)
            resign_forged_history(legacy)
            original_history = copy.deepcopy(legacy["history"])
            path = root / "ledger.json"
            self.write_legacy(path, legacy)

            migrated = AtomicLedger(path).migrate_lifecycle_v3()

            self.assertEqual(original_history, migrated["history"][:-1])
            self.assertEqual(
                "ledger-v3-lifecycle-migrated", migrated["history"][-1]["event"]
            )
            self.assertEqual(migrated, AtomicLedger(path).migrate_lifecycle_v3())

            conflicting = copy.deepcopy(legacy)
            inline = {
                "mode": "inline",
                "isolation": "shared-context",
                "parallel": False,
                "authority_ref": None,
            }
            conflicting["tickets"]["01"]["leaf_progress_events"][-1][
                "execution"
            ] = inline
            conflicting["history"][-1]["snapshot"]["tickets"]["01"][
                "leaf_progress_events"
            ][-1]["execution"] = inline
            resign_forged_history(conflicting)
            conflict_path = root / "conflict.json"
            self.write_legacy(conflict_path, conflicting)

            with self.assertRaisesRegex(
                LedgerError, "leaf-result-recorded deterministic replay differs"
            ):
                AtomicLedger(conflict_path).migrate_lifecycle_v3()

    def test_schema3_migration_state_matrix_requires_durable_completion(self) -> None:
        candidate = CandidateRef("base", "tree", "ticket", 2)

        def built(
            state: str, *, finalized: bool = False, source_mode: str = "tracked"
        ) -> Kernel:
            directory = tempfile.TemporaryDirectory()
            self.addCleanup(directory.cleanup)
            folder = Path(directory.name)
            (folder / "01.md").write_text(ticket_text("01"), encoding="utf-8")
            kernel = Kernel.new(
                f"legacy-{state}-{finalized}-{source_mode}",
                parse_ticket_folder(folder),
                source_mode=source_mode,
            )
            if state == "pending":
                return kernel
            kernel.activate("01", candidate)
            if state == "active":
                return kernel
            if state == "gated" and not finalized:
                kernel.record_stage("01", "implement", "gated", candidate)
                return kernel
            if state == "failed":
                kernel.record_stage("01", "implement", "fail", candidate)
                return kernel
            for stage in PIPELINE:
                if stage in {"review", "qa-plan", "qa-execute", "verify"}:
                    record_review_handoff(kernel, "01", candidate, stage=stage)
                kernel.record_stage("01", stage, "pass", candidate)
            if state == "verified":
                return kernel
            kernel.record_pr(
                "01",
                provider="github",
                pr_id="7",
                head_sha="head",
                branch="ticket/01",
                base_branch="main",
                base_sha="base",
            )
            if finalized:
                if source_mode == "ignored":
                    kernel.record_delivery_metadata(
                        "01",
                        "ignored-finalization-applied",
                        {"state": "applied", "ticket_id": "01"},
                    )
                    effect = "move-done-and-summarize-external"
                else:
                    effect = "move-done-and-stage"
                kernel.record_finalization_effect("01", effect)
            if state == "gated":
                kernel.open_gate(
                    "01",
                    "provider-environment",
                    scope="ticket",
                    reason="delivery observation unavailable",
                )
                return kernel
            if state == "pr-open":
                return kernel
            kernel.authorize_merge(
                "01", actor="human", head_sha="head", evidence="gate://approval"
            )
            kernel.record_integration("01", expected_head_sha="head")
            return kernel

        cases = (
            ("pending", False, "tracked", "open"),
            ("active", False, "tracked", "open"),
            ("gated", False, "tracked", "open"),
            ("gated", True, "tracked", "completed"),
            ("gated", True, "ignored", "completed"),
            ("failed", False, "tracked", "open"),
            ("verified", False, "tracked", "open"),
            ("pr-open", False, "tracked", "open"),
            ("pr-open", True, "tracked", "completed"),
            ("pr-open", True, "ignored", "completed"),
            ("integrated", False, "tracked", "completed"),
        )
        for state, finalized, source_mode, expected_disposition in cases:
            with self.subTest(
                state=state, finalized=finalized, source_mode=source_mode
            ):
                legacy = as_schema_three(
                    built(
                        state, finalized=finalized, source_mode=source_mode
                    ).ledger
                )
                original_state = legacy["tickets"]["01"]["state"]
                with tempfile.TemporaryDirectory() as temporary:
                    path = Path(temporary) / "ledger.json"
                    self.write_legacy(path, legacy)
                    migrated = AtomicLedger(path).migrate_lifecycle_v3()
                ticket = migrated["tickets"]["01"]
                self.assertEqual(original_state, ticket["state"])
                self.assertEqual(expected_disposition, ticket["disposition"])
                self.assertIsNone(ticket["attempt_outcome"])
                self.assertIsNone(ticket["stop_reason"])
                self.assertNotIn("lifecycle", ticket)

    def test_schema3_migration_rejects_rehashed_impossible_transition(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            tickets = root / "tickets"
            tickets.mkdir()
            (tickets / "01.md").write_text(ticket_text("01"), encoding="utf-8")
            kernel = Kernel.new("legacy-forged", parse_ticket_folder(tickets))
            kernel.activate("01", CandidateRef("base", "tree", "ticket", 2))
            legacy = as_schema_three(kernel.ledger)
            legacy["history"][-1]["details"]["candidate_digest"] = "0" * 64
            resign_forged_history(legacy)
            path = root / "ledger.json"
            self.write_legacy(path, legacy)

            with mock.patch(
                "autopilot.ledger._migrate_legacy_ticket"
            ) as migrate_ticket, self.assertRaisesRegex(
                LedgerError, "ticket-activated CandidateRef payload is invalid"
            ):
                AtomicLedger(path).migrate_lifecycle_v3()
            migrate_ticket.assert_not_called()

    def test_run_lock_serializes_decision_effect_and_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ledger.json"
            AtomicLedger(path).save(
                {"schema": 4, "run_id": "locked", "history": []}
            )
            effect_started = threading.Event()
            release_effect = threading.Event()
            effects: list[str] = []
            errors: list[Exception] = []

            def first_worker() -> None:
                store = AtomicLedger(path)
                with store.run_locked():
                    store.load()
                    effects.append("applied")
                    effect_started.set()
                    release_effect.wait(timeout=2)

            thread = threading.Thread(target=first_worker)
            thread.start()
            self.assertTrue(effect_started.wait(timeout=2))
            try:
                with AtomicLedger(path).run_locked():
                    effects.append("duplicate")
            except LedgerError as error:
                errors.append(error)
            release_effect.set()
            thread.join(timeout=2)

            self.assertEqual(["applied"], effects)
            self.assertEqual(1, len(errors))

    def test_atomic_ledger_round_trip_and_history_tamper_detection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ledger.json"
            store = AtomicLedger(path)
            document = {"schema": 4, "run_id": "r1", "history": []}
            store.save(document)
            loaded = store.load()
            self.assertEqual(document, loaded)
            envelope = json.loads(path.read_text())
            self.assertEqual({"envelope_schema", "integrity", "payload"}, set(envelope))
            self.assertFalse(path.with_suffix(".json.sha256").exists())
            envelope["payload"]["history"].append({"sequence": 2})
            path.write_text(json.dumps(envelope))
            with self.assertRaises(LedgerError):
                store.load()

    def test_stale_lock_file_does_not_block_after_process_lock_is_released(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ledger.json"
            store = AtomicLedger(path)
            store.lock_path.parent.mkdir(parents=True, exist_ok=True)
            store.lock_path.write_text("stale-owner\n")
            document = {"schema": 4, "run_id": "r1", "history": []}
            store.save(document)
            self.assertEqual(document, store.load())

    def test_optimistic_lock_rejects_a_lost_update(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ledger.json"
            seed = AtomicLedger(path)
            seed.save({"schema": 4, "run_id": "r1", "history": []})
            first = AtomicLedger(path)
            second = AtomicLedger(path)
            first_document = first.load()
            second_document = second.load()
            first_document["writer"] = "first"
            first.save(first_document)
            second_document["writer"] = "second"
            with self.assertRaises(LedgerError):
                second.save(second_document)

    def test_event_hash_chain_rejects_rewritten_history_even_with_new_file_digest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "tickets"
            folder.mkdir()
            (folder / "01.md").write_text(ticket_text("01"))
            kernel = Kernel.new("chain", parse_ticket_folder(folder))
            path = Path(tmp) / "ledger.json"
            store = AtomicLedger(path)
            store.save(kernel.ledger)
            envelope = json.loads(path.read_text())
            payload = envelope["payload"]
            payload["history"][0]["event"] = "rewritten"
            encoded = json.dumps(
                payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            )
            envelope["integrity"] = hashlib.sha256(encoded.encode()).hexdigest()
            path.write_text(json.dumps(envelope))
            with self.assertRaises(LedgerError):
                AtomicLedger(path).load()

    def test_semantically_impossible_snapshot_is_rejected_with_valid_integrity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "tickets"
            folder.mkdir()
            (folder / "01.md").write_text(ticket_text("01"))
            (folder / "02.md").write_text(ticket_text("02"))
            kernel = Kernel.new("impossible", parse_ticket_folder(folder))
            path = Path(tmp) / "ledger.json"
            store = AtomicLedger(path)
            store.save(kernel.ledger)
            envelope = json.loads(path.read_text())
            payload = envelope["payload"]
            payload["tickets"]["01"]["state"] = "active"
            payload["tickets"]["02"]["state"] = "active"
            encoded = json.dumps(
                payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            )
            envelope["integrity"] = hashlib.sha256(encoded.encode()).hexdigest()
            path.write_text(json.dumps(envelope))
            with self.assertRaises(LedgerError):
                AtomicLedger(path).load()

    def test_snapshot_history_must_replay_to_the_persisted_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "tickets"
            folder.mkdir()
            (folder / "01.md").write_text(ticket_text("01"))
            kernel = Kernel.new("replay", parse_ticket_folder(folder))
            path = Path(tmp) / "ledger.json"
            AtomicLedger(path).save(kernel.ledger)
            envelope = json.loads(path.read_text())
            payload = envelope["payload"]
            payload["tickets"]["01"]["state"] = "failed"
            payload["tickets"]["01"]["failure_kind"] = "implementation"
            payload["run_state"] = "failed"
            encoded = json.dumps(
                payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            )
            envelope["integrity"] = hashlib.sha256(encoded.encode()).hexdigest()
            path.write_text(json.dumps(envelope))
            with self.assertRaises(LedgerError):
                AtomicLedger(path).load()

    def test_history_snapshots_are_successive_not_final_state_copies(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "tickets"
            folder.mkdir()
            (folder / "01.md").write_text(ticket_text("01", mode="HITL"))
            kernel = Kernel.new("successive", parse_ticket_folder(folder))
            history = kernel.ledger["history"]
            self.assertEqual("pending", history[0]["snapshot"]["tickets"]["01"]["state"])
            self.assertEqual("gated", history[1]["snapshot"]["tickets"]["01"]["state"])


class FinalizerTests(unittest.TestCase):
    def test_reopened_held_or_canceled_source_finalizes_from_current_path(self) -> None:
        for source_mode in ("tracked", "ignored"):
            for target in ("on-hold", "canceled"):
                with self.subTest(source_mode=source_mode, target=target), tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    subprocess.run(
                        ["git", "init", "-b", "main"],
                        cwd=repo,
                        check=True,
                        capture_output=True,
                    )
                    subprocess.run(
                        ["git", "config", "user.email", "tests@example.invalid"],
                        cwd=repo,
                        check=True,
                    )
                    subprocess.run(
                        ["git", "config", "user.name", "Tests"],
                        cwd=repo,
                        check=True,
                    )
                    folder = repo / "tickets"
                    folder.mkdir()
                    source = folder / "01.md"
                    source.write_text(ticket_text("01"))
                    if source_mode == "ignored":
                        (repo / ".gitignore").write_text("tickets/\n")
                    else:
                        subprocess.run(["git", "add", "tickets/01.md"], cwd=repo, check=True)
                    subprocess.run(["git", "add", ".gitignore"], cwd=repo, check=False)
                    subprocess.run(["git", "commit", "-m", "ticket"], cwd=repo, check=True)
                    graph = parse_ticket_folder(folder)
                    kernel = Kernel.new(
                        f"finalizer-{source_mode}-{target}",
                        graph,
                        worktree=str(repo),
                        repo=str(repo),
                        source_mode=source_mode,
                    )
                    state_dir = repo / ".git" / "ticket-autopilot" / "lifecycle"
                    digest = graph.tickets["01"].digest
                    receipt = transition_ticket_source(
                        folder,
                        state_dir,
                        "01",
                        target,
                        actor="user:alice",
                        reason="administrative stop",
                        authority_ref=f"decision:{target}",
                        expected_digest=digest,
                    )
                    kernel.record_disposition_transition("01", receipt)
                    gate_id = kernel.request_reopen(
                        "01", requested_by="agent:planner", reason="resume approved"
                    )
                    kernel.approve_gate(
                        gate_id,
                        actor="user:alice",
                        evidence="decision:reopen-01",
                    )
                    authority = kernel.preflight_disposition_transition(
                        "01", "open", authority_gate_id=gate_id
                    )
                    reopened = transition_ticket_source(
                        folder,
                        state_dir,
                        "01",
                        "open",
                        actor=authority["actor"],
                        reason=authority["reason"],
                        authority_ref=authority["authority_ref"],
                        authority_gate_id=gate_id,
                        expected_digest=digest,
                    )
                    kernel.record_disposition_transition("01", reopened)
                    ticket = kernel.ledger["tickets"]["01"]
                    self.assertEqual("01.md", ticket["source_relative_path"])
                    self.assertEqual("01.md", ticket["current_source_relative_path"])

                    candidate = CandidateRef("base", "tree", digest, 2)
                    kernel.activate("01", candidate)
                    for stage in PIPELINE:
                        if stage in {"review", "qa-plan", "qa-execute", "verify"}:
                            record_review_handoff(kernel, "01", candidate, stage=stage)
                        kernel.record_stage("01", stage, "pass", candidate)
                    store = AtomicLedger(
                        repo / ".git" / "ticket-autopilot" / "ledger.json"
                    )
                    store.save(kernel.ledger)

                    self.assertTrue(finalize_done(store, kernel, "01"))
                    self.assertEqual("01.md", ticket["source_relative_path"])
                    self.assertEqual(
                        "done/01.md", ticket["current_source_relative_path"]
                    )
                    self.assertTrue((folder / "done" / "01.md").is_file())

    def test_done_move_and_git_staging_are_terminal_guarded_and_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True, capture_output=True)
            subprocess.run(
                ["git", "config", "user.email", "tests@example.invalid"],
                cwd=repo,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Tests"], cwd=repo, check=True
            )
            folder = repo / "tickets"
            folder.mkdir()
            path = folder / "01.md"
            path.write_text(ticket_text("01"))
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-m", "ticket"], cwd=repo, check=True)
            graph = parse_ticket_folder(folder)
            kernel = Kernel.new(
                "finalizer", graph, worktree=str(repo), repo=str(repo)
            )
            store = AtomicLedger(repo / ".git" / "ticket-autopilot" / "ledger.json")
            store.save(kernel.ledger)

            with self.assertRaises(TransitionError):
                finalize_done(store, kernel, "01")

            candidate = CandidateRef(
            base_tree_oid="base",
            candidate_tree_oid="tree",
                ticket_digest=graph.tickets["01"].digest,
            contract_version=2,
            )
            kernel.activate("01", candidate)
            for stage in (
                "implement",
                "simplify",
                "review",
                "qa-plan",
                "qa-execute",
                "verify",
                "finalize",
            ):
                if stage in {"review", "qa-plan", "qa-execute", "verify"}:
                    record_review_handoff(kernel, "01", candidate, stage=stage)
                kernel.record_stage("01", stage, "pass", candidate)
            store.save(kernel.ledger)

            self.assertTrue(finalize_done(store, kernel, "01"))
            self.assertFalse(path.exists())
            self.assertTrue((folder / "done" / "01.md").exists())
            self.assertEqual(
                "completed", kernel.ledger["tickets"]["01"]["disposition"]
            )
            self.assertNotIn("lifecycle", kernel.ledger["tickets"]["01"])
            self.assertEqual(
                "verified", kernel.report()["tickets"]["01"]["lifecycle"]
            )
            AtomicLedger._validate(json.loads(json.dumps(kernel.ledger)))
            status = subprocess.run(
                ["git", "status", "--porcelain=v1"],
                cwd=repo,
                text=True,
                capture_output=True,
                check=True,
            ).stdout
            self.assertIn("tickets/01.md", status)
            self.assertIn("tickets/done/01.md", status)
            self.assertFalse(finalize_done(store, kernel, "01"))

    def test_candidate_ref_hashes_staged_tree_and_detects_later_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True, capture_output=True)
            subprocess.run(
                ["git", "config", "user.email", "tests@example.invalid"],
                cwd=repo,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Tests"], cwd=repo, check=True
            )
            path = repo / "value.txt"
            path.write_text("one\n")
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-m", "one"], cwd=repo, check=True)
            path.write_text("two\n")

            fixed = candidate_ref(repo, "ticket-digest")
            assert_candidate(repo, fixed)
            path.write_text("three\n")
            with self.assertRaises(TransitionError):
                assert_candidate(repo, fixed)


def resign_forged_history(document: dict[str, object]) -> None:
    previous_hash = "0" * 64
    for event in document["history"]:
        event["previous_hash"] = previous_hash
        event.pop("hash", None)
        encoded = json.dumps(
            event,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        event["hash"] = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
        previous_hash = event["hash"]


def as_schema_three(document: dict[str, object]) -> dict[str, object]:
    legacy = copy.deepcopy(document)

    def strip(snapshot: dict[str, object]) -> None:
        snapshot["schema"] = 3
        snapshot.pop("pause", None)
        snapshot.pop("legacy_lifecycle_migration", None)
        for ticket in snapshot.get("tickets", {}).values():
            for field in (
                "disposition",
                "current_source_relative_path",
                "attempt_outcome",
                "lifecycle",
                "stop_reason",
                "disposition_receipt",
            ):
                ticket.pop(field, None)

    strip(legacy)
    for event in legacy["history"]:
        strip(event["snapshot"])
    resign_forged_history(legacy)
    return legacy


class ForgedLifecycleReplayTests(unittest.TestCase):
    def kernel(self) -> Kernel:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        folder = Path(directory.name)
        (folder / "01.md").write_text(ticket_text("01"))
        return Kernel.new(
            "forged-lifecycle",
            parse_ticket_folder(folder),
            provider="github",
        )

    def kernel_with_two_tickets(self) -> Kernel:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        folder = Path(directory.name)
        (folder / "01.md").write_text(ticket_text("01"))
        (folder / "02.md").write_text(ticket_text("02"))
        return Kernel.new(
            "forged-lifecycle-two",
            parse_ticket_folder(folder),
            provider="github",
        )

    @staticmethod
    def advance(
        kernel: Kernel,
        ticket_id: str,
        fixed: CandidateRef,
        stages: tuple[str, ...],
    ) -> None:
        for stage in stages:
            if stage in {"review", "qa-plan", "qa-execute", "verify"}:
                record_review_handoff(kernel, ticket_id, fixed, stage=stage)
            kernel.record_stage(ticket_id, stage, "pass", fixed)

    @staticmethod
    def capture_event_prefixes(
        documents: dict[str, dict[str, object]],
        kernel: Kernel,
    ) -> None:
        for index, event in enumerate(kernel.ledger["history"]):
            name = event["event"]
            if name in documents:
                continue
            snapshot = json.loads(json.dumps(event["snapshot"]))
            snapshot["history"] = json.loads(
                json.dumps(kernel.ledger["history"][: index + 1])
            )
            documents[name] = snapshot

    def emitted_event_documents(self) -> dict[str, dict[str, object]]:
        documents: dict[str, dict[str, object]] = {}
        fixed = CandidateRef("base-1", "tree-1", "ticket-1", 2)
        adopted = CandidateRef("base-1", "tree-2", "ticket-1", 2)
        invalidated = CandidateRef("base-1", "tree-3", "ticket-1", 2)
        prepared = CandidateRef("base-2", "tree-4", "ticket-1", 2)

        lifecycle = self.kernel()
        lifecycle.activate("01", fixed)
        lifecycle.adopt_implementation_candidate("01", adopted)
        lifecycle.invalidate_for_candidate_drift("01", invalidated)
        self.advance(
            lifecycle,
            "01",
            invalidated,
            (
                "implement",
                "simplify",
                "review",
                "qa-plan",
                "qa-execute",
                "verify",
                "finalize",
            ),
        )
        lifecycle.record_finalization_effect("01", "fixture-effect")
        lifecycle.record_evidence_cache_decision(
            "01",
            key_hash="0" * 64,
            hit=False,
            commands_avoided=0,
            limitations=["fixture limitation"],
            miss_reason="fixture miss",
        )
        lifecycle.record_delivery_metadata("01", "fixture-step", {"value": 1})
        for stale_step in (
            "pr-body-request",
            "pr-body",
            "pr",
            "provider-simulation",
            "result",
        ):
            lifecycle.record_delivery_metadata(
                "01", stale_step, {"value": f"stale-{stale_step}"}
            )
        lifecycle.record_delivery_candidate("01", invalidated)
        lifecycle.prepare_delivery_revalidation("01", prepared)
        self.assertEqual(
            {"fixture-step", "prepared"},
            set(lifecycle.ledger["tickets"]["01"]["delivery"]),
        )
        self.advance(
            lifecycle,
            "01",
            prepared,
            ("review", "qa-plan", "qa-execute", "verify", "finalize"),
        )
        lifecycle.record_pr(
            "01",
            provider="github",
            pr_id="7",
            head_sha="head-1",
            branch="ticket/01",
            base_branch="main",
            base_sha="base-sha",
        )
        lifecycle.update_pr_head("01", expected_old="head-1", new="head-2")
        lifecycle.authorize_merge(
            "01",
            actor="human",
            head_sha="head-2",
            evidence="artifact://approval",
        )
        lifecycle.record_integration("01", expected_head_sha="head-2")
        self.capture_event_prefixes(documents, lifecycle)

        external = self.kernel()
        external.activate("01", fixed)
        self.advance(
            external,
            "01",
            fixed,
            (
                "implement",
                "simplify",
                "review",
                "qa-plan",
                "qa-execute",
                "verify",
                "finalize",
            ),
        )
        external.record_pr(
            "01",
            provider="github",
            pr_id="9",
            head_sha="external-head",
            branch="ticket/01",
            base_branch="main",
            base_sha="base-sha",
        )
        external.record_external_integration(
            "01",
            actor="human",
            head_sha="external-head",
            evidence="artifact://external-approval",
            provider_observation={
                "schema": 1,
                "provider": "github",
                "operation": "get-pr-state",
                "evidence_class": "live",
                "observed": True,
                "pr_id": "9",
                "head_sha": "external-head",
                "state": "merged",
            },
        )
        self.capture_event_prefixes(documents, external)

        quality = self.kernel()
        quality.activate("01", fixed)
        self.advance(quality, "01", fixed, ("implement", "simplify"))
        record_review_handoff(
            quality,
            "01",
            fixed,
            findings=["blocker:test: quality replay fixture"],
        )
        quality.record_stage("01", "review", "fail", fixed)
        self.capture_event_prefixes(documents, quality)

        implementation_failure = self.kernel()
        implementation_failure.activate("01", fixed)
        implementation_failure.record_stage("01", "implement", "fail", fixed)
        self.capture_event_prefixes(documents, implementation_failure)

        gated = self.kernel_with_two_tickets()
        second = CandidateRef("base-1", "tree-2", "ticket-2", 2)
        gated.activate("01", fixed)
        gate_id = gated.open_gate(
            "01",
            "environment",
            scope="ticket",
            reason="fixture gate",
        )
        gated.refresh_gate_reason(gate_id, reason="refreshed fixture gate")
        gated.activate("02", second)
        gated.approve_gate(
            gate_id,
            actor="human",
            evidence="artifact://gate",
        )
        gated.record_stage("02", "implement", "fail", second)
        gated.activate("01", fixed)
        self.capture_event_prefixes(documents, gated)

        reconciliation = self.kernel()
        reconciliation.activate("01", fixed)
        self.advance(
            reconciliation,
            "01",
            fixed,
            (
                "implement",
                "simplify",
                "review",
                "qa-plan",
                "qa-execute",
                "verify",
                "finalize",
            ),
        )
        reconciliation.record_pr(
            "01",
            provider="github",
            pr_id="8",
            head_sha="old-head",
            branch="ticket/01",
            base_branch="parent/00",
            base_sha="parent-head",
        )
        reconciled = CandidateRef("new-base-tree", "new-tree", "ticket-1", 2)
        reconciliation.prepare_reconciliation(
            "01",
            reconciled,
            old_head="old-head",
            new_head="new-head",
            base_branch="main",
            base_sha="new-base-sha",
            base_tree_oid="new-base-tree",
            expected_remote_sha="old-head",
        )
        self.capture_event_prefixes(documents, reconciliation)

        equivalent = self.kernel()
        equivalent.activate("01", fixed)
        self.advance(
            equivalent,
            "01",
            fixed,
            (
                "implement",
                "simplify",
                "review",
                "qa-plan",
                "qa-execute",
                "verify",
                "finalize",
            ),
        )
        equivalent.record_pr(
            "01",
            provider="github",
            pr_id="10",
            head_sha="equivalent-old-head",
            branch="ticket/01",
            base_branch="parent/00",
            base_sha="parent-head",
        )
        equivalent.prepare_reconciliation(
            "01",
            fixed,
            old_head="equivalent-old-head",
            new_head="equivalent-new-head",
            base_branch="main",
            base_sha="merged-parent-head",
            base_tree_oid=fixed.base_tree_oid,
            expected_remote_sha="equivalent-old-head",
        )
        self.capture_event_prefixes(documents, equivalent)

        administrative = self.kernel()
        administrative.pause_run(actor="human", reason="fixture pause")
        administrative.unpause_run(actor="human", reason="fixture resume")
        administrative.activate("01", fixed)
        administrative.record_disposition_transition(
            "01",
            {
                "schema": 1,
                "transition_id": "fixture-hold",
                "ticket_id": "01",
                "from_disposition": "open",
                "to_disposition": "on-hold",
                "actor": "human",
                "reason": "fixture hold",
                "authority_ref": "artifact://fixture-hold",
                "expected_digest": administrative.ledger["tickets"]["01"][
                    "ticket_digest"
                ],
                "authority_gate_id": None,
                "source_relative_path": administrative.ledger["tickets"]["01"][
                    "current_source_relative_path"
                ],
                "destination_relative_path": "hold/01.md",
                "state": "applied",
            },
        )
        self.capture_event_prefixes(documents, administrative)

        cleaned = self.kernel()
        cleaned.abort(actor="human", reason="fixture abort")
        cleaned.record_cleanup(
            worktree="/tmp/fixture",
            worktree_removed=False,
            resume_abandoned=False,
        )
        self.capture_event_prefixes(documents, cleaned)
        return documents

    def assert_forged_last_snapshot_rejected(
        self,
        kernel: Kernel,
        mutation,
    ) -> None:
        document = json.loads(json.dumps(kernel.ledger))
        mutation(document)
        document["history"][-1]["snapshot"] = {
            key: json.loads(json.dumps(value))
            for key, value in document.items()
            if key != "history"
        }
        resign_forged_history(document)
        with self.assertRaises(LedgerError):
            AtomicLedger._validate(document)

    def test_replay_rejects_active_ticket_without_candidate_ref(self) -> None:
        kernel = self.kernel()
        fixed = CandidateRef("base", "tree", "ticket", 2)
        kernel.activate("01", fixed)

        def forge(document: dict[str, object]) -> None:
            document["tickets"]["01"]["candidate_ref"] = None

        self.assert_forged_last_snapshot_rejected(kernel, forge)

    def test_replay_rejects_finalize_without_validated_predecessors(self) -> None:
        kernel = self.kernel()
        fixed = CandidateRef("base", "tree", "ticket", 2)
        kernel.activate("01", fixed)
        for stage in (
            "implement",
            "simplify",
            "review",
            "qa-plan",
            "qa-execute",
            "verify",
        ):
            if stage in {"review", "qa-plan", "qa-execute", "verify"}:
                record_review_handoff(kernel, "01", fixed, stage=stage)
            kernel.record_stage("01", stage, "pass", fixed)

        def forge(document: dict[str, object]) -> None:
            document["tickets"]["01"]["validated_stages"] = []

        self.assert_forged_last_snapshot_rejected(kernel, forge)

    def test_replay_rejects_pending_ticket_with_progress_and_candidate(self) -> None:
        kernel = self.kernel()
        fixed = CandidateRef("base", "tree", "ticket", 2)
        kernel.activate("01", fixed)

        def forge(document: dict[str, object]) -> None:
            document["tickets"]["01"]["state"] = "pending"
            document["tickets"]["01"].pop("resume_pending", None)

        self.assert_forged_last_snapshot_rejected(kernel, forge)

    def test_replay_rejects_forged_integration_from_run_initialization(self) -> None:
        kernel = self.kernel()

        def forge(document: dict[str, object]) -> None:
            ticket = document["tickets"]["01"]
            ticket["state"] = "integrated"
            ticket["preexisting_integrated"] = False
            ticket["pr"] = None
            document["run_state"] = "completed"

        self.assert_forged_last_snapshot_rejected(kernel, forge)

    def test_delivery_recorded_cannot_smuggle_pending_to_verified(self) -> None:
        document = json.loads(json.dumps(self.kernel().ledger))
        ticket = document["tickets"]["01"]
        ticket["state"] = "verified"
        ticket["stage"] = None
        ticket["candidate_ref"] = {
            "base_tree_oid": "base",
            "candidate_tree_oid": "tree",
            "ticket_digest": ticket["ticket_digest"],
            "contract_version": 2,
        }
        ticket["validated_stages"] = [
            "implement",
            "simplify",
            "review",
            "qa-plan",
            "qa-execute",
            "verify",
            "finalize",
        ]
        ticket["delivery"]["forged"] = {"value": "smuggled"}
        document["run_state"] = "waiting"
        snapshot = {
            key: json.loads(json.dumps(value))
            for key, value in document.items()
            if key != "history"
        }
        document["history"].append(
            {
                "sequence": 2,
                "event": "delivery-recorded",
                "ticket_id": "01",
                "details": {"step": "forged"},
                "snapshot": snapshot,
            }
        )
        resign_forged_history(document)

        with self.assertRaises(LedgerError):
            AtomicLedger._validate(document)

    def test_replay_rejects_forged_pr_body_lineage_rebinds(self) -> None:
        kernel = self.kernel()
        ticket_digest = kernel.ledger["tickets"]["01"]["ticket_digest"]
        fixed = CandidateRef("base", "tree", ticket_digest, 2)
        kernel.activate("01", fixed)
        self.advance(
            kernel,
            "01",
            fixed,
            (
                "implement",
                "simplify",
                "review",
                "qa-plan",
                "qa-execute",
                "verify",
                "finalize",
            ),
        )

        def receipt(
            *, schema: int, request: str, head: str, body: str
        ) -> dict[str, object]:
            return {
                "schema": schema,
                "request_hash": request,
                "expected_head_sha": head,
                "body_sha256": body,
                "body_path": f"/artifacts/{body}.md",
                "bundle_sha256": "bundle",
                "bundle_path": "/artifacts/bundle.json",
                "verification_audit_root": "/verification-audit",
            }

        def rebind(
            previous: dict[str, object],
            *,
            request: str,
            head: str,
            body: str,
        ) -> dict[str, object]:
            rebound = receipt(schema=2, request=request, head=head, body=body)
            lineage = copy.deepcopy(previous.get("lineage_rebinds", []))
            lineage.append(
                {
                    "schema": 1,
                    "old_head": previous["expected_head_sha"],
                    "new_head": head,
                    "old_body_sha256": previous["body_sha256"],
                    "new_body_sha256": body,
                    "render_request_hash": request,
                    "old_receipt": copy.deepcopy(previous),
                }
            )
            rebound["lineage_rebinds"] = lineage
            return rebound

        original = receipt(
            schema=1,
            request="request-1",
            head="head-1",
            body="body-1",
        )
        first_rebind = rebind(
            original,
            request="request-2",
            head="head-2",
            body="body-2",
        )
        second_rebind = rebind(
            first_rebind,
            request="request-3",
            head="head-3",
            body="body-3",
        )
        kernel.record_delivery_metadata("01", "pr-body", original)
        kernel.record_delivery_metadata(
            "01",
            "reconcile-pr-body-request",
            {
                "request_hash": "request-2",
                "expected_head_sha": "head-2",
                "reconciled_from_head": "head-1",
            },
        )
        kernel.record_delivery_metadata("01", "pr-body", first_rebind)
        kernel.record_delivery_metadata(
            "01",
            "reconcile-pr-body-request",
            {
                "request_hash": "request-3",
                "expected_head_sha": "head-3",
                "reconciled_from_head": "head-2",
            },
        )
        kernel.record_delivery_metadata("01", "pr-body", second_rebind)
        AtomicLedger._validate(json.loads(json.dumps(kernel.ledger)))

        def forge_old_receipt(record: dict[str, object]) -> None:
            record["lineage_rebinds"][-1]["old_receipt"] = {}

        def forge_prefix(record: dict[str, object]) -> None:
            record["lineage_rebinds"] = [record["lineage_rebinds"][-1]]

        def forge_correlated_current_receipt(record: dict[str, object]) -> None:
            record.update(
                {
                    "request_hash": "forged-request",
                    "expected_head_sha": "forged-head",
                    "body_sha256": "forged-body",
                    "body_path": "/forged/forged-body.md",
                    "bundle_sha256": "forged-bundle",
                    "bundle_path": "/forged/forged-bundle.json",
                    "verification_audit_root": "/forged/verification-audit",
                }
            )
            latest = record["lineage_rebinds"][-1]
            latest["new_head"] = "forged-head"
            latest["new_body_sha256"] = "forged-body"
            latest["render_request_hash"] = "forged-request"

        mutations = {
            "old-receipt": forge_old_receipt,
            "lineage-prefix": forge_prefix,
            "old-head": lambda record: record["lineage_rebinds"][-1].__setitem__(
                "old_head", "forged-old-head"
            ),
            "new-head": lambda record: record["lineage_rebinds"][-1].__setitem__(
                "new_head", "forged-new-head"
            ),
            "old-body": lambda record: record["lineage_rebinds"][-1].__setitem__(
                "old_body_sha256", "forged-old-body"
            ),
            "new-body": lambda record: record["lineage_rebinds"][-1].__setitem__(
                "new_body_sha256", "forged-new-body"
            ),
            "request": lambda record: record["lineage_rebinds"][-1].__setitem__(
                "render_request_hash", "forged-request"
            ),
            "correlated-current-receipt": forge_correlated_current_receipt,
        }
        for variant, mutation in mutations.items():
            document = json.loads(json.dumps(kernel.ledger))
            for snapshot in (document, document["history"][-1]["snapshot"]):
                mutation(snapshot["tickets"]["01"]["delivery"]["pr-body"])
            resign_forged_history(document)
            with self.subTest(variant=variant), self.assertRaises(LedgerError):
                AtomicLedger._validate(document)

    def test_every_emitted_event_has_closed_semantic_replay(self) -> None:
        expected_names = {
            "run-initialized",
            "ticket-resumed",
            "ticket-activated",
            "candidate-adopted",
            "candidate-invalidated",
            "leaf-result-recorded",
            "evidence-cache-decision",
            "stage-passed",
            "quality-failed",
            "ticket-failed",
            "gate-opened",
            "gate-refreshed",
            "gate-passed",
            "effect-applied",
            "delivery-recorded",
            "delivery-candidate-recorded",
            "delivery-revalidation-required",
            "reconciliation-revalidation-required",
            "reconciliation-equivalent",
            "pr-opened",
            "pr-head-updated",
            "merge-authorized",
            "external-merge-integrated",
            "ticket-integrated",
            "ticket-disposition-changed",
            "run-paused",
            "run-unpaused",
            "run-aborted",
            "worktree-cleaned",
        }
        documents = self.emitted_event_documents()
        self.assertEqual(
            expected_names | {"ledger-v3-lifecycle-migrated"},
            set(KNOWN_LEDGER_EVENTS),
        )
        kernel_source = (
            Path(__file__).resolve().parents[1]
            / "scripts"
            / "autopilot"
            / "kernel.py"
        )
        syntax = ast.parse(kernel_source.read_text(encoding="utf-8"))
        emitted_names = {
            call.args[0].value
            for call in ast.walk(syntax)
            if isinstance(call, ast.Call)
            and isinstance(call.func, ast.Attribute)
            and call.func.attr == "_event"
            and call.args
            and isinstance(call.args[0], ast.Constant)
            and isinstance(call.args[0].value, str)
        }
        self.assertEqual(expected_names, emitted_names)
        self.assertEqual(expected_names, set(documents))

        for name, valid in documents.items():
            with self.subTest(name=name, variant="valid"):
                AtomicLedger._validate(json.loads(json.dumps(valid)))
            adversarial = json.loads(json.dumps(valid))
            if name == "run-initialized":
                forged_cleanup = {
                    "recorded": True,
                    "worktree": "/tmp/smuggled",
                    "worktree_removed": True,
                    "resume_abandoned": False,
                    "remote_state_deleted": False,
                }
                adversarial["cleanup"] = forged_cleanup
                adversarial["history"][-1]["snapshot"]["cleanup"] = (
                    forged_cleanup
                )
            else:
                adversarial["repo"] = "/tmp/smuggled-repo"
                adversarial["history"][-1]["snapshot"]["repo"] = (
                    "/tmp/smuggled-repo"
                )
            resign_forged_history(adversarial)
            with self.subTest(name=name, variant="unrelated-mutation"):
                with self.assertRaises(LedgerError):
                    AtomicLedger._validate(adversarial)

    def test_external_integration_event_cannot_smuggle_delivery_metadata(self) -> None:
        document = json.loads(
            json.dumps(
                self.emitted_event_documents()["external-merge-integrated"]
            )
        )
        document["tickets"]["01"]["delivery"]["smuggled"] = {
            "value": "forged"
        }
        document["history"][-1]["snapshot"]["tickets"]["01"]["delivery"][
            "smuggled"
        ] = {"value": "forged"}
        resign_forged_history(document)

        with self.assertRaises(LedgerError):
            AtomicLedger._validate(document)

    def test_unknown_event_name_is_rejected(self) -> None:
        document = json.loads(
            json.dumps(self.emitted_event_documents()["run-initialized"])
        )
        snapshot = {
            key: json.loads(json.dumps(value))
            for key, value in document.items()
            if key != "history"
        }
        document["history"].append(
            {
                "sequence": 2,
                "event": "unknown-event",
                "ticket_id": None,
                "details": {},
                "snapshot": snapshot,
            }
        )
        resign_forged_history(document)

        with self.assertRaises(LedgerError):
            AtomicLedger._validate(document)

    def test_run_scoped_gate_events_replay_without_ticket_owner(self) -> None:
        kernel = self.kernel()
        gate_id = kernel.open_gate(
            None,
            "credentials",
            scope="run",
            reason="fixture run gate",
        )
        kernel.approve_gate(
            gate_id,
            actor="human",
            evidence="artifact://run-gate",
        )

        AtomicLedger._validate(kernel.ledger)


class FakeProviderRunner:
    def __init__(self, *stdout: str):
        self.responses = [CommandResult(value, "", 0) for value in stdout]
        self.commands: list[list[str]] = []

    def run(self, command: list[str], *, cwd: Path) -> CommandResult:
        self.commands.append(command)
        if not self.responses:
            raise AssertionError(f"unexpected command: {command}")
        return self.responses.pop(0)


class ProviderTests(unittest.TestCase):
    def test_live_github_checks_are_exact_head_and_gh_235_compatible(self) -> None:
        runner = FakeProviderRunner(
            json.dumps(
                {
                    "number": 7,
                    "headRefOid": "head-1",
                    "baseRefName": "main",
                    "mergeStateStatus": "BLOCKED",
                    "statusCheckRollup": [
                        {
                            "__typename": "StatusContext",
                            "context": "qa/live",
                            "state": "PENDING",
                        }
                    ],
                }
            ),
            json.dumps(
                [
                    {
                        "type": "required_status_checks",
                        "ruleset_id": 42,
                        "ruleset_source_type": "Repository",
                        "ruleset_source": "org/repo",
                        "parameters": {
                            "required_status_checks": [
                                {"context": "qa/live"}
                            ]
                        },
                    },
                    {
                        "type": "merge_queue",
                        "ruleset_id": 42,
                        "ruleset_source_type": "Repository",
                        "ruleset_source": "org/repo",
                    },
                ]
            ),
        )

        receipt = ProviderExecutor(
            GitHubProvider(),
            cwd=Path("/tmp"),
            mode="live",
            runner=runner,
        ).execute(
            GET_CHECKS_AND_POLICIES,
            pr_id="7",
            expected_head="head-1",
        )

        self.assertEqual("head-1", receipt["head_sha"])
        self.assertEqual("queue", receipt["merge_mode"])
        self.assertEqual(
            {
                "bucket": "pending",
                "name": "qa/live",
                "state": "PENDING",
                "workflow": "",
            },
            receipt["checks_and_policies"][0],
        )
        self.assertEqual(["gh", "pr", "view"], runner.commands[0][:3])
        self.assertEqual(["gh", "api"], runner.commands[1][:2])
        self.assertFalse(
            any(command[:3] == ["gh", "pr", "checks"] for command in runner.commands)
        )

    def test_github_status_rollup_normalizes_pending_and_failed_states(self) -> None:
        for state, bucket in (("IN_PROGRESS", "pending"), ("FAILURE", "fail")):
            with self.subTest(state=state):
                runner = FakeProviderRunner(
                    json.dumps(
                        {
                            "number": 7,
                            "headRefOid": "head-1",
                            "baseRefName": "main",
                            "mergeStateStatus": "BLOCKED",
                            "statusCheckRollup": [
                                {
                                    "__typename": "CheckRun",
                                    "name": "required",
                                    "status": state,
                                    "conclusion": (
                                        None if state == "IN_PROGRESS" else state
                                    ),
                                    "workflowName": "CI",
                                }
                            ],
                        }
                    ),
                    "[]",
                )
                receipt = ProviderExecutor(
                    GitHubProvider(),
                    cwd=Path("/tmp"),
                    mode="live",
                    runner=runner,
                ).execute(
                    GET_CHECKS_AND_POLICIES,
                    pr_id="7",
                    expected_head="head-1",
                )
                self.assertEqual(
                    bucket,
                    receipt["checks_and_policies"][0]["bucket"],
                )

    def test_live_github_executor_mints_receipt_from_readback(self) -> None:
        runner = FakeProviderRunner(
            "[]",
            "https://github.example/pr/7",
            '[{"number":7}]',
            json.dumps(
                {
                    "number": 7,
                    "url": "https://github.example/pr/7",
                    "state": "OPEN",
                    "mergedAt": None,
                    "headRefName": "ticket/01",
                    "headRefOid": "head-1",
                    "baseRefName": "main",
                    "body": "ledger://run/01",
                    "reviewDecision": "",
                    "reviews": [],
                }
            ),
        )
        executor = ProviderExecutor(
            GitHubProvider(),
            cwd=Path("/tmp"),
            mode="live",
            runner=runner,
        )

        receipt = executor.execute(
            CREATE_OR_UPDATE_PR,
            branch="ticket/01",
            base="main",
            head_sha="head-1",
            title="Ticket 01",
            body_artifact="ledger://run/01",
        )

        self.assertEqual("live", receipt["evidence_class"])
        self.assertTrue(receipt["observed"])
        self.assertEqual("7", receipt["pr_id"])
        self.assertEqual("head-1", receipt["head_sha"])
        self.assertEqual("ledger://run/01", receipt["body"])
        self.assertEqual(4, len(runner.commands))
        self.assertEqual(["gh", "pr", "create"], runner.commands[1][:3])

    def test_existing_github_pr_uses_rest_update_and_reads_body_back(self) -> None:
        body = "rendered body"
        runner = FakeProviderRunner(
            '[{"number":7}]',
            "{}",
            json.dumps(
                {
                    "number": 7,
                    "url": "https://github.example/pr/7",
                    "state": "OPEN",
                    "mergedAt": None,
                    "headRefName": "ticket/01",
                    "headRefOid": "head-1",
                    "baseRefName": "main",
                    "body": body,
                    "reviewDecision": "",
                    "reviews": [],
                }
            ),
        )
        executor = ProviderExecutor(
            GitHubProvider(), cwd=Path("/tmp"), mode="live", runner=runner
        )

        receipt = executor.execute(
            CREATE_OR_UPDATE_PR,
            branch="ticket/01",
            base="main",
            head_sha="head-1",
            title="Ticket 01",
            body_artifact=body,
        )

        self.assertEqual(body, receipt["body"])
        self.assertEqual(["gh", "api"], runner.commands[1][:2])
        self.assertIn("PATCH", runner.commands[1])
        self.assertFalse(
            any(command[:3] == ["gh", "pr", "edit"] for command in runner.commands)
        )

    def test_github_retarget_publishes_base_and_body_in_one_rest_patch(self) -> None:
        body = "reconciled body"
        runner = FakeProviderRunner(
            "{}",
            json.dumps(
                {
                    "number": 7,
                    "url": "https://github.example/pr/7",
                    "state": "OPEN",
                    "mergedAt": None,
                    "headRefName": "ticket/02",
                    "headRefOid": "head-2",
                    "baseRefName": "main",
                    "body": body,
                    "reviewDecision": "",
                    "reviews": [],
                }
            ),
        )
        executor = ProviderExecutor(
            GitHubProvider(), cwd=Path("/tmp"), mode="live", runner=runner
        )

        receipt = executor.execute(
            RETARGET_PR,
            pr_id="7",
            base="main",
            body_artifact=body,
        )

        self.assertEqual("main", receipt["base"])
        self.assertEqual(body, receipt["body"])
        mutation = runner.commands[0]
        self.assertEqual(
            ["gh", "api", "repos/{owner}/{repo}/pulls/7"], mutation[:3]
        )
        self.assertIn("PATCH", mutation)
        self.assertIn("base=main", mutation)
        self.assertIn(f"body={body}", mutation)
        self.assertFalse(
            any(command[:3] == ["gh", "pr", "edit"] for command in runner.commands)
        )

    def test_simulated_executor_never_invokes_runner_or_claims_observation(self) -> None:
        runner = FakeProviderRunner()
        executor = ProviderExecutor(
            GitHubProvider(),
            cwd=Path("/tmp"),
            mode="simulated",
            runner=runner,
        )

        receipt = executor.execute(GET_PR_STATE, pr_id="7")

        self.assertEqual("simulated", receipt["evidence_class"])
        self.assertFalse(receipt["observed"])
        self.assertEqual([], runner.commands)
        self.assertNotIn("state", receipt)

    def test_detects_github_and_azure_and_negotiates_required_capabilities(self) -> None:
        github = detect_provider("git@github.com:org/repo.git")
        azure = detect_provider("https://dev.azure.com/org/project/_git/repo")
        self.assertIsInstance(github, GitHubProvider)
        self.assertIsInstance(azure, AzureDevOpsProvider)
        github.negotiate(
            {
                CREATE_OR_UPDATE_PR,
                RETARGET_PR,
                GET_CHECKS_AND_POLICIES,
                GET_APPROVALS,
                MERGE_WITH_EXPECTED_HEAD,
            }
        )
        azure.negotiate(
            {
                CREATE_OR_UPDATE_PR,
                GET_PR_STATE,
                GET_CHECKS_AND_POLICIES,
                GET_APPROVALS,
            }
        )
        with self.assertRaises(ProviderError):
            azure.negotiate({RETARGET_PR})
        with self.assertRaises(ProviderError):
            azure.negotiate({MERGE_WITH_EXPECTED_HEAD})
        with self.assertRaises(ProviderError):
            detect_provider("ssh://example.invalid/repo")

    def test_merge_command_requires_authorization_bound_to_current_head(self) -> None:
        provider = GitHubProvider()
        authorization = MergeAuthorization(
            provider="github",
            pr_id="7",
            head_sha="head-1",
            actor="human",
            evidence="artifact://approval",
        )
        command = provider.merge_command("7", "head-1", authorization)
        self.assertIn("--match-head-commit", command)
        self.assertIn("--merge", command)
        with self.assertRaises(ProviderError):
            provider.merge_command("7", "head-2", authorization)
        azure_authorization = MergeAuthorization(
            provider="azure-devops",
            pr_id="7",
            head_sha="head-1",
            actor="human",
            evidence="artifact://approval",
        )
        with self.assertRaises(ProviderError):
            AzureDevOpsProvider().merge_command("7", "head-1", azure_authorization)

    def test_live_merge_executor_returns_intent_bound_mutation_receipt(self) -> None:
        runner = FakeProviderRunner(
            json.dumps(
                {
                    "id": "PR_7",
                    "headRefOid": "head-1",
                    "baseRefName": "main",
                }
            ),
            "[]",
            "",
        )
        executor = ProviderExecutor(
            GitHubProvider(), cwd=Path("/tmp"), mode="live", runner=runner
        )
        authorization = MergeAuthorization(
            provider="github",
            pr_id="7",
            head_sha="head-1",
            actor="human",
            evidence="artifact://approval",
        )

        receipt = executor.execute(
            MERGE_WITH_EXPECTED_HEAD,
            pr_id="7",
            expected_head="head-1",
            intent_key="intent-1",
            authorization=authorization,
        )

        self.assertEqual("live", receipt["evidence_class"])
        self.assertEqual("intent-1", receipt["intent_key"])
        self.assertEqual("head-1", receipt["head_sha"])
        self.assertEqual(["gh", "pr", "merge"], runner.commands[2][:3])
        self.assertIn("--match-head-commit", runner.commands[2])
        self.assertIn("--merge", runner.commands[2])

    def test_live_github_queue_merge_is_atomically_head_pinned(self) -> None:
        queue_entry = {
            "id": "MQE_1",
            "position": 1,
            "state": "QUEUED",
            "enqueuedAt": "2026-08-06T09:14:16Z",
        }
        runner = FakeProviderRunner(
            json.dumps(
                {
                    "id": "PR_7",
                    "headRefOid": "head-1",
                    "baseRefName": "main",
                }
            ),
            json.dumps([{"type": "merge_queue", "ruleset_id": 42}]),
            json.dumps(
                {
                    "data": {
                        "node": {
                            "headRefOid": "head-1",
                            "mergeQueueEntry": None,
                        }
                    }
                }
            ),
            json.dumps(
                {
                    "data": {
                        "enqueuePullRequest": {
                            "clientMutationId": "intent-1",
                            "mergeQueueEntry": queue_entry,
                        }
                    }
                }
            ),
            json.dumps(
                {
                    "data": {
                        "node": {
                            "headRefOid": "head-1",
                            "mergeQueueEntry": queue_entry,
                        }
                    }
                }
            ),
        )
        authorization = MergeAuthorization(
            provider="github",
            pr_id="7",
            head_sha="head-1",
            actor="human",
            evidence="artifact://approval",
        )

        receipt = ProviderExecutor(
            GitHubProvider(), cwd=Path("/tmp"), mode="live", runner=runner
        ).execute(
            MERGE_WITH_EXPECTED_HEAD,
            pr_id="7",
            expected_head="head-1",
            intent_key="intent-1",
            authorization=authorization,
        )

        self.assertEqual("queue", receipt["merge_mode"])
        self.assertEqual(queue_entry, receipt["queue_entry"])
        mutations = [
            command
            for command in runner.commands
            if command[:3] == ["gh", "api", "graphql"]
            and any("enqueuePullRequest" in part for part in command)
        ]
        self.assertEqual(1, len(mutations))
        self.assertIn("expectedHeadOid=head-1", mutations[0])
        self.assertFalse(
            any(command[:3] == ["gh", "pr", "merge"] for command in runner.commands)
        )
        self.assertFalse(any("--admin" in command for command in runner.commands))

    def test_live_github_queue_recovers_a_lost_mutation_response_once(self) -> None:
        queue_entry = {
            "id": "MQE_1",
            "position": 1,
            "state": "AWAITING_CHECKS",
            "enqueuedAt": "2026-08-06T09:14:16Z",
        }
        runner = FakeProviderRunner()
        runner.responses = [
            CommandResult(
                json.dumps(
                    {
                        "id": "PR_7",
                        "headRefOid": "head-1",
                        "baseRefName": "main",
                    }
                ),
                "",
                0,
            ),
            CommandResult(json.dumps([{"type": "merge_queue"}]), "", 0),
            CommandResult(
                json.dumps(
                    {
                        "data": {
                            "node": {
                                "headRefOid": "head-1",
                                "mergeQueueEntry": None,
                            }
                        }
                    }
                ),
                "",
                0,
            ),
            CommandResult("", "provider response was lost", 1),
            CommandResult(
                json.dumps(
                    {
                        "data": {
                            "node": {
                                "headRefOid": "head-1",
                                "mergeQueueEntry": queue_entry,
                            }
                        }
                    }
                ),
                "",
                0,
            ),
        ]
        authorization = MergeAuthorization(
            provider="github",
            pr_id="7",
            head_sha="head-1",
            actor="human",
            evidence="artifact://approval",
        )

        receipt = ProviderExecutor(
            GitHubProvider(), cwd=Path("/tmp"), mode="live", runner=runner
        ).execute(
            MERGE_WITH_EXPECTED_HEAD,
            pr_id="7",
            expected_head="head-1",
            intent_key="intent-1",
            authorization=authorization,
        )

        self.assertEqual(queue_entry, receipt["queue_entry"])
        self.assertTrue(receipt["recovered_after_error"])
        mutations = [
            command
            for command in runner.commands
            if command[:3] == ["gh", "api", "graphql"]
            and any("enqueuePullRequest" in part for part in command)
        ]
        self.assertEqual(1, len(mutations))

    def test_live_github_queue_recovers_a_zero_exit_malformed_response_once(self) -> None:
        queue_entry = {
            "id": "MQE_1",
            "position": 1,
            "state": "AWAITING_CHECKS",
            "enqueuedAt": "2026-08-06T09:14:16Z",
        }
        runner = FakeProviderRunner()
        runner.responses = [
            CommandResult(
                json.dumps(
                    {
                        "id": "PR_7",
                        "headRefOid": "head-1",
                        "baseRefName": "main",
                    }
                ),
                "",
                0,
            ),
            CommandResult(json.dumps([{"type": "merge_queue"}]), "", 0),
            CommandResult(
                json.dumps(
                    {
                        "data": {
                            "node": {
                                "headRefOid": "head-1",
                                "mergeQueueEntry": None,
                            }
                        }
                    }
                ),
                "",
                0,
            ),
            CommandResult("{truncated", "", 0),
            CommandResult(
                json.dumps(
                    {
                        "data": {
                            "node": {
                                "headRefOid": "head-1",
                                "mergeQueueEntry": queue_entry,
                            }
                        }
                    }
                ),
                "",
                0,
            ),
        ]
        authorization = MergeAuthorization(
            provider="github",
            pr_id="7",
            head_sha="head-1",
            actor="human",
            evidence="artifact://approval",
        )

        receipt = ProviderExecutor(
            GitHubProvider(), cwd=Path("/tmp"), mode="live", runner=runner
        ).execute(
            MERGE_WITH_EXPECTED_HEAD,
            pr_id="7",
            expected_head="head-1",
            intent_key="intent-1",
            authorization=authorization,
        )

        self.assertEqual(queue_entry, receipt["queue_entry"])
        self.assertTrue(receipt["recovered_after_error"])
        mutations = [
            command
            for command in runner.commands
            if command[:3] == ["gh", "api", "graphql"]
            and any("enqueuePullRequest" in part for part in command)
        ]
        self.assertEqual(1, len(mutations))

    def test_provider_operations_are_normalized_and_capability_checked(self) -> None:
        provider = GitHubProvider()
        operation_names = {
            provider.operation(
                CREATE_OR_UPDATE_PR, head="ticket/01", base="main"
            )["operation"],
            provider.operation(GET_PR_STATE, pr_id="7")["operation"],
            provider.operation(GET_CHECKS_AND_POLICIES, pr_id="7")[
                "operation"
            ],
            provider.operation(GET_APPROVALS, pr_id="7")["operation"],
            provider.operation(RETARGET_PR, pr_id="7", base="main")[
                "operation"
            ],
            provider.operation(
                MERGE_WITH_EXPECTED_HEAD,
                pr_id="7",
                expected_head="sha",
            )["operation"],
        }
        self.assertEqual(
            {
                CREATE_OR_UPDATE_PR,
                GET_PR_STATE,
                GET_CHECKS_AND_POLICIES,
                GET_APPROVALS,
                RETARGET_PR,
                MERGE_WITH_EXPECTED_HEAD,
            },
            operation_names,
        )
        with self.assertRaises(ProviderError):
            AzureDevOpsProvider().operation(
                MERGE_WITH_EXPECTED_HEAD, pr_id="7", expected_head="sha"
            )

    def test_reconcile_commands_use_force_with_lease(self) -> None:
        provider = GitHubProvider()
        commands = provider.reconciliation_commands(
            branch="ticket/02",
            parent_branch="ticket/01",
            base_branch="main",
            expected_remote_sha="old-head",
        )
        flattened = [" ".join(command) for command in commands]
        self.assertTrue(any("rebase --onto main ticket/01 ticket/02" in item for item in flattened))
        self.assertTrue(
            any(
                "--force-with-lease=refs/heads/ticket/02:old-head" in item
                for item in flattened
            )
        )
        self.assertFalse(any("--force " in item for item in flattened))
        with self.assertRaises(ProviderError):
            AzureDevOpsProvider().retarget_command("42", "main")

    def test_delivery_plan_stacks_single_parent_and_gates_multi_parent_join(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "01.md").write_text(ticket_text("01"))
            (folder / "02.md").write_text(ticket_text("02", ("01",)))
            (folder / "03.md").write_text(ticket_text("03", ("01", "02")))
            kernel = Kernel.new("delivery", parse_ticket_folder(folder))
            kernel.ledger["tickets"]["01"]["state"] = "pr-open"
            kernel.ledger["tickets"]["01"]["pr"] = {
                "branch": "ticket-autopilot/delivery/01",
                "pr_id": "1",
                "head_sha": "sha-1",
                "provider": "github",
            }
            plan = build_delivery_plan(
                GitHubProvider(),
                kernel.ledger,
                "02",
                default_base="main",
                title="Ticket 02",
                body_artifact="artifact://body",
            )
            self.assertEqual("ticket-autopilot/delivery/01", plan.base_branch)
            self.assertEqual("01", plan.stacked_on)
            with self.assertRaises(ProviderError):
                build_delivery_plan(
                    GitHubProvider(),
                    kernel.ledger,
                    "03",
                    default_base="main",
                    title="Ticket 03",
                    body_artifact="artifact://body",
                )


if __name__ == "__main__":
    unittest.main()
