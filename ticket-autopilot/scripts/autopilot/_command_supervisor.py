"""Private per-command launcher; stdout/stderr belong only to the target.

Run as a standalone isolated Python script, not as an Autopilot entry point.
The owner establishes process containment before creating the release file.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time


def main() -> None:
    control = Path(sys.argv[1])
    request = json.loads((control / "request.json").read_text(encoding="utf-8"))
    if os.name == "posix":
        # Never signal an inherited caller group, even if invoked incorrectly.
        if os.getpgrp() != os.getpid():
            raise RuntimeError("command supervisor must own its process group")
        # Also bound this owned group if the caller dies without running cleanup.
        watchdog = threading.Timer(
            request["timeout_seconds"] + 5,
            lambda: os.killpg(os.getpid(), signal.SIGKILL),
        )
        watchdog.daemon = True
        watchdog.start()
    release_deadline = time.monotonic() + min(request["timeout_seconds"], 5)
    while not (control / "release").exists():
        if time.monotonic() >= release_deadline:
            return  # Caller died or could not establish containment; no target ran.
        time.sleep(0.01)
    try:
        child = subprocess.Popen(request["command"], cwd=request["cwd"])
        result = {"returncode": child.wait()}
    except Exception as error:
        diagnostic = f"{type(error).__name__}: {error}"
        # Even worst-case JSON escaping stays below the 8192-byte status bound.
        # This truncates diagnostics only, never command stdout or argument data.
        result = {"error": diagnostic[:512] + (" [truncated]" if len(diagnostic) > 512 else "")}
    pending = control / "result.pending"
    pending.write_text(json.dumps(result, ensure_ascii=True), encoding="utf-8")
    pending.replace(control / "result.json")
    # Publish status before EOF: readers must not race an in-progress rename.
    # The target inherited the original stdin and exact native output pipes.
    # Close descriptors explicitly; Python's standard wrappers may use closefd=False.
    # Keep the group leader alive until owner cleanup.
    sys.stdout.flush()
    sys.stderr.flush()
    os.close(1)
    os.close(2)
    while True:
        time.sleep(60)


if __name__ == "__main__":
    main()
