"""Offline tests for the delivery-bench judge; the live container test needs DBENCH_LIVE_DOCKER=1."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import judge

EXAMPLE = HERE / "example"


def materialize(target: Path, *overlays: Path) -> Path:
    """Seed plus overlays, committed, so the digest covers a real .git as well."""
    shutil.copytree(EXAMPLE / "seed", target)
    for overlay in overlays:
        shutil.copytree(overlay, target, dirs_exist_ok=True)
    subprocess.run(["git", "init", "-q", str(target)], check=True)
    subprocess.run(["git", "-C", str(target), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(target), "-c", "user.name=t", "-c", "user.email=t@t",
                    "commit", "-qm", "seed"], check=True)
    return target


def fake_result(checks: list[dict], request: int = 1) -> dict:
    return {"schema": 1, "scenario": "example", "request": request, "checks": checks}


def writer(document: dict, mutate: Path | None = None):
    def run(argv, timeout, name):
        target = next(a.split("source=")[1].split(",target=/out")[0]
                      for a in argv if a.endswith(",target=/out"))
        Path(target, "result.json").write_text(json.dumps(document), encoding="utf-8")
        if mutate is not None:
            (mutate / "toy" / "calc.py").write_text("tampered\n", encoding="utf-8")
        return {"exit_code": 0, "seconds": 0.0, "stdout_tail": "", "stderr_tail": ""}
    return run


class DigestTests(unittest.TestCase):
    def test_digest_is_stable_and_sensitive(self):
        with tempfile.TemporaryDirectory() as scratch:
            project = materialize(Path(scratch) / "p")
            first = judge.tree_digest(project)
            self.assertEqual(first, judge.tree_digest(project))
            (project / "toy" / "calc.py").write_text("x = 1\n", encoding="utf-8")
            self.assertNotEqual(first["sha256"], judge.tree_digest(project)["sha256"])

    def test_rename_changes_digest(self):
        with tempfile.TemporaryDirectory() as scratch:
            project = materialize(Path(scratch) / "p")
            first = judge.tree_digest(project)["sha256"]
            (project / "toy" / "calc.py").rename(project / "toy" / "calc2.py")
            self.assertNotEqual(first, judge.tree_digest(project)["sha256"])


class ValidationTests(unittest.TestCase):
    def feature(self, **extra):
        return {"id": "r1.x", "kind": "feature", "request": 1, "status": "pass", **extra}

    def test_rejects_wrong_request_and_future_checks(self):
        with self.assertRaises(judge.JudgeError):
            judge.validate_result(fake_result([self.feature()], request=2), "example", 1)
        future = {"id": "r2.x", "kind": "feature", "request": 2, "status": "pass"}
        with self.assertRaises(judge.JudgeError):
            judge.validate_result(fake_result([self.feature(), future]), "example", 1)

    def test_rejects_inconsistent_trap_distance(self):
        bad = {"id": "t", "kind": "trap", "request": 2, "status": "fail",
               "trap": {"type": "convention", "rule": 1, "temptation": 2, "distance": 3}}
        with self.assertRaises(judge.JudgeError):
            judge.validate_result(fake_result([self.feature(request=2, id="r2"), bad], 2),
                                  "example", 2)

    def test_needs_an_acceptance_check_for_the_request(self):
        with self.assertRaises(judge.JudgeError):
            judge.validate_result(fake_result([{"id": "l", "kind": "latent", "request": 1,
                                                "status": "pass"}]), "example", 1)

    def test_axes_split_acceptance_robustness_compass(self):
        checks = judge.validate_result(fake_result([
            {"id": "r1.a", "kind": "invariant", "request": 1, "status": "fail"},
            {"id": "r2.a", "kind": "feature", "request": 2, "status": "pass"},
            {"id": "r2.b", "kind": "feature", "request": 2, "status": "fail"},
            {"id": "r1.l", "kind": "latent", "request": 1, "status": "pass"},
            {"id": "r2.t", "kind": "trap", "request": 2, "status": "fail",
             "trap": {"type": "convention", "rule": 1, "temptation": 2, "distance": 1}},
        ], 2), "example", 2)
        result = judge.axes(checks, 2)
        self.assertEqual(result["acceptance"], {"passed": 1, "total": 2, "failed": ["r2.b"],
                                                "accepted": False})
        self.assertEqual(result["robustness"]["latent_found"], 1)
        self.assertEqual(result["compass"]["invariants"]["failed"], ["r1.a"])
        self.assertEqual(result["compass"]["traps_violated"][0]["distance"], 1)


class JudgeTests(unittest.TestCase):
    def test_docker_argv_mounts_project_read_only_without_network(self):
        doc = judge.load_scenario(EXAMPLE)
        argv = judge.docker_argv(doc, Path("P"), Path("H"), Path("O"), 2, "n")
        self.assertIn("none", argv[argv.index("--network") + 1])
        project_mount = next(a for a in argv if ",target=/repo" in a)
        self.assertTrue(project_mount.endswith(",readonly"))
        self.assertEqual(argv[-2:], ["--request", "2"])

    def test_judge_records_identical_tree_and_axes(self):
        with tempfile.TemporaryDirectory() as scratch:
            project = materialize(Path(scratch) / "p")
            document = fake_result([{"id": "r1.mul", "kind": "feature", "request": 1,
                                     "status": "fail", "detail": "no mul"}])
            record = judge.judge(project, EXAMPLE, 1, runner=writer(document))
            self.assertTrue(record["identical"])
            self.assertFalse(record["axes"]["acceptance"]["accepted"])

    def test_tampering_invalidates_the_judgement(self):
        with tempfile.TemporaryDirectory() as scratch:
            project = materialize(Path(scratch) / "p")
            document = fake_result([{"id": "r1.mul", "kind": "feature", "request": 1,
                                     "status": "pass"}])
            with self.assertRaisesRegex(judge.JudgeError, "changed"):
                judge.judge(project, EXAMPLE, 1, runner=writer(document, mutate=project))

    def test_hidden_suite_inside_the_project_is_refused(self):
        with tempfile.TemporaryDirectory() as scratch:
            project = materialize(Path(scratch) / "p")
            inner = project / "scenario"
            shutil.copytree(EXAMPLE, inner)
            with self.assertRaisesRegex(judge.JudgeError, "outside"):
                judge.judge(project, inner, 1, runner=writer(fake_result([])))


@unittest.skipUnless(os.environ.get("DBENCH_LIVE_DOCKER") == "1", "live container test")
class LiveContainerTests(unittest.TestCase):
    def run_case(self, request: int, *overlays: Path) -> dict:
        with tempfile.TemporaryDirectory() as scratch:
            project = materialize(Path(scratch) / "p", *overlays)
            return judge.judge(project, EXAMPLE, request)

    def test_reference_passes_everything_and_tree_is_untouched(self):
        record = self.run_case(2, EXAMPLE / "reference" / "02")
        self.assertTrue(record["identical"])
        self.assertTrue(all(c["status"] == "pass" for c in record["checks"]), record["checks"])

    def test_stub_fails_exactly_the_expected_checks(self):
        record = self.run_case(2)
        failed = sorted(c["id"] for c in record["checks"] if c["status"] != "pass")
        self.assertEqual(failed, ["r1.calc-error-exported", "r1.latent.half-rounds-up", "r1.mul",
                                  "r2.div", "r2.trap.errors-inherit-calc-error"])


if __name__ == "__main__":
    unittest.main()
