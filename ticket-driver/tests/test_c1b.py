"""Three fresh leaf sessions, fast-lane findings and bounded builder retry."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
sys.path.insert(0, str(HERE.parents[1] / "ticket-autopilot" / "scripts"))
from findings import parse_findings, planned_commands  # noqa: E402
from ticket_driver import main  # noqa: E402
from leaf import leaf_argv  # noqa: E402


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


class C1bTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="tdr-c1b-")
        self.addCleanup(tmp.cleanup)
        self.repo = Path(tmp.name) / "seed"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        git(self.repo, "config", "user.name", "test")
        git(self.repo, "config", "user.email", "test@example.org")
        (self.repo / "README.md").write_bytes(b"seed\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "seed")
        self.base = git(self.repo, "rev-parse", "HEAD")
        self.task = Path(tmp.name) / "TASK.md"

    def run_case(self, mode):
        self.task.write_text(f"MODE={mode}\n", encoding="utf-8")
        code = main(["run", "--candidate", "c1b", "--task", str(self.task), "--repo", str(self.repo),
                     "--leaf", str(HERE / "fake_c1b_leaf.py"), "--run-id", "one"])
        summary = json.loads((self.repo / ".git" / "ticket-driver" / "runs" / "one" / "summary.json").read_text())
        return code, summary

    def test_three_fresh_sessions_and_artifact_vs_observed_receipts(self):
        code, summary = self.run_case("clean")
        self.assertEqual(code, 0, summary)
        self.assertEqual(summary["status"], "integrated")
        self.assertEqual(set(summary["leaves"]), {"builder-1", "reviewer-1", "qa-1"})
        self.assertEqual([summary["leaves"][r]["cost"] for r in summary["leaves"]], [0.002] * 3)
        self.assertTrue(all(len(summary["leaves"][r]["session_files"]) == 1 for r in summary["leaves"]))
        self.assertEqual(summary["receipts"]["qa-artifact-1"]["kind"], "authored-by-model")
        self.assertTrue(any(name.startswith("tests-1-") for name in summary["receipts"]))
        self.assertFalse((self.repo / ".ticket-driver").exists())
        self.assertEqual(summary["candidate_tree_oid"], git(self.repo, "rev-parse", "HEAD^{tree}"))

    def test_one_retry_for_blocker_then_stop_on_second(self):
        code, summary = self.run_case("block-twice")
        self.assertEqual(code, 1)
        self.assertEqual(summary["status"], "stopped")
        self.assertIn("review blocker on second pass", summary["failure"])
        self.assertEqual(set(summary["leaves"]), {"builder-1", "reviewer-1", "builder-2", "reviewer-2"})
        self.assertEqual(git(self.repo, "rev-parse", "HEAD"), self.base)
        self.assertTrue(Path(summary["worktree"]).exists())
        self.assertIn("wrong boundary", (Path(summary["worktree"]) / ".ticket-driver" / "retry.md").read_text())

    def test_blocker_or_red_tests_get_one_successful_builder_retry(self):
        for mode in ("block-once", "tests-red-first"):
            with self.subTest(mode=mode):
                # A fresh repository/ID per case so no candidate is overwritten.
                if mode != "block-once":
                    self.setUp()
                code, summary = self.run_case(mode)
                self.assertEqual(code, 0, summary)
                self.assertIn("builder-2", summary["leaves"])
                self.assertEqual(summary["status"], "integrated")

    def test_reviewer_cannot_modify_candidate_without_gate(self):
        code, summary = self.run_case("reviewer-mutates")
        self.assertEqual(code, 1)
        self.assertEqual(summary["status"], "gated")
        self.assertEqual(summary["failure"], "reviewer modified candidate")
        self.assertEqual(git(self.repo, "rev-parse", "HEAD"), self.base)

    def test_unparsed_prose_opens_literal_gate(self):
        code, summary = self.run_case("unparsed")
        self.assertEqual(code, 1)
        self.assertEqual(summary["status"], "gated")
        self.assertIn("findings: unparsed", summary["failure"])
        self.assertEqual(git(self.repo, "rev-parse", "HEAD"), self.base)

    def test_operator_supplied_auth_extension_is_literal_argv(self):
        with patch.dict(os.environ, {"TICKET_DRIVER_PI_EXTENSION": str(HERE / "fake_c1b_leaf.py")}):
            argv = leaf_argv(None, {"provider": "anthropic", "model": "claude-sonnet-4-6", "thinking": "medium"},
                             HERE, "prompt")
        self.assertEqual(argv[-4:], ["-e", str(HERE / "fake_c1b_leaf.py"), "--", "prompt"])
        self.assertEqual(argv[0:2], ["pi", "-p"])

    def test_fast_lane_accepts_findings_and_rejects_unsafe_commands(self):
        parsed = parse_findings("intro\n[should-fix] calc.py:17 - wrong branch\n[nit] a.py:2 - spacing")
        self.assertEqual([r["severity"] for r in parsed["findings"]], ["should-fix", "nit"])
        self.assertEqual(parse_findings("maybe fine")["state"], "unparsed")
        self.assertEqual(parse_findings("No findings.\n")["state"], "clean")
        with self.assertRaises(ValueError):
            planned_commands("## Automated Checks\n```bash\npython -m unittest; rm -rf .\n```")


if __name__ == "__main__":
    unittest.main()
