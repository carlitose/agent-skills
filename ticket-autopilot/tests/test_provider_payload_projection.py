from __future__ import annotations

import ast
import json
import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from autopilot.git_ops import SubprocessCommandRunner  # noqa: E402
from autopilot.providers import (  # noqa: E402
    AZURE_DESCRIPTION_TERMINATOR,
    AZURE_PR_FIELDS,
    CREATE_OR_UPDATE_PR,
    ProviderExecutor,
    azure_pr_query,
    detect_provider,
)


PROVIDERS_SOURCE = SCRIPTS / "autopilot" / "providers.py"

# The payload shape that broke delivery of WCF-01. The undecodable byte is written as a
# byte, not as a character, so this test does not depend on the encoding of its own file.
# 0xf3 is "o" acute in cp1252, which is what `az` emits for `.repository.project.description`
# on a Windows console whose codepage is not UTF-8.
FULL_PAYLOAD = (
    b'{"pullRequestId": 24038, "description": "## Summary", '
    b'"repository": {"project": '
    b'{"description": "implementan la l\xf3gica de CORE"}}}'
)
PROJECTED_PAYLOAD = b'{"pullRequestId": 24038, "description": "## Summary"}'


def _fields_read_from(function_name: str) -> set[str]:
    """Every `document.get("X")` name the named function reads, found in the source.

    Read from the AST rather than declared by hand: a drift test that restates the field
    list is a second copy of the thing it is meant to guard.
    """

    tree = ast.parse(PROVIDERS_SOURCE.read_text(encoding="utf-8"))
    target = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            target = node
            break
    if target is None:  # pragma: no cover - guards the test itself
        raise AssertionError(f"{function_name} not found in {PROVIDERS_SOURCE}")

    found: set[str] = set()
    for node in ast.walk(target):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr != "get":
            continue
        if not isinstance(func.value, ast.Name) or func.value.id != "document":
            continue
        if node.args and isinstance(node.args[0], ast.Constant):
            if isinstance(node.args[0].value, str):
                found.add(node.args[0].value)
    return found


class ProjectionTracksTheReadersTests(unittest.TestCase):
    def test_every_field_the_readers_consume_is_declared(self) -> None:
        # The failure this guards: someone adds `document.get("mergeStatus")` to a reader,
        # the projection does not ask for it, and the field arrives `None` instead of
        # raising. Silent wrong answer, which is the mode this whole area exists to avoid.
        declared = {field.partition(".")[0] for field in AZURE_PR_FIELDS}
        consumed = _fields_read_from("_azure_state_receipt") | _fields_read_from(
            "_azure_state"
        )

        self.assertTrue(consumed, "the AST walk found no fields, so it proves nothing")
        self.assertEqual(
            set(),
            consumed - declared,
            "these fields are read but not projected, so they would arrive None",
        )

    def test_the_readers_find_every_declared_field(self) -> None:
        # The opposite drift: a field kept in the projection that nobody reads any more.
        # Not a correctness bug, but it is how the declaration rots into a wish list.
        declared = {field.partition(".")[0] for field in AZURE_PR_FIELDS}
        consumed = _fields_read_from("_azure_state_receipt") | _fields_read_from(
            "_azure_state"
        )

        self.assertEqual(set(), declared - consumed)

    def test_query_rebuilds_the_nested_commit_shape(self) -> None:
        # The readers do `document.get("lastMergeCommit").get("commitId")`, so a flattened
        # key would type-check and then read `None` for every merge commit.
        query = azure_pr_query()

        self.assertIn(
            "lastMergeCommit:{commitId:lastMergeCommit.commitId}", query
        )
        self.assertIn(
            "lastMergeSourceCommit:{commitId:lastMergeSourceCommit.commitId}", query
        )
        self.assertTrue(query.startswith("{") and query.endswith("}"))

    def test_array_form_wraps_the_same_projection(self) -> None:
        self.assertEqual(f"[].{azure_pr_query()}", azure_pr_query(many=True))


class UndecodableProviderByteTests(unittest.TestCase):
    """Reproduce the production failure through the real decode path, not a stand-in."""

    def _emit(self, payload: bytes) -> list[str]:
        return [
            sys.executable,
            "-c",
            "import sys; sys.stdout.buffer.write(" + repr(payload) + ")",
        ]

    def test_full_payload_dies_where_the_runner_decodes_it(self) -> None:
        # git_ops.py:89 `return raw.decode("utf-8")`. Strict by deliberate choice (WT-02):
        # stdout feeds digests and `assert_cleanup_safe`. This test does not argue with
        # that; it shows what the full payload does to it.
        with self.assertRaises(UnicodeDecodeError):
            SubprocessCommandRunner().run(self._emit(FULL_PAYLOAD), cwd=Path("."))

    def test_projected_payload_survives_the_same_path(self) -> None:
        result = SubprocessCommandRunner().run(
            self._emit(PROJECTED_PAYLOAD), cwd=Path(".")
        )

        self.assertEqual(0, result.returncode)
        self.assertEqual(24038, json.loads(result.stdout)["pullRequestId"])


class RecordingAzureRunner:
    """Records the argument vectors and answers with a projected-shaped document."""

    def __init__(self, *, existing: bool) -> None:
        self.commands: list[list[str]] = []
        self.existing = existing
        self.pr = {
            "pullRequestId": 91,
            "url": "https://dev.azure.example/pr/91",
            "status": "active",
            "sourceRefName": "refs/heads/ticket/pub-01",
            "targetRefName": "refs/heads/main",
            "description": "stale body",
            "lastMergeSourceCommit": {"commitId": "head-sha-pub01"},
            # What the projection returns when the PR has no merge commit: the parent is
            # present with a null child, where the full document omitted the parent.
            "lastMergeCommit": {"commitId": None},
        }

    def run(self, command: list[str], *, cwd: Path) -> object:
        from autopilot.git_ops import CommandResult

        self.commands.append(command)
        head = command[:4]
        if head == ["az", "repos", "pr", "list"]:
            return CommandResult(
                json.dumps([self.pr] if self.existing else []), "", 0
            )
        if head in (
            ["az", "repos", "pr", "update"],
            ["az", "repos", "pr", "create"],
        ):
            start = command.index("--description") + 1
            end = command.index(AZURE_DESCRIPTION_TERMINATOR, start)
            self.pr["description"] = "\n".join(command[start:end])
            return CommandResult(json.dumps(self.pr), "", 0)
        if head == ["az", "repos", "pr", "show"]:
            return CommandResult(json.dumps(self.pr), "", 0)
        return CommandResult("", f"unexpected: {command}", 1)

    def sent(self, verb: str) -> list[str]:
        for command in self.commands:
            if command[:4] == ["az", "repos", "pr", verb]:
                return command
        raise AssertionError(f"pr {verb} was never called: {self.commands}")


def _deliver(runner: RecordingAzureRunner) -> dict:
    executor = ProviderExecutor(
        detect_provider("", override="azure-devops"),
        cwd=Path("."),
        runner=runner,
    )
    return executor.execute(
        CREATE_OR_UPDATE_PR,
        branch="ticket/pub-01",
        base="main",
        head_sha="head-sha-pub01",
        title="PUB-01",
        body_artifact="## Summary\n\nA line.\n",
    )


class CallSitesAskForLessTests(unittest.TestCase):
    def test_pr_show_projects_the_document(self) -> None:
        runner = RecordingAzureRunner(existing=True)
        _deliver(runner)
        sent = runner.sent("show")

        self.assertIn("--query", sent)
        self.assertEqual(azure_pr_query(), sent[sent.index("--query") + 1])

    def test_pr_list_projects_the_array(self) -> None:
        runner = RecordingAzureRunner(existing=True)
        _deliver(runner)
        sent = runner.sent("list")

        self.assertEqual(azure_pr_query(many=True), sent[sent.index("--query") + 1])

    def test_pr_update_asks_for_no_payload_at_all(self) -> None:
        # This result is discarded, so the cheapest safe payload is none. It is also the
        # exact call site that raised in production.
        runner = RecordingAzureRunner(existing=True)
        _deliver(runner)
        sent = runner.sent("update")

        self.assertEqual("none", sent[sent.index("--output") + 1])

    def test_pr_create_projects_the_document(self) -> None:
        runner = RecordingAzureRunner(existing=False)
        _deliver(runner)
        sent = runner.sent("create")

        self.assertEqual(azure_pr_query(), sent[sent.index("--query") + 1])
        self.assertEqual("json", sent[sent.index("--output") + 1])

    def test_the_description_terminator_still_follows_the_description(self) -> None:
        # `AZURE_DESCRIPTION_TERMINATOR` is how the test double and any reader find the
        # end of the description values. Inserting `--query` after `--description` would
        # break that quietly, so both call sites keep `--output` immediately after.
        for existing, verb in ((True, "update"), (False, "create")):
            with self.subTest(verb):
                runner = RecordingAzureRunner(existing=existing)
                _deliver(runner)
                sent = runner.sent(verb)
                start = sent.index("--description") + 1
                end = sent.index(AZURE_DESCRIPTION_TERMINATOR, start)

                self.assertEqual("## Summary\n\nA line.\n", "\n".join(sent[start:end]))
                self.assertEqual(AZURE_DESCRIPTION_TERMINATOR, sent[end])

    def test_body_still_arrives_verbatim_through_the_projection(self) -> None:
        body = "## Summary\n\nA line.\n"
        runner = RecordingAzureRunner(existing=True)

        receipt = _deliver(runner)

        self.assertEqual(body, receipt["body"])
        self.assertEqual(body, runner.pr["description"])

    def test_null_merge_commit_from_the_projection_is_accepted(self) -> None:
        # The projection turns an absent `lastMergeCommit` into `{"commitId": None}`.
        # The reader must reach the same `None` it reached before, not raise on the shape.
        runner = RecordingAzureRunner(existing=True)

        receipt = _deliver(runner)

        self.assertIsNone(receipt["merge_commit_sha"])
        self.assertEqual("head-sha-pub01", receipt["head_sha"])


if __name__ == "__main__":
    unittest.main()
