"""Host-side Harbor agent boundary for Pi; task commands only use BaseEnvironment.exec.

This is an offline bridge for the two direct Pi arms. Ticket-driver arms fail closed
until the driver's Git/leaf boundary can be faithfully mapped onto a Harbor task.
No live evaluation may start through this module until budget and credential gates
are proved independently.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
from pathlib import Path
from typing import Literal

from harbor.agents.base import BaseAgent
from harbor.agents.options import AgentOptions
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext, ModelUsage

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

    async def _run_bridge(
        self, instruction: str, environment: BaseEnvironment, context: AgentContext
    ) -> None:
        arm = self.options.arm
        if arm.startswith("ticket-driver-"):
            raise RuntimeError("faithful ticket-driver Git/leaf sandbox bridge is unproved")
        if self.bridge_command == ("node", str(Path(__file__).with_name("pi_bridge.mjs"))):
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
            await self._send(proc, {"type": "start", "instruction": instruction,
                                    "arm": arm, "model": MODEL, "thinking": "high"})
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
                    usage = message.get("usage")
                    if (not isinstance(usage, dict) or
                        any(type(usage.get(key)) is not int or usage[key] < 0
                            for key in ("input_tokens", "output_tokens")) or
                        type(usage.get("cost_usd")) not in (int, float) or
                        not 0 <= usage["cost_usd"] < float("inf")):
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
