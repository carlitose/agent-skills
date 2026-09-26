"""One bounded task's SDK connection; never schedules or selects another trial."""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
from pathlib import Path

from comparison_exec import sandbox_exec
from harbor_pi_agent import PiHarborAgent, bounded_output

FRAME_BYTES = 262144


def model_identity(init: dict) -> dict:
    identity = {"method": init["method"], "task": init["task_name"], "arm": init["arm"],
                "trial": init["trial_id"], "model": init["model"], "thinking": init["thinking"],
                "instruction_sha256": hashlib.sha256(init["instruction"].encode("utf8")).hexdigest()}
    if "skills_sha256" in init:  # original-method skilled arms (skills-only, c1a, c3a)
        identity["skills_sha256"] = init["skills_sha256"]
    return identity


class ComparisonProcess:
    def __init__(self, directory: Path, environment, init: dict, *, command=None):
        self.directory = directory
        self.environment = environment
        self.init = init
        self.command = command or ("node", str(Path(__file__).with_name("comparison_bridge.mjs")))
        self.proc = None
        self.finished = False
        self.status = "failed"
        self.calls = 0
        self.phases = set()
        self.identity = model_identity(init)

    async def __aenter__(self):
        self.directory.mkdir(parents=True, exist_ok=True)
        try:
            self.proc = await asyncio.create_subprocess_exec(
                *self.command, cwd=str(self.directory), env=PiHarborAgent._child_env(),
                stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL, limit=FRAME_BYTES)
            await self._send(self.init)
            ready = await self._read()
            if ready.get("type") != "ready" or ready.get("identity") != self.identity:
                raise RuntimeError("comparison endpoint identity mismatch")
            return self
        except BaseException:
            await self.__aexit__(None, None, None)
            raise

    async def __aexit__(self, *_):
        try:
            # On transport failure do not close stdin and let the model continue
            # from a synthetic tool error. Stop the endpoint before reading its journal.
            if self.proc is not None and self.proc.returncode is None:
                if not self.finished:
                    self.proc.kill()
                await asyncio.wait_for(self.proc.wait(), timeout=10)
        finally:
            stopped = self.proc is None or self.proc.returncode is not None
            if not stopped:
                self.status = "failed"
            with (self.directory / "host-status.json").open("x", encoding="utf8") as file:
                json.dump({"status": self.status, "process_stopped": stopped,
                           "trial_id": self.init.get("trial_id"), "commands": self.calls,
                           "phases": sorted(self.phases)}, file, sort_keys=True)
                file.write("\n")
                file.flush()
                os.fsync(file.fileno())

    async def _send(self, value):
        line = (json.dumps(value, ensure_ascii=False) + "\n").encode("utf8")
        if len(line) > FRAME_BYTES:
            raise RuntimeError("comparison frame exceeded bound")
        self.proc.stdin.write(line)
        await self.proc.stdin.drain()

    async def _read(self):
        line = await asyncio.wait_for(self.proc.stdout.readline(), timeout=900)
        if not line or len(line) > FRAME_BYTES:
            raise RuntimeError("comparison endpoint stopped or exceeded frame bound")
        message = json.loads(line)
        if not isinstance(message, dict):
            raise RuntimeError("invalid comparison frame")
        return message

    async def phase(self, name, prompt, system_prompt, *, tools="sandbox"):
        if (self.finished or name in self.phases or len(self.phases) >= 8 or
                not re.fullmatch(r"[a-z][a-z0-9-]{0,63}", name) or tools not in ("sandbox", "none")):
            raise RuntimeError("invalid comparison phase")
        self.phases.add(name)
        await self._send({"type": "phase", "name": name, "prompt": prompt,
                          "system_prompt": system_prompt, "tools": tools})
        while True:
            message = await self._read()
            if message.get("type") == "phase-result" and message.get("phase") == name:
                if message.get("status") not in ("completed", "failed"):
                    raise RuntimeError("invalid phase status")
                return message
            if message.get("type") != "exec":
                raise RuntimeError("unexpected comparison message")
            if tools != "sandbox":
                raise RuntimeError("read-only phase requested a shell")
            self.calls += 1
            if (self.calls > 1000 or set(message) != {"type", "id", "command", "cwd", "timeout_sec"}
                    or message["id"] != str(self.calls)
                    or (message["cwd"] is not None and not isinstance(message["cwd"], str))):
                raise RuntimeError("invalid sandbox request")
            result = await sandbox_exec(self.environment, message["command"],
                                        cwd=message["cwd"], timeout_sec=message["timeout_sec"])
            await self._send({"type": "result", "id": message["id"],
                              "stdout": bounded_output(result.stdout), "stderr": bounded_output(result.stderr),
                              "return_code": result.return_code})

    async def finish(self, status):
        if self.finished or status not in ("completed", "failed"):
            raise RuntimeError("invalid terminal status")
        await self._send({"type": "finish", "status": status})
        final = await self._read()
        if (final.get("type") != "final" or final.get("status") not in ("completed", "failed")
                or final.get("identity") != self.identity):
            raise RuntimeError("missing or mismatched comparison terminal receipt")
        await asyncio.wait_for(self.proc.wait(), timeout=10)
        if self.proc.returncode != 0:
            raise RuntimeError("comparison endpoint failed")
        self.finished = True
        self.status = final["status"]
        return final
