from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from autopilot.providers import (  # noqa: E402
    AZURE_DESCRIPTION_TERMINATOR,
    CREATE_OR_UPDATE_PR,
    ProviderError,
    ProviderExecutor,
    _azure_description_arguments,
    detect_provider,
)


def stored_by_azure(body: str) -> str:
    """What Azure DevOps stores: the argument vector joined with newlines.

    Documented as "Each value sent to this arg will be a new line" by
    `az repos pr create --help` (observed on az 2.85.0).
    """

    return "\n".join(_azure_description_arguments(body))


class AzureDescriptionRoundTripTests(unittest.TestCase):
    def test_body_survives_the_argument_vector_unchanged(self) -> None:
        bodies = {
            "plain": "## Summary\nline two",
            "trailing newline": "## Summary\nline two\n",
            "blank line": "## Summary\n\nline three",
            "crlf": "## Summary\r\nline two",
            "line separator U+2028": "## Summary\u2028line two",
            "form feed": "## Summary\fline two",
            "vertical tab": "## Summary\vline two",
            "next line U+0085": "## Summary\x85line two",
            "empty": "",
            "single newline": "\n",
            "markdown bullets": "- first item\n- second item",
            "fenced block": "```\ncode --here\n```\n",
        }
        for name, body in bodies.items():
            with self.subTest(name):
                self.assertEqual(body, stored_by_azure(body))

    def test_trailing_newline_is_the_regression_splitlines_caused(self) -> None:
        # The delivery gate that motivated this: finalizer compares the readback to the
        # validated body with `!=`, and splitlines() made them differ by one character.
        body = "## Summary\nline two\n"
        self.assertEqual(body, stored_by_azure(body))
        self.assertNotEqual(body, "\n".join(body.splitlines()))

    def test_a_line_parsed_as_an_option_is_refused_with_its_position(self) -> None:
        # Verified against az 2.85.0: `--description "## S" "---" "t"` answers
        # `ERROR: unrecognized arguments: --- t` and never reaches the service.
        body = "## Summary\n---\nline three"
        with self.assertRaises(ProviderError) as raised:
            _azure_description_arguments(body)
        message = str(raised.exception)
        self.assertIn("line 2", message)
        self.assertIn("'---'", message)

    def test_lines_that_only_look_dangerous_are_delivered(self) -> None:
        # argparse treats a token containing a space, a lone `-`, or a negative number as
        # a value, so these must not be refused.
        for body in ("- a bullet", "-", "-42", "-3.5", "text -- with dashes"):
            with self.subTest(body):
                self.assertEqual(body, stored_by_azure(body))


class ExistingAzurePrRunner:
    """Models `az` for an already-open PR, so delivery takes the `pr update` branch."""

    def __init__(self, head_sha: str) -> None:
        self.head_sha = head_sha
        self.commands: list[list[str]] = []
        self.pr = {
            "pullRequestId": 91,
            "url": "https://dev.azure.example/pr/91",
            "status": "active",
            "sourceRefName": "refs/heads/ticket/wt-01",
            "targetRefName": "refs/heads/main",
            "description": "stale body",
            "lastMergeSourceCommit": {"commitId": head_sha},
            "reviewers": [],
        }

    def run(self, command: list[str], *, cwd: Path) -> object:
        from autopilot.git_ops import CommandResult

        self.commands.append(command)
        if command[:4] == ["az", "repos", "pr", "list"]:
            return CommandResult(json.dumps([self.pr]), "", 0)
        if command[:4] == ["az", "repos", "pr", "update"]:
            start = command.index("--description") + 1
            end = command.index(AZURE_DESCRIPTION_TERMINATOR, start)
            self.pr["description"] = "\n".join(command[start:end])
            return CommandResult(json.dumps(self.pr), "", 0)
        if command[:4] == ["az", "repos", "pr", "show"]:
            return CommandResult(json.dumps(self.pr), "", 0)
        return CommandResult("", f"unexpected: {command}", 1)


class AzureUpdatePathTests(unittest.TestCase):
    def test_update_path_publishes_the_body_verbatim(self) -> None:
        # The create path is covered by test_cli; this crosses the *other* call site,
        # which otherwise has no test and could drift from it unnoticed.
        body = "## Summary\n\nA line.\n\n```\nfenced\n```\n"
        runner = ExistingAzurePrRunner("head-sha-wt01")
        executor = ProviderExecutor(
            detect_provider("", override="azure-devops"),
            cwd=Path("."),
            runner=runner,
        )

        receipt = executor.execute(
            CREATE_OR_UPDATE_PR,
            branch="ticket/wt-01",
            base="main",
            head_sha="head-sha-wt01",
            title="WT-01",
            body_artifact=body,
        )

        self.assertEqual(body, receipt["body"])
        self.assertEqual(body, runner.pr["description"])
        self.assertTrue(
            any(c[:4] == ["az", "repos", "pr", "update"] for c in runner.commands),
            "the update call site was never exercised",
        )


if __name__ == "__main__":
    unittest.main()
