"""The shared repoint rule the movers call when a ticket changes disposition."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from autopilot.link_repoint import repoint_moved_file  # noqa: E402


class Fixture:
    def __init__(self, root: Path) -> None:
        self.root = root
        (root / "docs" / "specs").mkdir(parents=True)
        (root / "docs" / "tickets" / "family" / "done").mkdir(parents=True)
        self.map = root / "docs" / "specs" / "map.md"
        self.map.write_text(
            "# Map\n\n### Children\n- [the slice](../tickets/family/01-slice.md)\n",
            encoding="utf-8",
        )


class RepointTests(unittest.TestCase):
    def test_a_completion_move_repoints_the_map(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            changed = repoint_moved_file(
                fixture.root,
                "docs/tickets/family/01-slice.md",
                "docs/tickets/family/done/01-slice.md",
            )

            self.assertEqual(["docs/specs/map.md"], changed)
            self.assertIn(
                "(../tickets/family/done/01-slice.md)",
                fixture.map.read_text(encoding="utf-8"),
            )

    def test_a_reopen_repoints_in_reverse(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            fixture.map.write_text(
                "- [the slice](../tickets/family/done/01-slice.md)\n", encoding="utf-8"
            )
            changed = repoint_moved_file(
                fixture.root,
                "docs/tickets/family/done/01-slice.md",
                "docs/tickets/family/01-slice.md",
            )

            self.assertEqual(["docs/specs/map.md"], changed)
            self.assertIn(
                "(../tickets/family/01-slice.md)",
                fixture.map.read_text(encoding="utf-8"),
            )

    def test_a_fragment_survives(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            fixture.map.write_text(
                "- [plan](../tickets/family/01-slice.md#plan)\n", encoding="utf-8"
            )
            repoint_moved_file(
                fixture.root,
                "docs/tickets/family/01-slice.md",
                "docs/tickets/family/done/01-slice.md",
            )

            self.assertIn(
                "(../tickets/family/done/01-slice.md#plan)",
                fixture.map.read_text(encoding="utf-8"),
            )

    def test_a_replay_is_a_no_op(self) -> None:
        """Once repointed, no link names the old path — the second call changes nothing."""

        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            repoint_moved_file(
                fixture.root,
                "docs/tickets/family/01-slice.md",
                "docs/tickets/family/done/01-slice.md",
            )
            first = fixture.map.read_bytes()
            changed = repoint_moved_file(
                fixture.root,
                "docs/tickets/family/01-slice.md",
                "docs/tickets/family/done/01-slice.md",
            )

            self.assertEqual([], changed)
            self.assertEqual(first, fixture.map.read_bytes())


class ExclusionTests(unittest.TestCase):
    def test_a_ticket_source_is_never_rewritten(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            sibling = fixture.root / "docs" / "tickets" / "family" / "02-open.md"
            before = "# Open\n\n- [sibling](01-slice.md)\n"
            sibling.write_text(before, encoding="utf-8")
            changed = repoint_moved_file(
                fixture.root,
                "docs/tickets/family/01-slice.md",
                "docs/tickets/family/done/01-slice.md",
            )

            self.assertEqual(before, sibling.read_text(encoding="utf-8"))
            self.assertNotIn("docs/tickets/family/02-open.md", changed)

    def test_a_fenced_link_is_never_rewritten(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            lesson = fixture.root / "docs" / "specs" / "lesson.md"
            before = (
                "# Lesson\n\n```markdown\n"
                "- [example](../tickets/family/01-slice.md)\n"
                "```\n"
            )
            lesson.write_text(before, encoding="utf-8")
            repoint_moved_file(
                fixture.root,
                "docs/tickets/family/01-slice.md",
                "docs/tickets/family/done/01-slice.md",
            )

            self.assertEqual(before, lesson.read_text(encoding="utf-8"))

    def test_a_non_matching_document_is_not_even_rewritten_in_place(self) -> None:
        """Byte-identity for bystanders, asserted on mtime-independent content."""

        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            bystander = fixture.root / "docs" / "specs" / "other.md"
            before = "# Other\n\n- [elsewhere](another.md)\n"
            bystander.write_text(before, encoding="utf-8")
            changed = repoint_moved_file(
                fixture.root,
                "docs/tickets/family/01-slice.md",
                "docs/tickets/family/done/01-slice.md",
            )

            self.assertEqual(before, bystander.read_text(encoding="utf-8"))
            self.assertNotIn("docs/specs/other.md", changed)

    def test_crlf_line_endings_survive(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            fixture.map.write_bytes(
                b"# Map\r\n\r\n- [the slice](../tickets/family/01-slice.md)\r\n"
            )
            repoint_moved_file(
                fixture.root,
                "docs/tickets/family/01-slice.md",
                "docs/tickets/family/done/01-slice.md",
            )
            raw = fixture.map.read_bytes()

            self.assertIn(b"done/01-slice.md)\r\n", raw)
            self.assertEqual(raw.count(b"\n"), raw.count(b"\r\n"))

    def test_a_tree_with_no_docs_directory_is_a_no_op(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            changed = repoint_moved_file(
                Path(temporary), "docs/tickets/a/01.md", "docs/tickets/a/done/01.md"
            )

        self.assertEqual([], changed)


if __name__ == "__main__":
    unittest.main()
