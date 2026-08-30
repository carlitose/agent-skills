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
from autopilot.history_codec import decode_history
from autopilot.docs_only_contract import (
    APPROVED_SCOPE,
    CHECKPOINT_PHASES,
    RECEIPT_LIMITATIONS,
    sha256_document,
)
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
from autopilot.terminal_integration import (
    TerminalIntegrationError,
    build_terminal_integration_proof,
    canonical_digest,
    terminal_branch,
    validate_terminal_integration_proof,
)
from autopilot.ledger import (
    AtomicLedger,
    LedgerError,
    _pr_body_rebind_is_closed,
    completion_projection_grant_entries,
    completion_projection_grant_entry,
)
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


def _terminal_proof(
    kernel: Kernel,
    ticket_id: str,
    observation: dict[str, object],
    *,
    provenance: str,
) -> dict[str, object]:
    ticket = kernel.ledger["tickets"][ticket_id]
    lineage = ticket["delivery_lineage"]
    observation.setdefault("base", lineage["base_branch"])
    observation.setdefault("merge_commit_sha", "c" * 40)
    return {
        "schema": 1,
        "repository_identity": kernel.ledger.get("repo"),
        "provider": kernel.ledger.get("provider"),
        "pr_id": ticket["pr"]["pr_id"],
        "head_sha": ticket["pr"]["head_sha"],
        "pr_base": observation["base"],
        "terminal_branch": terminal_branch(kernel.ledger, ticket_id),
        "terminal_sha": "a" * 40,
        "terminal_tree_oid": "b" * 40,
        "merge_commit_sha": observation["merge_commit_sha"],
        "reachable_kind": "merge-commit",
        "reachable_sha": observation["merge_commit_sha"],
        "provider_observation_digest": canonical_digest(observation),
        "delivery_lineage_digest": canonical_digest(lineage),
        "provenance": provenance,
    }


def _record_test_integration(
    kernel: Kernel, ticket_id: str, *, expected_head_sha: str
) -> None:
    ticket = kernel.ledger["tickets"][ticket_id]
    observation: dict[str, object] = {
        "schema": 1,
        "provider": kernel.ledger["provider"],
        "operation": "get-pr-state",
        "evidence_class": "live",
        "observed": True,
        "pr_id": ticket["pr"]["pr_id"],
        "head_sha": expected_head_sha,
        "state": "merged",
    }
    proof = _terminal_proof(
        kernel,
        ticket_id,
        observation,
        provenance="runner-merge",
    )
    kernel.record_delivery_metadata(ticket_id, "integration", observation)
    kernel.record_integration(
        ticket_id,
        expected_head_sha=expected_head_sha,
        terminal_proof=proof,
    )


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

    def test_autonomous_merge_accepts_precompleted_dependency_without_lineage(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            done = folder / "done"
            done.mkdir()
            (done / "01.md").write_text(ticket_text("01"))
            (folder / "02.md").write_text(ticket_text("02", ("01",)))

            kernel = Kernel.new(
                "existing-done-autonomous",
                parse_ticket_folder(folder),
                provider="github",
                repo=tmp,
                snapshot_manifest_digest="a" * 64,
                merge_policy="autonomous",
                merge_actor="operator",
                merge_evidence="artifact://grant",
            )
            child = kernel.ledger["tickets"]["02"]
            child["state"] = "pr-open"
            child["pr"] = {"pr_id": "2"}
            child["delivery_lineage"] = {"base_branch": "main"}

            self.assertTrue(kernel.autonomous_merge_dependencies_ready("02"))
            self.assertEqual("02", kernel.pending_autonomous_merge_id())

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

    def test_existing_manual_run_grant_is_bound_append_only_and_idempotent(
        self,
    ) -> None:
        kernel = Kernel.new(
            "existing-manual-grant",
            parse_ticket_folder(FIXTURES / "happy"),
            provider="github",
            repo="/repo",
            snapshot_manifest_digest="a" * 64,
        )
        history_before = len(kernel.ledger["history"])

        grant, replayed = kernel.grant_autonomous_merge(
            actor="operator",
            evidence="artifact://existing-run-grant",
        )

        self.assertFalse(replayed)
        self.assertEqual("autonomous", kernel.ledger["merge_policy"])
        self.assertEqual(grant, kernel.ledger["autonomous_merge_grant"])
        self.assertEqual(grant, kernel.report()["merge_grant"])
        self.assertEqual(history_before + 1, len(kernel.ledger["history"]))
        self.assertEqual(
            "autonomous-merge-granted",
            kernel.ledger["history"][-1]["event"],
        )
        self.assertEqual(
            {"grant": grant}, kernel.ledger["history"][-1]["details"]
        )
        AtomicLedger._validate(json.loads(json.dumps(kernel.ledger)))

        stable = json.loads(json.dumps(kernel.ledger))
        replay_grant, replayed = kernel.grant_autonomous_merge(
            actor="operator",
            evidence="artifact://existing-run-grant",
        )
        self.assertTrue(replayed)
        self.assertEqual(grant, replay_grant)
        self.assertEqual(stable, kernel.ledger)

        with self.assertRaisesRegex(
            TransitionError, "autonomous merge grant is immutable"
        ):
            kernel.grant_autonomous_merge(
                actor="another-operator",
                evidence="artifact://another-grant",
            )
        self.assertEqual(stable, kernel.ledger)

    def test_existing_run_grant_rejects_missing_authority_terminal_and_inflight_merge(
        self,
    ) -> None:
        graph = parse_ticket_folder(FIXTURES / "happy")
        missing = Kernel.new(
            "missing-authority",
            graph,
            provider="github",
            repo="/repo",
        )
        missing_before = json.loads(json.dumps(missing.ledger))
        with self.assertRaisesRegex(TransitionError, "actor and durable evidence"):
            missing.grant_autonomous_merge(
                actor=" ", evidence="artifact://grant"
            )
        self.assertEqual(missing_before, missing.ledger)

        terminal = Kernel.new(
            "terminal-grant",
            graph,
            provider="github",
            repo="/repo",
        )
        terminal.abort(actor="operator", reason="stop")
        terminal_before = json.loads(json.dumps(terminal.ledger))
        with self.assertRaisesRegex(TransitionError, "non-terminal run"):
            terminal.grant_autonomous_merge(
                actor="operator", evidence="artifact://grant"
            )
        self.assertEqual(terminal_before, terminal.ledger)

        inflight = Kernel.new(
            "inflight-grant",
            graph,
            provider="github",
            repo="/repo",
        )
        inflight.ledger["tickets"]["01"]["delivery"]["merge-progress"] = {
            "status": "running"
        }
        inflight_before = json.loads(json.dumps(inflight.ledger))
        with self.assertRaisesRegex(
            TransitionError, "unresolved provider merge critical path"
        ):
            inflight.grant_autonomous_merge(
                actor="operator", evidence="artifact://grant"
            )
        self.assertEqual(inflight_before, inflight.ledger)


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
        self.assertIn("snapshot", kernel.ledger["history"][0])
        self.assertTrue(
            all(
                "snapshot_delta" in event
                for event in kernel.ledger["history"][1:]
            )
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
        _record_test_integration(kernel, "01", expected_head_sha="sha-1")
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
        external_proof = _terminal_proof(
            kernel,
            "01",
            observation,
            provenance="external-readback",
        )
        kernel.ledger["tickets"]["01"]["pr"]["provider"] = "azure-devops"
        wrong_provider = json.loads(json.dumps(kernel.ledger))
        with self.assertRaises(TransitionError):
            kernel.record_external_integration(
                "01",
                actor="reviewer",
                head_sha="sha-1",
                evidence="artifact://approval",
                provider_observation=observation,
                terminal_proof=external_proof,
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
                    terminal_proof=external_proof,
                )
            self.assertEqual(before, kernel.ledger)
        with self.assertRaises(TransitionError):
            kernel.record_external_integration(
                "01",
                actor="reviewer",
                head_sha="sha-1",
                evidence="",
                provider_observation=observation,
                terminal_proof=external_proof,
            )
        self.assertEqual(before, kernel.ledger)

        receipt, replayed = kernel.record_external_integration(
            "01",
            actor="reviewer",
            head_sha="sha-1",
            evidence="artifact://approval",
            provider_observation=observation,
            terminal_proof=external_proof,
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
            terminal_proof=external_proof,
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
            kernel.record_integration(
                "01", expected_head_sha="sha-2", terminal_proof={}
            )

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
            _record_test_integration(
                kernel, "01", expected_head_sha="head"
            )
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
            history = decode_history(kernel.ledger["history"])
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

    def test_done_move_repoints_the_linking_map_in_the_same_staged_state(self) -> None:
        """The flow fix: the map that links the ticket is repointed and staged with the move.

        Observed before the fix, twice: LW-12 repaired seven stale map links and left its own
        for LW-13, which repaired that one and left its own. The mover settling the map in the
        same staged state is the only shape where the drift never accumulates.
        """

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
            folder = repo / "docs" / "tickets" / "family"
            folder.mkdir(parents=True)
            (folder / "01.md").write_text(ticket_text("01"))
            specs = repo / "docs" / "specs"
            specs.mkdir()
            page = specs / "map.md"
            page.write_text(
                "# Map\n\n### Children\n- [the slice](../tickets/family/01.md)\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-m", "ticket and map"], cwd=repo, check=True)
            graph = parse_ticket_folder(folder)
            kernel = Kernel.new(
                "repoint", graph, worktree=str(repo), repo=str(repo)
            )
            store = AtomicLedger(repo / ".git" / "ticket-autopilot" / "ledger.json")
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

            rewritten = page.read_text(encoding="utf-8")
            self.assertIn("(../tickets/family/done/01.md)", rewritten)
            self.assertNotIn("(../tickets/family/01.md)", rewritten)
            status = subprocess.run(
                ["git", "status", "--porcelain=v1"],
                cwd=repo,
                text=True,
                capture_output=True,
                check=True,
            ).stdout
            self.assertIn("docs/specs/map.md", status, "the repoint must be staged")
            self.assertNotIn(
                " docs/specs/map.md", status.splitlines()[0][:1],
                "staged, not merely modified",
            )
            # The moved ticket's own bytes are untouched: the digest still matches.
            done_text = (folder / "done" / "01.md").read_text(encoding="utf-8")
            self.assertEqual(ticket_text("01"), done_text)
            # Replay: nothing left to repoint, nothing changed.
            self.assertFalse(finalize_done(store, kernel, "01"))
            self.assertEqual(rewritten, page.read_text(encoding="utf-8"))

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
    legacy["history"] = decode_history(legacy["history"])

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
    def kernel(self, *, source_mode: str = "tracked") -> Kernel:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        folder = Path(directory.name)
        (folder / "01.md").write_text(ticket_text("01"))
        return Kernel.new(
            "forged-lifecycle",
            parse_ticket_folder(folder),
            provider="github",
            repo=str(folder.parent.resolve()) if source_mode == "ignored" else "/repo",
            source_mode=source_mode,
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
            repo="/repo",
        )

    def test_normal_candidate_lifecycle_does_not_materialize_docs_only_state(
        self,
    ) -> None:
        kernel = self.kernel()
        ticket = kernel.ledger["tickets"]["01"]
        self.assertNotIn("docs_only", ticket)
        initial = CandidateRef("base", "tree-1", ticket["ticket_digest"], 2)
        adopted = CandidateRef("base", "tree-2", ticket["ticket_digest"], 2)
        invalidated = CandidateRef("base", "tree-3", ticket["ticket_digest"], 2)

        kernel.activate("01", initial)
        kernel.adopt_implementation_candidate("01", adopted)
        kernel.invalidate_for_candidate_drift("01", invalidated)

        self.assertNotIn("docs_only", kernel.ledger["tickets"]["01"])
        for event in decode_history(kernel.ledger["history"]):
            self.assertNotIn(
                "docs_only", event["snapshot"]["tickets"]["01"]
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
        history = decode_history(kernel.ledger["history"])
        for index, event in enumerate(history):
            name = event["event"]
            if name in documents:
                continue
            snapshot = json.loads(json.dumps(event["snapshot"]))
            snapshot["history"] = json.loads(
                json.dumps(history[: index + 1])
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
        _record_test_integration(
            lifecycle, "01", expected_head_sha="head-2"
        )
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
        external_observation: dict[str, object] = {
            "schema": 1,
            "provider": "github",
            "operation": "get-pr-state",
            "evidence_class": "live",
            "observed": True,
            "pr_id": "9",
            "head_sha": "external-head",
            "state": "merged",
        }
        external_proof = _terminal_proof(
            external,
            "01",
            external_observation,
            provenance="external-readback",
        )
        external.record_external_integration(
            "01",
            actor="human",
            head_sha="external-head",
            evidence="artifact://external-approval",
            provider_observation=external_observation,
            terminal_proof=external_proof,
        )
        self.capture_event_prefixes(documents, external)

        projection = self.kernel(source_mode="ignored")
        projection_candidate = CandidateRef(
            "projection-base",
            "projection-tree",
            projection.ledger["tickets"]["01"]["ticket_digest"],
            2,
        )
        projection.activate("01", projection_candidate)
        projection_destination = (
            Path(projection.ledger["ticket_folder"])
            .resolve()
            .relative_to(Path(projection.ledger["repo"]).resolve())
            .joinpath("done", "01.md")
            .as_posix()
        )
        projection_gate = projection.open_gate(
            "01",
            "source-mode-drift",
            scope="ticket",
            reason="fixture completion projection needs authority",
            details={
                "schema": 1,
                "ticket_id": "01",
                "snapshot_classification": "ignored",
                "observed_classification": "tracked",
                "base_classification": "ignored",
                "boundary": "git:symbolic-ref",
                "source_path": projection_destination,
                "recovery": "fixture recovery",
            },
        )
        projection.grant_completion_projection(
            "01",
            candidate=projection_candidate,
            destination_relative_path=projection_destination,
            actor="fixture-actor",
            evidence="artifact://fixture-completion-projection",
        )
        self.assertEqual(
            projection_gate,
            projection.resolve_completion_projection_gate("01"),
        )
        self.capture_event_prefixes(documents, projection)

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

        docs_only = self.kernel()
        docs_candidate = CandidateRef(
            fixed.base_tree_oid,
            fixed.candidate_tree_oid,
            docs_only.ledger["tickets"]["01"]["ticket_digest"],
            fixed.contract_version,
        )
        docs_only.activate("01", docs_candidate)
        docs_handoff = {
            "schema": 3,
            "complete": True,
            "candidate_ref": {
                "base_tree_oid": docs_candidate.base_tree_oid,
                "candidate_tree_oid": docs_candidate.candidate_tree_oid,
                "ticket_digest": docs_candidate.ticket_digest,
                "contract_version": docs_candidate.contract_version,
            },
            "stage": "verify",
            "phase_contract": list(LEAF_PHASE_CONTRACTS["verify"]),
            "scope": {
                "files_expected": ["docs/guide.md"],
                "files_inspected": ["docs/guide.md"],
                "files_remaining": [],
            },
            "phases_remaining": [],
            "commands_run": ["deterministic-docs-checks"],
            "findings": [],
            "progress_phase": "handoff-ready",
            "stop_reason": None,
            "quality": {
                "schema": 1,
                "causal_scope": ["documentation implementation"],
                "evidence": [
                    {
                        "id": "docs-only-evidence",
                        "artifact": "docs-only.json",
                        "sha256": "a" * 64,
                        "result": "pass",
                        "candidate_ref": {
                            "base_tree_oid": docs_candidate.base_tree_oid,
                            "candidate_tree_oid": docs_candidate.candidate_tree_oid,
                            "ticket_digest": docs_candidate.ticket_digest,
                            "contract_version": docs_candidate.contract_version,
                        },
                    }
                ],
                "limitations": ["implementation-only"],
            },
        }
        docs_request = {
            "contract_version": 1,
            "ticket_envelope": {
                "ticket_schema": 1,
                "ticket_id": "01",
                "execution_mode": "AFK",
                "blocked_by": [],
            },
            "ticket_digest": docs_candidate.ticket_digest,
            "source_relative_path": "01.md",
            "candidate_ref": {
                "base_tree_oid": docs_candidate.base_tree_oid,
                "candidate_tree_oid": docs_candidate.candidate_tree_oid,
                "ticket_digest": docs_candidate.ticket_digest,
                "contract_version": docs_candidate.contract_version,
            },
            "expected_changed_paths": ["docs/guide.md"],
            "approved_documentation_scope": APPROVED_SCOPE,
        }
        docs_only.complete_docs_only_candidate(
            "01",
            docs_candidate,
            receipt={
                "contract_version": 1,
                "status": "eligible",
                "request": docs_request,
                "request_sha256": sha256_document(docs_request),
                "candidate_ref": {
                    "base_tree_oid": docs_candidate.base_tree_oid,
                    "candidate_tree_oid": docs_candidate.candidate_tree_oid,
                    "ticket_digest": docs_candidate.ticket_digest,
                    "contract_version": docs_candidate.contract_version,
                },
                "changed_paths": ["docs/guide.md"],
                "checks": [
                    {"id": "patch-integrity", "result": "pass"},
                    {"id": "path-and-file-kind-policy", "result": "pass"},
                    {"id": "markdown-utf8", "result": "pass"},
                    {"id": "artifact-graph", "result": "pass"},
                    {"id": "documentation-links", "result": "pass"},
                ],
                "evidence": {
                    # Absolute on every platform. The contract requires an absolute path,
                    # and "/evidence/..." is not absolute on Windows, where an absolute
                    # path needs a drive — so this valid fixture was rejected there.
                    "artifact": str(Path("/evidence/docs-only.json").absolute()),
                    "sha256": "a" * 64,
                },
                "leaf_interactions_avoided": 4,
                "limitations": list(RECEIPT_LIMITATIONS),
                "checkpoint": {
                    "input_hash": "c" * 64,
                    "artifact_hashes": {
                        phase: "d" * 64 for phase in CHECKPOINT_PHASES
                    },
                    "phases_complete": list(CHECKPOINT_PHASES),
                },
            },
            verification_handoff=docs_handoff,
        )
        self.capture_event_prefixes(documents, docs_only)

        docs_rejected = self.kernel()
        docs_rejected.activate("01", fixed)
        docs_rejected.record_docs_only_rejection(
            "01", reason="mixed candidate"
        )
        self.capture_event_prefixes(documents, docs_rejected)

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
        corrected_reconciliation = CandidateRef(
            "new-base-tree", "corrected-tree", "ticket-1", 2
        )
        reconciliation.invalidate_for_candidate_drift(
            "01", corrected_reconciliation
        )
        self.advance(
            reconciliation,
            "01",
            corrected_reconciliation,
            PIPELINE,
        )
        stale_reconcile_render = {
            "schema": 1,
            "request_hash": "stale-request",
        }
        reconciliation.record_delivery_metadata(
            "01", "reconcile-pr-body-request", stale_reconcile_render
        )
        reconciliation.seal_revalidated_reconciliation_candidate(
            "01",
            corrected_reconciliation,
            expected_old_local_head="new-head",
            new_local_head="corrected-head",
        )
        sealed_ticket = reconciliation.ledger["tickets"]["01"]
        self.assertEqual(
            sealed_ticket["candidate_ref"],
            sealed_ticket["delivery_candidate_ref"],
        )
        self.assertEqual(
            "corrected-head",
            sealed_ticket["delivery"]["reconcile-prepare"]["new_head"],
        )
        self.assertEqual(
            {"reconcile-pr-body-request": stale_reconcile_render},
            sealed_ticket["delivery"]["reconcile-revalidation-history"][-1][
                "render_receipts"
            ],
        )
        self.assertNotIn(
            "reconcile-pr-body-request", sealed_ticket["delivery"]
        )
        self.capture_event_prefixes(documents, reconciliation)
        late_drift = CandidateRef(
            "new-base-tree", "late-drift-tree", "ticket-1", 2
        )
        reconciliation.prepare_reconciliation_delivery_revalidation(
            "01", late_drift
        )
        self.capture_event_prefixes(documents, reconciliation)

        refresh = self.kernel()
        refresh.activate("01", fixed)
        self.advance(
            refresh,
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
        refresh.record_pr(
            "01",
            provider="github",
            pr_id="11",
            head_sha="refresh-old-head",
            branch="ticket/01",
            base_branch="parent/00",
            base_sha="parent-head",
        )
        old_intent = {
            "schema": 1,
            "branch": "ticket/01",
            "old_head": "refresh-old-head",
            "parent_branch": "parent/00",
            "parent_head": "parent-head",
            "expected_remote_sha": "refresh-old-head",
            "target_base": {
                "branch": "main",
                "ref": "refs/remotes/origin/main",
                "sha": "refresh-base-sha-1",
                "tree_oid": "refresh-base-tree-1",
            },
        }
        refresh.record_delivery_metadata(
            "01", "reconcile-intent", old_intent
        )
        refresh_candidate = CandidateRef(
            "refresh-base-tree-1", "refresh-tree-1", "ticket-1", 2
        )
        refresh.prepare_reconciliation(
            "01",
            refresh_candidate,
            old_head="refresh-old-head",
            new_head="refresh-local-head-1",
            base_branch="main",
            base_sha="refresh-base-sha-1",
            base_tree_oid="refresh-base-tree-1",
            expected_remote_sha="refresh-old-head",
        )
        self.advance(
            refresh,
            "01",
            refresh_candidate,
            ("review", "qa-plan", "qa-execute", "verify", "finalize"),
        )
        old_prepare = copy.deepcopy(
            refresh.ledger["tickets"]["01"]["delivery"]["reconcile-prepare"]
        )
        replacement_intent = copy.deepcopy(old_intent)
        replacement_intent["target_base"] = {
            "branch": "main",
            "ref": "refs/remotes/origin/main",
            "sha": "refresh-base-sha-2",
            "tree_oid": "refresh-base-tree-2",
        }
        refresh_intent = {
            "schema": 1,
            "branch": "ticket/01",
            "old_head": "refresh-old-head",
            "expected_remote_sha": "refresh-old-head",
            "old_local_head": "refresh-local-head-1",
            "old_target": copy.deepcopy(old_intent["target_base"]),
            "new_target": copy.deepcopy(replacement_intent["target_base"]),
            "old_intent": copy.deepcopy(old_intent),
            "old_prepare": copy.deepcopy(old_prepare),
            "replacement_intent": copy.deepcopy(replacement_intent),
        }
        refresh.record_delivery_metadata(
            "01", "reconcile-refresh-intent", refresh_intent
        )
        refreshed_candidate = CandidateRef(
            "refresh-base-tree-2", "refresh-tree-2", "ticket-1", 2
        )
        refresh.prepare_reconciliation(
            "01",
            refreshed_candidate,
            old_head="refresh-old-head",
            new_head="refresh-local-head-2",
            base_branch="main",
            base_sha="refresh-base-sha-2",
            base_tree_oid="refresh-base-tree-2",
            expected_remote_sha="refresh-old-head",
            refresh_intent=refresh_intent,
            replacement_intent=replacement_intent,
        )
        self.capture_event_prefixes(documents, refresh)

        repaired_budget = self.kernel()
        repaired_budget.activate("01", fixed)
        self.advance(
            repaired_budget,
            "01",
            fixed,
            ("implement", "simplify", "review"),
        )
        stale_budget = copy.deepcopy(
            repaired_budget.ledger["tickets"]["01"]["leaf_budget"]
        )
        repaired_candidate = CandidateRef(
            "base-1", "tree-repaired", "ticket-1", 2
        )
        with mock.patch(
            "autopilot.kernel.new_leaf_budget",
            return_value=copy.deepcopy(stale_budget),
        ):
            repaired_budget.invalidate_for_candidate_drift(
                "01", repaired_candidate
            )
        self.advance(
            repaired_budget,
            "01",
            repaired_candidate,
            ("implement", "simplify"),
        )
        repaired_budget.repair_revalidation_leaf_budget(
            "01", repaired_candidate
        )
        self.capture_event_prefixes(documents, repaired_budget)

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

        grant = self.kernel()
        grant.grant_autonomous_merge(
            actor="human",
            evidence="artifact://fixture-autonomous-grant",
        )
        self.capture_event_prefixes(documents, grant)

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
        document["history"] = decode_history(document["history"])
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
            document["history"] = decode_history(document["history"])
            for snapshot in (document, document["history"][-1]["snapshot"]):
                mutation(snapshot["tickets"]["01"]["delivery"]["pr-body"])
            resign_forged_history(document)
            with self.subTest(variant=variant), self.assertRaises(LedgerError):
                AtomicLedger._validate(document)

    def test_fresh_bundle_rebind_closes_over_current_verified_handoff(self) -> None:
        candidate = {
            "base_tree_oid": "base-2",
            "candidate_tree_oid": "tree-2",
            "ticket_digest": "ticket-1",
            "contract_version": 2,
        }
        bundle_ref = {
            "artifact": str(Path("/artifacts/bundle-new.json").resolve()),
            "sha256": "b" * 64,
            "handoff_sha256": "h" * 64,
        }
        ticket = {
            "candidate_ref": candidate,
            "artifact_generation": 2,
            "leaf_results": {
                "verify": {
                    "quality": {
                        "evidence": [
                            {
                                "id": "verification-checkpoint:bundle-validated",
                                "artifact": bundle_ref["artifact"],
                                "sha256": bundle_ref["sha256"],
                                "result": "pass",
                                "candidate_ref": candidate,
                            },
                            {
                                "id": "verification-checkpoint:handoff-ready",
                                "artifact": "/artifacts/handoff-new.json",
                                "sha256": bundle_ref["handoff_sha256"],
                                "result": "pass",
                                "candidate_ref": candidate,
                            },
                        ]
                    }
                }
            },
        }
        previous = {
            "schema": 1,
            "request_hash": "request-old",
            "expected_head_sha": "head-old",
            "body_sha256": "body-old",
            "body_path": "/artifacts/body-old.md",
            "bundle_sha256": "bundle-old",
            "bundle_path": "/artifacts/bundle-old.json",
            "verification_audit_root": "/verification-audit",
        }
        request_payload = {
            "schema": 1,
            "candidate_ref": candidate,
            "artifact_generation": 2,
            "expected_head_sha": "head-new",
            "reconciled_from_head": "head-old",
            "required_head_literal": "head-new",
            "verification_bundle": bundle_ref,
            "bundle_sha256": "bundle-new",
        }

        def request_digest(value: dict[str, object]) -> str:
            payload = {
                key: item
                for key, item in value.items()
                if key != "request_hash"
            }
            return hashlib.sha256(
                json.dumps(
                    payload,
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=False,
                ).encode("utf-8")
            ).hexdigest()

        request = {
            **request_payload,
            "request_hash": request_digest(request_payload),
        }
        latest = {
            "schema": 2,
            "old_head": "head-old",
            "new_head": "head-new",
            "old_body_sha256": "body-old",
            "new_body_sha256": "body-new",
            "old_bundle_sha256": "bundle-old",
            "new_bundle_sha256": "bundle-new",
            "old_bundle_path": "/artifacts/bundle-old.json",
            "new_bundle_path": "/artifacts/bundle-new.json",
            "old_verification_audit_root": "/verification-audit",
            "new_verification_audit_root": "/verification-audit",
            "render_request_hash": request["request_hash"],
            "old_receipt": previous,
        }
        current = {
            "schema": 2,
            "request_hash": request["request_hash"],
            "expected_head_sha": "head-new",
            "body_sha256": "body-new",
            "body_path": "/artifacts/body-new.md",
            "bundle_sha256": "bundle-new",
            "bundle_path": "/artifacts/bundle-new.json",
            "verification_audit_root": "/verification-audit",
            "lineage_rebinds": [latest],
        }
        self.assertTrue(
            _pr_body_rebind_is_closed(previous, current, request, ticket)
        )

        def mutate_stale_bundle(
            _current: dict[str, object],
            forged_request: dict[str, object],
        ) -> None:
            forged_request["verification_bundle"] = {
                **bundle_ref,
                "sha256": "s" * 64,
            }

        def mutate_stale_candidate(
            _current: dict[str, object],
            forged_request: dict[str, object],
        ) -> None:
            forged_request["candidate_ref"] = {
                **candidate,
                "candidate_tree_oid": "tree-stale",
            }

        mutations = {
            "missing-lineage": lambda value, _request: value.__setitem__(
                "lineage_rebinds", []
            ),
            "missing-old-receipt": lambda value, _request: value[
                "lineage_rebinds"
            ][-1].pop("old_receipt"),
            "old-bundle": lambda value, _request: value[
                "lineage_rebinds"
            ][-1].__setitem__("old_bundle_sha256", "forged-old-bundle"),
            "new-bundle": lambda value, _request: value[
                "lineage_rebinds"
            ][-1].__setitem__("new_bundle_sha256", "forged-new-bundle"),
            "schema-downgrade": lambda value, _request: value.__setitem__(
                "schema", 1
            ),
            "stale-verified-bundle": mutate_stale_bundle,
            "stale-candidate": mutate_stale_candidate,
        }
        for variant, mutation in mutations.items():
            forged_current = copy.deepcopy(current)
            forged_request = copy.deepcopy(request)
            mutation(forged_current, forged_request)
            if forged_request != request:
                forged_request["request_hash"] = request_digest(forged_request)
                forged_current["request_hash"] = forged_request["request_hash"]
                forged_current["lineage_rebinds"][-1][
                    "render_request_hash"
                ] = forged_request["request_hash"]
            with self.subTest(variant=variant):
                self.assertFalse(
                    _pr_body_rebind_is_closed(
                        previous,
                        forged_current,
                        forged_request,
                        ticket,
                    )
                )
        ticket_without_handoff = copy.deepcopy(ticket)
        ticket_without_handoff["leaf_results"] = {}
        self.assertFalse(
            _pr_body_rebind_is_closed(
                previous,
                current,
                request,
                ticket_without_handoff,
            )
        )

    def test_every_emitted_event_has_closed_semantic_replay(self) -> None:
        expected_names = {
            "run-initialized",
            "ticket-resumed",
            "ticket-activated",
            "candidate-adopted",
            "candidate-invalidated",
            "docs-only-candidate-adopted",
            "docs-only-candidate-rejected",
            "leaf-result-recorded",
            "revalidation-budget-repaired",
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
            "reconciliation-delivery-revalidation-required",
            "reconciliation-candidate-sealed",
            "reconciliation-target-refreshed",
            "reconciliation-equivalent",
            "pr-opened",
            "pr-head-updated",
            "merge-authorized",
            "autonomous-merge-granted",
            "completion-projection-granted",
            "completion-projection-gate-resolved",
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

    def test_completion_projection_grant_survives_but_does_not_retarget_on_drift(self) -> None:
        kernel = self.kernel(source_mode="ignored")
        ticket_digest = kernel.ledger["tickets"]["01"]["ticket_digest"]
        original = CandidateRef("base", "tree-one", ticket_digest, 2)
        drifted = CandidateRef("base", "tree-two", ticket_digest, 2)
        kernel.activate("01", original)
        destination = (
            Path(kernel.ledger["ticket_folder"])
            .resolve()
            .relative_to(Path(kernel.ledger["repo"]).resolve())
            .joinpath("done", "01.md")
            .as_posix()
        )
        grant, _ = kernel.grant_completion_projection(
            "01",
            candidate=original,
            destination_relative_path=destination,
            actor="fixture-actor",
            evidence="artifact://fixture-completion-projection",
        )
        kernel.invalidate_for_candidate_drift("01", drifted)

        self.assertEqual(grant, kernel.ledger["tickets"]["01"]["completion_projection_grant"])
        self.assertNotEqual(
            grant["candidate_ref"],
            kernel.ledger["tickets"]["01"]["candidate_ref"],
        )
        AtomicLedger._validate(kernel.ledger)

    def test_completion_projection_grant_appends_an_explicit_successor(self) -> None:
        kernel = self.kernel(source_mode="ignored")
        ticket_digest = kernel.ledger["tickets"]["01"]["ticket_digest"]
        original = CandidateRef("base", "tree-one", ticket_digest, 2)
        drifted = CandidateRef("base", "tree-two", ticket_digest, 2)
        kernel.activate("01", original)
        destination = (
            Path(kernel.ledger["ticket_folder"])
            .resolve()
            .relative_to(Path(kernel.ledger["repo"]).resolve())
            .joinpath("done", "01.md")
            .as_posix()
        )
        first, _ = kernel.grant_completion_projection(
            "01",
            candidate=original,
            destination_relative_path=destination,
            actor="fixture-actor-one",
            evidence="artifact://fixture-completion-projection/one",
        )

        legacy = json.loads(json.dumps(kernel.ledger))
        legacy["history"] = decode_history(legacy["history"])
        legacy["tickets"]["01"].pop("completion_projection_grants")
        legacy["history"][-1]["snapshot"]["tickets"]["01"].pop(
            "completion_projection_grants"
        )
        resign_forged_history(legacy)
        AtomicLedger._validate(legacy)

        legacy_kernel = Kernel(legacy)
        legacy_kernel.invalidate_for_candidate_drift("01", drifted)
        second, replayed = legacy_kernel.grant_completion_projection(
            "01",
            candidate=drifted,
            destination_relative_path=destination,
            actor="fixture-actor-two",
            evidence="artifact://fixture-completion-projection/two",
        )
        entries = completion_projection_grant_entries(
            legacy_kernel.ledger, "01"
        )

        self.assertFalse(replayed)
        self.assertIsNotNone(entries)
        assert entries is not None
        self.assertEqual([first, second], [entry["grant"] for entry in entries])
        self.assertEqual([1, 2], [entry["sequence"] for entry in entries])
        self.assertIsNone(entries[0]["predecessor_grant_id"])
        self.assertEqual(
            entries[0]["grant_id"], entries[1]["predecessor_grant_id"]
        )
        self.assertEqual(
            second,
            legacy_kernel.ledger["tickets"]["01"][
                "completion_projection_grant"
            ],
        )
        authority = legacy_kernel.report()["tickets"]["01"][
            "completion_projection_authority"
        ]
        self.assertEqual(2, authority["count"])
        self.assertEqual(entries[1]["grant_id"], authority["active_grant_id"])
        self.assertEqual(entries[0]["grant_id"], authority["predecessor_grant_id"])
        with self.assertRaisesRegex(TransitionError, "current candidate is immutable"):
            legacy_kernel.grant_completion_projection(
                "01",
                candidate=drifted,
                destination_relative_path=destination,
                actor="fixture-actor-three",
                evidence="artifact://fixture-completion-projection/three",
            )
        legacy_kernel.invalidate_for_candidate_drift("01", original)
        replayed_first, replayed = legacy_kernel.grant_completion_projection(
            "01",
            candidate=original,
            destination_relative_path=destination,
            actor="fixture-actor-one",
            evidence="artifact://fixture-completion-projection/one",
        )
        self.assertTrue(replayed)
        self.assertEqual(first, replayed_first)
        self.assertEqual(
            second,
            legacy_kernel.ledger["tickets"]["01"][
                "completion_projection_grant"
            ],
        )
        self.assertEqual(
            2,
            len(
                legacy_kernel.ledger["tickets"]["01"][
                    "completion_projection_grants"
                ]
            ),
        )
        third, replayed = legacy_kernel.grant_completion_projection(
            "01",
            candidate=original,
            destination_relative_path=destination,
            actor="fixture-actor-four",
            evidence="artifact://fixture-completion-projection/four",
        )
        self.assertFalse(replayed)
        self.assertEqual(
            third,
            legacy_kernel.ledger["tickets"]["01"][
                "completion_projection_grant"
            ],
        )
        latest_delta = legacy_kernel.ledger["history"][-1]["snapshot_delta"]
        append_operations = [
            operation
            for operation in latest_delta["operations"]
            if operation["path"][-1] == "completion_projection_grants"
        ]
        self.assertEqual(1, len(append_operations))
        self.assertEqual("append", append_operations[0]["op"])
        self.assertEqual(1, len(append_operations[0]["values"]))
        self.assertEqual(
            3,
            legacy_kernel.report()["tickets"]["01"][
                "completion_projection_authority"
            ]["count"],
        )
        AtomicLedger._validate(legacy_kernel.ledger)

    def test_completion_projection_grant_log_rejects_corruption(self) -> None:
        kernel = self.kernel(source_mode="ignored")
        ticket_digest = kernel.ledger["tickets"]["01"]["ticket_digest"]
        candidates = [
            CandidateRef("base", f"tree-{name}", ticket_digest, 2)
            for name in ("one", "two", "three")
        ]
        kernel.activate("01", candidates[0])
        destination = (
            Path(kernel.ledger["ticket_folder"])
            .resolve()
            .relative_to(Path(kernel.ledger["repo"]).resolve())
            .joinpath("done", "01.md")
            .as_posix()
        )
        for sequence, candidate in enumerate(candidates, 1):
            if sequence > 1:
                kernel.invalidate_for_candidate_drift("01", candidate)
            kernel.grant_completion_projection(
                "01",
                candidate=candidate,
                destination_relative_path=destination,
                actor=f"fixture-actor-{sequence}",
                evidence=f"artifact://fixture-completion-projection/{sequence}",
            )

        def delete_latest(entries: list[dict[str, object]]) -> None:
            entries.pop()

        def reorder(entries: list[dict[str, object]]) -> None:
            entries[0], entries[1] = entries[1], entries[0]

        def create_sequence_gap(entries: list[dict[str, object]]) -> None:
            entries[1]["sequence"] = 3

        def break_predecessor(entries: list[dict[str, object]]) -> None:
            entries[1]["predecessor_grant_id"] = "0" * 64

        def branch(entries: list[dict[str, object]]) -> None:
            entries[2]["predecessor_grant_id"] = entries[0]["grant_id"]

        def change_fields_under_identity(
            entries: list[dict[str, object]],
        ) -> None:
            entries[2]["grant"]["actor"] = "forged-actor"

        def mutate_prior_entry(entries: list[dict[str, object]]) -> None:
            changed = copy.deepcopy(entries[0]["grant"])
            changed["actor"] = "forged-prior-actor"
            entries[0] = completion_projection_grant_entry(
                changed,
                sequence=1,
                predecessor_grant_id=None,
            )
            entries[1]["predecessor_grant_id"] = entries[0]["grant_id"]

        corruptions = {
            "deletion": delete_latest,
            "reordering": reorder,
            "sequence-gap": create_sequence_gap,
            "predecessor-mismatch": break_predecessor,
            "branching": branch,
            "changed-fields-under-identity": change_fields_under_identity,
            "prior-entry-mutation": mutate_prior_entry,
        }
        for name, corrupt in corruptions.items():
            with self.subTest(corruption=name):
                forged = json.loads(json.dumps(kernel.ledger))
                forged["history"] = decode_history(forged["history"])
                entries = forged["tickets"]["01"][
                    "completion_projection_grants"
                ]
                corrupt(entries)
                current = forged["tickets"]["01"]
                current["completion_projection_grant"] = copy.deepcopy(
                    entries[-1]["grant"]
                )
                latest = forged["history"][-1]["snapshot"]["tickets"]["01"]
                latest["completion_projection_grants"] = copy.deepcopy(entries)
                latest["completion_projection_grant"] = copy.deepcopy(
                    current["completion_projection_grant"]
                )
                resign_forged_history(forged)

                with self.assertRaisesRegex(
                    LedgerError, "completion.projection.grant"
                ):
                    AtomicLedger._validate(forged)

    def test_completion_projection_grant_cannot_retarget_candidate(self) -> None:
        document = json.loads(
            json.dumps(
                self.emitted_event_documents()["completion-projection-granted"]
            )
        )
        forged = document["tickets"]["01"]["completion_projection_grant"]
        forged["candidate_ref"]["candidate_tree_oid"] = "forged-tree"
        event = document["history"][-1]
        event["snapshot"]["tickets"]["01"]["completion_projection_grant"] = copy.deepcopy(
            forged
        )
        event["details"]["grant"] = copy.deepcopy(forged)
        resign_forged_history(document)

        with self.assertRaisesRegex(
            LedgerError, "completion projection grant"
        ):
            AtomicLedger._validate(document)

    def test_completion_projection_resolution_cannot_consume_another_gate(self) -> None:
        document = json.loads(
            json.dumps(
                self.emitted_event_documents()[
                    "completion-projection-gate-resolved"
                ]
            )
        )
        event = document["history"][-1]
        event["details"]["gate_id"] = "gate:01:dynamic:999"
        resign_forged_history(document)

        with self.assertRaisesRegex(LedgerError, "non-matching gate"):
            AtomicLedger._validate(document)

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

    def test_revalidation_budget_repair_cannot_forge_source_lineage(self) -> None:
        document = json.loads(
            json.dumps(
                self.emitted_event_documents()[
                    "revalidation-budget-repaired"
                ]
            )
        )
        repair = document["history"][-1]
        self.assertEqual("revalidation-budget-repaired", repair["event"])
        repair["details"]["invalidation_sequence"] = 1
        resign_forged_history(document)

        with self.assertRaisesRegex(LedgerError, "lineage is invalid"):
            AtomicLedger._validate(document)

    def test_reconciliation_target_refresh_cannot_forge_attempt_lineage(self) -> None:
        document = json.loads(
            json.dumps(
                self.emitted_event_documents()[
                    "reconciliation-target-refreshed"
                ]
            )
        )
        refresh = document["history"][-1]
        self.assertEqual("reconciliation-target-refreshed", refresh["event"])
        refresh["details"]["old_target_sha"] = "forged-target"
        resign_forged_history(document)

        with self.assertRaisesRegex(
            LedgerError, "reconciliation target refresh payload is invalid"
        ):
            AtomicLedger._validate(document)

    def test_reconciliation_candidate_seal_cannot_forge_head_lineage(self) -> None:
        document = json.loads(
            json.dumps(
                self.emitted_event_documents()[
                    "reconciliation-candidate-sealed"
                ]
            )
        )
        sealed = document["history"][-1]
        self.assertEqual("reconciliation-candidate-sealed", sealed["event"])
        sealed["details"]["new_local_head"] = "forged-head"
        resign_forged_history(document)

        with self.assertRaisesRegex(
            LedgerError, "reconciliation-candidate-sealed lineage is invalid"
        ):
            AtomicLedger._validate(document)

    def test_reconciliation_target_refresh_refuses_post_provider_state(self) -> None:
        document = self.emitted_event_documents()[
            "reconciliation-target-refreshed"
        ]
        before_refresh = copy.deepcopy(document["history"][-2]["snapshot"])
        before_refresh["history"] = copy.deepcopy(document["history"][:-1])
        kernel = Kernel(before_refresh)
        kernel.record_delivery_metadata(
            "01",
            "reconcile-push",
            {
                "operation": "force-with-lease-push",
                "branch": "ticket/01",
                "expected_old_head": "refresh-old-head",
                "new_head": "refresh-local-head-1",
            },
        )
        ticket = kernel.ledger["tickets"]["01"]
        refresh_intent = ticket["delivery"]["reconcile-refresh-intent"]
        refreshed_candidate = CandidateRef(
            "refresh-base-tree-2", "refresh-tree-2", "ticket-1", 2
        )

        with self.assertRaisesRegex(
            TransitionError, "cannot refresh after provider mutation"
        ):
            kernel.prepare_reconciliation(
                "01",
                refreshed_candidate,
                old_head="refresh-old-head",
                new_head="refresh-local-head-2",
                base_branch="main",
                base_sha="refresh-base-sha-2",
                base_tree_oid="refresh-base-tree-2",
                expected_remote_sha="refresh-old-head",
                refresh_intent=refresh_intent,
                replacement_intent=refresh_intent["replacement_intent"],
            )

    def test_replay_rejects_tampered_terminal_proof_binding(self) -> None:
        document = copy.deepcopy(
            self.emitted_event_documents()["ticket-integrated"]
        )
        proof = document["tickets"]["01"]["delivery"][
            "terminal-integration"
        ]
        proof["provider_observation_digest"] = "0" * 64
        event = document["history"][-1]
        self.assertEqual("ticket-integrated", event["event"])
        event["details"]["terminal_proof_digest"] = canonical_digest(proof)
        event["snapshot"] = {
            key: copy.deepcopy(value)
            for key, value in document.items()
            if key != "history"
        }
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


class TerminalIntegrationProofTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        root = Path(self.directory.name)
        self.remote = root / "remote.git"
        self.repo = root / "repo"
        subprocess.run(
            ["git", "init", "--bare", str(self.remote)],
            check=True,
            capture_output=True,
        )
        self.repo.mkdir()
        self.git("init", "-b", "main")
        self.git("config", "user.email", "tests@example.invalid")
        self.git("config", "user.name", "Tests")
        self.git("remote", "add", "origin", str(self.remote))
        (self.repo / "base.txt").write_text("base\n")
        self.git("add", ".")
        self.git("commit", "-m", "base")
        self.base = self.git("rev-parse", "HEAD")
        self.git("push", "-u", "origin", "main")

    def git(self, *args: str) -> str:
        return subprocess.run(
            ["git", *args],
            cwd=self.repo,
            text=True,
            capture_output=True,
            check=True,
        ).stdout.strip()

    def commit(self, branch: str, path: str, content: str) -> str:
        self.git("checkout", "-B", branch, self.base)
        (self.repo / path).write_text(content)
        self.git("add", path)
        self.git("commit", "-m", branch)
        return self.git("rev-parse", "HEAD")

    def ledger(
        self,
        *,
        ticket_id: str,
        head_sha: str,
        base_branch: str,
        blocked_by: list[str] | None = None,
        tickets: dict[str, object] | None = None,
    ) -> dict[str, object]:
        all_tickets = dict(tickets or {})
        all_tickets[ticket_id] = {
            "blocked_by": list(blocked_by or []),
            "delivery_lineage": {
                "branch": f"ticket/{ticket_id}",
                "base_branch": base_branch,
                "base_sha": self.base,
            },
            "pr": {
                "provider": "github",
                "pr_id": ticket_id,
                "head_sha": head_sha,
                "branch": f"ticket/{ticket_id}",
                "base_branch": base_branch,
                "base_sha": self.base,
            },
        }
        return {
            "repo": str(self.repo.resolve()),
            "provider": "github",
            "tickets": all_tickets,
        }

    @staticmethod
    def observation(
        ticket_id: str,
        head_sha: str,
        base_branch: str,
        merge_commit_sha: str | None,
    ) -> dict[str, object]:
        return {
            "schema": 1,
            "provider": "github",
            "operation": "get-pr-state",
            "evidence_class": "live",
            "observed": True,
            "pr_id": ticket_id,
            "head_sha": head_sha,
            "base": base_branch,
            "merge_commit_sha": merge_commit_sha,
            "state": "merged",
        }

    def build(
        self,
        ledger: dict[str, object],
        ticket_id: str,
        observation: dict[str, object],
    ) -> dict[str, object]:
        boundaries: list[str] = []
        proof = build_terminal_integration_proof(
            self.repo,
            ledger,
            ticket_id,
            observation,
            provenance="external-readback",
            boundary_guard=boundaries.append,
        )
        self.assertEqual(["git:terminal-integration-fetch"], boundaries)
        return proof

    def test_exact_head_reachability_is_bound_and_drift_is_rejected(self) -> None:
        head = self.commit("ticket/01", "head.txt", "head\n")
        self.git("push", "origin", f"{head}:refs/heads/main")
        ledger = self.ledger(
            ticket_id="01", head_sha=head, base_branch="main"
        )
        observation = self.observation("01", head, "main", None)

        proof = self.build(ledger, "01", observation)

        self.assertEqual("head", proof["reachable_kind"])
        self.assertEqual(head, proof["reachable_sha"])
        ledger["tickets"]["01"]["delivery_lineage"]["base_sha"] = "drift"
        with self.assertRaisesRegex(
            TerminalIntegrationError, "binding is stale"
        ):
            validate_terminal_integration_proof(
                ledger,
                "01",
                proof,
                observation,
                provenance="external-readback",
            )

    def test_explicit_provider_merge_commit_can_prove_squash_reachability(self) -> None:
        head = self.commit("ticket/01", "head.txt", "head\n")
        tree = self.git("rev-parse", f"{head}^{{tree}}")
        squash = self.git(
            "commit-tree",
            tree,
            "-p",
            self.base,
            "-m",
            "provider squash",
        )
        self.git("push", "origin", f"{squash}:refs/heads/main")
        ledger = self.ledger(
            ticket_id="01", head_sha=head, base_branch="main"
        )
        observation = self.observation("01", head, "main", squash)

        proof = self.build(ledger, "01", observation)

        self.assertEqual("merge-commit", proof["reachable_kind"])
        self.assertEqual(squash, proof["reachable_sha"])

    def test_terminal_branch_drift_during_fresh_proof_is_rejected(self) -> None:
        head = self.commit("ticket/01", "head.txt", "head\n")
        self.git("push", "origin", f"{head}:refs/heads/main")
        (self.repo / "advanced.txt").write_text("advanced\n")
        self.git("add", "advanced.txt")
        self.git("commit", "-m", "advanced terminal")
        advanced = self.git("rev-parse", "HEAD")
        ledger = self.ledger(
            ticket_id="01", head_sha=head, base_branch="main"
        )
        observation = self.observation("01", head, "main", None)
        repo = self.repo

        class DriftRunner:
            def __init__(self, owner: TerminalIntegrationProofTests):
                self.owner = owner
                self.advanced = False

            def run(
                self, command: list[str], *, cwd: Path
            ) -> subprocess.CompletedProcess[str]:
                if command[1:3] == ["ls-remote", "--heads"]:
                    self.owner.git(
                        "push", "origin", f"{advanced}:refs/heads/main"
                    )
                    self.advanced = True
                return subprocess.run(
                    command,
                    cwd=repo,
                    text=True,
                    capture_output=True,
                )

        runner = DriftRunner(self)
        with self.assertRaisesRegex(
            TerminalIntegrationError, "changed during reachability proof"
        ):
            build_terminal_integration_proof(
                self.repo,
                ledger,
                "01",
                observation,
                provenance="external-readback",
                boundary_guard=lambda _boundary: None,
                runner=runner,
            )
        self.assertTrue(runner.advanced)

    def test_stacked_child_waits_until_exact_head_reaches_terminal_branch(self) -> None:
        parent = self.commit("ticket/01", "parent.txt", "parent\n")
        self.git("push", "origin", f"{parent}:refs/heads/ticket/01")
        self.git("checkout", "-B", "ticket/02", parent)
        (self.repo / "child.txt").write_text("child\n")
        self.git("add", "child.txt")
        self.git("commit", "-m", "child")
        child = self.git("rev-parse", "HEAD")
        self.git("push", "origin", f"{child}:refs/heads/ticket/01")
        parent_ticket = self.ledger(
            ticket_id="01", head_sha=parent, base_branch="main"
        )["tickets"]["01"]
        ledger = self.ledger(
            ticket_id="02",
            head_sha=child,
            base_branch="ticket/01",
            blocked_by=["01"],
            tickets={"01": parent_ticket},
        )
        observation = self.observation(
            "02", child, "ticket/01", child
        )

        self.assertEqual("main", terminal_branch(ledger, "02"))
        with self.assertRaisesRegex(
            TerminalIntegrationError, "neither its exact head nor merge commit"
        ):
            self.build(ledger, "02", observation)

        self.git("push", "origin", f"{child}:refs/heads/main")
        proof = self.build(ledger, "02", observation)
        self.assertEqual("main", proof["terminal_branch"])
        self.assertEqual("head", proof["reachable_kind"])
        self.assertEqual(child, proof["reachable_sha"])


class FakeProviderRunner:
    def __init__(self, *responses: str | CommandResult):
        self.responses = [
            response
            if isinstance(response, CommandResult)
            else CommandResult(response, "", 0)
            for response in responses
        ]
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
        self.assertEqual("observed", receipt["rules_observation"]["status"])

    def test_github_private_plan_limit_is_explicit_live_policy_evidence(self) -> None:
        runner = FakeProviderRunner(
            json.dumps(
                {
                    "number": 7,
                    "headRefOid": "head-1",
                    "baseRefName": "main",
                    "mergeStateStatus": "CLEAN",
                    "statusCheckRollup": [],
                }
            ),
            CommandResult(
                json.dumps(
                    {
                        "message": (
                            "Upgrade to GitHub Pro or make this repository public "
                            "to enable this feature."
                        ),
                        "documentation_url": (
                            "https://docs.github.com/rest/repos/rules"
                            "#get-rules-for-a-branch"
                        ),
                        "status": "403",
                    }
                ),
                "gh: plan feature unavailable (HTTP 403)",
                1,
            ),
        )

        receipt = ProviderExecutor(
            GitHubProvider(), cwd=Path("/tmp"), mode="live", runner=runner
        ).execute(
            GET_CHECKS_AND_POLICIES,
            pr_id="7",
            expected_head="head-1",
        )

        self.assertEqual([], receipt["active_rules"])
        self.assertEqual("direct", receipt["merge_mode"])
        self.assertEqual(
            {
                "schema": 1,
                "source": "github-active-rules-api",
                "status": "feature-unavailable",
                "reason": "private-repository-plan-limit",
                "http_status": 403,
                "documentation_url": (
                    "https://docs.github.com/rest/repos/rules"
                    "#get-rules-for-a-branch"
                ),
            },
            receipt["rules_observation"],
        )

    def test_github_private_plan_near_misses_remain_provider_errors(self) -> None:
        canonical = {
            "message": (
                "Upgrade to GitHub Pro or make this repository public "
                "to enable this feature."
            ),
            "documentation_url": (
                "https://docs.github.com/rest/repos/rules"
                "#get-rules-for-a-branch"
            ),
            "status": "403",
        }
        near_misses = (
            {**canonical, "status": "401"},
            {**canonical, "message": "Resource not accessible by integration"},
            {**canonical, "documentation_url": "https://docs.github.com/rest/repos"},
            "not-json",
        )
        for response in near_misses:
            with self.subTest(response=response):
                runner = FakeProviderRunner(
                    json.dumps(
                        {
                            "number": 7,
                            "headRefOid": "head-1",
                            "baseRefName": "main",
                            "mergeStateStatus": "CLEAN",
                            "statusCheckRollup": [],
                        }
                    ),
                    CommandResult(
                        response if isinstance(response, str) else json.dumps(response),
                        "gh: provider request failed (HTTP 403)",
                        1,
                    ),
                )
                with self.assertRaises(ProviderError):
                    ProviderExecutor(
                        GitHubProvider(),
                        cwd=Path("/tmp"),
                        mode="live",
                        runner=runner,
                    ).execute(
                        GET_CHECKS_AND_POLICIES,
                        pr_id="7",
                        expected_head="head-1",
                    )

    def test_private_plan_limit_selects_direct_exact_head_merge(self) -> None:
        plan_limit = CommandResult(
            json.dumps(
                {
                    "message": (
                        "Upgrade to GitHub Pro or make this repository public "
                        "to enable this feature."
                    ),
                    "documentation_url": (
                        "https://docs.github.com/rest/repos/rules"
                        "#get-rules-for-a-branch"
                    ),
                    "status": "403",
                }
            ),
            "gh: plan feature unavailable (HTTP 403)",
            1,
        )
        runner = FakeProviderRunner(
            json.dumps(
                {
                    "id": "PR_7",
                    "headRefOid": "head-1",
                    "baseRefName": "main",
                }
            ),
            plan_limit,
            "",
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

        self.assertEqual("direct", receipt["merge_mode"])
        self.assertEqual(
            "feature-unavailable", receipt["rules_observation"]["status"]
        )
        self.assertEqual(["gh", "pr", "merge"], runner.commands[2][:3])
        self.assertIn("--match-head-commit", runner.commands[2])

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

    def test_provider_readback_normalizes_explicit_merge_commit_identity(self) -> None:
        github_runner = FakeProviderRunner(
            json.dumps(
                {
                    "number": 7,
                    "url": "https://github.example/pr/7",
                    "state": "MERGED",
                    "mergedAt": "2026-08-30T12:00:00Z",
                    "mergeCommit": {"oid": "a" * 40},
                    "headRefName": "ticket/01",
                    "headRefOid": "b" * 40,
                    "baseRefName": "main",
                    "body": "body",
                    "reviewDecision": "",
                    "reviews": [],
                }
            )
        )
        azure_runner = FakeProviderRunner(
            json.dumps(
                {
                    "pullRequestId": 8,
                    "status": "completed",
                    "sourceRefName": "refs/heads/ticket/02",
                    "targetRefName": "refs/heads/main",
                    "lastMergeSourceCommit": {"commitId": "c" * 40},
                    "lastMergeCommit": {"commitId": "d" * 40},
                    "description": "body",
                    "url": "https://azure.example/pr/8",
                }
            )
        )

        github = ProviderExecutor(
            GitHubProvider(),
            cwd=Path("/tmp"),
            mode="live",
            runner=github_runner,
        ).execute(GET_PR_STATE, pr_id="7")
        azure = ProviderExecutor(
            AzureDevOpsProvider(),
            cwd=Path("/tmp"),
            mode="live",
            runner=azure_runner,
        ).execute(GET_PR_STATE, pr_id="8")

        self.assertEqual("a" * 40, github["merge_commit_sha"])
        self.assertEqual("d" * 40, azure["merge_commit_sha"])
        self.assertIn("mergeCommit", github_runner.commands[0][-1])

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
