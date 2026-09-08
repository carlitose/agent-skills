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
from autopilot.tracked_status_delivery import (  # noqa: E402
    TrackedStatusDeliveryError,
    _provider_body,
    _validate_pr,
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


def status_document(
    from_disposition: str, to_disposition: str
) -> dict[str, object]:
    return {
        "transaction_id": "f57e59cc0f82db807e0e69cf066aa03aacbe14bb",
        "request": {
            "ticket_id": "16",
            "artifact_id": "artifact:langfuse-ocr-16-decidir-que-hace-paginas",
            "from_disposition": from_disposition,
            "to_disposition": to_disposition,
            "actor": "Carlo Giuseppe Sergi",
            "authority_ref": "session record 2026-09-08",
            "reason": "the approver is away",
        },
    }


def discarded_by_a_cp1252_console(body: str) -> str:
    """What a CLI prints when its console encoding cannot represent a character.

    Observed verbatim from `az repos pr show` on Windows:
    `WARNING: Unable to encode the output with cp1252 encoding. Unsupported
    characters are discarded.` `knack` re-encodes with `ascii`/`ignore`, so the
    character does not come back at all.
    """

    return body.encode("ascii", "ignore").decode("ascii")


class StatusChangeBodyIsAsciiTests(unittest.TestCase):
    """The body is compared byte for byte against the readback, so it must survive it.

    A single U+2192 arrow in this body made every `status-change-transaction` on Azure
    DevOps under Windows die with `provider PR readback is contradictory` *after* the PR
    was already created. The existing round-trip tests above could not catch it: their
    fake runner returns the JSON verbatim, so nothing was ever discarded.
    """

    transitions = (
        ("open", "on-hold"),
        ("open", "canceled"),
        ("on-hold", "open"),
        ("on-hold", "canceled"),
        ("canceled", "open"),
        ("completed", "open"),
    )

    def test_every_transition_body_is_pure_ascii(self) -> None:
        for source, target in self.transitions:
            with self.subTest(f"{source} -> {target}"):
                body = _provider_body(status_document(source, target), "head-sha-16")
                offenders = sorted({char for char in body if ord(char) > 127})
                self.assertEqual(
                    [],
                    offenders,
                    f"non-ASCII in the provider body: {offenders}",
                )

    def test_the_body_survives_a_lossy_console_unchanged(self) -> None:
        # This is the assertion the defect needed: send the body through the same loss the
        # CLI applies, and require it to come back identical.
        for source, target in self.transitions:
            with self.subTest(f"{source} -> {target}"):
                body = _provider_body(status_document(source, target), "head-sha-16")
                self.assertEqual(body, discarded_by_a_cp1252_console(body))

    def test_the_disposition_arrow_is_written_in_ascii(self) -> None:
        body = _provider_body(status_document("open", "on-hold"), "head-sha-16")
        self.assertIn("- Disposition: `open` -> `on-hold`", body)

    def test_a_non_ascii_body_would_not_survive_that_console(self) -> None:
        # Proves the check has teeth rather than passing for a trivial reason: the exact
        # old text loses its arrow on the same channel.
        old = "- Disposition: `open` \u2192 `on-hold`\n"
        self.assertNotEqual(old, discarded_by_a_cp1252_console(old))
        self.assertEqual(
            "- Disposition: `open`  `on-hold`\n",
            discarded_by_a_cp1252_console(old),
        )


class StatusPrReadbackStaysExactTests(unittest.TestCase):
    """The byte-for-byte comparison is the guarantee, and it is not relaxed here."""

    def receipt(self, **overrides: object) -> dict[str, object]:
        receipt = {
            "schema": 1,
            "provider": "azure-devops",
            "operation": CREATE_OR_UPDATE_PR,
            "evidence_class": "live",
            "observed": True,
            "branch": "ticket-autopilot/status-change/16",
            "base": "main",
            "head_sha": "head-sha-16",
            "body": "- Disposition: `open` -> `on-hold`\n",
            "state": "open",
            "pr_id": "24030",
        }
        receipt.update(overrides)
        return receipt

    def arguments(self) -> dict[str, object]:
        return {
            "provider": "azure-devops",
            "operation": CREATE_OR_UPDATE_PR,
            "branch": "ticket-autopilot/status-change/16",
            "base": "main",
            "head_sha": "head-sha-16",
            "body": "- Disposition: `open` -> `on-hold`\n",
        }

    def test_an_exact_readback_is_accepted(self) -> None:
        _validate_pr(self.receipt(), **self.arguments())

    def test_a_body_off_by_one_character_is_still_contradictory(self) -> None:
        for name, body in {
            "one character dropped": "- Disposition: `open` - `on-hold`\n",
            "trailing newline lost": "- Disposition: `open` -> `on-hold`",
            "arrow mutilated by the console": "- Disposition: `open`  `on-hold`\n",
        }.items():
            with self.subTest(name):
                with self.assertRaises(TrackedStatusDeliveryError) as raised:
                    _validate_pr(self.receipt(body=body), **self.arguments())
                self.assertIn("contradictory", str(raised.exception))


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
