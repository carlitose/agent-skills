"""Function risk batched into one loopback Jev request; directed review fake only."""
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
import driver  # noqa: E402
from autopilot.git_ops import semantic_candidate_ref  # noqa: E402
from function_diff import changed_functions  # noqa: E402
import test_c2 as fixture_support  # noqa: E402
FakeJev = fixture_support.FakeJev
git = fixture_support.git
from ticket_driver import main  # noqa: E402


class FunctionDiffTests(unittest.TestCase):
    def test_added_modified_renamed_deleted_decorated_nested_and_unsupported(self):
        with tempfile.TemporaryDirectory(prefix="tdr-ast-") as temp:
            repo = Path(temp) / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            git(repo, "config", "user.name", "test")
            git(repo, "config", "user.email", "test@example.org")
            before = "def untouched(x):\n    return x\ndef changed(x):\n    return x\ndef old_name():\n    return 1\ndef removed():\n    return 1\nclass Service:\n    @staticmethod\n    def decorated(x):\n        def nested():\n            return x\n        return nested()\n"
            (repo / "module.py").write_text(before, encoding="utf-8")
            git(repo, "add", "-A")
            git(repo, "commit", "-qm", "seed")
            after = before.replace("    return x\ndef old_name", "    return x + 1\ndef old_name")
            after = after.replace("def old_name():", "def new_name():")
            after = after.replace("def removed():\n    return 1\n", "")
            after = after.replace("            return x", "            return x * 2")
            after += "def added():\n    return 42\n"
            (repo / "module.py").write_text(after, encoding="utf-8")
            (repo / "notes.txt").write_text("not Python\n", encoding="utf-8")
            candidate = semantic_candidate_ref(repo, "a"*64)
            functions, unsupported = changed_functions(repo, candidate)
            named = {(f["function"], f["change"]) for f in functions}
            self.assertEqual(named, {("changed", "modified"), ("old_name", "deleted"),
                                     ("new_name", "added"), ("removed", "deleted"),
                                     ("added", "added"), ("Service.decorated", "modified"),
                                     ("Service.decorated.nested", "modified")})
            self.assertEqual(unsupported, [{"path": "notes.txt", "reason": "unsupported language"}])
            self.assertTrue(all(f["hunk"].startswith("--- old/") for f in functions))


class DirectedReviewParsingTests(unittest.TestCase):
    def test_section_local_clean_does_not_hide_other_function_findings(self):
        from findings import parse_directed_findings
        prose = ("# Directed Review\n## `billing/money.py:percentage`\nNo findings.\n"
                 "## `billing/discounts.py:apply_discount`\n"
                 "- nit `billing/discounts.py:43` \u2014 preserve exception cause\n"
                 "- nit `billing/discounts.py:25` \u2014 use a precise type\n"
                 "## Summary\nNo blockers.\n")
        result = parse_directed_findings(prose)
        self.assertEqual(result["state"], "parsed")
        self.assertEqual([(r["severity"], r["path"], r["line"]) for r in result["findings"]],
                         [("nit", "billing/discounts.py", 43), ("nit", "billing/discounts.py", 25)])

    def test_global_contradiction_and_pathless_nit_still_gate(self):
        from findings import parse_directed_findings
        global_clean = "No findings.\n## Findings\n[nit] billing/money.py:4 - round half up\n"
        pathless = "## Findings\n### Nit \u2014 no zero-subtotal test with a discount code\n"
        fenced = "```md\n[nit] billing/money.py:4 - illustrative\n```\n"
        self.assertEqual(parse_directed_findings(global_clean)["state"], "unparsed")
        self.assertEqual(parse_directed_findings(pathless)["state"], "unparsed")
        self.assertEqual(parse_directed_findings(fenced)["state"], "unparsed")


class C3Tests(unittest.TestCase):
    def setUp(self):
        fixture = fixture_support.C2Tests("test_batches_review_questions_and_observes_typed_usage")
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.fixture = fixture
        self.repo, self.task, self.skill, self.policy = fixture.repo, fixture.task, fixture.skill, fixture.policy
        self.base = fixture.base

    def run_case(self, candidate="c3a", mode="safe"):
        self.task.write_text(f"MODE={mode}\n", encoding="utf-8")
        with patch.object(driver, "ROOT", self.skill), patch.dict(os.environ, {"TYPESAFE_API_KEY": "fake-c3-key"}, clear=False):
            code = main(["run", "--candidate", candidate, "--task", str(self.task), "--repo", str(self.repo),
                         "--leaf", str(HERE / "fake_c3_leaf.py"), "--run-id", "one"])
        directory = self.repo / ".git" / "ticket-driver" / "runs" / "one"
        summary = json.loads((directory / "summary.json").read_text(encoding="utf-8"))
        return code, summary, directory

    def test_c3a_batches_per_function_scores_directs_only_two_and_integrates(self):
        code, summary, directory = self.run_case()
        self.assertEqual(code, 0, summary)
        self.assertEqual(summary["status"], "integrated")
        self.assertEqual({f["function"] for f in summary["risk"]["directed"]}, {"round_money", "boundary_tax"})
        risk_calls = [r for r in FakeJev.requests if any(key.startswith("risk_") for key in r["questions"])]
        self.assertEqual(len(risk_calls), 1)
        self.assertGreaterEqual(len(risk_calls[0]["questions"]), 3)
        prompt = (directory / "sessions" / "directed-reviewer-1" / "prompt.txt").read_text()
        self.assertIn("round_money", prompt)
        self.assertIn("boundary_tax", prompt)
        self.assertNotIn("helper(x)", prompt)
        self.assertEqual(summary["jev_usage"]["calls"], 4)
        records = [json.loads(line) for line in (directory / "judgments.jsonl").read_text().splitlines()]
        risk_records = [row for row in records if row["question"] == "risk.semantic_change"]
        self.assertEqual(len(risk_records), len(risk_calls[0]["questions"]))
        self.assertEqual(sum(row["directed"] for row in risk_records), 2)
        self.assertTrue(all("hunk_sha256" in row and "decision" in row for row in risk_records))
        self.assertEqual(git(self.repo, "rev-parse", "HEAD^{tree}"), summary["candidate_tree_oid"])

    def test_c3b_directed_blocker_reenters_one_builder_retry(self):
        code, summary, directory = self.run_case("c3b", mode="directed-block-once")
        self.assertEqual(code, 0, summary)
        self.assertIn("builder-2", summary["leaves"])
        self.assertIn("reviewer-2", summary["leaves"])
        self.assertIn("qa-2", summary["leaves"])
        self.assertIn("directed-reviewer-2", summary["leaves"])
        self.assertEqual(summary["status"], "integrated")
        self.assertEqual(git(self.repo, "rev-parse", "HEAD^{tree}"), summary["candidate_tree_oid"])

    def test_c3a_directed_blocker_retries_once_and_rechecks_tests_and_semantics(self):
        code, summary, directory = self.run_case("c3a", mode="directed-block-once")
        self.assertEqual(code, 0, summary)
        self.assertIn("builder-2", summary["leaves"])
        self.assertIn("tests-risk-retry", summary["receipts"])
        self.assertIn("directed-reviewer-2", summary["leaves"])
        self.assertEqual(summary["status"], "integrated")

    def test_directed_reviewer_relative_product_write_is_isolated_and_gated(self):
        code, summary, directory = self.run_case("c3a", mode="directed-mutate")
        self.assertEqual(code, 1)
        self.assertEqual(summary["status"], "gated")
        self.assertEqual(summary["failure"], "directed reviewer wrote outside artifact")
        self.assertIn("return 42", (Path(summary["worktree"]) / "calc.py").read_text(encoding="utf-8"))
        receipt = json.loads((directory / summary["receipts"]["directed-reviewer-1"]["path"]).read_text(encoding="utf-8"))
        self.assertNotEqual(receipt["cwd"], summary["worktree"])
        self.assertEqual(git(self.repo, "rev-parse", "HEAD"), self.base)

    def test_directed_blocker_without_line_does_not_invent_retry_location(self):
        code, summary, directory = self.run_case("c3a", mode="directed-no-line-block-once")
        self.assertEqual(code, 0, summary)
        retry = (directory / "sessions" / "builder-2" / "retry-copy.txt").read_text(encoding="utf-8")
        self.assertIn("[blocker] calc.py - money rounding edge", retry)
        self.assertNotIn(":None", retry)

    def test_persistent_directed_blocker_stops_after_one_retry_without_integration(self):
        code, summary, directory = self.run_case("c3b", mode="directed-always-block")
        self.assertEqual(code, 1)
        self.assertEqual(summary["status"], "stopped")
        self.assertIn("after retry", summary["failure"])
        self.assertEqual(git(self.repo, "rev-parse", "HEAD"), self.base)

    def test_c4_does_not_send_unallowed_repository_to_jev(self):
        self.policy["arbiter"]["external_judgment_allowed"]["repository_roots"] = []
        (self.skill / "policy.json").write_text(json.dumps(self.policy), encoding="utf-8")
        code, summary, directory = self.run_case("c4")
        self.assertEqual(code, 0, summary)
        self.assertEqual(summary["jev_usage"]["calls"], 0)
        self.assertEqual(FakeJev.requests, [])
        self.assertEqual(len(summary["risk"]["directed"]), len(summary["risk"]["functions"]))
        self.assertIn('"arbiter": "unavailable"', (directory / "judgments.jsonl").read_text())

    def test_c4_stays_in_original_directory_and_never_integrates_or_checks_gate_questions(self):
        code, summary, directory = self.run_case("c4")
        self.assertEqual(code, 0, summary)
        self.assertEqual(summary["status"], "completed-local")
        self.assertEqual(summary["worktree"], str(self.repo))
        self.assertEqual(summary["candidate_commit"], None)
        self.assertEqual(git(self.repo, "rev-parse", "HEAD"), self.base)
        self.assertEqual(summary["jev_usage"]["calls"], 1)
        self.assertEqual(len(FakeJev.requests), 1)
        self.assertNotIn("tests", summary["receipts"])
        self.assertEqual(set(summary["leaves"]), {"builder", "directed-reviewer-1"})
        self.assertFalse((self.repo.parent / ".project-ticket-driver-worktrees").exists())
        self.assertTrue((directory / "summary.json").is_file())


if __name__ == "__main__":
    unittest.main()
