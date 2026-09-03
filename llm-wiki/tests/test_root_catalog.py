from __future__ import annotations

import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from project_binding import write_binding  # noqa: E402
from root_catalog import (  # noqa: E402
    OWNERS,
    PROJECT_SOURCES,
    SESSION_SOURCES,
    TIMELINE,
    CatalogAdoptionSpan,
    CatalogOwnershipError,
    adopt_catalog_file,
    catalog_block,
    parse_catalog,
    update_catalog,
)
from scaffold import scaffold  # noqa: E402
from sync_project import sync_project  # noqa: E402

AUTOPILOT = SKILL_ROOT.parent / "ticket-autopilot"


class RootCatalogOwnershipTests(unittest.TestCase):
    def test_updates_owned_blocks_and_preserves_every_manual_byte(self) -> None:
        # Use non-ASCII UTF-8 and mixed newline shapes so preservation is measured
        # than an invalid byte. These spans belong to the human and must survive exactly.
        manual_before = "# Human index\r\n\r\n## Concepts\r\n- café\r\n\r\n"
        manual_between = "## Entities\n- Δ entity\n\n"
        manual_after = "## Open work\r- preserve me\r"
        original = (
            manual_before
            + catalog_block("project-sources", "stale project\n")
            + manual_between
            + catalog_block("session-sources", "stale session\n")
            + catalog_block("timeline", "stale timeline\n")
            + manual_after
        )

        updated = update_catalog(
            original,
            {
                "project-sources": "fresh project\n",
                "session-sources": "fresh session\n",
                "timeline": "fresh timeline\n",
            },
        )

        self.assertIn(manual_before, updated)
        self.assertIn(manual_between, updated)
        self.assertIn(manual_after, updated)
        self.assertLess(updated.index(manual_before), updated.index(manual_between))
        self.assertLess(updated.index(manual_between), updated.index(manual_after))
        self.assertNotIn("stale", updated)
        self.assertEqual(updated, update_catalog(updated, {
            "project-sources": "fresh project\n",
            "session-sources": "fresh session\n",
            "timeline": "fresh timeline\n",
        }))

    def test_missing_duplicate_malformed_nested_and_conflicting_boundaries_fail(self) -> None:
        valid = "# Index\n\n" + "".join(catalog_block(owner, "") for owner in OWNERS)
        cases = {
            "headings-only": "# Index\n\n## Spec sources\n\n## Session sources\n\n## Timeline\n",
            "missing": valid.replace(catalog_block("timeline", ""), ""),
            "duplicated": valid + catalog_block("timeline", ""),
            "malformed": valid.replace(
                "<!-- llm-wiki:catalog:start:timeline -->",
                "<!-- llm-wiki:catalog start timeline -->",
            ),
            "nested": valid.replace(
                "<!-- llm-wiki:catalog:end:project-sources -->",
                "<!-- llm-wiki:catalog:start:session-sources -->\n"
                "<!-- llm-wiki:catalog:end:project-sources -->",
            ),
            "conflicting": valid.replace(
                "<!-- llm-wiki:catalog:end:project-sources -->",
                "<!-- llm-wiki:catalog:end:timeline -->",
            ),
        }

        for label, text in cases.items():
            with self.subTest(label=label), self.assertRaises(CatalogOwnershipError):
                update_catalog(text, {"project-sources": "new\n"})


class RootCatalogSyncTests(unittest.TestCase):
    @staticmethod
    def _file_state(root: Path) -> dict[str, tuple[bytes, int]]:
        return {
            path.relative_to(root).as_posix(): (path.read_bytes(), path.stat().st_mtime_ns)
            for path in root.rglob("*")
            if path.is_file() and not path.is_symlink()
        }

    @staticmethod
    def _fixture(root: Path) -> tuple[Path, Path]:
        project = root / "project"
        (project / "docs" / "specs").mkdir(parents=True)
        (project / "docs" / "specs" / "alpha.md").write_text(
            "# Alpha\n\nOne project decision.\n", encoding="utf-8"
        )
        wiki = project / "knowledge"
        scaffold(wiki, "Fixture", project)
        write_binding(wiki, project)
        return project, wiki

    @staticmethod
    def _seed_manual_sections(index: Path) -> tuple[bytes, ...]:
        manual = (
            b"## Concepts\r\n\r\n- durable concept\r\n\r\n",
            b"## Entities\n\n- durable entity\n\n",
            b"## Open work\r\n\r\n- durable frontier\r\n",
        )
        data = index.read_bytes()
        project_start = f"<!-- llm-wiki:catalog:start:{PROJECT_SOURCES} -->\n".encode()
        project_end = f"<!-- llm-wiki:catalog:end:{PROJECT_SOURCES} -->\n".encode()
        timeline_end = f"<!-- llm-wiki:catalog:end:{TIMELINE} -->\n".encode()
        data = data.replace(project_start, manual[0] + project_start, 1)
        data = data.replace(project_end, project_end + manual[1], 1)
        data = data.replace(timeline_end, timeline_end + manual[2], 1)
        index.write_bytes(data)
        return manual

    def test_sync_preserves_manual_bytes_updates_owned_entries_and_replays_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project, wiki = self._fixture(Path(temporary))
            first = sync_project(project, autopilot_root=AUTOPILOT)
            self.assertEqual("updated-directly", first["status"])
            index = wiki / "wiki" / "index.md"
            manual = self._seed_manual_sections(index)
            (wiki / "wiki" / "sources" / "session-manual.md").write_text(
                "---\ntype: session\nprovider: test\nsession_id: manual\n"
                "span: 2026-09-02\nrecord_count: 1\ntickets_touched: []\n"
                "source_status: complete\n---\n\n# Manual session\n",
                encoding="utf-8",
            )
            (project / "docs" / "specs" / "alpha.md").unlink()
            (project / "docs" / "specs" / "beta.md").write_text(
                "# Beta\n\nReplacement project decision.\n", encoding="utf-8"
            )

            changed = sync_project(project, autopilot_root=AUTOPILOT)
            changed_index = index.read_bytes()
            before_replay = self._file_state(wiki)
            replay = sync_project(project, autopilot_root=AUTOPILOT)
            after_replay = self._file_state(wiki)

        self.assertEqual(
            ("updated-directly", "internal-untracked"),
            (changed["status"], changed["reason"]),
        )
        self.assertIn("wiki/index.md", changed["changed_paths"])
        self.assertNotEqual(
            changed["candidate_ref"]["base_tree_sha256"],
            changed["candidate_ref"]["candidate_tree_sha256"],
        )
        self.assertTrue(
            all(check["result"] == "pass" for check in changed["validation_receipt"]["checks"])
        )
        positions = [changed_index.index(block) for block in manual]
        self.assertEqual(sorted(positions), positions)
        self.assertIn(b"[[sources/session-manual]]", changed_index)
        self.assertIn(b"## Removed sources", changed_index)
        self.assertIn(b"[[timeline/index]]", changed_index)
        self.assertEqual(1, changed_index.count(b"[[sources/path-docs-specs-beta-md]]"))
        self.assertEqual(("unchanged", "no-diff"), (replay["status"], replay["reason"]))
        self.assertEqual([], replay["changed_paths"])
        self.assertEqual(
            replay["candidate_ref"]["base_tree_sha256"],
            replay["candidate_ref"]["candidate_tree_sha256"],
        )
        self.assertEqual(before_replay, after_replay)

    def test_invalid_boundaries_fail_before_protected_sync_application(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project, wiki = self._fixture(Path(temporary))
            sync_project(project, autopilot_root=AUTOPILOT)
            index = wiki / "wiki" / "index.md"
            index.write_text(
                index.read_text(encoding="utf-8") + catalog_block(SESSION_SOURCES, ""),
                encoding="utf-8",
            )
            (project / "docs" / "specs" / "beta.md").write_text(
                "# Beta\n\nWould require compilation.\n", encoding="utf-8"
            )
            protected = self._file_state(wiki)

            result = sync_project(project, autopilot_root=AUTOPILOT)
            after = self._file_state(wiki)

        self.assertEqual(("failed", "compile"), (result["status"], result["reason"]))
        self.assertIn("duplicates generated owner", result["detail"])
        self.assertEqual(protected, after)

    def test_tracked_legacy_catalog_requires_adoption_then_yields_a_stable_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project, wiki = self._fixture(root)
            index = wiki / "wiki" / "index.md"
            parts = (
                b"# Index\n\n> Exact legacy project catalog.\n\n## Spec sources\n\n- stale\n\n",
                b"## Session sources\n\n- stale session\n\n",
                b"## Timeline\n\n- stale timeline\n",
            )
            legacy = b"".join(parts)
            first = len(parts[0])
            second = first + len(parts[1])
            spans = (
                CatalogAdoptionSpan(PROJECT_SOURCES, 0, first),
                CatalogAdoptionSpan(SESSION_SOURCES, first, second),
                CatalogAdoptionSpan(TIMELINE, second, len(legacy)),
            )
            index.write_bytes(legacy)
            expected = hashlib.sha256(legacy).hexdigest()
            subprocess.run(
                ["git", "init", "--initial-branch=main"], cwd=project, check=True,
                capture_output=True, text=True,
            )
            subprocess.run(
                ["git", "config", "user.email", "test@example.invalid"], cwd=project,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test"], cwd=project, check=True,
            )
            subprocess.run(["git", "add", "."], cwd=project, check=True)
            subprocess.run(
                ["git", "commit", "-m", "legacy catalog"], cwd=project, check=True,
                capture_output=True, text=True,
            )
            protected_legacy = self._file_state(wiki)

            rejected = sync_project(project, autopilot_root=AUTOPILOT)
            self.assertEqual(("failed", "compile"), (rejected["status"], rejected["reason"]))
            self.assertIn("missing generated ownership boundaries", rejected["detail"])
            self.assertEqual(protected_legacy, self._file_state(wiki))

            adoption = adopt_catalog_file(index, expected, spans)
            subprocess.run(["git", "add", "knowledge/wiki/index.md"], cwd=project, check=True)
            subprocess.run(
                ["git", "commit", "-m", "adopt catalog"], cwd=project, check=True,
                capture_output=True, text=True,
            )
            protected_adopted = self._file_state(wiki)
            result = sync_project(project, autopilot_root=AUTOPILOT)
            replay = sync_project(project, autopilot_root=AUTOPILOT)
            adoption_replay = adopt_catalog_file(index, expected, spans)
            after_state = self._file_state(wiki)
            frozen_index = Path(result["candidate_path"]) / "wiki" / "index.md"
            frozen_owners = set(parse_catalog(frozen_index.read_text(encoding="utf-8")))

        self.assertEqual("adopted", adoption["status"])
        self.assertEqual(
            ("candidate-created", "manual-authorization"),
            (result["status"], result["reason"]),
        )
        self.assertEqual(result["candidate_ref"], replay["candidate_ref"])
        self.assertEqual(result["candidate_path"], replay["candidate_path"])
        self.assertEqual(protected_adopted, after_state)
        self.assertEqual("unchanged", adoption_replay["status"])
        self.assertEqual(set(OWNERS), frozen_owners)


if __name__ == "__main__":
    unittest.main()
