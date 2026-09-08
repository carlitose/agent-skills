"""Own a local command tree and return data only after bounded completion."""
from __future__ import annotations

import ctypes
from ctypes import wintypes as w
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import threading
import time


class CaptureFailure(RuntimeError):
    def __init__(self, reason: str, detail: str, *, started: bool = False):
        self.reason = reason
        self.started = started
        self.stderr = b""
        self.cleanup_issues: list[str] = []
        super().__init__(detail)


class _BasicLimits(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_longlong),
        ("PerJobUserTimeLimit", ctypes.c_longlong),
        ("LimitFlags", w.DWORD),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", w.DWORD),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", w.DWORD),
        ("SchedulingClass", w.DWORD),
    ]


class _ExtendedLimits(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", _BasicLimits),
        ("IoInfo", ctypes.c_ulonglong * 6),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


class _Accounting(ctypes.Structure):
    _fields_ = [(name, ctypes.c_longlong) for name in (
        "TotalUserTime", "TotalKernelTime", "ThisPeriodTotalUserTime",
        "ThisPeriodTotalKernelTime",
    )] + [(name, w.DWORD) for name in (
        "TotalPageFaultCount", "TotalProcesses", "ActiveProcesses",
        "TotalTerminatedProcesses",
    )]


class _JobMembers(ctypes.Structure):
    # A fixed observation bound, not an unbounded process inventory or PID scan.
    _fields_ = [
        ("assigned", w.DWORD), ("listed", w.DWORD),
        ("pids", ctypes.c_size_t * 4096),
    ]


class _WindowsJob:
    def __init__(self):
        self.member_handles = []
        self.observed_total = None
        self.membership_issues = []
        self.api = ctypes.WinDLL("kernel32", use_last_error=True)
        for name, arguments, result in (
            ("CreateJobObjectW", [ctypes.c_void_p, w.LPCWSTR], w.HANDLE),
            ("SetInformationJobObject", [w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD], w.BOOL),
            ("QueryInformationJobObject", [w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD, ctypes.c_void_p], w.BOOL),
            ("AssignProcessToJobObject", [w.HANDLE, w.HANDLE], w.BOOL),
            ("TerminateJobObject", [w.HANDLE, w.UINT], w.BOOL),
            ("OpenProcess", [w.DWORD, w.BOOL, w.DWORD], w.HANDLE),
            ("IsProcessInJob", [w.HANDLE, w.HANDLE, ctypes.POINTER(w.BOOL)], w.BOOL),
            ("WaitForSingleObject", [w.HANDLE, w.DWORD], w.DWORD),
            ("CloseHandle", [w.HANDLE], w.BOOL),
        ):
            function = getattr(self.api, name)
            function.argtypes, function.restype = arguments, result
        self.handle = self._checked(self.api.CreateJobObjectW(None, None))
        try:
            limits = _ExtendedLimits()
            limits.BasicLimitInformation.LimitFlags = 0x2000  # KILL_ON_JOB_CLOSE
            self._checked(self.api.SetInformationJobObject(
                self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)
            ))
        except BaseException:
            self.close()
            raise

    @staticmethod
    def _checked(value):
        if not value:
            raise ctypes.WinError(ctypes.get_last_error())
        return value

    def assign(self, process: subprocess.Popen) -> None:
        # Use the retained CPython process handle, not a PID lookup/reuse race.
        self._checked(self.api.AssignProcessToJobObject(self.handle, int(process._handle)))

    def _accounting(self):
        accounting = _Accounting()
        self._checked(self.api.QueryInformationJobObject(
            self.handle, 1, ctypes.byref(accounting), ctypes.sizeof(accounting), None
        ))
        return accounting

    def _pin_members(self, deadline):
        self.observed_total = self._accounting().TotalProcesses
        members = _JobMembers()
        self._checked(self.api.QueryInformationJobObject(
            self.handle, 3, ctypes.byref(members), ctypes.sizeof(members), None
        ))
        if members.listed != members.assigned or members.listed > len(members.pids):
            raise OSError("Windows job membership exceeds the bounded complete observation")
        for pid in members.pids[:members.listed]:
            if time.monotonic() >= deadline:
                raise TimeoutError("Windows job member observation exceeded the cleanup allowance")
            # SYNCHRONIZE | PROCESS_QUERY_LIMITED_INFORMATION; no terminate right.
            handle = self._checked(self.api.OpenProcess(0x00101000, False, pid))
            try:
                belongs = w.BOOL()
                self._checked(self.api.IsProcessInJob(handle, self.handle, ctypes.byref(belongs)))
                if not belongs.value:
                    raise OSError("observed PID no longer identifies a member of this Windows job")
                self.member_handles.append(handle)
            except BaseException:
                self.api.CloseHandle(handle)
                raise

    def terminate(self, deadline: float) -> None:
        try:
            self._pin_members(deadline)
        except OSError as error:
            self.membership_issues.append(str(error))
        finally:
            # Always terminate this owned job, even if member observation failed.
            # Never terminate a PID or an unverified process handle.
            self._checked(self.api.TerminateJobObject(self.handle, 1))

    def wait_empty(self, deadline: float) -> None:
        while True:
            if not self._accounting().ActiveProcesses:
                break
            if time.monotonic() >= deadline:
                raise TimeoutError("owned Windows job still has active processes")
            time.sleep(0.01)
        # ActiveProcesses==0 can precede process-handle signaling. Wait for the
        # verified members as well; native accounting alone is not exit proof.
        for handle in self.member_handles:
            milliseconds = int(max(0, deadline - time.monotonic()) * 1000)
            state = self.api.WaitForSingleObject(handle, milliseconds)
            if state == 0xFFFFFFFF:
                raise ctypes.WinError(ctypes.get_last_error())
            if state != 0:
                raise TimeoutError("an observed Windows job member has not signaled exit")
        if self.observed_total is not None and self._accounting().TotalProcesses != self.observed_total:
            self.membership_issues.append("Windows job membership changed during termination observation")
        if self.membership_issues:
            raise OSError("; ".join(self.membership_issues))

    def close(self) -> None:
        errors = []
        handles, self.member_handles = self.member_handles, []
        if self.handle is not None:
            handles.append(self.handle)
            self.handle = None
        for handle in handles:
            try:
                self._checked(self.api.CloseHandle(handle))
            except OSError as error:
                errors.append(str(error))
        if errors:
            raise OSError(f"could not close {len(errors)} owned handles: {'; '.join(errors[:3])}")


class _OutputBudget:
    def __init__(self, limit: int):
        self.remaining = limit
        self.lock = threading.Lock()
        self.exceeded = threading.Event()

    def append(self, target: bytearray, chunk: bytes) -> bool:
        with self.lock:
            count = min(len(chunk), self.remaining)
            target.extend(chunk[:count])
            self.remaining -= count
            if count != len(chunk):
                self.exceeded.set()
                return False
            return True


class _Reader:
    def __init__(self, stream, budget: _OutputBudget):
        self.stream = stream
        self.budget = budget
        self.data = bytearray()
        self.error: str | None = None
        self.eof = False
        self.entered = threading.Event()
        self.start_attempted = self.start_failed = False
        self.thread = threading.Thread(target=self._read, daemon=True)

    def start(self):
        self.start_attempted = True
        try:
            self.thread.start()
        except RuntimeError:
            self.start_failed = True
            raise

    def _read(self):
        self.entered.set()
        try:
            while chunk := self.stream.read(8192):
                if not self.budget.append(self.data, chunk):
                    return
            self.eof = True
        except Exception as error:
            self.error = str(error)


def _cleanup(process, job, assigned, readers) -> list[str]:
    deadline = time.monotonic() + 5
    issues = []
    if process is not None:
        try:
            if job is not None and assigned:
                job.terminate(deadline)
            elif os.name == "posix":
                # The supervisor retains this session/group identity until cleanup.
                os.killpg(process.pid, signal.SIGKILL)
            else:
                process.kill()  # Unreleased supervisor only; no target was launched.
        except ProcessLookupError:
            pass
        except OSError as error:
            issues.append(f"termination: {error}")
        try:
            process.wait(timeout=max(0, deadline - time.monotonic()))
        except (OSError, subprocess.TimeoutExpired) as error:
            issues.append(f"supervisor wait: {error}")
    if job is not None:
        try:
            job.wait_empty(deadline)
        except (OSError, TimeoutError) as error:
            issues.append(f"job wait: {error}")
        finally:
            try:
                job.close()  # Non-inheritable last-handle backstop; never another job.
            except OSError as error:
                issues.append(f"job close: {error}")

    def close_stream(stream):
        try:
            stream.close()
        except (OSError, ValueError) as error:
            issues.append(f"output close: {error}")

    for reader in readers:
        if reader.start_attempted and not reader.start_failed:
            if not reader.entered.wait(timeout=max(0, deadline - time.monotonic())):
                issues.append("output reader startup is unconfirmed")
                continue
        if reader.entered.is_set():
            reader.thread.join(timeout=max(0, deadline - time.monotonic()))
        if reader.thread.is_alive():
            issues.append("output reader did not stop; cleanup is unconfirmed")
        else:
            close_stream(reader.stream)
    if process is not None:
        for stream in (process.stdout, process.stderr):
            if stream is not None and all(reader.stream is not stream for reader in readers):
                close_stream(stream)  # Reader construction never took ownership.
    return issues


def capture_command(
    command: list[str], *, cwd: Path, timeout_seconds: float,
    max_output_bytes: int, cancel_event: threading.Event | None = None,
) -> tuple[bytes, bytes, int]:
    """Capture one owned tree; incomplete data is never a command result.

    The helper only releases the target after containment. Its private input
    record preserves caller arguments; bounded target status stays separate from
    stdout/stderr. Inherited stdin, literal argv and target environment stay intact.
    """
    if not command or any(not isinstance(arg, str) or "\0" in arg for arg in command):
        raise CaptureFailure("configuration", "command must be non-empty literal argv")
    if os.name not in {"nt", "posix"}:
        raise CaptureFailure("platform", "process-tree ownership is unsupported on this platform")
    if not 0.1 <= timeout_seconds <= 3600:
        raise CaptureFailure("configuration", "timeout must be finite and from 0.1 to 3600 seconds")
    if type(max_output_bytes) is not int or not 1 <= max_output_bytes <= 64 * 1024 * 1024:
        raise CaptureFailure("configuration", "output limit must be from 1 to 67108864 bytes")
    if cancel_event is not None and cancel_event.is_set():
        raise CaptureFailure("cancelled", "cancellation requested before launch")
    if os.name == "posix" and signal.getsignal(signal.SIGCHLD) != signal.SIG_DFL:
        raise CaptureFailure(
            "containment", "POSIX supervision requires the default SIGCHLD disposition; "
            "automatic or independent child reaping can lose exit identity and group ownership",
        )
    budget = _OutputBudget(max_output_bytes)
    cwd = cwd.absolute()
    deadline = time.monotonic() + timeout_seconds
    try:
        control_owner = tempfile.TemporaryDirectory(prefix="tap-command-")
    except OSError as error:
        raise CaptureFailure("capture", f"private control creation failed: {error}") from error
    control = Path(control_owner.name)
    process = job = None
    readers = []
    assigned = released = False
    failure = None
    result = None
    try:
        (control / "request.json").write_text(json.dumps({
            "command": command, "cwd": str(cwd), "timeout_seconds": timeout_seconds,
        }, ensure_ascii=True), encoding="utf-8")
        if os.name == "nt":
            try:
                job = _WindowsJob()
            except (OSError, AttributeError, TypeError) as error:
                raise CaptureFailure("containment", f"Windows job setup unavailable: {error}") from error
        process = subprocess.Popen(
            [sys.executable, "-I", "-S", "-B",
             str(Path(__file__).with_name("_command_supervisor.py")), str(control)],
            cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0,
            start_new_session=os.name == "posix",
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
        )
        for stream in (process.stdout, process.stderr):
            reader = _Reader(stream, budget)
            readers.append(reader)  # Register before starting another resource.
            reader.start()
        if job is not None:
            try:
                job.assign(process)
            except (OSError, AttributeError, TypeError) as error:
                raise CaptureFailure("containment", f"Windows job assignment unavailable: {error}") from error
            assigned = True
        if cancel_event is not None and cancel_event.is_set():
            raise CaptureFailure("cancelled", "cancellation requested before target release")
        if time.monotonic() >= deadline:
            raise CaptureFailure("timeout", "deadline exceeded before target release", started=True)
        # Be conservative if release itself raises: it may have become visible.
        released = True
        (control / "release").touch()
        result_path = control / "result.json"
        while True:
            if cancel_event is not None and cancel_event.is_set():
                raise CaptureFailure("cancelled", "caller requested cancellation", started=True)
            if budget.exceeded.is_set():
                raise CaptureFailure(
                    "output-limit", f"combined stdout/stderr exceeded {max_output_bytes} bytes; "
                    "complete data is unavailable", started=True,
                )
            if any(reader.error is not None for reader in readers):
                raise CaptureFailure("capture", "an output stream could not be read", started=True)
            if all(reader.eof for reader in readers):
                if not result_path.exists():
                    raise CaptureFailure(
                        "control", "supervisor output ended without an actual-target result", started=True,
                    )
                with result_path.open("rb") as record:
                    raw = record.read(8193)
                if len(raw) > 8192:
                    raise CaptureFailure("control", "supervisor result exceeded its bound", started=True)
                result = json.loads(raw)
                if not isinstance(result, dict) or set(result) not in ({"returncode"}, {"error"}):
                    raise CaptureFailure("control", "supervisor result is invalid", started=True)
                if "error" in result:
                    raise CaptureFailure("launch", str(result["error"]), started=True)
                if type(result["returncode"]) is not int:
                    raise CaptureFailure("control", "target exit code is invalid", started=True)
                break
            if time.monotonic() >= deadline:
                raise CaptureFailure("timeout", f"deadline {timeout_seconds:g}s exceeded", started=True)
            time.sleep(0.01)
    except CaptureFailure as error:
        failure = error
    except KeyboardInterrupt:
        failure = CaptureFailure("cancelled", "caller interrupted command execution", started=released)
    except (OSError, ValueError, AttributeError, RuntimeError) as error:
        failure = CaptureFailure("capture", str(error), started=released)
    finally:
        cleanup_issues = []
        try:
            cleanup_issues = _cleanup(process, job, assigned, readers)
        finally:
            try:
                control_owner.cleanup()
            except OSError as error:
                cleanup_issues.append(f"private control cleanup: {error}")
    # Readers may cross the limit between the loop's check and its EOF check.
    # Decide completeness again after their bounded joins, never from a prefix.
    if failure is None and budget.exceeded.is_set():
        failure = CaptureFailure(
            "output-limit", f"combined stdout/stderr exceeded {max_output_bytes} bytes; "
            "complete data is unavailable", started=released,
        )
    if failure is None and any(not reader.eof for reader in readers):
        failure = CaptureFailure(
            "capture", "an output stream did not reach EOF; complete data is unavailable",
            started=released,
        )
    stderr = bytes(readers[1].data) if len(readers) == 2 else b""
    if failure is not None or cleanup_issues:
        failure = failure or CaptureFailure("cleanup", "cleanup could not be confirmed", started=released)
        failure.stderr = stderr
        failure.cleanup_issues = cleanup_issues
        raise failure
    return bytes(readers[0].data), stderr, result["returncode"]
