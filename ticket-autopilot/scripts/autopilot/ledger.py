from __future__ import annotations

import copy
import hashlib
import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, IO, Iterator

from .leaf_protocol import (
    LeafProtocolError,
    record_leaf_result as reduce_leaf_result,
    validate_handoff_progression,
    verification_checkpoint_identity,
)

if os.name == "nt":
    import msvcrt
else:
    import fcntl


LEDGER_VERSION = 2
ENVELOPE_VERSION = 1
PIPELINE_STAGES = (
    "implement",
    "simplify",
    "review",
    "qa-plan",
    "qa-execute",
    "verify",
    "finalize",
)
KNOWN_LEDGER_EVENTS = frozenset(
    {
        "run-initialized",
        "ticket-resumed",
        "ticket-activated",
        "candidate-adopted",
        "candidate-invalidated",
        "leaf-result-recorded",
        "stage-passed",
        "quality-failed",
        "ticket-failed",
        "gate-opened",
        "gate-passed",
        "effect-applied",
        "delivery-recorded",
        "delivery-candidate-recorded",
        "delivery-revalidation-required",
        "reconciliation-revalidation-required",
        "pr-opened",
        "pr-head-updated",
        "merge-authorized",
        "ticket-integrated",
        "run-aborted",
        "worktree-cleaned",
    }
)


class LedgerError(RuntimeError):
    """A persisted run ledger is absent, locked, corrupt, or incompatible."""


def _acquire_file_lock(handle: IO[str]) -> None:
    if os.name == "nt":
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write("\0")
            handle.flush()
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        return
    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)


def _release_file_lock(handle: IO[str]) -> None:
    if os.name == "nt":
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        return
    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _canonical_bytes(document: dict[str, Any]) -> bytes:
    return json.dumps(
        document, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


class AtomicLedger:
    def __init__(self, path: Path):
        self.path = path
        self.lock_path = path.with_suffix(path.suffix + ".lock")
        self._loaded_revision: str | None = None
        self._lock_depth = 0

    @contextmanager
    def locked(self) -> Iterator[None]:
        if self._lock_depth:
            self._lock_depth += 1
            try:
                yield
            finally:
                self._lock_depth -= 1
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.lock_path.open("a+", encoding="ascii") as handle:
            try:
                _acquire_file_lock(handle)
            except OSError as error:
                raise LedgerError(f"ledger is locked: {self.lock_path}") from error
            try:
                self._lock_depth = 1
                handle.seek(0)
                handle.truncate()
                handle.write(f"{os.getpid()}\n")
                handle.flush()
                os.fsync(handle.fileno())
                yield
            finally:
                self._lock_depth = 0
                _release_file_lock(handle)

    @contextmanager
    def run_locked(self) -> Iterator[None]:
        """Hold one process-crash-releasing lock across decision and effects."""
        with self.locked():
            yield

    @staticmethod
    def _atomic_write(path: Path, content: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, raw_tmp = tempfile.mkstemp(
            prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
        )
        tmp_path = Path(raw_tmp)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_path, path)
            if os.name != "nt":
                directory = os.open(path.parent, os.O_RDONLY)
                try:
                    os.fsync(directory)
                finally:
                    os.close(directory)
        finally:
            tmp_path.unlink(missing_ok=True)

    def save(self, document: dict[str, Any]) -> None:
        self._validate(document)
        payload_bytes = _canonical_bytes(document)
        envelope = {
            "envelope_schema": ENVELOPE_VERSION,
            "integrity": hashlib.sha256(payload_bytes).hexdigest(),
            "payload": document,
        }
        content = _canonical_bytes(envelope) + b"\n"
        with self.locked():
            if self._loaded_revision is not None and self.path.exists():
                current = hashlib.sha256(self.path.read_bytes()).hexdigest()
                if current != self._loaded_revision:
                    raise LedgerError(
                        "ledger changed since load; refusing to overwrite a newer state"
                    )
            self._atomic_write(self.path, content)
            self._loaded_revision = hashlib.sha256(content).hexdigest()

    def load(self) -> dict[str, Any]:
        with self.locked():
            try:
                content = self.path.read_bytes()
            except FileNotFoundError as error:
                raise LedgerError(f"ledger does not exist: {self.path}") from error
            try:
                envelope = json.loads(content)
            except json.JSONDecodeError as error:
                raise LedgerError(f"ledger is not valid JSON: {self.path}") from error
            envelope_schema = (
                envelope.get("envelope_schema")
                if isinstance(envelope, dict)
                else None
            )
            if (
                not isinstance(envelope, dict)
                or type(envelope_schema) is not int
                or envelope_schema != ENVELOPE_VERSION
                or set(envelope) != {"envelope_schema", "integrity", "payload"}
            ):
                raise LedgerError("ledger integrity envelope is invalid")
            document = envelope["payload"]
            actual = hashlib.sha256(_canonical_bytes(document)).hexdigest()
            if actual != envelope["integrity"]:
                raise LedgerError(f"ledger integrity mismatch: {self.path}")
            self._validate(document)
            self._loaded_revision = hashlib.sha256(content).hexdigest()
            return document

    @staticmethod
    def _validate(document: dict[str, Any]) -> None:
        if not isinstance(document, dict):
            raise LedgerError("ledger root must be an object")
        schema = document.get("schema")
        if type(schema) is not int or schema != LEDGER_VERSION:
            raise LedgerError(
                "ledger schema is incompatible with bounded leaves: "
                f"{schema!r}; start a new run or use an "
                "explicit validated migration"
            )
        if not isinstance(document.get("run_id"), str) or not document["run_id"]:
            raise LedgerError("ledger run_id must be a non-empty string")
        history = document.get("history")
        if not isinstance(history, list):
            raise LedgerError("ledger history must be a list")
        for expected, event in enumerate(history, start=1):
            if not isinstance(event, dict) or event.get("sequence") != expected:
                raise LedgerError(
                    f"ledger history sequence must be contiguous at {expected}"
                )
        hashed = ["hash" in event for event in history]
        if any(hashed) and not all(hashed):
            raise LedgerError("ledger history cannot mix hashed and legacy events")
        if all(hashed) and history:
            previous_hash = "0" * 64
            previous_snapshot: dict[str, Any] | None = None
            for event in history:
                recorded_hash = event.get("hash")
                unhashed = dict(event)
                unhashed.pop("hash", None)
                if unhashed.get("previous_hash") != previous_hash:
                    raise LedgerError("ledger history hash chain is discontinuous")
                encoded = json.dumps(
                    unhashed, sort_keys=True, separators=(",", ":"), ensure_ascii=False
                )
                actual_hash = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
                if actual_hash != recorded_hash:
                    raise LedgerError("ledger history event hash mismatch")
                snapshot = event.get("snapshot")
                if not isinstance(snapshot, dict) or "history" in snapshot:
                    raise LedgerError("ledger history event snapshot is malformed")
                AtomicLedger._validate_ticket_snapshot(snapshot)
                AtomicLedger._validate_event_transition(
                    previous_snapshot, event, snapshot
                )
                previous_snapshot = snapshot
                previous_hash = recorded_hash
            persisted_snapshot = {
                key: value for key, value in document.items() if key != "history"
            }
            if history[-1]["snapshot"] != persisted_snapshot:
                raise LedgerError(
                    "ledger snapshot cannot be reproduced from history"
                )
        AtomicLedger._validate_ticket_snapshot(document)

    @staticmethod
    def _candidate_digest(candidate: Any) -> str:
        if (
            not isinstance(candidate, dict)
            or set(candidate)
            != {
                "base_sha",
                "tree_oid",
                "ticket_digest",
                "contract_version",
            }
            or candidate.get("contract_version") != 1
            or any(
                not isinstance(candidate.get(key), str)
                or not candidate[key]
                for key in ("base_sha", "tree_oid", "ticket_digest")
            )
        ):
            raise LedgerError("event CandidateRef is malformed")
        encoded = json.dumps(
            candidate, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    @staticmethod
    def _derived_run_state(snapshot: dict[str, Any]) -> str:
        tickets = snapshot["tickets"]
        states = [ticket["state"] for ticket in tickets.values()]
        if states and all(state == "integrated" for state in states):
            return "completed"

        def depends_on_failed(ticket_id: str, seen: set[str]) -> bool:
            if ticket_id in seen:
                return False
            seen = {*seen, ticket_id}
            for blocker_id in tickets[ticket_id]["blocked_by"]:
                blocker = tickets[blocker_id]
                if blocker["state"] == "failed" or depends_on_failed(
                    blocker_id, seen
                ):
                    return True
            return False

        if any(state == "failed" for state in states) and all(
            ticket["state"] in {"failed", "integrated"}
            or (
                ticket["state"] == "pending"
                and depends_on_failed(ticket_id, set())
            )
            for ticket_id, ticket in tickets.items()
        ):
            return "failed"
        active = any(ticket["state"] == "active" for ticket in tickets.values())
        run_gate_open = any(
            gate.get("state") == "open" and gate.get("scope") == "run"
            for gate in snapshot["gates"].values()
        )

        def dependency_ready(ticket: dict[str, Any]) -> bool:
            blockers = ticket["blocked_by"]
            if not blockers:
                return True
            blocker_states = [tickets[item]["state"] for item in blockers]
            if len(blockers) == 1:
                return blocker_states[0] in {"pr-open", "integrated"}
            return all(state == "integrated" for state in blocker_states)

        ready = (
            not run_gate_open
            and any(
                ticket["state"] == "pending" and dependency_ready(ticket)
                for ticket in tickets.values()
            )
        )
        return "running" if active or ready else "waiting"

    @staticmethod
    def _validate_event_transition(
        previous: dict[str, Any] | None,
        event: dict[str, Any],
        current: dict[str, Any],
    ) -> None:
        name = event.get("event")
        ticket_id = event.get("ticket_id")
        details = event.get("details", {})
        expected_event_fields = {
            "sequence",
            "event",
            "ticket_id",
            "details",
            "previous_hash",
            "snapshot",
            "hash",
        }
        if set(event) != expected_event_fields:
            raise LedgerError("ledger history event fields are invalid")
        if name not in KNOWN_LEDGER_EVENTS:
            raise LedgerError(f"unknown ledger history event: {name!r}")
        if not isinstance(details, dict):
            raise LedgerError("ledger history event details must be an object")

        def require(condition: bool, message: str) -> None:
            if not condition:
                raise LedgerError(message)

        def require_details(*fields: str) -> None:
            require(
                set(details) == set(fields),
                f"{name} event payload is invalid",
            )

        if name == "run-initialized":
            require(previous is None, "run-initialized must be the first event")
            require(ticket_id is None, "run-initialized cannot own a ticket")
            require_details()
            require(current.get("cleanup") is None, "run initialized with cleanup")
            require(current.get("gates") == {}, "run initialized with gates")
            require(current.get("effects") == {}, "run initialized with effects")
            for ticket in current.get("tickets", {}).values():
                preexisting = bool(ticket.get("preexisting_integrated"))
                expected_state = "integrated" if preexisting else "pending"
                require(
                    ticket.get("state") == expected_state
                    and ticket.get("stage") is None
                    and ticket.get("candidate_ref") is None
                    and ticket.get("delivery_candidate_ref") is None
                    and ticket.get("artifact_generation") == 0
                    and ticket.get("validated_stages") == []
                    and ticket.get("delivery") == {}
                    and ticket.get("pr") is None
                    and ticket.get("merge_authorization") is None
                    and ticket.get("quality_failures") == 0
                    and isinstance(ticket.get("leaf_budget"), dict)
                    and ticket["leaf_budget"].get("interactions_consumed") == 0
                    and ticket["leaf_budget"].get("tool_calls_consumed") == 0
                    and ticket["leaf_budget"].get("wall_time_consumed") == 0
                    and ticket.get("leaf_progress_events") == []
                    and ticket.get("leaf_handoff") is None
                    and ticket.get("leaf_results") == {}
                    and ticket.get("failure_kind") is None
                    and "resume_pending" not in ticket,
                    "run-initialized ticket snapshot is impossible",
                )
            require(
                current.get("run_state")
                == AtomicLedger._derived_run_state(current),
                "run-initialized run state is impossible",
            )
            return
        if previous is None:
            raise LedgerError("history does not begin with run-initialized")

        require(
            set(previous) == set(current),
            f"{name} changed the ledger schema",
        )
        mutable_roots = {"run_state", "tickets", "gates", "effects", "cleanup"}
        for key in current:
            if key not in mutable_roots:
                require(
                    previous[key] == current[key],
                    f"{name} changed immutable run field {key}",
                )
        require(
            set(previous["tickets"]) == set(current["tickets"]),
            f"{name} changed the ticket set",
        )

        ticket_events = KNOWN_LEDGER_EVENTS - {
            "run-initialized",
            "run-aborted",
            "worktree-cleaned",
            "gate-opened",
            "gate-passed",
        }
        if name in ticket_events:
            require(
                isinstance(ticket_id, str)
                and ticket_id in previous["tickets"]
                and ticket_id in current["tickets"],
                f"{name} has an invalid ticket owner",
            )
        elif name in {"gate-opened", "gate-passed"}:
            require(
                ticket_id is None
                or (
                    isinstance(ticket_id, str)
                    and ticket_id in previous["tickets"]
                    and ticket_id in current["tickets"]
                ),
                f"{name} has an invalid gate owner",
            )
        else:
            require(ticket_id is None, f"{name} cannot own a ticket")

        previous_ticket = (
            previous["tickets"].get(ticket_id)
            if isinstance(ticket_id, str)
            else None
        )
        current_ticket = (
            current["tickets"].get(ticket_id)
            if isinstance(ticket_id, str)
            else None
        )

        def require_scope(
            *,
            ticket: bool = False,
            gates: bool = False,
            effects: bool = False,
            cleanup: bool = False,
        ) -> None:
            if ticket:
                for other_id in current["tickets"]:
                    if other_id != ticket_id:
                        require(
                            previous["tickets"][other_id]
                            == current["tickets"][other_id],
                            f"{name} changed unrelated ticket {other_id}",
                        )
            else:
                require(
                    previous["tickets"] == current["tickets"],
                    f"{name} changed ticket state",
                )
            if not gates:
                require(
                    previous["gates"] == current["gates"],
                    f"{name} changed gate state",
                )
            if not effects:
                require(
                    previous["effects"] == current["effects"],
                    f"{name} changed effect state",
                )
            if not cleanup:
                require(
                    previous["cleanup"] == current["cleanup"],
                    f"{name} changed cleanup state",
                )

        def changed_ticket_fields() -> set[str]:
            return {
                key
                for key in set(previous_ticket) | set(current_ticket)
                if previous_ticket.get(key) != current_ticket.get(key)
                or (key in previous_ticket) != (key in current_ticket)
            }

        def require_ticket_changes(
            allowed: set[str],
            required: set[str] = frozenset(),
        ) -> None:
            changed = changed_ticket_fields()
            require(
                required <= changed <= allowed,
                f"{name} changed unauthorized ticket fields: {sorted(changed)}",
            )

        if name == "ticket-activated":
            require_scope(ticket=True)
            require_details("candidate_digest")
            hitl_start_approved = (
                previous_ticket.get("execution_mode") == "AFK"
                or any(
                    gate.get("ticket_id") == ticket_id
                    and gate.get("kind") == "start"
                    and gate.get("state") == "passed"
                    for gate in previous["gates"].values()
                )
            )
            require(
                previous_ticket["state"] == "pending"
                and "resume_pending" not in previous_ticket
                and current_ticket["state"] == "active"
                and current_ticket["stage"] == PIPELINE_STAGES[0]
                and hitl_start_approved,
                "ticket-activated lifecycle is impossible",
            )
            require_ticket_changes(
                {"state", "stage", "candidate_ref"},
                {"state", "stage", "candidate_ref"},
            )
            require(
                details["candidate_digest"]
                == AtomicLedger._candidate_digest(
                    current_ticket["candidate_ref"]
                ),
                "ticket-activated CandidateRef payload is invalid",
            )
        elif name == "ticket-resumed":
            require_scope(ticket=True)
            require_details("candidate_digest")
            require(
                previous_ticket["state"] == "pending"
                and previous_ticket.get("resume_pending") is True
                and current_ticket["state"] == "active"
                and "resume_pending" not in current_ticket
                and current_ticket["stage"] == previous_ticket["stage"]
                and current_ticket["candidate_ref"]
                == previous_ticket["candidate_ref"],
                "ticket-resumed lifecycle is impossible",
            )
            require_ticket_changes(
                {"state", "resume_pending"},
                {"state", "resume_pending"},
            )
            require(
                details["candidate_digest"]
                == AtomicLedger._candidate_digest(
                    current_ticket["candidate_ref"]
                ),
                "ticket-resumed CandidateRef payload is invalid",
            )
        elif name in {"candidate-adopted", "candidate-invalidated"}:
            require_scope(ticket=True)
            require_details("candidate_digest", "artifact_generation")
            allowed = {
                "candidate_ref",
                "validated_stages",
                "artifact_generation",
                "merge_authorization",
                "leaf_progress_events",
                "leaf_handoff",
                "leaf_results",
                "leaf_budget",
            }
            if name == "candidate-invalidated":
                allowed.add("stage")
            require_ticket_changes(
                allowed,
                {"candidate_ref", "artifact_generation"},
            )
            require(
                previous_ticket["state"] == "active"
                and current_ticket["state"] == "active"
                and current_ticket["artifact_generation"]
                == previous_ticket["artifact_generation"] + 1
                and current_ticket["validated_stages"] == []
                and current_ticket["merge_authorization"] is None
                and (
                    name != "candidate-adopted"
                    or (
                        previous_ticket["stage"] == "implement"
                        and current_ticket["stage"] == "implement"
                    )
                )
                and (
                    name != "candidate-invalidated"
                    or current_ticket["stage"] == "implement"
                ),
                f"{name} lifecycle is impossible",
            )
            digest = AtomicLedger._candidate_digest(
                current_ticket["candidate_ref"]
            )
            require(
                details
                == {
                    "candidate_digest": digest,
                    "artifact_generation": current_ticket[
                        "artifact_generation"
                    ],
                },
                f"{name} CandidateRef payload is invalid",
            )
        elif name == "leaf-result-recorded":
            require_scope(ticket=True)
            require_details(
                "candidate_digest",
                "complete",
                "interaction",
                "progress_phase",
                "stage",
                "stop_reason",
                "tool_calls",
                "wall_time",
                "input_drift",
            )
            before_budget = previous_ticket.get("leaf_budget")
            after_budget = current_ticket.get("leaf_budget")
            before_progress = previous_ticket.get("leaf_progress_events")
            after_progress = current_ticket.get("leaf_progress_events")
            handoff = current_ticket.get("leaf_handoff")
            require(
                details["stage"] in {"review", "qa-plan", "qa-execute", "verify"}
                and previous_ticket["state"] == "active"
                and current_ticket["state"] == "active"
                and previous_ticket["stage"] == details["stage"]
                and current_ticket["stage"] == details["stage"]
                and current_ticket["candidate_ref"]
                == previous_ticket["candidate_ref"]
                and isinstance(before_budget, dict)
                and isinstance(after_budget, dict)
                and isinstance(before_progress, list)
                and isinstance(after_progress, list)
                and isinstance(handoff, dict),
                "leaf-result-recorded lifecycle is impossible",
            )
            require_ticket_changes(
                {"leaf_budget", "leaf_progress_events", "leaf_handoff"},
                {"leaf_budget", "leaf_progress_events", "leaf_handoff"},
            )
            require(
                isinstance(details["complete"], bool)
                and isinstance(details["interaction"], int)
                and not isinstance(details["interaction"], bool)
                and isinstance(details["tool_calls"], int)
                and not isinstance(details["tool_calls"], bool)
                and details["tool_calls"] >= 0
                and isinstance(details["wall_time"], int)
                and not isinstance(details["wall_time"], bool)
                and details["wall_time"] >= 0
                and isinstance(details["input_drift"], bool),
                "leaf-result-recorded resource payload is invalid",
            )
            require(
                after_budget["interactions_consumed"]
                == before_budget["interactions_consumed"] + 1
                == details["interaction"]
                and after_budget["tool_calls_consumed"]
                == before_budget["tool_calls_consumed"]
                + details["tool_calls"]
                and after_budget["wall_time_consumed"]
                == before_budget["wall_time_consumed"]
                + details["wall_time"],
                "leaf-result-recorded budget transition is invalid",
            )
            if details["input_drift"]:
                retained_progress = [
                    progress
                    for progress in before_progress
                    if progress.get("stage") != "verify"
                ]
                require(
                    details["stage"] == "verify"
                    and len(after_progress) == len(retained_progress) + 1
                    and after_progress[:-1] == retained_progress,
                    "leaf-result-recorded input drift reset is invalid",
                )
            else:
                require(
                    len(after_progress) == len(before_progress) + 1
                    and after_progress[:-1] == before_progress,
                    "leaf-result-recorded progress append is invalid",
                )
            latest = after_progress[-1]
            require(
                latest.get("candidate_ref") == current_ticket["candidate_ref"]
                and latest.get("stage") == details["stage"]
                and latest.get("phase") == details["progress_phase"]
                and latest.get("complete") == details["complete"]
                and latest.get("stop_reason") == details["stop_reason"]
                and latest.get("resource_delta")
                == {
                    "interactions": 1,
                    "tool_calls": details["tool_calls"],
                    "wall_time": details["wall_time"],
                }
                and handoff.get("candidate_ref")
                == current_ticket["candidate_ref"]
                and handoff.get("stage") == details["stage"]
                and handoff.get("progress_phase")
                == details["progress_phase"]
                and handoff.get("complete") == details["complete"]
                and handoff.get("stop_reason") == details["stop_reason"],
                "leaf-result-recorded handoff payload is invalid",
            )
            require(
                details["candidate_digest"]
                == AtomicLedger._candidate_digest(
                    current_ticket["candidate_ref"]
                ),
                "leaf-result-recorded CandidateRef payload is invalid",
            )
            try:
                previous_handoff = previous_ticket.get("leaf_handoff")
                if previous_handoff is not None:
                    if details["input_drift"]:
                        previous_identity = verification_checkpoint_identity(
                            previous_handoff
                        )
                        current_identity = verification_checkpoint_identity(handoff)
                        if (
                            previous_identity == current_identity
                            or (
                                previous_identity is None
                                and current_identity is None
                            )
                        ):
                            raise LeafProtocolError(
                                "verification input drift lacks a new identity"
                            )
                    else:
                        progression = validate_handoff_progression(
                            previous_handoff,
                            handoff,
                        )
                        if progression != "advance":
                            raise LeafProtocolError(
                                "persisted leaf progress must advance"
                            )
                replay_source_budget = copy.deepcopy(before_budget)
                if details["input_drift"]:
                    replay_source_budget["reservations"]["verify"][
                        "complete"
                    ] = False
                replay_budget, replay_handoff, replay_progress = (
                    reduce_leaf_result(
                        current,
                        replay_source_budget,
                        handoff,
                        expected_candidate_ref=current_ticket["candidate_ref"],
                        expected_stage=details["stage"],
                        tool_calls=details["tool_calls"],
                        wall_time=details["wall_time"],
                    )
                )
            except LeafProtocolError as error:
                raise LedgerError(
                    f"leaf-result-recorded replay is invalid: {error}"
                ) from error
            require(
                replay_budget == after_budget
                and replay_handoff == handoff
                and replay_progress == latest,
                "leaf-result-recorded deterministic replay differs",
            )
        elif name == "stage-passed":
            require_scope(ticket=True)
            require_details("stage")
            stage = details.get("stage")
            require(stage in PIPELINE_STAGES, "stage-passed stage is invalid")
            index = PIPELINE_STAGES.index(stage)
            expected_validated = list(PIPELINE_STAGES[: index + 1])
            if stage == PIPELINE_STAGES[-1]:
                expected_state = "verified"
                expected_stage = None
                required_changes = {"state", "stage", "validated_stages"}
            else:
                expected_state = "active"
                expected_stage = PIPELINE_STAGES[index + 1]
                required_changes = {"stage", "validated_stages"}
            leaf_stages = {"review", "qa-plan", "qa-execute", "verify"}
            allowed_changes = {"state", "stage", "validated_stages"}
            if stage in leaf_stages:
                required_changes |= {"leaf_handoff", "leaf_results"}
                allowed_changes |= {"leaf_handoff", "leaf_results"}
                prior_results = previous_ticket.get("leaf_results")
                current_results = current_ticket.get("leaf_results")
                require(
                    isinstance(previous_ticket.get("leaf_handoff"), dict)
                    and current_ticket.get("leaf_handoff") is None
                    and isinstance(prior_results, dict)
                    and isinstance(current_results, dict)
                    and current_results
                    == {
                        **prior_results,
                        stage: previous_ticket["leaf_handoff"],
                    },
                    "stage-passed leaf handoff archival is invalid",
                )
            require(
                previous_ticket["state"] == "active"
                and previous_ticket["stage"] == stage
                and current_ticket["state"] == expected_state
                and current_ticket["stage"] == expected_stage
                and current_ticket["validated_stages"] == expected_validated
                and current_ticket["candidate_ref"]
                == previous_ticket["candidate_ref"],
                "stage-passed lifecycle is impossible",
            )
            require_ticket_changes(
                allowed_changes,
                required_changes,
            )
        elif name == "quality-failed":
            require_scope(ticket=True)
            require_details("stage", "failures")
            stage = details["stage"]
            failures = details["failures"]
            require(
                stage in {"review", "qa-execute", "verify"}
                and previous_ticket["state"] == "active"
                and previous_ticket["stage"] == stage
                and isinstance(failures, int)
                and failures == previous_ticket["quality_failures"] + 1
                and current_ticket["quality_failures"] == failures
                and current_ticket["validated_stages"] == [],
                "quality-failed lifecycle is impossible",
            )
            if stage in {"review", "qa-execute", "verify"}:
                require(
                    current_ticket.get("leaf_progress_events") == []
                    and current_ticket.get("leaf_handoff") is None
                    and current_ticket.get("leaf_results") == {},
                    "quality-failed leaf retained semantic evidence",
                )
            if failures >= current["max_quality_failures"]:
                require(
                    current_ticket["state"] == "failed"
                    and current_ticket["stage"] is None
                    and current_ticket["failure_kind"] == "quality",
                    "quality-failed terminal transition is impossible",
                )
                required_changes = {
                    "state",
                    "stage",
                    "quality_failures",
                    "validated_stages",
                    "failure_kind",
                }
            else:
                require(
                    current_ticket["state"] == "active"
                    and current_ticket["stage"] == "implement"
                    and current_ticket["failure_kind"]
                    == previous_ticket["failure_kind"],
                    "quality-failed retry transition is impossible",
                )
                required_changes = {
                    "stage",
                    "quality_failures",
                    "validated_stages",
                }
            require_ticket_changes(
                {
                    "state",
                    "stage",
                    "quality_failures",
                    "validated_stages",
                    "failure_kind",
                    "leaf_progress_events",
                    "leaf_handoff",
                    "leaf_results",
                    "leaf_budget",
                },
                required_changes,
            )
        elif name == "ticket-failed":
            require_scope(ticket=True)
            require_details("stage", "failure_kind")
            stage = details["stage"]
            failure_kind = details["failure_kind"]
            require(
                stage in PIPELINE_STAGES
                and stage not in {"review", "qa-execute", "verify"}
                and previous_ticket["state"] == "active"
                and previous_ticket["stage"] == stage
                and current_ticket["state"] == "failed"
                and current_ticket["stage"] is None
                and current_ticket["validated_stages"] == []
                and current_ticket["failure_kind"] == failure_kind
                and failure_kind
                == ("finalization" if stage == "finalize" else "implementation"),
                "ticket-failed lifecycle is impossible",
            )
            require_ticket_changes(
                {"state", "stage", "validated_stages", "failure_kind"},
                {"state", "stage", "failure_kind"},
            )
        elif name == "gate-opened":
            require_scope(ticket=ticket_id is not None, gates=True)
            require_details("gate_id", "scope")
            gate_id = details.get("gate_id")
            gate = current.get("gates", {}).get(gate_id)
            new_gate_ids = set(current["gates"]) - set(previous["gates"])
            require(
                new_gate_ids == {gate_id}
                and all(
                    previous["gates"][key] == current["gates"][key]
                    for key in previous["gates"]
                )
                and isinstance(gate, dict)
                and gate.get("state") == "open"
                and gate.get("ticket_id") == ticket_id
                and gate.get("scope") == details["scope"]
                and details["scope"] in {"ticket", "run"}
                and isinstance(gate.get("category"), str)
                and bool(gate["category"])
                and isinstance(gate.get("reason"), str)
                and bool(gate["reason"])
                and isinstance(gate.get("kind"), str)
                and bool(gate["kind"])
                and gate.get("actor") is None
                and gate.get("evidence") is None,
                "gate-opened transition is impossible",
            )
            owner = ticket_id or "run"
            require(
                gate_id
                == f"gate:{owner}:{gate['kind']}:{len(current['gates'])}",
                "gate-opened ID is invalid",
            )
            if gate["kind"] == "start":
                require(
                    ticket_id is not None
                    and previous_ticket.get("execution_mode") == "HITL"
                    and previous_ticket.get("state") == "pending"
                    and previous_ticket.get("stage") is None
                    and gate.get("category") == "human"
                    and gate.get("scope") == "ticket"
                    and gate.get("reason") == "HITL start approval required"
                    and not any(
                        item.get("ticket_id") == ticket_id
                        and item.get("kind") == "start"
                        for item in previous["gates"].values()
                    ),
                    "HITL start gate is invalid",
                )
            if ticket_id is None:
                require(
                    set(gate)
                    == {
                        "gate_id",
                        "ticket_id",
                        "category",
                        "scope",
                        "reason",
                        "kind",
                        "state",
                        "actor",
                        "evidence",
                    },
                    "run gate fields are invalid",
                )
            else:
                require(
                    set(gate)
                    == {
                        "gate_id",
                        "ticket_id",
                        "category",
                        "scope",
                        "reason",
                        "kind",
                        "state",
                        "actor",
                        "evidence",
                        "resume_state",
                        "resume_stage",
                    }
                    and gate["resume_state"] == previous_ticket["state"]
                    and gate["resume_stage"] == previous_ticket["stage"]
                    and current_ticket["state"] == "gated"
                    and current_ticket["stage"] == previous_ticket["stage"],
                    "ticket gate resume state is invalid",
                )
                require_ticket_changes({"state"})
        elif name == "gate-passed":
            require_scope(ticket=ticket_id is not None, gates=True)
            require_details("gate_id", "actor")
            gate_id = details.get("gate_id")
            before_gate = previous["gates"].get(gate_id)
            after_gate = current["gates"].get(gate_id)
            require(
                set(previous["gates"]) == set(current["gates"])
                and isinstance(before_gate, dict)
                and isinstance(after_gate, dict)
                and before_gate.get("state") == "open"
                and after_gate.get("state") == "passed"
                and after_gate.get("actor") == details["actor"]
                and isinstance(after_gate.get("evidence"), str)
                and bool(after_gate["evidence"])
                and after_gate.get("ticket_id") == ticket_id
                and {
                    key
                    for key in set(before_gate) | set(after_gate)
                    if before_gate.get(key) != after_gate.get(key)
                }
                == {"state", "actor", "evidence"}
                and all(
                    previous["gates"][key] == current["gates"][key]
                    for key in previous["gates"]
                    if key != gate_id
                ),
                "gate-passed transition is impossible",
            )
            if ticket_id is not None:
                other_open = any(
                    key != gate_id
                    and gate.get("ticket_id") == ticket_id
                    and gate.get("state") == "open"
                    for key, gate in current["gates"].items()
                )
                if other_open:
                    require(
                        previous_ticket == current_ticket,
                        "gate-passed resumed a multiply-gated ticket",
                    )
                else:
                    active_other = any(
                        key != ticket_id and ticket["state"] == "active"
                        for key, ticket in previous["tickets"].items()
                    )
                    expected_state = before_gate["resume_state"]
                    if expected_state == "active" and active_other:
                        require(
                            current_ticket["state"] == "pending"
                            and current_ticket.get("resume_pending") is True,
                            "gate-passed did not defer active resume",
                        )
                    else:
                        require(
                            current_ticket["state"] == expected_state
                            and "resume_pending" not in current_ticket,
                            "gate-passed restored the wrong ticket state",
                        )
                    require(
                        current_ticket["stage"] == before_gate["resume_stage"],
                        "gate-passed restored the wrong ticket stage",
                    )
                    require_ticket_changes(
                        {"state", "stage", "resume_pending"}
                    )
        elif name == "effect-applied":
            require_scope(effects=True)
            require_details("effect", "idempotency_key")
            effect = details.get("effect")
            new_effects = set(current.get("effects", {})) - set(
                previous.get("effects", {})
            )
            key = details["idempotency_key"]
            expected_key_source = json.dumps(
                [
                    current["run_id"],
                    ticket_id,
                    effect,
                    current_ticket["candidate_ref"],
                ],
                sort_keys=True,
                separators=(",", ":"),
            )
            expected_key = hashlib.sha256(
                expected_key_source.encode("utf-8")
            ).hexdigest()
            require(
                new_effects == {key}
                and key == expected_key
                and all(
                    previous["effects"][item] == current["effects"][item]
                    for item in previous["effects"]
                )
                and current["effects"][key]
                == {
                    "ticket_id": ticket_id,
                    "effect": effect,
                    "state": "applied",
                }
                and current_ticket["state"]
                in {"verified", "pr-open", "integrated"},
                "effect-applied transition is impossible",
            )
        elif name == "delivery-recorded":
            require_scope(ticket=True)
            require_details("step")
            step = details["step"]
            require(
                isinstance(step, str)
                and bool(step)
                and previous_ticket["state"]
                in {"verified", "pr-open", "integrated"}
                and current_ticket["state"] == previous_ticket["state"],
                "delivery-recorded lifecycle is impossible",
            )
            before_delivery = previous_ticket["delivery"]
            after_delivery = current_ticket["delivery"]
            require(
                {
                    key
                    for key in set(before_delivery) | set(after_delivery)
                    if before_delivery.get(key) != after_delivery.get(key)
                    or (key in before_delivery) != (key in after_delivery)
                }
                == {step},
                "delivery-recorded changed an unrelated delivery step",
            )
            require_ticket_changes({"delivery"}, {"delivery"})
        elif name == "delivery-candidate-recorded":
            require_scope(ticket=True)
            require_details("candidate_digest")
            require(
                previous_ticket["state"] == "verified"
                and current_ticket["state"] == "verified"
                and current_ticket["delivery_candidate_ref"]
                != previous_ticket["delivery_candidate_ref"]
                and current_ticket["merge_authorization"] is None,
                "delivery-candidate-recorded lifecycle is impossible",
            )
            require_ticket_changes(
                {"delivery_candidate_ref", "merge_authorization"},
                {"delivery_candidate_ref"},
            )
            require(
                details["candidate_digest"]
                == AtomicLedger._candidate_digest(
                    current_ticket["delivery_candidate_ref"]
                ),
                "delivery-candidate-recorded payload is invalid",
            )
        elif name in {
            "delivery-revalidation-required",
            "reconciliation-revalidation-required",
        }:
            require_scope(ticket=True)
            base_fields = {"candidate_digest", "artifact_generation"}
            if name == "reconciliation-revalidation-required":
                require_details(
                    "old_head",
                    "new_head",
                    "candidate_digest",
                    "artifact_generation",
                )
                delivery_step = "reconcile-prepare"
                expected_before_state = "pr-open"
            else:
                require_details(*sorted(base_fields))
                delivery_step = "prepared"
                expected_before_state = "verified"
            require(
                previous_ticket["state"] == expected_before_state
                and current_ticket["state"] == "active"
                and current_ticket["stage"] == "review"
                and current_ticket["validated_stages"]
                == ["implement", "simplify"]
                and current_ticket["artifact_generation"]
                == previous_ticket["artifact_generation"] + 1
                and current_ticket["candidate_ref"]
                == current_ticket["delivery_candidate_ref"]
                and current_ticket["merge_authorization"] is None,
                f"{name} lifecycle is impossible",
            )
            require_ticket_changes(
                {
                    "candidate_ref",
                    "delivery_candidate_ref",
                    "state",
                    "stage",
                    "validated_stages",
                    "artifact_generation",
                    "merge_authorization",
                    "delivery",
                    "leaf_progress_events",
                    "leaf_handoff",
                    "leaf_results",
                    "leaf_budget",
                },
                {
                    "candidate_ref",
                    "delivery_candidate_ref",
                    "state",
                    "stage",
                    "validated_stages",
                    "artifact_generation",
                    "delivery",
                },
            )
            before_delivery = previous_ticket["delivery"]
            after_delivery = current_ticket["delivery"]
            require(
                {
                    key
                    for key in set(before_delivery) | set(after_delivery)
                    if before_delivery.get(key) != after_delivery.get(key)
                    or (key in before_delivery) != (key in after_delivery)
                }
                == {delivery_step},
                f"{name} changed unrelated delivery metadata",
            )
            candidate_digest = AtomicLedger._candidate_digest(
                current_ticket["candidate_ref"]
            )
            require(
                details["candidate_digest"] == candidate_digest
                and details["artifact_generation"]
                == current_ticket["artifact_generation"],
                f"{name} payload is invalid",
            )
            delivery = after_delivery[delivery_step]
            require(
                delivery.get("candidate_ref")
                == current_ticket["candidate_ref"]
                and delivery.get("artifact_generation")
                == current_ticket["artifact_generation"],
                f"{name} delivery CandidateRef is invalid",
            )
            if name == "reconciliation-revalidation-required":
                require(
                    details["old_head"] == delivery.get("old_head")
                    and details["new_head"] == delivery.get("new_head")
                    and details["new_head"]
                    == current_ticket["candidate_ref"]["base_sha"]
                    and previous_ticket.get("pr", {}).get("head_sha")
                    == details["old_head"],
                    "reconciliation payload contradicts PR state",
                )
        elif name == "pr-opened":
            require_scope(ticket=True)
            require_details("provider", "pr_id")
            pr = current_ticket.get("pr")
            require(
                previous_ticket["state"] == "verified"
                and previous_ticket.get("pr") is None
                and current_ticket["state"] == "pr-open"
                and isinstance(pr, dict)
                and set(pr) == {"provider", "pr_id", "head_sha", "branch"}
                and pr["provider"] == details["provider"]
                and pr["pr_id"] == details["pr_id"]
                and all(isinstance(pr[key], str) and pr[key] for key in pr),
                "pr-opened transition is impossible",
            )
            require_ticket_changes({"state", "pr"}, {"state", "pr"})
        elif name == "pr-head-updated":
            require_scope(ticket=True)
            require(
                set(details)
                in (
                    {"expected_old", "new"},
                    {"expected_old", "new", "base"},
                ),
                "pr-head-updated event payload is invalid",
            )
            before_pr = previous_ticket.get("pr")
            after_pr = current_ticket.get("pr")
            require(
                isinstance(before_pr, dict)
                and isinstance(after_pr, dict),
                "pr-head-updated requires before and after PR records",
            )
            require(
                before_pr.get("head_sha") == details["expected_old"],
                "pr-head-updated old head payload is invalid",
            )
            require(
                after_pr.get("head_sha") == details["new"],
                "pr-head-updated new head payload is invalid",
            )
            changed_pr_fields = {
                key
                for key in set(before_pr) | set(after_pr)
                if before_pr.get(key) != after_pr.get(key)
            }
            expected_pr_changes = (
                set()
                if details["expected_old"] == details["new"]
                else {"head_sha"}
            )
            require(
                changed_pr_fields == expected_pr_changes,
                "pr-head-updated changed unrelated PR fields: "
                f"{sorted(changed_pr_fields)}",
            )
            require(
                current_ticket["merge_authorization"] is None,
                "pr-head-updated retained merge authorization",
            )
            if "base" in details:
                prepared = previous_ticket["delivery"].get(
                    "reconcile-prepare", {}
                )
                require(
                    previous_ticket["state"] == "verified"
                    and current_ticket["state"] == "pr-open"
                    and prepared.get("old_head") == details["expected_old"]
                    and prepared.get("new_head") == details["new"]
                    and prepared.get("base") == details["base"],
                    "reconciled pr-head-updated transition is impossible",
                )
                require_ticket_changes(
                    {"state", "pr", "merge_authorization"},
                    {"state"},
                )
            else:
                require(
                    previous_ticket["state"] == "pr-open"
                    and current_ticket["state"] == "pr-open",
                    "pr-head-updated lifecycle is impossible",
                )
                require_ticket_changes(
                    {"pr", "merge_authorization"},
                )
        elif name == "ticket-integrated":
            require_scope(ticket=True)
            require_details("head_sha")
            authorization = current_ticket.get("merge_authorization")
            require(
                previous_ticket["state"] == "pr-open"
                and current_ticket["state"] == "integrated"
                and current_ticket["pr"] == previous_ticket["pr"]
                and current_ticket["merge_authorization"]
                == previous_ticket["merge_authorization"]
                and isinstance(authorization, dict)
                and authorization.get("head_sha") == details["head_sha"]
                and current_ticket["pr"].get("head_sha")
                == details["head_sha"],
                "ticket-integrated transition is impossible",
            )
            require_ticket_changes({"state"}, {"state"})
        elif name == "merge-authorized":
            require_scope(ticket=True)
            require_details("actor", "head_sha", "mode")
            authorization = current_ticket.get("merge_authorization")
            require(
                previous_ticket["state"] == "pr-open"
                and current_ticket["state"] == "pr-open"
                and previous_ticket["pr"] == current_ticket["pr"]
                and isinstance(authorization, dict)
                and set(authorization)
                == {"actor", "head_sha", "evidence", "mode"}
                and authorization["actor"] == details["actor"]
                and authorization["head_sha"] == details["head_sha"]
                and authorization["head_sha"]
                == current_ticket["pr"]["head_sha"]
                and authorization["mode"] == details["mode"]
                and authorization["mode"] in {"runner", "external"}
                and isinstance(authorization["evidence"], str)
                and bool(authorization["evidence"]),
                "merge-authorized transition is impossible",
            )
            require_ticket_changes(
                {"merge_authorization"}, {"merge_authorization"}
            )
        elif name == "run-aborted":
            require_scope()
            require_details("actor", "reason")
            require(
                previous["run_state"] not in {"completed", "aborted"}
                and current["run_state"] == "aborted"
                and all(
                    isinstance(details[key], str) and details[key]
                    for key in ("actor", "reason")
                ),
                "run-aborted transition is impossible",
            )
        elif name == "worktree-cleaned":
            require_scope(cleanup=True)
            require_details("worktree", "resume_abandoned")
            cleanup = current.get("cleanup")
            require(
                previous["run_state"] != "running"
                and current["run_state"] == previous["run_state"]
                and previous.get("cleanup") is None
                and isinstance(cleanup, dict)
                and cleanup
                == {
                    "recorded": True,
                    "worktree": details["worktree"],
                    "worktree_removed": cleanup.get("worktree_removed"),
                    "resume_abandoned": details["resume_abandoned"],
                    "remote_state_deleted": False,
                }
                and isinstance(cleanup["worktree_removed"], bool)
                and isinstance(details["worktree"], str)
                and bool(details["worktree"])
                and isinstance(details["resume_abandoned"], bool),
                "worktree-cleaned transition is impossible",
            )

        if name not in {"run-aborted", "worktree-cleaned"}:
            require(
                current["run_state"]
                == AtomicLedger._derived_run_state(current),
                f"{name} produced an impossible run state",
            )

    @staticmethod
    def _validate_ticket_snapshot(document: dict[str, Any]) -> None:
        tickets = document.get("tickets")
        if tickets is not None:
            if not isinstance(tickets, dict) or not isinstance(
                document.get("ticket_order"), list
            ):
                raise LedgerError("ledger ticket snapshot is malformed")
            if document["ticket_order"] != list(tickets):
                raise LedgerError("ledger ticket order differs from ticket snapshot")
            active = [
                ticket
                for ticket in tickets.values()
                if isinstance(ticket, dict) and ticket.get("state") == "active"
            ]
            if len(active) > 1:
                raise LedgerError("ledger has more than one active mutating ticket")
            valid_ticket_states = {
                "pending",
                "active",
                "gated",
                "failed",
                "verified",
                "pr-open",
                "integrated",
            }
            stages = (
                "implement",
                "simplify",
                "review",
                "qa-plan",
                "qa-execute",
                "verify",
                "finalize",
            )
            for ticket in tickets.values():
                if (
                    not isinstance(ticket, dict)
                    or ticket.get("state") not in valid_ticket_states
                ):
                    raise LedgerError("ledger contains an invalid ticket state")
                if ticket.get("execution_mode") not in {"AFK", "HITL"}:
                    raise LedgerError("ledger contains an invalid execution mode")
                if "effective_mode" in ticket:
                    raise LedgerError(
                        "ledger contains non-canonical effective_mode"
                    )
                state = ticket["state"]
                stage = ticket.get("stage")
                candidate = ticket.get("candidate_ref")
                validated = ticket.get("validated_stages", [])
                if not isinstance(validated, list) or validated != list(
                    stages[: len(validated)]
                ):
                    raise LedgerError(
                        "ledger validated stages are not a pipeline prefix"
                    )
                if state == "active" and (
                    stage not in stages or not isinstance(candidate, dict)
                ):
                    raise LedgerError("active ticket has no valid stage/CandidateRef")
                if state in {"failed", "verified", "pr-open", "integrated"} and stage is not None:
                    raise LedgerError("terminal ticket retains an active stage")
                preexisting = bool(ticket.get("preexisting_integrated"))
                if (
                    state in {"verified", "pr-open", "integrated"}
                    and not preexisting
                    and validated != list(stages)
                ):
                    raise LedgerError(
                        "delivered ticket lacks complete stage validation"
                    )
                if (
                    state in {"pr-open", "integrated"}
                    and not preexisting
                    and not isinstance(ticket.get("pr"), dict)
                ):
                    raise LedgerError("delivered ticket has no PR record")
                authorization = ticket.get("merge_authorization")
                if authorization is not None:
                    pr = ticket.get("pr")
                    if (
                        not isinstance(pr, dict)
                        or authorization.get("head_sha") != pr.get("head_sha")
                    ):
                        raise LedgerError(
                            "merge authorization is stale for the PR snapshot"
                        )
            if document.get("run_state") not in {
                "running",
                "waiting",
                "completed",
                "failed",
                "aborted",
            }:
                raise LedgerError("ledger contains an invalid run state")
            run_state = document.get("run_state")
            states = [ticket["state"] for ticket in tickets.values()]
            if run_state == "completed" and not all(
                state == "integrated" for state in states
            ):
                raise LedgerError("completed run contains non-integrated tickets")
            if run_state == "failed" and not any(
                state == "failed" for state in states
            ):
                raise LedgerError("failed run contains no failed ticket")
            gates = document.get("gates", {})
            if not isinstance(gates, dict):
                raise LedgerError("ledger gates must be an object")
            for gate_id, gate in gates.items():
                if not isinstance(gate, dict) or gate.get("gate_id") != gate_id:
                    raise LedgerError("ledger contains a malformed gate")
                if gate.get("state") not in {"open", "passed", "failed", "waived"}:
                    raise LedgerError("ledger contains an invalid gate state")
                owner = gate.get("ticket_id")
                if owner is not None and owner not in tickets:
                    raise LedgerError("ledger gate owns an unknown ticket")
                if gate.get("kind") == "start" and (
                    owner is None
                    or tickets[owner].get("execution_mode") != "HITL"
                    or gate.get("category") != "human"
                    or gate.get("scope") != "ticket"
                    or gate.get("resume_state") != "pending"
                    or gate.get("resume_stage") is not None
                ):
                    raise LedgerError("ledger contains an invalid HITL start gate")
                if gate.get("state") == "open" and owner is not None:
                    if tickets[owner]["state"] != "gated":
                        raise LedgerError("open ticket gate does not gate its owner")
