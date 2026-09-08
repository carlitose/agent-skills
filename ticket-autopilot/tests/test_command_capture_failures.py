from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from autopilot import command_capture
from autopilot.git_ops import GitError, SubprocessCommandRunner


class CommandCaptureFailureTests(unittest.TestCase):
    def test_second_reader_start_failure_keeps_cleanup_owned_and_prevents_target_release(self):
        before = set(threading.enumerate())
        real_start = threading.Thread.start
        starts = 0

        def start_thread(thread):
            nonlocal starts
            starts += 1
            if starts == 2:
                raise RuntimeError("fixture cannot start second output reader")
            return real_start(thread)

        with tempfile.TemporaryDirectory(prefix="reader-start-") as directory:
            root = Path(directory)
            marker = root / "must-not-run"
            program = f"from pathlib import Path; Path({str(marker)!r}).write_bytes(b'executed')"
            with patch.object(threading.Thread, "start", autospec=True, side_effect=start_thread):
                with self.assertRaisesRegex(GitError, "second output reader") as raised:
                    SubprocessCommandRunner().run(
                        [sys.executable, "-I", "-S", "-B", "-c", program], cwd=root,
                    )
            self.assertIn("not executed", str(raised.exception))
            self.assertFalse(marker.exists())
            self.assertEqual([t.name for t in threading.enumerate() if t not in before], [])

    def test_private_control_creation_failure_is_reported_before_target_launch(self):
        with tempfile.TemporaryDirectory(prefix="control-unavailable-") as directory:
            root = Path(directory)
            marker = root / "must-not-run"
            program = f"from pathlib import Path; Path({str(marker)!r}).write_bytes(b'executed')"
            with patch("autopilot.command_capture.tempfile.TemporaryDirectory",
                       side_effect=PermissionError("fixture private control unavailable")):
                with self.assertRaisesRegex(GitError, "private control") as raised:
                    SubprocessCommandRunner().run(
                        [sys.executable, "-I", "-S", "-B", "-c", program], cwd=root,
                    )
            self.assertIn("not executed", str(raised.exception))
            self.assertFalse(marker.exists())

    def test_output_close_failure_preserves_failure_and_closes_the_other_pipe(self):
        class FailedClose:
            def __init__(self, stream):
                self.stream = stream

            def read(self, size):
                return self.stream.read(size)

            def close(self):
                self.stream.close()
                raise OSError("fixture output close refused")

        real_popen = subprocess.Popen
        pipes = []

        def failing_close(*args, **kwargs):
            process = real_popen(*args, **kwargs)
            pipes.extend([process.stdout, process.stderr])
            process.stdout = FailedClose(process.stdout)
            return process

        with tempfile.TemporaryDirectory(prefix="close-failure-") as directory:
            with patch("autopilot.command_capture.subprocess.Popen", side_effect=failing_close):
                with self.assertRaisesRegex(GitError, "cleanup unconfirmed") as raised:
                    SubprocessCommandRunner().run(
                        [sys.executable, "-I", "-S", "-B", "-c", 'print("{}")'], cwd=Path(directory),
                    )
            self.assertIn("fixture output close refused", str(raised.exception))
            self.assertEqual(len(pipes), 2)
            self.assertTrue(all(pipe.closed for pipe in pipes))

    def test_private_control_cleanup_failure_preserves_diagnostics_and_primary_failure(self):
        real_directory = tempfile.TemporaryDirectory

        class FailedControlCleanup:
            def __init__(self, *args, **kwargs):
                self.owner = real_directory(*args, **kwargs)
                self.name = self.owner.name

            def cleanup(self):
                self.owner.cleanup()
                raise PermissionError("fixture private control cleanup refused")

        for mode in ("complete", "timeout"):
            with self.subTest(mode=mode), real_directory(prefix="control-cleanup-") as directory:
                program = "import sys,time; print('fixture diagnostic',file=sys.stderr,flush=True); " + (
                    "time.sleep(2)" if mode == "timeout" else 'print("{}")'
                )
                with patch("autopilot.command_capture.tempfile.TemporaryDirectory", FailedControlCleanup), \
                        patch.dict(os.environ, {"TICKET_AUTOPILOT_COMMAND_TIMEOUT_SECONDS": ".5"}):
                    with self.assertRaisesRegex(GitError, "command timeout" if mode == "timeout" else "command cleanup") as raised:
                        SubprocessCommandRunner().run(
                            [sys.executable, "-I", "-S", "-B", "-c", program], cwd=Path(directory),
                        )
                message = str(raised.exception)
                self.assertIn("fixture diagnostic", message)
                self.assertIn("cleanup unconfirmed", message)
                self.assertIn("private control cleanup refused", message)

    def test_missing_or_invalid_target_status_never_returns_valid_stdout_as_complete(self):
        cases = [
            ("missing", None, "control"),
            ("shape", b"{}", "control"),
            ("boolean", b'{"returncode":true}', "control"),
            ("oversize", b'{"returncode":0}' + b" " * 9000, "control"),
            ("malformed", b"{broken", "capture"),
        ]
        real_popen = subprocess.Popen
        for label, status, reason in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory(prefix="invalid-status-") as directory:
                root = Path(directory)
                helper = root / "fixture_supervisor.py"
                body = (
                    "import os,pathlib,sys,time\n"
                    "control=pathlib.Path(sys.argv[1]); deadline=time.monotonic()+5\n"
                    "while not (control/'release').exists() and time.monotonic()<deadline: time.sleep(.01)\n"
                    + (f"(control/'result.json').write_bytes(bytes.fromhex({status.hex()!r}))\n" if status is not None else "")
                    + "sys.stdout.buffer.write(b'{}'); sys.stdout.flush()\n"
                    "os.close(1); os.close(2); time.sleep(8)\n"
                )
                helper.write_text(body, encoding="utf-8", newline="\n")

                def status_producer(command, **options):
                    # Substitute only the private-status producer; it is still a
                    # real contained process. This is not a live provider fixture.
                    return real_popen([*command[:4], str(helper), command[-1]], **options)

                with patch("autopilot.command_capture.subprocess.Popen", side_effect=status_producer), \
                        patch.dict(os.environ, {"TICKET_AUTOPILOT_COMMAND_TIMEOUT_SECONDS": ".5"}):
                    with self.assertRaisesRegex(GitError, f"command {reason}"):
                        SubprocessCommandRunner().run(
                            [sys.executable, "-I", "-S", "-B", "-c", 'print("{}")'], cwd=root,
                        )

    @unittest.skipUnless(os.name == "nt", "native Windows job membership")
    def test_an_unassociated_process_handle_is_not_adopted_or_terminated(self):
        job = command_capture._WindowsJob()
        control = subprocess.Popen([
            sys.executable, "-I", "-S", "-B", "-c", "import time; time.sleep(8)",
        ])
        real_open = job.api.OpenProcess
        # Model a stale PID lookup using a fresh handle to our living control.
        # Membership validation and the owned job/control process remain native.
        job.api.OpenProcess = lambda access, inherit, pid: real_open(0x00101000, False, control.pid)
        try:
            with tempfile.TemporaryDirectory(prefix="wrong-job-member-") as directory:
                started = time.monotonic()
                with patch("autopilot.command_capture._WindowsJob", return_value=job):
                    with self.assertRaisesRegex(GitError, "no longer identifies a member") as raised:
                        SubprocessCommandRunner().run(
                            [sys.executable, "-I", "-S", "-B", "-c", 'print("{}")'], cwd=Path(directory),
                        )
                self.assertIn("cleanup unconfirmed", str(raised.exception))
                self.assertIsNone(control.poll())
                self.assertLess(time.monotonic() - started, 2.5)
        finally:
            try:
                if control.poll() is None:
                    control.kill()
                control.wait(timeout=3)
            finally:
                job.close()

    @unittest.skipUnless(os.name == "nt", "Windows membership accounting adapter")
    def test_membership_growth_prevents_a_confirmed_cleanup_claim(self):
        job = command_capture._WindowsJob()
        real_accounting = job._accounting
        reads = 0

        def advanced_accounting():
            nonlocal reads
            reads += 1
            accounting = real_accounting()
            if reads > 1:
                accounting.TotalProcesses += 1  # Modeled birth after the pinned snapshot.
            return accounting

        try:
            with tempfile.TemporaryDirectory(prefix="changed-job-members-") as directory:
                with patch("autopilot.command_capture._WindowsJob", return_value=job), \
                        patch.object(job, "_accounting", side_effect=advanced_accounting):
                    with self.assertRaisesRegex(GitError, "membership changed") as raised:
                        SubprocessCommandRunner().run(
                            [sys.executable, "-I", "-S", "-B", "-c", 'print("{}")'], cwd=Path(directory),
                        )
                self.assertIn("cleanup unconfirmed", str(raised.exception))
        finally:
            job.close()

    def test_launch_error_status_is_bounded_at_its_producer_not_just_its_reader(self):
        real_popen = subprocess.Popen
        real_directory = tempfile.TemporaryDirectory
        sizes = []

        class ObservedControl:
            def __init__(self, *args, **kwargs):
                self.owner = real_directory(*args, **kwargs)
                self.name = self.owner.name

            def cleanup(self):
                sizes.append((Path(self.name) / "result.json").stat().st_size)
                self.owner.cleanup()

        with real_directory(prefix="large-launch-diagnostic-") as directory:
            root = Path(directory)
            helper = root / "fixture_supervisor.py"
            scripts = str(Path(__file__).resolve().parents[1] / "scripts")
            helper.write_text(
                "import sys\n"
                f"sys.path.insert(0,{scripts!r})\n"
                "from autopilot import _command_supervisor as supervisor\n"
                "def failed_launch(*args,**kwargs): raise OSError('β'*10000)\n"
                "supervisor.subprocess.Popen=failed_launch\n"
                "supervisor.main()\n",
                encoding="utf-8", newline="\n",
            )

            def failing_producer(command, **options):
                return real_popen([*command[:4], str(helper), command[-1]], **options)

            with patch("autopilot.command_capture.subprocess.Popen", side_effect=failing_producer), \
                    patch("autopilot.command_capture.tempfile.TemporaryDirectory", ObservedControl):
                with self.assertRaisesRegex(GitError, "command launch") as raised:
                    SubprocessCommandRunner().run(
                        [sys.executable, "-I", "-S", "-B", "-c", 'print("{}")'], cwd=root,
                    )
            self.assertEqual(len(sizes), 1)
            self.assertLessEqual(sizes[0], 8192)
            self.assertIn("truncated", str(raised.exception))
            self.assertLess(len(str(raised.exception)), 2048)

    def test_default_limits_and_per_call_overrides_reach_the_capture_capability(self):
        observations = []

        def capture(command, **options):
            observations.append((options["timeout_seconds"], options["max_output_bytes"]))
            return b"{}", b"", 0

        # This proves configuration wiring, not a 300-second native timing run.
        with patch.dict(os.environ), patch("autopilot.git_ops.capture_command", side_effect=capture):
            os.environ.pop("TICKET_AUTOPILOT_COMMAND_TIMEOUT_SECONDS", None)
            os.environ.pop("TICKET_AUTOPILOT_COMMAND_MAX_OUTPUT_BYTES", None)
            runner = SubprocessCommandRunner()
            runner.run([sys.executable, "-c", 'print("{}")'], cwd=Path("."))
            os.environ["TICKET_AUTOPILOT_COMMAND_TIMEOUT_SECONDS"] = ".25"
            os.environ["TICKET_AUTOPILOT_COMMAND_MAX_OUTPUT_BYTES"] = "1234"
            runner.run([sys.executable, "-c", 'print("{}")'], cwd=Path("."))
        self.assertEqual(observations, [(300, 16777216), (.25, 1234)])


if __name__ == "__main__":
    unittest.main()
