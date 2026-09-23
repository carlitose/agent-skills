"""Disposable local Git integration; no Pi, model, network or provider mutation."""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ticket-autopilot" / "scripts"))
import driver  # noqa: E402
from ticket_driver import main  # noqa: E402

FAKE = Path(__file__).with_name("fake_leaf.py")


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


class DriverTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="tdr-tests-")
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / "seed"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        git(self.repo, "config", "user.name", "test")
        git(self.repo, "config", "user.email", "test@example.org")
        (self.repo / "README.md").write_bytes(b"seed\n")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-qm", "seed")
        self.base = git(self.repo, "rev-parse", "HEAD")
        self.task = Path(self.temp.name) / "TASK.md"
        self.task.write_bytes(b"MODE=ok\n")

    def arguments(self, run_id="one"):
        return ["run", "--candidate", "c1a", "--task", str(self.task), "--repo", str(self.repo),
                "--leaf", str(FAKE), "--run-id", run_id]

    def summary(self, run_id="one"):
        directory = Path(git(self.repo, "rev-parse", "--git-common-dir")) / "ticket-driver" / "runs" / run_id
        if not directory.is_absolute():
            directory = self.repo / directory
        return json.loads((directory / "summary.json").read_text()), directory

    def test_integrates_identical_tree_and_receipts_owned_by_driver(self):
        exit_code = main(self.arguments())
        summary, directory = self.summary()
        self.assertEqual(exit_code, 0, (directory / summary['receipts']['tests']['path']).read_text())
        self.assertEqual(summary["status"], "integrated")
        self.assertEqual(summary["base_commit"], self.base)
        self.assertEqual(summary["candidate_commit"], git(self.repo, "rev-parse", "HEAD"))
        self.assertEqual(summary["candidate_tree_oid"], git(self.repo, "rev-parse", "HEAD^{tree}"))
        self.assertEqual(summary["leaves"]["builder"]["tokens"], 11)
        self.assertEqual(len(summary["receipts"]), 2)
        for receipt in summary["receipts"].values():
            self.assertEqual(receipt["sha256"], hashlib.sha256((directory / receipt["path"]).read_bytes()).hexdigest())
        self.assertEqual(len((directory / "ledger.jsonl").read_text().splitlines()), 5)

    def test_red_tests_preserve_worktree_and_branch(self):
        self.task.write_bytes(b"MODE=red\n")
        self.assertEqual(main(self.arguments()), 1)
        summary, _ = self.summary()
        self.assertEqual(summary["failure"], "tests")
        self.assertEqual(git(self.repo, "rev-parse", "HEAD"), self.base)
        self.assertTrue(Path(summary["worktree"]).exists())
        self.assertIn("42", (Path(summary["worktree"]) / "calc.py").read_text())
        self.assertIn("7", (Path(summary["worktree"]) / "tests" / "test_calc.py").read_text())

    def test_timeout_preserves_partial_session_and_worktree(self):
        self.task.write_bytes(b"MODE=timeout\n")
        with patch.object(driver, "ROOT", Path(self.temp.name) / "skill"):
            root = driver.ROOT
            (root / "prompts").mkdir(parents=True)
            (root / "prompts" / "builder.md").write_bytes((SCRIPTS.parent / "prompts" / "builder.md").read_bytes())
            policy = json.loads((SCRIPTS.parent / "policy.json").read_text())
            policy["leaf_timeout_seconds"] = 0.4
            (root / "policy.json").write_text(json.dumps(policy))
            self.assertEqual(main(self.arguments()), 1)
        summary, directory = self.summary()
        self.assertEqual(summary["failure"], "leaf-timeout")
        self.assertTrue(Path(summary["worktree"]).exists())
        self.assertTrue((directory / "sessions" / "builder").exists())
        self.assertEqual(git(self.repo, "rev-parse", "HEAD"), self.base)

    def test_preflight_rejects_before_worktree(self):
        for name, change in (("missing", lambda: self.arguments() + ["--base", "no-such-base"]),
                             ("not-repo", lambda: [*self.arguments()[:], "--repo", self.temp.name])):
            with self.subTest(name=name):
                self.assertEqual(main(change()), 2)
                self.assertFalse((self.repo.parent / ".seed-ticket-driver-worktrees" / "one").exists())
        (self.repo / "dirty").write_bytes(b"untracked")
        self.assertEqual(main(self.arguments()), 2)

    def test_existing_summary_rejected_before_worktree(self):
        directory = self.repo / ".git" / "ticket-driver" / "runs" / "one"
        directory.mkdir(parents=True)
        (directory / "summary.json").write_bytes(b"{}")
        self.assertEqual(main(self.arguments()), 2)
        self.assertEqual((directory / "summary.json").read_bytes(), b"{}")
        self.assertFalse((self.repo.parent / ".seed-ticket-driver-worktrees" / "one").exists())

    def test_target_advances_during_leaf_keeps_candidate(self):
        self.task.write_bytes(f"MODE=move TARGET={self.repo}\n".encode())
        self.assertEqual(main(self.arguments()), 1)
        summary, _ = self.summary()
        self.assertEqual(summary["failure"], "integration")
        self.assertNotEqual(git(self.repo, "rev-parse", "HEAD"), self.base)
        self.assertTrue(Path(summary["worktree"]).exists())
        self.assertIsNotNone(summary["candidate_commit"])

    def test_live_requires_batch_authorization(self):
        args = [x for x in self.arguments() if x != str(FAKE)]
        args.remove("--leaf")
        self.assertEqual(main(args), 2)
        self.assertFalse((self.repo.parent / ".seed-ticket-driver-worktrees" / "one").exists())


if __name__ == "__main__":
    unittest.main()
