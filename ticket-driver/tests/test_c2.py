"""Jev HTTP contract is exercised only against a loopback fake server."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
sys.path.insert(0, str(HERE.parents[1] / "ticket-autopilot" / "scripts"))
import driver  # noqa: E402
import approval  # noqa: E402
from ticket_driver import main  # noqa: E402


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


class FakeJev(BaseHTTPRequestHandler):
    requests = []
    rate_limit = 0

    def do_POST(self):
        self.__class__.requests.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
        if self.__class__.rate_limit:
            self.__class__.rate_limit -= 1
            self.send_response(429 if self.__class__.rate_limit % 2 == 0 else 529)
            self.end_headers()
            return
        state, selected = self.requests[-1]["state"], self.requests[-1]["questions"]
        mode = state.get("acceptance_text", "")
        answers = {}
        for key, question in selected.items():
            if question["type"] == "noul":
                uncertain = ("MODE=uncertain" in mode or "MODE=gate" in mode or
                             (key == "review.findings_block" and "MODE=directed-block-once-judge-twice" in mode))
                probability = .5 if uncertain else .95 if "MODE=negative" in mode else .05 if key == "review.findings_block" else .95
                answers[key] = {"type": "noul", "noul": probability}
            elif question["type"] == "score":
                index = int(key.split("_")[-1])
                function = state["functions"][index]["function"]
                high = function in ("round_money", "boundary_tax")
                probabilities = {str(level): (.9 if level == (3 if high else 0) else .1 / 3) for level in range(4)}
                answers[key] = {"type": "score", "score": 2.85 if high else .15,
                                "legend": {str(i): text for i, text in enumerate(question["criteria"])},
                                "probabilities": probabilities, "confidence": .9}
            else:
                selected_choice = "simulated" if key == "qa.evidence_class" else "fix-in-place"
                options = list(question["criteria"])
                probabilities = {name: (.9 if name == selected_choice else .1 / (len(options) - 1)) for name in options}
                answers[key] = {"type": "choice", "choice": selected_choice, "probabilities": probabilities, "confidence": .9}
        body = json.dumps({"model": "jev-fake", "answers": answers,
                           "usage": {"input_tokens": 10, "output_tokens": 2}}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        pass


class C2Tests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="tdr-c2-")
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        self.repo = root / "project"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        git(self.repo, "config", "user.name", "test")
        git(self.repo, "config", "user.email", "test@example.org")
        (self.repo / "README.md").write_bytes(b"seed\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "seed")
        self.base = git(self.repo, "rev-parse", "HEAD")
        self.task = root / "TASK.md"
        self.skill = root / "skill"
        self.skill.mkdir()
        for part in ("policy.json",):
            shutil.copy2(HERE.parent / part, self.skill / part)
        for directory in ("prompts", "questions"):
            shutil.copytree(HERE.parent / directory, self.skill / directory)
        self.policy = json.loads((self.skill / "policy.json").read_text())
        self.policy["arbiter"]["external_judgment_allowed"]["repository_roots"] = [str(self.repo)]
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), FakeJev)
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(lambda: (self.server.shutdown(), self.server.server_close(), thread.join(timeout=2)))
        self.policy["arbiter"]["endpoint"] = f"http://127.0.0.1:{self.server.server_port}/v1/systemone"
        self.save_policy()
        FakeJev.requests = []
        FakeJev.rate_limit = 0

    def save_policy(self):
        (self.skill / "policy.json").write_text(json.dumps(self.policy), encoding="utf-8")

    def run_case(self, candidate="c2a", mode="safe", key="fake-secret-not-persisted"):
        self.task.write_text(f"MODE={mode}\n", encoding="utf-8")
        with patch.object(driver, "ROOT", self.skill), patch.dict(os.environ, {"TYPESAFE_API_KEY": key}, clear=False):
            code = main(["run", "--candidate", candidate, "--task", str(self.task), "--repo", str(self.repo),
                         "--leaf", str(HERE / "fake_c2_leaf.py"), "--run-id", "one"])
        directory = self.repo / ".git" / "ticket-driver" / "runs" / "one"
        summary = json.loads((directory / "summary.json").read_text(encoding="utf-8"))
        return code, summary, directory

    def test_live_missing_key_refuses_before_execute(self):
        self.task.write_text("MODE=safe\n", encoding="utf-8")
        authorization = self.task.parent / "live-authorization.json"
        authorization.write_text(json.dumps({"batch_id": "test-c2a", "repository": str(self.repo),
                                             "candidates": ["c2a"], "jev_spend_authorized": True}), encoding="utf-8")
        with patch.dict(os.environ, {"TYPESAFE_API_KEY": ""}), patch("ticket_driver.execute", return_value={"status": "integrated"}) as execute:
            code = main(["run", "--candidate", "c2a", "--task", str(self.task),
                         "--repo", str(self.repo), "--live-authorization", str(authorization)])
        self.assertEqual(code, 2)
        execute.assert_not_called()
        self.assertFalse((self.repo / ".git" / "ticket-driver").exists())

    def test_live_key_is_absent_during_execute_and_restored_on_failure(self):
        secret = "fake-secret-not-persisted"
        def fail_inside_driver(_args):
            self.assertFalse("TYPESAFE_API_KEY" in os.environ, "credential inherited by driver child scope")
            child = subprocess.check_output([sys.executable, "-B", "-c",
                "import os; print('TYPESAFE_API_KEY' in os.environ)"], text=True)
            self.assertEqual(child.strip(), "False")
            raise RuntimeError("deliberate failure")
        with patch.dict(os.environ, {"TYPESAFE_API_KEY": secret}), patch("ticket_driver.execute", side_effect=fail_inside_driver):
            code = main(["run", "--candidate", "c2a", "--task", str(self.task),
                         "--repo", str(self.repo), "--leaf", str(HERE / "fake_c2_leaf.py")])
            self.assertEqual(os.environ.get("TYPESAFE_API_KEY"), secret)
        self.assertEqual(code, 2)

    def test_batches_review_questions_and_observes_typed_usage(self):
        code, summary, directory = self.run_case("c2a")
        self.assertEqual(code, 0, summary)
        self.assertEqual(summary["status"], "integrated")
        self.assertEqual(set(FakeJev.requests[0]["questions"]), {"review.findings_block", "review.scope_complete"})
        self.assertIn("candidate_diff", FakeJev.requests[0]["state"])
        self.assertIn("acceptance_text", FakeJev.requests[0]["state"])
        self.assertEqual(summary["jev_usage"], {"calls": 3, "input_tokens": 30, "output_tokens": 6})
        self.assertEqual(len(summary["question_hashes"]), 6)
        self.assertEqual(len((directory / "judgments.jsonl").read_text().splitlines()), 4)
        self.assertEqual(git(self.repo, "rev-parse", "HEAD^{tree}"), summary["candidate_tree_oid"])
        self.assertNotIn("fake-secret-not-persisted", "".join(p.read_text(encoding="utf-8") for p in directory.rglob("*") if p.is_file()))

    def test_c2b_uses_fresh_review_and_qa_plus_arbiter(self):
        code, summary, _ = self.run_case("c2b")
        self.assertEqual(code, 0, summary)
        self.assertIn("reviewer-1", summary["leaves"])
        self.assertIn("qa-1", summary["leaves"])
        self.assertEqual(summary["jev_usage"]["calls"], 3)
        self.assertEqual(summary["status"], "integrated")

    def test_unparsed_review_is_arbitrated_in_c2b_not_gated_by_c1b_parser(self):
        code, summary, directory = self.run_case("c2b", mode="unparsed")
        self.assertEqual(code, 0, summary)
        self.assertEqual(summary["status"], "integrated")
        self.assertIn('"state": "unparsed"', (directory / "ledger.jsonl").read_text())

    def test_jev_blocker_vetoes_clean_fast_lane_without_builder_self_approval(self):
        code, summary, directory = self.run_case("c2b", mode="negative")
        self.assertEqual(code, 1)
        self.assertEqual(summary["status"], "gated")
        self.assertIn("semantic gate: review", summary["failure"])
        self.assertEqual(git(self.repo, "rev-parse", "HEAD"), self.base)
        self.assertEqual(summary["jev_usage"]["calls"], 3)

    def test_uncertainty_uses_fresh_judge_and_then_gates_on_ambiguity(self):
        code, summary, directory = self.run_case(mode="gate")
        self.assertEqual(code, 1)
        self.assertEqual(summary["status"], "gated")
        self.assertIn("review.findings_block", summary["failure"])
        self.assertIn("judge=I cannot determine", summary["failure"])
        self.assertIn("judge-1", summary["leaves"])
        self.assertEqual(len((directory / "gates.jsonl").read_text().splitlines()), 1)
        self.assertEqual(git(self.repo, "rev-parse", "HEAD"), self.base)

    def test_explicit_approval_resumes_frozen_gate_without_overwriting_summary(self):
        _, summary, directory = self.run_case(mode="gate")
        original = (directory / "summary.json").read_bytes()
        with patch.object(approval, "ROOT", self.skill), patch.dict(os.environ, {"TYPESAFE_API_KEY": "fake-secret-not-persisted"}):
            code = main(["approve", "--repo", str(self.repo), "one", "--actor", "test-operator", "--reason", "reviewed disputed hunk"])
            self.assertEqual(os.environ.get("TYPESAFE_API_KEY"), "fake-secret-not-persisted")
        self.assertEqual(code, 0)
        self.assertEqual((directory / "summary.json").read_bytes(), original)
        result = json.loads((directory / "approval-result.json").read_text())
        self.assertEqual(result["status"], "integrated")
        self.assertEqual(result["candidate_commit"], git(self.repo, "rev-parse", "HEAD"))
        self.assertEqual(main(["approve", "--repo", str(self.repo), "one", "--actor", "again", "--reason", "again"]), 2)

    def test_approval_refuses_candidate_drift(self):
        _, summary, directory = self.run_case(mode="gate")
        Path(summary["worktree"], "calc.py").write_text("def answer():\n    return 0\n", encoding="utf-8")
        with patch.object(approval, "ROOT", self.skill):
            code = main(["approve", "--repo", str(self.repo), "one", "--actor", "operator", "--reason", "reviewed"])
        self.assertEqual(code, 2)
        self.assertFalse((directory / "approval-result.json").exists())
        self.assertEqual(git(self.repo, "rev-parse", "HEAD"), self.base)

    def test_uncertain_jev_is_resolved_by_fresh_judge_without_self_attestation(self):
        code, summary, directory = self.run_case(mode="uncertain")
        self.assertEqual(code, 0, summary)
        self.assertIn("judge-1", summary["leaves"])
        self.assertTrue((directory / "escalations.jsonl").is_file())

    def test_unallowed_repo_missing_key_and_rate_limit_fall_back_without_leaking_key(self):
        for kind in ("unallowed", "missing", "rate-limit"):
            with self.subTest(kind=kind):
                if kind != "unallowed":
                    self.setUp()
                if kind == "unallowed":
                    self.policy["arbiter"]["external_judgment_allowed"]["repository_roots"] = []
                if kind == "rate-limit":
                    FakeJev.rate_limit = 5
                self.save_policy()
                code, summary, directory = self.run_case(key="" if kind == "missing" else "fake-secret-not-persisted")
                self.assertEqual(code, 0, summary)
                self.assertIn("judge-1", summary["leaves"])
                self.assertIn('"arbiter": "unavailable"', (directory / "judgments.jsonl").read_text())
                self.assertNotIn("fake-secret-not-persisted", "".join(p.read_text(encoding="utf-8") for p in directory.rglob("*.json*")))
                if kind in ("unallowed", "missing"):
                    self.assertEqual(len(FakeJev.requests), 0)


if __name__ == "__main__":
    unittest.main()
