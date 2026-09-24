"""Host-side Harbor agent boundary for Pi; task commands only use BaseEnvironment.exec.

The original-image Pi-bare pilot requires a task-bound external ledger and a
per-request model budget. Modified four-arm comparisons remain gated until their
Git/leaf and costing boundaries are proved independently.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Literal

from harbor.agents.base import BaseAgent
from harbor.agents.options import AgentOptions
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext, ModelUsage
from pilot_ledger import GateError, PilotLedger, frozen_bytes

MODEL = "openai-codex/gpt-6-sol"
MAX_LINE = 65536
MAX_CALLS = 1000
MAX_STREAM_BYTES = 4096  # Two JSON-escaped streams still fit one bounded protocol line.
GIT_SETUP = (
    "set -eu; test -d /app && test ! -e /app/.git && command -v git >/dev/null || exit 1; "
    "git init -q -b tbf-base /app; : > /app/.git/tbf-owned; git -C /app add -A; "
    "GIT_AUTHOR_DATE=2000-01-01T00:00:00+0000 "
    "GIT_COMMITTER_DATE=2000-01-01T00:00:00+0000 "
    "git -C /app -c user.name=tbf -c user.email=tbf@local.invalid "
    "-c commit.gpgsign=false commit --allow-empty -qm 'tbf baseline'; "
    "test -z \"$(git -C /app status --porcelain)\"; "
    "git -C /app rev-parse HEAD"
)
GIT_CLEANUP = "test -f /app/.git/tbf-owned && rm -rf -- /app/.git && test ! -e /app/.git"
GIT_CLEANUP_AFTER_FAILURE = f"if test -e /app/.git; then {GIT_CLEANUP}; fi"


def bounded_output(value: str | None) -> str | None:
    if value is None:
        return None
    raw = value.encode("utf-8")
    if len(raw) <= MAX_STREAM_BYTES:
        return value
    return raw[:MAX_STREAM_BYTES].decode("utf-8", errors="ignore") + "\n[truncated]"


class PiOptions(AgentOptions):
    arm: Literal["pi-bare", "skills-only", "ticket-driver-c1a", "ticket-driver-c3a"] = "pi-bare"


class PiHarborAgent(BaseAgent):
    """An external agent: the child has no native host file or shell tools."""

    options_model = PiOptions

    def __init__(self, logs_dir: Path, model_name: str | None = None, **kwargs):
        super().__init__(logs_dir, model_name=model_name, **kwargs)
        if self.model_name != MODEL:
            raise ValueError(f"pilot requires frozen model {MODEL}")
        self.bridge_command = ("node", str(Path(__file__).with_name("pi_bridge.mjs")))
        self._git_initialized = False

    @staticmethod
    def name() -> str:
        return "pi-harbor"

    def version(self) -> str:
        return "0.1.0-offline"

    async def setup(self, environment: BaseEnvironment) -> None:
        """Bootstrap the same task-local Git baseline for every arm; Pi remains host-side."""
        try:
            result = await environment.exec(GIT_SETUP, timeout_sec=60)
        except BaseException:
            await self._cleanup_failed_setup(environment)
            raise
        if result.return_code != 0 or not re.fullmatch(r"[a-f0-9]{40}\n?", result.stdout or ""):
            await self._cleanup_failed_setup(environment)
            raise RuntimeError("Git bootstrap failed in task sandbox")
        self._git_initialized = True

    @staticmethod
    async def _cleanup_failed_setup(environment: BaseEnvironment) -> None:
        result = await environment.exec(GIT_CLEANUP_AFTER_FAILURE, timeout_sec=30)
        if result.return_code != 0:
            raise RuntimeError("Git bootstrap failed; cleanup unconfirmed")

    @staticmethod
    def _child_env() -> dict[str, str]:
        # No judge key, unrelated model credentials or inherited task secrets in Pi.
        needed = ("PATH", "SYSTEMROOT", "COMSPEC", "TEMP", "TMP", "USERPROFILE",
                  "HOME", "APPDATA", "LOCALAPPDATA")
        return {key: os.environ[key] for key in needed if key in os.environ}

    async def run(
        self, instruction: str, environment: BaseEnvironment, context: AgentContext
    ) -> None:
        try:
            await self._run_bridge(instruction, environment, context)
        finally:
            if self._git_initialized:
                result = await environment.exec(GIT_CLEANUP, timeout_sec=30)
                if result.return_code != 0:
                    raise RuntimeError("Git cleanup failed before separate verifier")
                self._git_initialized = False

    def _start_payload(self, instruction: str, arm: str) -> dict:
        return {"type": "start", "instruction": instruction, "arm": arm,
                "model": MODEL, "thinking": "high"}

    def _validate_final(self, message: dict) -> None:
        """Arm-specific final receipts are checked before attributing usage."""

    async def _run_bridge(
        self, instruction: str, environment: BaseEnvironment, context: AgentContext
    ) -> None:
        arm = self.options.arm
        if arm.startswith("ticket-driver-"):
            raise RuntimeError("faithful ticket-driver Git/leaf sandbox bridge is unproved")
        if (self.bridge_command == ("node", str(Path(__file__).with_name("pi_bridge.mjs")))
                and not getattr(self, "_live_enabled", False)):
            raise RuntimeError("live pilot gate: budget, credentials and skill binding are unproved")
        if not isinstance(instruction, str) or not instruction:
            raise ValueError("missing task instruction")
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        proc = await asyncio.create_subprocess_exec(
            *self.bridge_command,
            cwd=str(self.logs_dir),
            env=self._child_env(),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
            limit=MAX_LINE,
        )
        try:
            await self._send(proc, self._start_payload(instruction, arm))
            for _ in range(MAX_CALLS):
                try:
                    line = await asyncio.wait_for(proc.stdout.readline(), timeout=900)
                except ValueError as exc:
                    raise RuntimeError("bridge message exceeded message bound") from exc
                if not line or len(line) > MAX_LINE:
                    raise RuntimeError("bridge stopped or exceeded message bound")
                try:
                    message = json.loads(line)
                except (ValueError, UnicodeDecodeError) as exc:
                    raise RuntimeError("invalid bridge message") from exc
                if not isinstance(message, dict):
                    raise RuntimeError("invalid bridge message")
                if message.get("type") == "exec":
                    if (set(message) != {"type", "id", "command", "cwd", "timeout_sec"}
                        or not isinstance(message["id"], str)
                        or not isinstance(message["command"], str)
                        or not message["command"]
                        or len(message["command"]) > 16384
                        or (message["cwd"] is not None and not isinstance(message["cwd"], str))
                        or type(message["timeout_sec"]) is not int
                        or not 1 <= message["timeout_sec"] <= 120):
                        raise RuntimeError("invalid sandbox command")
                    result = await environment.exec(
                        message["command"], cwd=message["cwd"],
                        timeout_sec=message["timeout_sec"]
                    )
                    await self._send(proc, {"type": "result", "id": message["id"],
                                            "stdout": bounded_output(result.stdout),
                                            "stderr": bounded_output(result.stderr),
                                            "return_code": result.return_code})
                    continue
                if message.get("type") == "final":
                    await asyncio.wait_for(proc.wait(), timeout=10)
                    if proc.returncode != 0:
                        raise RuntimeError("Pi bridge failed")
                    if message.get("instruction") != instruction or message.get("arm") != arm:
                        raise RuntimeError("final task or arm mismatch")
                    self._validate_final(message)
                    usage = message.get("usage")
                    if (not isinstance(usage, dict) or
                        any(type(usage.get(key)) is not int or usage[key] < 0
                            for key in ("input_tokens", "output_tokens")) or
                        type(usage.get("cost_usd")) not in (int, float) or
                        not 0 <= usage["cost_usd"] < float("inf") or
                        (usage["output_tokens"] > 0 and usage["cost_usd"] == 0)):
                        raise RuntimeError("missing or invalid attributable model usage")
                    context.n_input_tokens = usage["input_tokens"]
                    context.n_output_tokens = usage["output_tokens"]
                    context.cost_usd = usage["cost_usd"]
                    context.model_usage = {MODEL: ModelUsage(
                        n_input_tokens=usage["input_tokens"],
                        n_output_tokens=usage["output_tokens"],
                        cost_usd=usage["cost_usd"],
                    )}
                    context.metadata = {"arm": arm, "bridge": "external-pi-sandbox-exec",
                                        "offline_probe": message.get("offline_probe") is True}
                    (self.logs_dir / "pi-harbor-trajectory.json").write_text(
                        json.dumps(message, ensure_ascii=False, sort_keys=True) + "\n",
                        encoding="utf-8",
                    )
                    return
                raise RuntimeError("unexpected bridge message")
            raise RuntimeError("too many sandbox commands")
        finally:
            if proc.returncode is None:
                proc.kill()
                await proc.wait()

    @staticmethod
    async def _send(proc: asyncio.subprocess.Process, message: dict) -> None:
        payload = (json.dumps(message, ensure_ascii=False) + "\n").encode("utf-8")
        if len(payload) > MAX_LINE:
            raise RuntimeError("bridge reply exceeds message bound")
        proc.stdin.write(payload)
        await proc.stdin.drain()


class StandardPiHarborAgent(PiHarborAgent):
    """Pi bare on the original Harbor image: never install or initialize Git."""

    def __init__(self, logs_dir: Path, model_name: str | None = None,
                 *, ledger_path: Path | None = None, task_name: str | None = None, **kwargs):
        super().__init__(logs_dir, model_name=model_name, **kwargs)
        if self.options.arm != "pi-bare":
            raise ValueError("standard Harbor pilot permits only pi-bare")
        self.ledger_path = Path(ledger_path) if ledger_path is not None else None
        self.task_name = task_name
        if self.ledger_path is not None:
            repo_root = Path(__file__).resolve().parents[2]
            if (self.ledger_path.resolve().is_relative_to(repo_root)
                    or self.logs_dir.resolve().is_relative_to(repo_root)):
                raise ValueError("live ledger and trajectory must remain outside the repository")
        self._live_enabled = False

    @staticmethod
    def name() -> str:
        return "pi-harbor-standard"

    def version(self) -> str:
        return "0.2.0-standard"

    async def setup(self, environment: BaseEnvironment) -> None:
        if self.ledger_path is not None or self.task_name is not None:
            binding = json.loads(Path(__file__).with_name("standard-pilot.json").read_text(encoding="utf-8"))
            rows = [row for row in binding["tasks"] if row["name"] == self.task_name]
            image = getattr(getattr(environment, "task_env_config", None), "docker_image", None)
            if self.ledger_path is None or len(rows) != 1 or image != rows[0]["original_agent_image_ref"]:
                raise RuntimeError("standard pilot requires the bound original image")
        result = await environment.exec("test -d /app && test ! -e /app/.git", timeout_sec=30)
        if result.return_code != 0:
            raise RuntimeError("original task sandbox is unavailable or modified")

    def _start_payload(self, instruction: str, arm: str) -> dict:
        return {**super()._start_payload(instruction, arm), "method": "standard",
                "task_name": self.task_name,
                "budget": {"limit_usd": "60", "max_requests": 16}}

    async def run(self, instruction: str, environment: BaseEnvironment,
                  context: AgentContext) -> None:
        if self.bridge_command == ("node", str(Path(__file__).with_name("pi_bridge.mjs"))):
            if self.ledger_path is None or self.task_name is None:
                raise RuntimeError("standard pilot needs a task-bound reserved ledger")
            root = Path(__file__).parent
            manifest = frozen_bytes(root / "manifest.json")
            binding = json.loads((root / "standard-pilot.json").read_text(encoding="utf-8"))
            entries = [row for row in binding["tasks"] if row["name"] == self.task_name]
            if (binding.get("method") != "original-harbor-pi-bare"
                or binding.get("model") != MODEL or binding.get("arm") != "pi-bare"
                or binding.get("source_manifest_sha256") != hashlib.sha256(manifest).hexdigest()
                or binding.get("agent_import") != "harbor_pi_agent:StandardPiHarborAgent"
                or binding.get("max_starts") != 3 or binding.get("cap_usd") != "250"
                or binding.get("per_start_reservation_usd") != "60"
                or binding.get("max_model_requests") != 16
                or len(entries) != 1
                or entries[0]["harbor_instruction_sha256"] != hashlib.sha256(instruction.encode("utf-8")).hexdigest()
                or getattr(getattr(environment, "task_env_config", None), "docker_image", None)
                    != entries[0]["original_agent_image_ref"]):
                raise RuntimeError("standard task binding differs from Harbor instruction")
            try:
                PilotLedger(self.ledger_path, root / "manifest.json", standard=True).start(
                    self.task_name, "pi-bare")
            except GateError as exc:
                raise RuntimeError("standard pilot ledger is not reserved") from exc
            self._live_enabled = True
        try:
            await super().run(instruction, environment, context)
            context.metadata = {**(context.metadata or {}), "method": "original-harbor-pi-bare",
                                "task_name": self.task_name}
        finally:
            self._live_enabled = False

    def _validate_final(self, message: dict) -> None:
        if not message.get("offline_probe") and (
                not self.task_name or message.get("task_name") != self.task_name):
            raise RuntimeError("standard budget task identity mismatch")
        receipt = message.get("budget")
        if (message.get("method") != "standard" or not isinstance(receipt, dict)
            or receipt.get("limitUsd") != "60" or receipt.get("maxRequests") != 16
            or type(receipt.get("requests")) is not int or not 0 <= receipt["requests"] <= 16
            or type(receipt.get("pendingRequests")) is not int or receipt["pendingRequests"] != 0
            or type(receipt.get("maxPerRequestUsd")) not in (int, float)
            or not 0 < receipt["maxPerRequestUsd"] < float("inf")
            or abs(receipt["maxPerRequestUsd"] - 8.2) > 0.000001
            or type(receipt.get("ambiguous")) is not bool or receipt["ambiguous"]
            or any(type(receipt.get(key)) not in (int, float) or
                   not 0 <= receipt[key] < float("inf")
                   for key in ("reservedUsd", "observedUsd"))
            or receipt["reservedUsd"] > 60
            or abs(receipt["reservedUsd"] - receipt["observedUsd"]) > 0.000001
            or (not message.get("offline_probe") and
                (receipt["requests"] == 0 or receipt["observedUsd"] == 0))):
            raise RuntimeError("standard budget receipt is missing or invalid")
        usage = message.get("usage")
        if (not isinstance(usage, dict) or type(usage.get("cost_usd")) not in (int, float)
                or abs(usage["cost_usd"] - receipt["observedUsd"]) > 0.000001):
            raise RuntimeError("standard budget usage differs from Pi session")
