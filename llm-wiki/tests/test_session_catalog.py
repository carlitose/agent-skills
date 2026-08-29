from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from ingest_docs import Artefact, _write_index  # noqa: E402
from lint_wiki import run_passes  # noqa: E402
from scaffold import scaffold  # noqa: E402
from session_catalog import (  # noqa: E402
    SessionCatalogError,
    refresh_session_catalog,
    render_session_catalog,
    session_entries,
)


def write_session(root: Path, name: str, title: str) -> Path:
    sources = root / "wiki" / "sources"
    sources.mkdir(parents=True, exist_ok=True)
    path = sources / f"session-{name}.md"
    path.write_text(
        f"---\ntype: session\nsession_id: {name}\n---\n\n# {title}\n",
        encoding="utf-8",
    )
    return path


class SessionSectionTests(unittest.TestCase):
    def test_render_repairs_duplicates_and_keeps_stable_order(self) -> None:
        index = """# Index

## Spec sources

- [[sources/spec]] — Spec

## Session sources

- [[sources/session-z]] — stale
- [[sources/session-z]] — duplicate

## Timeline

- [[timeline/index]] — Timeline
"""
        rendered = render_session_catalog(
            index,
            [
                "- [[sources/session-a]] — Session A",
                "- [[sources/session-z]] — Session Z",
            ],
        )

        self.assertEqual(1, rendered.count("## Session sources"))
        self.assertEqual(1, rendered.count("[[sources/session-a]]"))
        self.assertEqual(1, rendered.count("[[sources/session-z]]"))
        self.assertLess(
            rendered.index("[[sources/session-a]]"),
            rendered.index("[[sources/session-z]]"),
        )
        self.assertLess(
            rendered.index("## Session sources"), rendered.index("## Timeline")
        )
        self.assertIn("[[sources/spec]]", rendered)

    def test_refresh_is_idempotent_and_removes_a_missing_page(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "knowledge"
            scaffold(root, "Catalog test")
            first = write_session(root, "a", "Session A")
            second = write_session(root, "b", "Session B")

            self.assertTrue(refresh_session_catalog(root))
            before = (root / "wiki" / "index.md").read_bytes()
            self.assertFalse(refresh_session_catalog(root))
            self.assertEqual(before, (root / "wiki" / "index.md").read_bytes())

            second.unlink()
            self.assertTrue(refresh_session_catalog(root))
            text = (root / "wiki" / "index.md").read_text(encoding="utf-8")

        self.assertIn(f"[[sources/{first.stem}]]", text)
        self.assertNotIn(f"[[sources/{second.stem}]]", text)

    def test_a_symlinked_sources_directory_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "knowledge"
            scaffold(root, "Catalog test")
            external = Path(temporary) / "external"
            external.mkdir()
            (external / "session-outside.md").write_text(
                "# Outside\n", encoding="utf-8"
            )
            sources = root / "wiki" / "sources"
            sources.rmdir()
            sources.symlink_to(external, target_is_directory=True)

            with self.assertRaisesRegex(SessionCatalogError, "is a symlink"):
                session_entries(root)

    def test_session_entries_ignore_symlinks_and_use_page_titles(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "knowledge"
            scaffold(root, "Catalog test")
            page = write_session(root, "real", "Human title")
            link = page.with_name("session-link.md")
            link.symlink_to(page.name)
            entries = session_entries(root)

        self.assertEqual(
            [f"- [[sources/{page.stem}]] — Human title"], entries
        )


class SharedIndexOwnershipTests(unittest.TestCase):
    def test_project_docs_rebuild_preserves_session_entries_and_timeline(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "knowledge"
            scaffold(root, "Shared index test")
            session = write_session(root, "codex-demo", "Codex demo")
            timeline = root / "wiki" / "timeline" / "index.md"
            timeline.write_text("# Timeline\n", encoding="utf-8")
            artefact = Artefact(
                relative_path="docs/specs/map.md",
                identity_key="artifact:map",
                kind="spec",
                digest="sha256:" + "a" * 64,
                disposition="not-applicable",
                title="The map",
            )

            _write_index(root, {artefact.identity_key: artefact}, {})
            first = (root / "wiki" / "index.md").read_bytes()
            _write_index(root, {artefact.identity_key: artefact}, {})
            second = (root / "wiki" / "index.md").read_bytes()
            text = second.decode("utf-8")

        self.assertEqual(first, second)
        self.assertEqual(1, text.count(f"[[sources/{session.stem}]]"))
        self.assertEqual(1, text.count("[[sources/artifact-map]]"))
        self.assertEqual(1, text.count("[[timeline/index]]"))

    def test_cataloged_session_pages_have_no_index_drift_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "knowledge"
            scaffold(root, "Lint integration")
            write_session(root, "one", "Session one")
            write_session(root, "two", "Session two")
            refresh_session_catalog(root)
            results = {result.name: result.issues for result in run_passes(root)}

        self.assertEqual([], results["index-drift"])


if __name__ == "__main__":
    unittest.main()
