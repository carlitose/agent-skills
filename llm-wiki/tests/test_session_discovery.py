from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import session_discovery  # noqa: E402
from session_discovery import (  # noqa: E402
    CLAUDE_TIMESTAMP_FIELD,
    CODEX_TIMESTAMP_FIELDS,
    claude_project_directory,
    claude_transcripts,
    codex_session_cwd,
    codex_transcripts,
    discover,
    mangle_path,
    same_project,
    unaccounted_claude_directories,
)

WINDOWS_SAMPLES = {
    "C--Users-Ada-Projects-agent-skills": r"C:\Users\Ada\Projects\agent-skills",
    "D--work-wiki": r"D:\work\wiki",
    "E--source-one-two": r"E:\source\one\two",
}


def write_jsonl(path: Path, *records: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record) + "\n" for record in records), encoding="utf-8"
    )
    return path


class ManglingRuleTests(unittest.TestCase):
    def test_the_rule_reproduces_known_windows_directory_names(self) -> None:
        for name, cwd in WINDOWS_SAMPLES.items():
            with self.subTest(directory=name):
                self.assertEqual(name, mangle_path(cwd))

    def test_collapsing_runs_of_separators_loses_the_windows_drive_prefix(self) -> None:
        """The rule that looks equally plausible and is wrong.

        Replacing each *run* of non-alphanumerics with one dash loses the double dash that a
        Windows drive prefix produces, so it matches none of the expected Windows names.
        """

        import re

        for name, cwd in WINDOWS_SAMPLES.items():
            with self.subTest(directory=name):
                self.assertNotEqual(name, re.sub(r"[^A-Za-z0-9]+", "-", cwd))

    def test_each_single_separator_contributes_one_dash(self) -> None:
        self.assertEqual("C--Users-Ada", mangle_path(r"C:\Users\Ada"))
        self.assertEqual(
            "C--Users-Ada-Projects-agent-skills",
            mangle_path(r"C:\Users\Ada\Projects\agent-skills"),
        )
        self.assertEqual("-home-user-project", mangle_path("/home/user/project"))


class ClaudeStoreTests(unittest.TestCase):
    def test_the_directory_is_derived_from_the_project_root(self) -> None:
        store = Path("/synthetic/claude/projects")
        project = Path(r"C:\Users\Ada\Projects\agent-skills")
        with patch.object(session_discovery, "CLAUDE_ROOT", store):
            self.assertEqual(
                store / "C--Users-Ada-Projects-agent-skills",
                claude_project_directory(project),
            )

    def test_project_transcripts_are_sorted_direct_jsonl_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            store = root / "claude"
            directory = store / mangle_path(project)
            write_jsonl(directory / "one.jsonl", {"cwd": str(project)})
            write_jsonl(directory / "two.jsonl", {"cwd": str(project)})
            (directory / "notes.txt").write_text("not a transcript\n", encoding="utf-8")

            with patch.object(session_discovery, "CLAUDE_ROOT", store):
                transcripts = claude_transcripts(project)

        self.assertEqual(["one.jsonl", "two.jsonl"], [path.name for path in transcripts])

    def test_memory_and_per_session_directories_are_not_transcripts(self) -> None:
        """Excluded by an explicit rule, not by a glob that happens to miss them."""

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            store = root / "claude"
            directory = store / mangle_path(project)
            write_jsonl(directory / "one.jsonl", {"cwd": str(project)})
            (directory / "memory").mkdir()
            (directory / "00000000-0000-0000-0000-000000000000").mkdir()

            with patch.object(session_discovery, "CLAUDE_ROOT", store):
                names = {path.name for path in claude_transcripts(project)}

        self.assertEqual({"one.jsonl"}, names)

    def test_an_absent_project_directory_yields_nothing_rather_than_raising(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            store = root / "claude"
            store.mkdir()
            with patch.object(session_discovery, "CLAUDE_ROOT", store):
                self.assertEqual([], claude_transcripts(root / "never-used"))

    def test_a_directory_the_rule_cannot_produce_is_reported(self) -> None:
        """Criterion: report, never silently skip.

        The store fixture carries one such directory beside valid Windows and POSIX names.
        """

        with tempfile.TemporaryDirectory() as temporary:
            store = Path(temporary) / "claude"
            for name in ("foxtrick_v3", "C--Users-Ada", "-home-ada-project"):
                (store / name).mkdir(parents=True)
            with patch.object(session_discovery, "CLAUDE_ROOT", store):
                unaccounted = unaccounted_claude_directories()

        self.assertEqual(["foxtrick_v3"], unaccounted)


class CodexStoreTests(unittest.TestCase):
    def test_sessions_are_partitioned_by_project_and_missing_cwd(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            unrelated = root / "unrelated"
            project.mkdir()
            unrelated.mkdir()
            store = root / "codex"
            mine_path = write_jsonl(
                store / "2026" / "08" / "27" / "rollout-mine.jsonl",
                {"type": "session_meta", "payload": {"cwd": str(project)}},
            )
            write_jsonl(
                store / "2026" / "08" / "27" / "rollout-other.jsonl",
                {"type": "session_meta", "payload": {"cwd": str(unrelated)}},
            )
            unresolved_path = write_jsonl(
                store / "2026" / "08" / "27" / "rollout-unresolved.jsonl",
                {"type": "event_msg"},
            )

            with patch.object(session_discovery, "CODEX_ROOT", store):
                mine, unresolved = codex_transcripts(project)

        self.assertEqual([mine_path], mine)
        self.assertEqual([unresolved_path], unresolved)

    def test_a_rollout_without_session_meta_is_unresolved_not_attributed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            transcript = Path(temporary) / "rollout-x.jsonl"
            transcript.write_text('{"type":"event_msg"}\n', encoding="utf-8")
            self.assertIsNone(codex_session_cwd(transcript))

    def test_the_recorded_cwd_is_read_from_session_meta(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            transcript = Path(temporary) / "rollout-y.jsonl"
            transcript.write_text(
                json.dumps({"type": "session_meta", "payload": {"cwd": "C:/x/y"}}) + "\n",
                encoding="utf-8",
            )
            self.assertEqual("C:/x/y", codex_session_cwd(transcript))


class WorktreeMembershipTests(unittest.TestCase):
    def test_a_linked_worktree_belongs_to_the_same_project(self) -> None:
        """The recorded answer to the worktree question.

        Work done in a linked worktree is the project's history: excluding it would drop the
        sessions in which the project was actually changed. Sameness is decided by Git's common
        directory rather than by string prefix, because a worktree lives outside the tree.
        """

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            (project / "a.txt").write_text("a\n", encoding="utf-8")
            for arguments in (
                ("init", "--initial-branch=main"),
                ("config", "user.email", "t@example.invalid"),
                ("config", "user.name", "T"),
                ("add", "a.txt"),
                ("commit", "-m", "a"),
            ):
                subprocess.run(
                    ["git", "-C", str(project), *arguments],
                    check=True, capture_output=True, text=True, encoding="utf-8",
                )
            linked = root / "linked"
            subprocess.run(
                ["git", "-C", str(project), "worktree", "add", str(linked), "-b", "side"],
                check=True, capture_output=True, text=True, encoding="utf-8",
            )
            try:
                self.assertTrue(same_project(project, linked))
                self.assertTrue(same_project(project, project))
                unrelated = root / "unrelated"
                unrelated.mkdir()
                self.assertFalse(same_project(project, unrelated))
            finally:
                subprocess.run(
                    ["git", "-C", str(project), "worktree", "remove", "--force", str(linked)],
                    check=True, capture_output=True, text=True, encoding="utf-8",
                )

    def test_a_subdirectory_belongs_without_consulting_git(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            (project / "docs").mkdir(parents=True)
            self.assertTrue(same_project(project, project / "docs"))


class ContractDocumentationTests(unittest.TestCase):
    def test_the_timestamp_fields_are_declared_per_provider(self) -> None:
        self.assertEqual("timestamp", CLAUDE_TIMESTAMP_FIELD)
        self.assertEqual(("timestamp", "payload.timestamp"), CODEX_TIMESTAMP_FIELDS)

    def test_the_report_separates_mine_from_what_it_could_not_account_for(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            claude_store = root / "claude"
            codex_store = root / "codex"
            write_jsonl(
                claude_store / mangle_path(project) / "one.jsonl",
                {"cwd": str(project)},
            )
            (claude_store / "unaccounted_name").mkdir(parents=True)
            write_jsonl(
                codex_store / "2026" / "08" / "27" / "rollout-one.jsonl",
                {"type": "session_meta", "payload": {"cwd": str(project)}},
            )
            with patch.object(session_discovery, "CLAUDE_ROOT", claude_store), patch.object(
                session_discovery, "CODEX_ROOT", codex_store
            ):
                report = discover(project)

        self.assertEqual(str(project), report["project_root"])
        self.assertEqual(1, report["claude"]["count"])
        self.assertEqual(1, report["codex"]["count"])
        self.assertIn("unresolved_codex_sessions", report)
        self.assertIn("unaccounted_claude_directories", report)
        self.assertEqual(["unaccounted_name"], report["unaccounted_claude_directories"])
        self.assertEqual(
            "store directory name, from the startup cwd", report["claude"]["identity"]
        )
        self.assertEqual("session_meta.payload.cwd", report["codex"]["identity"])


if __name__ == "__main__":
    unittest.main()
