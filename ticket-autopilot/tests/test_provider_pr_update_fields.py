"""Updating an existing GitHub pull request sends only what actually differs.

Patching base, title and body together made GitHub answer 422 on a merged pull request
while it had already stored the new body, so a real effect was reported as a failure.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from autopilot.git_ops import CommandResult  # noqa: E402
from autopilot.providers import (  # noqa: E402
    CREATE_OR_UPDATE_PR,
    GitHubProvider,
    ProviderError,
    ProviderExecutor,
)


class Runner:
    """Models `gh` for one pull request that already exists."""

    def __init__(self, **overrides: object) -> None:
        self.pr: dict[str, object] = {
            "number": 27,
            "url": "https://github.example/pr/27",
            "state": "OPEN",
            "mergedAt": None,
            "mergeCommit": None,
            "headRefName": "ticket/27",
            "headRefOid": "b658c9c3c7385ce45cd325ce41a41404ec05eac5",
            "baseRefName": "main",
            "title": "stored title",
            "body": "stored body",
            "reviewDecision": "",
            "reviews": [],
            "mergeable": "MERGEABLE",
            "mergeStateStatus": "CLEAN",
        }
        self.pr.update(overrides)
        self.commands: list[list[str]] = []
        self.patches: list[dict[str, str]] = []
        self.patch_returncode = 0
        self.patch_applies: tuple[str, ...] = ()

    def fields(self, command: list[str]) -> dict[str, str]:
        return dict(
            command[index + 1].split("=", 1)
            for index, value in enumerate(command)
            if value == "--raw-field"
        )

    def run(self, command: list[str], *, cwd: Path) -> CommandResult:
        self.commands.append(command)
        if command[:3] == ["gh", "pr", "list"]:
            return CommandResult(json.dumps([{"number": self.pr["number"]}]), "", 0)
        if command[:3] == ["gh", "pr", "view"]:
            return CommandResult(json.dumps(self.pr), "", 0)
        if command[:2] == ["gh", "api"] and "PATCH" in command:
            fields = self.fields(command)
            self.patches.append(fields)
            stored = {"base": "baseRefName", "title": "title", "body": "body"}
            applied = fields if self.patch_returncode == 0 else {
                name: value for name, value in fields.items() if name in self.patch_applies
            }
            for name, value in applied.items():
                self.pr[stored[name]] = value
            if self.patch_returncode:
                return CommandResult("", "gh: Validation Failed (HTTP 422)", self.patch_returncode)
            return CommandResult("{}", "", 0)
        raise AssertionError(f"unexpected command: {command}")

    def execute(self, **overrides: object) -> dict[str, object]:
        executor = ProviderExecutor(GitHubProvider(), cwd=Path.cwd(), runner=self)
        parameters: dict[str, object] = {
            "branch": "ticket/27",
            "base": "main",
            "head_sha": self.pr["headRefOid"],
            "title": "stored title",
            "body_artifact": "stored body",
        }
        parameters.update(overrides)
        return executor.execute(CREATE_OR_UPDATE_PR, **parameters)


class UpdateSendsOnlyChangedFieldsTests(unittest.TestCase):
    def test_an_unchanged_pull_request_is_not_patched_at_all(self) -> None:
        runner = Runner()
        receipt = runner.execute()
        self.assertEqual(runner.patches, [])
        self.assertEqual(receipt["base"], "main")

    def test_only_the_new_body_is_sent(self) -> None:
        runner = Runner()
        runner.execute(body_artifact="fresh body")
        self.assertEqual(runner.patches, [{"body": "fresh body"}])
        self.assertEqual(runner.pr["body"], "fresh body")

    def test_a_merged_pull_request_keeps_its_base_out_of_the_request(self) -> None:
        # The case that produced HTTP 422 with the body stored anyway.
        runner = Runner(state="MERGED", mergedAt="2026-09-01T00:00:00Z")
        runner.execute(body_artifact="postsync body")
        self.assertEqual(runner.patches, [{"body": "postsync body"}])

    def test_moving_the_base_of_a_merged_pull_request_is_refused_before_the_request(self) -> None:
        runner = Runner(state="MERGED", mergedAt="2026-09-01T00:00:00Z")
        with self.assertRaises(ProviderError) as raised:
            runner.execute(base="release")
        self.assertIn("merged", str(raised.exception))
        self.assertEqual(runner.patches, [])

    def test_a_changed_base_on_an_open_pull_request_is_still_sent(self) -> None:
        runner = Runner()
        receipt = runner.execute(base="release", body_artifact="fresh body")
        self.assertEqual(runner.patches, [{"base": "release", "body": "fresh body"}])
        self.assertEqual(receipt["base"], "release")

    def test_a_failed_request_reports_what_it_already_stored(self) -> None:
        runner = Runner()
        runner.patch_returncode = 1
        runner.patch_applies = ("body",)
        with self.assertRaises(ProviderError) as raised:
            runner.execute(title="fresh title", body_artifact="fresh body")
        message = str(raised.exception)
        self.assertIn("422", message)
        self.assertIn("fields already applied on pull request 27: body", message)
        self.assertEqual(len(runner.patches), 1, "a failure is never retried")


if __name__ == "__main__":  # pragma: no cover - convenience
    unittest.main()
