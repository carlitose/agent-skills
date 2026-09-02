from __future__ import annotations

import copy
import hashlib
import json
import re
import time
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterator, cast

from .autonomous_readiness import (
    autonomous_merge_dependencies_ready as dependencies_ready_for_merge,
)
from .leaf_protocol import (
    BudgetConfig,
    LeafProtocolError,
    budget_status,
    candidate_dict,
    continuation_context,
    leaf_health,
    new_leaf_budget,
    normalize_file_manifest,
    normalize_resource_usage,
    record_leaf_result as normalize_leaf_result,
    rebuild_leaf_budget_epoch,
    validate_handoff_progression,
    validate_leaf_budget,
    validate_leaf_result,
    verification_checkpoint_identity,
)
from .candidate_contract import (
    CandidateContractError,
    CandidateRef,
    DeliveryLineage,
    delivery_lineage,
    semantic_candidate,
)
from .docs_only_contract import DocsOnlyError, normalize_docs_only_receipt
from .equivalent_head import (
    DELIVERY_STEP as EQUIVALENT_HEAD_DELIVERY_STEP,
    EquivalentHeadError,
    validate_equivalent_head_receipt,
)
from .history_codec import diff_snapshots, history_event_hash
from .ledger import (
    AUTONOMOUS_GRANT_VERSION,
    COMPLETION_PROJECTION_GRANT_VERSION,
    LEDGER_VERSION,
    autonomous_merge_grant_matches_run,
    completion_projection_delivery_head_proof_matches,
    completion_projection_grant_entries,
    completion_projection_grant_entry,
    completion_projection_grant_matches_ticket,
    wiki_sync_merge_grant_matches_run,
    WIKI_SYNC_GRANT_VERSION,
)
from .ticket_contract import TicketGraph
from .reconciliation_gates import RECONCILIATION_CONDITION_GATE_CATEGORIES
from .reconciliation_intent import (
    PREPARATION_REFRESH_HISTORY_STEP,
    PREPARATION_REFRESH_STEP,
    ReconciliationIntentError,
    validate_preparation_refresh,
)
from .terminal_integration import (
    PROOF_VERSION,
    TerminalIntegrationError,
    canonical_digest,
    validate_terminal_integration_proof,
)
from .status_barrier import StatusBarrierError, active_status_barrier


STAGES = (
    "implement",
    "simplify",
    "review",
    "qa-plan",
    "qa-execute",
    "verify",
    "finalize",
)
QUALITY_STAGES = frozenset({"review", "qa-execute", "verify"})
TERMINAL_TICKET_STATES = frozenset({"failed", "integrated"})
RUN_STATES = frozenset({"running", "waiting", "completed", "failed", "aborted"})
MERGE_POLICIES = frozenset({"manual", "autonomous"})
HEAD_BOUND_MERGE_DELIVERY_STEPS = (
    "autonomous-eligibility",
    "merge-intent",
    "merge-observation",
    "merge-attempt",
    "merge-mutation",
    "merge-readback",
    "merge-progress",
    "integration",
    "terminal-integration",
    EQUIVALENT_HEAD_DELIVERY_STEP,
)
STALE_DELIVERY_PREPARATION_STEPS = (
    "prepared",
    "pr-body-request",
    "pr-body",
    "provider-simulation",
    "result",
)
LEAF_BUDGET_EPOCH_EVENTS = frozenset(
    {
        "candidate-invalidated",
        "delivery-revalidation-required",
        "reconciliation-revalidation-required",
    }
)


class TransitionError(RuntimeError):
    """The requested transition would violate a workflow invariant."""


class Kernel:
    def __init__(self, ledger: dict[str, Any]):
        self.ledger = ledger
        self._validate_shape()

    @classmethod
    def new(
        cls,
        run_id: str,
        graph: TicketGraph,
        *,
        max_quality_failures: int = 3,
        max_leaf_interactions: int = 10,
        max_leaf_tool_calls: int | None = None,
        max_leaf_wall_time: int | None = None,
        provider: str | None = None,
        provider_mode: str = "live",
        worktree: str | None = None,
        repo: str | None = None,
        provider_capabilities: dict[str, object] | None = None,
        base_sha: str | None = None,
        source_mode: str = "tracked",
        snapshot_manifest_digest: str | None = None,
        snapshot_manifest_path: str | None = None,
        source_folder_identity: dict[str, int] | None = None,
        merge_policy: str = "manual",
        merge_actor: str | None = None,
        merge_evidence: str | None = None,
        wiki_sync_merge_policy: str = "manual",
        wiki_sync_merge_actor: str | None = None,
        wiki_sync_merge_evidence: str | None = None,
    ) -> "Kernel":
        try:
            budget_config = BudgetConfig(
                max_quality_failures=max_quality_failures,
                max_leaf_interactions=max_leaf_interactions,
                max_leaf_tool_calls=max_leaf_tool_calls,
                max_leaf_wall_time=max_leaf_wall_time,
            ).normalized()
        except LeafProtocolError as error:
            raise TransitionError(str(error)) from error
        if provider_mode not in {"live", "simulated"}:
            raise TransitionError("provider_mode must be live or simulated")
        if source_mode not in {"tracked", "ignored"}:
            raise TransitionError("ticket source mode must be tracked or ignored")
        if snapshot_manifest_digest is None:
            snapshot_manifest_digest = hashlib.sha256(
                json.dumps(
                    [
                        {
                            "ticket_id": ticket_id,
                            "digest": graph.tickets[ticket_id].digest,
                            "path": str(
                                graph.tickets[ticket_id].path.relative_to(graph.folder)
                            ),
                        }
                        for ticket_id in graph.order
                    ],
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest()
        if snapshot_manifest_path is None:
            snapshot_manifest_path = f"memory://ticket-source/{snapshot_manifest_digest}"
        if merge_policy not in MERGE_POLICIES:
            raise TransitionError("merge policy must be manual or autonomous")
        if merge_policy == "manual":
            if merge_actor is not None or merge_evidence is not None:
                raise TransitionError(
                    "manual merge policy cannot carry an autonomous grant"
                )
            autonomous_merge_grant = None
        else:
            if not merge_actor or not merge_evidence:
                raise TransitionError(
                    "autonomous merge policy requires actor and durable evidence"
                )
            if not provider or not repo:
                raise TransitionError(
                    "autonomous merge policy requires repository and provider identity"
                )
            autonomous_merge_grant = {
                "schema": 1,
                "policy_version": AUTONOMOUS_GRANT_VERSION,
                "repository_identity": repo,
                "run_id": run_id,
                "ticket_set_digest": snapshot_manifest_digest,
                "provider": provider,
                "policy": "autonomous",
                "actor": merge_actor,
                "evidence": merge_evidence,
            }
        if wiki_sync_merge_policy not in MERGE_POLICIES:
            raise TransitionError(
                "wiki-sync merge policy must be manual or autonomous"
            )
        if wiki_sync_merge_policy == "manual":
            if (
                wiki_sync_merge_actor is not None
                or wiki_sync_merge_evidence is not None
            ):
                raise TransitionError(
                    "manual wiki-sync policy cannot carry an autonomous grant"
                )
            wiki_sync_grant = None
        else:
            if not wiki_sync_merge_actor or not wiki_sync_merge_evidence:
                raise TransitionError(
                    "autonomous wiki-sync policy requires actor and durable evidence"
                )
            if not provider or not repo:
                raise TransitionError(
                    "autonomous wiki-sync policy requires repository and provider identity"
                )
            wiki_sync_grant = {
                "schema": 1,
                "policy_version": WIKI_SYNC_GRANT_VERSION,
                "repository_identity": repo,
                "run_id": run_id,
                "ticket_set_digest": snapshot_manifest_digest,
                "provider": provider,
                "policy": "autonomous",
                "scope": "wiki-sync-v1",
                "actor": wiki_sync_merge_actor,
                "evidence": wiki_sync_merge_evidence,
            }
        if source_folder_identity is None:
            try:
                folder_stat = graph.folder.stat(follow_symlinks=False)
                source_folder_identity = {
                    "device": folder_stat.st_dev,
                    "inode": folder_stat.st_ino,
                }
            except OSError:
                source_folder_identity = {"device": 0, "inode": 0}
        tickets: dict[str, dict[str, Any]] = {}
        for ticket_id in graph.order:
            ticket = graph.tickets[ticket_id]
            disposition = graph.dispositions.get(
                ticket_id,
                "completed" if ticket_id in graph.completed_ids else "open",
            )
            initial_state = (
                "integrated" if disposition == "completed" else "pending"
            )
            tickets[ticket_id] = {
                "ticket_id": ticket_id,
                "path": str(ticket.path),
                "source_relative_path": ticket.path.relative_to(graph.folder).as_posix(),
                "current_source_relative_path": ticket.path.relative_to(
                    graph.folder
                ).as_posix(),
                "ticket_digest": ticket.digest,
                "execution_mode": ticket.execution_mode,
                "blocked_by": list(ticket.blocked_by),
                "state": initial_state,
                "preexisting_integrated": initial_state == "integrated",
                "disposition": disposition,
                "attempt_outcome": None,
                "stop_reason": None,
                "disposition_receipt": None,
                "status_barrier": None,
                "status_barrier_history": [],
                "stage": None,
                "quality_failures": 0,
                "leaf_budget": new_leaf_budget(budget_config),
                "leaf_progress_events": [],
                "leaf_handoff": None,
                "leaf_results": {},
                "failure_kind": None,
                "candidate_ref": None,
                "delivery_candidate_ref": None,
                "delivery_lineage": None,
                "artifact_generation": 0,
                "validated_stages": [],
                "delivery": {},
                "pr": None,
                "merge_authorization": None,
                "completion_projection_grant": None,
            }
        ledger: dict[str, Any] = {
            "schema": LEDGER_VERSION,
            "run_id": run_id,
            "run_state": "running",
            "pause": None,
            "ticket_folder": str(graph.folder),
            "ticket_source_mode": source_mode,
            "snapshot_manifest_digest": snapshot_manifest_digest,
            "snapshot_manifest_path": snapshot_manifest_path,
            "ticket_source_folder_identity": source_folder_identity,
            "ticket_order": list(graph.order),
            **budget_config,
            "provider": provider,
            "provider_mode": provider_mode,
            "provider_capabilities": provider_capabilities,
            "merge_policy": merge_policy,
            "autonomous_merge_grant": autonomous_merge_grant,
            "wiki_sync_policy": {
                "schema": 1,
                "merge_policy": wiki_sync_merge_policy,
                "autonomous_grant": wiki_sync_grant,
            },
            "repo": repo,
            "worktree": worktree,
            "base_sha": base_sha,
            "terminal_integration_proof_version": PROOF_VERSION,
            "legacy_lifecycle_migration": None,
            "cleanup": None,
            "tickets": tickets,
            "gates": {},
            "effects": {},
            "history": [],
        }
        kernel = cls(ledger)
        kernel._event("run-initialized", ticket_id=None)
        kernel._update_run_state()
        kernel._seal_history(0, previous_snapshot=None)
        for ticket_id in graph.order:
            if (
                tickets[ticket_id]["state"] == "pending"
                and tickets[ticket_id]["disposition"] in {"open", "on-hold"}
                and tickets[ticket_id]["execution_mode"] == "HITL"
            ):
                previous_snapshot = copy.deepcopy(
                    {
                        key: value
                        for key, value in kernel.ledger.items()
                        if key != "history"
                    }
                )
                history_start = len(kernel.ledger["history"])
                kernel._open_gate(
                    ticket_id,
                    category="human",
                    scope="ticket",
                    reason="HITL start approval required",
                    kind="start",
                )
                kernel._update_run_state()
                kernel._seal_history(
                    history_start, previous_snapshot=previous_snapshot
                )
        kernel._validate_shape()
        return kernel

    @contextmanager
    def _transaction(self) -> Iterator[None]:
        snapshot = copy.deepcopy(self.ledger)
        previous_snapshot = {
            key: value for key, value in snapshot.items() if key != "history"
        }
        history_start = len(self.ledger["history"])
        try:
            yield
            self._seal_history(
                history_start, previous_snapshot=previous_snapshot
            )
            self._validate_shape()
        except Exception:
            self.ledger.clear()
            self.ledger.update(snapshot)
            raise

    def _validate_shape(self) -> None:
        if self.ledger.get("schema") != LEDGER_VERSION:
            raise TransitionError(
                "ledger schema is incompatible with semantic CandidateRef v2; "
                "start a new run or use an explicit validated migration"
            )
        try:
            BudgetConfig(
                max_quality_failures=cast(
                    int, self.ledger.get("max_quality_failures")
                ),
                max_leaf_interactions=cast(
                    int, self.ledger.get("max_leaf_interactions")
                ),
                max_leaf_tool_calls=self.ledger.get("max_leaf_tool_calls"),
                max_leaf_wall_time=self.ledger.get("max_leaf_wall_time"),
                reservations=self.ledger.get("reservations"),
            ).normalized()
        except LeafProtocolError as error:
            raise TransitionError(str(error)) from error
        if self.ledger.get("run_state") not in RUN_STATES:
            raise TransitionError("invalid run state")
        pause = self.ledger.get("pause")
        if pause is not None and (
            not isinstance(pause, dict)
            or set(pause) != {"actor", "reason"}
            or any(not isinstance(value, str) or not value for value in pause.values())
        ):
            raise TransitionError("invalid run pause receipt")
        if self.ledger.get("provider_mode", "live") not in {"live", "simulated"}:
            raise TransitionError("invalid provider mode")
        proof_version = self.ledger.get("terminal_integration_proof_version")
        if proof_version not in {None, PROOF_VERSION}:
            raise TransitionError("invalid terminal integration proof version")
        merge_policy = self.ledger.get("merge_policy", "manual")
        grant = self.ledger.get("autonomous_merge_grant")
        if merge_policy not in MERGE_POLICIES:
            raise TransitionError("invalid merge policy")
        if merge_policy == "manual":
            if grant is not None:
                raise TransitionError(
                    "manual merge policy cannot carry an autonomous grant"
                )
        elif not autonomous_merge_grant_matches_run(self.ledger):
            raise TransitionError(
                "autonomous merge grant contradicts its run binding"
            )
        if not wiki_sync_merge_grant_matches_run(self.ledger):
            raise TransitionError(
                "wiki-sync merge grant contradicts its scoped run binding"
            )
        if self.ledger.get("ticket_source_mode") not in {"tracked", "ignored"}:
            raise TransitionError(
                "ledger ticket source metadata is required; start a new run"
            )
        manifest_digest = self.ledger.get("snapshot_manifest_digest")
        folder_identity = self.ledger.get("ticket_source_folder_identity")
        if (
            not isinstance(manifest_digest, str)
            or len(manifest_digest) != 64
            or any(character not in "0123456789abcdef" for character in manifest_digest)
            or not isinstance(self.ledger.get("snapshot_manifest_path"), str)
            or not self.ledger["snapshot_manifest_path"]
        ):
            raise TransitionError(
                "ledger managed ticket snapshot metadata is invalid"
            )
        if (
            not isinstance(folder_identity, dict)
            or set(folder_identity) != {"device", "inode"}
            or any(type(folder_identity[field]) is not int for field in folder_identity)
            or any(folder_identity[field] < 0 for field in folder_identity)
        ):
            raise TransitionError("ledger ticket source folder identity is invalid")
        order = self.ledger.get("ticket_order")
        tickets = self.ledger.get("tickets")
        if not isinstance(order, list) or not isinstance(tickets, dict):
            raise TransitionError("invalid ticket ledger shape")
        if order != list(tickets):
            raise TransitionError("ticket order and ticket map differ")
        gates = self.ledger.get("gates")
        if not isinstance(gates, dict):
            raise TransitionError("invalid gate ledger shape")
        for ticket_id, ticket in tickets.items():
            disposition = ticket.get("disposition")
            if disposition not in {"open", "on-hold", "canceled", "completed"}:
                raise TransitionError("invalid ticket disposition")
            if "lifecycle" in ticket:
                raise TransitionError("persisted lifecycle duplicates ticket state")
            if ticket.get("attempt_outcome") not in {None, "stopped"}:
                raise TransitionError("invalid ticket attempt outcome")
            if ticket.get("stop_reason") is not None and (
                not isinstance(ticket["stop_reason"], str)
                or not ticket["stop_reason"]
            ):
                raise TransitionError("invalid ticket stop reason")
            if (ticket.get("attempt_outcome") == "stopped") != (
                ticket.get("stop_reason") is not None
            ):
                raise TransitionError("stopped attempt and reason must agree")
            receipt = ticket.get("disposition_receipt")
            if receipt is not None and (
                not isinstance(receipt, dict)
                or receipt.get("ticket_id") != ticket_id
                or receipt.get("to_disposition") != disposition
                or receipt.get("state") != "applied"
            ):
                raise TransitionError("invalid ticket disposition receipt")
            barrier_fields = {
                "schema",
                "transaction_id",
                "ticket_id",
                "from_disposition",
                "to_disposition",
                "actor",
                "reason",
                "authority_ref",
                "prior_state",
                "execution_lifecycle",
                "readiness",
                "prior_stop_reason",
                "outcome",
                "gate_ids",
                "readiness_causes",
                "evidence_preserved",
            }
            barrier_history = ticket.get("status_barrier_history", [])
            current_barrier = ticket.get("status_barrier")
            if not isinstance(barrier_history, list):
                raise TransitionError("invalid ticket status barrier history")
            for barrier in barrier_history:
                if (
                    not isinstance(barrier, dict)
                    or set(barrier) != barrier_fields
                    or barrier.get("schema") != 1
                    or barrier.get("ticket_id") != ticket_id
                    or not isinstance(barrier.get("transaction_id"), str)
                    or re.fullmatch(r"[0-9a-f]{64}", barrier["transaction_id"])
                    is None
                    or barrier.get("from_disposition")
                    not in {"open", "on-hold", "canceled"}
                    or barrier.get("to_disposition")
                    not in {"open", "on-hold", "canceled"}
                    or barrier.get("prior_state")
                    not in {"pending", "active", "gated", "waiting"}
                    or barrier.get("outcome")
                    not in {
                        "inactive-safe-boundary",
                        "stopped-at-safe-boundary",
                        "preserved-at-safe-boundary",
                    }
                    or any(
                        not isinstance(barrier.get(field), str)
                        or not barrier[field]
                        for field in (
                            "actor",
                            "reason",
                            "authority_ref",
                            "execution_lifecycle",
                            "readiness",
                        )
                    )
                    or (
                        barrier.get("prior_stop_reason") is not None
                        and (
                            not isinstance(barrier["prior_stop_reason"], str)
                            or not barrier["prior_stop_reason"]
                        )
                    )
                    or not isinstance(barrier.get("gate_ids"), list)
                    or any(
                        not isinstance(gate_id, str) or not gate_id
                        for gate_id in barrier.get("gate_ids", [])
                    )
                    or not isinstance(barrier.get("readiness_causes"), list)
                    or barrier.get("evidence_preserved") is not True
                ):
                    raise TransitionError("invalid ticket status barrier receipt")
            if len({item["transaction_id"] for item in barrier_history}) != len(
                barrier_history
            ):
                raise TransitionError("duplicate ticket status barrier receipt")
            if current_barrier is not None and (
                not barrier_history or current_barrier != barrier_history[-1]
            ):
                raise TransitionError("current ticket status barrier is contradictory")
            for barrier in barrier_history:
                expected_outcome = (
                    "stopped-at-safe-boundary"
                    if barrier["prior_state"] == "active"
                    else "preserved-at-safe-boundary"
                    if barrier["prior_state"] in {"gated", "waiting"}
                    else "inactive-safe-boundary"
                )
                if barrier["outcome"] != expected_outcome:
                    raise TransitionError(
                        "ticket status barrier outcome contradicts prior state"
                    )
            if ticket.get("execution_mode") not in {"AFK", "HITL"}:
                raise TransitionError("invalid ticket execution mode")
            if "effective_mode" in ticket:
                raise TransitionError("effective_mode is not canonical ticket metadata")
            if (
                not isinstance(ticket.get("source_relative_path"), str)
                or not ticket["source_relative_path"]
            ):
                raise TransitionError("ticket source relative path is invalid")
            if (
                not isinstance(ticket.get("current_source_relative_path"), str)
                or not ticket["current_source_relative_path"]
            ):
                raise TransitionError("ticket current source path is invalid")
            start_gates = [
                gate
                for gate in gates.values()
                if gate.get("ticket_id") == ticket_id
                and gate.get("kind") == "start"
            ]
            if ticket["execution_mode"] == "AFK" and start_gates:
                raise TransitionError("AFK ticket cannot have a start gate")
            if (
                ticket["execution_mode"] == "HITL"
                and self.ledger.get("history")
            ):
                requires_start_gate = (
                    not ticket.get("preexisting_integrated")
                    and disposition in {"open", "on-hold"}
                )
                valid_start_gate_counts = {1} if requires_start_gate else {0, 1}
                if len(start_gates) not in valid_start_gate_counts:
                    raise TransitionError(
                        "HITL ticket has invalid persisted start gate cardinality"
                    )
                if start_gates:
                    start_gate = start_gates[0]
                    if (
                        start_gate.get("category") != "human"
                        or start_gate.get("scope") != "ticket"
                        or start_gate.get("resume_state") != "pending"
                        or start_gate.get("resume_stage") is not None
                    ):
                        raise TransitionError("HITL start gate is malformed")
        active = [item for item in tickets.values() if item["state"] == "active"]
        if len(active) > 1:
            raise TransitionError("more than one active mutating ticket")
        history = self.ledger.get("history")
        if not isinstance(history, list):
            raise TransitionError("history must be a list")
        for sequence, event in enumerate(history, start=1):
            if event.get("sequence") != sequence:
                raise TransitionError("history sequence is not contiguous")

        for ticket in self.ledger["tickets"].values():
            try:
                if ticket.get("candidate_ref") is not None:
                    semantic_candidate(ticket["candidate_ref"])
                if ticket.get("delivery_lineage") is not None:
                    delivery_lineage(ticket["delivery_lineage"])
                integration = ticket.get("delivery", {}).get("integration")
                terminal_proof = ticket.get("delivery", {}).get(
                    "terminal-integration"
                )
                if terminal_proof is not None:
                    if not isinstance(integration, dict):
                        raise TerminalIntegrationError(
                            "terminal integration proof has no provider observation"
                        )
                    validate_terminal_integration_proof(
                        self.ledger,
                        ticket["ticket_id"],
                        terminal_proof,
                        integration,
                    )
                if (
                    proof_version == PROOF_VERSION
                    and ticket.get("state") == "integrated"
                    and not ticket.get("preexisting_integrated")
                    and terminal_proof is None
                ):
                    raise TerminalIntegrationError(
                        "integrated ticket lacks terminal reachability proof"
                    )
                validate_leaf_budget(self.ledger, ticket.get("leaf_budget"))
                progress_events = ticket.get("leaf_progress_events")
                if not isinstance(progress_events, list) or not all(
                    isinstance(event, dict) for event in progress_events
                ):
                    raise LeafProtocolError(
                        "leaf_progress_events must be an array of objects"
                    )
                handoff = ticket.get("leaf_handoff")
                results = ticket.get("leaf_results")
                if not isinstance(results, dict):
                    raise LeafProtocolError("leaf_results must be an object")
                for result_stage, result in results.items():
                    if result_stage not in {"review", "qa-plan", "qa-execute", "verify"}:
                        raise LeafProtocolError("leaf_results contains an invalid stage")
                    normalized_result = validate_leaf_result(
                        result,
                        expected_candidate_ref=ticket.get("candidate_ref"),
                        expected_stage=result_stage,
                    )
                    if not normalized_result["complete"]:
                        raise LeafProtocolError(
                            "leaf_results can contain only complete handoffs"
                        )
                if handoff is not None:
                    normalized = validate_leaf_result(
                        handoff,
                        expected_candidate_ref=ticket.get("candidate_ref"),
                        expected_stage=ticket.get("stage"),
                    )
                    if not progress_events:
                        raise LeafProtocolError(
                            "leaf handoff requires a persisted progress event"
                        )
                    latest = progress_events[-1]
                    if (
                        latest.get("candidate_ref")
                        != normalized["candidate_ref"]
                        or latest.get("stage") != normalized["stage"]
                        or latest.get("phase_contract")
                        != normalized["phase_contract"]
                        or latest.get("phase") != normalized["progress_phase"]
                    ):
                        raise LeafProtocolError(
                            "leaf handoff contradicts latest progress event"
                        )
            except (
                CandidateContractError,
                LeafProtocolError,
                TerminalIntegrationError,
            ) as error:
                raise TransitionError(str(error)) from error

    def _event(self, event: str, ticket_id: str | None, **details: Any) -> None:
        self.ledger["history"].append(
            {
                "sequence": len(self.ledger["history"]) + 1,
                "event": event,
                "ticket_id": ticket_id,
                "details": details,
            }
        )

    def _seal_history(
        self, start: int, *, previous_snapshot: dict[str, Any] | None
    ) -> None:
        if start >= len(self.ledger["history"]):
            return
        snapshot = copy.deepcopy(
            {key: value for key, value in self.ledger.items() if key != "history"}
        )
        previous_hash = (
            self.ledger["history"][start - 1]["hash"] if start else "0" * 64
        )
        for event in self.ledger["history"][start:]:
            event["previous_hash"] = previous_hash
            event.pop("snapshot", None)
            event.pop("snapshot_delta", None)
            event.pop("hash", None)
            if previous_snapshot is None:
                event["snapshot"] = snapshot
            else:
                event["snapshot_delta"] = diff_snapshots(
                    previous_snapshot, snapshot
                )
            event["hash"] = history_event_hash(event, snapshot)
            previous_hash = event["hash"]
            previous_snapshot = snapshot

    def _ticket(self, ticket_id: str) -> dict[str, Any]:
        try:
            return self.ledger["tickets"][ticket_id]
        except KeyError as error:
            raise TransitionError(f"unknown ticket {ticket_id!r}") from error

    @staticmethod
    def _invalidate_leaf_artifacts(ticket: dict[str, Any]) -> None:
        ticket["leaf_progress_events"] = []
        ticket["leaf_handoff"] = None
        ticket["leaf_results"] = {}
        for reservation in ticket["leaf_budget"]["reservations"].values():
            reservation["complete"] = False

    @staticmethod
    def _complete_ticket_lifecycle(ticket: dict[str, Any]) -> None:
        ticket["disposition"] = "completed"
        ticket["attempt_outcome"] = None
        ticket["stop_reason"] = None
        ticket["disposition_receipt"] = None

    def _active_ticket_id(self) -> str | None:
        active = [
            ticket_id
            for ticket_id, ticket in self.ledger["tickets"].items()
            if ticket["state"] == "active"
        ]
        return active[0] if active else None

    def _dependency_ready(self, ticket: dict[str, Any]) -> bool:
        if ticket.get("disposition", "open") != "open":
            return False
        blockers = ticket["blocked_by"]
        if not blockers:
            return True
        if any(
            self._ticket(blocker).get("disposition", "open")
            in {"on-hold", "canceled"}
            for blocker in blockers
        ):
            return False
        states = [self._ticket(blocker)["state"] for blocker in blockers]
        if len(blockers) == 1:
            blocker = self._ticket(blockers[0])
            return states[0] in {"pr-open", "integrated"} or (
                states[0] == "gated"
                and isinstance(blocker.get("pr"), dict)
                and self._has_open_provider_merge_gate(blockers[0])
            )
        return all(state == "integrated" for state in states)

    def ready_ids(self) -> list[str]:
        if self.ledger["run_state"] in {"aborted", "completed", "failed"}:
            return []
        if any(
            gate["state"] == "open" and gate["scope"] == "run"
            for gate in self.ledger["gates"].values()
        ):
            return []
        if self.ledger.get("pause") is not None:
            return []
        if self._active_ticket_id() is not None:
            return []
        if self.pending_runner_merge_id() is not None:
            return []
        return [
            ticket_id
            for ticket_id in self.ledger["ticket_order"]
            if self._ticket(ticket_id)["state"] == "pending"
            and self._ticket(ticket_id).get("disposition", "open") == "open"
            and self._ticket(ticket_id).get("status_barrier") is None
            and self._dependency_ready(self._ticket(ticket_id))
        ]

    def dependency_blocked_ids(self) -> list[str]:
        return [
            ticket_id
            for ticket_id in self.ledger["ticket_order"]
            if self._ticket(ticket_id)["state"] == "pending"
            and self._ticket(ticket_id).get("disposition", "open") == "open"
            and self._ticket(ticket_id).get("status_barrier") is None
            and not self._dependency_ready(self._ticket(ticket_id))
        ]

    def _administrative_dependency_causes(
        self, ticket_id: str, seen: set[str] | None = None
    ) -> list[dict[str, str]]:
        visited = set() if seen is None else set(seen)
        if ticket_id in visited:
            return []
        visited.add(ticket_id)
        causes: list[dict[str, str]] = []
        for blocker_id in self._ticket(ticket_id)["blocked_by"]:
            blocker = self._ticket(blocker_id)
            disposition = blocker.get("disposition", "open")
            if disposition == "on-hold":
                causes.append(
                    {"ticket_id": blocker_id, "reason": "dependency-on-hold"}
                )
            elif disposition == "canceled":
                causes.append(
                    {"ticket_id": blocker_id, "reason": "dependency-canceled"}
                )
            else:
                causes.extend(
                    self._administrative_dependency_causes(blocker_id, visited)
                )
        return [
            cause
            for index, cause in enumerate(causes)
            if cause not in causes[:index]
        ]

    def human_gated_ids(self) -> list[str]:
        return [
            gate_id
            for gate_id, gate in self.ledger["gates"].items()
            if gate["state"] == "open"
        ]

    def next_ready_id(self) -> str | None:
        ready = self.ready_ids()
        return ready[0] if ready else None

    def pending_runner_merge_id(self) -> str | None:
        pending = [
            ticket_id
            for ticket_id, ticket in self.ledger["tickets"].items()
            if ticket["state"] in {"pr-open", "gated"}
            and isinstance(ticket.get("merge_authorization"), dict)
            and ticket["merge_authorization"].get("mode")
            in {"runner", "autonomous"}
            and (
                ticket["merge_authorization"].get("mode") != "autonomous"
                or self.autonomous_merge_dependencies_ready(ticket_id)
            )
        ]
        if len(pending) > 1:
            raise TransitionError("multiple runner merges cannot be pending")
        return pending[0] if pending else None

    def pending_autonomous_merge_id(self) -> str | None:
        if self.ledger.get("merge_policy") != "autonomous":
            return None
        first_gated: str | None = None
        for ticket_id in self.ledger["ticket_order"]:
            ticket = self.ledger["tickets"][ticket_id]
            if ticket.get("merge_authorization") is not None:
                continue
            if not self.autonomous_merge_dependencies_ready(ticket_id):
                continue
            if ticket["state"] == "pr-open":
                return ticket_id
            if (
                first_gated is None
                and ticket["state"] == "gated"
                and self._has_open_provider_merge_gate(ticket_id)
            ):
                first_gated = ticket_id
        return first_gated

    def autonomous_merge_candidate_ready(self, ticket_id: str) -> bool:
        ticket = self._ticket(ticket_id)
        candidate = ticket.get("candidate_ref")
        if not isinstance(candidate, dict) or not isinstance(
            ticket.get("delivery_candidate_ref"), dict
        ):
            return False
        if ticket.get("validated_stages") == list(STAGES):
            return True
        receipt = ticket.get("docs_only")
        if (
            not isinstance(receipt, dict)
            or receipt.get("status") != "eligible"
            or ticket.get("validated_stages") != ["implement"]
            or set(ticket.get("leaf_results", {})) != {"verify"}
        ):
            return False
        try:
            normalized = normalize_docs_only_receipt(
                receipt,
                ticket=ticket,
                candidate=candidate,
            )
        except (DocsOnlyError, ValueError, TypeError, KeyError):
            return False
        return normalized == receipt

    def autonomous_merge_dependencies_ready(self, ticket_id: str) -> bool:
        return dependencies_ready_for_merge(
            self._ticket(ticket_id), self.ledger["tickets"]
        )

    def _has_open_provider_merge_gate(self, ticket_id: str) -> bool:
        return any(
            gate["ticket_id"] == ticket_id
            and gate["category"] == "provider-merge"
            and gate["state"] == "open"
            for gate in self.ledger["gates"].values()
        )

    def activate(self, ticket_id: str, candidate: CandidateRef) -> None:
        with self._transaction():
            candidate.validate()
            if self._active_ticket_id() is not None:
                raise TransitionError("another ticket is already active")
            if ticket_id not in self.ready_ids():
                raise TransitionError(f"ticket {ticket_id!r} is not ready")
            ticket = self._ticket(ticket_id)
            if (
                ticket["execution_mode"] == "HITL"
                and not any(
                    gate["ticket_id"] == ticket_id
                    and gate["kind"] == "start"
                    and gate["state"] == "passed"
                    for gate in self.ledger["gates"].values()
                )
            ):
                raise TransitionError(
                    f"ticket {ticket_id!r} lacks explicit HITL start approval"
                )
            ticket["state"] = "active"
            ticket["attempt_outcome"] = None
            ticket["stop_reason"] = None
            if ticket.pop("resume_pending", False):
                self._require_candidate(ticket, candidate)
                self._event(
                    "ticket-resumed", ticket_id, candidate_digest=candidate.digest
                )
            else:
                ticket["stage"] = STAGES[0]
                ticket["candidate_ref"] = asdict(candidate)
                self._event(
                    "ticket-activated", ticket_id, candidate_digest=candidate.digest
                )
            self._update_run_state()

    def _require_candidate(
        self, ticket: dict[str, Any], candidate: CandidateRef
    ) -> None:
        candidate.validate()
        if ticket["candidate_ref"] != asdict(candidate):
            raise TransitionError("CandidateRef drift; downstream result is stale")

    def adopt_implementation_candidate(
        self, ticket_id: str, candidate: CandidateRef
    ) -> bool:
        with self._transaction():
            ticket = self._ticket(ticket_id)
            if ticket["state"] != "active" or ticket["stage"] != "implement":
                raise TransitionError(
                    "implementation candidate can only be adopted at implement"
                )
            candidate.validate()
            if ticket["candidate_ref"] == asdict(candidate):
                return False
            ticket["candidate_ref"] = asdict(candidate)
            ticket["validated_stages"] = []
            self._invalidate_leaf_artifacts(ticket)
            ticket["artifact_generation"] += 1
            ticket["merge_authorization"] = None
            ticket.pop("docs_only", None)
            self._event(
                "candidate-adopted",
                ticket_id,
                candidate_digest=candidate.digest,
                artifact_generation=ticket["artifact_generation"],
            )
            return True

    def complete_docs_only_candidate(
        self,
        ticket_id: str,
        candidate: CandidateRef,
        *,
        receipt: dict[str, Any],
        verification_handoff: dict[str, Any],
    ) -> bool:
        """Atomically adopt a deterministic docs candidate without leaf accounting."""

        with self._transaction():
            ticket = self._ticket(ticket_id)
            existing = ticket.get("docs_only")
            if ticket["state"] == "verified" and existing == receipt:
                return False
            if ticket["state"] != "active" or ticket["stage"] != "implement":
                raise TransitionError(
                    "docs-only adoption requires an active implement stage"
                )
            candidate.validate()
            if ticket["leaf_budget"]["interactions_consumed"] != 0:
                raise TransitionError(
                    "docs-only adoption requires zero prior leaf interactions"
                )
            try:
                normalized_receipt = normalize_docs_only_receipt(
                    receipt,
                    ticket=ticket,
                    candidate=candidate,
                )
            except DocsOnlyError as error:
                raise TransitionError(str(error)) from error
            try:
                handoff = validate_leaf_result(
                    verification_handoff,
                    expected_candidate_ref=candidate_dict(candidate),
                    expected_stage="verify",
                )
            except LeafProtocolError as error:
                raise TransitionError(str(error)) from error
            if not handoff["complete"] or handoff["findings"]:
                raise TransitionError(
                    "docs-only verification handoff must be complete and finding-free"
                )
            expected_paths = normalized_receipt["changed_paths"]
            if handoff["scope"] != {
                "files_expected": expected_paths,
                "files_inspected": expected_paths,
                "files_remaining": [],
            }:
                raise TransitionError(
                    "docs-only verification scope differs from the adopted paths"
                )
            ticket["candidate_ref"] = candidate_dict(candidate)
            ticket["leaf_handoff"] = None
            ticket["leaf_results"] = {"verify": handoff}
            ticket["validated_stages"] = ["implement"]
            ticket["artifact_generation"] += 1
            ticket["merge_authorization"] = None
            ticket["docs_only"] = normalized_receipt
            ticket["state"] = "verified"
            ticket["stage"] = None
            self._event(
                "docs-only-candidate-adopted",
                ticket_id,
                candidate_digest=candidate.digest,
                evidence_sha256=normalized_receipt["evidence"]["sha256"],
                leaf_interactions_avoided=normalized_receipt.get(
                    "leaf_interactions_avoided", 0
                ),
            )
            self._update_run_state()
            return True

    def record_docs_only_rejection(
        self, ticket_id: str, *, reason: str
    ) -> bool:
        if not isinstance(reason, str) or not reason:
            raise TransitionError("docs-only rejection requires a reason")
        with self._transaction():
            ticket = self._ticket(ticket_id)
            if ticket["state"] != "active" or ticket["stage"] != "implement":
                raise TransitionError(
                    "docs-only rejection requires an active implement stage"
                )
            receipt = {
                "contract_version": 1,
                "status": "rejected",
                "reason": reason,
                "leaf_interactions_avoided": 0,
            }
            if ticket.get("docs_only") == receipt:
                return False
            ticket["docs_only"] = receipt
            self._event("docs-only-candidate-rejected", ticket_id, reason=reason)
            return True

    def invalidate_for_candidate_drift(
        self, ticket_id: str, candidate: CandidateRef
    ) -> None:
        with self._transaction():
            ticket = self._ticket(ticket_id)
            if ticket["state"] != "active":
                raise TransitionError("candidate drift requires an active ticket")
            candidate.validate()
            ticket["candidate_ref"] = asdict(candidate)
            ticket["stage"] = "implement"
            ticket["validated_stages"] = []
            ticket["leaf_budget"] = new_leaf_budget(self.ledger)
            self._invalidate_leaf_artifacts(ticket)
            ticket["artifact_generation"] += 1
            ticket["merge_authorization"] = None
            ticket.pop("docs_only", None)
            self._event(
                "candidate-invalidated",
                ticket_id,
                candidate_digest=candidate.digest,
                artifact_generation=ticket["artifact_generation"],
            )

    def repair_revalidation_leaf_budget(
        self, ticket_id: str, candidate: CandidateRef
    ) -> bool:
        """Repair a pre-fix semantic-revalidation budget without editing the ledger."""
        with self._transaction():
            ticket = self._ticket(ticket_id)
            if ticket["state"] != "active" or ticket["stage"] not in {
                "review",
                "qa-plan",
                "qa-execute",
                "verify",
            }:
                raise TransitionError(
                    "revalidation budget repair requires an active leaf stage"
                )
            self._require_candidate(ticket, candidate)
            generation = ticket["artifact_generation"]
            invalidations = [
                (index, event)
                for index, event in enumerate(self.ledger["history"])
                if event.get("ticket_id") == ticket_id
                and event.get("event") in LEAF_BUDGET_EPOCH_EVENTS
                and event.get("details", {}).get("artifact_generation")
                == generation
            ]
            if not invalidations:
                raise TransitionError(
                    "revalidation budget repair requires a semantic invalidation "
                    "for the current artifact generation"
                )
            invalidation_index, invalidation = invalidations[-1]
            if (
                invalidation.get("details", {}).get("candidate_digest")
                != candidate.digest
            ):
                raise TransitionError(
                    "revalidation budget repair CandidateRef differs from the "
                    "invalidation record"
                )
            epoch_events = [
                event
                for event in self.ledger["history"][invalidation_index + 1 :]
                if event.get("ticket_id") == ticket_id
                and event.get("event") == "leaf-result-recorded"
            ]
            progress_events = ticket["leaf_progress_events"]
            if len(epoch_events) != len(progress_events):
                raise TransitionError(
                    "revalidation budget repair cannot discard same-CandidateRef "
                    "leaf retries; start a new run with a larger budget"
                )
            for event, progress in zip(epoch_events, progress_events, strict=True):
                details = event["details"]
                delta = progress.get("resource_delta")
                if (
                    details.get("candidate_digest") != candidate.digest
                    or details.get("stage") != progress.get("stage")
                    or details.get("complete") != progress.get("complete")
                    or not isinstance(delta, dict)
                    or delta
                    != {
                        "interactions": 1,
                        "tool_calls": details.get("tool_calls"),
                        "wall_time": details.get("wall_time"),
                    }
                ):
                    raise TransitionError(
                        "revalidation budget repair history differs from current "
                        "CandidateRef progress"
                    )
            try:
                before = validate_leaf_budget(self.ledger, ticket["leaf_budget"])
                rebuilt = rebuild_leaf_budget_epoch(
                    self.ledger,
                    progress_events,
                    expected_candidate_ref=candidate_dict(candidate),
                )
            except LeafProtocolError as error:
                raise TransitionError(str(error)) from error
            if before == rebuilt:
                return False
            for field in (
                "interactions_consumed",
                "tool_calls_consumed",
                "wall_time_consumed",
            ):
                if before[field] < rebuilt[field]:
                    raise TransitionError(
                        "revalidation budget repair cannot increase consumed resources"
                    )
            for stage, rebuilt_reservation in rebuilt["reservations"].items():
                before_reservation = before["reservations"][stage]
                if (
                    before_reservation["consumed"]
                    < rebuilt_reservation["consumed"]
                    or before_reservation["complete"]
                    != rebuilt_reservation["complete"]
                ):
                    raise TransitionError(
                        "revalidation budget repair cannot rewrite current "
                        "mandatory-stage progress"
                    )
            ticket["leaf_budget"] = rebuilt
            self._event(
                "revalidation-budget-repaired",
                ticket_id,
                artifact_generation=generation,
                candidate_digest=candidate.digest,
                invalidation_event=invalidation["event"],
                invalidation_sequence=invalidation["sequence"],
                source_event_sequences=[
                    event["sequence"] for event in epoch_events
                ],
                before_budget=before,
                after_budget=rebuilt,
            )
            return True

    def record_stage(
        self,
        ticket_id: str,
        stage: str,
        result: str,
        candidate: CandidateRef,
    ) -> None:
        with self._transaction():
            ticket = self._ticket(ticket_id)
            if ticket["state"] != "active" or ticket["stage"] != stage:
                raise TransitionError(
                    f"expected active stage {ticket['stage']!r}, received {stage!r}"
                )
            if stage not in STAGES:
                raise TransitionError(f"unknown stage {stage!r}")
            if result not in {"pass", "fail", "gated"}:
                raise TransitionError(f"unknown stage result {result!r}")
            self._require_candidate(ticket, candidate)
            leaf_stages = {"review", "qa-plan", "qa-execute", "verify"}
            if stage in leaf_stages and result in {"pass", "fail"}:
                try:
                    handoff = validate_leaf_result(
                        ticket["leaf_handoff"],
                        expected_candidate_ref=candidate_dict(candidate),
                        expected_stage=stage,
                    )
                except LeafProtocolError as error:
                    raise TransitionError(
                        f"{stage} result requires a valid structured leaf handoff"
                    ) from error
                if result == "pass" and (
                    not handoff["complete"] or handoff["findings"]
                ):
                    raise TransitionError(
                        f"{stage} cannot pass with partial scope or findings"
                    )
                if result == "fail" and not handoff["findings"]:
                    raise TransitionError(
                        f"{stage} failure requires a structured finding"
                    )
            if result == "gated":
                self._open_gate(
                    ticket_id,
                    category="environment",
                    scope="ticket",
                    reason=f"{stage} reported a gate",
                    kind="stage",
                )
            elif result == "pass":
                if stage in leaf_stages:
                    ticket["leaf_results"][stage] = handoff
                    ticket["leaf_handoff"] = None
                ticket["validated_stages"].append(stage)
                if stage == STAGES[-1]:
                    ticket["state"] = "verified"
                    ticket["stage"] = None
                else:
                    ticket["stage"] = STAGES[STAGES.index(stage) + 1]
                self._event("stage-passed", ticket_id, stage=stage)
            elif stage in QUALITY_STAGES:
                ticket["quality_failures"] += 1
                ticket["validated_stages"] = []
                if stage in leaf_stages:
                    self._invalidate_leaf_artifacts(ticket)
                if (
                    ticket["quality_failures"]
                    >= self.ledger["max_quality_failures"]
                ):
                    ticket["state"] = "failed"
                    ticket["stage"] = None
                    ticket["failure_kind"] = "quality"
                else:
                    ticket["stage"] = STAGES[0]
                self._event(
                    "quality-failed",
                    ticket_id,
                    stage=stage,
                    failures=ticket["quality_failures"],
                )
            else:
                ticket["state"] = "failed"
                ticket["stage"] = None
                ticket["validated_stages"] = []
                ticket["failure_kind"] = (
                    "finalization" if stage == "finalize" else "implementation"
                )
                self._event(
                    "ticket-failed",
                    ticket_id,
                    stage=stage,
                    failure_kind=ticket["failure_kind"],
                )
            self._update_run_state()

    def record_evidence_cache_decision(
        self,
        ticket_id: str,
        *,
        key_hash: str,
        hit: bool,
        commands_avoided: int,
        limitations: list[str],
        miss_reason: str | None,
    ) -> None:
        if not re.fullmatch(r"[0-9a-f]{64}", key_hash):
            raise TransitionError("evidence cache key_hash must be sha256")
        if not isinstance(hit, bool):
            raise TransitionError("evidence cache hit must be boolean")
        if (
            not isinstance(commands_avoided, int)
            or isinstance(commands_avoided, bool)
            or commands_avoided < 0
        ):
            raise TransitionError(
                "evidence cache commands_avoided must be non-negative"
            )
        if not limitations or any(
            not isinstance(item, str) or not item for item in limitations
        ):
            raise TransitionError(
                "evidence cache limitations must be non-empty strings"
            )
        if miss_reason is not None and (
            not isinstance(miss_reason, str) or not miss_reason
        ):
            raise TransitionError(
                "evidence cache miss_reason must be null or non-empty"
            )
        with self._transaction():
            self._ticket(ticket_id)
            self._event(
                "evidence-cache-decision",
                ticket_id,
                key_hash=key_hash,
                hit=hit,
                commands_avoided=commands_avoided,
                limitations=list(limitations),
                miss_reason=miss_reason,
            )

    def record_leaf_result(
        self,
        ticket_id: str,
        result: dict[str, Any],
        candidate: CandidateRef,
        *,
        expected_files: list[str],
        tool_calls: int = 0,
        wall_time: int = 0,
    ) -> dict[str, Any]:
        with self._transaction():
            ticket = self._ticket(ticket_id)
            stage = ticket["stage"]
            if (
                ticket["state"] != "active"
                or stage not in {"review", "qa-plan", "qa-execute", "verify"}
            ):
                raise TransitionError(
                    "bounded leaf results require an active leaf stage"
                )
            self._require_candidate(ticket, candidate)
            try:
                normalized_input = validate_leaf_result(
                    result,
                    expected_candidate_ref=candidate_dict(candidate),
                    expected_stage=stage,
                )
                manifest = normalize_file_manifest(expected_files)
                if normalized_input["scope"]["files_expected"] != manifest:
                    raise LeafProtocolError(
                        f"{stage} scope differs from the authoritative diff manifest"
                    )
                normalized_tool_calls, normalized_wall_time = (
                    normalize_resource_usage(tool_calls, wall_time)
                )
                input_drift = False
                if ticket["leaf_handoff"] is not None:
                    previous_identity = verification_checkpoint_identity(
                        ticket["leaf_handoff"]
                    )
                    current_identity = verification_checkpoint_identity(
                        normalized_input
                    )
                    input_drift = (
                        stage == "verify"
                        and previous_identity != current_identity
                        and (
                            previous_identity is not None
                            or current_identity is not None
                        )
                    )
                    if input_drift:
                        ticket["leaf_handoff"] = None
                        ticket["leaf_results"].pop("verify", None)
                        ticket["leaf_progress_events"] = [
                            event
                            for event in ticket["leaf_progress_events"]
                            if event.get("stage") != "verify"
                        ]
                        ticket["leaf_budget"]["reservations"]["verify"][
                            "complete"
                        ] = False
                    else:
                        progression = validate_handoff_progression(
                            ticket["leaf_handoff"], normalized_input
                        )
                        if progression == "duplicate":
                            delta = ticket["leaf_progress_events"][-1][
                                "resource_delta"
                            ]
                            if delta != {
                                "interactions": 1,
                                "tool_calls": normalized_tool_calls,
                                "wall_time": normalized_wall_time,
                            }:
                                raise LeafProtocolError(
                                    "duplicate leaf handoff changed resource deltas"
                                )
                            return copy.deepcopy(result)
                budget, handoff, progress = normalize_leaf_result(
                    self.ledger,
                    ticket["leaf_budget"],
                    normalized_input,
                    expected_candidate_ref=candidate_dict(candidate),
                    expected_stage=stage,
                    tool_calls=normalized_tool_calls,
                    wall_time=normalized_wall_time,
                )
            except LeafProtocolError as error:
                raise TransitionError(str(error)) from error
            ticket["leaf_budget"] = budget
            ticket["leaf_handoff"] = handoff
            ticket["leaf_progress_events"].append(progress)
            self._event(
                "leaf-result-recorded",
                ticket_id,
                stage=stage,
                complete=handoff["complete"],
                progress_phase=handoff["progress_phase"],
                stop_reason=handoff["stop_reason"],
                candidate_digest=candidate.digest,
                interaction=budget["interactions_consumed"],
                tool_calls=progress["resource_delta"]["tool_calls"],
                wall_time=progress["resource_delta"]["wall_time"],
                input_drift=input_drift,
            )
            return copy.deepcopy(handoff)

    def leaf_continuation(
        self, ticket_id: str, candidate: CandidateRef
    ) -> dict[str, Any] | None:
        ticket = self._ticket(ticket_id)
        self._require_candidate(ticket, candidate)
        handoff = ticket["leaf_handoff"]
        if handoff is None:
            return None
        try:
            return continuation_context(
                handoff,
                candidate_ref=candidate_dict(candidate),
                stage=ticket["stage"],
            )
        except LeafProtocolError as error:
            raise TransitionError(str(error)) from error

    def review_continuation(
        self, ticket_id: str, candidate: CandidateRef
    ) -> dict[str, Any] | None:
        return self.leaf_continuation(ticket_id, candidate)

    def _open_gate(
        self,
        ticket_id: str | None,
        *,
        category: str,
        scope: str,
        reason: str,
        kind: str,
        lifecycle_request: dict[str, str] | None = None,
        details: dict[str, Any] | None = None,
    ) -> str:
        if scope not in {"ticket", "run"}:
            raise TransitionError("gate scope must be ticket or run")
        ordinal = len(self.ledger["gates"]) + 1
        owner = ticket_id or "run"
        gate_id = f"gate:{owner}:{kind}:{ordinal}"
        gate = {
            "gate_id": gate_id,
            "ticket_id": ticket_id,
            "category": category,
            "scope": scope,
            "reason": reason,
            "kind": kind,
            "state": "open",
            "actor": None,
            "evidence": None,
        }
        if lifecycle_request is not None:
            gate["lifecycle_request"] = copy.deepcopy(lifecycle_request)
        if details is not None:
            gate["details"] = copy.deepcopy(details)
        if ticket_id is not None:
            ticket = self._ticket(ticket_id)
            gate["resume_state"] = ticket["state"]
            gate["resume_stage"] = ticket["stage"]
            ticket["state"] = "gated"
        self.ledger["gates"][gate_id] = gate
        self._event("gate-opened", ticket_id, gate_id=gate_id, scope=scope)
        return gate_id

    def open_gate(
        self,
        ticket_id: str | None,
        category: str,
        *,
        scope: str,
        reason: str,
        details: dict[str, Any] | None = None,
    ) -> str:
        with self._transaction():
            gate_id = self._open_gate(
                ticket_id,
                category=category,
                scope=scope,
                reason=reason,
                kind="dynamic",
                details=details,
            )
            self._update_run_state()
            return gate_id

    def request_reopen(
        self, ticket_id: str, *, requested_by: str, reason: str
    ) -> str:
        with self._transaction():
            ticket = self._ticket(ticket_id)
            if (
                ticket.get("disposition") not in {"on-hold", "canceled"}
                or ticket["state"] != "pending"
            ):
                raise TransitionError(
                    "reopen request requires an on-hold or canceled pending ticket"
                )
            if not requested_by or not reason:
                raise TransitionError("reopen request requires requester and reason")
            if any(
                gate.get("kind") == "reopen"
                and gate.get("ticket_id") == ticket_id
                and gate.get("state") in {"open", "passed"}
                and not gate.get("consumed_by_transition_id")
                for gate in self.ledger["gates"].values()
            ):
                raise TransitionError("ticket already has an active reopen request")
            request = {
                "ticket_id": ticket_id,
                "target_disposition": "open",
                "reason": reason,
                "requested_by": requested_by,
            }
            gate_id = self._open_gate(
                ticket_id,
                category="human",
                scope="ticket",
                reason=f"ticket reopen requested: {reason}",
                kind="reopen",
                lifecycle_request=request,
            )
            self._update_run_state()
            return gate_id

    def approve_gate(self, gate_id: str, *, actor: str, evidence: str) -> None:
        with self._transaction():
            if not actor or not evidence:
                raise TransitionError("gate approval requires actor and evidence")
            try:
                gate = self.ledger["gates"][gate_id]
            except KeyError as error:
                raise TransitionError(f"unknown gate {gate_id!r}") from error
            if gate["state"] != "open":
                raise TransitionError(f"gate {gate_id!r} is not open")
            gate["state"] = "passed"
            gate["actor"] = actor
            gate["evidence"] = evidence
            ticket_id = gate["ticket_id"]
            if ticket_id is not None:
                other_open = [
                    item
                    for other_id, item in self.ledger["gates"].items()
                    if other_id != gate_id
                    and item["ticket_id"] == ticket_id
                    and item["state"] == "open"
                ]
                if not other_open:
                    ticket = self._ticket(ticket_id)
                    resume_state = gate["resume_state"]
                    resume_stage = gate["resume_stage"]
                    prepared = ticket.get("delivery", {}).get(
                        "reconcile-prepare"
                    )
                    pending_reconciliation_resume = False
                    if (
                        isinstance(prepared, dict)
                        and ticket["state"] == "gated"
                        and prepared.get("pending_resume_state")
                        in {"active", "verified"}
                    ):
                        resume_state = prepared["pending_resume_state"]
                        resume_stage = prepared.get("pending_resume_stage")
                        pending_reconciliation_resume = True
                    active_ticket = self._active_ticket_id()
                    if (
                        resume_state == "active"
                        and active_ticket is not None
                        and active_ticket != ticket_id
                    ):
                        ticket["state"] = "pending"
                        ticket["resume_pending"] = True
                    else:
                        ticket["state"] = resume_state
                    ticket["stage"] = resume_stage
                    if pending_reconciliation_resume:
                        prepared.pop("pending_resume_state")
                        prepared.pop("pending_resume_stage")
            self._event("gate-passed", ticket_id, gate_id=gate_id, actor=actor)
            self._update_run_state()

    def refresh_gate_reason(self, gate_id: str, *, reason: str) -> bool:
        with self._transaction():
            if not reason:
                raise TransitionError("gate reason must be non-empty")
            try:
                gate = self.ledger["gates"][gate_id]
            except KeyError as error:
                raise TransitionError(f"unknown gate {gate_id!r}") from error
            if gate["state"] != "open":
                raise TransitionError(f"gate {gate_id!r} is not open")
            if gate["reason"] == reason:
                return False
            gate["reason"] = reason
            self._event(
                "gate-refreshed",
                gate["ticket_id"],
                gate_id=gate_id,
                reason=reason,
            )
            return True

    def _provider_delivery_gate_open(self, ticket_id: str) -> bool:
        return any(
            gate["ticket_id"] == ticket_id
            and gate["state"] == "open"
            and gate["category"]
            in {
                "provider-environment",
                "provider-pr",
                "delivery-pr-body",
                "provider-merge",
            }
            and gate["resume_state"] in {"verified", "pr-open"}
            for gate in self.ledger["gates"].values()
        )

    def record_finalization_effect(self, ticket_id: str, effect: str) -> bool:
        with self._transaction():
            ticket = self._ticket(ticket_id)
            if (
                ticket["state"] not in {"verified", "pr-open", "integrated"}
                and not self._provider_delivery_gate_open(ticket_id)
            ):
                raise TransitionError(
                    "finalization requires a validated terminal stage result"
                )
            candidate = ticket["candidate_ref"]
            key_source = json.dumps(
                [self.ledger["run_id"], ticket_id, effect, candidate],
                sort_keys=True,
                separators=(",", ":"),
            )
            key = hashlib.sha256(key_source.encode("utf-8")).hexdigest()
            if key in self.ledger["effects"]:
                return False
            self.ledger["effects"][key] = {
                "ticket_id": ticket_id,
                "effect": effect,
                "state": "applied",
            }
            if effect in {
                "move-done-and-stage",
                "move-done-and-summarize-external",
            }:
                ticket["current_source_relative_path"] = (
                    "done/" + ticket["current_source_relative_path"].rsplit("/", 1)[-1]
                )
                self._complete_ticket_lifecycle(ticket)
            self._event("effect-applied", ticket_id, effect=effect, idempotency_key=key)
            return True

    def record_delivery_metadata(
        self, ticket_id: str, step: str, data: dict[str, Any]
    ) -> None:
        with self._transaction():
            ticket = self._ticket(ticket_id)
            provider_gated = (
                ticket["state"] == "gated"
                and self._provider_delivery_gate_open(ticket_id)
            )
            progress_only = step == "result" and ticket["state"] in {
                "active",
                "gated",
            }
            reconciliation_gated = (
                ticket["state"] == "gated"
                and step.startswith("repository-reconciliation-")
                and any(
                    gate["ticket_id"] == ticket_id
                    and gate["state"] == "open"
                    and gate["category"]
                    in {"stack-reconciliation", "stack-reconciliation-recovery"}
                    for gate in self.ledger["gates"].values()
                )
            )
            if (
                ticket["state"] not in {"verified", "pr-open", "integrated"}
                and not provider_gated
                and not progress_only
                and not reconciliation_gated
            ):
                raise TransitionError(
                    "delivery metadata requires a validated terminal result"
                )
            normalized = copy.deepcopy(data)
            if ticket["delivery"].get(step) == normalized:
                return
            ticket["delivery"][step] = normalized
            self._event("delivery-recorded", ticket_id, step=step)

    def reset_stale_delivery_preparation(
        self, ticket_id: str, candidate: CandidateRef
    ) -> bool:
        """Archive and clear preparation bound to another semantic candidate."""

        with self._transaction():
            ticket = self._ticket(ticket_id)
            if ticket["state"] not in {"active", "verified", "pr-open", "gated"}:
                raise TransitionError(
                    "stale delivery preparation reset requires a deliverable ticket"
                )
            candidate.validate()
            if candidate.ticket_digest != ticket["ticket_digest"]:
                raise TransitionError(
                    "stale delivery preparation candidate belongs to another ticket"
                )
            delivery = ticket["delivery"]
            prepared = delivery.get("prepared")
            if prepared is None:
                return False
            try:
                if not isinstance(prepared, dict):
                    raise CandidateContractError(
                        "prepared delivery must be an object"
                    )
                old_candidate = semantic_candidate(
                    prepared.get("candidate_ref")
                )
                old_document = old_candidate.as_dict()
            except CandidateContractError as error:
                raise TransitionError(
                    "stale delivery preparation is malformed"
                ) from error
            if old_candidate.ticket_digest != ticket["ticket_digest"]:
                raise TransitionError(
                    "stale delivery preparation is malformed"
                )
            new_document = asdict(candidate)
            if old_document == new_document:
                return False
            receipts = {
                step: copy.deepcopy(delivery[step])
                for step in STALE_DELIVERY_PREPARATION_STEPS
                if step in delivery
            }
            history = delivery.setdefault("preparation-history", [])
            if not isinstance(history, list):
                raise TransitionError(
                    "stale delivery preparation history is malformed"
                )
            history.append(
                {
                    "schema": 1,
                    "old_candidate_ref": old_document,
                    "new_candidate_ref": new_document,
                    "artifact_generation": ticket["artifact_generation"],
                    "receipts": receipts,
                }
            )
            for step in receipts:
                delivery.pop(step)
            self._event(
                "stale-delivery-preparation-reset",
                ticket_id,
                old_candidate_ref=old_document,
                new_candidate_ref=new_document,
                artifact_generation=ticket["artifact_generation"],
                cleared_steps=list(receipts),
            )
            return True

    def record_delivery_candidate(
        self, ticket_id: str, candidate: CandidateRef
    ) -> None:
        with self._transaction():
            ticket = self._ticket(ticket_id)
            if ticket["state"] != "verified":
                raise TransitionError(
                    "delivery CandidateRef requires verified ticket state"
                )
            candidate.validate()
            if ticket["delivery_candidate_ref"] == asdict(candidate):
                return
            ticket["delivery_candidate_ref"] = asdict(candidate)
            ticket["merge_authorization"] = None
            self._event(
                "delivery-candidate-recorded",
                ticket_id,
                candidate_digest=candidate.digest,
            )

    def seal_revalidated_reconciliation_candidate(
        self,
        ticket_id: str,
        candidate: CandidateRef,
        *,
        expected_old_local_head: str,
        new_local_head: str,
    ) -> None:
        with self._transaction():
            ticket = self._ticket(ticket_id)
            if ticket["state"] != "verified" or ticket["stage"] is not None:
                raise TransitionError(
                    "reconciliation candidate sealing requires verified state"
                )
            candidate.validate()
            candidate_document = asdict(candidate)
            if ticket["candidate_ref"] != candidate_document:
                raise TransitionError(
                    "reconciliation candidate sealing requires the verified CandidateRef"
                )
            if ticket["delivery_candidate_ref"] == candidate_document:
                return
            delivery = ticket["delivery"]
            prepared = delivery.get("reconcile-prepare")
            if not isinstance(prepared, dict):
                raise TransitionError(
                    "reconciliation candidate sealing requires prepared lineage"
                )
            if (
                prepared.get("new_head") != expected_old_local_head
                or prepared.get("new_delivery_ref")
                != ticket["delivery_candidate_ref"]
                or prepared.get("target_base", {}).get("tree_oid")
                != candidate.base_tree_oid
                or not all((expected_old_local_head, new_local_head))
            ):
                raise TransitionError(
                    "reconciliation candidate sealing contradicts prepared lineage"
                )
            stale_render = {
                step: copy.deepcopy(delivery[step])
                for step in (
                    "reconcile-pr-body-request",
                    "reconcile-pr-body",
                )
                if step in delivery
            }
            history = delivery.setdefault(
                "reconcile-revalidation-history", []
            )
            if not isinstance(history, list):
                raise TransitionError(
                    "reconciliation revalidation history is malformed"
                )
            history.append(
                {
                    "schema": 1,
                    "prepare": copy.deepcopy(prepared),
                    "delivery_candidate_ref": copy.deepcopy(
                        ticket["delivery_candidate_ref"]
                    ),
                    "new_candidate_ref": copy.deepcopy(candidate_document),
                    "old_local_head": expected_old_local_head,
                    "new_local_head": new_local_head,
                    "render_receipts": stale_render,
                }
            )
            rebound = copy.deepcopy(prepared)
            rebound.update(
                {
                    "result": "revalidated",
                    "new_semantic_ref": copy.deepcopy(candidate_document),
                    "new_delivery_ref": copy.deepcopy(candidate_document),
                    "new_head": new_local_head,
                    "candidate_ref": copy.deepcopy(candidate_document),
                    "artifact_generation_after": ticket["artifact_generation"],
                }
            )
            delivery["reconcile-prepare"] = rebound
            for step in stale_render:
                delivery.pop(step)
            ticket["delivery_candidate_ref"] = copy.deepcopy(candidate_document)
            ticket["merge_authorization"] = None
            self._event(
                "reconciliation-candidate-sealed",
                ticket_id,
                old_local_head=expected_old_local_head,
                new_local_head=new_local_head,
                candidate_digest=candidate.digest,
                artifact_generation=ticket["artifact_generation"],
            )

    def prepare_delivery_revalidation(
        self, ticket_id: str, candidate: CandidateRef
    ) -> None:
        with self._transaction():
            ticket = self._ticket(ticket_id)
            if ticket["state"] != "verified":
                raise TransitionError(
                    "delivery preparation requires verified ticket state"
                )
            candidate.validate()
            ticket["candidate_ref"] = asdict(candidate)
            ticket["delivery_candidate_ref"] = asdict(candidate)
            ticket["state"] = "active"
            ticket["stage"] = "review"
            ticket["validated_stages"] = ["implement", "simplify"]
            ticket["leaf_budget"] = new_leaf_budget(self.ledger)
            self._invalidate_leaf_artifacts(ticket)
            ticket["artifact_generation"] += 1
            ticket["merge_authorization"] = None
            ticket.pop("docs_only", None)
            ticket["delivery"]["prepared"] = {
                "candidate_ref": asdict(candidate),
                "artifact_generation": ticket["artifact_generation"],
            }
            for stale_step in (
                "pr-body-request",
                "pr-body",
                "pr",
                "provider-simulation",
                "result",
            ):
                ticket["delivery"].pop(stale_step, None)
            self._event(
                "delivery-revalidation-required",
                ticket_id,
                candidate_digest=candidate.digest,
                artifact_generation=ticket["artifact_generation"],
            )
            self._update_run_state()

    def prepare_reconciliation_delivery_revalidation(
        self, ticket_id: str, candidate: CandidateRef
    ) -> None:
        with self._transaction():
            ticket = self._ticket(ticket_id)
            if ticket["state"] != "verified":
                raise TransitionError(
                    "reconciliation delivery revalidation requires verified state"
                )
            candidate.validate()
            candidate_document = asdict(candidate)
            if ticket["candidate_ref"] == candidate_document:
                raise TransitionError(
                    "reconciliation delivery revalidation requires candidate drift"
                )
            prepared = ticket["delivery"].get("reconcile-prepare")
            if (
                not isinstance(prepared, dict)
                or prepared.get("new_delivery_ref")
                != ticket["delivery_candidate_ref"]
                or prepared.get("target_base", {}).get("tree_oid")
                != candidate.base_tree_oid
            ):
                raise TransitionError(
                    "reconciliation delivery revalidation contradicts prepared lineage"
                )
            ticket["candidate_ref"] = candidate_document
            ticket["state"] = "active"
            ticket["stage"] = "review"
            ticket["validated_stages"] = ["implement", "simplify"]
            ticket["leaf_budget"] = new_leaf_budget(self.ledger)
            self._invalidate_leaf_artifacts(ticket)
            ticket["artifact_generation"] += 1
            ticket["merge_authorization"] = None
            ticket.pop("docs_only", None)
            self._event(
                "reconciliation-delivery-revalidation-required",
                ticket_id,
                candidate_digest=candidate.digest,
                artifact_generation=ticket["artifact_generation"],
            )
            self._update_run_state()

    def prepare_reconciliation(
        self,
        ticket_id: str,
        observed_candidate: CandidateRef,
        *,
        old_head: str,
        new_head: str,
        base_branch: str,
        base_sha: str,
        base_tree_oid: str,
        expected_remote_sha: str,
        refresh_intent: dict[str, object] | None = None,
        replacement_intent: dict[str, object] | None = None,
        resolved_gate_ids: list[str] | None = None,
        gate_actor: str | None = None,
        gate_evidence: str | None = None,
    ) -> bool:
        with self._transaction():
            ticket = self._ticket(ticket_id)
            resolved_gates = list(resolved_gate_ids or [])
            if any(
                not isinstance(gate_id, str) or not gate_id
                for gate_id in resolved_gates
            ) or len(set(resolved_gates)) != len(resolved_gates):
                raise TransitionError(
                    "resolved reconciliation gate IDs are invalid"
                )
            if resolved_gates and (not gate_actor or not gate_evidence):
                raise TransitionError(
                    "resolved reconciliation gates require actor and evidence"
                )
            for gate_id in resolved_gates:
                gate = self.ledger["gates"].get(gate_id)
                if (
                    not isinstance(gate, dict)
                    or gate.get("ticket_id") != ticket_id
                    or gate.get("category")
                    not in RECONCILIATION_CONDITION_GATE_CATEGORIES
                    or gate.get("state") != "passed"
                    or gate.get("actor") != gate_actor
                    or gate.get("evidence") != gate_evidence
                ):
                    raise TransitionError(
                        "resolved reconciliation gate evidence contradicts the ledger"
                    )
            refreshing = refresh_intent is not None or replacement_intent is not None
            if (refresh_intent is None) != (replacement_intent is None):
                raise TransitionError(
                    "reconciliation refresh requires both old and replacement intents"
                )
            expected_states = {"verified", "gated"} if refreshing else {
                "pr-open",
                "gated",
            }
            if ticket["state"] not in expected_states or not ticket["pr"]:
                raise TransitionError(
                    "reconciliation preparation requires an open PR"
                )
            if ticket["pr"]["head_sha"] != old_head:
                raise TransitionError("PR head changed before reconciliation")
            observed_candidate.validate()
            if observed_candidate.base_tree_oid != base_tree_oid:
                raise TransitionError(
                    "reconciled candidate contradicts the Git-resolved base tree"
                )
            if not all((new_head, base_branch, base_sha, expected_remote_sha)):
                raise TransitionError("reconciliation lineage fields are required")
            delivery = ticket["delivery"]
            preparation_refresh = delivery.get(PREPARATION_REFRESH_STEP)
            if preparation_refresh is not None:
                if refreshing:
                    raise TransitionError(
                        "prepared and pre-prepare target refreshes cannot overlap"
                    )
                prior_intent = delivery.get("reconcile-intent")
                if not isinstance(prior_intent, dict):
                    raise TransitionError(
                        "pre-prepare target refresh requires its prior intent"
                    )
                try:
                    replacement = validate_preparation_refresh(
                        preparation_refresh, prior_intent
                    )
                except ReconciliationIntentError as error:
                    raise TransitionError(str(error)) from error
                if any(
                    step in delivery
                    for step in ("reconcile-push", "reconcile-retarget")
                ):
                    raise TransitionError(
                        "reconciliation target cannot refresh after provider mutation"
                    )
                target = replacement["target_base"]
                if (
                    replacement.get("branch") != ticket["pr"]["branch"]
                    or replacement.get("old_head") != old_head
                    or replacement.get("expected_remote_sha")
                    != expected_remote_sha
                    or target.get("branch") != base_branch
                    or target.get("sha") != base_sha
                    or target.get("tree_oid") != base_tree_oid
                ):
                    raise TransitionError(
                        "pre-prepare target refresh contradicts Git readback"
                    )
                refresh_history = delivery.setdefault(
                    PREPARATION_REFRESH_HISTORY_STEP, []
                )
                if not isinstance(refresh_history, list):
                    raise TransitionError(
                        "pre-prepare target refresh history is malformed"
                    )
                refresh_history.append(
                    {
                        "schema": 1,
                        "refresh": copy.deepcopy(preparation_refresh),
                        "result": "consumed",
                    }
                )
                delivery["reconcile-intent"] = copy.deepcopy(replacement)
                delivery.pop(PREPARATION_REFRESH_STEP)
            if refreshing:
                assert refresh_intent is not None
                assert replacement_intent is not None
                prior_intent = delivery.get("reconcile-intent")
                prior_prepare = delivery.get("reconcile-prepare")
                if (
                    delivery.get("reconcile-refresh-intent") != refresh_intent
                    or not isinstance(prior_intent, dict)
                    or not isinstance(prior_prepare, dict)
                ):
                    raise TransitionError(
                        "reconciliation refresh lineage is incomplete"
                    )
                if any(
                    step in delivery
                    for step in ("reconcile-push", "reconcile-retarget")
                ):
                    raise TransitionError(
                        "reconciliation target cannot refresh after provider mutation"
                    )
                if (
                    refresh_intent.get("old_intent") != prior_intent
                    or refresh_intent.get("old_prepare") != prior_prepare
                    or refresh_intent.get("replacement_intent")
                    != replacement_intent
                    or refresh_intent.get("old_local_head")
                    != prior_prepare.get("new_head")
                    or refresh_intent.get("new_target", {}).get("sha")
                    != base_sha
                    or refresh_intent.get("new_target", {}).get("tree_oid")
                    != base_tree_oid
                ):
                    raise TransitionError(
                        "reconciliation refresh intent contradicts prepared state"
                    )
                attempt_history = delivery.setdefault(
                    "reconcile-attempt-history", []
                )
                if not isinstance(attempt_history, list):
                    raise TransitionError(
                        "reconciliation attempt history is malformed"
                    )
                stale_render = {
                    step: copy.deepcopy(delivery[step])
                    for step in (
                        "reconcile-pr-body-request",
                        "reconcile-pr-body",
                    )
                    if step in delivery
                }
                attempt_history.append(
                    {
                        "schema": 1,
                        "intent": copy.deepcopy(prior_intent),
                        "prepare": copy.deepcopy(prior_prepare),
                        "refresh_intent": copy.deepcopy(refresh_intent),
                        "render_receipts": stale_render,
                    }
                )
                delivery["reconcile-intent"] = copy.deepcopy(
                    replacement_intent
                )
                delivery.pop("reconcile-refresh-intent", None)
                for step in stale_render:
                    delivery.pop(step, None)
            old_candidate = copy.deepcopy(ticket["candidate_ref"])
            old_delivery_candidate = copy.deepcopy(
                ticket["delivery_candidate_ref"]
            )
            if not isinstance(old_delivery_candidate, dict):
                raise TransitionError(
                    "reconciliation requires a semantic delivery-tree binding"
                )
            old_generation = ticket["artifact_generation"]
            observed_document = asdict(observed_candidate)
            semantic_identity_fields = (
                "contract_version",
                "ticket_digest",
                "base_tree_oid",
            )
            equivalent = all(
                old_candidate[field] == observed_document[field]
                for field in semantic_identity_fields
            ) and old_delivery_candidate == observed_document
            new_candidate = old_candidate if equivalent else observed_document
            ticket["candidate_ref"] = copy.deepcopy(new_candidate)
            ticket["delivery_candidate_ref"] = observed_document
            superseded_receipts = {
                step: copy.deepcopy(ticket["delivery"][step])
                for step in HEAD_BOUND_MERGE_DELIVERY_STEPS
                if step in ticket["delivery"]
            }
            old_authorization = copy.deepcopy(ticket["merge_authorization"])
            if superseded_receipts or old_authorization is not None:
                history = ticket["delivery"].setdefault(
                    "merge-lineage-history", []
                )
                if not isinstance(history, list):
                    raise TransitionError("merge lineage history is malformed")
                history.append(
                    {
                        "schema": 1,
                        "old_head": old_head,
                        "new_head": new_head,
                        "receipts": superseded_receipts,
                        "merge_authorization": old_authorization,
                    }
                )
                for step in superseded_receipts:
                    ticket["delivery"].pop(step)
            ticket["merge_authorization"] = None
            ticket["delivery"]["reconcile-prepare"] = {
                "schema": 1,
                "result": "equivalent" if equivalent else "invalidated",
                "old_semantic_ref": old_candidate,
                "new_semantic_ref": copy.deepcopy(new_candidate),
                "old_delivery_ref": old_delivery_candidate,
                "new_delivery_ref": observed_document,
                "old_head": old_head,
                "new_head": new_head,
                "target_base": {
                    "branch": base_branch,
                    "sha": base_sha,
                    "tree_oid": base_tree_oid,
                },
                "expected_remote_sha": expected_remote_sha,
                "candidate_ref": copy.deepcopy(new_candidate),
                "artifact_generation_before": old_generation,
                "artifact_generation_after": (
                    old_generation if equivalent else old_generation + 1
                ),
                "resolved_gate_ids": resolved_gates,
                "gate_actor": gate_actor if resolved_gates else None,
                "gate_evidence": gate_evidence if resolved_gates else None,
            }
            if equivalent:
                ticket["state"] = "verified"
                ticket["stage"] = None
                if refreshing:
                    self._event(
                        "reconciliation-target-refreshed",
                        ticket_id,
                        old_head=old_head,
                        new_head=new_head,
                        old_target_sha=refresh_intent["old_target"]["sha"],
                        new_target_sha=base_sha,
                        candidate_digest=CandidateRef(**new_candidate).digest,
                        artifact_generation=ticket["artifact_generation"],
                        semantic_change=False,
                        resolved_gate_ids=resolved_gates,
                    )
                else:
                    self._event(
                        "reconciliation-equivalent",
                        ticket_id,
                        old_head=old_head,
                        new_head=new_head,
                        candidate_digest=CandidateRef(**new_candidate).digest,
                        artifact_generation=ticket["artifact_generation"],
                        resolved_gate_ids=resolved_gates,
                    )
            else:
                ticket["state"] = "active"
                ticket["stage"] = "review"
                ticket["validated_stages"] = ["implement", "simplify"]
                ticket["leaf_budget"] = new_leaf_budget(self.ledger)
                self._invalidate_leaf_artifacts(ticket)
                ticket["artifact_generation"] += 1
                ticket.pop("docs_only", None)
                if refreshing:
                    self._event(
                        "reconciliation-target-refreshed",
                        ticket_id,
                        old_head=old_head,
                        new_head=new_head,
                        old_target_sha=refresh_intent["old_target"]["sha"],
                        new_target_sha=base_sha,
                        candidate_digest=observed_candidate.digest,
                        artifact_generation=ticket["artifact_generation"],
                        semantic_change=True,
                        resolved_gate_ids=resolved_gates,
                    )
                else:
                    self._event(
                        "reconciliation-revalidation-required",
                        ticket_id,
                        old_head=old_head,
                        new_head=new_head,
                        candidate_digest=observed_candidate.digest,
                        artifact_generation=ticket["artifact_generation"],
                        resolved_gate_ids=resolved_gates,
                    )
            remaining_open_gates = any(
                gate.get("ticket_id") == ticket_id
                and gate.get("state") == "open"
                for gate in self.ledger["gates"].values()
            )
            if remaining_open_gates:
                prepared = ticket["delivery"]["reconcile-prepare"]
                prepared["pending_resume_state"] = (
                    "verified" if equivalent else "active"
                )
                prepared["pending_resume_stage"] = (
                    None if equivalent else "review"
                )
                ticket["state"] = "gated"
                ticket["stage"] = None
            self._update_run_state()
            return equivalent

    def complete_reconciliation(
        self,
        ticket_id: str,
        *,
        expected_old: str,
        new_head: str,
        base_branch: str,
    ) -> None:
        with self._transaction():
            ticket = self._ticket(ticket_id)
            prepared = ticket["delivery"].get("reconcile-prepare")
            if ticket["state"] != "verified" or not ticket["pr"] or not prepared:
                raise TransitionError(
                    "reconciliation publication requires revalidated PR state"
                )
            if (
                ticket["pr"]["head_sha"] != expected_old
                or prepared.get("old_head") != expected_old
                or prepared.get("new_head") != new_head
                or prepared.get("target_base", {}).get("branch") != base_branch
            ):
                raise TransitionError(
                    "reconciliation publication contradicts prepared state"
                )
            ticket["pr"]["head_sha"] = new_head
            lineage = ticket.get("delivery_lineage")
            if not isinstance(lineage, dict):
                raise TransitionError("reconciliation requires delivery lineage")
            lineage["head_sha"] = new_head
            lineage["base_branch"] = base_branch
            lineage["base_sha"] = prepared["target_base"]["sha"]
            ticket["state"] = "pr-open"
            ticket["merge_authorization"] = None
            ticket["delivery"]["result"] = {
                "phase": "readback",
                "result": "pr-open",
            }
            self._event(
                "pr-head-updated",
                ticket_id,
                expected_old=expected_old,
                new=new_head,
                base=base_branch,
            )
            self._update_run_state()

    def record_pr(
        self,
        ticket_id: str,
        *,
        provider: str,
        pr_id: str,
        head_sha: str,
        base_branch: str,
        base_sha: str,
        branch: str | None = None,
    ) -> None:
        with self._transaction():
            ticket = self._ticket(ticket_id)
            if ticket["state"] != "verified":
                raise TransitionError("PR recording requires verified finalization state")
            if not all((provider, pr_id, head_sha)):
                raise TransitionError("provider, pr_id, and head_sha are required")
            if ticket["delivery_candidate_ref"] is None:
                ticket["delivery_candidate_ref"] = copy.deepcopy(
                    ticket["candidate_ref"]
                )
            ticket["pr"] = {
                "provider": provider,
                "pr_id": pr_id,
                "head_sha": head_sha,
                "branch": branch
                or f"ticket-autopilot/{self.ledger['run_id']}/{ticket_id}",
            }
            ticket["delivery_lineage"] = DeliveryLineage(
                provider=provider,
                pr_id=pr_id,
                branch=ticket["pr"]["branch"],
                base_branch=base_branch,
                base_sha=base_sha,
                head_sha=head_sha,
            ).as_dict()
            ticket["state"] = "pr-open"
            self._event("pr-opened", ticket_id, provider=provider, pr_id=pr_id)
            self._update_run_state()

    def update_pr_head(self, ticket_id: str, *, expected_old: str, new: str) -> None:
        with self._transaction():
            ticket = self._ticket(ticket_id)
            if ticket["state"] != "pr-open" or not ticket["pr"]:
                raise TransitionError("PR head update requires an open PR")
            if ticket["pr"]["head_sha"] != expected_old:
                raise TransitionError("PR head changed before reconciliation")
            if not new:
                raise TransitionError("new PR head SHA is required")
            ticket["pr"]["head_sha"] = new
            lineage = ticket.get("delivery_lineage")
            if not isinstance(lineage, dict):
                raise TransitionError("PR head update requires delivery lineage")
            lineage["head_sha"] = new
            ticket["merge_authorization"] = None
            self._event(
                "pr-head-updated",
                ticket_id,
                expected_old=expected_old,
                new=new,
            )

    def authorize_merge(
        self,
        ticket_id: str,
        *,
        actor: str,
        head_sha: str,
        evidence: str,
        mode: str = "runner",
    ) -> None:
        with self._transaction():
            ticket = self._ticket(ticket_id)
            if ticket["state"] != "pr-open" or not ticket["pr"]:
                raise TransitionError("merge authorization requires an open PR")
            if ticket["pr"]["head_sha"] != head_sha:
                raise TransitionError("merge authorization head SHA is stale")
            if not actor or not evidence:
                raise TransitionError("merge authorization requires actor and evidence")
            if mode not in {"runner", "external", "autonomous"}:
                raise TransitionError("merge authorization mode is invalid")
            ticket["merge_authorization"] = {
                "actor": actor,
                "head_sha": head_sha,
                "evidence": evidence,
                "mode": mode,
            }
            self._event(
                "merge-authorized",
                ticket_id,
                actor=actor,
                head_sha=head_sha,
                mode=mode,
            )
            self._update_run_state()

    def adopt_equivalent_external_head(
        self,
        ticket_id: str,
        receipt: dict[str, Any],
    ) -> tuple[dict[str, Any], bool]:
        with self._transaction():
            ticket = self._ticket(ticket_id)
            current_pr = ticket.get("pr")
            lineage = ticket.get("delivery_lineage")
            if not isinstance(current_pr, dict) or not isinstance(lineage, dict):
                raise TransitionError(
                    "equivalent-head adoption requires PR delivery lineage"
                )
            existing = ticket.get("delivery", {}).get(
                EQUIVALENT_HEAD_DELIVERY_STEP
            )
            if existing is not None:
                try:
                    normalized = validate_equivalent_head_receipt(
                        self.ledger, ticket_id, existing
                    )
                except EquivalentHeadError as error:
                    raise TransitionError(str(error)) from error
                if normalized != receipt:
                    raise TransitionError(
                        "equivalent-head adoption receipt is contradictory"
                    )
                return copy.deepcopy(normalized), True
            if ticket["state"] not in {"pr-open", "gated"}:
                raise TransitionError(
                    "equivalent-head adoption requires an open PR or provider gate"
                )
            if current_pr.get("head_sha") != receipt.get("recorded_head_sha"):
                raise TransitionError("equivalent-head recorded PR head is stale")
            if lineage.get("head_sha") != receipt.get("recorded_head_sha"):
                raise TransitionError(
                    "equivalent-head recorded delivery lineage is stale"
                )
            if lineage.get("base_sha") != receipt.get("recorded_base_sha"):
                raise TransitionError("equivalent-head recorded base is stale")
            observed_head = receipt.get("observed_head_sha")
            current_pr["head_sha"] = observed_head
            lineage["head_sha"] = observed_head
            ticket["merge_authorization"] = None
            ticket["delivery"][EQUIVALENT_HEAD_DELIVERY_STEP] = copy.deepcopy(
                receipt
            )
            try:
                normalized = validate_equivalent_head_receipt(
                    self.ledger, ticket_id, receipt
                )
            except EquivalentHeadError as error:
                raise TransitionError(str(error)) from error
            self._update_run_state()
            self._event(
                "external-head-equivalent",
                ticket_id,
                recorded_head=receipt["recorded_head_sha"],
                observed_head=receipt["observed_head_sha"],
                receipt_digest=canonical_digest(normalized),
            )
            return copy.deepcopy(normalized), False

    def record_external_integration(
        self,
        ticket_id: str,
        *,
        actor: str,
        head_sha: str,
        evidence: str,
        provider_observation: dict[str, Any],
        terminal_proof: dict[str, Any],
    ) -> tuple[dict[str, Any], bool]:
        with self._transaction():
            ticket = self._ticket(ticket_id)
            current_pr = ticket.get("pr")
            if not current_pr:
                raise TransitionError(
                    "external merge reconciliation requires a recorded PR"
                )
            if not actor or not evidence:
                raise TransitionError(
                    "external merge reconciliation requires actor and evidence"
                )
            if current_pr.get("provider") != self.ledger["provider"]:
                raise TransitionError(
                    "external merge reconciliation provider contradicts the recorded PR"
                )
            if current_pr["head_sha"] != head_sha:
                raise TransitionError(
                    "external merge reconciliation head SHA is stale"
                )
            expected_observation = {
                "schema": 1,
                "provider": self.ledger["provider"],
                "operation": "get-pr-state",
                "evidence_class": "live",
                "observed": True,
                "pr_id": current_pr["pr_id"],
                "head_sha": head_sha,
                "state": "merged",
            }
            if any(
                provider_observation.get(key) != value
                for key, value in expected_observation.items()
            ):
                raise TransitionError(
                    "external merge observation contradicts the recorded PR"
                )
            observation = copy.deepcopy(provider_observation)
            try:
                proof = validate_terminal_integration_proof(
                    self.ledger,
                    ticket_id,
                    terminal_proof,
                    observation,
                    provenance="external-readback",
                )
            except TerminalIntegrationError as error:
                raise TransitionError(str(error)) from error
            authorization = {
                "actor": actor,
                "head_sha": head_sha,
                "evidence": evidence,
                "mode": "external",
            }
            receipt = {
                "schema": 1,
                "mode": "external",
                "provider": self.ledger["provider"],
                "pr_id": current_pr["pr_id"],
                "head_sha": head_sha,
                "actor": actor,
                "evidence": evidence,
                "observation": observation,
                "terminal_proof": proof,
            }
            if ticket["state"] == "integrated":
                if (
                    ticket.get("merge_authorization") != authorization
                    or ticket["delivery"].get("integration") != observation
                    or ticket["delivery"].get("terminal-integration") != proof
                    or ticket["delivery"].get("external-reconciliation") != receipt
                ):
                    raise TransitionError(
                        "integrated ticket has contradictory external reconciliation"
                    )
                return copy.deepcopy(receipt), True
            if ticket["state"] != "pr-open":
                raise TransitionError(
                    "external merge reconciliation requires an open PR"
                )
            if ticket.get("merge_authorization") is not None:
                raise TransitionError(
                    "persisted merge authorization is contradictory"
                )
            ticket["merge_authorization"] = authorization
            ticket["delivery"]["external-reconciliation"] = receipt
            ticket["delivery"]["integration"] = observation
            ticket["delivery"]["terminal-integration"] = proof
            ticket["state"] = "integrated"
            self._complete_ticket_lifecycle(ticket)
            self._update_run_state()
            self._event(
                "external-merge-integrated",
                ticket_id,
                actor=actor,
                head_sha=head_sha,
                provider=self.ledger["provider"],
                pr_id=current_pr["pr_id"],
                terminal_proof_digest=canonical_digest(proof),
            )
            return copy.deepcopy(receipt), False

    def record_integration(
        self,
        ticket_id: str,
        *,
        expected_head_sha: str,
        terminal_proof: dict[str, Any],
    ) -> None:
        with self._transaction():
            ticket = self._ticket(ticket_id)
            authorization = ticket["merge_authorization"]
            if ticket["state"] != "pr-open" or not ticket["pr"]:
                raise TransitionError("integration requires an open PR")
            if ticket["pr"]["head_sha"] != expected_head_sha:
                raise TransitionError("integrated head differs from expected PR head")
            if not authorization or authorization["head_sha"] != expected_head_sha:
                raise TransitionError("current-head human merge authorization is required")
            observation = ticket.get("delivery", {}).get("integration")
            if not isinstance(observation, dict):
                raise TransitionError("integration requires live provider readback")
            try:
                proof = validate_terminal_integration_proof(
                    self.ledger,
                    ticket_id,
                    terminal_proof,
                    observation,
                    provenance="runner-merge",
                )
            except TerminalIntegrationError as error:
                raise TransitionError(str(error)) from error
            ticket["delivery"]["terminal-integration"] = proof
            ticket["state"] = "integrated"
            self._complete_ticket_lifecycle(ticket)
            self._event(
                "ticket-integrated",
                ticket_id,
                head_sha=expected_head_sha,
                terminal_proof_digest=canonical_digest(proof),
            )
            self._update_run_state()

    def _validated_disposition_receipt(
        self,
        ticket_id: str,
        ticket: dict[str, Any],
        receipt: dict[str, Any],
    ) -> dict[str, Any]:
        fields = {
            "schema",
            "transition_id",
            "ticket_id",
            "from_disposition",
            "to_disposition",
            "actor",
            "reason",
            "authority_ref",
            "authority_gate_id",
            "expected_digest",
            "source_relative_path",
            "destination_relative_path",
            "state",
        }
        if not isinstance(receipt, dict) or set(receipt) != fields:
            raise TransitionError("lifecycle receipt shape is invalid")
        if (
            receipt["schema"] != 1
            or receipt["state"] != "applied"
            or receipt["ticket_id"] != ticket_id
            or receipt["expected_digest"] != ticket["ticket_digest"]
            or receipt["source_relative_path"]
            != ticket["current_source_relative_path"]
            or receipt["from_disposition"]
            != ticket.get("disposition", "open")
            or receipt["to_disposition"]
            not in {"open", "on-hold", "canceled"}
            or any(
                not isinstance(receipt[field], str) or not receipt[field]
                for field in fields - {"schema", "authority_gate_id"}
            )
        ):
            raise TransitionError("lifecycle receipt contradicts ticket state")
        authority = self.preflight_disposition_transition(
            ticket_id,
            receipt["to_disposition"],
            actor=receipt["actor"],
            reason=receipt["reason"],
            authority_ref=receipt["authority_ref"],
            authority_gate_id=receipt["authority_gate_id"],
        )
        if any(receipt[key] != authority[key] for key in authority):
            raise TransitionError("lifecycle receipt authority is not current")
        return copy.deepcopy(receipt)

    def preflight_disposition_transition(
        self,
        ticket_id: str,
        disposition: str,
        *,
        actor: str | None = None,
        reason: str | None = None,
        authority_ref: str | None = None,
        authority_gate_id: str | None = None,
    ) -> dict[str, str | None]:
        """Purely reject inadmissible administrative transitions before effects."""

        ticket = self._ticket(ticket_id)
        if disposition not in {"open", "on-hold", "canceled"}:
            raise TransitionError("lifecycle target disposition is invalid")
        current = ticket.get("disposition", "open")
        if disposition in {"on-hold", "canceled"}:
            if any(
                not isinstance(value, str) or not value.strip()
                for value in (actor, reason, authority_ref)
            ) or authority_gate_id is not None:
                raise TransitionError(
                    "hold or cancel requires direct identity, reason, and authority"
                )
            receipt = ticket.get("disposition_receipt")
            if current == disposition and isinstance(receipt, dict):
                expected = {
                    "actor": actor,
                    "reason": reason,
                    "authority_ref": authority_ref,
                    "authority_gate_id": None,
                }
                if all(receipt.get(key) == value for key, value in expected.items()):
                    return expected
            barrier = ticket.get("status_barrier")
            barrier_allows_gated = (
                ticket["state"] == "gated"
                and isinstance(barrier, dict)
                and barrier.get("actor") == actor
                and barrier.get("reason") == reason
                and barrier.get("authority_ref") == authority_ref
                and barrier.get("to_disposition") == disposition
            )
            if current != "open" or (
                ticket["state"] not in {"pending", "active"}
                and not barrier_allows_gated
            ):
                raise TransitionError(
                    "hold or cancel requires an open safe-boundary ticket"
                )
            return {
                "actor": actor,
                "reason": reason,
                "authority_ref": authority_ref,
                "authority_gate_id": None,
            }
        if current not in {"on-hold", "canceled"} or ticket["state"] != "pending":
            raise TransitionError(
                "reopen requires an on-hold or canceled pending ticket"
            )
        gate = self.ledger["gates"].get(authority_gate_id)
        request = gate.get("lifecycle_request") if isinstance(gate, dict) else None
        if (
            not isinstance(gate, dict)
            or gate.get("ticket_id") != ticket_id
            or gate.get("kind") != "reopen"
            or gate.get("category") != "human"
            or gate.get("state") != "passed"
            or gate.get("consumed_by_transition_id") is not None
            or not isinstance(request, dict)
            or request.get("ticket_id") != ticket_id
            or request.get("target_disposition") != "open"
            or not isinstance(request.get("reason"), str)
            or not request["reason"]
            or not isinstance(gate.get("actor"), str)
            or not gate["actor"]
            or not isinstance(gate.get("evidence"), str)
            or not gate["evidence"]
        ):
            raise TransitionError("reopen requires a passed ticket-bound human gate")
        authority = {
            "actor": gate["actor"],
            "reason": request["reason"],
            "authority_ref": gate["evidence"],
            "authority_gate_id": authority_gate_id,
        }
        supplied = {
            "actor": actor,
            "reason": reason,
            "authority_ref": authority_ref,
            "authority_gate_id": authority_gate_id,
        }
        if any(value is not None for key, value in supplied.items() if key != "authority_gate_id") and supplied != authority:
            raise TransitionError("reopen authority differs from the passed human gate")
        return authority

    def preflight_mutation_boundary(
        self, ticket_id: str, boundary: str
    ) -> None:
        """Fail closed immediately before implementation or external mutation."""

        ticket = self._ticket(ticket_id)
        if not isinstance(boundary, str) or not boundary:
            raise TransitionError("mutation boundary name is required")
        if self.ledger.get("pause") is not None:
            raise TransitionError(f"run is paused before {boundary}")
        current_barrier = ticket.get("status_barrier")
        repository = self.ledger.get("repo")
        run_id = self.ledger.get("run_id")
        repository_checked = bool(
            isinstance(repository, str)
            and repository
            and Path(repository).is_dir()
            and isinstance(run_id, str)
            and run_id
        )
        repository_barrier = None
        if repository_checked:
            try:
                repository_barrier = active_status_barrier(
                    Path(repository), run_id=run_id, ticket_id=ticket_id
                )
            except StatusBarrierError as error:
                raise TransitionError(str(error)) from error
        if isinstance(current_barrier, dict):
            if repository_checked and (
                repository_barrier is None
                or repository_barrier.get("transaction_id")
                != current_barrier.get("transaction_id")
                or repository_barrier.get("safe_boundary", {}).get(
                    "run_barrier_receipt_digest"
                )
                != canonical_digest(current_barrier)
            ):
                raise TransitionError(
                    "repository lifecycle barrier journal contradicts run receipt"
                )
            raise TransitionError(
                "repository lifecycle barrier forbids "
                f"{boundary}: {current_barrier['transaction_id']}"
            )
        if repository_barrier is not None:
            raise TransitionError(
                "repository lifecycle barrier forbids "
                f"{boundary}: {repository_barrier['transaction_id']}"
            )
        if ticket.get("disposition") in {"on-hold", "canceled"}:
            raise TransitionError(
                f"ticket disposition forbids {boundary}: {ticket['disposition']}"
            )

    def arm_status_barrier(
        self, ticket_id: str, receipt: dict[str, Any]
    ) -> dict[str, Any]:
        """Persist one exact safe-boundary receipt without discarding attempt evidence."""

        with self._transaction():
            ticket = self._ticket(ticket_id)
            history = ticket.setdefault("status_barrier_history", [])
            current = ticket.get("status_barrier")
            if isinstance(current, dict):
                if current == receipt:
                    return copy.deepcopy(current)
                raise TransitionError("another repository lifecycle barrier is active")
            if any(
                item.get("transaction_id") == receipt.get("transaction_id")
                for item in history
                if isinstance(item, dict)
            ):
                raise TransitionError("completed status barrier cannot be rearmed")
            if (
                receipt.get("ticket_id") != ticket_id
                or receipt.get("from_disposition")
                != ticket.get("disposition", "open")
                or receipt.get("prior_state")
                not in {"pending", "active", "gated", "waiting"}
                or receipt.get("to_disposition")
                not in {"open", "on-hold", "canceled"}
                or receipt.get("evidence_preserved") is not True
                or receipt.get("prior_state")
                != (
                    "waiting"
                    if ticket["state"] == "pending"
                    and ticket.get("disposition", "open") == "open"
                    and receipt.get("readiness") != "ready"
                    else ticket["state"]
                )
            ):
                raise TransitionError("status barrier contradicts ticket state")
            normalized = copy.deepcopy(receipt)
            history.append(normalized)
            ticket["status_barrier"] = copy.deepcopy(normalized)
            if receipt["prior_state"] == "active":
                ticket["state"] = "pending"
                ticket["attempt_outcome"] = "stopped"
                ticket["stop_reason"] = receipt["reason"]
            self._event(
                "ticket-status-barrier-armed",
                ticket_id,
                transaction_id=receipt["transaction_id"],
                outcome=receipt["outcome"],
            )
            self._update_run_state()
            return copy.deepcopy(normalized)

    def record_disposition_transition(
        self, ticket_id: str, receipt: dict[str, Any]
    ) -> None:
        """Bind a durable source move receipt to the run at a safe boundary."""

        with self._transaction():
            ticket = self._ticket(ticket_id)
            if ticket.get("disposition_receipt") == receipt:
                return
            normalized = self._validated_disposition_receipt(
                ticket_id, ticket, receipt
            )
            target = normalized["to_disposition"]
            barrier = ticket.get("status_barrier")
            barrier_matches = isinstance(barrier, dict) and all(
                barrier.get(key) == normalized.get(receipt_key)
                for key, receipt_key in (
                    ("actor", "actor"),
                    ("reason", "reason"),
                    ("authority_ref", "authority_ref"),
                    ("to_disposition", "to_disposition"),
                )
            )
            if target in {"on-hold", "canceled"}:
                if ticket["state"] not in {"pending", "active", "gated"}:
                    raise TransitionError(
                        "ticket disposition change requires a proved safe boundary"
                    )
                was_active = ticket["state"] == "active"
                ticket["state"] = "pending"
                if was_active:
                    ticket["attempt_outcome"] = "stopped"
                    ticket["stop_reason"] = f"administrative-{target}"
                elif not barrier_matches:
                    ticket["attempt_outcome"] = None
                    ticket["stop_reason"] = None
                for gate in self.ledger["gates"].values():
                    if gate.get("ticket_id") == ticket_id and gate.get("state") == "open":
                        gate["state"] = "superseded"
                        gate["superseded_by_transition_id"] = normalized[
                            "transition_id"
                        ]
            else:
                if ticket["state"] != "pending":
                    raise TransitionError("ticket reopen requires a stopped pending ticket")
                ticket["state"] = "pending"
                ticket["stage"] = None
                ticket["quality_failures"] = 0
                ticket["leaf_budget"] = new_leaf_budget(self.ledger)
                self._invalidate_leaf_artifacts(ticket)
                ticket["failure_kind"] = None
                ticket["candidate_ref"] = None
                ticket["delivery_candidate_ref"] = None
                ticket["delivery_lineage"] = None
                ticket["artifact_generation"] += 1
                ticket["validated_stages"] = []
                ticket["delivery"] = {}
                ticket["pr"] = None
                ticket["merge_authorization"] = None
                ticket["preexisting_integrated"] = False
                ticket.pop("resume_pending", None)
                ticket["attempt_outcome"] = None
                ticket["stop_reason"] = None
            ticket["status_barrier"] = None
            ticket["disposition"] = target
            ticket["current_source_relative_path"] = normalized[
                "destination_relative_path"
            ]
            ticket["disposition_receipt"] = normalized
            if target == "open":
                gate = self.ledger["gates"][normalized["authority_gate_id"]]
                gate["consumed_by_transition_id"] = normalized["transition_id"]
            self._event(
                "ticket-disposition-changed", ticket_id, receipt=normalized
            )
            self._update_run_state()

    def _completion_projection_resolved_gate_id(
        self, ticket_id: str, grant: dict[str, Any]
    ) -> str | None:
        gate_ids = [
            event.get("details", {}).get("gate_id")
            for event in self.ledger["history"]
            if event.get("event") == "completion-projection-gate-resolved"
            and event.get("ticket_id") == ticket_id
            and event.get("details", {}).get("grant") == grant
        ]
        if not gate_ids:
            return None
        if len(gate_ids) != 1 or not isinstance(gate_ids[0], str):
            raise TransitionError(
                "completion projection grant has contradictory gate history"
            )
        gate_id = gate_ids[0]
        gate = self.ledger["gates"].get(gate_id)
        if (
            not isinstance(gate, dict)
            or gate.get("ticket_id") != ticket_id
            or gate.get("category") != "source-mode-drift"
            or gate.get("state") != "passed"
            or gate.get("actor") != grant["actor"]
            or gate.get("evidence") != grant["evidence"]
            or not isinstance(gate.get("details"), dict)
            or gate["details"].get("source_path")
            != grant["destination_relative_path"]
        ):
            raise TransitionError(
                "completion projection grant has contradictory resolved gate"
            )
        return gate_id

    def _completion_projection_completed_recovery_allowed(
        self,
        ticket_id: str,
        ticket: dict[str, Any],
        candidate: dict[str, Any],
        destination_relative_path: str,
    ) -> bool:
        if ticket.get("disposition") != "completed":
            return False
        matching_open_gate = any(
            gate.get("ticket_id") == ticket_id
            and gate.get("category") == "source-mode-drift"
            and gate.get("state") == "open"
            and isinstance(gate.get("details"), dict)
            and gate["details"].get("snapshot_classification") == "ignored"
            and gate["details"].get("observed_classification") == "tracked"
            and gate["details"].get("base_classification")
            in {"ignored", "tracked"}
            and gate["details"].get("source_path")
            == destination_relative_path
            for gate in self.ledger["gates"].values()
        )
        if ticket.get("state") == "gated" and matching_open_gate:
            return True
        current_grant = ticket.get("completion_projection_grant")
        return (
            isinstance(current_grant, dict)
            and current_grant.get("candidate_ref") == candidate
            and current_grant.get("destination_relative_path")
            == destination_relative_path
            and self._completion_projection_resolved_gate_id(
                ticket_id, current_grant
            )
            is not None
        )

    def grant_completion_projection(
        self,
        ticket_id: str,
        *,
        candidate: CandidateRef,
        destination_relative_path: str,
        actor: str,
        evidence: str,
    ) -> tuple[dict[str, Any], bool]:
        """Persist one immutable exact-candidate ignored-source projection grant."""

        with self._transaction():
            ticket = self._ticket(ticket_id)
            if self.ledger["run_state"] in {"completed", "failed", "aborted"}:
                raise TransitionError(
                    "completion projection grant requires a non-terminal run"
                )
            if ticket["state"] in {"failed", "integrated"}:
                raise TransitionError(
                    "completion projection grant requires a non-terminal ticket"
                )
            if self.ledger.get("ticket_source_mode") != "ignored":
                raise TransitionError(
                    "completion projection grant requires an ignored ticket source"
                )
            if any(
                not isinstance(value, str) or not value.strip()
                for value in (destination_relative_path, actor, evidence)
            ):
                raise TransitionError(
                    "completion projection grant requires destination, actor, and durable evidence"
                )
            candidate_document = asdict(candidate)
            if ticket.get("candidate_ref") != candidate_document:
                raise TransitionError(
                    "completion projection grant CandidateRef differs from the ticket"
                )
            if ticket.get("disposition") != "open" and not (
                self._completion_projection_completed_recovery_allowed(
                    ticket_id,
                    ticket,
                    candidate_document,
                    destination_relative_path,
                )
            ):
                raise TransitionError(
                    "completion projection grant requires an open ticket or "
                    "an exact completed-source recovery gate"
                )
            grant = {
                "schema": 1,
                "policy_version": COMPLETION_PROJECTION_GRANT_VERSION,
                "repository_identity": self.ledger["repo"],
                "run_id": self.ledger["run_id"],
                "ticket_id": ticket_id,
                "snapshot_manifest_digest": self.ledger[
                    "snapshot_manifest_digest"
                ],
                "ticket_digest": ticket["ticket_digest"],
                "candidate_ref": candidate_document,
                "destination_relative_path": destination_relative_path,
                "actor": actor,
                "evidence": evidence,
            }
            entries = completion_projection_grant_entries(
                self.ledger, ticket_id
            )
            if entries is None:
                raise TransitionError(
                    "completion projection grant lineage is invalid"
                )
            existing = ticket.get("completion_projection_grant")
            if existing == grant:
                return copy.deepcopy(grant), True
            if (
                isinstance(existing, dict)
                and existing.get("candidate_ref") == candidate_document
            ):
                raise TransitionError(
                    "completion projection grant for the current candidate is immutable"
                )
            for entry in entries[:-1]:
                if entry["grant"] == grant:
                    return copy.deepcopy(grant), True
            predecessor = entries[-1]["grant_id"] if entries else None
            entry = completion_projection_grant_entry(
                grant,
                sequence=len(entries) + 1,
                predecessor_grant_id=predecessor,
            )
            ticket["completion_projection_grants"] = [*entries, entry]
            ticket["completion_projection_grant"] = grant
            self._event(
                "completion-projection-granted",
                ticket_id,
                grant=copy.deepcopy(grant),
            )
            self._update_run_state()
            return copy.deepcopy(grant), False

    def resolve_completion_projection_gate(
        self,
        ticket_id: str,
        *,
        delivery_head_proof: dict[str, Any] | None = None,
    ) -> str | None:
        """Resolve only the exact source-mode gate covered by a persisted grant."""

        with self._transaction():
            ticket = self._ticket(ticket_id)
            grant = ticket.get("completion_projection_grant")
            if (
                not isinstance(grant, dict)
                or not completion_projection_grant_matches_ticket(
                    self.ledger, ticket_id
                )
                or grant.get("candidate_ref") != ticket.get("candidate_ref")
            ):
                raise TransitionError(
                    "completion projection gate requires a current exact grant"
                )
            destination = grant["destination_relative_path"]

            def matches(gate: dict[str, Any], state: str) -> bool:
                details = gate.get("details")
                if not (
                    gate.get("ticket_id") == ticket_id
                    and gate.get("category") == "source-mode-drift"
                    and gate.get("state") == state
                    and isinstance(details, dict)
                    and details.get("ticket_id") == ticket_id
                    and details.get("snapshot_classification") == "ignored"
                    and details.get("observed_classification") == "tracked"
                    and details.get("source_path") == destination
                ):
                    return False
                if details.get("base_classification") == "ignored":
                    return delivery_head_proof is None
                return (
                    details.get("base_classification") == "tracked"
                    and delivery_head_proof is not None
                    and completion_projection_delivery_head_proof_matches(
                        self.ledger,
                        ticket_id,
                        gate["gate_id"],
                        delivery_head_proof,
                    )
                )

            source_mode_gates = [
                gate
                for gate in self.ledger["gates"].values()
                if gate.get("ticket_id") == ticket_id
                and gate.get("category") == "source-mode-drift"
                and gate.get("state") == "open"
            ]
            if not source_mode_gates:
                return self._completion_projection_resolved_gate_id(
                    ticket_id, grant
                )
            matching = [
                gate for gate in source_mode_gates if matches(gate, "open")
            ]
            if len(matching) != 1 or len(source_mode_gates) != 1:
                raise TransitionError(
                    "completion projection grant does not match the open source-mode gate"
                )
            gate = matching[0]
            gate_id = gate["gate_id"]
            gate["state"] = "passed"
            gate["actor"] = grant["actor"]
            gate["evidence"] = grant["evidence"]
            if delivery_head_proof is not None:
                gate["completion_projection_delivery_head_proof"] = copy.deepcopy(
                    delivery_head_proof
                )
            other_open = [
                item
                for other_id, item in self.ledger["gates"].items()
                if other_id != gate_id
                and item.get("ticket_id") == ticket_id
                and item.get("state") == "open"
            ]
            if not other_open:
                resume_state = gate["resume_state"]
                active_ticket = self._active_ticket_id()
                if (
                    resume_state == "active"
                    and active_ticket is not None
                    and active_ticket != ticket_id
                ):
                    ticket["state"] = "pending"
                    ticket["resume_pending"] = True
                else:
                    ticket["state"] = resume_state
                ticket["stage"] = gate["resume_stage"]
            event_details = {
                "gate_id": gate_id,
                "grant": copy.deepcopy(grant),
            }
            if delivery_head_proof is not None:
                event_details["delivery_head_proof"] = copy.deepcopy(
                    delivery_head_proof
                )
            self._event(
                "completion-projection-gate-resolved",
                ticket_id,
                **event_details,
            )
            self._update_run_state()
            return gate_id

    def grant_autonomous_merge(
        self, *, actor: str, evidence: str
    ) -> tuple[dict[str, Any], bool]:
        """Append one immutable, run-bound autonomous merge grant."""

        with self._transaction():
            if self.ledger["run_state"] in {"completed", "failed", "aborted"}:
                raise TransitionError(
                    "autonomous merge grant requires a non-terminal run"
                )
            if any(
                not isinstance(value, str) or not value.strip()
                for value in (actor, evidence)
            ):
                raise TransitionError(
                    "autonomous merge grant requires actor and durable evidence"
                )
            if not isinstance(self.ledger.get("repo"), str) or not self.ledger["repo"]:
                raise TransitionError(
                    "autonomous merge grant requires repository identity"
                )
            if (
                not isinstance(self.ledger.get("provider"), str)
                or not self.ledger["provider"]
            ):
                raise TransitionError(
                    "autonomous merge grant requires provider identity"
                )
            grant = {
                "schema": 1,
                "policy_version": AUTONOMOUS_GRANT_VERSION,
                "repository_identity": self.ledger["repo"],
                "run_id": self.ledger["run_id"],
                "ticket_set_digest": self.ledger["snapshot_manifest_digest"],
                "provider": self.ledger["provider"],
                "policy": "autonomous",
                "actor": actor,
                "evidence": evidence,
            }
            policy = self.ledger.get("merge_policy", "manual")
            if policy == "autonomous":
                if self.ledger.get("autonomous_merge_grant") == grant:
                    return copy.deepcopy(grant), True
                raise TransitionError("autonomous merge grant is immutable")
            if policy != "manual":
                raise TransitionError("invalid merge policy")
            for ticket in self.ledger["tickets"].values():
                delivery = ticket.get("delivery", {})
                if ticket["state"] != "integrated" and (
                    ticket.get("merge_authorization") is not None
                    or any(
                        step in delivery
                        for step in HEAD_BOUND_MERGE_DELIVERY_STEPS
                    )
                ):
                    raise TransitionError(
                        "unresolved provider merge critical path forbids a new grant"
                    )
            self.ledger["merge_policy"] = "autonomous"
            self.ledger["autonomous_merge_grant"] = grant
            self._event(
                "autonomous-merge-granted",
                None,
                grant=copy.deepcopy(grant),
            )
            self._update_run_state()
            return copy.deepcopy(grant), False

    def pause_run(self, *, actor: str, reason: str) -> None:
        with self._transaction():
            if self.ledger["run_state"] in {"completed", "failed", "aborted"}:
                raise TransitionError("terminal run cannot be paused")
            if self.ledger.get("pause") is not None:
                raise TransitionError("run is already paused")
            if not actor or not reason:
                raise TransitionError("pause requires actor and reason")
            self.ledger["pause"] = {"actor": actor, "reason": reason}
            self._event("run-paused", None, actor=actor, reason=reason)
            self._update_run_state()

    def unpause_run(self, *, actor: str, reason: str) -> None:
        with self._transaction():
            if self.ledger.get("pause") is None:
                raise TransitionError("run is not paused")
            if not actor or not reason:
                raise TransitionError("unpause requires actor and reason")
            previous = copy.deepcopy(self.ledger["pause"])
            self.ledger["pause"] = None
            self._event(
                "run-unpaused", None, actor=actor, reason=reason, previous=previous
            )
            self._update_run_state()

    def abort(self, *, actor: str, reason: str) -> None:
        with self._transaction():
            if self.ledger["run_state"] in {"completed", "aborted"}:
                raise TransitionError("run is already terminal")
            if not actor or not reason:
                raise TransitionError("abort requires actor and reason")
            self.ledger["run_state"] = "aborted"
            self._event("run-aborted", None, actor=actor, reason=reason)

    def record_cleanup(
        self,
        *,
        worktree: str,
        worktree_removed: bool,
        resume_abandoned: bool,
    ) -> None:
        with self._transaction():
            if self.ledger["run_state"] == "running":
                raise TransitionError("running run cannot be cleaned up")
            self.ledger["cleanup"] = {
                "recorded": True,
                "worktree": worktree,
                "worktree_removed": worktree_removed,
                "resume_abandoned": resume_abandoned,
                "remote_state_deleted": False,
            }
            self._event(
                "worktree-cleaned",
                None,
                worktree=worktree,
                resume_abandoned=resume_abandoned,
            )

    def _update_run_state(self) -> None:
        if self.ledger["run_state"] == "aborted":
            return
        states = [ticket["state"] for ticket in self.ledger["tickets"].values()]
        if states and all(state == "integrated" for state in states):
            self.ledger["run_state"] = "completed"
        elif any(state == "failed" for state in states) and all(
            ticket["state"] in {"failed", "integrated"}
            or (
                ticket["state"] == "pending"
                and self._depends_on_failed(ticket["ticket_id"], set())
            )
            for ticket in self.ledger["tickets"].values()
        ):
            self.ledger["run_state"] = "failed"
        elif (
            states
            and all(state in TERMINAL_TICKET_STATES for state in states)
            and any(state == "failed" for state in states)
        ):
            self.ledger["run_state"] = "failed"
        elif self.ledger.get("pause") is not None:
            self.ledger["run_state"] = "waiting"
        elif (
            self._active_ticket_id() is not None
            or self.pending_runner_merge_id() is not None
            or self.ready_ids()
        ):
            self.ledger["run_state"] = "running"
        else:
            self.ledger["run_state"] = "waiting"

    def _depends_on_failed(self, ticket_id: str, seen: set[str]) -> bool:
        if ticket_id in seen:
            return False
        seen.add(ticket_id)
        ticket = self._ticket(ticket_id)
        for blocker_id in ticket["blocked_by"]:
            blocker = self._ticket(blocker_id)
            if blocker["state"] == "failed" or self._depends_on_failed(
                blocker_id, seen
            ):
                return True
        return False

    def report(self) -> dict[str, Any]:
        def cache_summary(ticket_id: str) -> dict[str, Any]:
            decisions = [
                item["details"]
                for item in self.ledger["history"]
                if item["event"] == "evidence-cache-decision"
                and item["ticket_id"] == ticket_id
            ]
            limitations = sorted(
                {
                    limitation
                    for decision in decisions
                    for limitation in decision["limitations"]
                }
            )
            return {
                "hits": sum(1 for item in decisions if item["hit"]),
                "misses": sum(1 for item in decisions if not item["hit"]),
                "commands_avoided": sum(
                    item["commands_avoided"] for item in decisions
                ),
                "limitations": limitations,
                "last_decision": (
                    copy.deepcopy(decisions[-1]) if decisions else None
                ),
            }

        def merge_summary(ticket: dict[str, Any]) -> dict[str, Any] | None:
            progress = ticket.get("delivery", {}).get("merge-progress")
            if not isinstance(progress, dict):
                return None
            started_ns = progress.get("started_at_ns")
            updated_ns = progress.get("updated_at_ns")
            if not isinstance(started_ns, int) or not isinstance(updated_ns, int):
                return copy.deepcopy(progress)
            status = progress.get("status")
            end_ns = (
                updated_ns
                if status in {"gated", "failed", "integrated"}
                else time.time_ns()
            )
            return {
                **copy.deepcopy(progress),
                "elapsed_seconds": round(
                    max(0, end_ns - started_ns) / 1_000_000_000,
                    3,
                ),
            }

        def completion_effect(
            ticket_id: str, ticket: dict[str, Any]
        ) -> dict[str, Any]:
            applied = ticket.get("delivery", {}).get(
                "ignored-finalization-applied"
            )
            if isinstance(applied, dict):
                return {"state": "applied", **copy.deepcopy(applied)}
            effects = [
                copy.deepcopy(effect)
                for effect in self.ledger["effects"].values()
                if effect.get("ticket_id") == ticket_id
                and effect.get("effect")
                in {"move-done-and-stage", "move-done-and-summarize-external"}
            ]
            if effects:
                return {"state": "applied", "receipts": effects}
            intent = ticket.get("delivery", {}).get(
                "ignored-finalization-intent"
            )
            if isinstance(intent, dict):
                return {"state": "intent-recorded", **copy.deepcopy(intent)}
            return {"state": "pending"}

        def source_drift_gate(ticket_id: str) -> dict[str, Any] | None:
            gates = [
                copy.deepcopy(gate)
                for gate in self.ledger["gates"].values()
                if gate.get("ticket_id") == ticket_id
                and gate.get("category")
                in {"source-drift", "source-mode-drift"}
                and gate.get("state") == "open"
            ]
            return gates[0] if gates else None

        def completion_projection_gate(
            ticket_id: str, ticket: dict[str, Any]
        ) -> dict[str, Any] | None:
            grant = ticket.get("completion_projection_grant")
            if not isinstance(grant, dict):
                return None
            gate_id = self._completion_projection_resolved_gate_id(
                ticket_id, grant
            )
            return (
                copy.deepcopy(self.ledger["gates"][gate_id])
                if gate_id is not None
                else None
            )

        def completion_projection_delivery_head_proof(
            ticket_id: str, ticket: dict[str, Any]
        ) -> dict[str, Any] | None:
            gate = completion_projection_gate(ticket_id, ticket)
            proof = (
                gate.get("completion_projection_delivery_head_proof")
                if isinstance(gate, dict)
                else None
            )
            if not isinstance(proof, dict):
                return None
            return {
                "schema": proof["schema"],
                "proof_id": proof["proof_id"],
                "provenance": proof["provenance"],
                "gate_id": proof["gate_id"],
                "head_sha": proof["head_sha"],
                "head_tree_oid": proof["head_tree_oid"],
                "terminal_branch": proof["terminal_branch"],
                "terminal_sha": proof["terminal_sha"],
                "terminal_tree_oid": proof["terminal_tree_oid"],
            }

        def completion_projection_authority(
            ticket_id: str,
        ) -> dict[str, Any]:
            entries = completion_projection_grant_entries(
                self.ledger, ticket_id
            )
            if entries is None:
                raise TransitionError(
                    "completion projection grant lineage is invalid"
                )
            active = entries[-1] if entries else None
            return {
                "schema": 1,
                "count": len(entries),
                "active_grant_id": (
                    active["grant_id"] if active is not None else None
                ),
                "active_sequence": (
                    active["sequence"] if active is not None else None
                ),
                "predecessor_grant_id": (
                    active["predecessor_grant_id"]
                    if active is not None
                    else None
                ),
                "lineage": [
                    {
                        "sequence": entry["sequence"],
                        "grant_id": entry["grant_id"],
                        "predecessor_grant_id": entry[
                            "predecessor_grant_id"
                        ],
                    }
                    for entry in entries
                ],
            }

        def readiness(ticket_id: str, ticket: dict[str, Any]) -> str:
            disposition = ticket.get("disposition", "open")
            if disposition == "completed":
                return "completed"
            if disposition in {"on-hold", "canceled"}:
                return "not-schedulable"
            if ticket.get("status_barrier") is not None:
                return "not-schedulable"
            if self._administrative_dependency_causes(ticket_id):
                return "blocked"
            if ticket["state"] == "gated":
                return "human-gated"
            if ticket["state"] != "pending" or self.ledger.get("pause") is not None:
                return "not-schedulable"
            return "ready" if self._dependency_ready(ticket) else "blocked"

        def lifetime_leaf_usage(ticket_id: str) -> dict[str, int]:
            leaf_events = [
                event
                for event in self.ledger["history"]
                if event["ticket_id"] == ticket_id
                and event["event"] == "leaf-result-recorded"
            ]
            return {
                "interactions": len(leaf_events),
                "tool_calls": sum(
                    event["details"]["tool_calls"] for event in leaf_events
                ),
                "wall_time": sum(
                    event["details"]["wall_time"] for event in leaf_events
                ),
            }

        invalidation_events = {
            "candidate-invalidated",
            "delivery-revalidation-required",
            "reconciliation-revalidation-required",
        }
        lifetime_usage = {
            ticket_id: lifetime_leaf_usage(ticket_id)
            for ticket_id in self.ledger["tickets"]
        }

        tickets = {
            ticket_id: {
                "state": ticket["state"],
                "disposition": ticket.get("disposition", "open"),
                "lifecycle": (
                    "not-started"
                    if ticket["state"] == "pending"
                    else "running"
                    if ticket["state"] == "active"
                    else "completed"
                    if ticket["state"] == "integrated"
                    else ticket["state"]
                ),
                "attempt_outcome": ticket.get("attempt_outcome"),
                "readiness": readiness(ticket_id, ticket),
                "readiness_causes": (
                    [
                        {
                            "ticket_id": ticket_id,
                            "reason": "administrative-status-barrier",
                        }
                    ]
                    if ticket.get("status_barrier") is not None
                    else self._administrative_dependency_causes(ticket_id)
                ),
                "stop_reason": ticket.get("stop_reason"),
                "status_barrier": copy.deepcopy(ticket.get("status_barrier")),
                "status_barrier_history": copy.deepcopy(
                    ticket.get("status_barrier_history", [])
                ),
                "stage": ticket["stage"],
                "quality_failures": ticket["quality_failures"],
                "failure_kind": ticket["failure_kind"],
                "execution_mode": ticket["execution_mode"],
                "blocked_by": list(ticket["blocked_by"]),
                "source_relative_path": ticket["source_relative_path"],
                "current_source_relative_path": ticket[
                    "current_source_relative_path"
                ],
                "completion_effect": completion_effect(ticket_id, ticket),
                "source_drift_gate": source_drift_gate(ticket_id),
                "completion_projection_grant": copy.deepcopy(
                    ticket.get("completion_projection_grant")
                ),
                "completion_projection_authority": (
                    completion_projection_authority(ticket_id)
                ),
                "completion_projection_delivery_head_proof": (
                    completion_projection_delivery_head_proof(ticket_id, ticket)
                ),
                "completion_projection_gate": completion_projection_gate(
                    ticket_id, ticket
                ),
                "candidate_ref": copy.deepcopy(ticket["candidate_ref"]),
                "delivery_candidate_ref": copy.deepcopy(
                    ticket["delivery_candidate_ref"]
                ),
                "delivery_lineage": copy.deepcopy(ticket["delivery_lineage"]),
                "docs_only": copy.deepcopy(ticket.get("docs_only")),
                "artifact_generation": ticket["artifact_generation"],
                "validated_stages": list(ticket["validated_stages"]),
                "delivery": copy.deepcopy(ticket["delivery"]),
                "wiki_sync": copy.deepcopy(
                    ticket.get("delivery", {}).get("wiki-sync")
                ),
                "delivery_progress": (
                    {
                        "last_phase": ticket["delivery"]["result"]["phase"],
                        **{
                            key: copy.deepcopy(value)
                            for key, value in ticket["delivery"]["result"].items()
                            if key != "phase"
                        },
                    }
                    if "result" in ticket["delivery"]
                    else None
                ),
                "evidence_cache": cache_summary(ticket_id),
                "pr": copy.deepcopy(ticket["pr"]),
                "merge_authorization": copy.deepcopy(
                    ticket["merge_authorization"]
                ),
                "merge_eligibility": copy.deepcopy(
                    ticket.get("delivery", {}).get(
                        "autonomous-eligibility"
                    )
                ),
                "merge_critical_path": merge_summary(ticket),
                "budgets": {
                    **budget_status(self.ledger, ticket["leaf_budget"]),
                    "quality_failures": {
                        "configured": self.ledger["max_quality_failures"],
                        "consumed": ticket["quality_failures"],
                        "remaining": max(
                            0,
                            self.ledger["max_quality_failures"]
                            - ticket["quality_failures"],
                        ),
                        "enforcement": "hard",
                    },
                },
                "leaf_progress": {
                    "last_phase": (
                        ticket["leaf_progress_events"][-1]["phase"]
                        if ticket["leaf_progress_events"]
                        else None
                    ),
                    "health": leaf_health(
                        ticket["leaf_handoff"]
                        or (
                            ticket["leaf_results"].get(
                                ticket["leaf_progress_events"][-1]["stage"]
                            )
                            if ticket["leaf_progress_events"]
                            else None
                        )
                    ),
                    "events": len(ticket["leaf_progress_events"]),
                    "handoff": copy.deepcopy(ticket["leaf_handoff"]),
                    "completed": copy.deepcopy(ticket["leaf_results"]),
                },
                "verbosity": {
                    "leaf_interactions": lifetime_usage[ticket_id][
                        "interactions"
                    ],
                    "leaf_tool_calls": lifetime_usage[ticket_id][
                        "tool_calls"
                    ],
                    "leaf_wall_time": lifetime_usage[ticket_id][
                        "wall_time"
                    ],
                    "candidate_invalidations": sum(
                        1
                        for event in self.ledger["history"]
                        if event["ticket_id"] == ticket_id
                        and event["event"] in invalidation_events
                    ),
                    "leaf_interactions_avoided": (
                        ticket.get("docs_only", {}).get(
                            "leaf_interactions_avoided", 0
                        )
                        if isinstance(ticket.get("docs_only"), dict)
                        else 0
                    ),
                    "wait_count": 0,
                    "token_count": {
                        "value": None,
                        "enforcement": "unavailable",
                    },
                },
            }
            for ticket_id, ticket in self.ledger["tickets"].items()
        }
        return {
            "schema": 2,
            "run_id": self.ledger["run_id"],
            "run_state": self.ledger["run_state"],
            "execution_lifecycle": (
                "paused" if self.ledger.get("pause") is not None else "running"
            ),
            "pause": copy.deepcopy(self.ledger.get("pause")),
            "provider_mode": self.ledger.get("provider_mode", "live"),
            "merge_policy": self.ledger.get("merge_policy", "manual"),
            "merge_grant": copy.deepcopy(
                self.ledger.get("autonomous_merge_grant")
            ),
            "wiki_sync_policy": copy.deepcopy(
                self.ledger.get(
                    "wiki_sync_policy",
                    {
                        "schema": 1,
                        "merge_policy": "manual",
                        "autonomous_grant": None,
                    },
                )
            ),
            "ticket_source_mode": self.ledger["ticket_source_mode"],
            "snapshot_manifest_digest": self.ledger[
                "snapshot_manifest_digest"
            ],
            "snapshot_manifest_path": self.ledger["snapshot_manifest_path"],
            "ticket_source_folder_identity": copy.deepcopy(
                self.ledger["ticket_source_folder_identity"]
            ),
            "budget_config": {
                "max_quality_failures": self.ledger[
                    "max_quality_failures"
                ],
                "max_leaf_interactions": self.ledger[
                    "max_leaf_interactions"
                ],
                "max_leaf_tool_calls": self.ledger[
                    "max_leaf_tool_calls"
                ],
                "max_leaf_wall_time": self.ledger[
                    "max_leaf_wall_time"
                ],
                "reservations": copy.deepcopy(self.ledger["reservations"]),
            },
            "next_ready": self.next_ready_id(),
            "ready": self.ready_ids(),
            "dependency_blocked": self.dependency_blocked_ids(),
            "open_gates": self.human_gated_ids(),
            "cleanup": copy.deepcopy(self.ledger.get("cleanup")),
            "tickets": tickets,
        }
