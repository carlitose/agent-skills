"""The drift passes: a page against the artefact it came from.

Each pass gets a seeded defect *and* a clean fixture. Only the seeded pass may fire — a pass
that reports on a healthy wiki is as useless as one that cannot report at all.

Two fixtures exist for the constraints rather than for a pass: one on a host with no Git
repository, one on a repository whose `docs/` is ignored. Both must report zero errors, because
both are supported configurations and a missing history is not drift.
"""

from __future__ import annotations

import shutil
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

from build_timeline import build  # noqa: E402
from ingest_docs import ingest, source_digest  # noqa: E402
from lint_wiki import ERROR, INFO, WARNING, run_passes  # noqa: E402
from project_binding import write_binding  # noqa: E402
from scaffold import scaffold  # noqa: E402

AUTOPILOT = REPO_ROOT / "ticket-autopilot"

MAP = """# A map

## Artifact Graph
- Artifact ID: `artifact:the-map`
- Role: `wayfinder`
- Standalone: true

### Children
- [slice one](../tickets/family/01-slice.md)

body
"""

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
- Parent: [a map](../../specs/map.md)

body
"""


def git(cwd: Path, *arguments: str) -> None:
    subprocess.run(
        ["git", "-C", str(cwd), *arguments],
        check=True, capture_output=True, text=True, encoding="utf-8",
    )


class Fixture:
    """A bound wiki over a two-artefact project, ingested and timelined."""

    def __init__(self, root: Path, *, repository: bool = True, ignore_docs: bool = False) -> None:
        self.project = root / "project"
        (self.project / "docs" / "specs").mkdir(parents=True)
        (self.project / "docs" / "tickets" / "family").mkdir(parents=True)
        (self.project / "docs" / "specs" / "map.md").write_text(MAP, encoding="utf-8")
        self.ticket = self.project / "docs" / "tickets" / "family" / "01-slice.md"
        self.ticket.write_text(TICKET, encoding="utf-8")

        if repository:
            git(self.project, "init", "--initial-branch=main")
            git(self.project, "config", "user.email", "t@example.invalid")
            git(self.project, "config", "user.name", "T")
            if ignore_docs:
                (self.project / ".gitignore").write_text("docs/\n", encoding="utf-8")
                git(self.project, "add", ".gitignore")
            else:
                git(self.project, "add", ".")
            git(self.project, "commit", "-m", "initial")

        self.wiki = root / "wiki"
        self.wiki.mkdir()
        scaffold(self.wiki, "Fixture")
        write_binding(self.wiki, self.project)
        ingest(self.wiki, AUTOPILOT)
        build(self.wiki)

    def results(self) -> dict:
        return {result.name: result for result in run_passes(self.wiki)}

    def issues(self) -> dict[str, list[str]]:
        return {name: result.issues for name, result in self.results().items()}

    def errors(self) -> dict[str, list[str]]:
        return {
            name: result.issues
            for name, result in self.results().items()
            if result.issues and result.severity == ERROR
        }

    def page(self, stem: str) -> Path:
        return self.wiki / "wiki" / "sources" / f"{stem}.md"

    def only(self, test: unittest.TestCase, pass_name: str) -> list[str]:
        """Assert exactly one pass fires, and hand back its issues."""

        firing = {name: issues for name, issues in self.issues().items() if issues}
        test.assertEqual([pass_name], sorted(firing), firing)
        return firing[pass_name]


class DriftTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temporary, True)
        self.fixture = Fixture(Path(self.temporary))


class CleanFixtureTests(DriftTestCase):
    def test_a_freshly_ingested_wiki_reports_no_error_at_all(self) -> None:
        """Criterion 6: a clean state has to be reachable, or the lint is decoration."""

        self.assertEqual({}, self.fixture.errors())

    def test_a_freshly_ingested_wiki_reports_nothing_at_all(self) -> None:
        firing = {name: issues for name, issues in self.fixture.issues().items() if issues}

        self.assertEqual({}, firing)

    def test_every_drift_pass_actually_ran(self) -> None:
        """A pass that is absent looks exactly like a pass that is green."""

        for name in (
            "dangling-source",
            "stale-page",
            "duplicate-identity",
            "provenance-validity",
            "timeline-coverage",
            "stale-session-pointer",
            "un-ingested-artefact",
        ):
            self.assertIn(name, self.fixture.results(), name)


class DanglingSourceTests(DriftTestCase):
    def test_it_fires_when_the_artefact_is_deleted_without_a_reingest(self) -> None:
        self.fixture.ticket.unlink()
        issues = self.fixture.only(self, "dangling-source")

        self.assertEqual(1, len(issues))
        self.assertIn("does not exist", issues[0])

    def test_it_stays_quiet_on_a_deliberate_tombstone(self) -> None:
        """A page marked missing is the record of a deletion, not a defect."""

        page = self.fixture.page("ticket-family-01")
        page.write_text(
            page.read_text(encoding="utf-8").replace(
                "source_status: present", "source_status: missing"
            ),
            encoding="utf-8",
        )
        self.fixture.ticket.unlink()

        self.assertEqual([], self.fixture.results()["dangling-source"].issues)

    def test_it_is_an_error(self) -> None:
        self.assertEqual(ERROR, self.fixture.results()["dangling-source"].severity)


class StalePageTests(DriftTestCase):
    def test_it_fires_when_the_artefact_is_edited_after_ingest(self) -> None:
        self.fixture.ticket.write_text(
            TICKET.replace("body", "body, revised"), encoding="utf-8"
        )
        issues = self.fixture.only(self, "stale-page")

        self.assertEqual(1, len(issues))
        self.assertIn("now digests to", issues[0])

    def test_it_does_not_fire_when_only_the_mtime_moved(self) -> None:
        """Content digests, never timestamps. That is the whole design."""

        before = source_digest(self.fixture.ticket)
        self.fixture.ticket.write_text(
            self.fixture.ticket.read_text(encoding="utf-8"), encoding="utf-8"
        )
        self.fixture.ticket.touch()

        self.assertEqual(before, source_digest(self.fixture.ticket))
        self.assertEqual([], self.fixture.results()["stale-page"].issues)

    def test_it_is_an_error(self) -> None:
        self.assertEqual(ERROR, self.fixture.results()["stale-page"].severity)


class UnIngestedArtefactTests(DriftTestCase):
    def test_it_fires_on_a_new_artefact_and_reports_it_as_informational(self) -> None:
        """The normal steady state. Reporting it as an error would train the reader to skip."""

        (self.fixture.project / "docs" / "specs" / "later.md").write_text(
            "# Later\n", encoding="utf-8"
        )
        result = self.fixture.results()["un-ingested-artefact"]

        self.assertEqual(1, len(result.issues))
        self.assertIn("docs/specs/later.md", result.issues[0])
        self.assertEqual(INFO, result.severity)
        self.assertEqual({}, self.fixture.errors())


class DuplicateIdentityTests(DriftTestCase):
    def test_it_catches_two_pages_minted_across_a_disposition_move(self) -> None:
        """The concrete corruption the identity contract exists to prevent."""

        original = self.fixture.page("ticket-family-01")
        done = self.fixture.project / "docs" / "tickets" / "family" / "done"
        done.mkdir()
        moved = done / "01-slice.md"
        self.fixture.ticket.rename(moved)

        # The page a path-derived name would have produced, beside the identity-derived one.
        duplicate = self.fixture.page("docs-tickets-family-done-01-slice")
        duplicate.write_text(
            original.read_text(encoding="utf-8").replace(
                "source_path: docs/tickets/family/01-slice.md",
                "source_path: docs/tickets/family/done/01-slice.md",
            ),
            encoding="utf-8",
        )
        original.write_text(
            original.read_text(encoding="utf-8").replace(
                "source_path: docs/tickets/family/01-slice.md",
                "source_path: docs/tickets/family/done/01-slice.md",
            ),
            encoding="utf-8",
        )
        result = self.fixture.results()["duplicate-identity"]

        self.assertEqual(1, len(result.issues))
        self.assertIn("ticket:family/01", result.issues[0])
        self.assertIn("2 pages", result.issues[0])
        self.assertEqual(ERROR, result.severity)

    def test_it_stays_quiet_when_one_identity_has_one_page(self) -> None:
        self.assertEqual([], self.fixture.results()["duplicate-identity"].issues)


class ProvenanceValidityTests(DriftTestCase):
    def _rewrite(self, old: str, new: str) -> list[str]:
        page = self.fixture.page("ticket-family-01")
        page.write_text(
            page.read_text(encoding="utf-8").replace(old, new), encoding="utf-8"
        )
        return self.fixture.results()["provenance-validity"].issues

    def test_it_fires_on_a_rung_the_ladder_does_not_have(self) -> None:
        issues = self._rewrite("created_provenance: git-commit", "created_provenance: vibes")

        self.assertEqual(1, len(issues))
        self.assertIn("not a rung of the ladder", issues[0])

    def test_it_fires_on_a_date_with_no_witness(self) -> None:
        issues = self._rewrite("created_provenance: git-commit", "created_provenance: unknown")

        self.assertEqual(1, len(issues))
        self.assertIn("has no witness", issues[0])

    def test_it_fires_on_a_witness_with_no_date(self) -> None:
        issues = self._rewrite(
            "disposition_changed_provenance: unknown",
            "disposition_changed_provenance: git-rename",
        )

        self.assertEqual(1, len(issues))
        self.assertIn("a witness is claimed for nothing", issues[0])

    def test_it_fires_when_the_rung_field_is_gone_entirely(self) -> None:
        page = self.fixture.page("ticket-family-01")
        page.write_text(
            "\n".join(
                line
                for line in page.read_text(encoding="utf-8").splitlines()
                if not line.startswith("created_provenance:")
            ),
            encoding="utf-8",
        )
        issues = self.fixture.results()["provenance-validity"].issues

        self.assertEqual(1, len(issues))
        self.assertIn("has no `created_provenance`", issues[0])

    def test_an_mtime_date_is_valid_and_never_reported(self) -> None:
        """The no-Git constraint. On an untracked project mtime is the only rung there is."""

        issues = self._rewrite("created_provenance: git-commit", "created_provenance: mtime")

        self.assertEqual([], issues)

    def test_it_fires_on_a_date_that_is_not_a_date(self) -> None:
        issues = self._rewrite("created: 20", "created: not-a-date\nunused: 20")

        self.assertTrue(any("not an ISO date" in issue for issue in issues), issues)


class TimelineCoverageTests(DriftTestCase):
    def test_it_fires_when_a_ticket_has_no_lifecycle_record(self) -> None:
        for record in (self.fixture.wiki / "wiki" / "timeline" / "tickets").glob("*.md"):
            record.unlink()
        result = self.fixture.results()["timeline-coverage"]

        self.assertTrue(
            any("no lifecycle record" in issue for issue in result.issues), result.issues
        )
        self.assertEqual(WARNING, result.severity)

    def test_it_fires_when_a_dated_page_has_no_period(self) -> None:
        for period in (self.fixture.wiki / "wiki" / "timeline").glob("2*.md"):
            period.unlink()
        issues = self.fixture.results()["timeline-coverage"].issues

        self.assertTrue(any("there is no page for" in issue for issue in issues), issues)

    def test_it_fires_when_the_axis_was_never_built(self) -> None:
        shutil.rmtree(self.fixture.wiki / "wiki" / "timeline")
        issues = self.fixture.results()["timeline-coverage"].issues

        self.assertEqual(1, len(issues))
        self.assertIn("never been built", issues[0])


class SessionPointerTests(DriftTestCase):
    def _pointer(self, size: int) -> Path:
        transcript = Path(self.temporary) / "session.jsonl"
        transcript.write_text("x" * size, encoding="utf-8")
        pointer = self.fixture.page("session-ref")
        pointer.write_text(
            "---\n"
            "kind: ref\n"
            "provider: claude-code\n"
            "session_id: abc\n"
            f"external_path: {transcript.as_posix()}\n"
            f"size_bytes: {size}\n"
            "record_count: 3\n"
            "---\n\n# Session abc\n\nbody\n",
            encoding="utf-8",
        )
        return transcript

    def test_it_fires_when_the_transcript_grew(self) -> None:
        transcript = self._pointer(10)
        transcript.write_text("x" * 40, encoding="utf-8")
        result = self.fixture.results()["stale-session-pointer"]

        self.assertEqual(1, len(result.issues))
        self.assertIn("grew from 10 to 40", result.issues[0])
        self.assertEqual(WARNING, result.severity)

    def test_it_fires_when_the_transcript_is_gone(self) -> None:
        self._pointer(10).unlink()
        issues = self.fixture.results()["stale-session-pointer"].issues

        self.assertEqual(1, len(issues))
        self.assertIn("is gone", issues[0])

    def test_it_stays_quiet_on_a_byte_identical_transcript(self) -> None:
        transcript = self._pointer(10)
        transcript.write_text(transcript.read_text(encoding="utf-8"), encoding="utf-8")

        self.assertEqual([], self.fixture.results()["stale-session-pointer"].issues)


class NoGitTests(unittest.TestCase):
    """The supported configurations a git-assuming lint would break on."""

    def test_a_host_with_no_repository_reports_no_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary), repository=False)
            errors = fixture.errors()
            results = fixture.results()

        self.assertEqual({}, errors)
        self.assertIn("provenance-validity", results)
        self.assertEqual([], results["provenance-validity"].issues)

    def test_an_untracked_docs_tree_reports_no_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary), ignore_docs=True)
            errors = fixture.errors()

        self.assertEqual({}, errors)

    def test_the_binding_is_required_before_the_drift_passes_apply(self) -> None:
        """No binding is not drift either. One informational line, never seven green passes."""

        with tempfile.TemporaryDirectory() as temporary:
            wiki = Path(temporary) / "wiki"
            wiki.mkdir()
            scaffold(wiki, "Unbound")
            results = {result.name: result for result in run_passes(wiki)}

        self.assertIn("project-drift", results)
        self.assertEqual(INFO, results["project-drift"].severity)
        self.assertNotIn("stale-page", results)


class FixProposalTests(DriftTestCase):
    def test_every_pass_proposes_a_repair(self) -> None:
        """Propose, confirm, apply. A finding with no proposed repair stalls at 'propose'."""

        without = [
            result.name for result in run_passes(self.fixture.wiki) if not result.fix
        ]

        self.assertEqual([], without)


if __name__ == "__main__":
    unittest.main()
