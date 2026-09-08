from __future__ import annotations

import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from autopilot.git_ops import GitError, SubprocessCommandRunner


class PosixCommandBoundsTests(unittest.TestCase):
    @unittest.skipUnless(
        sys.platform == "linux" and hasattr(os, "pidfd_open") and hasattr(signal, "pidfd_send_signal"),
        "native Linux pidfd lifetime observations",
    )
    def test_owned_descendants_exit_and_are_reaped_without_harming_control(self):
        try:
            probe = os.pidfd_open(os.getpid())
        except OSError as error:
            self.skipTest(f"native pidfd observation unavailable: {error}")
        os.close(probe)
        for reason in ("timeout", "cancelled", "output-limit"):
            with self.subTest(reason=reason), tempfile.TemporaryDirectory(prefix="posix-tree-") as directory:
                root = Path(directory)
                pid_file = root / "pids.json"
                release = root / "observed"
                child_program = (
                    "import os,pathlib,sys,time\n"
                    "release=pathlib.Path(sys.argv[1]); deadline=time.monotonic()+8\n"
                    "while not release.exists() and time.monotonic()<deadline: time.sleep(.01)\n"
                    + ("while time.monotonic()<deadline: os.write(1,b'x'*4096)\n"
                       if reason == "output-limit" else "time.sleep(8)\n")
                )
                program = (
                    "import json,os,pathlib,subprocess,time\n"
                    f"child=subprocess.Popen({[sys.executable, '-I', '-S', '-B', '-c', child_program, str(release)]!r})\n"
                    f"pathlib.Path({str(pid_file)!r}).write_text(json.dumps([os.getpid(),child.pid]),encoding='ascii')\n"
                    "deadline=time.monotonic()+8\n"
                    f"while not pathlib.Path({str(release)!r}).exists() and time.monotonic()<deadline: time.sleep(.01)\n"
                    + ("raise SystemExit(0)\n" if reason == "timeout" else "time.sleep(8)\n")
                )
                stop = threading.Event()
                cancel = threading.Event()
                pidfds = []
                faults = []

                def observe_and_release():
                    while not stop.wait(.01):
                        try:
                            pids = json.loads(pid_file.read_text(encoding="ascii"))
                        except (FileNotFoundError, ValueError):
                            continue
                        try:
                            for pid in pids:
                                pidfds.append(os.pidfd_open(pid))
                        except OSError as error:
                            faults.append(str(error))
                        release.touch()
                        if reason == "cancelled":
                            cancel.set()
                        return

                observer = threading.Thread(target=observe_and_release, daemon=True)
                control = subprocess.Popen([
                    sys.executable, "-I", "-S", "-B", "-c", "import time; time.sleep(8)",
                ])
                observer.start()
                try:
                    with patch.dict(os.environ, {
                        "TICKET_AUTOPILOT_COMMAND_TIMEOUT_SECONDS": ".8" if reason == "timeout" else "5",
                        "TICKET_AUTOPILOT_COMMAND_MAX_OUTPUT_BYTES": "1024",
                    }):
                        started = time.monotonic()
                        with self.assertRaisesRegex(GitError, reason):
                            SubprocessCommandRunner(cancel_event=cancel).run(
                                [sys.executable, "-I", "-S", "-B", "-c", program], cwd=root,
                            )
                        self.assertLess(time.monotonic() - started, 2.5)
                    self.assertFalse(faults)
                    self.assertEqual(len(pidfds), 2)
                    poller = select.poll()
                    for fd in pidfds:
                        poller.register(fd, select.POLLIN)
                    exited = dict(poller.poll(0))
                    for fd in pidfds:
                        self.assertTrue(exited.get(fd, 0) & (select.POLLIN | select.POLLHUP))
                    self.assertIsNone(control.poll())
                    # POLLIN proves exact-process exit; HUP additionally proves
                    # reaping. Orphan reaping here is by this Linux environment's
                    # init/subreaper, not an invented portable Autopilot capability.
                    deadline = time.monotonic() + 2
                    while True:
                        reaped = dict(poller.poll(0))
                        if all(reaped.get(fd, 0) & select.POLLHUP for fd in pidfds):
                            break
                        if time.monotonic() >= deadline:
                            self.fail(f"Linux environment did not reap fixture processes: {reaped}")
                        time.sleep(.01)
                finally:
                    stop.set()
                    observer.join(timeout=2)
                    for fd in pidfds:
                        try:
                            poller = select.poll()
                            poller.register(fd, select.POLLIN)
                            if not poller.poll(0):
                                signal.pidfd_send_signal(fd, signal.SIGKILL)
                            self.assertTrue(poller.poll(5000))
                        finally:
                            os.close(fd)
                    if control.poll() is None:
                        control.kill()
                    control.wait(timeout=3)
                    self.assertFalse(observer.is_alive())

    @unittest.skipUnless(os.name == "posix", "native POSIX SIGCHLD disposition")
    def test_ignored_sigchld_is_rejected_before_launch(self):
        with tempfile.TemporaryDirectory(prefix="ignored-sigchld-") as directory:
            root = Path(directory)
            marker = root / "must-not-run"
            target = (
                "import pathlib,sys; "
                f"pathlib.Path({str(marker)!r}).write_bytes(b'executed'); sys.exit(7)"
            )
            driver = f'''
import json,signal,sys
from pathlib import Path
sys.path.insert(0,{str(SCRIPTS)!r})
from autopilot.git_ops import GitError,SubprocessCommandRunner
signal.signal(signal.SIGCHLD,signal.SIG_IGN)
try:
    result=SubprocessCommandRunner().run({[sys.executable, '-I', '-S', '-B', '-c', target]!r},cwd=Path({directory!r}))
except GitError as error:
    print(json.dumps({{'error':str(error)}}))
else:
    print(json.dumps({{'unexpected_completed_exit':result.returncode}}))
'''
            result = subprocess.run(
                [sys.executable, "-I", "-S", "-B", "-c", driver], capture_output=True, cwd=root,
                env=dict(os.environ, TICKET_AUTOPILOT_COMMAND_TIMEOUT_SECONDS="5"), timeout=15,
            )
            self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", errors="replace"))
            observation = json.loads(result.stdout.decode("utf-8"))
            self.assertIn("containment", observation.get("error", ""), observation)
            self.assertIn("not executed", observation["error"])
            self.assertFalse(marker.exists())


if __name__ == "__main__":
    unittest.main()
