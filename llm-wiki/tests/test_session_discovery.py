from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from session_discovery import (  # noqa: E402
    CLAUDE_ROOT,
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

THIS_PROJECT = Path(r"C:\Users\CGS03\Projects\agent-skills")


def collect_real_samples() -> dict[str, str]:
    """Map each Claude project directory to the first cwd its transcripts record."""

    samples: dict[str, str] = {}
    if not CLAUDE_ROOT.is_dir():
        return samples
    for directory in sorted(CLAUDE_ROOT.iterdir()):
        if not directory.is_dir():
            continue
        for transcript in sorted(directory.glob("*.jsonl")):
            try:
                with transcript.open(encoding="utf-8", errors="replace") as handle:
                    for line in handle:
                        try:
                            record = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        cwd = record.get("cwd")
                        if isinstance(cwd, str) and cwd:
                            samples.setdefault(directory.name, cwd)
                            break
            except OSError:
                continue
            if directory.name in samples:
                break
    return samples


class ManglingRuleTests(unittest.TestCase):
    def test_the_rule_reproduces_every_real_directory_that_records_a_cwd(self) -> None:
        samples = collect_real_samples()
        self.assertGreaterEqual(
            len(samples), 3, "the rule must be discriminated against at least three samples"
        )
        for name, cwd in samples.items():
            with self.subTest(directory=name):
                self.assertEqual(
                    name,
                    mangle_path(cwd),
                    f"the rule must reproduce {name} from {cwd}",
                )

    def test_collapsing_runs_of_separators_reproduces_nothing(self) -> None:
        """The rule that looks equally plausible and is wrong.

        Replacing each *run* of non-alphanumerics with one dash loses the double dash that a
        Windows drive prefix produces, so it matches none of the real names.
        """

        import re

        samples = collect_real_samples()
        self.assertTrue(samples)
        for name, cwd in samples.items():
            with self.subTest(directory=name):
                self.assertNotEqual(name, re.sub(r"[^A-Za-z0-9]+", "-", cwd))

    def test_each_single_separator_contributes_one_dash(self) -> None:
        self.assertEqual("C--Users-CGS03", mangle_path(r"C:\Users\CGS03"))
        self.assertEqual(
            "C--Users-CGS03-Projects-agent-skills",
            mangle_path(r"C:\Users\CGS03\Projects\agent-skills"),
        )
        self.assertEqual("-home-user-project", mangle_path("/home/user/project"))


class ClaudeStoreTests(unittest.TestCase):
    def test_the_directory_is_derived_from_the_project_root(self) -> None:
        self.assertEqual(
            CLAUDE_ROOT / "C--Users-CGS03-Projects-agent-skills",
            claude_project_directory(THIS_PROJECT),
        )

    def test_this_project_has_transcripts_and_they_are_all_jsonl(self) -> None:
        transcripts = claude_transcripts(THIS_PROJECT)
        self.assertGreaterEqual(len(transcripts), 1)
        for path in transcripts:
            self.assertEqual(".jsonl", path.suffix)
            self.assertTrue(path.is_file())

    def test_memory_and_per_session_directories_are_not_transcripts(self) -> None:
        """Excluded by an explicit rule, not by a glob that happens to miss them."""

        directory = claude_project_directory(THIS_PROJECT)
        names = {path.name for path in claude_transcripts(THIS_PROJECT)}
        self.assertNotIn("memory", names)
        for entry in directory.iterdir():
            if entry.is_dir():
                self.assertNotIn(entry.name, names)

    def test_an_absent_project_directory_yields_nothing_rather_than_raising(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            self.assertEqual([], claude_transcripts(Path(temporary) / "never-used"))

    def test_a_directory_the_rule_cannot_produce_is_reported(self) -> None:
        """Criterion: report, never silently skip.

        This machine carries exactly such a directory, so the behaviour is observed rather than
        only designed.
        """

        unaccounted = unaccounted_claude_directories()
        self.assertIn("foxtrick_v3", unaccounted)
        for name in unaccounted:
            self.assertFalse(name.startswith("C--"))


class CodexStoreTests(unittest.TestCase):
    def test_this_project_resolves_its_codex_sessions_and_leaves_none_unresolved(self) -> None:
        mine, unresolved = codex_transcripts(THIS_PROJECT)
        self.assertGreaterEqual(len(mine), 1)
        self.assertEqual([], unresolved, "every rollout on this machine records a cwd")
        for path in mine:
            self.assertTrue(path.name.startswith("rollout-"))
            self.assertEqual(
                THIS_PROJECT.resolve(),
                Path(codex_session_cwd(path) or "").resolve(),
                "these sessions started in the project root itself",
            )

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
        report = discover(THIS_PROJECT)
        self.assertEqual(str(THIS_PROJECT), report["project_root"])
        self.assertGreaterEqual(report["claude"]["count"], 1)
        self.assertGreaterEqual(report["codex"]["count"], 1)
        self.assertIn("unresolved_codex_sessions", report)
        self.assertIn("unaccounted_claude_directories", report)
        self.assertEqual(
            "store directory name, from the startup cwd", report["claude"]["identity"]
        )
        self.assertEqual("session_meta.payload.cwd", report["codex"]["identity"])


if __name__ == "__main__":
    unittest.main()
