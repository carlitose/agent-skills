"""A repository scope may reuse structure facts, and must never reuse a stale one."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from autopilot import git_ops  # noqa: E402

from git_test_support import GitIsolatedTestCase  # noqa: E402


class RepositoryScopeTests(GitIsolatedTestCase):
    """`repository_scope` exists to stop one invocation asking Git the same thing 116 times."""

    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory(prefix="repository-scope-")
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        self.repo = self.directory / "repo"
        self.repo.mkdir()
        for command in (
            ("init", "--quiet"),
            ("config", "user.email", "scope@example.invalid"),
            ("config", "user.name", "scope"),
        ):
            subprocess.run(["git", *command], cwd=self.repo, check=True, capture_output=True)
        (self.repo / "file.md").write_text("one\n", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=self.repo, check=True, capture_output=True)
        subprocess.run(["git", "commit", "--quiet", "-m", "first"], cwd=self.repo, check=True, capture_output=True)

    def counted(self):
        """Count how many times Git is actually asked, without changing what it answers."""
        calls: list[tuple[str, ...]] = []
        original = git_ops.run_git

        def recorder(repo: Path, *args: str) -> str:
            calls.append(args)
            return original(repo, *args)

        return calls, recorder

    def test_repeated_structure_questions_ask_git_once_inside_one_scope(self) -> None:
        calls, recorder = self.counted()
        with mock.patch.object(git_ops, "run_git", recorder):
            with git_ops.repository_scope():
                roots = [git_ops.repository_root(self.repo) for _ in range(6)]
                directories = [git_ops.common_git_dir(self.repo) for _ in range(6)]
        self.assertEqual(len(set(roots)), 1)
        self.assertEqual(len(set(directories)), 1)
        self.assertEqual(calls.count(("rev-parse", "--show-toplevel")), 1)
        self.assertEqual(calls.count(("rev-parse", "--git-common-dir")), 1)

    def test_without_a_scope_every_question_still_reaches_git(self) -> None:
        calls, recorder = self.counted()
        with mock.patch.object(git_ops, "run_git", recorder):
            for _ in range(3):
                git_ops.repository_root(self.repo)
        self.assertEqual(calls.count(("rev-parse", "--show-toplevel")), 3)

    def test_a_scope_never_outlives_itself(self) -> None:
        calls, recorder = self.counted()
        with mock.patch.object(git_ops, "run_git", recorder):
            with git_ops.repository_scope():
                git_ops.repository_root(self.repo)
            with git_ops.repository_scope():
                git_ops.repository_root(self.repo)
        self.assertEqual(calls.count(("rev-parse", "--show-toplevel")), 2)

    def test_a_nested_repository_created_inside_the_scope_is_not_answered_from_cache(self) -> None:
        """`git init` below a cached path changes the answer, so the cache must not survive it."""
        nested = self.repo / "nested"
        nested.mkdir()
        with git_ops.repository_scope():
            self.assertEqual(git_ops.repository_root(nested), self.repo.resolve())
            git_ops.run_git(nested, "init", "--quiet")
            self.assertEqual(git_ops.repository_root(nested), nested.resolve())

    def test_a_worktree_added_inside_the_scope_is_not_answered_from_cache(self) -> None:
        worktree = self.directory / "tree"
        with git_ops.repository_scope():
            git_ops.repository_root(self.repo)
            git_ops.run_git(self.repo, "worktree", "add", "--detach", str(worktree), "HEAD")
            self.assertEqual(git_ops.repository_root(worktree), worktree.resolve())

    def test_a_failed_question_is_never_remembered(self) -> None:
        outside = self.directory / "plain"
        outside.mkdir()
        with git_ops.repository_scope():
            with self.assertRaises(git_ops.GitError):
                git_ops.repository_root(outside)
            git_ops.run_git(outside, "init", "--quiet")
            self.assertEqual(git_ops.repository_root(outside), outside.resolve())

    def test_content_reads_are_never_served_from_the_scope(self) -> None:
        """Only structure facts are reused; a tree read must reach Git after every mutation."""
        calls, recorder = self.counted()
        with mock.patch.object(git_ops, "run_git", recorder):
            with git_ops.repository_scope():
                first = git_ops.run_git(self.repo, "write-tree")
                (self.repo / "file.md").write_text("two\n", encoding="utf-8")
                git_ops.run_git(self.repo, "add", "-A")
                second = git_ops.run_git(self.repo, "write-tree")
        self.assertEqual(calls.count(("write-tree",)), 2)
        self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
