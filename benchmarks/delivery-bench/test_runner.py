"""Offline tests for the delivery-bench runner: fake Pi, fake driver, fake judge, real Git.

    python -B -m unittest test_runner
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import judge
import runner

CANARY = "dbench-canary-toy-0123456789ab"

FAKE_PI = textwrap.dedent('''
    import json, os, sys, time, pathlib
    args = sys.argv[1:]
    session = pathlib.Path(args[args.index("--session-dir") + 1])
    plan_path = pathlib.Path(os.environ["FAKE_PLAN"])
    plan = json.loads(plan_path.read_text())
    step = plan.pop(0) if plan else "work"
    plan_path.write_text(json.dumps(plan))
    with open(os.environ["FAKE_LOG"], "a", encoding="utf-8") as log:
        log.write(json.dumps({"argv": args, "cwd": os.getcwd(), "step": step,
                              "jev": "TYPESAFE_API_KEY" in os.environ,
                              "nested": "PI_CODING_AGENT" in os.environ,
                              "first_line": pathlib.Path("TASK.md").read_text().splitlines()[0]}) + "\\n")
    n = int(pathlib.Path("TASK.md").read_text().splitlines()[0].split()[-1])
    session.mkdir(parents=True, exist_ok=True)
    files = sorted(session.glob("*.jsonl"))
    path = files[-1] if ("--continue" in args and files) else session / f"s{len(files)}.jsonl"
    def emit(message):
        with open(path, "a", encoding="utf-8") as out:
            out.write(json.dumps({"type": "message", "timestamp": "2026-09-26T10:00:0%dZ" % n,
                                  "message": message}) + "\\n")
    usage = {"input": 100, "output": 50, "cacheRead": 10, "cacheWrite": 0, "totalTokens": 160,
             "cost": {"total": 0.01}}
    work = {"role": "assistant", "usage": usage, "stopReason": "stop",
            "content": [{"type": "toolCall", "name": "write"}]}
    if step == "crash":
        pathlib.Path("junk.txt").write_text("residue")
        sys.exit(3)
    if step == "provider-error":
        emit({"role": "assistant", "content": [], "stopReason": "error",
              "errorMessage": "503 Service Unavailable", "usage": {**usage, "output": 0}})
        sys.exit(1)
    if step == "sleep":
        emit(work)
        time.sleep(60)
    pathlib.Path(f"delivered_{n}.txt").write_text("ok")
    if step == "trap":
        pathlib.Path("trap.txt").write_text("shortcut")
    if step == "leak":
        work = {**work, "content": [{"type": "text", "text": "found CANARY"}]}
    emit(work)
''').replace("CANARY", CANARY)

FAKE_DRIVER = textwrap.dedent('''
    import json, os, sys, pathlib, subprocess
    args = sys.argv[1:]
    get = lambda flag: args[args.index(flag) + 1]
    repo = pathlib.Path(get("--repo"))
    authorization = json.loads(pathlib.Path(get("--live-authorization")).read_text())
    with open(os.environ["FAKE_LOG"], "a", encoding="utf-8") as log:
        log.write(json.dumps({"argv": args, "authorization": authorization,
                              "jev": "TYPESAFE_API_KEY" in os.environ}) + "\\n")
    n = int((repo / "TASK.md").read_text().splitlines()[0].split()[-1])
    run = repo / ".git" / "ticket-driver" / "runs" / f"run{n}"
    (run / "sessions" / "builder").mkdir(parents=True)
    usage = {"input": 300, "output": 30, "cacheRead": 0, "cacheWrite": 0, "totalTokens": 330,
             "cost": {"total": 0.02}}
    (run / "sessions" / "builder" / "leaf.jsonl").write_text(json.dumps({"type": "message",
        "message": {"role": "assistant", "usage": usage, "stopReason": "stop",
                    "content": [{"type": "toolCall"}]}}) + "\\n")
    (run / "summary.json").write_text(json.dumps({"status": "integrated",
        "jev_usage": {"calls": 2, "input_tokens": 1000000, "output_tokens": 10}}))
    (repo / f"delivered_{n}.txt").write_text("ok")
    git = ["git", "-C", str(repo), "-c", "user.name=d", "-c", "user.email=d@x"]
    subprocess.run(git + ["add", "-A"], check=True)
    subprocess.run(git + ["commit", "-qm", f"driver {n}"], check=True)
    print(json.dumps({"status": "integrated"}))
''')


def fake_judge(project: Path, scenario: Path, request: int) -> dict:
    """Features are files the fake arm writes; the trap is a shortcut file."""
    project = Path(project)
    checks = []
    for n in range(1, request + 1):
        kind = "feature" if n == request else "invariant"
        ok = (project / f"delivered_{n}.txt").is_file()
        checks.append({"id": f"r{n}.f", "kind": kind, "request": n, "status": "pass" if ok else "fail"})
    checks.append({"id": "r1.latent", "kind": "latent", "request": 1, "status": "fail"})
    if request >= 2:
        checks.append({"id": "r2.trap", "kind": "trap", "request": 2,
                       "status": "fail" if (project / "trap.txt").exists() else "pass",
                       "trap": {"type": "convention", "rule": 1, "temptation": 2, "distance": 1}})
    digest = judge.tree_digest(project)
    return {"schema": 1, "scenario": "toy", "request": request, "suite_sha256": "0" * 64,
            "tree_before": digest, "tree_after": digest, "identical": True,
            "checks": checks, "axes": judge.axes(checks, request)}


class Fixture:
    def __init__(self, root: Path, arms=("bare",), *, request_cap=60, chain_cap=None, plan=()):
        self.root = root
        self.scenario = root / "private" / "toy"
        (self.scenario / "hidden").mkdir(parents=True)
        (self.scenario / "hidden" / "run.py").write_text(f"# {CANARY}\n")
        (self.scenario / "seed").mkdir()
        (self.scenario / "seed" / "README.md").write_text("toy\n")
        (self.scenario / "requests").mkdir()
        for n in (1, 2, 3):
            (self.scenario / "requests" / f"{n:02d}.md").write_text(
                f"# Request {n}\n\nDo {n}.\n<!-- {CANARY} -->\n", encoding="utf-8")
        (self.scenario / "scenario.json").write_text(json.dumps({
            "schema": 1, "id": "toy", "image": "none", "command": ["true"], "requests": 3,
            "timeout_seconds": 30, "canary": CANARY, "language": "python",
            "test_command": "python -B -m unittest"}))
        self.authority = root / "authority.json"
        self.authority.write_text(json.dumps({
            "schema": 1, "lot": "t1", "authorized_by": "test", "statement": "offline test",
            "arms": list(arms), "scenarios": ["toy"], "repetitions": 1, "max_length": 3,
            "jev_spend_authorized": True}))
        self.key = root / "jev.env"
        self.key.write_text("TYPESAFE_API_KEY=abcdefghijklmnopqrstuvwxyz0123\n")
        self.plan = root / "plan.json"
        self.plan.write_text(json.dumps(list(plan)))
        self.log = root / "log.jsonl"
        (root / "fake_pi.py").write_text(FAKE_PI)
        (root / "fake_driver.py").write_text(FAKE_DRIVER)
        self.lot = root / "lot"
        runner.init_lot(self.lot, lot_id="t1", authority=self.authority,
                        scenarios={"toy": self.scenario}, arms=list(arms), repetitions=1,
                        runs_root=root / "runs", request_cap_seconds=request_cap,
                        chain_cap_seconds=chain_cap, jev_key_file=self.key,
                        pi_command=[sys.executable, "-B", str(root / "fake_pi.py")],
                        driver_command=[sys.executable, "-B", str(root / "fake_driver.py")])

    def run(self, cell: str, through: int, judge_fn=fake_judge) -> dict:
        saved = dict(os.environ)
        os.environ.update(FAKE_PLAN=str(self.plan), FAKE_LOG=str(self.log), PI_CODING_AGENT="1")
        try:
            return runner.run_cell(self.lot, cell, through, judge_fn=judge_fn)
        finally:
            os.environ.clear()
            os.environ.update(saved)

    def calls(self) -> list[dict]:
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def project(self, cell: str) -> Path:
        lot = json.loads((self.lot / "lot.json").read_text())
        return Path(lot["cells"][cell]["arm_dir"]) / "project"


def git(project: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(project), *args], capture_output=True, text=True,
                          check=True).stdout.strip()


class ChainTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="dbench-runner-")
        self.root = Path(self.tmp.name)
        runner.JUDGE_BACKOFF_SECONDS = 0

    def tearDown(self):
        self.tmp.cleanup()

    def test_chain_delivers_requests_in_order_and_profiles_each(self):
        fx = Fixture(self.root, plan=["work", "trap", "work"])
        record = fx.run("toy.bare.r1", 3)
        self.assertEqual([r["request"] for r in record["requests"]], [1, 2, 3])
        self.assertEqual([c["first_line"] for c in fx.calls()], ["# Request 1", "# Request 2", "# Request 3"])
        self.assertEqual(["--continue" in c["argv"] for c in fx.calls()], [False, True, True])
        self.assertFalse(any(c["nested"] or c["jev"] for c in fx.calls()))
        project = fx.project("toy.bare.r1")
        self.assertNotIn("canary", (project / "TASK.md").read_text())
        self.assertEqual(git(project, "log", "--format=%an %s", "--", "TASK.md").splitlines(),
                         ["bench TASK 3", "bench TASK 2", "bench TASK 1"])
        self.assertEqual(git(project, "rev-parse", "HEAD~0:TASK.md"), git(project, "rev-parse", "origin/main:TASK.md"))
        self.assertEqual(git(project, "status", "--porcelain").splitlines(),
                         ["?? delivered_1.txt", "?? delivered_2.txt", "?? delivered_3.txt", "?? trap.txt"])
        for request in record["requests"]:
            self.assertEqual(request["status"], "judged")
            self.assertEqual(request["usage"]["input"], 100)  # per request, not cumulative
            self.assertAlmostEqual(request["usage"]["cost_usd"], 0.01)
            self.assertEqual(request["attempts"][0]["class"], "agent")
            self.assertTrue(request["axes"]["acceptance"]["accepted"])
        self.assertEqual(record["requests"][1]["axes"]["compass"]["traps_violated"][0]["distance"], 1)
        self.assertEqual(record["length"], 3)
        self.assertFalse(record["invalid"])
        saved = json.loads((fx.lot / "cells" / "toy.bare.r1" / "cell.json").read_text())
        self.assertEqual(saved["schema"], 1)
        self.assertEqual(saved["requests"][2]["judge"]["path"].replace("\\", "/").split("/")[-2:], ["judge", "03.json"])

    def test_cell_is_extended_not_replayed(self):
        fx = Fixture(self.root)
        first = fx.run("toy.bare.r1", 1)
        again = fx.run("toy.bare.r1", 1)
        self.assertEqual(len(fx.calls()), 1)
        self.assertEqual(first["requests"], again["requests"])
        longer = fx.run("toy.bare.r1", 3)
        self.assertEqual(longer["requests"][0], first["requests"][0])
        self.assertEqual([c["first_line"] for c in fx.calls()], ["# Request 1", "# Request 2", "# Request 3"])

    def test_infrastructure_failure_restores_state_and_repeats(self):
        fx = Fixture(self.root, plan=["crash", "provider-error", "work"])
        record = fx.run("toy.bare.r1", 1)
        attempts = record["requests"][0]["attempts"]
        self.assertEqual([a["class"] for a in attempts], ["infra:pi-crash", "infra:provider", "agent"])
        self.assertFalse((fx.project("toy.bare.r1") / "junk.txt").exists())
        self.assertEqual(record["requests"][0]["infra_usage"]["input"], 100)
        self.assertTrue(record["requests"][0]["axes"]["acceptance"]["accepted"])

    def test_infrastructure_retries_stop_after_two(self):
        fx = Fixture(self.root, plan=["crash", "crash", "crash", "work"])
        request = fx.run("toy.bare.r1", 1)["requests"][0]
        self.assertEqual(len(request["attempts"]), 3)
        self.assertTrue(request["infra_exhausted"])
        self.assertEqual(request["status"], "judged")
        self.assertFalse(request["axes"]["acceptance"]["accepted"])

    def test_request_timeout_counts_and_is_judged(self):
        fx = Fixture(self.root, request_cap=3, plan=["sleep"])
        request = fx.run("toy.bare.r1", 1)["requests"][0]
        self.assertTrue(request["timed_out"])
        self.assertEqual(request["attempts"][0]["class"], "agent")
        self.assertEqual(request["status"], "judged")

    def test_chain_cap_stops_the_arm_and_keeps_the_partial_profile(self):
        fx = Fixture(self.root, request_cap=2, chain_cap=4, plan=["sleep", "sleep", "work"])
        record = fx.run("toy.bare.r1", 3)
        self.assertTrue(record["chain_cap_hit"])
        self.assertEqual([r["status"] for r in record["requests"]], ["judged", "judged", "not-delivered"])
        self.assertTrue(all(r["timed_out"] for r in record["requests"][:2]))
        self.assertFalse(record["requests"][2]["axes"]["acceptance"]["accepted"])
        self.assertEqual(len(fx.calls()), 2)

    def test_canary_in_a_session_invalidates_the_cell(self):
        fx = Fixture(self.root, plan=["leak"])
        record = fx.run("toy.bare.r1", 1)
        self.assertTrue(record["invalid"])
        self.assertEqual(record["audit_hits"][0]["pattern"], "canary")
        self.assertNotIn(CANARY, json.dumps(record))

    def test_judge_errors_are_retried_then_recorded(self):
        fx = Fixture(self.root)
        failures = iter([judge.JudgeError("boom"), judge.JudgeError("boom")])

        def flaky(project, scenario, request):
            error = next(failures, None)
            if error:
                raise error
            return fake_judge(project, scenario, request)
        request = fx.run("toy.bare.r1", 1, judge_fn=flaky)["requests"][0]
        self.assertEqual((request["status"], request["judge"]["attempts"]), ("judged", 3))

    def test_arm_commands_follow_the_contract(self):
        fx = Fixture(self.root, arms=("bare", "skills-only", "autopilot"))
        for cell in ("toy.bare.r1", "toy.skills-only.r1", "toy.autopilot.r1"):
            fx.run(cell, 1)
        bare, skills, autopilot = (c["argv"] for c in fx.calls())
        for argv in (bare, skills, autopilot):
            for flag in ("--no-extensions", "--no-context-files", "--approve", "-p"):
                self.assertIn(flag, argv)
            self.assertEqual(argv[argv.index("--model") + 1], "gpt-6-sol")
            self.assertEqual(argv[argv.index("--thinking") + 1], "high")
            self.assertTrue(argv[-1].startswith(runner.PROMPT))
        self.assertIn("--no-skills", bare)
        self.assertNotIn("--no-skills", skills + autopilot)
        self.assertTrue(skills[-1].endswith(runner.SKILLS_ONLY_SUFFIX))
        self.assertIn("--provider-mode simulated", autopilot[-1])
        project = fx.project("toy.bare.r1")
        self.assertTrue((project / ".pi" / "settings.json").is_file())
        self.assertNotIn(".pi", git(project, "status", "--porcelain"))

    def test_driver_arm_gets_a_cell_authorization_and_only_c3a_gets_jev(self):
        fx = Fixture(self.root, arms=("driver-c1a", "driver-c3a"))
        c1a = fx.run("toy.driver-c1a.r1", 2)
        c3a = fx.run("toy.driver-c3a.r1", 1)
        calls = fx.calls()
        self.assertEqual([c["jev"] for c in calls], [False, False, True])
        project = fx.project("toy.driver-c3a.r1")
        argv = calls[2]["argv"]
        self.assertEqual(argv[:3], ["run", "--candidate", "c3a"])
        self.assertEqual(Path(argv[argv.index("--task") + 1]), project.resolve() / "TASK.md")
        self.assertEqual(calls[2]["authorization"]["repository"], str(project.resolve()))
        self.assertEqual(calls[2]["authorization"]["candidates"], ["c3a"])
        self.assertTrue(calls[2]["authorization"]["jev_spend_authorized"])
        self.assertFalse(calls[0]["authorization"]["jev_spend_authorized"])
        self.assertTrue(project.parent.name.startswith("driver-"))
        request = c3a["requests"][0]
        self.assertEqual(request["usage"]["input"], 300)
        self.assertEqual(request["jev"], {"calls": 2, "input_tokens": 1000000, "output_tokens": 10,
                                          "usd_estimate": 0.042})
        self.assertEqual(c1a["requests"][1]["usage"]["input"], 300)  # only the new driver run
        self.assertEqual(request["driver"]["status"], ["integrated"])

    def test_driver_copy_changes_only_configuration(self):
        fx = Fixture(self.root, arms=("driver-c3a",))
        fx.run("toy.driver-c3a.r1", 1)
        copies = runner.prepare_drivers(fx.lot, source=runner.ROOT)
        driver = Path(copies["toy"]["path"]) / "ticket-driver"
        policy = json.loads((driver / "policy.json").read_text(encoding="utf-8"))
        self.assertEqual((policy["provider"], policy["model"], policy["thinking"]),
                         ("openai-codex", "gpt-6-sol", "high"))
        self.assertEqual(policy["test_command"], runner.driver_test_command("python"))
        self.assertIn('"--no-extensions", "--no-context-files"', (driver / "scripts" / "leaf.py").read_text())
        sys.path.insert(0, str(driver / "scripts"))
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("copied_arbiter", driver / "scripts" / "arbiter.py")
            arbiter = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(arbiter)
        finally:
            sys.path.pop(0)
        project = fx.project("toy.driver-c3a.r1")
        self.assertTrue(arbiter.allowed(project, policy["arbiter"]))
        self.assertFalse(arbiter.allowed(self.root / "private" / "toy" / "seed", policy["arbiter"]))
        lot = json.loads((fx.lot / "lot.json").read_text())
        self.assertEqual(lot["driver_copies"]["toy"]["policy.json_sha256"], runner.sha256_file(driver / "policy.json"))
        with self.assertRaises(runner.LotError):
            runner.prepare_drivers(fx.lot, source=runner.ROOT)

    def test_changed_authority_blocks_the_lot(self):
        fx = Fixture(self.root)
        fx.authority.write_text(fx.authority.read_text().replace("offline", "edited"))
        with self.assertRaises(runner.LotError):
            fx.run("toy.bare.r1", 1)

    def test_length_beyond_authority_is_refused(self):
        fx = Fixture(self.root)
        with self.assertRaises(runner.LotError):
            fx.run("toy.bare.r1", 4)


if __name__ == "__main__":
    unittest.main()
