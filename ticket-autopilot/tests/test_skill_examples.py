"""Two failures of the q2 autopilot benchmark run came from the skill's own examples.

At turn 63 the model read "`resume --events` accepts `leaf-result`" and ran exactly that;
the CLI opened a file named `leaf-result` and reported `[Errno 2] No such file or
directory`. At turn 137 it ran the documented `python3` on Windows, where that name is
often a Microsoft Store stub that prints "Python was not found" (see
`docs/specs/autopilot-protocol-friction-wayfinder.md`).

These tests read every runner command example in `ticket-autopilot/SKILL.md` and its
references the way a reader would, and hold them to three things: the interpreter is the
one variable the skill defines, every example parses against the real parser, and every
command the skill names answers `--help` when actually executed. A separate test starts a
real run and feeds it the documented `--events` file shape.
"""
from __future__ import annotations

import contextlib
import io
import json
import re
import shlex
import subprocess
import sys
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path

if __package__:
    from .git_test_support import GitIsolatedTestCase
else:
    from git_test_support import GitIsolatedTestCase

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
CLI = SCRIPTS / "ticket-autopilot.py"
sys.path.insert(0, str(SCRIPTS))

from autopilot.cli import build_parser

INTERPRETER = "$TICKET_AUTOPILOT_PYTHON"
ROOT_PREFIX = "$TICKET_AUTOPILOT_ROOT/scripts/"
HEX40 = "0" * 40
HEX64 = "0" * 64
PLACEHOLDERS = {
    "<repository>": ".",
    "<run>": "run-1",
    "<gate-id>": "G-1",
    "<ticket.md>": "ticket.md",
    "<ticket-or-folder>": "ticket.md",
    "<envelope.json>": "envelope.json",
    "<body.md>": "body.md",
    "<candidate-tree-oid>": HEX40,
    "<reported-digest>": HEX64,
    "<exact-file-sha256>": HEX64,
    "<registered-exact-source>": "source",
}


@dataclass(frozen=True)
class Example:
    source: str
    line: int
    text: str
    argv: tuple[str, ...]

    def __str__(self) -> str:
        return f"{self.source}:{self.line}: {self.text}"


def skill_documents() -> list[Path]:
    return [SKILL_ROOT / "SKILL.md", *sorted((SKILL_ROOT / "references").glob("*.md"))]


def runner_examples() -> list[Example]:
    """Every command in a fenced block that invokes a runner script, continuations joined."""
    examples: list[Example] = []
    for document in skill_documents():
        in_block, buffer, start = False, "", 0
        for number, line in enumerate(document.read_text(encoding="utf-8").splitlines(), 1):
            if line.startswith("```"):
                in_block = not in_block
                continue
            if not in_block:
                continue
            if not buffer:
                start = number
            if line.rstrip().endswith("\\"):
                buffer += line.rstrip()[:-1] + " "
                continue
            text, buffer = (buffer + line).strip(), ""
            if "ticket-autopilot.py" in text or "final_tree_forward_test.py" in text:
                examples.append(Example(document.name, start, text, tuple(shlex.split(text))))
    return examples


def listed_commands() -> list[str]:
    """The commands SKILL.md says exist, in the sentence that names them."""
    skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    sentence = re.search(r"Commands are (.*?); use `<command> --help`", skill, re.S)
    assert sentence, "SKILL.md no longer lists its commands in the expected sentence"
    return re.findall(r"`([a-z0-9-]+)`", sentence.group(1))


def substitute(token: str) -> str:
    if token in PLACEHOLDERS:
        return PLACEHOLDERS[token]
    if token.startswith("<") and token.endswith(">"):
        return "x"
    if token == "$PWD":
        return "."
    return token


class SkillExamplesTest(unittest.TestCase):
    """The examples, held to what a reader will do with them."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.examples = runner_examples()
        assert len(cls.examples) >= 20, "the inventory found too few examples to be reading the skill"

    def test_every_example_names_the_interpreter_the_skill_defines(self) -> None:
        """Turn 137: a hardcoded `python3` is a Store stub on many Windows hosts.

        No interpreter name resolves everywhere, so the skill defines one variable and
        every example uses it. `-B` stays: the installed skill must not grow `__pycache__`.
        """
        for example in self.examples:
            with self.subTest(str(example)):
                self.assertEqual(INTERPRETER, example.argv[0])
                self.assertEqual("-B", example.argv[1])
                self.assertTrue(
                    example.argv[2].startswith(ROOT_PREFIX),
                    f"the script path must be under {ROOT_PREFIX}: {example.argv[2]}",
                )
                self.assertNotIn("python3", example.text)

    def test_skill_md_defines_the_interpreter_before_its_first_command(self) -> None:
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        definition = skill.index("`TICKET_AUTOPILOT_PYTHON` is")
        first_command = skill.index('"$TICKET_AUTOPILOT_PYTHON" -B')
        self.assertLess(definition, first_command)
        for platform_note in ("python3", "Windows", "py -3"):
            self.assertIn(platform_note, skill[definition:first_command])

    def test_every_example_parses_against_the_real_parser(self) -> None:
        """Placeholders become plausible values; flags, choices and arity are the parser's."""
        parser = build_parser()
        for example in self.examples:
            if example.argv[2].endswith("final_tree_forward_test.py"):
                continue
            argv = [substitute(token) for token in example.argv[3:]]
            if argv == ["--help"]:
                continue
            with self.subTest(str(example)):
                captured = io.StringIO()
                try:
                    with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(captured):
                        parser.parse_args(argv)
                except SystemExit:
                    self.fail(f"the example does not parse: {captured.getvalue().strip()}")

    def test_every_command_the_skill_names_answers_help_when_executed(self) -> None:
        """The list is the reader's map of the CLI: a listed name that does not exist costs a turn."""
        for command in ["--help", *listed_commands()]:
            with self.subTest(command):
                argv = [command] if command == "--help" else [command, "--help"]
                completed = subprocess.run(
                    [sys.executable, "-B", str(CLI), *argv],
                    capture_output=True, text=True, timeout=120,
                )
                self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
                self.assertIn("usage:", completed.stdout)

    def test_the_events_example_shows_a_file_not_an_operation_name(self) -> None:
        """Turn 63: `--events` takes a path to a schema-1 document; `leaf-result` is an event inside it."""
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("--events <file.json>", skill)
        self.assertIn('{"schema": 1, "events": [...]}', skill)
        self.assertIn('"operation": "leaf-result"', skill)
        self.assertNotRegex(skill, r"--events\s+leaf-result")
        self.assertNotRegex(skill, r"`resume --events` accepts")


TICKET = (
    b'---\nticket_schema: 1\nticket_id: "X-01"\nexecution_mode: AFK\n'
    b"blocked_by: []\n---\n\n# X-01\n\n## What to Build\na\n"
)


class DocumentedEventsShapeTest(GitIsolatedTestCase):
    """The documented shape has to be the one the runner reads."""

    def setUp(self) -> None:
        super().setUp()
        self.temporary = tempfile.TemporaryDirectory(prefix="apf04-")
        self.addCleanup(self.temporary.cleanup)
        root = Path(self.temporary.name)
        self.repo, upstream = root / "repo", root / "upstream.git"
        self.repo.mkdir()
        git = lambda *a: subprocess.run(["git", *a], capture_output=True, text=True, check=True)
        git("init", "-b", "main", str(self.repo))
        git("-C", str(self.repo), "config", "user.email", "t@example.com")
        git("-C", str(self.repo), "config", "user.name", "Test")
        folder = self.repo / "docs/tickets/x"
        folder.mkdir(parents=True)
        (folder / "01-a.md").write_bytes(TICKET)
        git("-C", str(self.repo), "add", "-A")
        git("-C", str(self.repo), "commit", "-m", "init")
        git("init", "--bare", "-b", "main", str(upstream))
        git("-C", str(self.repo), "remote", "add", "origin", str(upstream))
        git("-C", str(self.repo), "push", "-q", "origin", "main")
        started = self.cli("run", str(folder), "--repo", str(self.repo), "--base", "main",
                           "--provider", "github", "--run-id", "docs-shape")
        self.assertTrue(started["ok"], started)
        self.tree = git("-C", str(self.repo), "rev-parse", "HEAD^{tree}").stdout.strip()

    def cli(self, *args: str) -> dict:
        completed = subprocess.run(
            [sys.executable, "-B", str(CLI), *args],
            capture_output=True, text=True, cwd=str(self.repo), timeout=300,
        )
        return json.loads(completed.stdout or completed.stderr)

    def test_the_documented_file_shape_is_read_as_a_document(self) -> None:
        """A file in the shape SKILL.md shows gets past the document check to the event itself."""
        events = Path(self.temporary.name) / "events.json"
        events.write_text(json.dumps({
            "schema": 1,
            "events": [{
                "operation": "leaf-result",
                "ticket_id": "X-01",
                "expected_tree_oid": self.tree,
                "leaf_result": {},
            }],
        }), encoding="utf-8")
        response = self.cli("resume", "docs-shape", "--repo", str(self.repo), "--events", str(events))
        self.assertFalse(response["ok"], response)
        message = response["error"]["message"]
        self.assertNotIn("No such file", message)
        self.assertNotIn("event document must have schema 1", message)
        self.assertNotIn("unsupported orchestration event operation", message)

    def test_the_turn_63_command_still_fails_only_because_it_ignores_the_document(self) -> None:
        """Run what the old sentence invited; the CLI is unchanged, the sentence is not."""
        response = self.cli("resume", "docs-shape", "--repo", str(self.repo), "--events", "leaf-result")
        self.assertFalse(response["ok"])
        self.assertIn("No such file or directory", response["error"]["message"])
        self.assertIn("leaf-result", response["error"]["message"])


if __name__ == "__main__":
    unittest.main()
