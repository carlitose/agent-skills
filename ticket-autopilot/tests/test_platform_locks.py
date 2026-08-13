from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from autopilot import file_lock  # noqa: E402
from autopilot.git_ops import SubprocessCommandRunner  # noqa: E402
from autopilot.ticket_lifecycle import LifecycleError, _folder_lock  # noqa: E402


class FolderLockTests(unittest.TestCase):
    """Both branches, from either platform.

    `_folder_lock` was impossible to reach on Windows until recently and still has no test.
    Each branch is driven here by patching the platform switch, so a POSIX CI run exercises
    the Windows code path and vice versa — otherwise whichever platform nobody develops on
    silently rots.
    """

    def test_posix_branch_takes_and_releases_the_lock(self) -> None:
        acquired: list[bool] = []
        with tempfile.TemporaryDirectory() as temporary:
            with mock.patch.object(file_lock, "WINDOWS", False), mock.patch.object(
                file_lock, "fcntl", create=True
            ) as fake_fcntl:
                fake_fcntl.LOCK_EX = 2
                fake_fcntl.LOCK_UN = 8
                with _folder_lock(Path(temporary) / "state"):
                    acquired.append(True)

        self.assertEqual([True], acquired)
        modes = [call.args[1] for call in fake_fcntl.flock.call_args_list]
        self.assertEqual([2, 8], modes, "acquire blocking, then release")

    def test_windows_branch_takes_and_releases_the_lock(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with mock.patch.object(file_lock, "WINDOWS", True), mock.patch.object(
                file_lock, "msvcrt", create=True
            ) as fake_msvcrt:
                fake_msvcrt.LK_LOCK = 1
                fake_msvcrt.LK_NBLCK = 2
                fake_msvcrt.LK_UNLCK = 0
                with _folder_lock(Path(temporary) / "state"):
                    pass

        modes = [call.args[1] for call in fake_msvcrt.locking.call_args_list]
        self.assertEqual([1, 0], modes, "LK_LOCK to acquire, LK_UNLCK to release")

    def test_a_held_folder_is_reported_as_held_not_as_a_broken_lock(self) -> None:
        # The defect this replaces reported "folder is locked" for an ImportError, sending
        # you hunting for a stale lockfile that was never created.
        with tempfile.TemporaryDirectory() as temporary:
            state = Path(temporary) / "state"
            # Patched where it is used, not where it is defined: ticket_lifecycle imported
            # the name, so rebinding it in file_lock would have no effect.
            with mock.patch(
                "autopilot.ticket_lifecycle.acquire_file_lock",
                side_effect=OSError("held"),
            ):
                with self.assertRaises(LifecycleError) as raised:
                    with _folder_lock(state):
                        pass

        self.assertIn("locked", str(raised.exception))
        self.assertIn(str(state), str(raised.exception))

    def test_the_lock_is_released_when_the_body_raises(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state = Path(temporary) / "state"
            with self.assertRaisesRegex(RuntimeError, "boom"):
                with _folder_lock(state):
                    raise RuntimeError("boom")
            # A leaked lock would make the next acquisition hang or fail.
            with _folder_lock(state):
                pass


class CommandResolutionTests(unittest.TestCase):
    def test_the_executable_is_resolved_through_pathext(self) -> None:
        # On Windows the provider CLI is `az.cmd` and CreateProcess does not apply PATHEXT,
        # so the bare name fails with [WinError 2] even when it is on PATH.
        with tempfile.TemporaryDirectory() as temporary:
            with mock.patch(
                "autopilot.git_ops.shutil.which", return_value="C:\\tools\\az.CMD"
            ):
                with mock.patch("autopilot.git_ops.subprocess.run") as invoked:
                    invoked.return_value = mock.Mock(
                        stdout=b"", stderr=b"", returncode=0
                    )
                    SubprocessCommandRunner().run(
                        ["az", "repos", "pr", "list"], cwd=Path(temporary)
                    )

        self.assertEqual(
            ["C:\\tools\\az.CMD", "repos", "pr", "list"], invoked.call_args.args[0]
        )

    def test_an_unresolvable_command_is_passed_through_unchanged(self) -> None:
        # Falling back preserves the original FileNotFoundError, which names the command
        # the caller actually asked for.
        with tempfile.TemporaryDirectory() as temporary:
            with mock.patch("autopilot.git_ops.shutil.which", return_value=None):
                with mock.patch("autopilot.git_ops.subprocess.run") as invoked:
                    invoked.return_value = mock.Mock(
                        stdout=b"", stderr=b"", returncode=0
                    )
                    SubprocessCommandRunner().run(
                        ["definitely-not-installed"], cwd=Path(temporary)
                    )

        self.assertEqual(["definitely-not-installed"], invoked.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
