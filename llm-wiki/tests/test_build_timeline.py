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

from build_timeline import (  # noqa: E402
    Event,
    build,
    collect,
    render_index,
    render_lifecycle,
    render_period,
)
from ingest_docs import ingest as ingest_docs  # noqa: E402
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
blocked_by: []
---

# One slice

## Artifact Graph
- Artifact ID: `artifact:one-slice`
- Role: `ticket`
- Parent: [map](../../specs/map.md)

body
"""


def source_page(**fields: str) -> str:
    defaults = {
        "type": "source", "title": '"A thing"', "identity_key": "ticket:family/01",
        "identity_strength": "stable", "source_path": "docs/tickets/family/done/01.md",
        "source_digest": "sha256:x", "source_status": "present", "artefact_kind": "ticket",
        "disposition": "completed", "created": "2026-08-12",
        "created_provenance": "git-commit", "disposition_changed": "2026-08-13",
        "disposition_changed_provenance": "git-rename",
    }
    defaults.update(fields)
    body = "\n".join(f"{key}: {value}" for key, value in defaults.items())
    return f"---\n{body}\n---\n\n# A thing\n\nbody\n"


def session_page(session_id: str, tickets: str, span: str) -> str:
    return (
        "---\n"
        "type: session\n"
        "provider: claude-code\n"
        f"session_id: {session_id}\n"
        f"span: {span}\n"
        "record_count: 10\n"
        f"tickets_touched: [{tickets}]\n"
        "source_status: complete\n"
        "---\n\n# session\n\nbody\n"
    )


class RenderingTests(unittest.TestCase):
    def test_an_unresolved_date_renders_as_unknown_with_its_reason(self) -> None:
        """The failure this module exists to prevent: a page that looks complete and is not."""

        record = {
            "identity": "ticket:family/01", "title": "A thing", "page": "p", "kind": "ticket",
            "disposition": "completed", "source_path": "docs/x.md", "source_status": "present",
            "run_id": None, "created": "", "created_provenance": "unknown",
            "changed": "", "changed_provenance": "unknown",
        }
        text = render_lifecycle(record, [])
        self.assertIn("Created: **unknown** — no witness at all", text)
        self.assertIn("Disposition changed: **unknown** — no witness at all", text)
        self.assertNotRegex(text, r"Created: \*\*\d{4}-\d{2}-\d{2}")

    def test_a_low_confidence_date_is_distinguishable_from_a_recorded_one(self) -> None:
        record = {
            "identity": "ticket:family/01", "title": "A thing", "page": "p", "kind": "ticket",
            "disposition": "completed", "source_path": "docs/x.md", "source_status": "present",
            "run_id": None, "created": "2026-08-01", "created_provenance": "mtime",
            "changed": "2026-08-13", "changed_provenance": "git-rename",
        }
        text = render_lifecycle(record, [])
        self.assertIn("**2026-08-01** — low confidence, from a filesystem timestamp", text)
        self.assertIn("**2026-08-13** — from a rename recorded in Git", text)
        self.assertNotIn("low confidence, from a rename", text)

    def test_a_period_page_uses_mermaid_and_no_ascii_diagram(self) -> None:
        events = [
            Event("2026-08-12", "created", "ticket:family/01", "One", "git-commit"),
            Event("2026-08-13", "disposition-changed", "ticket:family/01", "One", "git-rename"),
        ]
        text = render_period("2026-08", events)
        self.assertIn("```mermaid", text)
        self.assertIn("timeline", text)
        for ascii_art in ("+---", "|  ", "----+", "\\__"):
            self.assertNotIn(ascii_art, text)

    def test_the_index_names_every_rung_it_used_and_lists_the_gaps(self) -> None:
        months = {
            "2026-08": [Event("2026-08-12", "created", "a", "A", "git-commit")],
        }
        text = render_index(
            months,
            [{"identity": "a", "kind": "ticket"}],
            [],
            [{"identity": "b", "event": "disposition-changed", "reason": "unknown"}],
        )
        self.assertIn("`git-commit` — 1 event(s)", text)
        self.assertIn("Dates that could not be established", text)
        self.assertIn("`b` — disposition-changed: unknown", text)


class CollectionTests(unittest.TestCase):
    def _wiki(self, root: Path) -> Path:
        wiki = root / "wiki"
        sources = wiki / "wiki" / "sources"
        sources.mkdir(parents=True)
        return wiki

    def test_no_month_without_an_event_is_fabricated(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            wiki = self._wiki(Path(temporary))
            (wiki / "wiki" / "sources" / "a.md").write_text(
                source_page(created="2026-05-01", disposition_changed="2026-09-01"),
                encoding="utf-8",
            )
            report = build(wiki)

        self.assertEqual(["2026-05", "2026-09"], report["periods"])
        self.assertFalse((wiki / "wiki" / "timeline" / "2026-06.md").exists())
        self.assertFalse((wiki / "wiki" / "timeline" / "2026-07.md").exists())

    def test_sessions_link_to_tickets_and_tickets_back_to_sessions(self) -> None:
        """The bare identifier a digest records must join the full lifecycle identity."""

        with tempfile.TemporaryDirectory() as temporary:
            wiki = self._wiki(Path(temporary))
            sources = wiki / "wiki" / "sources"
            (sources / "ticket-family-01.md").write_text(source_page(), encoding="utf-8")
            (sources / "session-claude-code-abc.md").write_text(
                session_page("abc", "01", "2026-08-12 to 2026-08-13"), encoding="utf-8"
            )
            build(wiki)
            record = (wiki / "wiki" / "timeline" / "tickets" / "ticket-family-01.md").read_text(
                encoding="utf-8"
            )

        self.assertIn("[[sources/session-claude-code-abc]]", record)
        self.assertIn("dates *attention*, not completion", record)

    def test_an_unknown_disposition_date_is_reported_rather_than_dropped(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            wiki = self._wiki(Path(temporary))
            (wiki / "wiki" / "sources" / "a.md").write_text(
                source_page(disposition_changed="", disposition_changed_provenance="unknown"),
                encoding="utf-8",
            )
            report = build(wiki)
            index = (wiki / "wiki" / "timeline" / "index.md").read_text(encoding="utf-8")

        self.assertEqual(1, report["unknown_dates"])
        self.assertIn("Dates that could not be established", index)

    def test_a_tombstoned_source_keeps_its_lifecycle_record(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            wiki = self._wiki(Path(temporary))
            (wiki / "wiki" / "sources" / "a.md").write_text(
                source_page(source_status="missing"), encoding="utf-8"
            )
            build(wiki)
            record = (wiki / "wiki" / "timeline" / "tickets" / "ticket-family-01.md").read_text(
                encoding="utf-8"
            )

        self.assertIn("no longer exists", record)
        self.assertIn("deleting it would make the axis claim otherwise", record)

    def test_the_lifecycle_record_is_keyed_on_identity_not_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            wiki = self._wiki(Path(temporary))
            page = wiki / "wiki" / "sources" / "a.md"
            page.write_text(
                source_page(source_path="docs/tickets/family/01.md", disposition="open",
                            disposition_changed="", disposition_changed_provenance="unknown"),
                encoding="utf-8",
            )
            build(wiki)
            before = sorted(
                p.name for p in (wiki / "wiki" / "timeline" / "tickets").glob("*.md")
            )
            page.write_text(source_page(), encoding="utf-8")
            build(wiki)
            after = sorted(
                p.name for p in (wiki / "wiki" / "timeline" / "tickets").glob("*.md")
            )

        self.assertEqual(before, after, "a move must not mint a second lifecycle record")


class UntrackedProjectTests(unittest.TestCase):
    def test_a_move_on_an_untracked_project_renders_unknown_not_a_timestamp(self) -> None:
        """End to end on the case the whole ladder exists for."""

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            (project / "docs" / "tickets" / "family" / "done").mkdir(parents=True)
            (project / "docs" / "tickets" / "family" / "done" / "01-slice.md").write_text(
                TICKET, encoding="utf-8"
            )
            git(project, "init", "--initial-branch=main")
            git(project, "config", "user.email", "t@example.invalid")
            git(project, "config", "user.name", "T")
            (project / ".gitignore").write_text("docs/\n", encoding="utf-8")
            git(project, "add", ".gitignore")
            git(project, "commit", "-m", "ignore docs")

            wiki = root / "wiki"
            wiki.mkdir()
            write_binding(wiki, project)
            ingest_docs(wiki, AUTOPILOT)
            report = build(wiki)
            record = next(
                (wiki / "wiki" / "timeline" / "tickets").glob("*.md")
            ).read_text(encoding="utf-8")

        self.assertIn("Disposition changed: **unknown**", record)
        self.assertNotIn("Disposition changed: **2", record)
        self.assertGreaterEqual(report["unknown_dates"], 1)


class TrackedRepositoryTests(unittest.TestCase):
    def test_git_creation_and_rename_facts_appear_on_the_axis(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            tickets = project / "docs" / "tickets" / "family"
            tickets.mkdir(parents=True)
            ticket = tickets / "01-slice.md"
            ticket.write_text(TICKET, encoding="utf-8")
            git(project, "init", "--initial-branch=main")
            git(project, "config", "user.email", "t@example.invalid")
            git(project, "config", "user.name", "T")
            git(project, "add", "docs")
            git(
                project,
                "commit",
                "-m",
                "create ticket",
                "--date=2026-08-12T12:00:00+00:00",
            )
            done = tickets / "done"
            done.mkdir()
            git(
                project,
                "mv",
                "docs/tickets/family/01-slice.md",
                "docs/tickets/family/done/01-slice.md",
            )
            git(
                project,
                "commit",
                "-m",
                "complete ticket",
                "--date=2026-08-13T12:00:00+00:00",
            )

            wiki = root / "wiki"
            wiki.mkdir()
            write_binding(wiki, project)
            ingest_docs(wiki, AUTOPILOT)
            build(wiki)
            august = (wiki / "wiki" / "timeline" / "2026-08.md").read_text(encoding="utf-8")
            record = (
                wiki / "wiki" / "timeline" / "tickets"
                / "ticket-family-01.md"
            ).read_text(encoding="utf-8")
            collected = collect(wiki)

        self.assertIn("2026-08-12", august)
        self.assertIn("2026-08-13", august)
        self.assertIn("created: 2026-08-12", record)
        self.assertIn("disposition_changed: 2026-08-13", record)
        self.assertIn("disposition_changed_provenance: git-rename", record)
        provenances = {event.provenance for event in collected["events"]}
        self.assertIn("git-rename", provenances)
        self.assertIn("git-commit", provenances)
        self.assertNotIn(
            "mtime", provenances, "the fixture's docs are tracked, so no date is a guess"
        )


if __name__ == "__main__":
    unittest.main()
