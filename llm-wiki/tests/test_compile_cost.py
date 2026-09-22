"""A compile may not pay for the same answer twice.

Compiling a 690-page wiki launched 1,792 processes and spent 260 s of a 276 s ingest inside
them. Two of those costs were redundant: asking Git whether a directory is a repository and
whether a file is tracked, once per artefact, and starting a Python interpreter once per
ticket to reach a parser already importable. These tests hold both answers to their cost and,
more importantly, to their correctness: a cache that survives a commit would be a wrong answer
delivered quickly.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import date_provenance  # noqa: E402
import ingest_docs  # noqa: E402
from date_provenance import resolve_created  # noqa: E402




def git(cwd: Path, *arguments: str) -> None:
    subprocess.run(
        ["git", "-C", str(cwd), *arguments],
        check=True, capture_output=True, text=True, encoding="utf-8",
    )


def init_repo(project: Path) -> None:
    git(project, "init", "--initial-branch=main")
    git(project, "config", "user.email", "test@example.invalid")
    git(project, "config", "user.name", "Test")


class CountedProcesses:
    """Count process launches without hiding them: the real call still runs."""

    def __init__(self, module) -> None:
        self.module = module
        self.commands: list[list[str]] = []

    def __enter__(self):
        self.original = self.module.subprocess.run

        def counted(*args, **kwargs):
            command = args[0] if args else kwargs.get("args")
            self.commands.append([str(part) for part in command])
            return self.original(*args, **kwargs)

        self.module.subprocess.run = counted
        return self

    def __exit__(self, *_):
        self.module.subprocess.run = self.original


class RepositoryAnswersAreNotRepaid(unittest.TestCase):
    def setUp(self) -> None:
        date_provenance._REPOSITORY_STATE.clear()
        date_provenance._TRACKED_FILES.clear()
        self.directory = tempfile.TemporaryDirectory()
        self.project = Path(self.directory.name)
        self.addCleanup(self.directory.cleanup)

    def write(self, relative: str, text: str = "x\n") -> None:
        target = self.project / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    def test_the_same_question_about_many_files_costs_one_pair_of_processes(self) -> None:
        init_repo(self.project)
        for index in range(5):
            self.write(f"docs/specs/{index}.md")
        git(self.project, "add", "-A")
        git(self.project, "commit", "-m", "add specs")
        with CountedProcesses(date_provenance) as counted:
            for index in range(5):
                resolve_created(self.project, f"docs/specs/{index}.md")
        shapes = [command[3] for command in counted.commands]
        self.assertEqual(1, shapes.count("rev-parse"), "repository-ness is asked once")
        self.assertEqual(1, shapes.count("ls-files"), "the tracked set is read once")
        self.assertEqual(5, shapes.count("log"), "each file still gets its own history")

    def test_a_commit_between_two_calls_is_seen(self) -> None:
        init_repo(self.project)
        self.write("docs/specs/one.md")
        git(self.project, "add", "-A")
        git(self.project, "commit", "-m", "one")
        first = resolve_created(self.project, "docs/specs/one.md")
        self.assertEqual("git-commit", first.provenance)

        self.write("docs/specs/two.md")
        untracked = resolve_created(self.project, "docs/specs/two.md")
        self.assertNotEqual("git-commit", untracked.provenance)

        git(self.project, "add", "-A")
        git(self.project, "commit", "-m", "two")
        tracked = resolve_created(self.project, "docs/specs/two.md")
        self.assertEqual(
            "git-commit", tracked.provenance, "a stale tracked set would miss the commit"
        )

    def test_a_directory_that_becomes_a_repository_is_seen(self) -> None:
        self.write("docs/specs/one.md")
        before = resolve_created(self.project, "docs/specs/one.md")
        self.assertNotEqual("git-commit", before.provenance)
        init_repo(self.project)
        git(self.project, "add", "-A")
        git(self.project, "commit", "-m", "one")
        after = resolve_created(self.project, "docs/specs/one.md")
        self.assertEqual("git-commit", after.provenance)

    def test_two_repositories_do_not_share_an_answer(self) -> None:
        init_repo(self.project)
        self.write("docs/specs/one.md")
        git(self.project, "add", "-A")
        git(self.project, "commit", "-m", "one")
        other = tempfile.TemporaryDirectory()
        self.addCleanup(other.cleanup)
        elsewhere = Path(other.name)
        (elsewhere / "docs/specs").mkdir(parents=True)
        (elsewhere / "docs/specs/one.md").write_text("x\n", encoding="utf-8")
        self.assertEqual("git-commit", resolve_created(self.project, "docs/specs/one.md").provenance)
        self.assertNotEqual(
            "git-commit", resolve_created(elsewhere, "docs/specs/one.md").provenance
        )


class TicketsCostOneProcessPerTree(unittest.TestCase):
    """The canonical CLI stays behind a process boundary; it is crossed once, not per ticket."""

    def setUp(self) -> None:
        ingest_docs._TICKET_INVENTORIES.clear()
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.tickets = self.root / "docs" / "tickets" / "family"
        self.tickets.mkdir(parents=True)
        self.addCleanup(self.directory.cleanup)

    def write(self, name: str, ticket_id: str = "T-1", blocked: tuple = ()) -> Path:
        blockers = "blocked_by: []\n" if not blocked else "blocked_by:\n" + "".join(
            f'  - "{item}"\n' for item in blocked
        )
        target = self.tickets / name
        target.write_text(
            "---\nticket_schema: 1\n"
            f'ticket_id: "{ticket_id}"\nexecution_mode: AFK\n{blockers}'
            "---\n\n# One\n\nBody.\n",
            encoding="utf-8",
        )
        return target

    def test_a_whole_tree_of_tickets_costs_one_process(self) -> None:
        paths = [self.write(f"{index}-slice.md", f"T-{index}") for index in range(4)]
        with CountedProcesses(ingest_docs) as counted:
            envelopes = [
                ingest_docs._ticket_envelope(ingest_docs.default_autopilot_root(), path)
                for path in paths
            ]
        self.assertEqual(
            1, len(counted.commands), "one inventory answers the whole tree"
        )
        self.assertIn("ticket-list", counted.commands[0])
        self.assertEqual(
            ["T-0", "T-1", "T-2", "T-3"], [envelope["ticket_id"] for envelope in envelopes]
        )

    def test_blockers_survive_the_inventory(self) -> None:
        path = self.write("01-slice.md", "T-9", blocked=("T-1",))
        envelope = ingest_docs._ticket_envelope(ingest_docs.default_autopilot_root(), path)
        self.assertEqual("T-9", envelope["ticket_id"])
        self.assertEqual(["T-1"], list(envelope["blocked_by"]))

    def test_an_edited_ticket_is_never_answered_from_the_previous_reading(self) -> None:
        path = self.write("01-slice.md", "T-1")
        first = ingest_docs._ticket_envelope(ingest_docs.default_autopilot_root(), path)
        self.assertEqual("T-1", first["ticket_id"])
        self.write("01-slice.md", "T-2")
        second = ingest_docs._ticket_envelope(ingest_docs.default_autopilot_root(), path)
        self.assertEqual(
            "T-2", second["ticket_id"], "a stale inventory would keep T-1"
        )

    def test_a_new_ticket_is_seen(self) -> None:
        first = self.write("01-slice.md", "T-1")
        ingest_docs._ticket_envelope(ingest_docs.default_autopilot_root(), first)
        second = self.write("02-slice.md", "T-2")
        envelope = ingest_docs._ticket_envelope(ingest_docs.default_autopilot_root(), second)
        self.assertEqual("T-2", envelope["ticket_id"])

    def test_a_missing_parser_is_still_refused_by_name(self) -> None:
        path = self.write("01-slice.md")
        with self.assertRaises(ingest_docs.TicketParserError) as failure:
            ingest_docs._ticket_envelope(self.root / "absent", path)
        self.assertIn("ticket parser is unavailable", str(failure.exception))

    def test_an_unparseable_ticket_is_still_refused_with_its_own_message(self) -> None:
        broken = self.tickets / "broken.md"
        broken.write_text("# no front matter\n", encoding="utf-8")
        with self.assertRaises(ingest_docs.TicketParserError) as failure:
            ingest_docs._ticket_envelope(ingest_docs.default_autopilot_root(), broken)
        self.assertIn("canonical ticket parser failed", str(failure.exception))

    def test_a_ticket_outside_the_usual_layout_still_parses(self) -> None:
        elsewhere = self.root / "loose.md"
        elsewhere.write_text(
            '---\nticket_schema: 1\nticket_id: "T-7"\n'
            'execution_mode: AFK\nblocked_by: []\n---\n\n# One\n\nBody.\n',
            encoding="utf-8",
        )
        envelope = ingest_docs._ticket_envelope(
            ingest_docs.default_autopilot_root(), elsewhere
        )
        self.assertEqual("T-7", envelope["ticket_id"])


if __name__ == "__main__":
    unittest.main()
