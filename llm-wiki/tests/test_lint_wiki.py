"""Scaffold and lint, against the single layout.

Every lint pass gets a seeded defect. A pass that cannot fail is worse than no pass: it
reports green and a reader believes it.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from lint_wiki import (  # noqa: E402
    LAYOUT_DIRECTORIES,
    LAYOUT_FILES,
    lint,
    run_passes,
)
from scaffold import DIRECTORIES, scaffold  # noqa: E402

AUDIT_ENTRY = """---
id: 20260826-101500-demo
target: concepts/thing.md
target_lines: [4, 6]
anchor_before: "before"
anchor_text: "the claim"
anchor_after: "after"
severity: warn
author: carlo
source: manual
created: 2026-08-26T10:15:00Z
status: open
---

# Comment

The count is wrong.
"""


def passes(root: Path) -> dict[str, list[str]]:
    """Pass name to its issues, so a test can name the pass it seeded."""

    return {result.name: result.issues for result in run_passes(root)}


class ScaffoldTests(unittest.TestCase):
    def test_a_fresh_scaffold_lints_clean(self) -> None:
        """The bar this ticket exists to clear: a new wiki passes its own lint.

        One informational finding is expected and correct: an unbound wiki has no project, so
        the drift passes say they do not apply rather than reporting green.
        """

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "wiki"
            root.mkdir()
            scaffold(root, "Smoke Test")
            results = {result.name: result for result in run_passes(root)}
            reported = {
                name: result.issues
                for name, result in results.items()
                if result.issues and result.severity != "info"
            }

            self.assertEqual({}, reported)
            self.assertEqual(["project-drift"], [
                name for name, result in results.items() if result.issues
            ])
            self.assertEqual(0, lint(root))

    def test_scaffold_creates_exactly_the_layout_lint_enforces(self) -> None:
        """One layout. The two lists are the same list or the wiki cannot pass."""

        self.assertEqual(sorted(LAYOUT_DIRECTORIES), sorted(DIRECTORIES))

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "wiki"
            root.mkdir()
            scaffold(root, "Smoke Test")
            for relative in LAYOUT_DIRECTORIES:
                self.assertTrue((root / relative).is_dir(), relative)
            for relative in LAYOUT_FILES:
                self.assertTrue((root / relative).is_file(), relative)

    def test_scaffold_creates_nothing_the_retired_layout_had(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "wiki"
            root.mkdir()
            scaffold(root, "Smoke Test")
            for retired in (
                "CLAUDE.md",
                "log",
                "outputs",
                "raw/articles",
                "raw/papers",
                "raw/notes",
                "wiki/summaries",
            ):
                self.assertFalse((root / retired).exists(), retired)

    def test_scaffold_does_not_overwrite_an_existing_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "wiki"
            root.mkdir()
            scaffold(root, "Smoke Test")
            (root / "purpose.md").write_text("# Mine\n", encoding="utf-8")
            written = scaffold(root, "Smoke Test")

            self.assertEqual([], written)
            self.assertEqual("# Mine\n", (root / "purpose.md").read_text(encoding="utf-8"))

    def test_scaffold_records_the_binding_when_given_a_project(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "wiki"
            root.mkdir()
            project = Path(temporary) / "project"
            project.mkdir()
            written = scaffold(root, "Smoke Test", project)

            self.assertIn("llm-wiki-project.json", written)
            self.assertTrue((root / "llm-wiki-project.json").is_file())


class SeededDefectTests(unittest.TestCase):
    """One defect per pass. Each asserts its own pass fires and stays specific."""

    def setUp(self) -> None:
        self.temporary = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temporary, True)
        self.root = Path(self.temporary) / "wiki"
        self.root.mkdir()
        scaffold(self.root, "Seeded")

    def _page(self, relative: str, body: str) -> None:
        target = self.root / "wiki" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")

    def _index(self, *entries: str) -> None:
        index = self.root / "wiki" / "index.md"
        index.write_text(
            index.read_text(encoding="utf-8") + "\n" + "\n".join(entries) + "\n",
            encoding="utf-8",
        )

    def test_layout_fires_on_a_missing_directory(self) -> None:
        shutil.rmtree(self.root / "wiki" / "timeline" / "tickets")
        issues = passes(self.root)["layout"]

        self.assertEqual(1, len(issues))
        self.assertIn("wiki/timeline/tickets/", issues[0])

    def test_layout_fires_on_a_missing_file(self) -> None:
        (self.root / "schema.md").unlink()
        issues = passes(self.root)["layout"]

        self.assertEqual(1, len(issues))
        self.assertIn("schema.md", issues[0])

    def test_dead_wikilinks_fires_on_a_link_with_no_page(self) -> None:
        self._page("concepts/real.md", "# Real\n\nSee [[concepts/absent]].\n")
        self._index("- [[concepts/real]] — a page")
        result = passes(self.root)

        self.assertEqual(1, len(result["dead-wikilinks"]))
        self.assertIn("concepts/absent", result["dead-wikilinks"][0])
        self.assertEqual([], result["index-drift"])

    def test_orphan_pages_fires_on_a_page_nothing_links_to(self) -> None:
        self._page("concepts/lonely.md", "# Lonely\n\nNo one links here.\n")
        self._index("- [[concepts/lonely]] — a page")
        result = passes(self.root)

        self.assertEqual(1, len(result["orphan-pages"]))
        self.assertIn("lonely", result["orphan-pages"][0])
        self.assertEqual([], result["dead-wikilinks"])

    def test_being_listed_in_the_index_does_not_rescue_a_page_from_orphan(self) -> None:
        """Otherwise the orphan pass is a duplicate of index coverage and never fires."""

        self._page("concepts/lonely.md", "# Lonely\n\nNothing cites this.\n")
        self._index("- [[concepts/lonely]] — listed, still uncited")
        result = passes(self.root)

        self.assertEqual([], result["index-drift"])
        self.assertEqual(1, len(result["orphan-pages"]))

    def test_index_drift_fires_on_a_page_in_no_catalog(self) -> None:
        self._page("concepts/hub.md", "# Hub\n\nSee [[concepts/leaf]].\n")
        self._page("concepts/leaf.md", "# Leaf\n\nSee [[concepts/hub]].\n")
        self._index("- [[concepts/hub]] — indexed")
        result = passes(self.root)

        self.assertEqual(1, len(result["index-drift"]))
        self.assertIn("leaf", result["index-drift"][0])
        self.assertEqual([], result["dead-wikilinks"])
        self.assertEqual([], result["orphan-pages"])

    def test_the_log_is_never_treated_as_an_indexable_page(self) -> None:
        """wiki/log.md is machinery. Demanding an index entry for it is the old bug."""

        result = passes(self.root)

        self.assertEqual([], result["index-drift"])
        self.assertEqual([], result["orphan-pages"])

    def test_unlinked_concepts_fires_at_three_links_and_not_at_two(self) -> None:
        for count, expected in ((2, 0), (3, 1)):
            with self.subTest(links=count):
                self._page(
                    "concepts/hub.md",
                    "# Hub\n\n" + "See [[ghost]].\n" * count + "\n[[concepts/hub]]\n",
                )
                self._index("- [[concepts/hub]] — indexed")
                self.assertEqual(expected, len(passes(self.root)["unlinked-concepts"]))

    def test_log_shape_fires_on_a_missing_log(self) -> None:
        (self.root / "wiki" / "log.md").unlink()
        issues = passes(self.root)["log-shape"]

        self.assertEqual(1, len(issues))
        self.assertIn("wiki/log.md", issues[0])

    def test_log_shape_fires_when_the_log_is_not_newest_first(self) -> None:
        (self.root / "wiki" / "log.md").write_text(
            "# Log — Seeded\n\n## 2026-08-01\n\n- 09:00 lint — early\n\n"
            "## 2026-08-26\n\n- 10:00 lint — later\n",
            encoding="utf-8",
        )
        issues = passes(self.root)["log-shape"]

        self.assertEqual(1, len(issues))
        self.assertIn("newest first", issues[0])

    def test_log_shape_fires_on_an_unknown_operation(self) -> None:
        log = self.root / "wiki" / "log.md"
        log.write_text(
            log.read_text(encoding="utf-8") + "- 11:00 teleport — not an operation\n",
            encoding="utf-8",
        )
        issues = passes(self.root)["log-shape"]

        self.assertEqual(1, len(issues))
        self.assertIn("teleport", issues[0])

    def test_log_shape_fires_on_an_entry_without_a_time(self) -> None:
        log = self.root / "wiki" / "log.md"
        log.write_text(
            log.read_text(encoding="utf-8") + "- lint — no time on this one\n",
            encoding="utf-8",
        )
        issues = passes(self.root)["log-shape"]

        self.assertEqual(1, len(issues))
        self.assertIn("HH:MM", issues[0])

    def test_log_shape_fires_on_a_date_that_is_not_a_date(self) -> None:
        log = self.root / "wiki" / "log.md"
        log.write_text(
            log.read_text(encoding="utf-8") + "\n## 2026-02-31\n\n- 12:00 lint — impossible\n",
            encoding="utf-8",
        )
        issues = passes(self.root)["log-shape"]

        self.assertTrue(any("not a real date" in issue for issue in issues), issues)

    def test_audit_shape_fires_on_a_missing_required_field(self) -> None:
        entry = AUDIT_ENTRY.replace("severity: warn\n", "")
        (self.root / "audit" / "a.md").write_text(entry, encoding="utf-8")
        issues = passes(self.root)["audit-shape"]

        self.assertEqual(1, len(issues))
        self.assertIn("severity", issues[0])

    def test_audit_shape_fires_on_an_invalid_severity(self) -> None:
        entry = AUDIT_ENTRY.replace("severity: warn", "severity: catastrophic")
        (self.root / "audit" / "a.md").write_text(entry, encoding="utf-8")
        issues = passes(self.root)["audit-shape"]

        self.assertEqual(1, len(issues))
        self.assertIn("catastrophic", issues[0])

    def test_audit_shape_fires_when_status_contradicts_the_directory(self) -> None:
        (self.root / "audit" / "resolved" / "a.md").write_text(
            AUDIT_ENTRY, encoding="utf-8"
        )
        issues = passes(self.root)["audit-shape"]

        self.assertEqual(1, len(issues))
        self.assertIn("does not match its directory", issues[0])

    def test_audit_shape_fires_on_a_file_with_no_front_matter(self) -> None:
        (self.root / "audit" / "a.md").write_text("just prose\n", encoding="utf-8")
        issues = passes(self.root)["audit-shape"]

        self.assertEqual(1, len(issues))
        self.assertIn("missing YAML frontmatter", issues[0])

    def test_the_audit_readme_is_not_mistaken_for_a_correction(self) -> None:
        """It ships with the scaffold and has no front matter. Flagging it is noise."""

        self.assertTrue((self.root / "audit" / "README.md").is_file())
        self.assertEqual([], passes(self.root)["audit-shape"])

    def test_audit_targets_fires_when_an_open_audit_points_nowhere(self) -> None:
        (self.root / "audit" / "a.md").write_text(AUDIT_ENTRY, encoding="utf-8")
        result = passes(self.root)

        self.assertEqual([], result["audit-shape"])
        self.assertEqual(1, len(result["audit-targets"]))
        self.assertIn("concepts/thing.md", result["audit-targets"][0])

    def test_audit_targets_is_green_once_the_target_exists(self) -> None:
        (self.root / "audit" / "a.md").write_text(AUDIT_ENTRY, encoding="utf-8")
        self._page("concepts/thing.md", "# Thing\n\n[[concepts/thing]]\n")
        self._index("- [[concepts/thing]] — indexed")

        self.assertEqual([], passes(self.root)["audit-targets"])


class AuditReviewTests(unittest.TestCase):
    """audit_review.py is kept, not dead code that appears to be running."""

    def test_audit_review_groups_an_open_entry_and_skips_the_readme(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "wiki"
            root.mkdir()
            scaffold(root, "Seeded")
            (root / "audit" / "a.md").write_text(AUDIT_ENTRY, encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, "-B", str(SCRIPTS / "audit_review.py"), str(root), "--open"],
                capture_output=True, text=True, encoding="utf-8", check=True,
            )

        self.assertIn("OPEN audits: 1 across 1 target files", completed.stdout)
        self.assertIn("concepts/thing.md", completed.stdout)
        self.assertIn("The count is wrong.", completed.stdout)
        self.assertNotIn("README", completed.stderr)


if __name__ == "__main__":
    unittest.main()
