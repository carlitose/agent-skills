"""Model leaf invocation and independently observed session usage."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import time
from pathlib import Path

from autopilot.command_capture import CaptureFailure, capture_command


def render_prompt(template: Path, *, kind: str, source_digest: str, task_text: str) -> tuple[str, str]:
    raw = template.read_bytes()
    text = raw.decode("utf-8").replace("{kind}", kind).replace("{source_digest}", source_digest)
    # Do not format arbitrary user text: braces in a ticket must remain literal.
    return text.replace("{task_text}", task_text), hashlib.sha256(raw).hexdigest()


def pi_command(*, platform: str | None = None) -> list[str]:
    """Resolve a native launch target; the process-tree owner cannot start npm CMD shims."""
    found = shutil.which("pi")
    if not found:
        raise ValueError("Pi is unavailable on PATH")
    shim = Path(found)
    if (platform or os.name) != "nt":
        return [str(shim.resolve(strict=True))]
    if shim.suffix.lower() == ".exe":
        return [str(shim.resolve(strict=True))]
    if shim.suffix.lower() not in (".cmd", ".bat"):
        raise ValueError("Pi on Windows must be a native .exe or an npm .CMD/.BAT shim")

    package = shim.parent / "node_modules" / "@earendil-works" / "pi-coding-agent"
    try:
        metadata = json.loads((package / "package.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError("Pi npm package is missing beside its shim or has invalid metadata") from error
    if not isinstance(metadata, dict) or metadata.get("name") != "@earendil-works/pi-coding-agent":
        raise ValueError("Pi npm package identity does not match its shim")
    bins = metadata.get("bin")
    relative = bins.get("pi") if isinstance(bins, dict) else None
    if not isinstance(relative, str) or not relative:
        raise ValueError("Pi package has no bin.pi entry")
    entry_path = Path(relative)
    if entry_path.is_absolute() or ".." in entry_path.parts or entry_path.suffix.lower() not in (".js", ".mjs"):
        raise ValueError("Pi bin path is outside the package or is not JavaScript")
    try:
        package_root = package.resolve(strict=True)
        entry = (package_root / entry_path).resolve(strict=True)
    except OSError as error:
        raise ValueError("Pi bin entry is missing from the npm package") from error
    if not entry.is_relative_to(package_root) or not entry.is_file():
        raise ValueError("Pi bin path resolves outside the package")
    node = shutil.which("node")
    if not node or Path(node).suffix.lower() != ".exe":
        raise ValueError("Native Node.exe is unavailable on PATH for the Pi npm shim")
    return [str(Path(node).resolve(strict=True)), str(entry)]


def leaf_argv(leaf: str | None, policy: dict, session: Path, prompt: str) -> list[str]:
    if leaf:
        program = Path(leaf).resolve(strict=True)
        if program.suffix == ".py":
            return [sys.executable, "-B", str(program), "--session-dir", str(session), "--", prompt]
        return [str(program), "--session-dir", str(session), "--", prompt]
    argv = [*pi_command(), "-p", "--provider", policy["provider"], "--model", policy["model"],
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
