"""Record every child process a runner spawns, in the runner and in its CLI subprocesses.

Placed first on `PYTHONPATH`, Python imports this before user code in *every* interpreter of
the tree, so a case that shells out to `ticket-autopilot.py` is measured as thoroughly as one
that calls the kernel in process. Patching `subprocess.Popen` rather than
`autopilot.git_ops._run_captured` keeps the probe below the code under study: it needs no
import hook, it cannot miss a call site, and it stays correct if capture changes.

One JSONL file per PID under `AUTOPILOT_CMD_LOG_DIR` avoids interleaved appends from the
parallel reader threads and from concurrent processes.
"""

from __future__ import annotations

import builtins
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

_DIRECTORY = os.environ.get("AUTOPILOT_CMD_LOG_DIR")

if _DIRECTORY:
    _SINK = Path(_DIRECTORY) / f"{os.getpid()}.jsonl"
    _SINK.parent.mkdir(parents=True, exist_ok=True)
    _HEX = re.compile(r"\b[0-9a-f]{7,40}\b")
    _WINDOWS_PATH = re.compile(r"[A-Za-z]:[\\/][^\s\"']*")
    _POSIX_PATH = re.compile(r"/(?:tmp|home|Users|var)/[^\s\"']*")

    def _normalize(token: str) -> str:
        token = _HEX.sub("<oid>", token)
        token = _WINDOWS_PATH.sub("<path>", token)
        return _POSIX_PATH.sub("<path>", token)

    _state = {"frame": None, "instance": 0}

    def _operation() -> tuple[str, str, int]:
        """Operation, call site, and which *invocation* of that operation this call belongs to.

        The outermost autopilot frame names the operation, but one process runs many
        operations in sequence, and several share a name. Identity of that frame object
        separates invocation N from invocation N+1; the strong reference kept in `_state`
        stops a freed frame's id from being reused while it is still the comparison key.
        Without this, two unrelated calls would look like one repeated call.
        """
        outer = inner = "-"
        outer_frame = None
        frame = sys._getframe(1)
        while frame is not None:
            name = frame.f_code.co_filename.replace("\\", "/")
            if "/autopilot/" in name or name.endswith("/ticket-autopilot.py"):
                label = f"{Path(name).stem}.{frame.f_code.co_name}"
                if inner == "-":
                    inner = label
                outer, outer_frame = label, frame
            frame = frame.f_back
        if outer_frame is not _state["frame"]:
            _state["frame"] = outer_frame
            _state["instance"] += 1
        return outer, inner, _state["instance"]

    _real_init = subprocess.Popen.__init__
    _real_wait = subprocess.Popen.wait

    def _directory(value: object) -> str:
        """Two calls only repeat each other if they asked the same directory the same question."""
        raw = os.path.abspath(str(value)) if value is not None else os.getcwd()
        return hashlib.sha1(raw.encode("utf-8", "replace")).hexdigest()[:8]

    def _init(self, args, *rest, **options):  # type: ignore[no-untyped-def]
        self._probe_started = time.perf_counter()
        sequence = list(args) if isinstance(args, (list, tuple)) else [str(args)]
        self._probe_argv = [_normalize(str(item)) for item in sequence]
        self._probe_cwd = _directory(options.get("cwd", rest[7] if len(rest) > 7 else None))
        self._probe_operation, self._probe_call_site, self._probe_instance = _operation()
        self._probe_logged = False
        return _real_init(self, args, *rest, **options)

    def _log(self, returncode: object) -> None:
        if getattr(self, "_probe_logged", True):
            return
        self._probe_logged = True
        record = {
            "pid": os.getpid(),
            "argv": self._probe_argv,
            "cwd": self._probe_cwd,
            "operation": self._probe_operation,
            "operation_instance": self._probe_instance,
            "call_site": self._probe_call_site,
            "ms": round((time.perf_counter() - self._probe_started) * 1000, 3),
            "returncode": returncode,
        }
        with _SINK.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    def _wait(self, timeout=None):  # type: ignore[no-untyped-def]
        code = _real_wait(self, timeout)
        _log(self, code)
        return code

    subprocess.Popen.__init__ = _init  # type: ignore[method-assign]
    subprocess.Popen.wait = _wait  # type: ignore[method-assign]

    if os.environ.get("AUTOPILOT_DISABLE_SCOPE") == "1":
        # Baseline mode: measure the tree as if the reuse scope did not exist, in this process
        # and in every CLI subprocess, without editing product code for a measurement.
        from contextlib import contextmanager

        @contextmanager
        def _no_scope():
            yield

        _real_import = builtins.__import__

        def _patched_import(name, *rest, **options):  # type: ignore[no-untyped-def]
            module = _real_import(name, *rest, **options)
            target = sys.modules.get("autopilot.git_ops")
            if target is not None and getattr(target, "repository_scope", None) is not _no_scope:
                target.repository_scope = _no_scope
            return module

        builtins.__import__ = _patched_import
