from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
AUTOPILOT = SKILL_ROOT.parent / "ticket-autopilot"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import sync_project as sync_module  # noqa: E402
from project_binding import write_binding  # noqa: E402
from scaffold import scaffold  # noqa: E402
from sync_project import CONTRACT_VERSION, normalize_request, sync_project  # noqa: E402


def git(root: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *arguments],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    return result.stdout.strip()


def make_project(base: Path) -> Path:
    project = base / "project"
    (project / "docs" / "specs").mkdir(parents=True)
    (project / "docs" / "specs" / "alpha.md").write_text(
        "# Alpha\n\nOne project decision.\n", encoding="utf-8"
    )
    return project


def make_wiki(project: Path, root: Path | None = None, *, auto_sync: str = "enabled") -> Path:
    wiki = root or project / "knowledge"
    scaffold(wiki, "Fixture", project)
    write_binding(wiki, project, auto_sync=auto_sync)
    return wiki


def file_state(root: Path) -> dict[str, tuple[bytes, int]]:
    return {
        path.relative_to(root).as_posix(): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in root.rglob("*")
        if path.is_file() and not path.is_symlink()
    }


class SyncProjectContractTests(unittest.TestCase):
    def test_request_normalization_is_order_independent_and_invalid_types_return_failure(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = make_project(Path(temporary))
            first = normalize_request(
                project,
                origin_kind="ticket-batch",
                origin_id="batch-1",
                triggers=("post-ticket-batch", "manual", "post-ticket-batch"),
            )
            second = normalize_request(
                project,
                origin_kind="ticket-batch",
                origin_id="batch-1",
                triggers=("manual", "post-ticket-batch"),
            )
            self.assertEqual(first, second)

            invalid = sync_project(
                project,
                origin_kind=7,  # type: ignore[arg-type]
                autopilot_root=AUTOPILOT,
            )
            self.assertEqual(
                ("failed", "broken-binding"),
                (invalid["status"], invalid["reason"]),
            )

    def test_absent_and_disabled_are_durable_skips(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = make_project(Path(temporary))
            absent = sync_project(project, autopilot_root=AUTOPILOT)
            self.assertEqual(("skipped", "absent"), (absent["status"], absent["reason"]))
            self.assertEqual(CONTRACT_VERSION, absent["contract_version"])
            self.assertIsNone(absent["wiki_identity"])

            wiki = make_wiki(project, auto_sync="disabled")
            before = file_state(wiki)
            disabled = sync_project(project, autopilot_root=AUTOPILOT)
            self.assertEqual(
                ("skipped", "disabled"),
                (disabled["status"], disabled["reason"]),
            )
            self.assertEqual(before, file_state(wiki))

    def test_internal_untracked_sync_is_direct_then_byte_for_byte_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = make_project(Path(temporary))
            wiki = make_wiki(project)
            events: list[str] = []

            first = sync_project(
                project,
                origin_kind="ticket-batch",
                origin_id="batch-7",
                triggers=("post-ticket-batch",),
                autopilot_root=AUTOPILOT,
                observer=events.append,
            )

            self.assertEqual("updated-directly", first["status"])
            self.assertEqual("internal-untracked", first["reason"])
            self.assertEqual(
                [
                    "discover",
                    "stage",
                    "ingest",
                    "timeline",
                    "scope",
                    "lint",
                    "compare-and-swap",
                    "publish",
                ],
                events,
            )
            self.assertIn("wiki/index.md", first["changed_paths"])
            self.assertIn("wiki/log.md", first["changed_paths"])
            self.assertEqual(
                "implementation-complete",
                first["validation_receipt"]["claim_ceiling"],
            )
            self.assertEqual(
                first["wiki_sync_ref"]["digest"],
                first["candidate_ref"]["wiki_sync_ref"],
            )
            before_replay = file_state(wiki)

            replay = sync_project(
                project,
                origin_kind="ticket-batch",
                origin_id="batch-7",
                triggers=("post-ticket-batch",),
                autopilot_root=AUTOPILOT,
            )

            self.assertEqual(("unchanged", "no-diff"), (replay["status"], replay["reason"]))
            self.assertEqual(before_replay, file_state(wiki), "unchanged must write zero bytes")

    def test_project_root_can_be_the_wiki_without_staging_or_rewriting_project_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = make_project(Path(temporary))
            source = project / "docs" / "specs" / "alpha.md"
            source_before = (source.read_bytes(), source.stat().st_mtime_ns)
            wiki = make_wiki(project, project)
            index = wiki / "wiki" / "index.md"
            index.chmod(0o600)
            unrelated = project / "unrelated.bin"
            unrelated.write_bytes(b"not part of the wiki")
            unrelated.chmod(0)

            try:
                result = sync_project(project, autopilot_root=AUTOPILOT)
            finally:
                unrelated.chmod(0o600)

            self.assertEqual("updated-directly", result["status"])
            self.assertEqual(source_before, (source.read_bytes(), source.stat().st_mtime_ns))
            self.assertEqual(0o600, index.stat().st_mode & 0o777)

    def test_internal_tracked_output_is_frozen_without_touching_the_wiki_or_git(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = make_project(Path(temporary))
            wiki = make_wiki(project)
            git(project, "init", "--initial-branch=main")
            git(project, "config", "user.email", "test@example.invalid")
            git(project, "config", "user.name", "Test")
            git(project, "add", ".")
            git(project, "commit", "-m", "fixture")
            head = git(project, "rev-parse", "HEAD")
            protected = file_state(wiki)

            result = sync_project(
                project,
                origin_kind="integrated-ticket",
                origin_id="WS-03",
                triggers=("post-integration",),
                autopilot_root=AUTOPILOT,
            )

            self.assertEqual(
                ("candidate-created", "manual-authorization"),
                (result["status"], result["reason"]),
            )
            self.assertEqual(protected, file_state(wiki))
            self.assertEqual(head, git(project, "rev-parse", "HEAD"))
            self.assertEqual("", git(project, "status", "--porcelain"))
            frozen = Path(result["candidate_path"])
            self.assertTrue((frozen / "manifest.json").is_file())
            manifest = json.loads((frozen / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(result["candidate_ref"], manifest["candidate_ref"])

            replay = sync_project(
                project,
                origin_kind="integrated-ticket",
                origin_id="WS-03",
                triggers=("post-integration",),
                autopilot_root=AUTOPILOT,
            )
            self.assertEqual(result["candidate_ref"], replay["candidate_ref"])
            self.assertEqual(result["candidate_path"], replay["candidate_path"])

            other_origin = sync_project(
                project,
                origin_kind="integrated-ticket",
                origin_id="WS-99",
                triggers=("post-integration",),
                autopilot_root=AUTOPILOT,
            )
            self.assertEqual("candidate-created", other_origin["status"])
            self.assertEqual(
                result["candidate_ref"]["candidate_tree_sha256"],
                other_origin["candidate_ref"]["candidate_tree_sha256"],
            )
            self.assertNotEqual(result["candidate_path"], other_origin["candidate_path"])
            self.assertTrue(Path(other_origin["candidate_path"]).is_dir())

    def test_external_wiki_is_updated_directly_even_when_its_own_git_tracks_it(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            project = make_project(base)
            wiki = make_wiki(project, base / "external-wiki")
            git(wiki, "init", "--initial-branch=main")
            git(wiki, "config", "user.email", "test@example.invalid")
            git(wiki, "config", "user.name", "Test")
            git(wiki, "add", ".")
            git(wiki, "commit", "-m", "wiki")
            head = git(wiki, "rev-parse", "HEAD")

            result = sync_project(project, [wiki], autopilot_root=AUTOPILOT)

            self.assertEqual(
                ("updated-directly", "external"),
                (result["status"], result["reason"]),
            )
            self.assertEqual(head, git(wiki, "rev-parse", "HEAD"))
            self.assertTrue(git(wiki, "status", "--porcelain"))

    def test_ambiguous_broken_and_partial_tracking_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            project = make_project(base)
            first = make_wiki(project, project / "one")
            second = make_wiki(project, project / "two")
            before = (file_state(first), file_state(second))
            ambiguous = sync_project(project, autopilot_root=AUTOPILOT)
            self.assertEqual("ambiguous-root", ambiguous["reason"])
            self.assertEqual(before, (file_state(first), file_state(second)))

        with tempfile.TemporaryDirectory() as temporary:
            project = make_project(Path(temporary))
            broken = Path(temporary) / "broken"
            broken.mkdir()
            (broken / "llm-wiki-project.json").write_text("{}\n", encoding="utf-8")
            result = sync_project(project, [broken], autopilot_root=AUTOPILOT)
            self.assertEqual(("failed", "broken-binding"), (result["status"], result["reason"]))

        with tempfile.TemporaryDirectory() as temporary:
            project = make_project(Path(temporary))
            wiki = make_wiki(project)
            git(project, "init", "--initial-branch=main")
            git(project, "config", "user.email", "test@example.invalid")
            git(project, "config", "user.name", "Test")
            git(project, "add", "docs", "knowledge/wiki/index.md")
            git(project, "commit", "-m", "partial")
            protected = file_state(wiki)
            result = sync_project(project, autopilot_root=AUTOPILOT)
            self.assertEqual("partial-tracking", result["reason"])
            self.assertEqual(protected, file_state(wiki))

    def test_forbidden_lint_stale_and_concurrent_fail_without_publishing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = make_project(Path(temporary))
            wiki = make_wiki(project)
            protected = file_state(wiki)
            original = sync_module.ingest_docs

            def mixed(stage: Path, autopilot: Path) -> dict[str, object]:
                report = original(stage, autopilot)
                (stage / "purpose.md").write_text(
                    "changed outside generated scope\n", encoding="utf-8"
                )
                return report

            with mock.patch.object(sync_module, "ingest_docs", side_effect=mixed):
                result = sync_project(project, autopilot_root=AUTOPILOT)
            self.assertEqual("forbidden-scope", result["reason"])
            self.assertEqual(protected, file_state(wiki))

        with tempfile.TemporaryDirectory() as temporary:
            project = make_project(Path(temporary))
            wiki = make_wiki(project)
            broken = wiki / "wiki" / "concepts" / "broken.md"
            broken.write_text("# Broken\n\n[[missing-page]]\n", encoding="utf-8")
            protected = file_state(wiki)
            result = sync_project(project, autopilot_root=AUTOPILOT)
            self.assertEqual("lint", result["reason"])
            self.assertEqual(protected, file_state(wiki))

        with tempfile.TemporaryDirectory() as temporary:
            project = make_project(Path(temporary))
            wiki = make_wiki(project)

            def race() -> None:
                with (wiki / "wiki" / "index.md").open("a", encoding="utf-8") as handle:
                    handle.write("\nExternal concurrent edit.\n")

            result = sync_project(project, autopilot_root=AUTOPILOT, before_publish=race)
            self.assertEqual(("failed", "stale-tree"), (result["status"], result["reason"]))
            self.assertEqual("retryable", result["retry"]["disposition"])

        with tempfile.TemporaryDirectory() as temporary:
            project = make_project(Path(temporary))
            wiki = make_wiki(project)
            git(project, "init", "--initial-branch=main")
            git(project, "config", "user.email", "test@example.invalid")
            git(project, "config", "user.name", "Test")
            git(project, "add", "docs")
            git(project, "commit", "-m", "project docs")
            protected = file_state(wiki)

            def track_during_sync() -> None:
                git(project, "add", "knowledge/wiki")

            result = sync_project(
                project,
                autopilot_root=AUTOPILOT,
                before_publish=track_during_sync,
            )
            self.assertEqual(
                ("failed", "stale-tree"),
                (result["status"], result["reason"]),
            )
            self.assertEqual(protected, file_state(wiki))

        with tempfile.TemporaryDirectory() as temporary:
            project = make_project(Path(temporary))
            wiki = make_wiki(project)
            with sync_module._wiki_lock(wiki.resolve()):
                result = sync_project(project, autopilot_root=AUTOPILOT)
            self.assertEqual("concurrent-operation", result["reason"])
            self.assertEqual("retryable", result["retry"]["disposition"])


if __name__ == "__main__":
    unittest.main()
