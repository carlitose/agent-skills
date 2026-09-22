"""Delivering a PR body through a Windows batch wrapper without cmd.exe reading it."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "ticket-autopilot" / "scripts" / "ticket-autopilot.py"
sys.path.insert(0, str(CLI.parent))

from autopilot.git_ops import (  # type: ignore[import-not-found]
    CommandResult,
    SubprocessCommandRunner,
    resolves_to_batch_wrapper,
)
from autopilot.providers import (  # type: ignore[import-not-found]
    AZURE_DESCRIPTION_MAX_CHARS,
    CREATE_OR_UPDATE_PR,
    AzureDevOpsProvider,
    ProviderError,
    ProviderExecutor,
    _azure_description_argv,
    _render_command,
)

# One separator row of a Markdown table and one link line: no spaces, so `list2cmdline`
# leaves them bare and `cmd.exe` reads a pipe and a redirection.
TABLE_ROW = "|---|---|"
REDIRECTING_LINE = "see>stray.txt"
BODY = f"## Summary\n\n{TABLE_ROW}\n{REDIRECTING_LINE}\nplain text\n"


class RecordingRunner:
    """A runner that records argv and answers whatever the test needs."""

    def __init__(self, results):
        self.commands: list[list[str]] = []
        self._results = list(results)

    def run(self, command, *, cwd):
        self.commands.append(list(command))
        return self._results.pop(0)


def azure_provider() -> AzureDevOpsProvider:
    return AzureDevOpsProvider()


class AzureDescriptionArgvTests(unittest.TestCase):
    def test_batch_wrapper_sends_one_file_reference_holding_the_body(self) -> None:
        with _azure_description_argv(BODY, batch_wrapper=True) as values:
            self.assertEqual(len(values), 1)
            reference = values[0]
            self.assertTrue(reference.startswith("@"))
            path = Path(reference[1:])
            self.assertTrue(path.is_file())
            self.assertEqual(path.read_bytes().decode("utf-8"), BODY)
        self.assertFalse(path.exists(), "the temporary body is removed with the call")

    def test_batch_wrapper_argv_carries_no_shell_character(self) -> None:
        with _azure_description_argv(BODY, batch_wrapper=True) as values:
            for value in values:
                self.assertFalse(
                    set(value) & set("\n|<>&^"),
                    f"{value!r} still reaches cmd.exe with a shell character",
                )

    def test_temporary_body_is_not_written_inside_the_worktree(self) -> None:
        with (
            tempfile.TemporaryDirectory(prefix="tap-worktree-") as worktree,
            _azure_description_argv(BODY, batch_wrapper=True) as values,
        ):
            path = Path(values[0][1:])
            self.assertFalse(
                path.is_relative_to(Path(worktree)),
                "a body written into the worktree would dirty the candidate",
            )
            self.assertEqual(sorted(Path(worktree).iterdir()), [])

    def test_without_a_batch_wrapper_the_per_line_vector_is_unchanged(self) -> None:
        with _azure_description_argv(BODY, batch_wrapper=False) as values:
            self.assertEqual(values, BODY.split("\n"))

    def test_a_body_over_the_limit_is_refused_before_anything_runs(self) -> None:
        body = "x" * (AZURE_DESCRIPTION_MAX_CHARS + 1)
        for batch_wrapper in (False, True):
            with self.subTest(batch_wrapper=batch_wrapper):
                with (
                    self.assertRaises(ProviderError) as raised,
                    _azure_description_argv(body, batch_wrapper=batch_wrapper),
                ):
                    pass
                message = str(raised.exception)
                self.assertIn(str(AZURE_DESCRIPTION_MAX_CHARS), message)
                self.assertIn(str(len(body)), message)

    def test_a_body_at_the_limit_is_accepted(self) -> None:
        body = "x" * AZURE_DESCRIPTION_MAX_CHARS
        with _azure_description_argv(body, batch_wrapper=False) as values:
            self.assertEqual(values, [body])


class RenderedCommandTests(unittest.TestCase):
    def test_a_long_argument_is_replaced_by_its_length(self) -> None:
        rendered = _render_command(["az", "repos", "pr", "update", "--description", "b" * 3000])
        self.assertNotIn("bbb", rendered)
        self.assertIn("<3000 characters>", rendered)
        self.assertIn("az repos pr update --description", rendered)

    def test_the_whole_rendering_stays_bounded(self) -> None:
        rendered = _render_command(["az", *[f"value-{index}" for index in range(200)]])
        self.assertLessEqual(len(rendered), 460)
        self.assertIn("rendering truncated", rendered)

    def test_a_failing_command_reports_the_producer_detail_without_the_body(self) -> None:
        runner = RecordingRunner([CommandResult(stdout="", stderr="TF401019: nope", returncode=1)])
        executor = ProviderExecutor(azure_provider(), cwd=Path.cwd(), runner=runner)
        with self.assertRaises(ProviderError) as raised:
            executor._run(["az", "repos", "pr", "update", "--description", BODY * 40])
        message = str(raised.exception)
        self.assertIn("TF401019: nope", message)
        self.assertNotIn(TABLE_ROW, message)


class AzureCreateOrUpdateTests(unittest.TestCase):
    def executor(self, runner, *, batch_wrapper):
        executor = ProviderExecutor(azure_provider(), cwd=Path.cwd(), runner=runner)
        executor._azure_uses_batch_wrapper = lambda: batch_wrapper  # type: ignore[method-assign]
        return executor

    def parameters(self):
        return {
            "branch": "topic",
            "base": "main",
            "title": "one title",
            "body_artifact": BODY,
            "head_sha": "a" * 40,
        }

    def view(self):
        return {
            "pullRequestId": 7,
            "sourceRefName": "refs/heads/topic",
            "targetRefName": "refs/heads/main",
            "lastMergeSourceCommit": {"commitId": "a" * 40},
            "status": "active",
            "mergeStatus": "succeeded",
            "isDraft": False,
        }

    def test_creation_through_a_batch_wrapper_keeps_the_body_off_the_command_line(self) -> None:
        runner = RecordingRunner([
            CommandResult(stdout="[]", stderr="", returncode=0),
            CommandResult(stdout='{"pullRequestId": 7}', stderr="", returncode=0),
            CommandResult(stdout=repr(self.view()).replace("'", '"'), stderr="", returncode=0),
        ])
        executor = self.executor(runner, batch_wrapper=True)
        with mock.patch.object(ProviderExecutor, "_azure_state_receipt", lambda self, operation, view: {
            "branch": "topic", "base": "main", "head_sha": "a" * 40,
        }), mock.patch.object(ProviderExecutor, "_azure_view", lambda self, pr_id: self):
            executor.execute(CREATE_OR_UPDATE_PR, **self.parameters())
        create = runner.commands[1]
        index = create.index("--description")
        self.assertTrue(create[index + 1].startswith("@"))
        self.assertEqual(create[index + 2], "--output")
        for argument in create:
            self.assertFalse(set(argument) & set("\n|<>&^"), argument)

    def test_creation_without_a_batch_wrapper_still_sends_one_value_per_line(self) -> None:
        runner = RecordingRunner([
            CommandResult(stdout="[]", stderr="", returncode=0),
            CommandResult(stdout='{"pullRequestId": 7}', stderr="", returncode=0),
        ])
        executor = self.executor(runner, batch_wrapper=False)
        with mock.patch.object(ProviderExecutor, "_azure_state_receipt", lambda self, operation, view: {
            "branch": "topic", "base": "main", "head_sha": "a" * 40,
        }), mock.patch.object(ProviderExecutor, "_azure_view", lambda self, pr_id: self):
            executor.execute(CREATE_OR_UPDATE_PR, **self.parameters())
        create = runner.commands[1]
        index = create.index("--description")
        self.assertEqual(create[index + 1:index + 1 + len(BODY.split("\n"))], BODY.split("\n"))


@unittest.skipUnless(os.name == "nt", "cmd.exe reparses only on Windows")
class WindowsBatchWrapperTests(unittest.TestCase):
    """What a batch wrapper actually receives on this host."""

    def wrapper(self, home: Path) -> Path:
        script = home / "fakeaz.cmd"
        # `shift` moves `%0` too, so the destination is captured before the loop:
        # after the first shift `%~dp0` would name the first argument, not this script.
        script.write_text(
            "@echo off\r\nset \"SEEN=%~dp0seen.txt\"\r\n:loop\r\n"
            "if \"%~1\"==\"\" goto end\r\necho %~1>> \"%SEEN%\"\r\n"
            "shift\r\ngoto loop\r\n:end\r\n",
            encoding="ascii",
        )
        return script

    def test_a_table_row_on_the_command_line_breaks_the_call(self) -> None:
        with tempfile.TemporaryDirectory(prefix="tap-batch-") as home:
            script = self.wrapper(Path(home))
            worktree = Path(home) / "work"
            worktree.mkdir()
            result = SubprocessCommandRunner().run(
                [str(script), "--description", TABLE_ROW], cwd=worktree
            )
            self.assertNotEqual(result.returncode, 0, "cmd.exe read the row as a pipe")

    def test_a_redirecting_line_writes_a_file_into_the_working_directory(self) -> None:
        with tempfile.TemporaryDirectory(prefix="tap-batch-") as home:
            script = self.wrapper(Path(home))
            worktree = Path(home) / "work"
            worktree.mkdir()
            SubprocessCommandRunner().run(
                [str(script), "--description", REDIRECTING_LINE], cwd=worktree
            )
            self.assertTrue(
                (worktree / "stray.txt").exists(),
                "this is the stray file the redirection leaves in the worktree",
            )

    def test_the_file_reference_survives_the_same_wrapper_untouched(self) -> None:
        with tempfile.TemporaryDirectory(prefix="tap-batch-") as home:
            script = self.wrapper(Path(home))
            worktree = Path(home) / "work"
            worktree.mkdir()
            with _azure_description_argv(BODY, batch_wrapper=True) as values:
                result = SubprocessCommandRunner().run(
                    [str(script), "--description", *values], cwd=worktree
                )
                seen = (Path(home) / "seen.txt").read_text(encoding="utf-8").splitlines()
            self.assertEqual(result.returncode, 0)
            self.assertEqual(seen, ["--description", values[0]])
            self.assertEqual(sorted(path.name for path in worktree.iterdir()), [])

    def test_the_resolver_reports_this_host_wrapper(self) -> None:
        self.assertFalse(resolves_to_batch_wrapper(""))
        self.assertIsInstance(resolves_to_batch_wrapper("az"), bool)


if __name__ == "__main__":
    unittest.main()
