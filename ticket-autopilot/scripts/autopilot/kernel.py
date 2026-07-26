from __future__ import annotations

import copy
import hashlib
import json
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from typing import Any, Iterator

from .contract import TicketGraph
from .ledger import LEDGER_VERSION


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
        supervision: str = "AFK",
        provider: str | None = None,
        provider_mode: str = "live",
        worktree: str | None = None,
        repo: str | None = None,
        provider_capabilities: dict[str, object] | None = None,
        base_sha: str | None = None,
    ) -> "Kernel":
        if max_quality_failures < 1:
            raise TransitionError("max_quality_failures must be at least 1")
        if supervision not in {"AFK", "HITL"}:
            raise TransitionError("supervision must be AFK or HITL")
        if provider_mode not in {"live", "simulated"}:
            raise TransitionError("provider_mode must be live or simulated")
        tickets: dict[str, dict[str, Any]] = {}
        for ticket_id in graph.order:
            ticket = graph.tickets[ticket_id]
            effective_mode = "HITL" if "HITL" in {ticket.execution_mode, supervision} else "AFK"
            initial_state = (
                "integrated" if ticket_id in graph.completed_ids else "pending"
            )
            tickets[ticket_id] = {
                "ticket_id": ticket_id,
                "path": str(ticket.path),
                "ticket_digest": ticket.digest,
                "execution_mode": ticket.execution_mode,
                "effective_mode": effective_mode,
                "blocked_by": list(ticket.blocked_by),
                "state": initial_state,
                "preexisting_integrated": initial_state == "integrated",
                "stage": None,
                "quality_failures": 0,
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
            "max_quality_failures": max_quality_failures,
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
                and tickets[ticket_id]["effective_mode"] == "HITL"
            ):
                history_start = len(kernel.ledger["history"])
                kernel._open_gate(
                    ticket_id,
                    category="approval",
                    scope="ticket",
                    reason="HITL start approval required",
                    kind="start",
                )
                kernel._update_run_state()
                kernel._seal_history(history_start)
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
            raise TransitionError("unsupported ledger schema")
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
        active = [item for item in tickets.values() if item["state"] == "active"]
        if len(active) > 1:
            raise TransitionError("more than one active mutating ticket")
        history = self.ledger.get("history")
        if not isinstance(history, list):
            raise TransitionError("history must be a list")
        for sequence, event in enumerate(history, start=1):
            if event.get("sequence") != sequence:
                raise TransitionError("history sequence is not contiguous")

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
            if result == "gated":
                self._open_gate(
                    ticket_id,
                    category="environment",
                    scope="ticket",
                    reason=f"{stage} reported a gate",
                    kind="stage",
                )
            elif result == "pass":
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

    def record_finalization_effect(self, ticket_id: str, effect: str) -> bool:
        with self._transaction():
            ticket = self._ticket(ticket_id)
            if ticket["state"] not in {"verified", "pr-open", "integrated"}:
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
            if ticket["state"] not in {"verified", "pr-open", "integrated"}:
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
            ticket["artifact_generation"] += 1
            ticket["merge_authorization"] = None
            ticket["delivery"]["prepared"] = {
                "candidate_ref": asdict(candidate),
                "artifact_generation": ticket["artifact_generation"],
            }
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
        tickets = {
            ticket_id: {
                "state": ticket["state"],
                "stage": ticket["stage"],
                "quality_failures": ticket["quality_failures"],
                "failure_kind": ticket["failure_kind"],
                "blocked_by": list(ticket["blocked_by"]),
                "candidate_ref": copy.deepcopy(ticket["candidate_ref"]),
                "delivery_candidate_ref": copy.deepcopy(
                    ticket["delivery_candidate_ref"]
                ),
                "artifact_generation": ticket["artifact_generation"],
                "validated_stages": list(ticket["validated_stages"]),
                "delivery": copy.deepcopy(ticket["delivery"]),
                "pr": copy.deepcopy(ticket["pr"]),
                "merge_authorization": copy.deepcopy(
                    ticket["merge_authorization"]
                ),
            }
            for ticket_id, ticket in self.ledger["tickets"].items()
        }
        return {
            "schema": 1,
            "run_id": self.ledger["run_id"],
            "run_state": self.ledger["run_state"],
            "provider_mode": self.ledger.get("provider_mode", "live"),
            "next_ready": self.next_ready_id(),
            "ready": self.ready_ids(),
            "dependency_blocked": self.dependency_blocked_ids(),
            "open_gates": self.human_gated_ids(),
            "cleanup": copy.deepcopy(self.ledger.get("cleanup")),
            "tickets": tickets,
        }
