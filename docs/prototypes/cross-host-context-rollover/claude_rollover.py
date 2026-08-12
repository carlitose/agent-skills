"""Claude Code stream-json tracer bullet for the frozen rollover policy."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
import uuid

from rollover_common import (
    PrivateRegistry,
    PrototypeError,
    THRESHOLD_TOKENS,
    ValidatedHandoff,
    validate_handoff,
)


FIXTURE_SCHEMA = 1
ADAPTER_ID = "claude-code-stream-json"
REQUIRED_FLAGS = (
    "--autocompact",
    "--forward-subagent-text",
    "--include-hook-events",
    "--include-partial-messages",
    "--input-format",
    "--output-format",
    "--replay-user-messages",
    "--session-id",
)
REQUIRED_HOOK_EVENTS = ("SessionStart", "Stop", "PreCompact", "PostCompact")


def _valid_uuid(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        return str(uuid.UUID(value)) == value.lower()
    except (ValueError, AttributeError):
        return False


@dataclass(frozen=True)
class ClaudeSurface:
    version: str
    observed_flags: tuple[str, ...]
    autocompact_tokens: int

    @classmethod
    def from_fixture(cls, fixture: dict[str, Any]) -> "ClaudeSurface":
        installed = fixture.get("installed_surface")
        if not isinstance(installed, dict):
            raise PrototypeError("Claude fixture lacks an installed surface")
        flags = installed.get("observed_flags")
        if not isinstance(flags, list) or not all(
            isinstance(item, str) and item for item in flags
        ):
            raise PrototypeError("Claude fixture flag surface is malformed")
        surface = cls(
            version=installed.get("version"),
            observed_flags=tuple(flags),
            autocompact_tokens=installed.get("autocompact_tokens"),
        )
        surface.validate()
        return surface

    def validate(self) -> None:
        if not isinstance(self.version, str) or not self.version:
            raise PrototypeError("Claude version binding must be non-empty")
        missing = sorted(set(REQUIRED_FLAGS) - set(self.observed_flags))
        if missing:
            raise PrototypeError(
                "installed Claude surface lacks required flags: " + ", ".join(missing)
            )
        if (
            type(self.autocompact_tokens) is not int
            or self.autocompact_tokens <= THRESHOLD_TOKENS
        ):
            raise PrototypeError("Claude autocompact must be above the rollover threshold")


def _direct_user_text(message: Any) -> bool:
    if not isinstance(message, dict) or message.get("role") != "user":
        return False
    content = message.get("content")
    if isinstance(content, str):
        return bool(content.strip())
    if not isinstance(content, list):
        return False
    has_text = False
    for item in content:
        if not isinstance(item, dict):
            return False
        item_type = item.get("type")
        if item_type == "tool_result":
            return False
        if item_type == "text" and isinstance(item.get("text"), str):
            has_text = has_text or bool(item["text"].strip())
    return has_text


def project_messages(stream_document: dict[str, Any]) -> dict[str, Any]:
    """Project CR-01 logical messages from prospective stream-json events."""
    if stream_document.get("schema") != FIXTURE_SCHEMA:
        raise PrototypeError("unsupported Claude stream fixture schema")
    if stream_document.get("identity_source") != "controller-owned-event-id":
        raise PrototypeError("Claude stream events lack controller-owned identities")
    events = stream_document.get("events")
    if not isinstance(events, list):
        raise PrototypeError("Claude stream events must be a list")

    user_messages = 0
    assistant_messages = 0
    seen_users: set[str] = set()
    seen_results: set[str] = set()
    for event in events:
        if not isinstance(event, dict) or not isinstance(event.get("type"), str):
            raise PrototypeError("malformed Claude stream event")
        event_type = event["type"]
        if event_type == "user":
            if event.get("isReplay") is True or event.get("parent_tool_use_id") is not None:
                continue
            if not _direct_user_text(event.get("message")):
                continue
            event_id = event.get("controller_event_id")
            if not isinstance(event_id, str) or not event_id:
                raise PrototypeError("Claude user controller identity is required")
            if event_id in seen_users:
                continue
            seen_users.add(event_id)
            user_messages += 1
        elif event_type == "result":
            if not (
                event.get("subtype") == "success"
                and event.get("is_error") is False
                and isinstance(event.get("result"), str)
                and event["result"].strip()
            ):
                continue
            event_id = event.get("controller_event_id")
            if not isinstance(event_id, str) or not event_id:
                raise PrototypeError("Claude result controller identity is required")
            if event_id in seen_results:
                continue
            seen_results.add(event_id)
            assistant_messages += 1

    return {
        "schema": FIXTURE_SCHEMA,
        "adapter": ADAPTER_ID,
        "source": "prospective stream-json controller events",
        "user_messages": user_messages,
        "assistant_messages": assistant_messages,
        "total_messages": user_messages + assistant_messages,
        "assistant_count_available": True,
    }


def project_context_pressure(
    status_line: dict[str, Any],
    *,
    precompact: dict[str, Any] | None = None,
) -> dict[str, Any]:
    context = status_line.get("context_window")
    if not isinstance(context, dict):
        raise PrototypeError("Claude status line lacks context_window")
    input_tokens = context.get("total_input_tokens")
    output_tokens = context.get("total_output_tokens")
    if input_tokens is None and output_tokens is None:
        current = None
    elif type(input_tokens) is int and input_tokens >= 0 and type(output_tokens) is int and output_tokens >= 0:
        current = input_tokens + output_tokens
    else:
        raise PrototypeError("Claude current context token fields are incomplete or invalid")
    used = context.get("used_percentage")
    remaining = context.get("remaining_percentage")
    for label, value in (("used", used), ("remaining", remaining)):
        if value is not None and (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or value < 0
            or value > 100
        ):
            raise PrototypeError(f"Claude {label} percentage is invalid")
    precompact_seen = False
    precompact_trigger = None
    if precompact is not None:
        if precompact.get("hook_event_name") != "PreCompact":
            raise PrototypeError("context-pressure hook must be PreCompact")
        precompact_seen = True
        precompact_trigger = precompact.get("trigger")
    return {
        "schema": FIXTURE_SCHEMA,
        "adapter": ADAPTER_ID,
        "current_context_tokens": current,
        "used_percentage": used,
        "remaining_percentage": remaining,
        "precompact_seen": precompact_seen,
        "precompact_trigger": precompact_trigger,
        "message_count_source": None,
    }


@dataclass
class StatusTrigger:
    source_session_id: str
    surface: ClaudeSurface
    state: str = "monitoring"
    generation: int = 0
    current_context_tokens: int | None = None

    def observe(self, status_line: dict[str, Any]) -> None:
        self.surface.validate()
        if status_line.get("session_id") != self.source_session_id:
            raise PrototypeError("Claude status line session mismatch")
        context = status_line.get("context_window")
        if not isinstance(context, dict):
            raise PrototypeError("Claude status line lacks context_window")
        window = context.get("context_window_size")
        if type(window) is not int or window <= THRESHOLD_TOKENS:
            raise PrototypeError("Claude context_window_size cannot reach threshold")
        pressure = project_context_pressure(status_line)
        current = pressure["current_context_tokens"]
        self.current_context_tokens = current
        if current is not None and current >= THRESHOLD_TOKENS and self.state == "monitoring":
            self.state = "rollover-pending"
            self.generation += 1

    def observe_precompact(self, event: dict[str, Any]) -> str:
        if (
            event.get("hook_event_name") != "PreCompact"
            or event.get("session_id") != self.source_session_id
        ):
            raise PrototypeError("PreCompact event is not source-session-bound")
        if self.state != "rollover-pending":
            raise PrototypeError("PreCompact occurred before the rollover threshold")
        return "pending-generation-preserved"


class AmbiguousSessionStart(PrototypeError):
    """Session creation may have happened; replay must retain the UUID."""


class ObservedSessionStartFailure(PrototypeError):
    """Session creation definitely did not happen; a bounded retry may advance."""


class FakeClaudeProcess:
    """Local stream controller boundary with UUID-idempotent synthetic sessions."""

    def __init__(self, source_session_id: str) -> None:
        self.sessions: dict[str, dict[str, Any]] = {
            source_session_id: {"source": True, "prompts": []}
        }
        self.calls: list[dict[str, Any]] = []
        self.next_start_failure: str | None = None

    def can_resume(self, session_id: str) -> bool:
        return session_id in self.sessions

    def start_session(
        self,
        *,
        session_id: str,
        argv: list[str],
        stream_input: dict[str, Any],
    ) -> dict[str, Any]:
        call = {
            "operation": "start-session",
            "session_id": session_id,
            "argv": list(argv),
            "stream_input": stream_input,
        }
        self.calls.append(call)
        if self.next_start_failure == "observed":
            self.next_start_failure = None
            raise ObservedSessionStartFailure("observed Claude start failure")

        existing = self.sessions.get(session_id)
        if existing is None:
            receipt = f"result:{session_id}"
            existing = {
                "source": False,
                "argv": list(argv),
                "stream_input": stream_input,
                "bootstrap_receipt": receipt,
                "prompts": [],
            }
            self.sessions[session_id] = existing
        if self.next_start_failure == "ambiguous":
            self.next_start_failure = None
            raise AmbiguousSessionStart("Claude start response was lost")
        return {
            "session_id": session_id,
            "bootstrap_receipt": existing["bootstrap_receipt"],
            "events": [
                {"type": "system", "subtype": "init", "session_id": session_id},
                {
                    "type": "result",
                    "subtype": "success",
                    "is_error": False,
                    "session_id": session_id,
                    "uuid": existing["bootstrap_receipt"],
                    "result": "frontier restored",
                },
            ],
        }

    def send_prompt(self, session_id: str, prompt: str) -> None:
        if session_id not in self.sessions or not prompt:
            raise PrototypeError("held prompt requires an existing target session")
        self.calls.append(
            {"operation": "send-prompt", "session_id": session_id, "prompt": prompt}
        )
        self.sessions[session_id]["prompts"].append(prompt)


def build_bootstrap(handoff: ValidatedHandoff) -> str:
    return "\n".join(
        (
            f"Restore only from validated handoff: {handoff.path}",
            "Read the Wayfinder path recorded in that handoff.",
            "Run ticket-autopilot ticket-list on its ticket folder.",
            "If a run ID is present, run ticket-autopilot status for that exact run.",
            "Report the reconstructed map, inventory, run status, and next frontier.",
            "Do not read or copy transcript content.",
        )
    )


def reconstruct_frontier(
    handoff: ValidatedHandoff,
    *,
    ticket_list: Callable[[str], Any],
    run_status: Callable[[str], Any],
) -> dict[str, Any]:
    pointers = handoff.pointers
    map_text = Path(pointers.wayfinder_path).read_text(encoding="utf-8")
    if not map_text.strip():
        raise PrototypeError("Wayfinder readback is empty")
    inventory = ticket_list(pointers.ticket_folder)
    if inventory is None:
        raise PrototypeError("ticket-list readback is unavailable")
    status = run_status(pointers.run_id) if pointers.run_id is not None else None
    if pointers.run_id is not None and status is None:
        raise PrototypeError("ticket-autopilot status readback is unavailable")
    return {
        "map_read": True,
        "ticket_inventory": inventory,
        "run_status": status,
        "next_frontier": pointers.next_frontier,
    }


class ClaudeRolloverController:
    def __init__(
        self,
        *,
        process: FakeClaudeProcess,
        registry: PrivateRegistry,
        surface: ClaudeSurface,
        workspace: Path,
        source_session_id: str,
    ) -> None:
        surface.validate()
        if not _valid_uuid(source_session_id):
            raise PrototypeError("Claude source session must be a UUID")
        self.process = process
        self.registry = registry
        self.surface = surface
        self.workspace = workspace.resolve()
        if self.registry.root.resolve().is_relative_to(self.workspace):
            raise PrototypeError("registry must remain outside the workspace")
        self.source_session_id = source_session_id
        self.trigger = StatusTrigger(source_session_id, surface)
        self.active_turn = True
        self.owner_terminal = False
        self.stop_completed = False
        self.held_prompt: str | None = None

    def submit_or_hold(self, prompt: str) -> str:
        if not isinstance(prompt, str) or not prompt:
            raise PrototypeError("next prompt must be non-empty")
        if self.trigger.state == "rollover-pending":
            self.held_prompt = prompt
            return "held"
        return "source-session"

    def observe_stop(self, event: dict[str, Any]) -> bool:
        if (
            event.get("hook_event_name") != "Stop"
            or event.get("session_id") != self.source_session_id
        ):
            raise PrototypeError("Stop event is not source-session-bound")
        if event.get("interrupted") is True or event.get("api_error") is True:
            return False
        if event.get("stop_hook_active") is not False:
            raise PrototypeError("recursive Stop hook cannot establish the boundary")
        if not isinstance(event.get("last_assistant_message"), str):
            raise PrototypeError("Stop event lacks the terminal assistant message")
        self.active_turn = False
        self.stop_completed = True
        return True

    def mark_owner_terminal(self) -> None:
        self.owner_terminal = True

    def rollover(
        self,
        handoff_path: Path,
        *,
        now: int,
        target_status_line: dict[str, Any],
        ticket_list: Callable[[str], Any],
        run_status: Callable[[str], Any],
        session_id_factory: Callable[[], str],
    ) -> dict[str, Any]:
        self.surface.validate()
        if self.trigger.state != "rollover-pending":
            raise PrototypeError("rollover is not pending")
        if self.active_turn or not self.stop_completed or not self.owner_terminal:
            raise PrototypeError("safe Claude task boundary has not been reached")
        handoff = validate_handoff(
            handoff_path,
            workspace=self.workspace,
            host_adapter_id=ADAPTER_ID,
            source_session_id=self.source_session_id,
            generation=self.trigger.generation,
            now=now,
        )
        if not self.process.can_resume(self.source_session_id):
            raise PrototypeError("source Claude session is not resumable")
        entry = self.registry.create_or_read(
            handoff=handoff,
            host_adapter_id=ADAPTER_ID,
            generation=self.trigger.generation,
        )
        entry = self.registry.begin_attempt(entry)
        if entry["target_thread_id"] is None:
            target_session_id = session_id_factory()
            if (
                not _valid_uuid(target_session_id)
                or target_session_id == self.source_session_id
            ):
                self.registry.fail_attempt(entry)
                raise PrototypeError("replacement Claude session must be a fresh UUID")
            entry = self.registry.record_target(entry, target_session_id)
        else:
            target_session_id = entry["target_thread_id"]

        bootstrap = build_bootstrap(handoff)
        argv = [
            "-p",
            "--input-format",
            "stream-json",
            "--output-format",
            "stream-json",
            "--include-hook-events",
            "--include-partial-messages",
            "--forward-subagent-text",
            "--replay-user-messages",
            "--session-id",
            target_session_id,
            "--autocompact",
            str(self.surface.autocompact_tokens),
        ]
        stream_input = {
            "type": "user",
            "message": {
                "role": "user",
                "content": [{"type": "text", "text": bootstrap}],
            },
        }
        try:
            start = self.process.start_session(
                session_id=target_session_id,
                argv=argv,
                stream_input=stream_input,
            )
        except AmbiguousSessionStart:
            raise
        except Exception:
            self.registry.fail_attempt(entry)
            raise

        try:
            if start.get("session_id") != target_session_id:
                raise PrototypeError("Claude target session receipt mismatch")
            receipt = start.get("bootstrap_receipt")
            if not isinstance(receipt, str) or not receipt:
                raise PrototypeError("Claude bootstrap receipt is unavailable")
            entry = self.registry.record_bootstrap(entry, receipt)
            frontier = reconstruct_frontier(
                handoff,
                ticket_list=ticket_list,
                run_status=run_status,
            )
            target_trigger = StatusTrigger(target_session_id, self.surface)
            target_trigger.observe(target_status_line)
            if target_trigger.current_context_tokens is None or (
                target_trigger.current_context_tokens >= THRESHOLD_TOKENS
            ):
                raise PrototypeError("replacement Claude context is not below threshold")
        except Exception:
            self.registry.fail_attempt(entry)
            raise

        entry = self.registry.consume(entry, target_session_id)
        handoff.path.unlink()
        if self.held_prompt is not None:
            self.process.send_prompt(target_session_id, self.held_prompt)
        self.trigger.state = "restored"
        return {
            "source_session_id": self.source_session_id,
            "source_resumable": self.process.can_resume(self.source_session_id),
            "target_session_id": target_session_id,
            "target_mode": "fresh-uuid-session",
            "bootstrap": bootstrap,
            "bootstrap_receipt": entry["bootstrap_turn_id"],
            "frontier": frontier,
            "held_prompt_released": self.held_prompt is not None,
            "registry_state": entry["state"],
        }


def hook_only_report(hook_events: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(hook_events, dict):
        raise PrototypeError("Claude hook fixture must be a mapping")
    observed: dict[str, dict[str, Any]] = {}
    for event in hook_events.values():
        if not isinstance(event, dict):
            raise PrototypeError("Claude hook fixture event is malformed")
        name = event.get("hook_event_name")
        if not isinstance(name, str) or name in observed:
            raise PrototypeError("Claude hook fixture event identity is invalid")
        observed[name] = event
    if set(observed) != set(REQUIRED_HOOK_EVENTS):
        raise PrototypeError("Claude hook fixture lacks the required lifecycle surface")
    session_ids = {event.get("session_id") for event in observed.values()}
    if len(session_ids) != 1 or not _valid_uuid(next(iter(session_ids))):
        raise PrototypeError("Claude hook fixture is not bound to one UUID session")
    return {
        "schema": FIXTURE_SCHEMA,
        "adapter": ADAPTER_ID,
        "fixture_surface": list(REQUIRED_HOOK_EVENTS),
        "can": [
            "observe a completed Stop boundary when the host emits it",
            "preserve an already pending generation across PreCompact/PostCompact",
            "report session-bound hook lifecycle events in stream-json output",
        ],
        "cannot_claim": [
            "arming rollover from PreCompact before 150000 tokens",
            "creating a fresh UUID session without the controller",
            "submitting the bootstrap without the controller",
            "successful live rollover or interactive clear behavior",
        ],
        "controller_required": True,
    }


def load_fixture(path: Path) -> dict[str, Any]:
    import json

    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise PrototypeError(f"duplicate Claude fixture key: {key}")
            value[key] = item
        return value

    try:
        value = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=unique_object
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise PrototypeError("Claude fixture is unavailable or malformed") from error
    if value.get("schema") != FIXTURE_SCHEMA or value.get("adapter") != ADAPTER_ID:
        raise PrototypeError("unsupported Claude fixture")
    return value
