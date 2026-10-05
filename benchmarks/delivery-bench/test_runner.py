"""Offline tests for the delivery-bench runner: fake Pi, fake driver, fake judge, real Git.

    python -B -m unittest test_runner
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

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
    if step == "refused":
        emit({"role": "assistant", "content": [], "stopReason": "error", "usage": {**usage, "output": 0},
              "errorMessage": '400 {"type":"error","error":{"type":"invalid_request_error",'
                              '"message":"Third-party apps now draw from extra usage, not plan limits."}}'})
        sys.exit(0)
    if step in ("cut", "overflow"):  # the model worked, then a late error ended the session
        pathlib.Path(f"delivered_{n}.txt").write_text("ok")
        emit(work)
        emit({"role": "assistant", "content": [], "stopReason": "error", "usage": {**usage, "output": 0},
              "errorMessage": '429 {"type":"error","error":{"type":"rate_limit_error","message":'
                              '"This request would exceed your account rate limit."}}' if step == "cut"
                              else '400 {"type":"error","error":{"type":"invalid_request_error",'
                                   '"message":"prompt is too long: 1000001 tokens > 1000000 maximum"}}'})
        sys.exit(1)
    if step == "sleep":
        emit(work)
        time.sleep(60)
    if step == "nul":  # a Windows device name, as a build redirected to NUL from a POSIX shell leaves
        for folder in (pathlib.Path.cwd(), pathlib.Path.cwd().parent / ".project-ticket-driver-worktrees" / "t"):
            folder.mkdir(parents=True, exist_ok=True)
            name = str(folder.resolve() / "NUL")
            with open(os.sep * 2 + "?" + os.sep + name if os.name == "nt" else name, "w") as out:
                out.write("build log")
    pathlib.Path(f"delivered_{n}.txt").write_text("ok")
    if step == "trap":
        pathlib.Path("trap.txt").write_text("shortcut")
    if step == "leak":
        work = {**work, "content": [{"type": "text", "text": "found CANARY"}]}
    if step == "compact":
        with open(path, "a", encoding="utf-8") as out:
            out.write(json.dumps({"type": "compaction", "timestamp": "2026-09-26T10:00:0%dZ" % n,
                                  "summary": "## Goal", "tokensBefore": 206743,
                                  "usage": {"input": 113062, "output": 1058,
                                            "cost": {"total": 0.24}}}) + "\\n")
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
                              "jev": "TYPESAFE_API_KEY" in os.environ,
                              "extension": os.environ.get("TICKET_DRIVER_PI_EXTENSION")}) + "\\n")
    n = int((repo / "TASK.md").read_text().splitlines()[0].split()[-1])
    run = repo / ".git" / "ticket-driver" / "runs" / f"run{n}"
    (run / "sessions" / "builder").mkdir(parents=True)
    usage = {"input": 300, "output": 30, "cacheRead": 0, "cacheWrite": 0, "totalTokens": 330,
             "cost": {"total": 0.02}}
    (run / "sessions" / "builder" / "leaf.jsonl").write_text(json.dumps({"type": "message",
        "message": {"role": "assistant", "usage": usage, "stopReason": "stop",
                    "content": [{"type": "toolCall"}]}}) + "\\n")
    marker = pathlib.Path(os.environ["FAKE_LOG"]).parent / "cut-once"
    if os.environ.get("FAKE_DRIVER_STATUS") == "cut" and not marker.exists():
        marker.write_text("")
        with open(run / "sessions" / "builder" / "leaf.jsonl", "a", encoding="utf-8") as out:
            out.write(json.dumps({"type": "message", "message": {
                "role": "assistant", "content": [], "stopReason": "error", "usage": usage,
                "errorMessage": '{"type":"error","error":{"type":"overloaded_error","message":"Overloaded"}}'}})
                + "\\n")
        (run / "summary.json").write_text(json.dumps({"status": "failed", "failure": "leaf"}))
        print(json.dumps({"status": "failed"}))
        sys.exit(1)
    if os.environ.get("FAKE_DRIVER_STATUS") == "gated":
        tree = repo.parent / ".project-ticket-driver-worktrees" / f"run{n}"
        tree.mkdir(parents=True)
        (tree / f"delivered_{n}.txt").write_text("ok")
        (run / "summary.json").write_text(json.dumps({"status": "gated", "worktree": str(tree),
            "jev_usage": {"calls": 1, "input_tokens": 10, "output_tokens": 1}}))
        print(json.dumps({"status": "gated"}))
        sys.exit(1)
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
    def __init__(self, root: Path, arms=("bare",), *, request_cap=60, chain_cap=None, plan=(),
                 model=None, thinking=None, authority_extra=None, scenario_extra=None, pi_extension=None,
                 pi_config_root=None):
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
            "test_command": "python -B -m unittest", **(scenario_extra or {})}))
        self.authority = root / "authority.json"
        self.authority.write_text(json.dumps({
            "schema": 1, "lot": "t1", "authorized_by": "test", "statement": "offline test",
            "arms": list(arms), "scenarios": ["toy"], "repetitions": 1, "max_length": 3,
            "jev_spend_authorized": True, **(authority_extra or {})}))
        self.key = root / "jev.env"
        self.key.write_text("TYPESAFE_API_KEY=abcdefghijklmnopqrstuvwxyz0123\n")
        self.plan = root / "plan.json"
        self.plan.write_text(json.dumps(list(plan)))
        self.log = root / "log.jsonl"
        (root / "fake_pi.py").write_text(FAKE_PI)
        (root / "fake_driver.py").write_text(FAKE_DRIVER)
        self.lot = root / "lot"
        chosen = {key: value for key, value in (("model", model), ("thinking", thinking),
                                                ("pi_extension", pi_extension),
                                                ("pi_config_root", pi_config_root)) if value}
        runner.init_lot(self.lot, lot_id="t1", authority=self.authority, **chosen,
                        scenarios={"toy": self.scenario}, arms=list(arms), repetitions=1,
                        runs_root=root / "runs", request_cap_seconds=request_cap,
                        chain_cap_seconds=chain_cap, jev_key_file=self.key,
                        pi_command=[sys.executable, "-B", str(root / "fake_pi.py")],
                        driver_command=[sys.executable, "-B", str(root / "fake_driver.py")])

    def run(self, cell: str, through: int, judge_fn=fake_judge, env=None) -> dict:
        saved = dict(os.environ)
        os.environ.update(FAKE_PLAN=str(self.plan), FAKE_LOG=str(self.log), PI_CODING_AGENT="1", **(env or {}))
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


def record_pauses(test: unittest.TestCase) -> list:
    """Infrastructure waits are recorded, never slept."""
    pauses = []
    patcher = mock.patch.object(runner, "pause", pauses.append)
    patcher.start()
    test.addCleanup(patcher.stop)
    return pauses


def isolate_skills(test: unittest.TestCase, root: Path) -> Path:
    """The installed-skills manifest a lot binds, kept apart from the host's own (DBH-17)."""
    manifest = root / "installed-skills.json"
    patcher = mock.patch.object(runner, "SKILLS_MANIFEST", manifest, create=True)
    patcher.start()
    test.addCleanup(patcher.stop)
    return manifest


def outage_plan(minutes: float, attempt_seconds: float = 25.0) -> list[str]:
    """Attempts fail while the outage lasts, given the runner's waits between them."""
    plan, elapsed = [], 0.0
    while elapsed < minutes * 60 and len(plan) <= runner.MAX_INFRA_RETRIES:
        plan.append("crash")
        waits = runner.INFRA_WAIT_SECONDS
        elapsed += attempt_seconds + (waits[len(plan) - 1] if len(plan) <= len(waits) else 0.0)
    return plan + ["work"]


class ChainTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="dbench-runner-")
        self.root = Path(self.tmp.name)
        runner.JUDGE_BACKOFF_SECONDS = 0
        self.pauses = record_pauses(self)
        self.skills = isolate_skills(self, self.root)

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

    def test_a_lot_binds_the_installed_skills_and_stops_when_they_change(self):
        # lot `dbh`: an update replaced the installed skills during the lot, and nothing recorded it
        manifest = lambda head, tree: json.dumps({"schema": 1, "head": head, "tree": tree}).encode()
        self.skills.write_bytes(manifest("a" * 40, "b" * 40))
        fx = Fixture(self.root, plan=["work", "work"])
        bound = json.loads((fx.lot / "lot.json").read_text())["installed_skills"]
        self.assertEqual((bound["head"], bound["tree"]), ("a" * 40, "b" * 40))
        request = fx.run("toy.bare.r1", 1)["requests"][0]
        self.assertEqual(request["attempts"][0]["installed_skills"], bound["sha256"])
        self.skills.write_bytes(manifest("c" * 40, "d" * 40))
        with self.assertRaisesRegex(runner.LotError, "installed skills changed"):
            fx.run("toy.bare.r1", 2)
        with self.assertRaisesRegex(runner.LotError, "installed skills changed"):
            runner.run_lot(fx.lot, 2)
        self.assertEqual(len(fx.calls()), 1)  # no attempt ran with the other skills
        saved = json.loads((fx.lot / "cells" / "toy.bare.r1" / "cell.json").read_text())
        self.assertIn("installed skills changed", saved["error"])
        self.assertEqual(len(saved["requests"]), 1)

    def test_an_error_before_any_output_is_infrastructure(self):
        # Opus 5.5 without its OAuth extension: a 400 the provider pattern misses, and Pi exits 0
        fx = Fixture(self.root, plan=["refused", "work"])
        request = fx.run("toy.bare.r1", 1)["requests"][0]
        self.assertEqual([a["class"] for a in request["attempts"]], ["infra:provider", "agent"])
        self.assertTrue(request["axes"]["acceptance"]["accepted"])

    def test_a_provider_error_that_ends_the_session_after_work_is_infrastructure(self):
        # lot dbh-opus: the Claude plan's rate limit (429) and an overloaded provider ended sessions
        # after the model had worked, and the truncated work was judged as the arm's outcome
        fx = Fixture(self.root, plan=["cut", "work"])
        request = fx.run("toy.bare.r1", 1)["requests"][0]
        self.assertEqual([a["class"] for a in request["attempts"]], ["infra:provider", "agent"])
        self.assertEqual(request["infra_usage"]["output"], 50)
        self.assertTrue(request["axes"]["acceptance"]["accepted"])

        fx = Fixture(self.root / "driver", arms=("driver-c1a",))
        request = fx.run("toy.driver-c1a.r1", 1, env={"FAKE_DRIVER_STATUS": "cut"})["requests"][0]
        self.assertEqual([a["class"] for a in request["attempts"]], ["infra:provider", "agent"])
        self.assertEqual(request["driver"]["status"], ["integrated"])

    def test_the_arms_own_late_error_counts_and_exhausted_cut_work_is_not_judged(self):
        fx = Fixture(self.root, plan=["overflow"])  # the context overflow is the arm's outcome
        request = fx.run("toy.bare.r1", 1)["requests"][0]
        self.assertEqual([a["class"] for a in request["attempts"]], ["agent"])

        fx = Fixture(self.root / "exhausted", plan=["cut"] * 6)
        request = fx.run("toy.bare.r1", 1)["requests"][0]
        self.assertTrue(request["infra_exhausted"])
        self.assertFalse((fx.project("toy.bare.r1") / "delivered_1.txt").exists())
        self.assertFalse(request["axes"]["acceptance"]["accepted"])

    def test_a_bound_pi_extension_reaches_every_arm_and_stops_the_lot_when_it_changes(self):
        # the arms and the driver leaves run with --no-extensions, which loads only what -e names
        extension = self.root / "anthropic" / "index.ts"
        extension.parent.mkdir()
        extension.write_text("export default function () {}\n")
        fx = Fixture(self.root, arms=("bare", "driver-c1a"), pi_extension=extension)
        bound = json.loads((fx.lot / "lot.json").read_text())["pi_extension"]
        self.assertEqual(Path(bound["path"]), extension.resolve())
        fx.run("toy.bare.r1", 1)
        fx.run("toy.driver-c1a.r1", 1)
        bare, driver = fx.calls()
        self.assertIn("--no-extensions", bare["argv"])
        self.assertEqual(bare["argv"][bare["argv"].index("-e") + 1], str(extension.resolve()))
        self.assertEqual(driver["extension"], str(extension.resolve()))
        (extension.parent / "auth.ts").write_text("export const changed = true;\n")
        with self.assertRaisesRegex(runner.LotError, "Pi extension changed"):
            fx.run("toy.bare.r1", 2)
        self.assertEqual(len(fx.calls()), 2)

    def test_infrastructure_retries_stop_after_five(self):
        fx = Fixture(self.root, plan=["crash"] * 6 + ["work"])
        request = fx.run("toy.bare.r1", 1)["requests"][0]
        self.assertEqual(len(request["attempts"]), 6)
        self.assertTrue(request["infra_exhausted"])
        self.assertEqual(request["status"], "judged")
        self.assertFalse(request["axes"]["acceptance"]["accepted"])
        self.assertEqual(len(self.pauses), 5)  # one wait before each retry, none after the last
        self.assertEqual(self.pauses, sorted(self.pauses))
        events = [json.loads(line) for line in (fx.lot / "ledger.jsonl").read_text().splitlines()]
        self.assertEqual([e["seconds"] for e in events if e["event"] == "infra-wait"], self.pauses)
        self.assertEqual(request["infra_wait_seconds"], sum(self.pauses))

    def test_infrastructure_retries_wait_out_the_observed_outages(self):
        # lot `dbh`: 9 minutes of network outage; lot `dbh-drivers`: 42 minutes of `fetch failed`,
        # which outlasted the 11 minutes of waiting of DBH-14 and exhausted 10 requests
        for minutes in (9, 42):
            with self.subTest(minutes=minutes):
                self.pauses.clear()
                root = self.root / f"outage-{minutes}"
                root.mkdir()
                fx = Fixture(root, plan=outage_plan(minutes))
                request = fx.run("toy.bare.r1", 1)["requests"][0]
                self.assertFalse(request["infra_exhausted"])
                self.assertTrue(request["axes"]["acceptance"]["accepted"])

    def test_an_agent_outcome_is_never_followed_by_a_wait(self):
        fx = Fixture(self.root, plan=["crash", "work", "work"])
        record = fx.run("toy.bare.r1", 2)
        self.assertEqual(len(self.pauses), 1)
        self.assertEqual([r["infra_wait_seconds"] for r in record["requests"]], [self.pauses[0], 0])

    def test_a_file_with_a_windows_device_name_survives_snapshot_and_restore(self):
        fx = Fixture(self.root, plan=["nul", "crash", "work"])
        try:
            record = fx.run("toy.bare.r1", 2)
            second = record["requests"][1]
            self.assertEqual([a["class"] for a in second["attempts"]], ["infra:pi-crash", "agent"])
            self.assertTrue(second["axes"]["acceptance"]["accepted"])
            project = fx.project("toy.bare.r1")
            self.assertFalse((project / "junk.txt").exists())
            for folder in (project, project.parent / ".project-ticket-driver-worktrees" / "t"):
                with open(runner.native_path(folder / "NUL"), encoding="utf-8") as handle:
                    self.assertEqual(handle.read(), "build log")
        finally:  # the temporary directory cannot remove a device name by itself
            runner.rmtree(self.root)

    def test_a_cell_stopped_after_its_task_was_delivered_resumes_that_request(self):
        fx = Fixture(self.root, plan=["work", "work"])
        fx.run("toy.bare.r1", 1)
        saved = runner.snapshot

        def failing(arm_dir, target):
            raise OSError("snapshot failed")

        runner.snapshot = failing
        try:
            with self.assertRaises(OSError):
                fx.run("toy.bare.r1", 2)
        finally:
            runner.snapshot = saved
        record = fx.run("toy.bare.r1", 2)
        self.assertNotIn("error", record)
        self.assertEqual([r["status"] for r in record["requests"]], ["judged", "judged"])
        self.assertTrue(record["requests"][1]["axes"]["acceptance"]["accepted"])
        self.assertEqual([c["first_line"] for c in fx.calls()], ["# Request 1", "# Request 2"])
        self.assertEqual(git(fx.project("toy.bare.r1"), "log", "--format=%s", "--", "TASK.md").splitlines(),
                         ["TASK 2", "TASK 1"])

    def test_host_stop_during_the_last_request_is_resumed_and_its_cost_kept(self):
        fx = Fixture(self.root, plan=["work", "work", "work", "work"])

        class HostStop(BaseException):
            pass

        real_diff = runner.request_diff

        def stopping_diff(project, base, target, store):  # still inside the request, before judging
            if target.name == "03.diff":
                raise HostStop()
            return real_diff(project, base, target, store)

        with mock.patch.object(runner, "request_diff", stopping_diff), self.assertRaises(HostStop):
            fx.run("toy.bare.r1", 3)
        lot = runner.load_lot(fx.lot)
        self.assertFalse(runner.cell_done(lot, "toy.bare.r1", 3))
        shorter = fx.run("toy.bare.r1", 2)
        self.assertEqual(len(fx.calls()), 3)  # a request beyond `through` is left as it is
        self.assertEqual(shorter["requests"][2]["status"], "running")
        record = fx.run("toy.bare.r1", 3)
        self.assertEqual(len(fx.calls()), 4)
        last = record["requests"][2]
        self.assertEqual(last["status"], "judged")
        self.assertEqual([a["class"] for a in last["attempts"]], ["agent", "infra:host", "agent"])
        self.assertEqual(last["infra_usage"]["input"], 100)  # the superseded attempt still cost
        self.assertEqual(last["usage"]["input"], 100)
        self.assertTrue(last["axes"]["acceptance"]["accepted"])
        self.assertTrue(runner.cell_done(lot, "toy.bare.r1", 3))

    def test_host_stop_while_judging_keeps_the_work_and_resume_only_judges(self):
        fx = Fixture(self.root)

        class HostStop(BaseException):
            pass

        def stopping_judge(project, scenario, request):
            raise HostStop()

        with self.assertRaises(HostStop):
            fx.run("toy.bare.r1", 1, judge_fn=stopping_judge)
        self.assertFalse(runner.cell_done(runner.load_lot(fx.lot), "toy.bare.r1", 1))
        record = fx.run("toy.bare.r1", 1)
        self.assertEqual(len(fx.calls()), 1)
        self.assertEqual([a["class"] for a in record["requests"][0]["attempts"]], ["agent"])
        self.assertEqual(record["requests"][0]["status"], "judged")

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

    def test_every_request_keeps_its_diff_and_the_arm_repository_is_untouched(self):
        fx = Fixture(self.root)
        record = fx.run("toy.bare.r1", 2)
        project = fx.project("toy.bare.r1")
        for n, request in enumerate(record["requests"], 1):
            diff = request["diff"]
            self.assertEqual(diff["files"], [f"delivered_{n}.txt"])
            text = Path(diff["path"]).read_text(encoding="utf-8")
            self.assertIn(f"+++ b/delivered_{n}.txt", text)
            self.assertNotIn(".pi/", text)
        self.assertEqual(git(project, "status", "--porcelain"), "?? delivered_1.txt\n?? delivered_2.txt".strip())

    def test_the_diff_reads_the_work_tree_without_writing_into_git(self):
        project = self.root / "repo"
        project.mkdir()
        git(project, "init", "-q", "-b", "main")
        (project / ".gitignore").write_text("build/\n")
        (project / "a.txt").write_text("one\n")
        git(project, "add", "-A")
        git(project, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "base")
        base = git(project, "rev-parse", "HEAD")
        (project / "a.txt").write_text("two\n")
        (project / "new.txt").write_text("new\n")
        (project / "build").mkdir()
        (project / "build" / "out.o").write_text("ignored")
        (project / "TASK.md").write_text("the request\n")
        store = self.root / "out" / "objects"
        before = {p: p.read_bytes() for p in (project / ".git").rglob("*") if p.is_file()}
        result = runner.request_diff(project, base, self.root / "out" / "01.diff", store)
        after = {p: p.read_bytes() for p in (project / ".git").rglob("*") if p.is_file()}
        self.assertEqual(before, after)
        self.assertEqual(result["files"], ["a.txt", "new.txt"])
        text = (self.root / "out" / "01.diff").read_text(encoding="utf-8")
        self.assertIn("-one", text)
        self.assertIn("+two", text)
        self.assertNotIn("out.o", text)
        (project / "new.txt").write_text("newer\n")  # the next request starts from the tree left
        second = runner.request_diff(project, result["tree"], self.root / "out" / "02.diff", store)
        self.assertEqual(second["files"], ["new.txt"])
        self.assertIn("error", runner.request_diff(project, "0" * 40, self.root / "out" / "03.diff", store))

    def test_an_unreachable_judge_is_waited_for_without_spending_judge_attempts(self):
        fx = Fixture(self.root)
        answers = iter([False, False, True])
        with mock.patch.object(runner, "docker_ready", lambda: next(answers)), \
                mock.patch.object(runner.judge, "judge", fake_judge):
            request = fx.run("toy.bare.r1", 1, judge_fn=fake_judge)["requests"][0]
        self.assertEqual((request["status"], request["judge"]["attempts"]), ("judged", 1))
        self.assertEqual(self.pauses, list(runner.INFRA_WAIT_SECONDS[:2]))
        self.assertEqual(request["judge"]["wait_seconds"], sum(self.pauses))
        events = [json.loads(line) for line in (fx.lot / "ledger.jsonl").read_text().splitlines()]
        self.assertEqual([e["seconds"] for e in events if e["event"] == "judge-wait"], self.pauses)

    def test_a_judge_that_never_answers_stops_the_cell_and_resume_only_judges(self):
        fx = Fixture(self.root)
        with mock.patch.object(runner, "docker_ready", lambda: False), \
                mock.patch.object(runner.judge, "judge", fake_judge):
            with self.assertRaises(runner.LotError):
                fx.run("toy.bare.r1", 1, judge_fn=fake_judge)
        record = json.loads((fx.lot / "cells" / "toy.bare.r1" / "cell.json").read_text())
        self.assertEqual(record["requests"][0]["status"], "unjudged")
        self.assertIn("did not answer", record["error"])
        lot = runner.load_lot(fx.lot)
        self.assertFalse(runner.cell_done(lot, "toy.bare.r1", 1))
        calls = len(fx.calls())
        record = fx.run("toy.bare.r1", 1)  # the judge is back: no new attempt, only the judgment
        self.assertEqual(len(fx.calls()), calls)
        request = record["requests"][0]
        self.assertEqual((request["status"], len(request["attempts"])), ("judged", 1))
        self.assertTrue(request["axes"]["acceptance"]["accepted"])

    def test_arm_commands_follow_the_contract(self):
        fx = Fixture(self.root, arms=("bare", "skills-only", "autopilot"))
        for cell in ("toy.bare.r1", "toy.skills-only.r1", "toy.autopilot.r1"):
            fx.run(cell, 1)
        bare, skills, autopilot = (c["argv"] for c in fx.calls())
        for argv in (bare, skills, autopilot):
            for flag in ("--no-extensions", "--no-context-files", "--approve", "-p"):
                self.assertIn(flag, argv)
            self.assertNotIn("-e", argv)  # a lot without a bound extension loads none
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
        leaf = (driver / "scripts" / "leaf.py").read_text()
        self.assertIn('"--no-extensions", "--no-context-files"', leaf)
        self.assertLess(leaf.index(runner.LEAF_NEW), leaf.index('os.environ.get("TICKET_DRIVER_PI_EXTENSION")'))
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

    def test_exact_driver_source_records_its_commit_and_refuses_dirty_checkouts(self):
        source = self.root / "source"
        for part in ("ticket-driver/policy.json", "ticket-driver/scripts/leaf.py",
                     "ticket-driver/scripts/arbiter.py", "ticket-autopilot/SKILL.md"):
            (source / part).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(runner.ROOT / part, source / part)
        runner.git(source, "init", "-q")
        runner.git(source, "-c", "user.name=t", "-c", "user.email=t@example.org", "add", "-A")
        runner.git(source, "-c", "user.name=t", "-c", "user.email=t@example.org", "commit", "-qm", "source")
        fx = Fixture(self.root, arms=("driver-c3a",))
        (source / "stray.txt").write_text("dirty", encoding="utf-8")
        with self.assertRaises(runner.LotError):
            runner.prepare_drivers(fx.lot, source=source, exact=True)
        with self.assertRaises(runner.LotError):
            runner.prepare_drivers(fx.lot, source=source / "ticket-driver", exact=True)
        self.assertEqual(json.loads((fx.lot / "lot.json").read_text())["driver_copies"], {})
        (source / "stray.txt").unlink()
        copies = runner.prepare_drivers(fx.lot, source=source, exact=True)
        self.assertEqual(copies["toy"]["source_commit"], runner.git(source, "rev-parse", "HEAD").stdout.strip())
        self.assertEqual(copies["toy"]["source_tree"], runner.git(source, "rev-parse", "HEAD^{tree}").stdout.strip())
        self.assertTrue((Path(copies["toy"]["path"]) / "ticket-driver" / "policy.json").is_file())

    def test_gated_driver_candidates_are_judged_apart(self):
        fx = Fixture(self.root, arms=("driver-c3a",))
        request = fx.run("toy.driver-c3a.r1", 1, env={"FAKE_DRIVER_STATUS": "gated"})["requests"][0]
        self.assertEqual((request["driver"]["status"], request["attempts"][0]["class"]), (["gated"], "agent"))
        self.assertFalse(request["axes"]["acceptance"]["accepted"])
        self.assertEqual(runner.judge_gated(fx.lot, judge_fn=fake_judge),
                         [{"cell": "toy.driver-c3a.r1", "request": 1, "status": "judged"}])
        saved = json.loads((fx.lot / "cells" / "toy.driver-c3a.r1" / "cell.json").read_text())["requests"][0]
        self.assertTrue(saved["counterfactual"]["axes"]["acceptance"]["accepted"])
        self.assertFalse(saved["axes"]["acceptance"]["accepted"])
        self.assertEqual(runner.judge_gated(fx.lot, judge_fn=fake_judge), [])

    def test_changed_authority_blocks_the_lot(self):
        fx = Fixture(self.root)
        fx.authority.write_text(fx.authority.read_text().replace("offline", "edited"))
        with self.assertRaises(runner.LotError):
            fx.run("toy.bare.r1", 1)

    def test_a_corrected_suite_is_bound_on_the_record_and_a_seed_never(self):
        fx = Fixture(self.root)
        fx.run("toy.bare.r1", 1)
        with self.assertRaises(runner.LotError):
            runner.amend_suite(fx.lot, "toy", "nothing changed")
        (fx.scenario / "hidden" / "helper.py").write_text("# fixed comparison\n")
        with self.assertRaises(runner.LotError):
            runner.load_lot(fx.lot)
        with self.assertRaises(runner.LotError):
            runner.amend_suite(fx.lot, "toy", "  ")
        amendment = runner.amend_suite(fx.lot, "toy", "oracle defect")
        self.assertNotEqual(amendment["from"], amendment["to"])
        lot = runner.load_lot(fx.lot)
        self.assertEqual(lot["amendments"], [amendment])
        self.assertIn('"event": "amend-suite"', (fx.lot / "ledger.jsonl").read_text())
        (fx.scenario / "seed" / "extra.txt").write_text("changed\n")
        (fx.scenario / "hidden" / "helper.py").write_text("# fixed again\n")
        with self.assertRaises(runner.LotError):
            runner.amend_suite(fx.lot, "toy", "seed moved")

    def test_length_beyond_authority_is_refused(self):
        fx = Fixture(self.root)
        with self.assertRaises(runner.LotError):
            fx.run("toy.bare.r1", 4)

    def test_run_lot_selects_cells_by_repetition_and_arm_in_launch_order(self):
        fx = Fixture(self.root, arms=("bare", "autopilot"))
        fx.run("toy.bare.r1", 1)
        lot = runner.load_lot(fx.lot)
        for arm in ("bare", "autopilot"):
            lot["cells"][f"toy.{arm}.r2"] = {**lot["cells"][f"toy.{arm}.r1"], "rep": 2}
        self.assertEqual(runner.select_cells(lot, 1), ["toy.autopilot.r1", "toy.bare.r2", "toy.autopilot.r2"])
        self.assertEqual(runner.select_cells(lot, 2, reps=[1]), ["toy.bare.r1", "toy.autopilot.r1"])
        self.assertEqual(runner.select_cells(lot, 2, reps=[2], arms=["autopilot"]), ["toy.autopilot.r2"])


class HardRegimeTests(unittest.TestCase):
    """DBH-02: model and caps come from the lot, the scenario sets its length and test command."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="dbench-runner-")
        self.root = Path(self.tmp.name)
        runner.JUDGE_BACKOFF_SECONDS = 0
        self.pauses = record_pauses(self)
        self.skills = isolate_skills(self, self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_lot_model_and_thinking_reach_pi_the_record_and_the_driver_policy(self):
        fx = Fixture(self.root, arms=("bare", "driver-c3a"), model="openai-codex/gpt-6-luna",
                     thinking="medium")
        record = fx.run("toy.bare.r1", 1)
        argv = fx.calls()[0]["argv"]
        self.assertEqual([argv[argv.index(flag) + 1] for flag in ("--provider", "--model", "--thinking")],
                         ["openai-codex", "gpt-6-luna", "medium"])
        self.assertEqual((record["model"], record["thinking"]), ("openai-codex/gpt-6-luna", "medium"))
        copies = runner.prepare_drivers(fx.lot, source=runner.ROOT)
        policy = json.loads((Path(copies["toy"]["path"]) / "ticket-driver" / "policy.json").read_text(
            encoding="utf-8"))
        self.assertEqual((policy["provider"], policy["model"], policy["thinking"]),
                         ("openai-codex", "gpt-6-luna", "medium"))

    def test_an_authority_that_names_a_model_binds_the_lot_to_it(self):
        luna = {"model": {"provider": "openai-codex", "id": "gpt-6-luna", "thinking": "medium"}}
        (self.root / "a").mkdir()
        (self.root / "b").mkdir()
        with self.assertRaises(runner.LotError):
            Fixture(self.root / "a", authority_extra=luna)
        fx = Fixture(self.root / "b", authority_extra=luna, model="openai-codex/gpt-6-luna", thinking="medium")
        self.assertEqual(runner.load_lot(fx.lot)["model"], "gpt-6-luna")

    def test_compactions_are_counted_apart_with_their_cost(self):
        fx = Fixture(self.root, plan=["compact", "work"])
        record = fx.run("toy.bare.r1", 2)
        first, second = record["requests"]
        self.assertEqual(first["compaction"], {"count": 1, "tokens_before": [206743], "cost_usd": 0.24})
        self.assertAlmostEqual(first["usage"]["cost_usd"], 0.01)  # the assistant's own spend, as before
        self.assertEqual(second["compaction"], {"count": 0, "tokens_before": [], "cost_usd": 0.0})

    def test_a_scenario_names_the_test_command_of_the_driver(self):
        fx = Fixture(self.root, arms=("driver-c1a",), scenario_extra={
            "language": "javascript", "driver_test_command": ["node", "--test"]})
        copies = runner.prepare_drivers(fx.lot, source=runner.ROOT)
        policy = json.loads((Path(copies["toy"]["path"]) / "ticket-driver" / "policy.json").read_text(
            encoding="utf-8"))
        self.assertEqual(policy["test_command"], ["node", "--test"])

    def test_a_request_cap_over_an_hour_reaches_the_arm(self):
        fx = Fixture(self.root, request_cap=5400)
        request = fx.run("toy.bare.r1", 1)["requests"][0]
        self.assertEqual([(a["class"], a["timeout_seconds"]) for a in request["attempts"]],
                         [("agent", 5400)])
        self.assertTrue(request["axes"]["acceptance"]["accepted"])

    def test_a_cap_the_capture_cannot_honor_is_refused_before_the_lot_exists(self):
        for request_cap, chain_cap in ((0, None), (86401, None), (60, 0)):
            with self.subTest(request_cap=request_cap, chain_cap=chain_cap):
                root = self.root / f"caps-{request_cap}-{chain_cap}"
                with self.assertRaisesRegex(runner.LotError, "cap"):
                    Fixture(root, request_cap=request_cap, chain_cap=chain_cap)
                self.assertFalse((root / "lot").exists())

    def test_chain_length_is_bounded_by_the_scenario_too(self):
        fx = Fixture(self.root, authority_extra={"max_length": 12})
        with self.assertRaises(runner.LotError):
            fx.run("toy.bare.r1", 4)

    def test_init_lot_command_line_takes_model_thinking_and_caps(self):
        fx = Fixture(self.root)
        saved = runner.resolve_pi
        runner.resolve_pi = lambda: ["pi"]
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                code = runner.main([
                    "init-lot", "--lot", str(self.root / "lot2"), "--lot-id", "t1",
                    "--authority", str(fx.authority), "--scenario", f"toy={fx.scenario}",
                    "--arm", "bare", "--repetitions", "1", "--runs-root", str(self.root / "runs2"),
                    "--arms-root", str(self.root / "arms2"), "--model", "openai-codex/gpt-6-luna",
                    "--thinking", "medium", "--request-cap", "5400", "--chain-cap", "20000"])
        finally:
            runner.resolve_pi = saved
        self.assertEqual(code, 0)
        lot = json.loads((self.root / "lot2" / "lot.json").read_text(encoding="utf-8"))
        self.assertEqual((lot["provider"], lot["model"], lot["thinking"], lot["request_cap_seconds"],
                          lot["chain_cap_seconds"]), ("openai-codex", "gpt-6-luna", "medium", 5400, 20000))


def fake_pi_config(root: Path) -> Path:
    """An installed pi-personal-config holding every profile extension, as Pi's settings name it."""
    root.mkdir(parents=True)
    (root / "package.json").write_text(json.dumps({"name": "pi-personal-config"}))
    for relative in runner.ARM_PROFILES["pi-full"]:
        path = root / relative
        if path.suffix:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("export default function () {}\n")
        else:  # an extension folder, loaded through its index.ts
            path.mkdir(parents=True)
            (path / "index.ts").write_text("export default function () {}\n")
    return root


def e_args(argv: list[str]) -> list[str]:
    return [argv[i + 1] for i, flag in enumerate(argv) if flag == "-e"]


class ArmProfileTests(unittest.TestCase):
    """DBH-21: `pi-tools` and `pi-full` load a closed list of installed extensions, bound to the lot."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="dbench-runner-")
        self.root = Path(self.tmp.name)
        runner.JUDGE_BACKOFF_SECONDS = 0
        self.pauses = record_pauses(self)
        self.skills = isolate_skills(self, self.root)
        self.config = fake_pi_config(self.root / "pi-personal-config")

    def tearDown(self):
        self.tmp.cleanup()

    def test_new_arms_load_their_profile_and_the_old_arms_keep_their_argv(self):
        arms = ("bare", "skills-only", "autopilot", "pi-tools", "pi-full")
        fx = Fixture(self.root, arms=arms, pi_config_root=self.config)
        for arm in arms:
            fx.run(f"toy.{arm}.r1", 1)
        argv = dict(zip(arms, (c["argv"] for c in fx.calls())))
        lot = json.loads((fx.lot / "lot.json").read_text())
        for arm, (options, suffix) in (("bare", (["--no-skills"], "")),
                                       ("skills-only", ([], runner.SKILLS_ONLY_SUFFIX)),
                                       ("autopilot", ([], runner.AUTOPILOT_SUFFIX))):
            sessions = str(Path(lot["cells"][f"toy.{arm}.r1"]["arm_dir"]) / "sessions")
            self.assertEqual(argv[arm], [
                "-p", "--provider", "openai-codex", "--model", "gpt-6-sol", "--thinking", "high",
                "--no-extensions", "--no-context-files", "--approve", *options,
                "--session-dir", sessions, "--", runner.PROMPT + suffix])
        tools = [str((self.config / relative).resolve()) for relative in runner.TOOL_PROFILE]
        mandatory = str((self.config / runner.MANDATORY_EXTENSION).resolve())
        self.assertEqual(e_args(argv["pi-tools"]), tools)
        self.assertEqual(e_args(argv["pi-full"]), [*tools, mandatory])
        self.assertEqual(len(runner.TOOL_PROFILE), 4)
        for arm in ("pi-tools", "pi-full"):
            self.assertGreater(argv[arm].index("-e"), argv[arm].index("--no-extensions"))
            self.assertIn("--no-context-files", argv[arm])
            self.assertEqual(argv[arm][-1], runner.PROMPT)  # no suffix: the mandatory rule speaks
        self.assertIn("--no-skills", argv["pi-tools"])
        self.assertNotIn("--no-skills", argv["pi-full"])
        self.assertTrue((fx.project("toy.pi-full.r1") / ".pi" / "settings.json").is_file())

    def test_init_lot_binds_each_arms_extensions_and_refuses_a_missing_one(self):
        fx = Fixture(self.root, arms=("bare", "pi-tools", "pi-full"), pi_config_root=self.config)
        bound = json.loads((fx.lot / "lot.json").read_text())["arm_extensions"]
        self.assertEqual(bound["bare"], [])
        self.assertEqual([Path(e["path"]) for e in bound["pi-full"]],
                         [(self.config / r).resolve() for r in runner.ARM_PROFILES["pi-full"]])
        self.assertEqual(bound["pi-tools"], bound["pi-full"][:4])
        for entry in bound["pi-full"]:  # the folder holding it: an extension imports its siblings
            self.assertEqual(entry["sha256"], judge.tree_digest(Path(entry["path"]).parent)["sha256"])

        (self.config / runner.TOOL_PROFILE[3]).unlink()
        with self.assertRaisesRegex(runner.LotError, "web.ts"):
            Fixture(self.root / "missing", arms=("pi-tools",), pi_config_root=self.config)
        self.assertFalse((self.root / "missing" / "lot").exists())

    def test_a_changed_or_vanished_extension_stops_the_lot_and_each_attempt_records_its_list(self):
        fx = Fixture(self.root, arms=("bare", "pi-tools"), pi_config_root=self.config)
        bound = json.loads((fx.lot / "lot.json").read_text())["arm_extensions"]
        tools = fx.run("toy.pi-tools.r1", 1)["requests"][0]["attempts"][0]
        bare = fx.run("toy.bare.r1", 1)["requests"][0]["attempts"][0]
        self.assertEqual(tools["arm_extensions"], bound["pi-tools"])
        self.assertEqual(bare["arm_extensions"], [])

        sibling = self.config / "extensions" / "pi-code-tool" / "runtime.ts"
        sibling.write_text("export const changed = true;\n")
        with self.assertRaisesRegex(runner.LotError, "pi-code-tool.*changed or disappeared"):
            runner.load_lot(fx.lot)
        with self.assertRaisesRegex(runner.LotError, "changed or disappeared"):
            fx.run("toy.pi-tools.r1", 2)
        sibling.unlink()
        runner.load_lot(fx.lot)  # the same bytes again: the binding holds
        shutil.rmtree(self.config / runner.TOOL_PROFILE[2])
        with self.assertRaisesRegex(runner.LotError, "pi-code.extensions.*changed or disappeared"):
            runner.load_lot(fx.lot)
        self.assertEqual(len(fx.calls()), 2)

    def test_a_lot_bound_before_profiles_still_loads_and_runs(self):
        fx = Fixture(self.root, arms=("bare",))
        stored = json.loads((fx.lot / "lot.json").read_text())
        del stored["arm_extensions"]
        (fx.lot / "lot.json").write_text(json.dumps(stored))
        self.assertNotIn("arm_extensions", runner.load_lot(fx.lot))
        attempt = fx.run("toy.bare.r1", 1)["requests"][0]["attempts"][0]
        self.assertEqual(attempt["arm_extensions"], [])
        self.assertNotIn("-e", fx.calls()[0]["argv"])

    def test_the_authority_covers_the_new_arms_like_the_others(self):
        with self.assertRaisesRegex(runner.LotError, "authority does not cover"):
            Fixture(self.root, arms=("bare", "pi-full"), pi_config_root=self.config,
                    authority_extra={"arms": ["bare", "pi-tools"]})
        fx = Fixture(self.root / "ok", arms=("pi-full",), pi_config_root=self.config)
        self.assertEqual(runner.load_lot(fx.lot)["arms"], ["pi-full"])

    def test_the_profile_root_is_the_installed_pi_personal_config(self):
        settings = self.root / "agent" / "settings.json"
        settings.parent.mkdir()
        other = self.root / "other"
        other.mkdir()
        (other / "package.json").write_text(json.dumps({"name": "something-else"}))
        packages = ["npm:@scope/tool", "../other", {"source": "../pi-personal-config", "extensions": []}]
        settings.write_text(json.dumps({"packages": packages}))
        with mock.patch.object(runner, "PI_AGENT_SETTINGS", settings):
            self.assertEqual(runner.installed_pi_config(), self.config.resolve())
            fx = Fixture(self.root / "lot-a", arms=("pi-tools",))
            bound = json.loads((fx.lot / "lot.json").read_text())["arm_extensions"]["pi-tools"]
            self.assertTrue(all(Path(e["path"]).is_relative_to(self.config.resolve()) for e in bound))
            Fixture(self.root / "lot-b", arms=("bare",))  # no profiled arm: nothing to resolve
            settings.write_text(json.dumps({"packages": packages[:2]}))
            with self.assertRaisesRegex(runner.LotError, "pi-personal-config"):
                runner.installed_pi_config()


FAKE_PREFLIGHT_PI = textwrap.dedent('''
    import json, os, sys, time, pathlib
    args = sys.argv[1:]
    mode = os.environ.get("FAKE_PREFLIGHT", "ok")
    with open(os.environ["FAKE_LOG"], "a", encoding="utf-8") as log:
        log.write(json.dumps({"argv": args, "cwd": os.getcwd()}) + "\\n")
    if mode == "fail-load":
        print("Error: Failed to load extension", file=sys.stderr)
        sys.exit(1)
    loaded = [pathlib.Path(args[i + 1]) for i, flag in enumerate(args) if flag == "-e"]
    names = [p.parent.name if p.name == "index.ts" else p.stem for p in loaded]
    provided = {"pi-code-tool": ["code"], "todo": ["todo"], "plan-mode": ["plan_mode_complete"],
                "web": [] if mode == "no-web" else ["web_search", "web_fetch"]}
    tools = ["read", "bash", "edit", "write"] + [t for name in names for t in provided.get(name, [])]
    skills = [] if "--no-skills" in args else ["ask-skills", "change-status-ticket", "to-spec",
                                                "to-tickets", "execute-ticket", "tdd"]
    session = pathlib.Path(args[args.index("--session-dir") + 1])
    session.mkdir(parents=True, exist_ok=True)
    lines = [{"type": "session", "version": 3, "cwd": os.getcwd()},
             {"type": "message", "message": {"role": "system", "content": "",
                                              "toolsAdded": [{"name": t} for t in tools + ["stray"]]}},
             {"type": "message", "message": {"role": "system", "content": "", "toolsRemoved": [{"name": "stray"}],
                                              "sections": {"preamble": "You are Pi", "skills": "<available_skills>" + "".join(
                                                  f"<skill><name>{s}</name></skill>" for s in skills) + "</available_skills>"
                                                  if skills else None}}}]
    text = args[-1]
    if "mandatory-agent-skills" in names:
        text = '<skill name="ask-skills" location="x">\\nroute\\n</skill>\\n\\n' + text
    lines.append({"type": "message", "message": {"role": "user", "content": [{"type": "text", "text": text}]}})
    usage = {"input": 10, "output": 5, "cost": {"total": 0.001}}
    if "code" in tools:
        lines.append({"type": "message", "message": {"role": "assistant", "usage": usage, "stopReason": "toolUse",
            "content": [{"type": "toolCall", "id": "c1", "name": "code", "arguments": {}}]}})
        denied = mode == "approval"
        if not denied:
            pathlib.Path("preflight.txt").write_text("ok")
        lines.append({"type": "message", "message": {"role": "toolResult", "toolCallId": "c1", "toolName": "code",
            "isError": denied, "content": [{"type": "text", "text": "denied" if denied else "wrote"}]}})
    with open(session / "s.jsonl", "w", encoding="utf-8") as out:
        out.write("".join(json.dumps(line) + "\\n" for line in lines))
    if mode == "hang":  # code waits for a human that never comes
        time.sleep(60)
    with open(session / "s.jsonl", "a", encoding="utf-8") as out:
        out.write(json.dumps({"type": "message", "message": {"role": "assistant", "usage": usage,
            "stopReason": "stop", "content": [{"type": "text", "text": "done"}]}}) + "\\n")
''')


class PreflightTests(unittest.TestCase):
    """DBH-21: one minimal request per arm, outside any lot, before a lot spends anything."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="dbench-runner-")
        self.root = Path(self.tmp.name)
        self.config = fake_pi_config(self.root / "pi-personal-config")
        (self.root / "fake_pi.py").write_text(FAKE_PREFLIGHT_PI)
        self.log = self.root / "log.jsonl"
        self.pi = [sys.executable, "-B", str(self.root / "fake_pi.py")]

    def tearDown(self):
        self.tmp.cleanup()

    def preflight(self, mode="ok", arms=("bare", "pi-tools", "pi-full"), timeout=60) -> dict:
        env = {"FAKE_LOG": str(self.log), "FAKE_PREFLIGHT": mode}
        with mock.patch.dict(os.environ, env):
            return runner.preflight(list(arms), model="openai-codex/gpt-6-luna", thinking="medium",
                                    pi_command=self.pi, pi_config_root=self.config, timeout_seconds=timeout)

    def calls(self) -> list[dict]:
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def test_each_arm_matches_its_profile_with_the_argv_of_a_lot(self):
        report = self.preflight()
        self.assertTrue(report["ok"], report)
        bare, tools, full = (report["arms"][arm] for arm in ("bare", "pi-tools", "pi-full"))
        self.assertEqual(bare["tools"], ["bash", "edit", "read", "write"])
        self.assertEqual(tools["tools"], sorted(["bash", "edit", "read", "write", "code", "todo",
                                                 "plan_mode_complete", "web_search", "web_fetch"]))
        self.assertEqual(full["tools"], tools["tools"])
        self.assertEqual((bare["skills"], tools["skills"]), ([], []))
        self.assertIn("execute-ticket", full["skills"])
        self.assertEqual([a["routed"] for a in (bare, tools, full)], [False, False, True])
        self.assertEqual([a["code_write"] for a in (bare, tools, full)], ["n/a", "ok", "ok"])
        self.assertEqual([a["problems"] for a in (bare, tools, full)], [[], [], []])
        argv = {Path(c["cwd"]).parent.name: c["argv"] for c in self.calls()}
        self.assertEqual(len(e_args(argv["pi-full"])), 5)
        self.assertEqual([argv[arm][argv[arm].index("--model") + 1] for arm in argv], ["gpt-6-luna"] * 3)
        self.assertTrue(all("--continue" not in a and a[-1] == runner.PROMPT for a in argv.values()))
        self.assertTrue(all(not Path(c["cwd"]).exists() for c in self.calls()))  # temporary, then gone

    def test_an_arm_that_does_not_match_its_profile_fails_the_preflight(self):
        for mode, arm, problem in (("approval", "pi-tools", "code"), ("no-web", "pi-full", "web_search"),
                                   ("fail-load", "pi-tools", "exit"), ("hang", "pi-tools", "timeout")):
            with self.subTest(mode=mode):
                report = self.preflight(mode, arms=(arm,), timeout=3 if mode == "hang" else 60)
                self.assertFalse(report["ok"])
                self.assertRegex(" ".join(report["arms"][arm]["problems"]), problem)

    def test_visible_skills_where_none_belong_fail_the_preflight(self):
        with mock.patch.dict(runner.PI_ARMS, {"pi-tools": ([], "")}):  # as if --no-skills were lost
            report = self.preflight(arms=("pi-tools",))
        self.assertFalse(report["ok"])
        self.assertRegex(" ".join(report["arms"]["pi-tools"]["problems"]), "skills")

    def test_the_command_line_exits_non_zero_when_an_arm_fails(self):
        def run(mode: str) -> int:
            with mock.patch.dict(os.environ, {"FAKE_LOG": str(self.log), "FAKE_PREFLIGHT": mode}), \
                    mock.patch.object(runner, "resolve_pi", lambda: self.pi), \
                    mock.patch.object(runner, "installed_pi_config", lambda: self.config), \
                    contextlib.redirect_stdout(io.StringIO()) as out:
                code = runner.main(["preflight", "--lot-free", "--arm", "pi-tools",
                                    "--model", "openai-codex/gpt-6-luna", "--thinking", "medium"])
            self.assertIn('"ok"', out.getvalue())
            return code
        self.assertEqual(run("ok"), 0)
        self.assertEqual(run("approval"), 1)
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            runner.main(["preflight", "--arm", "pi-tools"])  # never without saying it is outside a lot


if __name__ == "__main__":
    unittest.main()
