"""Codex App Server tracer bullet for the frozen context-rollover policy."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Callable

from rollover_common import (
    PrivateRegistry,
    PrototypeError,
    THRESHOLD_TOKENS,
    ValidatedHandoff,
    validate_handoff,
)


FIXTURE_SCHEMA = 1
ADAPTER_ID = "codex-app-server-v2"


def project_messages(thread_read_response: dict[str, Any]) -> dict[str, Any]:
    """Project only CR-01 logical messages from thread/read(includeTurns=true)."""
    if (
        thread_read_response.get("method") != "thread/read"
        or not isinstance(thread_read_response.get("params"), dict)
        or thread_read_response["params"].get("includeTurns") is not True
    ):
        raise PrototypeError("message projection requires thread/read(includeTurns=true)")
    try:
        turns = thread_read_response["result"]["thread"]["turns"]
    except (KeyError, TypeError) as error:
        raise PrototypeError("invalid thread/read response") from error
    if not isinstance(turns, list):
        raise PrototypeError("thread/read turns must be a list")

    user_messages = 0
    assistant_messages = 0
    assistant_available = True
    seen_items: set[str] = set()
    for turn in turns:
        if not isinstance(turn, dict) or not isinstance(turn.get("items"), list):
            raise PrototypeError("invalid turn projection")
        final_items = []
        phase_unknown = []
        for item in turn["items"]:
            if not isinstance(item, dict):
                raise PrototypeError("invalid ThreadItem")
            item_id = item.get("id")
            item_type = item.get("type")
            if not isinstance(item_id, str) or not item_id or not isinstance(item_type, str):
                raise PrototypeError("ThreadItem identity is required")
            if item_id in seen_items:
                continue
            seen_items.add(item_id)
            if item_type == "userMessage":
                user_messages += 1
            elif item_type == "agentMessage":
                phase = item.get("phase")
                if phase == "final_answer":
                    final_items.append(item_id)
                elif phase is None:
                    phase_unknown.append(item_id)
                elif phase != "commentary":
                    raise PrototypeError("unknown agentMessage phase")

        assistant_messages += len(final_items)
        if (
            not final_items
            and phase_unknown
            and turn.get("status") == "completed"
        ):
            if len(phase_unknown) == 1:
                assistant_messages += 1
            else:
                assistant_available = False

    assistant_value = assistant_messages if assistant_available else None
    return {
        "schema": FIXTURE_SCHEMA,
        "adapter": ADAPTER_ID,
        "source": "thread/read(includeTurns=true)",
        "user_messages": user_messages,
        "assistant_messages": assistant_value,
        "total_messages": (
            user_messages + assistant_messages if assistant_available else None
        ),
        "assistant_count_available": assistant_available,
    }


@dataclass
class TriggerState:
    source_thread_id: str
    state: str = "monitoring"
    generation: int = 0
    current_context_tokens: int | None = None

    def observe(self, notification: dict[str, Any]) -> None:
        if notification.get("method") != "thread/tokenUsage/updated":
            raise PrototypeError("unexpected token notification method")
        try:
            params = notification["params"]
            if params["threadId"] != self.source_thread_id:
                raise PrototypeError("token notification thread mismatch")
            usage = params["tokenUsage"]
            current = usage["last"]["totalTokens"]
            window = usage["modelContextWindow"]
        except (KeyError, TypeError) as error:
            raise PrototypeError("invalid token usage notification") from error
        if type(current) is not int or current < 0:
            raise PrototypeError("current context must be a non-negative integer")
        if type(window) is not int or window <= THRESHOLD_TOKENS:
            raise PrototypeError("modelContextWindow cannot reach the rollover threshold")
        self.current_context_tokens = current
        if current >= THRESHOLD_TOKENS and self.state == "monitoring":
            self.state = "rollover-pending"
            self.generation += 1


class FakeAppServer:
    """Local causal boundary that records exact App Server v2 method calls."""

    def __init__(self, source_thread: dict[str, Any]) -> None:
        self.threads = {source_thread["id"]: source_thread}
        self.calls: list[dict[str, Any]] = []
        self._next_thread = 1
        self._next_turn = 1
        self._turns_by_client_id: dict[tuple[str, str], dict[str, Any]] = {}

    def request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        self.calls.append({"method": method, "params": params})
        if method == "thread/read":
            thread = self.threads.get(params.get("threadId"))
            if thread is None or params.get("includeTurns") is not True:
                raise PrototypeError("thread/read requires a known thread and includeTurns")
            return {"thread": thread}
        if method == "thread/start":
            thread_id = f"target-thread-{self._next_thread}"
            self._next_thread += 1
            thread = {
                "id": thread_id,
                "cwd": params.get("cwd"),
                "status": {"type": "idle"},
                "turns": [],
            }
            self.threads[thread_id] = thread
            return {"thread": thread}
        if method == "turn/start":
            thread = self.threads.get(params.get("threadId"))
            if thread is None or not isinstance(params.get("input"), list):
                raise PrototypeError("turn/start requires a known thread and input")
            client_id = params.get("clientUserMessageId")
            if client_id is not None:
                key = (thread["id"], client_id)
                if key in self._turns_by_client_id:
                    return {"turn": self._turns_by_client_id[key]}
            turn = {
                "id": f"target-turn-{self._next_turn}",
                "status": "completed",
                "items": [
                    {
                        "id": f"target-input-{self._next_turn}",
                        "type": "userMessage",
                        "content": params["input"],
                    }
                ],
            }
            self._next_turn += 1
            thread["turns"].append(turn)
            if client_id is not None:
                self._turns_by_client_id[(thread["id"], client_id)] = turn
            return {"turn": turn}
        raise PrototypeError(f"unsupported fake App Server method: {method}")


def build_bootstrap(handoff: ValidatedHandoff) -> str:
    return "\n".join(
        (
            f"Restore only from validated handoff: {handoff.path}",
            "Read the Wayfinder path recorded in that handoff.",
            "Run ticket-autopilot ticket-list on its ticket folder.",
            "If a run ID is present, run ticket-autopilot status for that exact run.",
            "Report the reconstructed map, inventory, run status, and next frontier.",
            "Do not copy or infer transcript content.",
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


class CodexRolloverController:
    def __init__(
        self,
        *,
        app_server: FakeAppServer,
        registry: PrivateRegistry,
        workspace: Path,
        source_thread_id: str,
        source_session_id: str,
    ) -> None:
        self.app_server = app_server
        self.registry = registry
        self.workspace = workspace.resolve()
        if self.registry.root.resolve().is_relative_to(self.workspace):
            raise PrototypeError("registry must remain outside the workspace")
        self.source_thread_id = source_thread_id
        self.source_session_id = source_session_id
        self.trigger = TriggerState(source_thread_id)
        self.active_turn = True
        self.owner_terminal = False
        self.held_prompt: str | None = None

    def submit_or_hold(self, prompt: str) -> str:
        if not prompt:
            raise PrototypeError("next prompt must be non-empty")
        if self.trigger.state == "rollover-pending":
            self.held_prompt = prompt
            return "held"
        return "source-thread"

    def mark_turn_completed(self) -> None:
        self.active_turn = False

    def mark_owner_terminal(self) -> None:
        self.owner_terminal = True

    def rollover(
        self,
        handoff_path: Path,
        *,
        now: int,
        target_token_notification: dict[str, Any],
        ticket_list: Callable[[str], Any],
        run_status: Callable[[str], Any],
    ) -> dict[str, Any]:
        if self.trigger.state != "rollover-pending":
            raise PrototypeError("rollover is not pending")
        if self.active_turn or not self.owner_terminal:
            raise PrototypeError("safe task boundary has not been reached")
        handoff = validate_handoff(
            handoff_path,
            workspace=self.workspace,
            host_adapter_id=ADAPTER_ID,
            source_session_id=self.source_session_id,
            generation=self.trigger.generation,
            now=now,
        )
        entry = self.registry.create_or_read(
            handoff=handoff,
            host_adapter_id=ADAPTER_ID,
            generation=self.trigger.generation,
        )

        source_readback = self.app_server.request(
            "thread/read",
            {"threadId": self.source_thread_id, "includeTurns": True},
        )
        entry = self.registry.begin_attempt(entry)
        bootstrap = build_bootstrap(handoff)
        try:
            if entry["target_thread_id"] is None:
                target = self.app_server.request(
                    "thread/start",
                    {
                        "cwd": str(self.workspace),
                        "runtimeWorkspaceRoots": [str(self.workspace)],
                    },
                )["thread"]
                entry = self.registry.record_target(entry, target["id"])
            else:
                target = self.app_server.request(
                    "thread/read",
                    {"threadId": entry["target_thread_id"], "includeTurns": True},
                )["thread"]
            if entry["bootstrap_turn_id"] is None:
                bootstrap_result = self.app_server.request(
                    "turn/start",
                    {
                        "threadId": target["id"],
                        "clientUserMessageId": (
                            f"rollover:{entry['rollover_id']}:{entry['attempt_count']}:bootstrap"
                        ),
                        "input": [{"type": "text", "text": bootstrap}],
                    },
                )
                entry = self.registry.record_bootstrap(
                    entry, bootstrap_result["turn"]["id"]
                )
            frontier = reconstruct_frontier(
                handoff,
                ticket_list=ticket_list,
                run_status=run_status,
            )
            if (
                not isinstance(target_token_notification.get("params"), dict)
                or target_token_notification["params"].get("turnId")
                != entry["bootstrap_turn_id"]
            ):
                raise PrototypeError("target token notification turn mismatch")
            target_usage = TriggerState(target["id"])
            target_usage.observe(target_token_notification)
            if target_usage.current_context_tokens is None or (
                target_usage.current_context_tokens >= THRESHOLD_TOKENS
            ):
                raise PrototypeError("replacement context is not below threshold")
        except Exception:
            self.registry.fail_attempt(entry)
            raise

        entry = self.registry.consume(entry, target["id"])
        handoff.path.unlink()
        if self.held_prompt is not None:
            self.app_server.request(
                "turn/start",
                {
                    "threadId": target["id"],
                    "clientUserMessageId": f"rollover:{entry['rollover_id']}:held-prompt",
                    "input": [{"type": "text", "text": self.held_prompt}],
                },
            )
        self.trigger.state = "restored"
        return {
            "source_thread_id": source_readback["thread"]["id"],
            "target_thread_id": target["id"],
            "target_mode": "fresh-thread",
            "bootstrap": bootstrap,
            "frontier": frontier,
            "held_prompt_released": self.held_prompt is not None,
            "registry_state": entry["state"],
        }


def hook_only_report() -> dict[str, Any]:
    return {
        "schema": FIXTURE_SCHEMA,
        "adapter": ADAPTER_ID,
        "observed_surface": ["PreCompact", "PostCompact", "SessionStart"],
        "can": [
            "preserve an already pending rollover generation across compaction",
            "observe SessionStart source values supplied by the host",
            "run controller-owned commands when the host invokes the hook",
        ],
        "cannot_claim": [
            "arming below 150000 tokens",
            "issuing /clear or creating a fresh thread",
            "submitting a bootstrap without controller authority",
            "successful live rollover",
        ],
        "controller_required": True,
    }


def load_fixture(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schema") != FIXTURE_SCHEMA:
        raise PrototypeError("unsupported Codex fixture schema")
    return value
