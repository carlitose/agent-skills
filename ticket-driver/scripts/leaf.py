"""Model leaf invocation and independently observed session usage."""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

from autopilot.command_capture import CaptureFailure, capture_command


def render_prompt(template: Path, *, kind: str, source_digest: str, task_text: str) -> tuple[str, str]:
    raw = template.read_bytes()
    text = raw.decode("utf-8").replace("{kind}", kind).replace("{source_digest}", source_digest)
    # Do not format arbitrary user text: braces in a ticket must remain literal.
    return text.replace("{task_text}", task_text), hashlib.sha256(raw).hexdigest()


def leaf_argv(leaf: str | None, policy: dict, session: Path, prompt: str) -> list[str]:
    if leaf:
        program = Path(leaf).resolve(strict=True)
        if program.suffix == ".py":
            return [sys.executable, "-B", str(program), "--session-dir", str(session), "--", prompt]
        return [str(program), "--session-dir", str(session), "--", prompt]
    argv = ["pi", "-p", "--provider", policy["provider"], "--model", policy["model"],
            "--thinking", policy["thinking"], "--session-dir", str(session)]
    # The benchmark's provider credential extension is operator-supplied, not stored in policy.
    extension = os.environ.get("TICKET_DRIVER_PI_EXTENSION")
    if extension:
        argv.extend(["-e", str(Path(extension).resolve(strict=True))])
    return [*argv, "--", prompt]


def usage(session: Path) -> dict:
    """Count actual assistant message usage and persisted session time; absence stays unknown."""
    totals = {"turns": 0, "tokens": 0, "cost": 0.0, "elapsed_seconds": None, "session_files": []}
    stamps = []
    for path in sorted(session.rglob("*.jsonl")):
        totals["session_files"].append(str(path.relative_to(session)))
        stamps.append(path.stat().st_mtime)
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            message = event.get("message", {})
            if not isinstance(message, dict) or not isinstance(message.get("usage"), dict):
                continue
            value = message["usage"]
            totals["turns"] += 1
            totals["tokens"] += value.get("totalTokens", 0) or 0
            totals["cost"] += (value.get("cost") or {}).get("total", 0) or 0
            stamp = event.get("timestamp")
            if isinstance(stamp, str):
                try:
                    from datetime import datetime
                    stamps.append(datetime.fromisoformat(stamp.replace("Z", "+00:00")).timestamp())
                except ValueError:
                    pass
    if len(stamps) > 1:
        totals["elapsed_seconds"] = max(stamps) - min(stamps)
    return totals


def invoke(leaf: str | None, policy: dict, session: Path, prompt: str, worktree: Path):
    session.mkdir(parents=True, exist_ok=False)
    argv = leaf_argv(leaf, policy, session, prompt)
    # capture_command owns/terminates the entire process tree on timeout or output overflow.
    started = time.monotonic()
    try:
        stdout, stderr, code = capture_command(argv, cwd=worktree,
            timeout_seconds=policy["leaf_timeout_seconds"],
            max_output_bytes=policy["max_output_bytes"])
        return argv, stdout, stderr, code, time.monotonic() - started, None
    except CaptureFailure as error:
        return argv, error.stderr[:policy["max_output_bytes"]], b"", None, time.monotonic() - started, error.reason
