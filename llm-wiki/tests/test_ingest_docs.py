from __future__ import annotations

import json
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

from ingest_docs import (  # noqa: E402
    ingest,
    page_name,
    plan,
    read_page_front_matter,
    source_digest,
)
from project_binding import write_binding  # noqa: E402

AUTOPILOT = REPO_ROOT / "ticket-autopilot"


def git(cwd: Path, *arguments: str) -> None:
    subprocess.run(
        ["git", "-C", str(cwd), *arguments],
        check=True, capture_output=True, text=True, encoding="utf-8",
    )


TICKET = """---
ticket_schema: 1
ticket_id: "01"
execution_mode: AFK
blocked_by:
  - "02"
---

# One slice

## Artifact Graph
- Artifact ID: `artifact:one-slice`
- Role: `ticket`
- Parent: [map](../../specs/map.md)

{body}
"""

SPEC = """# The map

## Artifact Graph

- Artifact ID: `artifact:map`
- Role: `wayfinder`
- Standalone: true

{body}
"""


class Fixture:
    """A project with one ticket, one spec, and one artefact with no stable identifier."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.project = root / "project"
        self.wiki = root / "wiki"
        (self.project / "docs" / "tickets" / "family").mkdir(parents=True)
        (self.project / "docs" / "specs").mkdir(parents=True)
        (self.project / "docs" / "research").mkdir(parents=True)
        self.ticket = self.project / "docs" / "tickets" / "family" / "01-slice.md"
        self.ticket.write_text(TICKET.format(body="original body"), encoding="utf-8")
        (self.project / "docs" / "specs" / "map.md").write_text(
            SPEC.format(body="original map"), encoding="utf-8"
        )
        self.weak = self.project / "docs" / "research" / "note.md"
        self.weak.write_text("# A note\n\nno artifact graph here\n", encoding="utf-8")
        git(self.project, "init", "--initial-branch=main")
        git(self.project, "config", "user.email", "t@example.invalid")
        git(self.project, "config", "user.name", "T")
        git(self.project, "add", "docs")
        git(self.project, "commit", "-m", "docs")
        self.wiki.mkdir()
        write_binding(self.wiki, self.project)

    def run(self, **kwargs) -> dict:
        return ingest(self.wiki, AUTOPILOT, **kwargs)

    def snapshot(self) -> dict[str, str]:
        return {
            path.relative_to(self.wiki).as_posix(): path.read_text(encoding="utf-8")
            for path in sorted(self.wiki.rglob("*.md"))
        }


class TransitionTests(unittest.TestCase):
    def test_1_a_second_run_over_an_unchanged_corpus_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            first = fixture.run()
            before = fixture.snapshot()
            second = fixture.run()
            after = fixture.snapshot()

        self.assertEqual(3, first["transitions"]["new"])
        self.assertEqual([], second["written"], "a no-op run must write zero bytes")
        self.assertEqual(3, second["transitions"]["unchanged"])
        self.assertEqual(before, after)

    def test_2_a_disposition_move_updates_one_page_and_creates_none(self) -> None:
        """The fixture the whole contract exists for.

        Also asserts the counterfactual: a page named from the source path would have been a
        different filename after the move, which is the duplicate this design prevents.
        """

        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            fixture.run()
            pages_before = sorted(p.name for p in (fixture.wiki / "wiki" / "sources").glob("*.md"))

            done = fixture.ticket.parent / "done"
            done.mkdir()
            git(fixture.project, "mv", "docs/tickets/family/01-slice.md",
                "docs/tickets/family/done/01-slice.md")
            git(fixture.project, "commit", "-m", "complete")

            report = fixture.run()
            pages_after = sorted(p.name for p in (fixture.wiki / "wiki" / "sources").glob("*.md"))

        self.assertEqual(1, report["transitions"]["moved"])
        self.assertEqual(0, report["transitions"]["new"], "no second page may appear")
        self.assertEqual(pages_before, pages_after, "the page set must be unchanged")
        self.assertEqual(
            [{"identity": "ticket:family/01", "event": "disposition-changed"}],
            [e for e in report["events"] if e["identity"] == "ticket:family/01"],
        )

    def test_2b_a_path_derived_name_would_have_produced_a_duplicate(self) -> None:
        """Shows the test above can fail: the defect is real, not hypothetical."""

        from ingest_docs import Artefact

        before = Artefact(
            relative_path="docs/tickets/family/01-slice.md",
            identity_key="path:docs/tickets/family/01-slice.md",
            kind="other", digest="sha256:x", disposition="open", title="One",
        )
        after = Artefact(
            relative_path="docs/tickets/family/done/01-slice.md",
            identity_key="path:docs/tickets/family/done/01-slice.md",
            kind="other", digest="sha256:x", disposition="completed", title="One",
        )
        self.assertNotEqual(
            page_name(before), page_name(after),
            "a path-derived identity yields two different pages for one artefact",
        )
        stable = Artefact(
            relative_path="docs/tickets/family/done/01-slice.md",
            identity_key="ticket:family/01", kind="ticket", digest="sha256:x",
            disposition="completed", title="One",
        )
        moved = Artefact(
            relative_path="docs/tickets/family/01-slice.md",
            identity_key="ticket:family/01", kind="ticket", digest="sha256:x",
            disposition="open", title="One",
        )
        self.assertEqual(page_name(stable), page_name(moved))

    def test_3_an_amendment_rewrites_the_page_and_appends_an_event(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            fixture.run()
            (fixture.project / "docs" / "specs" / "map.md").write_text(
                SPEC.format(body="a materially different map"), encoding="utf-8"
            )
            report = fixture.run()

        self.assertEqual(1, report["transitions"]["changed"])
        self.assertIn({"identity": "artifact:map", "event": "amended"}, report["events"])

    def test_4_a_touch_without_a_content_change_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            fixture.run()
            text = fixture.weak.read_text(encoding="utf-8")
            fixture.weak.write_text(text, encoding="utf-8")
            report = fixture.run()

        self.assertEqual([], report["written"], "detection is by digest, never by timestamp")

    def test_5_converting_line_endings_is_not_a_change(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            fixture.run()
            # Normalise first. On a checkout with core.autocrlf the file may already be CRLF,
            # and a naive replace would produce \r\r\n, which is a genuine content change
            # rather than a line-ending conversion.
            raw = fixture.weak.read_bytes().replace(b"\r\n", b"\n")
            fixture.weak.write_bytes(raw.replace(b"\n", b"\r\n"))
            self.assertIn(b"\r\n", fixture.weak.read_bytes(), "the fixture must be CRLF")
            report = fixture.run()

        self.assertEqual([], report["written"])
        self.assertEqual(3, report["transitions"]["unchanged"])

    def test_6_a_removed_artefact_is_tombstoned_and_never_deleted(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            fixture.run()
            pages_before = sorted(p.name for p in (fixture.wiki / "wiki" / "sources").glob("*.md"))
            fixture.weak.unlink()
            report = fixture.run()
            sources = fixture.wiki / "wiki" / "sources"
            pages_after = sorted(p.name for p in sources.glob("*.md"))
            tombstone = next(
                p for p in sources.glob("*.md")
                if read_page_front_matter(p).get("source_status") == "missing"
            )
            surviving = tombstone.read_text(encoding="utf-8")

        self.assertEqual(1, report["transitions"]["missing"])
        self.assertEqual(pages_before, pages_after, "nothing is deleted")
        self.assertIn("A note", surviving, "the last known content survives")
        self.assertTrue(
            any(e["event"] == "source-removed" for e in report["events"])
        )

    def test_7_moving_a_weak_key_artefact_is_reported_not_hidden(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            first = fixture.run()
            self.assertIn("path:docs/research/note.md", first["weak_identities"])

            moved = fixture.project / "docs" / "research" / "moved-note.md"
            fixture.weak.rename(moved)
            report = fixture.run()

        self.assertEqual(1, report["transitions"]["missing"])
        self.assertEqual(1, report["transitions"]["new"])
        self.assertIn(
            "path:docs/research/moved-note.md",
            report["weak_identities"],
            "the weak key is labelled so the limitation is visible",
        )


class ContractTests(unittest.TestCase):
    def test_the_standard_command_resolves_the_canonical_ticket_parser(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(SCRIPTS / "ingest_docs.py"),
                    str(fixture.wiki),
                    "--json",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            ticket = fixture.wiki / "wiki" / "sources" / "ticket-family-01.md"
            matter = read_page_front_matter(ticket)

        self.assertIn("ticket-family-01.md", report["written"])
        self.assertEqual("ticket:family/01", matter["identity_key"])
        self.assertEqual("ticket", matter["artefact_kind"])

    def test_a_ticket_fails_explicitly_when_the_parser_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixture = Fixture(root)
            unavailable = root / "missing-ticket-autopilot"
            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(SCRIPTS / "ingest_docs.py"),
                    str(fixture.wiki),
                    "--autopilot-root",
                    str(unavailable),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )

            self.assertFalse(
                (fixture.wiki / "wiki" / "sources").exists(),
                "a failed ticket parse must not write a spec-shaped fallback page",
            )

        self.assertEqual(2, result.returncode)
        self.assertRegex(result.stderr, "ticket parser.*unavailable")

    def test_blocked_by_comes_from_the_canonical_parser(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            fixture.run()
            page = fixture.wiki / "wiki" / "sources" / "ticket-family-01.md"
            text = page.read_text(encoding="utf-8")

        self.assertIn("ticket:family/02", text, "blocked_by must be materialised")
        self.assertNotIn(
            "[[ticket:family/02]]",
            text,
            "an identity key is not a page name, so it is never a wikilink target",
        )

    def test_a_blocker_inside_the_wiki_links_to_that_blockers_page(self) -> None:
        """The form that was dead: the page is `ticket-family-02`, the key is `ticket:family/02`."""

        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            second = fixture.project / "docs" / "tickets" / "family" / "02-second.md"
            second.write_text(
                fixture.ticket.read_text(encoding="utf-8")
                .replace('ticket_id: "01"', 'ticket_id: "02"')
                .replace("blocked_by:\n  - \"02\"", "blocked_by: []")
                .replace("artifact:one-slice", "artifact:two-slice"),
                encoding="utf-8",
            )
            fixture.run()
            text = (fixture.wiki / "wiki" / "sources" / "ticket-family-01.md").read_text(
                encoding="utf-8"
            )
            pages = {
                path.stem for path in (fixture.wiki / "wiki" / "sources").glob("*.md")
            }

        self.assertIn("ticket-family-02", pages, "the blocker must have a page to link to")
        self.assertIn("- Blocked by: [[sources/ticket-family-02]]", text)

    def test_a_parent_link_resolves_across_a_disposition_move(self) -> None:
        """A ticket in `done/` has a parent link written for its open location."""

        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            fixture.run()
            done = fixture.ticket.parent / "done"
            done.mkdir(exist_ok=True)
            fixture.ticket.rename(done / fixture.ticket.name)
            fixture.run()
            text = (fixture.wiki / "wiki" / "sources" / "ticket-family-01.md").read_text(
                encoding="utf-8"
            )

        parent_line = next(
            line for line in text.splitlines() if line.startswith("- Parent source:")
        )

        self.assertIn("docs/tickets/family/done/", text, "the move really happened")
        self.assertEqual("- Parent source: [[sources/artifact-map]]", parent_line)

    def test_the_digest_normalises_line_endings(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            lf, crlf = root / "lf.md", root / "crlf.md"
            lf.write_bytes(b"# a\n\nbody\n")
            crlf.write_bytes(b"# a\r\n\r\nbody\r\n")
            self.assertEqual(source_digest(lf), source_digest(crlf))

    def test_ingest_never_writes_to_the_project(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            before = {
                path.relative_to(fixture.project).as_posix(): path.read_bytes()
                for path in sorted((fixture.project / "docs").rglob("*.md"))
            }
            fixture.run()
            after = {
                path.relative_to(fixture.project).as_posix(): path.read_bytes()
                for path in sorted((fixture.project / "docs").rglob("*.md"))
            }
        self.assertEqual(before, after)

    def test_the_index_lists_every_page_exactly_once(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            fixture.run()
            index = (fixture.wiki / "wiki" / "index.md").read_text(encoding="utf-8")
            pages = [p.stem for p in (fixture.wiki / "wiki" / "sources").glob("*.md")]

        for stem in pages:
            self.assertEqual(
                1, index.count(f"[[sources/{stem}]]"), f"{stem} must appear once"
            )

    def test_dates_carry_their_provenance_on_every_page(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            fixture.run()
            for page in (fixture.wiki / "wiki" / "sources").glob("*.md"):
                text = page.read_text(encoding="utf-8")
                matter = read_page_front_matter(page)
                with self.subTest(page=page.name):
                    self.assertIn("created_provenance", matter)
                    self.assertIn("disposition_changed_provenance", matter)
                    self.assertNotIn("disposition_changed: \n", text)


class CorpusIdentityTests(unittest.TestCase):
    def test_a_mixed_corpus_plans_without_duplicate_page_names(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            resolved = plan(fixture.wiki, AUTOPILOT)

        corpus = resolved["corpus"]
        self.assertEqual(
            {"ticket:family/01", "artifact:map", "path:docs/research/note.md"},
            set(corpus),
        )
        names = [page_name(artefact) for artefact in corpus.values()]
        self.assertEqual(len(names), len(set(names)), "two artefacts share a page name")


if __name__ == "__main__":
    unittest.main()
