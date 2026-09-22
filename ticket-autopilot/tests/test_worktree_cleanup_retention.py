"""Cleanup must prove the head is retained, not assume the run branch still exists."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from autopilot import git_ops  # noqa: E402
from autopilot.git_ops import (  # noqa: E402
    GitError,
    assert_cleanup_safe,
    head_retained_by_integration,
)
from git_test_support import GitIsolatedTestCase  # noqa: E402


def _git(cwd: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(cwd), *arguments],
        capture_output=True, check=True, text=True, timeout=60,
    )
    return result.stdout.strip()


class _Scenario:
    """One disposable origin, clone and worktree, built per case."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.origin = root / "origin.git"
        subprocess.run(
            ["git", "init", "--bare", "-q", "-b", "main", str(self.origin)],
            check=True, capture_output=True, timeout=60,
        )
        self.clone = root / "clone"
        subprocess.run(
            ["git", "clone", "-q", str(self.origin), str(self.clone)],
            check=True, capture_output=True, timeout=60,
        )
        _git(self.clone, "config", "user.email", "fixture@example.invalid")
        _git(self.clone, "config", "user.name", "fixture")
        (self.clone / "seed.txt").write_text("seed\n", encoding="utf-8")
        _git(self.clone, "add", "-A")
        _git(self.clone, "commit", "-qm", "seed")
        _git(self.clone, "push", "-q", "origin", "main")
        self.base_sha = _git(self.clone, "rev-parse", "HEAD")
        self.worktree = root / "worktree"

    def branch_worktree(self, branch: str = "feat/x") -> Path:
        _git(
            self.clone, "worktree", "add", "-q", "-b", branch,
            str(self.worktree), "main",
        )
        return self.worktree

    def commit(self, text: str = "work\n") -> str:
        (self.worktree / "feature.txt").write_text(text, encoding="utf-8")
        _git(self.worktree, "add", "-A")
        _git(self.worktree, "commit", "-qm", "feature")
        return _git(self.worktree, "rev-parse", "HEAD")

    def publish(self, branch: str = "feat/x") -> None:
        _git(self.worktree, "push", "-q", "-u", "origin", f"HEAD:refs/heads/{branch}")

    def merge_into_main(self, branch: str = "feat/x") -> str:
        _git(self.clone, "merge", "-q", "--no-ff", "-m", f"merge {branch}", branch)
        _git(self.clone, "push", "-q", "origin", "main")
        return _git(self.clone, "rev-parse", "HEAD")

    def merge_into_main_elsewhere(self, branch: str = "feat/x") -> str:
        """Merge from another clone, so this repository never sees the merge commit."""

        other = self.root / "other"
        subprocess.run(
            ["git", "clone", "-q", str(self.origin), str(other)],
            check=True, capture_output=True, timeout=60,
        )
        _git(other, "config", "user.email", "fixture@example.invalid")
        _git(other, "config", "user.name", "fixture")
        _git(
            other, "merge", "-q", "--no-ff", "-m", f"merge {branch}",
            f"origin/{branch}",
        )
        _git(other, "push", "-q", "origin", "main")
        return _git(other, "rev-parse", "HEAD")

    def provider_deletes_branch(self, branch: str = "feat/x") -> None:
        """Delete the branch on the server, as a provider does when it merges."""

        _git(self.origin, "update-ref", "-d", f"refs/heads/{branch}")

    def prune_tracking_ref(self, branch: str = "feat/x") -> None:
        _git(self.worktree, "update-ref", "-d", f"refs/remotes/origin/{branch}")

    @property
    def ledger(self) -> dict[str, object]:
        return {"base_sha": self.base_sha, "worktree": str(self.worktree)}


class RetentionProofTests(GitIsolatedTestCase):
    def scenario(self) -> _Scenario:
        owner = tempfile.TemporaryDirectory(prefix="wgr-retention-")
        self.addCleanup(owner.cleanup)
        return _Scenario(Path(owner.name))

    def test_merged_head_is_retained_after_the_provider_deletes_the_branch(self):
        scenario = self.scenario()
        scenario.branch_worktree()
        head = scenario.commit()
        scenario.publish()
        scenario.merge_into_main()
        scenario.provider_deletes_branch()
        _git(scenario.worktree, "fetch", "-q", "origin", "main")

        proof = head_retained_by_integration(scenario.worktree, head)

        self.assertTrue(proof["retained"])
        self.assertEqual(proof["default_branch"], "main")
        self.assertIsNone(assert_cleanup_safe(scenario.worktree, scenario.ledger))

    def test_merged_head_is_retained_once_the_tracking_ref_is_gone_too(self):
        scenario = self.scenario()
        scenario.branch_worktree()
        head = scenario.commit()
        scenario.publish()
        scenario.merge_into_main()
        scenario.provider_deletes_branch()
        _git(scenario.worktree, "fetch", "-q", "origin", "main")
        scenario.prune_tracking_ref()

        proof = head_retained_by_integration(scenario.worktree, head)
        self.assertTrue(proof["retained"])
        self.assertIsNone(assert_cleanup_safe(scenario.worktree, scenario.ledger))

    def test_a_branch_that_was_never_published_but_is_contained_is_retained(self):
        scenario = self.scenario()
        scenario.branch_worktree("feat/local")

        self.assertIsNone(assert_cleanup_safe(scenario.worktree, scenario.ledger))

    def test_an_unmerged_head_is_still_refused_and_the_message_names_the_default(self):
        scenario = self.scenario()
        scenario.branch_worktree()
        scenario.commit()
        scenario.publish()
        scenario.provider_deletes_branch()

        with self.assertRaises(GitError) as raised:
            assert_cleanup_safe(scenario.worktree, scenario.ledger)

        message = str(raised.exception)
        listed = _git(scenario.worktree, "ls-remote", "origin", "refs/heads/main")
        default_sha = listed.split()[0]
        self.assertIn("main", message)
        self.assertIn(default_sha, message)

    def test_a_default_branch_absent_here_refuses_and_names_the_fetch(self):
        scenario = self.scenario()
        scenario.branch_worktree()
        head = scenario.commit()
        scenario.publish()
        scenario.merge_into_main_elsewhere()
        scenario.provider_deletes_branch()
        # The merge happened in another clone and was never fetched here, so this
        # repository cannot prove ancestry against it.

        proof = head_retained_by_integration(scenario.worktree, head)
        self.assertFalse(proof["retained"])
        self.assertEqual(proof["reason"], "default-branch-object-missing")

        with self.assertRaises(GitError) as raised:
            assert_cleanup_safe(scenario.worktree, scenario.ledger)
        self.assertIn("git fetch", str(raised.exception))

    def test_a_dirty_worktree_is_refused_even_when_the_head_is_contained(self):
        scenario = self.scenario()
        scenario.branch_worktree()
        head = scenario.commit()
        scenario.publish()
        scenario.merge_into_main()
        scenario.provider_deletes_branch()
        _git(scenario.worktree, "fetch", "-q", "origin", "main")
        (scenario.worktree / "feature.txt").write_text("edited\n", encoding="utf-8")

        proof = head_retained_by_integration(scenario.worktree, head)
        self.assertTrue(proof["retained"])
        with self.assertRaises(GitError) as raised:
            assert_cleanup_safe(scenario.worktree, scenario.ledger)
        self.assertIn("unpublished local state", str(raised.exception))

    def test_a_published_branch_at_its_head_is_still_accepted_without_the_proof(self):
        scenario = self.scenario()
        scenario.branch_worktree()
        scenario.commit()
        scenario.publish()

        calls: list[tuple[str, ...]] = []
        original = git_ops.head_retained_by_integration

        def record(worktree, head):
            calls.append(("proof", str(worktree), head))
            return original(worktree, head)

        git_ops.head_retained_by_integration = record
        try:
            self.assertIsNone(assert_cleanup_safe(scenario.worktree, scenario.ledger))
        finally:
            git_ops.head_retained_by_integration = original
        self.assertEqual(calls, [])

    def test_a_detached_head_contained_in_the_default_branch_is_retained(self):
        scenario = self.scenario()
        scenario.branch_worktree()
        head = scenario.commit()
        scenario.publish()
        scenario.merge_into_main()
        _git(scenario.worktree, "fetch", "-q", "origin", "main")
        _git(scenario.worktree, "checkout", "-q", "--detach", head)

        self.assertIsNone(assert_cleanup_safe(scenario.worktree, scenario.ledger))

    def test_a_detached_head_outside_the_default_branch_is_still_refused(self):
        scenario = self.scenario()
        scenario.branch_worktree()
        head = scenario.commit()
        _git(scenario.worktree, "checkout", "-q", "--detach", head)

        with self.assertRaises(GitError) as raised:
            assert_cleanup_safe(scenario.worktree, scenario.ledger)
        self.assertIn("unretained", str(raised.exception))

    def test_the_proof_never_fetches_or_writes_to_the_remote(self):
        scenario = self.scenario()
        scenario.branch_worktree()
        head = scenario.commit()
        scenario.publish()
        scenario.merge_into_main()
        scenario.provider_deletes_branch()
        _git(scenario.worktree, "fetch", "-q", "origin", "main")

        observed: list[list[str]] = []
        original = git_ops._run_captured

        def record(command, **keywords):
            observed.append(list(command))
            return original(command, **keywords)

        git_ops._run_captured = record
        try:
            head_retained_by_integration(scenario.worktree, head)
        finally:
            git_ops._run_captured = original

        self.assertTrue(observed)
        forbidden = {"fetch", "push", "pull", "remote"}
        for command in observed:
            self.assertFalse(
                forbidden.intersection(command),
                f"the retention proof must stay read-only: {command}",
            )

    def test_the_proof_reports_the_default_branch_it_observed(self):
        scenario = self.scenario()
        scenario.branch_worktree()
        head = scenario.commit()
        scenario.publish()
        scenario.merge_into_main()
        _git(scenario.worktree, "fetch", "-q", "origin", "main")

        proof = head_retained_by_integration(scenario.worktree, head)

        self.assertEqual(proof["default_branch"], "main")
        listed = _git(scenario.worktree, "ls-remote", "origin", "refs/heads/main")
        self.assertEqual(proof["default_sha"], listed.split()[0])
        self.assertEqual(proof["reason"], "contained-in-default-branch")

    def test_a_repository_without_a_remote_reports_that_and_does_not_crash(self):
        owner = tempfile.TemporaryDirectory(prefix="wgr-no-remote-")
        self.addCleanup(owner.cleanup)
        solo = Path(owner.name) / "solo"
        solo.mkdir()
        subprocess.run(
            ["git", "init", "-q", "-b", "main", str(solo)],
            check=True, capture_output=True, timeout=60,
        )
        _git(solo, "config", "user.email", "fixture@example.invalid")
        _git(solo, "config", "user.name", "fixture")
        (solo / "seed.txt").write_text("seed\n", encoding="utf-8")
        _git(solo, "add", "-A")
        _git(solo, "commit", "-qm", "seed")
        head = _git(solo, "rev-parse", "HEAD")

        proof = head_retained_by_integration(solo, head)

        self.assertFalse(proof["retained"])
        self.assertEqual(proof["reason"], "default-branch-unobservable")


if __name__ == "__main__":
    unittest.main()
