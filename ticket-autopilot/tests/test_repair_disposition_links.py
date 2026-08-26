"""The one-time disposition-drift repair: repoint what moved, guess at nothing."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import repair_disposition_links as module  # noqa: E402
from repair_disposition_links import repair  # noqa: E402


class Fixture:
    """A docs/ tree with one spec linking one ticket that moved into done/."""

    def __init__(self, root: Path) -> None:
        self.root = root
        (root / "docs" / "specs").mkdir(parents=True)
        (root / "docs" / "tickets" / "family" / "done").mkdir(parents=True)
        (root / "docs" / "tickets" / "family" / "done" / "01-slice.md").write_text(
            "# Slice\n", encoding="utf-8"
        )
        self.map = root / "docs" / "specs" / "map.md"
        self.map.write_text(
            "# Map\n\n### Children\n"
            "- [the slice](../tickets/family/01-slice.md)\n",
            encoding="utf-8",
        )


class RepointTests(unittest.TestCase):
    def test_a_link_into_a_disposition_directory_is_repointed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            report = repair(fixture.root)
            text = fixture.map.read_text(encoding="utf-8")

            self.assertIn("(../tickets/family/done/01-slice.md)", text)
        self.assertEqual(1, len(report.repointed))
        self.assertEqual([], report.unresolved)

    def test_a_fragment_survives_the_repoint(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            fixture.map.write_text(
                "- [a section](../tickets/family/01-slice.md#plan)\n", encoding="utf-8"
            )
            repair(fixture.root)

            self.assertIn(
                "(../tickets/family/done/01-slice.md#plan)",
                fixture.map.read_text(encoding="utf-8"),
            )

    def test_a_link_out_of_a_disposition_directory_is_repointed(self) -> None:
        """The reverse direction: the written path says done/, the file moved back out."""

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "docs" / "specs").mkdir(parents=True)
            (root / "docs" / "notes").mkdir(parents=True)
            (root / "docs" / "notes" / "reopened.md").write_text("# Back\n", encoding="utf-8")
            page = root / "docs" / "specs" / "map.md"
            page.write_text("- [back](../notes/done/reopened.md)\n", encoding="utf-8")
            report = repair(root)

            self.assertIn("(../notes/reopened.md)", page.read_text(encoding="utf-8"))
            self.assertEqual(1, len(report.repointed))

    def test_more_than_one_candidate_is_reported_not_guessed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            canceled = fixture.root / "docs" / "tickets" / "family" / "canceled"
            canceled.mkdir()
            (canceled / "01-slice.md").write_text("# Twin\n", encoding="utf-8")
            report = repair(fixture.root)

            self.assertIn(
                "(../tickets/family/01-slice.md)",
                fixture.map.read_text(encoding="utf-8"),
                "left untouched",
            )
        self.assertEqual(1, len(report.ambiguous))
        self.assertEqual([], report.repointed)

    def test_a_target_existing_nowhere_is_reported_dead(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            fixture.map.write_text("- [ghost](../tickets/family/99-ghost.md)\n", encoding="utf-8")
            report = repair(fixture.root)

            self.assertEqual(1, len(report.unresolved))
            self.assertEqual([], report.repointed)
            self.assertIn(
                "(../tickets/family/99-ghost.md)",
                fixture.map.read_text(encoding="utf-8"),
            )


class ExclusionTests(unittest.TestCase):
    def test_a_ticket_source_is_never_rewritten(self) -> None:
        """A ticket's bytes are digest-frozen; rewriting one corrupts the contract."""

        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            ticket = fixture.root / "docs" / "tickets" / "family" / "02-open.md"
            before = "# Open\n\n- [sibling](01-slice.md)\n"
            ticket.write_text(before, encoding="utf-8")
            report = repair(fixture.root)

            self.assertEqual(before, ticket.read_text(encoding="utf-8"))
        self.assertNotIn("docs/tickets/family/02-open.md", report.changed_files)
        self.assertGreaterEqual(report.frozen_skipped, 1)

    def test_a_fenced_link_is_never_rewritten(self) -> None:
        """The Artifact Graph decision teaches the format with example links in fences."""

        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            lesson = fixture.root / "docs" / "specs" / "lesson.md"
            before = (
                "# Lesson\n\n```markdown\n"
                "- [example](../tickets/family/01-slice.md)\n"
                "```\n"
            )
            lesson.write_text(before, encoding="utf-8")
            repair(fixture.root)

            self.assertEqual(before, lesson.read_text(encoding="utf-8"))

    def test_a_live_link_is_never_rewritten(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            other = fixture.root / "docs" / "specs" / "other.md"
            other.write_text("# Other\n", encoding="utf-8")
            fixture.map.write_text("- [fine](other.md)\n", encoding="utf-8")
            report = repair(fixture.root)

            self.assertEqual(
                "- [fine](other.md)\n", fixture.map.read_text(encoding="utf-8")
            )
        self.assertEqual(0, report.dead)

    def test_non_markdown_and_external_targets_are_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            fixture.map.write_text(
                "- [site](https://example.invalid/page.md)\n"
                "- [anchor](#section)\n"
                "- [image](../assets/figure.png)\n",
                encoding="utf-8",
            )
            report = repair(fixture.root)

        self.assertEqual(0, report.links_seen)
        self.assertEqual(0, report.dead)


class StabilityTests(unittest.TestCase):
    def test_the_repair_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            repair(fixture.root)
            first = fixture.map.read_bytes()
            second_report = repair(fixture.root)

            self.assertEqual(first, fixture.map.read_bytes())
            self.assertEqual(0, second_report.dead)
            self.assertEqual([], second_report.changed_files)

    def test_crlf_line_endings_survive(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            fixture.map.write_bytes(
                b"# Map\r\n\r\n- [the slice](../tickets/family/01-slice.md)\r\n"
            )
            repair(fixture.root)
            raw = fixture.map.read_bytes()

        self.assertIn(b"done/01-slice.md)\r\n", raw)
        self.assertEqual(
            raw.count(b"\n"),
            raw.count(b"\r\n"),
            "every newline must still be CRLF; a bare LF means the repair rewrote endings",
        )

    def test_dry_run_writes_nothing_and_reports_everything(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            before = fixture.map.read_bytes()
            report = repair(fixture.root, dry_run=True)

            self.assertEqual(before, fixture.map.read_bytes())
            self.assertEqual(1, len(report.repointed))
            self.assertEqual(["docs/specs/map.md"], report.changed_files)

    def test_disposition_names_come_from_the_lifecycle_module(self) -> None:
        """No third copy of the directory set — that is how the readers diverged."""

        from autopilot.ticket_lifecycle import DISPOSITION_DIRECTORIES

        self.assertIs(module.DISPOSITION_DIRECTORIES, DISPOSITION_DIRECTORIES)


if __name__ == "__main__":
    unittest.main()
