from __future__ import annotations

import copy
import hashlib
import json
import re
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from typing import Any, Iterator, cast

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
    validate_handoff_progression,
    validate_leaf_budget,
    validate_leaf_result,
    verification_checkpoint_identity,
)
from .ledger import LEDGER_VERSION
from .ticket_contract import TicketGraph


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


class TransitionError(RuntimeError):
    """The requested transition would violate a workflow invariant."""


@dataclass(frozen=True)
class CandidateRef:
    base_sha: str
    tree_oid: str
    ticket_digest: str
    contract_version: int

    def validate(self) -> None:
        if self.contract_version != 1:
            raise TransitionError("unsupported CandidateRef contract_version")
        for field, value in asdict(self).items():
            if field != "contract_version" and (not isinstance(value, str) or not value):
                raise TransitionError(f"CandidateRef {field} must be non-empty")

    @property
    def digest(self) -> str:
        encoded = json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


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
        tickets: dict[str, dict[str, Any]] = {}
        for ticket_id in graph.order:
            ticket = graph.tickets[ticket_id]
            initial_state = (
                "integrated" if ticket_id in graph.completed_ids else "pending"
            )
            tickets[ticket_id] = {
                "ticket_id": ticket_id,
                "path": str(ticket.path),
                "ticket_digest": ticket.digest,
                "execution_mode": ticket.execution_mode,
                "blocked_by": list(ticket.blocked_by),
                "state": initial_state,
                "preexisting_integrated": initial_state == "integrated",
                "stage": None,
                "quality_failures": 0,
                "leaf_budget": new_leaf_budget(budget_config),
                "leaf_progress_events": [],
                "leaf_handoff": None,
                "leaf_results": {},
                "failure_kind": None,
                "candidate_ref": None,
                "delivery_candidate_ref": None,
                "artifact_generation": 0,
                "validated_stages": [],
                "delivery": {},
                "pr": None,
                "merge_authorization": None,
            }
        ledger: dict[str, Any] = {
            "schema": LEDGER_VERSION,
            "run_id": run_id,
            "run_state": "running",
            "ticket_folder": str(graph.folder),
            "ticket_order": list(graph.order),
            **budget_config,
            "provider": provider,
            "provider_mode": provider_mode,
            "provider_capabilities": provider_capabilities,
            "repo": repo,
            "worktree": worktree,
            "base_sha": base_sha,
            "cleanup": None,
            "tickets": tickets,
            "gates": {},
            "effects": {},
            "history": [],
        }
        kernel = cls(ledger)
        kernel._event("run-initialized", ticket_id=None)
        kernel._update_run_state()
        kernel._seal_history(0)
        for ticket_id in graph.order:
            if (
                tickets[ticket_id]["state"] == "pending"
                and tickets[ticket_id]["execution_mode"] == "HITL"
            ):
                history_start = len(kernel.ledger["history"])
                kernel._open_gate(
                    ticket_id,
                    category="human",
                    scope="ticket",
                    reason="HITL start approval required",
                    kind="start",
                )
                kernel._update_run_state()
                kernel._seal_history(history_start)
        kernel._validate_shape()
        return kernel

    @contextmanager
    def _transaction(self) -> Iterator[None]:
        snapshot = copy.deepcopy(self.ledger)
        history_start = len(self.ledger["history"])
        try:
            yield
            self._seal_history(history_start)
            self._validate_shape()
        except Exception:
            self.ledger.clear()
            self.ledger.update(snapshot)
            raise

    def _validate_shape(self) -> None:
        if self.ledger.get("schema") != LEDGER_VERSION:
            raise TransitionError(
                "ledger schema is incompatible with bounded leaves; "
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
        if self.ledger.get("provider_mode", "live") not in {"live", "simulated"}:
            raise TransitionError("invalid provider mode")
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
            if ticket.get("execution_mode") not in {"AFK", "HITL"}:
                raise TransitionError("invalid ticket execution mode")
            if "effective_mode" in ticket:
                raise TransitionError("effective_mode is not canonical ticket metadata")
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
                and not ticket.get("preexisting_integrated")
                and self.ledger.get("history")
            ):
                if len(start_gates) != 1:
                    raise TransitionError(
                        "HITL ticket requires exactly one persisted start gate"
                    )
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
            except LeafProtocolError as error:
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

    def _seal_history(self, start: int) -> None:
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
            event["snapshot"] = snapshot
            event.pop("hash", None)
            encoded = json.dumps(event, sort_keys=True, separators=(",", ":"))
            event["hash"] = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
            previous_hash = event["hash"]

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

    def _active_ticket_id(self) -> str | None:
        active = [
            ticket_id
            for ticket_id, ticket in self.ledger["tickets"].items()
            if ticket["state"] == "active"
        ]
        return active[0] if active else None

    def _dependency_ready(self, ticket: dict[str, Any]) -> bool:
        blockers = ticket["blocked_by"]
        if not blockers:
            return True
        states = [self._ticket(blocker)["state"] for blocker in blockers]
        if len(blockers) == 1:
            return states[0] in {"pr-open", "integrated"}
        return all(state == "integrated" for state in states)

    def ready_ids(self) -> list[str]:
        if self.ledger["run_state"] in {"aborted", "completed", "failed"}:
            return []
        if any(
            gate["state"] == "open" and gate["scope"] == "run"
            for gate in self.ledger["gates"].values()
        ):
            return []
        if self._active_ticket_id() is not None:
            return []
        return [
            ticket_id
            for ticket_id in self.ledger["ticket_order"]
            if self._ticket(ticket_id)["state"] == "pending"
            and self._dependency_ready(self._ticket(ticket_id))
        ]

    def dependency_blocked_ids(self) -> list[str]:
        return [
            ticket_id
            for ticket_id in self.ledger["ticket_order"]
            if self._ticket(ticket_id)["state"] == "pending"
            and not self._dependency_ready(self._ticket(ticket_id))
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
            self._event(
                "candidate-adopted",
                ticket_id,
                candidate_digest=candidate.digest,
                artifact_generation=ticket["artifact_generation"],
            )
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
            self._invalidate_leaf_artifacts(ticket)
            ticket["artifact_generation"] += 1
            ticket["merge_authorization"] = None
            self._event(
                "candidate-invalidated",
                ticket_id,
                candidate_digest=candidate.digest,
                artifact_generation=ticket["artifact_generation"],
            )

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
                            return copy.deepcopy(ticket["leaf_handoff"])
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
    ) -> str:
        with self._transaction():
            gate_id = self._open_gate(
                ticket_id,
                category=category,
                scope=scope,
                reason=reason,
                kind="dynamic",
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
            self._event("gate-passed", ticket_id, gate_id=gate_id, actor=actor)
            self._update_run_state()

    def _provider_delivery_gate_open(self, ticket_id: str) -> bool:
        return any(
            gate["ticket_id"] == ticket_id
            and gate["state"] == "open"
            and gate["category"]
            in {"provider-environment", "provider-pr", "delivery-pr-body"}
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
            if (
                ticket["state"] not in {"verified", "pr-open", "integrated"}
                and not provider_gated
                and not progress_only
            ):
                raise TransitionError(
                    "delivery metadata requires a validated terminal result"
                )
            normalized = copy.deepcopy(data)
            if ticket["delivery"].get(step) == normalized:
                return
            ticket["delivery"][step] = normalized
            self._event("delivery-recorded", ticket_id, step=step)

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
            self._invalidate_leaf_artifacts(ticket)
            ticket["artifact_generation"] += 1
            ticket["merge_authorization"] = None
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

    def prepare_reconciliation(
        self,
        ticket_id: str,
        candidate: CandidateRef,
        *,
        old_head: str,
        base_branch: str,
        expected_remote_sha: str,
    ) -> None:
        with self._transaction():
            ticket = self._ticket(ticket_id)
            if ticket["state"] != "pr-open" or not ticket["pr"]:
                raise TransitionError(
                    "reconciliation preparation requires an open PR"
                )
            if ticket["pr"]["head_sha"] != old_head:
                raise TransitionError("PR head changed before reconciliation")
            candidate.validate()
            ticket["candidate_ref"] = asdict(candidate)
            ticket["delivery_candidate_ref"] = asdict(candidate)
            ticket["state"] = "active"
            ticket["stage"] = "review"
            ticket["validated_stages"] = ["implement", "simplify"]
            self._invalidate_leaf_artifacts(ticket)
            ticket["artifact_generation"] += 1
            ticket["merge_authorization"] = None
            ticket["delivery"]["reconcile-prepare"] = {
                "old_head": old_head,
                "new_head": candidate.base_sha,
                "base": base_branch,
                "expected_remote_sha": expected_remote_sha,
                "candidate_ref": asdict(candidate),
                "artifact_generation": ticket["artifact_generation"],
            }
            self._event(
                "reconciliation-revalidation-required",
                ticket_id,
                old_head=old_head,
                new_head=candidate.base_sha,
                candidate_digest=candidate.digest,
                artifact_generation=ticket["artifact_generation"],
            )
            self._update_run_state()

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
                or prepared.get("base") != base_branch
            ):
                raise TransitionError(
                    "reconciliation publication contradicts prepared state"
                )
            ticket["pr"]["head_sha"] = new_head
            ticket["state"] = "pr-open"
            ticket["merge_authorization"] = None
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
        branch: str | None = None,
    ) -> None:
        with self._transaction():
            ticket = self._ticket(ticket_id)
            if ticket["state"] != "verified":
                raise TransitionError("PR recording requires verified finalization state")
            if not all((provider, pr_id, head_sha)):
                raise TransitionError("provider, pr_id, and head_sha are required")
            ticket["pr"] = {
                "provider": provider,
                "pr_id": pr_id,
                "head_sha": head_sha,
                "branch": branch
                or f"ticket-autopilot/{self.ledger['run_id']}/{ticket_id}",
            }
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
            if mode not in {"runner", "external"}:
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

    def record_integration(self, ticket_id: str, *, expected_head_sha: str) -> None:
        with self._transaction():
            ticket = self._ticket(ticket_id)
            authorization = ticket["merge_authorization"]
            if ticket["state"] != "pr-open" or not ticket["pr"]:
                raise TransitionError("integration requires an open PR")
            if ticket["pr"]["head_sha"] != expected_head_sha:
                raise TransitionError("integrated head differs from expected PR head")
            if not authorization or authorization["head_sha"] != expected_head_sha:
                raise TransitionError("current-head human merge authorization is required")
            ticket["state"] = "integrated"
            self._event("ticket-integrated", ticket_id, head_sha=expected_head_sha)
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
        elif self._active_ticket_id() is not None or self.ready_ids():
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

        tickets = {
            ticket_id: {
                "state": ticket["state"],
                "stage": ticket["stage"],
                "quality_failures": ticket["quality_failures"],
                "failure_kind": ticket["failure_kind"],
                "execution_mode": ticket["execution_mode"],
                "blocked_by": list(ticket["blocked_by"]),
                "candidate_ref": copy.deepcopy(ticket["candidate_ref"]),
                "delivery_candidate_ref": copy.deepcopy(
                    ticket["delivery_candidate_ref"]
                ),
                "artifact_generation": ticket["artifact_generation"],
                "validated_stages": list(ticket["validated_stages"]),
                "delivery": copy.deepcopy(ticket["delivery"]),
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
                    "leaf_interactions": ticket["leaf_budget"][
                        "interactions_consumed"
                    ],
                    "leaf_tool_calls": ticket["leaf_budget"][
                        "tool_calls_consumed"
                    ],
                    "leaf_wall_time": ticket["leaf_budget"][
                        "wall_time_consumed"
                    ],
                    "candidate_invalidations": sum(
                        1
                        for event in self.ledger["history"]
                        if event["ticket_id"] == ticket_id
                        and event["event"] == "candidate-invalidated"
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
            "schema": 1,
            "run_id": self.ledger["run_id"],
            "run_state": self.ledger["run_state"],
            "provider_mode": self.ledger.get("provider_mode", "live"),
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
