from __future__ import annotations

import json
import os
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


def pi_transcript(directory: Path, session_id: str, cwd: str, *extra: dict) -> Path:
    """Write a Pi transcript the way Pi names and shapes one."""

    return write_jsonl(
        directory / f"2026-09-07T09-04-49-036Z_{session_id}.jsonl",
        {
            "type": "session",
            "version": 3,
            "id": session_id,
            "timestamp": "2026-09-07T09:04:49.036Z",
            "cwd": cwd,
        },
        *extra,
    )


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


class PiStoreRootTests(unittest.TestCase):
    """Where Pi keeps its sessions is configuration, not a constant.

    Pi resolves the store in a fixed order, and three of its four steps are durable enough for
    a wiki to read: the session-directory variable, ``sessionDir`` in the agent's settings, and
    the agent-directory variable. The fourth, ``--session-dir`` on one command line, leaves no
    trace and cannot be honoured. Hardcoding ``~/.pi/agent/sessions`` would silently find
    nothing for anyone who moved the store, and reading nothing looks exactly like a project
    with no history.
    """

    def test_the_session_directory_variable_wins(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            moved = Path(temporary) / "moved"
            with patch.dict(
                os.environ, {session_discovery.PI_SESSION_DIR_ENV: str(moved)}, clear=False
            ):
                self.assertEqual(moved, session_discovery.pi_sessions_root())

    def test_settings_name_the_store_when_no_variable_does(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            agent = Path(temporary) / "agent"
            agent.mkdir()
            elsewhere = Path(temporary) / "elsewhere"
            (agent / "settings.json").write_text(
                json.dumps({"sessionDir": str(elsewhere)}), encoding="utf-8"
            )
            with patch.dict(
                os.environ, {session_discovery.PI_AGENT_DIR_ENV: str(agent)}, clear=False
            ):
                os.environ.pop(session_discovery.PI_SESSION_DIR_ENV, None)
                self.assertEqual(elsewhere, session_discovery.pi_sessions_root())

    def test_the_agent_directory_decides_when_settings_are_silent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            agent = Path(temporary) / "agent"
            agent.mkdir()
            with patch.dict(
                os.environ, {session_discovery.PI_AGENT_DIR_ENV: str(agent)}, clear=False
            ):
                os.environ.pop(session_discovery.PI_SESSION_DIR_ENV, None)
                self.assertEqual(agent / "sessions", session_discovery.pi_sessions_root())

    def test_unreadable_settings_fall_back_instead_of_raising(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            agent = Path(temporary) / "agent"
            agent.mkdir()
            (agent / "settings.json").write_text("{ not json", encoding="utf-8")
            with patch.dict(
                os.environ, {session_discovery.PI_AGENT_DIR_ENV: str(agent)}, clear=False
            ):
                os.environ.pop(session_discovery.PI_SESSION_DIR_ENV, None)
                self.assertEqual(agent / "sessions", session_discovery.pi_sessions_root())


class PiStoreTests(unittest.TestCase):
    """The recorded ``cwd`` decides; the directory is only where the file happens to sit."""

    def test_the_in_file_cwd_attributes_a_transcript_not_its_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project, unrelated = root / "project", root / "unrelated"
            project.mkdir()
            unrelated.mkdir()
            store = root / "sessions"
            directory = store / f"--{project.name}--"
            mine = pi_transcript(
                directory, "01a07b1c-ef8c-73cd-9f7c-0baef19f02c4", str(project)
            )
            # Sits in this project's directory, and says it belongs to another one.
            pi_transcript(directory, "01a07b1d-7720-774c-bec5-c26cbf93f443", str(unrelated))

            with patch.object(session_discovery, "pi_sessions_root", lambda: store):
                found, unresolved = session_discovery.pi_transcripts(project)

        self.assertEqual([mine], found)
        self.assertEqual([], unresolved)

    def test_a_rotated_transcript_keeps_its_project(self) -> None:
        """``_oversized-backup/`` is why the directory cannot be the identity.

        Pi rotates a large transcript there, which strips its project directory and keeps its
        ``cwd``. Reading the file rather than its parent needs no special case for it.
        """

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            store = root / "sessions"
            rotated = pi_transcript(
                store / "_oversized-backup",
                "01a081aa-7ddb-76aa-94c5-e80a3c73dae3",
                str(project),
            )

            with patch.object(session_discovery, "pi_sessions_root", lambda: store):
                found, unresolved = session_discovery.pi_transcripts(project)

        self.assertEqual([rotated], found)
        self.assertEqual([], unresolved)

    def test_a_transcript_with_no_session_record_is_unresolved(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            store = root / "sessions"
            headless = write_jsonl(
                store / "--x--" / "2026-09-07T09-04-49-036Z_01a07b1c-ef8c-73cd-9f7c-0baef19f02c4.jsonl",
                {"type": "message", "message": {"content": [{"type": "text", "text": "hi"}]}},
            )

            with patch.object(session_discovery, "pi_sessions_root", lambda: store):
                found, unresolved = session_discovery.pi_transcripts(project)

        self.assertEqual([], found)
        self.assertEqual([headless], unresolved)

    def test_a_filename_that_disagrees_with_the_record_is_unresolved(self) -> None:
        """Two identities for one session is a contradiction, not a preference.

        Picking either one attaches this session's history to an identifier the other half of
        the store does not use, and nothing afterwards would show which half was guessed.
        """

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            store = root / "sessions"
            mismatched = write_jsonl(
                store / "--x--" / "2026-09-07T09-04-49-036Z_01a07b1c-ef8c-73cd-9f7c-0baef19f02c4.jsonl",
                {
                    "type": "session",
                    "id": "01a081aa-7ddb-76aa-94c5-e80a3c73dae3",
                    "cwd": str(project),
                },
            )

            with patch.object(session_discovery, "pi_sessions_root", lambda: store):
                found, unresolved = session_discovery.pi_transcripts(project)

        self.assertEqual([], found)
        self.assertEqual([mismatched], unresolved)

    def test_an_absent_store_reports_nothing_rather_than_failing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            project.mkdir()
            with patch.object(
                session_discovery, "pi_sessions_root", lambda: Path(temporary) / "absent"
            ):
                self.assertEqual(([], []), session_discovery.pi_transcripts(project))


class ProviderDispatchTests(unittest.TestCase):
    """The binding's provider list decides what is computed, and a typo is not an empty store."""

    def _stores(self, root: Path, project: Path) -> tuple[Path, Path, Path]:
        claude, codex, pi = root / "claude", root / "codex", root / "pi"
        write_jsonl(claude / mangle_path(project) / "one.jsonl", {"cwd": str(project)})
        write_jsonl(
            codex / "2026" / "08" / "27" / "rollout-one.jsonl",
            {"type": "session_meta", "payload": {"cwd": str(project)}},
        )
        pi_transcript(pi / "--p--", "01a07b1c-ef8c-73cd-9f7c-0baef19f02c4", str(project))
        return claude, codex, pi

    def test_an_unknown_provider_names_the_offending_value(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            project.mkdir()
            with self.assertRaises(session_discovery.DiscoveryError) as raised:
                discover(project, providers=("claude-code", "cladue-code"))
        self.assertIn("cladue-code", str(raised.exception))

    def test_the_default_provider_set_is_what_a_binding_gets_by_default(self) -> None:
        self.assertEqual(("claude-code", "codex"), session_discovery.DEFAULT_PROVIDERS)

    def test_an_omitted_provider_is_absent_rather_than_reported_empty(self) -> None:
        """A zero next to a provider name is a claim, and it would be a false one."""

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            claude, codex, pi = self._stores(root, project)
            with patch.object(session_discovery, "CLAUDE_ROOT", claude), patch.object(
                session_discovery, "CODEX_ROOT", codex
            ), patch.object(session_discovery, "pi_sessions_root", lambda: pi):
                only_pi = discover(project, providers=("pi",))
                everything = discover(project, providers=("claude-code", "codex", "pi"))

        self.assertNotIn("claude", only_pi)
        self.assertNotIn("codex", only_pi)
        self.assertEqual(1, only_pi["pi"]["count"])
        self.assertEqual(1, everything["claude"]["count"])
        self.assertEqual(1, everything["codex"]["count"])
        self.assertEqual(1, everything["pi"]["count"])
        self.assertEqual("session.cwd, read from the transcript", everything["pi"]["identity"])


if __name__ == "__main__":
    unittest.main()
