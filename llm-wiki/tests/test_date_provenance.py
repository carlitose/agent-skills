from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_ROOT.parent
SCRIPTS = SKILL_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from date_provenance import (  # noqa: E402
    PROVENANCE_RUNGS,
    ResolvedDate,
    disposition_of,
    resolve_artefact_dates,
    resolve_created,
    resolve_disposition_change,
)

TICKET = "docs/tickets/windows-text-fidelity/done/01-body-round-trip-fidelity.md"
CANCELED = "docs/tickets/windows-text-fidelity/canceled/07-decide-and-introduce-ci.md"


def git(cwd: Path, *arguments: str) -> None:
    subprocess.run(
        ["git", "-C", str(cwd), *arguments],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def init_repo(project: Path) -> None:
    git(project, "init", "--initial-branch=main")
    git(project, "config", "user.email", "test@example.invalid")
    git(project, "config", "user.name", "Test")


def ticket_text(body: str) -> str:
    return f'---\nticket_schema: 1\nticket_id: "01"\n---\n\n# One\n\n{body}\n'


class ProvenanceTypeTests(unittest.TestCase):
    def test_a_date_cannot_exist_without_a_known_rung(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown provenance rung"):
            ResolvedDate("2026-08-13", "vibes")

    def test_unknown_carries_no_value_and_a_value_needs_a_rung(self) -> None:
        with self.assertRaisesRegex(ValueError, "cannot carry a value"):
            ResolvedDate("2026-08-13", "unknown")
        with self.assertRaisesRegex(ValueError, "must carry a value"):
            ResolvedDate(None, "git-rename")

    def test_only_mtime_is_low_confidence(self) -> None:
        self.assertTrue(ResolvedDate("2026-08-13", "mtime").low_confidence)
        for rung in ("git-rename", "git-commit", "frontmatter", "session-observed"):
            self.assertFalse(ResolvedDate("2026-08-13", rung).low_confidence, rung)

    def test_the_ladder_is_declared_in_order(self) -> None:
        self.assertEqual(
            (
                "git-rename",
                "git-commit",
                "frontmatter",
                "session-observed",
                "mtime",
                "unknown",
            ),
            PROVENANCE_RUNGS,
        )


class RealRepositoryTests(unittest.TestCase):
    """Pinned to facts verified by hand before this module existed."""

    def test_the_disposition_move_is_recovered_as_a_rename(self) -> None:
        changed = resolve_disposition_change(REPO_ROOT, TICKET)
        self.assertEqual("2026-08-13", changed.value)
        self.assertEqual("git-rename", changed.provenance)
        self.assertIn("437b287", changed.detail or "")
        self.assertIn("R100", changed.detail or "")

    def test_creation_comes_from_the_first_commit(self) -> None:
        created = resolve_created(REPO_ROOT, TICKET)
        self.assertEqual("2026-08-12", created.value)
        self.assertEqual("git-commit", created.provenance)
        self.assertIn("81c351f", created.detail or "")

    def test_a_canceled_ticket_resolves_the_same_way(self) -> None:
        changed = resolve_disposition_change(REPO_ROOT, CANCELED)
        self.assertEqual("2026-08-13", changed.value)
        self.assertEqual("git-rename", changed.provenance)
        self.assertIn("711e574", changed.detail or "")

    def test_disposition_is_read_from_the_location(self) -> None:
        self.assertEqual("completed", disposition_of(TICKET))
        self.assertEqual("canceled", disposition_of(CANCELED))
        self.assertEqual(
            "open", disposition_of("docs/tickets/windows-text-fidelity/04-x.md")
        )
        self.assertEqual("on-hold", disposition_of("docs/tickets/f/hold/05-x.md"))

    def test_an_open_ticket_has_no_disposition_change_to_date(self) -> None:
        changed = resolve_disposition_change(
            REPO_ROOT, "docs/tickets/llm-wiki-project-history/04-date-provenance-ladder.md"
        )
        self.assertEqual("unknown", changed.provenance)
        self.assertIsNone(changed.value)


class DegradationTests(unittest.TestCase):
    def test_untracked_docs_report_unknown_rather_than_an_mtime_guess(self) -> None:
        """The defect this module exists to prevent.

        With ``docs/`` untracked there is no witness to a move at all. Returning a filesystem
        timestamp would be indistinguishable from a recorded fact at the point of reading.
        """

        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            init_repo(project)
            (project / ".gitignore").write_text("docs/\n", encoding="utf-8")
            git(project, "add", ".gitignore")
            git(project, "commit", "-m", "ignore docs")
            done = project / "docs" / "tickets" / "family" / "done"
            done.mkdir(parents=True)
            (done / "01-slice.md").write_text(ticket_text("body"), encoding="utf-8")

            report = resolve_artefact_dates(project, "docs/tickets/family/done/01-slice.md")

        self.assertEqual("completed", report["disposition"])
        self.assertIsNone(report["disposition_changed"])
        self.assertEqual("unknown", report["disposition_changed_provenance"])
        self.assertEqual(
            "mtime",
            report["created_provenance"],
            "creation may still fall to mtime; only the move must not",
        )
        self.assertTrue(report["created_low_confidence"])

    def test_a_non_git_host_resolves_without_raising(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            done = project / "docs" / "tickets" / "family" / "done"
            done.mkdir(parents=True)
            (done / "01-slice.md").write_text(ticket_text("body"), encoding="utf-8")

            report = resolve_artefact_dates(project, "docs/tickets/family/done/01-slice.md")

        self.assertIn(report["created_provenance"], {"mtime", "unknown"})
        self.assertEqual("unknown", report["disposition_changed_provenance"])

    def test_frontmatter_outranks_a_filesystem_timestamp(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            folder = project / "docs" / "specs"
            folder.mkdir(parents=True)
            (folder / "a.md").write_text(
                "---\ncreated: 2026-01-02\n---\n\n# a\n", encoding="utf-8"
            )

            created = resolve_created(project, "docs/specs/a.md")

        self.assertEqual("2026-01-02", created.value)
        self.assertEqual("frontmatter", created.provenance)

    def test_a_transcript_mention_dates_a_move_when_git_is_silent(self) -> None:
        """The session-observed rung: the only witness left on an untracked project."""

        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            done = project / "docs" / "tickets" / "family" / "done"
            done.mkdir(parents=True)
            (done / "01-slice.md").write_text(ticket_text("body"), encoding="utf-8")

            changed = resolve_disposition_change(
                project,
                "docs/tickets/family/done/01-slice.md",
                session_mentions=("2026-08-11", "2026-08-14", "2026-08-12"),
            )

        self.assertEqual("2026-08-14", changed.value, "the latest mention dates the move")
        self.assertEqual("session-observed", changed.provenance)
        self.assertFalse(changed.low_confidence)


class DeleteAddPairTests(unittest.TestCase):
    def _repo_with_move_and_edit(self, project: Path) -> str:
        """Move a ticket into done/ and rewrite it in the same commit.

        A rewrite this heavy falls below the rename similarity threshold, so Git records a
        delete plus an add rather than a rename.
        """

        init_repo(project)
        folder = project / "docs" / "tickets" / "family"
        folder.mkdir(parents=True)
        source = folder / "01-slice.md"
        source.write_text(ticket_text("original body " * 40), encoding="utf-8")
        git(project, "add", "docs")
        git(project, "commit", "-m", "add ticket")
        (folder / "done").mkdir()
        source.unlink()
        (folder / "done" / "01-slice.md").write_text(
            ticket_text("completely different content " * 60), encoding="utf-8"
        )
        git(project, "add", "-A", "docs")
        git(project, "commit", "-m", "complete and rewrite")
        return "docs/tickets/family/done/01-slice.md"

    def test_a_move_recorded_as_delete_plus_add_is_still_dated(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            relative = self._repo_with_move_and_edit(project)

            renames = subprocess.run(
                ["git", "-C", str(project), "log", "--diff-filter=R",
                 "--find-renames", "--format=%h", "--", relative],
                capture_output=True, text=True, encoding="utf-8", check=False,
            ).stdout.strip()
            changed = resolve_disposition_change(
                project, relative, identity_key="ticket:family/01"
            )

        self.assertEqual("", renames, "the fixture must not be a detectable rename")
        self.assertTrue(changed.known, "the pairing must recover a date the rename missed")
        self.assertEqual("git-rename", changed.provenance)
        self.assertIn("delete-plus-add", changed.detail or "")


if __name__ == "__main__":
    unittest.main()
