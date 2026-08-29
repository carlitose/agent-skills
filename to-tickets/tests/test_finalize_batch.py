from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
LLM_WIKI_SCRIPTS = SKILL_ROOT.parent / "llm-wiki" / "scripts"
AUTOPILOT_SCRIPTS = SKILL_ROOT.parent / "ticket-autopilot" / "scripts"
for scripts_root in (SCRIPTS, LLM_WIKI_SCRIPTS, AUTOPILOT_SCRIPTS):
    if str(scripts_root) not in sys.path:
        sys.path.insert(0, str(scripts_root))

from autopilot.ticket_contract import serialize_ticket_markdown  # noqa: E402
from finalize_batch import (  # noqa: E402
    BatchValidationError,
    finalize_ticket_batch,
)
from project_binding import write_binding  # noqa: E402
from scaffold import scaffold  # noqa: E402
from sync_project import sync_project  # noqa: E402


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
    return project


def make_wiki(project: Path, root: Path | None = None) -> Path:
    wiki = root or project / "knowledge"
    scaffold(wiki, "Batch fixture", project)
    write_binding(wiki, project, auto_sync="enabled")
    return wiki


def write_batch(
    project: Path,
    tickets: list[tuple[str, str, list[str]]],
) -> tuple[Path, list[Path]]:
    folder = project / "docs" / "tickets" / "batch"
    folder.mkdir(parents=True)
    names = [
        f"{index:02d}-{ticket_id.lower()}.md"
        for index, (ticket_id, _, _) in enumerate(tickets, 1)
    ]
    children = "\n".join(
        f"- [{name}](../tickets/batch/{name})" for name in names
    )
    spec = """# Batch spec

## Artifact Graph
- Artifact ID: `artifact:batch-spec`
- Role: `spec`
- Standalone: true
"""
    if children:
        spec += f"\n### Children\n{children}\n"
    (project / "docs" / "specs" / "batch-spec.md").write_text(
        spec, encoding="utf-8"
    )

    paths: list[Path] = []
    for name, (ticket_id, mode, blockers) in zip(names, tickets):
        body = f"""# Ticket {ticket_id}

## Artifact Graph
- Artifact ID: `artifact:{ticket_id.lower()}`
- Role: `ticket`
- Parent: [batch-spec.md](../../specs/batch-spec.md)

## Parent Spec
[batch-spec.md](../../specs/batch-spec.md)

## What to Build
Implement {ticket_id}.

## Acceptance Criteria
- [ ] The behavior is visible.

## Frontier
Canonical dependency state.

## Step-by-Step Implementation Plan
1. Implement and verify the slice.

## Testing Plan
Run the focused tests.

## Out of Scope
- Unrelated work.
"""
        path = folder / name
        path.write_text(
            serialize_ticket_markdown(
                {
                    "ticket_schema": 1,
                    "ticket_id": ticket_id,
                    "execution_mode": mode,
                    "blocked_by": blockers,
                },
                body,
            ),
            encoding="utf-8",
        )
        paths.append(path)
    return folder, paths


class FinalizeBatchTests(unittest.TestCase):
    def test_cli_reports_the_absent_wiki_noop_after_batch_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = make_project(Path(temporary))
            folder, paths = write_batch(project, [("A", "AFK", [])])

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "finalize_batch.py"),
                    str(project),
                    str(folder),
                    *(str(path) for path in paths),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )

            self.assertEqual(0, completed.returncode, completed.stderr)
            report = json.loads(completed.stdout)
            self.assertEqual("ticket-batch-finalize-v1", report["contract_version"])
            self.assertEqual(
                ("skipped", "absent"),
                (report["wiki_sync"]["status"], report["wiki_sync"]["reason"]),
            )

    def test_symlinked_ticket_folder_is_rejected_before_sync(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = make_project(Path(temporary))
            folder, paths = write_batch(project, [("A", "AFK", [])])
            alias = project.parent / "batch-alias"
            try:
                alias.symlink_to(folder, target_is_directory=True)
            except OSError as error:
                self.skipTest(f"directory symlinks unavailable: {error}")

            with self.assertRaisesRegex(BatchValidationError, "symlink"):
                finalize_ticket_batch(
                    project,
                    alias,
                    [alias / paths[0].name],
                    sync_operation=lambda *args, **kwargs: self.fail(
                        "sync must follow path validation"
                    ),
                )

    def test_nonreciprocal_batch_is_rejected_before_sync(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = make_project(Path(temporary))
            folder, paths = write_batch(project, [("A", "AFK", [])])
            spec = project / "docs" / "specs" / "batch-spec.md"
            spec.write_text(
                spec.read_text(encoding="utf-8").split("### Children", 1)[0],
                encoding="utf-8",
            )
            calls: list[object] = []

            def forbidden(*args, **kwargs):  # type: ignore[no-untyped-def]
                calls.append((args, kwargs))
                raise AssertionError("sync must follow reciprocal-link validation")

            with self.assertRaisesRegex(
                BatchValidationError, "reciprocity-mismatch"
            ):
                finalize_ticket_batch(
                    project, folder, paths, sync_operation=forbidden
                )

            self.assertEqual([], calls)

    def test_partial_batch_is_rejected_before_sync(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = make_project(Path(temporary))
            folder, paths = write_batch(
                project,
                [("A", "AFK", []), ("B", "AFK", ["A"])],
            )
            calls: list[object] = []

            def forbidden(*args, **kwargs):  # type: ignore[no-untyped-def]
                calls.append((args, kwargs))
                raise AssertionError("sync must follow complete-batch validation")

            with self.assertRaisesRegex(
                BatchValidationError, "complete top-level batch"
            ):
                finalize_ticket_batch(
                    project,
                    folder.relative_to(project),
                    paths[:1],
                    sync_operation=forbidden,
                )

            self.assertEqual([], calls)

    def test_empty_batch_with_absent_wiki_calls_sync_once_and_reports_canonical_noop(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = make_project(Path(temporary))
            folder, paths = write_batch(project, [])
            calls: list[str] = []

            def observed(*args, **kwargs):  # type: ignore[no-untyped-def]
                calls.append(kwargs["origin_id"])
                return sync_project(*args, **kwargs)

            report = finalize_ticket_batch(
                project, folder, paths, sync_operation=observed
            )

            self.assertEqual(1, len(calls))
            self.assertEqual(report["batch_id"], calls[0])
            self.assertEqual([], report["ticket_paths"])
            self.assertEqual([], report["ready_frontier"])
            self.assertEqual(
                ("skipped", "absent"),
                (report["wiki_sync"]["status"], report["wiki_sync"]["reason"]),
            )

    def test_complete_untracked_batch_is_compiled_once_and_frontier_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = make_project(Path(temporary))
            folder, paths = write_batch(
                project,
                [("A", "AFK", []), ("B", "AFK", ["A"])],
            )
            wiki = make_wiki(project)
            calls: list[str] = []

            def observed(*args, **kwargs):  # type: ignore[no-untyped-def]
                calls.append(kwargs["origin_id"])
                return sync_project(*args, **kwargs)

            report = finalize_ticket_batch(
                project, folder, paths, sync_operation=observed
            )

            self.assertEqual(1, len(calls), "the hook is per batch, never per ticket")
            self.assertEqual(["A"], report["ready_frontier"])
            self.assertEqual(
                ["B"],
                [item["ticket_id"] for item in report["blocked_tickets"]],
            )
            self.assertEqual(
                ("updated-directly", "internal-untracked"),
                (report["wiki_sync"]["status"], report["wiki_sync"]["reason"]),
            )
            self.assertTrue(report["wiki_sync"]["validation_receipt"])
            lifecycle = sorted((wiki / "wiki" / "timeline" / "tickets").glob("*.md"))
            self.assertEqual(2, len(lifecycle))

    def test_tracked_wiki_yields_a_separate_candidate_without_changing_ticket_tree(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = make_project(Path(temporary))
            make_wiki(project)
            (project / "docs" / "specs" / "batch-spec.md").write_text(
                "# Placeholder\n", encoding="utf-8"
            )
            git(project, "init", "--initial-branch=main")
            git(project, "config", "user.email", "test@example.invalid")
            git(project, "config", "user.name", "Test")
            git(project, "add", ".")
            git(project, "commit", "-m", "tracked wiki")
            (project / "docs" / "specs" / "batch-spec.md").unlink()
            folder, paths = write_batch(project, [("A", "AFK", [])])
            before = git(project, "status", "--porcelain=v1")

            report = finalize_ticket_batch(project, folder, paths)

            self.assertEqual(
                ("candidate-created", "manual-authorization"),
                (report["wiki_sync"]["status"], report["wiki_sync"]["reason"]),
            )
            self.assertEqual(before, git(project, "status", "--porcelain=v1"))
            candidate = Path(report["wiki_sync"]["candidate_path"])
            self.assertTrue((candidate / "manifest.json").is_file())
            self.assertFalse(candidate.is_relative_to(project / "docs" / "tickets"))

    def test_ambiguous_wiki_failure_keeps_created_ticket_report_and_retry_decision(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = make_project(Path(temporary))
            folder, paths = write_batch(project, [("H", "HITL", [])])
            make_wiki(project, project / "one")
            make_wiki(project, project / "two")

            report = finalize_ticket_batch(project, folder, paths)

            self.assertEqual(
                [paths[0].relative_to(project).as_posix()], report["ticket_paths"]
            )
            self.assertEqual(
                [{"ticket_id": "H", "state": "human-gated"}],
                report["hitl_decisions"],
            )
            self.assertEqual(
                ("failed", "ambiguous-root"),
                (report["wiki_sync"]["status"], report["wiki_sync"]["reason"]),
            )
            self.assertEqual("terminal", report["wiki_sync"]["retry"]["disposition"])


if __name__ == "__main__":
    unittest.main()
