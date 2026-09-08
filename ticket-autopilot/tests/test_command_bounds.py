from __future__ import annotations

import ctypes
from ctypes import wintypes
import json
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

from autopilot import git_ops
from autopilot.command_capture import CaptureFailure
from autopilot.git_ops import GitError, SubprocessCommandRunner
from autopilot.providers import GET_PR_STATE, ProviderError, ProviderExecutor, detect_provider

if __package__:
    from .git_test_support import isolated_git_environment
else:
    from git_test_support import isolated_git_environment


def windows_process_api():
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    for name, arguments, result in (
        ("OpenProcess", [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD], wintypes.HANDLE),
        ("WaitForSingleObject", [wintypes.HANDLE, wintypes.DWORD], wintypes.DWORD),
        ("CloseHandle", [wintypes.HANDLE], wintypes.BOOL),
        ("TerminateProcess", [wintypes.HANDLE, wintypes.UINT], wintypes.BOOL),
    ):
        function = getattr(kernel, name)
        function.argtypes, function.restype = arguments, result
    return kernel


class CommandBoundsTests(unittest.TestCase):
    def test_default_executor_times_out_with_diagnostics_instead_of_complete_data(self):
        program = (
            "import pathlib,sys,time; "
            "pathlib.Path(sys.argv[1]).write_bytes(b'entered'); "
            "sys.stderr.buffer.write(b'fixture diagnostic \\xf3'); "
            "sys.stderr.buffer.flush(); time.sleep(2); "
            "sys.stdout.buffer.write(b'{\"complete\":true}')"
        )
        with tempfile.TemporaryDirectory(prefix="command-café-") as directory:
            root = Path(directory)
            entered = root / "started marker.txt"
            with patch.dict(os.environ, {"TICKET_AUTOPILOT_COMMAND_TIMEOUT_SECONDS": "0.5"}):
                started = time.monotonic()
                with self.assertRaisesRegex(GitError, "timeout") as raised:
                    SubprocessCommandRunner().run(
                        [sys.executable, "-I", "-S", "-B", "-c", program, str(entered)],
                        cwd=root,
                    )
                elapsed = time.monotonic() - started
            self.assertTrue(entered.exists(), "fixture never reached execution")
            self.assertLess(elapsed, 1.75)
            self.assertIn("fixture diagnostic \ufffd", str(raised.exception))
            self.assertIn("uncertain", str(raised.exception))
            self.assertIn("reobserve", str(raised.exception))

    def test_output_limit_does_not_return_valid_json_with_incomplete_diagnostics(self):
        program = "import os; os.write(1,b'{\"ok\":true}'); os.write(2,b'x'*2048)"
        with tempfile.TemporaryDirectory(prefix="command-noise-") as directory:
            with patch.dict(os.environ, {
                "TICKET_AUTOPILOT_COMMAND_TIMEOUT_SECONDS": "5",
                "TICKET_AUTOPILOT_COMMAND_MAX_OUTPUT_BYTES": "1024",
            }):
                with self.assertRaisesRegex(GitError, "output-limit") as raised:
                    SubprocessCommandRunner().run(
                        [sys.executable, "-I", "-S", "-B", "-c", program], cwd=Path(directory)
                    )
                self.assertIn("uncertain", str(raised.exception))

    @unittest.skipUnless(os.name == "nt", "native Windows descendant handles")
    def test_timeout_reaps_descendant_after_parent_exit_without_killing_control(self):
        kernel = windows_process_api()
        sleeping = [sys.executable, "-I", "-S", "-B", "-c", "import time; time.sleep(8)"]
        program = (
            "import pathlib,subprocess,sys; "
            "p=subprocess.Popen([sys.executable,'-I','-S','-B','-c',"
            "'import time; time.sleep(8)']); "
            "pathlib.Path(sys.argv[1]).write_text(str(p.pid),encoding='ascii'); "
            "sys.stdout.buffer.write(b'{\"complete\":true}')"
        )
        with tempfile.TemporaryDirectory(prefix="command-tree-") as directory:
            root = Path(directory)
            pid_file = root / "fixture-child.pid"
            handles = []
            faults = []
            stop = threading.Event()

            def observe_fixture_child():
                while not stop.wait(0.01):
                    try:
                        pid = int(pid_file.read_text(encoding="ascii"))
                    except (FileNotFoundError, ValueError):
                        continue
                    handle = kernel.OpenProcess(0x00100001, False, pid)
                    if not handle:
                        faults.append(ctypes.get_last_error())
                    else:
                        handles.append(handle)
                    return

            observer = threading.Thread(target=observe_fixture_child, daemon=True)
            control = subprocess.Popen(sleeping)
            observer.start()
            try:
                with patch.dict(os.environ, {"TICKET_AUTOPILOT_COMMAND_TIMEOUT_SECONDS": "1"}):
                    started = time.monotonic()
                    with self.assertRaisesRegex(GitError, "timeout"):
                        SubprocessCommandRunner().run(
                            [sys.executable, "-I", "-S", "-B", "-c", program, str(pid_file)],
                            cwd=root,
                        )
                    elapsed = time.monotonic() - started
                self.assertFalse(faults, f"fixture handle observation failed: {faults}")
                self.assertEqual(len(handles), 1, "fixture child was not observed")
                self.assertEqual(kernel.WaitForSingleObject(handles[0], 0), 0,
                                 "command returned while its fixture child was alive")
                self.assertLess(elapsed, 2.5, "capture waited for the child's natural expiry")
                self.assertIsNone(control.poll(), "unassociated control was terminated")
            finally:
                stop.set()
                observer.join(timeout=2)
                for handle in handles:
                    try:
                        if kernel.WaitForSingleObject(handle, 0) == 258:
                            self.assertTrue(kernel.TerminateProcess(handle, 123))
                        self.assertEqual(kernel.WaitForSingleObject(handle, 5000), 0)
                    finally:
                        kernel.CloseHandle(handle)
                if control.poll() is None:
                    control.kill()
                control.wait(timeout=3)
                self.assertFalse(observer.is_alive(), "fixture observer remained alive")

    @unittest.skipUnless(os.name == "nt", "native Windows cancellation handles")
    def test_cancellation_reaps_the_started_tree_and_preserves_control(self):
        kernel = windows_process_api()
        sleeping = [sys.executable, "-I", "-S", "-B", "-c", "import time; time.sleep(8)"]
        program = (
            "import json,os,pathlib,subprocess,sys,time; "
            "p=subprocess.Popen([sys.executable,'-I','-S','-B','-c',"
            "'import time; time.sleep(8)']); "
            "pathlib.Path(sys.argv[1]).write_text(json.dumps([os.getpid(),p.pid]),encoding='ascii'); "
            "sys.stderr.buffer.write(b'fixture cancellation'); sys.stderr.buffer.flush(); time.sleep(8)"
        )
        with tempfile.TemporaryDirectory(prefix="command-cancel-") as directory:
            root = Path(directory)
            pid_file = root / "fixture-pids.json"
            cancel = threading.Event()
            stop = threading.Event()
            handles = []
            faults = []

            def cancel_started_fixture():
                while not stop.wait(0.01):
                    try:
                        pids = json.loads(pid_file.read_text(encoding="ascii"))
                    except (FileNotFoundError, ValueError):
                        continue
                    for pid in pids:
                        handle = kernel.OpenProcess(0x00100001, False, pid)
                        if handle:
                            handles.append(handle)
                        else:
                            faults.append(ctypes.get_last_error())
                    cancel.set()
                    return

            observer = threading.Thread(target=cancel_started_fixture, daemon=True)
            control = subprocess.Popen(sleeping)
            observer.start()
            try:
                with patch.dict(os.environ, {"TICKET_AUTOPILOT_COMMAND_TIMEOUT_SECONDS": "5"}):
                    started = time.monotonic()
                    with self.assertRaisesRegex(GitError, "cancelled") as raised:
                        SubprocessCommandRunner(cancel_event=cancel).run(
                            [sys.executable, "-I", "-S", "-B", "-c", program, str(pid_file)],
                            cwd=root,
                        )
                    elapsed = time.monotonic() - started
                self.assertTrue(cancel.is_set(), "fixture cancellation was not requested")
                self.assertFalse(faults)
                self.assertEqual(len(handles), 2)
                for handle in handles:
                    self.assertEqual(kernel.WaitForSingleObject(handle, 0), 0,
                                     "cancelled command returned with a live fixture process")
                self.assertLess(elapsed, 2.5)
                self.assertIsNone(control.poll())
                self.assertIn("fixture cancellation", str(raised.exception))
                self.assertIn("uncertain", str(raised.exception))
            finally:
                stop.set()
                observer.join(timeout=2)
                for handle in handles:
                    try:
                        if kernel.WaitForSingleObject(handle, 0) == 258:
                            self.assertTrue(kernel.TerminateProcess(handle, 123))
                        self.assertEqual(kernel.WaitForSingleObject(handle, 5000), 0)
                    finally:
                        kernel.CloseHandle(handle)
                if control.poll() is None:
                    control.kill()
                control.wait(timeout=3)
                self.assertFalse(observer.is_alive())

    @unittest.skipUnless(os.name == "nt", "native Windows local CLI fixture")
    def test_default_provider_executor_reports_bounded_failure_with_diagnostics(self):
        if not sys.executable.isascii():
            self.skipTest("ASCII Python launcher spelling is required by this batch fixture")
        with tempfile.TemporaryDirectory(prefix="provider-café-") as directory:
            root = Path(directory)
            producer = root / "fixture.py"
            producer.write_text(
                "import json,pathlib,sys,time\n"
                "pathlib.Path(__file__).with_name('started.json').write_text(json.dumps(sys.argv[1:]),encoding='utf-8')\n"
                "sys.stderr.buffer.write(b'fixture provider diagnostic \\xf3'); sys.stderr.buffer.flush()\n"
                "time.sleep(2); sys.stdout.buffer.write(b'{}')\n",
                encoding="utf-8", newline="\n",
            )
            shim = root / "gh.cmd"
            shim.write_text(
                f'@"{sys.executable}" -I -S -B "%~dp0fixture.py" %*\r\n',
                encoding="ascii", newline="",
            )
            with patch.dict(os.environ, {"TICKET_AUTOPILOT_COMMAND_TIMEOUT_SECONDS": "1"}), \
                    patch("autopilot.git_ops.shutil.which", return_value=str(shim)):
                executor = ProviderExecutor(detect_provider("", override="github"), cwd=root)
                with self.assertRaisesRegex(ProviderError, "timeout") as raised:
                    executor.execute(GET_PR_STATE, pr_id="91")
            self.assertEqual(json.loads((root / "started.json").read_text(encoding="utf-8"))[:3],
                             ["pr", "view", "91"])
            self.assertIn("fixture provider diagnostic \ufffd", str(raised.exception))
            self.assertIn("uncertain", str(raised.exception))
            self.assertIn("reobserve", str(raised.exception))

    def test_ticket_folder_comparison_uses_the_bounded_git_failure_path(self):
        with isolated_git_environment(), tempfile.TemporaryDirectory(prefix="bounded-git-") as directory:
            root = Path(directory)
            folder = root / "tickets"
            folder.mkdir()
            source = folder / "fixture.md"
            source.write_bytes(b"fixture\n")

            def git(*args):
                return subprocess.run(
                    ["git", *args], cwd=root, capture_output=True, check=True, timeout=15,
                ).stdout.decode("utf-8").strip()

            git("init", "-b", "main")
            git("config", "user.name", "Fixture")
            git("config", "user.email", "fixture@example.invalid")
            git("add", ".")
            git("commit", "-m", "fixture")
            head = git("rev-parse", "HEAD")
            capture = git_ops.capture_command

            def failed_diff(command, **options):
                if command[:2] == ["git", "diff"]:
                    raise CaptureFailure("timeout", "fixture bounded Git diff expired", started=True)
                return capture(command, **options)

            # Inject only the resource failure at the process capability; the
            # disposable Git root/status/ref checks remain real and unchanged.
            with patch("autopilot.git_ops.capture_command", side_effect=failed_diff):
                with self.assertRaisesRegex(GitError, "timeout"):
                    git_ops.assert_ticket_folder_at_ref(root, folder, base_ref=head)
            self.assertEqual(git("rev-parse", "HEAD"), head)
            self.assertEqual(source.read_bytes(), b"fixture\n")
            self.assertEqual(git("status", "--porcelain"), "")

    def test_invalid_limits_fail_before_a_target_can_run(self):
        cases = {
            "TICKET_AUTOPILOT_COMMAND_TIMEOUT_SECONDS": ["", "nan", "inf", "0", "-1", "3601", "bad"],
            "TICKET_AUTOPILOT_COMMAND_MAX_OUTPUT_BYTES": ["", "0", "-1", "67108865", "1.5", "bad"],
        }
        with tempfile.TemporaryDirectory(prefix="invalid-command-limit-") as directory:
            root = Path(directory)
            marker = root / "should-not-exist"
            program = "import pathlib,sys; pathlib.Path(sys.argv[1]).write_bytes(b'executed')"
            for setting, values in cases.items():
                for value in values:
                    with self.subTest(setting=setting, value=value), patch.dict(os.environ, {
                        "TICKET_AUTOPILOT_COMMAND_TIMEOUT_SECONDS": "5",
                        "TICKET_AUTOPILOT_COMMAND_MAX_OUTPUT_BYTES": "8192",
                        setting: value,
                    }):
                        with self.assertRaisesRegex(GitError, setting):
                            SubprocessCommandRunner().run(
                                [sys.executable, "-I", "-S", "-B", "-c", program, str(marker)], cwd=root,
                            )
                        self.assertFalse(marker.exists())

    def test_exact_combined_byte_limit_preserves_data_diagnostics_and_target_exit(self):
        body = " café β\r\n "
        stdout = json.dumps({"body": body}, ensure_ascii=False).encode("utf-8") + b"\r\n \t"
        stderr = b"diagnostic \xf3\r\n"
        total = len(stdout) + len(stderr)
        program = (
            "import sys; "
            f"sys.stdout.buffer.write(bytes.fromhex('{stdout.hex()}')); "
            f"sys.stderr.buffer.write(bytes.fromhex('{stderr.hex()}')); sys.exit(7)"
        )
        with tempfile.TemporaryDirectory(prefix="combined-capture-") as directory:
            with patch.dict(os.environ, {
                "TICKET_AUTOPILOT_COMMAND_TIMEOUT_SECONDS": "5",
                "TICKET_AUTOPILOT_COMMAND_MAX_OUTPUT_BYTES": str(total),
            }):
                result = SubprocessCommandRunner().run(
                    [sys.executable, "-I", "-S", "-B", "-c", program], cwd=Path(directory),
                )
                self.assertEqual(json.loads(result.stdout)["body"], body)
                self.assertEqual(result.stderr, "diagnostic \ufffd")
                self.assertEqual(result.returncode, 7)
                # Each stream fits separately; their combined raw bytes do not.
                self.assertLess(max(len(stdout), len(stderr)), total - 1)
                os.environ["TICKET_AUTOPILOT_COMMAND_MAX_OUTPUT_BYTES"] = str(total - 1)
                with self.assertRaisesRegex(GitError, "output-limit"):
                    SubprocessCommandRunner().run(
                        [sys.executable, "-I", "-S", "-B", "-c", program], cwd=Path(directory),
                    )

    def test_pre_cancelled_runner_does_not_launch_or_clear_the_callers_event(self):
        cancel = threading.Event()
        cancel.set()
        with tempfile.TemporaryDirectory(prefix="pre-cancelled-") as directory:
            root = Path(directory)
            marker = root / "entered"
            program = "import pathlib,sys; pathlib.Path(sys.argv[1]).write_bytes(b'entered'); print('ready')"
            command = [sys.executable, "-I", "-S", "-B", "-c", program, str(marker)]
            runner = SubprocessCommandRunner(cancel_event=cancel)
            with self.assertRaisesRegex(GitError, "cancelled") as raised:
                runner.run(command, cwd=root)
            self.assertIn("not executed", str(raised.exception))
            self.assertFalse(marker.exists())
            self.assertTrue(cancel.is_set())
            cancel.clear()  # Only the caller authorizes reuse; no automatic retry.
            self.assertEqual(runner.run(command, cwd=root).stdout, "ready")
            self.assertEqual(marker.read_bytes(), b"entered")

    def test_default_output_limit_is_applied_without_an_override(self):
        with tempfile.TemporaryDirectory(prefix="default-output-limit-") as directory:
            with patch.dict(os.environ, {"TICKET_AUTOPILOT_COMMAND_TIMEOUT_SECONDS": "5"}):
                os.environ.pop("TICKET_AUTOPILOT_COMMAND_MAX_OUTPUT_BYTES", None)
                with self.assertRaisesRegex(GitError, "output-limit") as raised:
                    SubprocessCommandRunner().run(
                        [sys.executable, "-I", "-S", "-B", "-c",
                         "import sys; sys.stdout.buffer.write(b'x'*(17*1024*1024))"],
                        cwd=Path(directory),
                    )
                self.assertIn("16777216", str(raised.exception))

    def test_supervision_preserves_inherited_stdin_and_literal_unicode_arguments(self):
        arguments = [" café β 日本 ", "quotes'\";&|<>$%!", "line one\nline two", ""]
        payload = b"raw stdin\x00\xff\r\n "
        target = (
            "import json,sys; "
            "sys.stdout.buffer.write(json.dumps({'args':sys.argv[1:],"
            "'input':sys.stdin.buffer.read().hex()},ensure_ascii=False).encode('utf-8'))"
        )
        scripts = str(Path(__file__).resolve().parents[1] / "scripts")
        with tempfile.TemporaryDirectory(prefix="stdin-café-") as directory:
            driver = (
                "import sys; from pathlib import Path; "
                f"sys.path.insert(0,{scripts!r}); "
                "from autopilot.git_ops import SubprocessCommandRunner; "
                f"r=SubprocessCommandRunner().run({[sys.executable, '-I', '-S', '-B', '-c', target, *arguments]!r},"
                f"cwd=Path({directory!r})); "
                "sys.stdout.buffer.write(r.stdout.encode('utf-8')); sys.exit(r.returncode)"
            )
            env = dict(os.environ, TICKET_AUTOPILOT_COMMAND_TIMEOUT_SECONDS="5",
                       TICKET_AUTOPILOT_COMMAND_MAX_OUTPUT_BYTES="8192")
            result = subprocess.run(
                [sys.executable, "-I", "-S", "-B", "-c", driver],
                input=payload, capture_output=True, env=env, cwd=directory, timeout=15,
            )
            self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", errors="replace"))
            document = json.loads(result.stdout.decode("utf-8"))
            self.assertEqual(document, {"args": arguments, "input": payload.hex()})

    def test_failed_launch_names_the_requested_executable_without_exposing_arguments(self):
        with tempfile.TemporaryDirectory(prefix="missing-command-") as directory:
            root = Path(directory)
            missing = str(root / "missing café.exe")
            with self.assertRaisesRegex(GitError, "launch") as raised:
                SubprocessCommandRunner().run([missing, "fixture-sensitive-argument"], cwd=root)
            self.assertIn(repr(missing), str(raised.exception))
            self.assertNotIn("fixture-sensitive-argument", str(raised.exception))

    @unittest.skipUnless(os.name == "nt", "native Windows noisy-tree handles")
    def test_output_limit_terminates_a_noisy_descendant_and_leaves_control_alive(self):
        kernel = windows_process_api()
        sleeping = [sys.executable, "-I", "-S", "-B", "-c", "import time; time.sleep(8)"]
        noisy = (
            "import os,pathlib,sys,time\n"
            "release=pathlib.Path(sys.argv[1]); deadline=time.monotonic()+8\n"
            "while not release.exists() and time.monotonic()<deadline: time.sleep(.01)\n"
            "while time.monotonic()<deadline: os.write(1,b'x'*4096)\n"
        )
        with tempfile.TemporaryDirectory(prefix="noisy-tree-") as directory:
            root = Path(directory)
            pid_file = root / "fixture-pids.json"
            release = root / "observed"
            program = (
                "import json,os,pathlib,subprocess,sys,time; "
                f"p=subprocess.Popen({[sys.executable, '-I', '-S', '-B', '-c', noisy, str(release)]!r}); "
                f"pathlib.Path({str(pid_file)!r}).write_text(json.dumps([os.getpid(),p.pid]),encoding='ascii'); "
                "time.sleep(8)"
            )
            stop = threading.Event()
            handles = []
            faults = []

            def release_observed_fixture():
                while not stop.wait(0.01):
                    try:
                        pids = json.loads(pid_file.read_text(encoding="ascii"))
                    except (FileNotFoundError, ValueError):
                        continue
                    for pid in pids:
                        handle = kernel.OpenProcess(0x00100001, False, pid)
                        if handle:
                            handles.append(handle)
                        else:
                            faults.append(ctypes.get_last_error())
                    release.touch()
                    return

            observer = threading.Thread(target=release_observed_fixture, daemon=True)
            control = subprocess.Popen(sleeping)
            observer.start()
            try:
                with patch.dict(os.environ, {
                    "TICKET_AUTOPILOT_COMMAND_TIMEOUT_SECONDS": "5",
                    "TICKET_AUTOPILOT_COMMAND_MAX_OUTPUT_BYTES": "1024",
                }):
                    started = time.monotonic()
                    with self.assertRaisesRegex(GitError, "output-limit") as raised:
                        SubprocessCommandRunner().run(
                            [sys.executable, "-I", "-S", "-B", "-c", program], cwd=root,
                        )
                    elapsed = time.monotonic() - started
                self.assertFalse(faults)
                self.assertEqual(len(handles), 2)
                states = [kernel.WaitForSingleObject(handle, 0) for handle in handles]
                self.assertEqual(states, [0, 0], str(raised.exception))
                self.assertLess(elapsed, 2.5)
                self.assertIsNone(control.poll())
                self.assertNotIn("cleanup unconfirmed", str(raised.exception))
            finally:
                stop.set()
                observer.join(timeout=2)
                cleanup_errors = []
                try:
                    for handle in handles:
                        try:
                            if kernel.WaitForSingleObject(handle, 0) == 258:
                                # Concurrent exit may make TerminateProcess return
                                # access denied; the retained-handle wait decides.
                                kernel.TerminateProcess(handle, 123)
                            state = kernel.WaitForSingleObject(handle, 5000)
                            if state != 0:
                                cleanup_errors.append(f"fixture handle did not exit: {state}")
                        finally:
                            kernel.CloseHandle(handle)
                finally:
                    if control.poll() is None:
                        control.kill()
                    control.wait(timeout=3)
                self.assertFalse(observer.is_alive())
                self.assertFalse(cleanup_errors)

    def test_keyboard_interrupt_is_reported_as_cancellation_without_reader_threads(self):
        scripts = str(Path(__file__).resolve().parents[1] / "scripts")
        with tempfile.TemporaryDirectory(prefix="interrupt-command-") as directory:
            root = Path(directory)
            marker = root / "started"
            program = (
                "import pathlib,time; "
                f"pathlib.Path({str(marker)!r}).write_bytes(b'started'); time.sleep(8)"
            )
            driver = f'''
import _thread,json,sys,threading,time
from pathlib import Path
sys.path.insert(0,{scripts!r})
from autopilot.git_ops import GitError,SubprocessCommandRunner
before=set(threading.enumerate())
stop=threading.Event()
def interrupt_started_command():
    while not stop.wait(.01):
        if Path({str(marker)!r}).exists():
            _thread.interrupt_main()
            return
observer=threading.Thread(target=interrupt_started_command,daemon=True)
observer.start()
started=time.monotonic()
try:
    SubprocessCommandRunner().run({[sys.executable, '-I', '-S', '-B', '-c', program]!r},cwd=Path({directory!r}))
except GitError as error:
    message=str(error)
else:
    raise AssertionError('interrupted command returned complete data')
finally:
    stop.set()
    observer.join(timeout=2)
extra=[t.name for t in threading.enumerate() if t not in before and t.is_alive()]
print(json.dumps({{'message':message,'elapsed':time.monotonic()-started,'extra_threads':extra}}))
'''
            result = subprocess.run(
                [sys.executable, "-I", "-S", "-B", "-c", driver], capture_output=True,
                env=dict(os.environ, TICKET_AUTOPILOT_COMMAND_TIMEOUT_SECONDS="5"),
                cwd=root, timeout=15,
            )
            self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", errors="replace"))
            observation = json.loads(result.stdout.decode("utf-8"))
            self.assertIn("cancelled", observation["message"])
            self.assertIn("uncertain", observation["message"])
            self.assertLess(observation["elapsed"], 2.5)
            self.assertEqual(observation["extra_threads"], [])

    def test_an_empty_pipe_error_cannot_turn_a_valid_prefix_into_complete_data(self):
        class FailedRead:
            def __init__(self, stream):
                self.stream = stream

            def read(self, size):
                data = self.stream.read(size)
                if not data:
                    raise OSError()  # An empty diagnostic is still a failed read.
                return data

            def close(self):
                self.stream.close()

        real_popen = subprocess.Popen

        def faulty_pipe(*args, **kwargs):
            process = real_popen(*args, **kwargs)
            process.stdout = FailedRead(process.stdout)
            return process

        with tempfile.TemporaryDirectory(prefix="failed-pipe-") as directory:
            # The process is real; only the final OS-pipe observation is failed.
            with patch("autopilot.command_capture.subprocess.Popen", side_effect=faulty_pipe):
                with self.assertRaisesRegex(GitError, "capture"):
                    SubprocessCommandRunner().run(
                        [sys.executable, "-I", "-S", "-B", "-c", 'print("{}")'], cwd=Path(directory),
                    )

    @unittest.skipUnless(os.name == "nt", "Windows containment adapter")
    def test_unavailable_containment_fails_before_target_release_without_fallback(self):
        with tempfile.TemporaryDirectory(prefix="unavailable-job-") as directory:
            root = Path(directory)
            marker = root / "must-not-run"
            program = f"from pathlib import Path; Path({str(marker)!r}).write_bytes(b'executed')"
            with patch("autopilot.command_capture._WindowsJob.assign",
                       side_effect=OSError("fixture job assignment unavailable")):
                with self.assertRaisesRegex(GitError, "containment") as raised:
                    SubprocessCommandRunner().run(
                        [sys.executable, "-I", "-S", "-B", "-c", program], cwd=root,
                    )
            self.assertIn("not executed", str(raised.exception))
            self.assertFalse(marker.exists())

    @unittest.skipUnless(os.name == "nt", "Windows cleanup adapter")
    def test_cleanup_failure_never_returns_data_or_claims_confirmed_reaping(self):
        real_popen = subprocess.Popen
        helpers = []

        def observe_helper(*args, **kwargs):
            process = real_popen(*args, **kwargs)
            helpers.append(process)
            return process

        with tempfile.TemporaryDirectory(prefix="failed-cleanup-") as directory:
            try:
                started = time.monotonic()
                with patch("autopilot.command_capture.subprocess.Popen", side_effect=observe_helper), \
                        patch("autopilot.command_capture._WindowsJob.terminate",
                              side_effect=OSError("fixture termination refused")):
                    with self.assertRaisesRegex(GitError, "cleanup unconfirmed") as raised:
                        SubprocessCommandRunner().run(
                            [sys.executable, "-I", "-S", "-B", "-c", 'print("{}")'],
                            cwd=Path(directory),
                        )
                self.assertLess(time.monotonic() - started, 7.5)
                self.assertIn("fixture termination refused", str(raised.exception))
                self.assertIn("uncertain", str(raised.exception))
            finally:
                # Fixture-owned retained objects only. This does not change the
                # command's reported unconfirmed cleanup into a success claim.
                for helper in helpers:
                    if helper.poll() is None:
                        helper.kill()
                    helper.wait(timeout=5)
                    helper._handle.Close()  # Release the fixture's retained Windows handle.
                # Windows may still report a sharing violation after this modeled
                # failure; the exact lock holder is not established. Reobserve only
                # this empty fixture directory, without suppressing other errors
                # or changing the runtime's unconfirmed-cleanup claim.
                deadline = time.monotonic() + 5
                while True:
                    try:
                        Path(directory).rmdir()
                        break
                    except PermissionError as error:
                        if error.winerror not in (32, 33) or time.monotonic() >= deadline:
                            raise
                        time.sleep(0.01)


if __name__ == "__main__":
    unittest.main()
