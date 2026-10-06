"""DBH-30: mutation of the added lines. The real image runs only with DBENCH_DOCKER_SMOKE=1."""
from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path

import quality_coverage as qc
import quality_mutation as qm
from test_quality_coverage import build_lot

SOURCE = "def f(a, b):\n    if a < b and a == 1:\n        return a + b\n    total = a * 2\n    return total\n"


def coverage(files: dict) -> dict:
    return {"status": "ok", "files": {p: {"covered": c, "missed": m} for p, (c, m) in files.items()}}


class OperatorTests(unittest.TestCase):
    def test_operators_skip_strings_comments_and_arrows(self):
        ops = qm.line_mutants('    if a < b and x == "a < b":  # a > b', "python")
        self.assertEqual(sorted((o, old, new) for o, _, old, new in ops),
                         [("boolean", "and", "or"), ("relational", "<", "<="), ("relational", "==", "!=")])
        self.assertEqual(qm.line_mutants("def f(a) -> int:", "python"), [])
        self.assertEqual(qm.line_mutants("#include <stdio.h>", "c"), [])
        c = {(o, old, new) for o, _, old, new in qm.line_mutants("  if (p->n >= 0 && !q) x = y - 1;", "c")}
        self.assertEqual(c, {("relational", ">=", ">"), ("boolean", "&&", "||"), ("boolean", "!", ""),
                             ("arithmetic", " - ", " + "), ("constant", "0", "1"), ("constant", "1", "2")})
        js = {(o, new) for o, _, _, new in qm.line_mutants("  return x === undefined || ok;", "javascript")}
        self.assertIn(("relational", "!=="), js)
        self.assertIn(("return", "undefined"), js)
        self.assertNotIn("delete", {o for o, _ in js})
        self.assertIn(("delete", ";"), {(o, new) for o, _, _, new in qm.line_mutants("  count += 1;", "javascript")})

    def test_return_and_delete(self):
        ops = {(o, old, new) for o, _, old, new in qm.line_mutants("    return a + b", "python")}
        self.assertIn(("return", "a + b", "None"), ops)
        self.assertNotIn("delete", {o for o, *_ in qm.line_mutants("    return a + b", "python")})
        self.assertIn(("delete", "total = a * 2", "pass"),
                      {(o, old, new) for o, _, old, new in qm.line_mutants("    total = a * 2", "python")})
        self.assertNotIn("delete", {o for o, *_ in qm.line_mutants("    x = f(a,", "python")})

    def test_same_seed_same_mutants_and_apply(self):
        root = Path(tempfile.mkdtemp(prefix="dbq-mut-test-"))
        self.addCleanup(shutil.rmtree, root, True)
        (root / "m.py").write_bytes(SOURCE.replace("\n", "\r\n").encode())
        found = qm.candidates(root, {"m.py": [2, 3, 4, 5]}, "python")
        first, again = qm.pick(found, "u1", 5), qm.pick(found, "u1", 5)
        self.assertEqual(first, again)
        self.assertEqual(len(first), 5)
        self.assertNotEqual(qm.pick(found, "u2", 5), first)
        mutant = next(m for m in found if m["operator"] == "relational" and m["original"] == "<")
        qm.apply(root, mutant)
        self.assertIn(b"    if a <= b and a == 1:\r\n", (root / "m.py").read_bytes())
        with self.assertRaises(ValueError):
            qm.apply(root, {**mutant, "column": mutant["column"] + 1})

    def test_classification(self):
        green, red = {"exit": 0}, {"exit": 1, "output": "FAIL: test_a (t.T.test_a)\n"}
        self.assertEqual(qm.classify({"exit": 1}, green), "killed")
        self.assertEqual(qm.classify({"exit": 0}, green), "survived")
        self.assertEqual(qm.classify({"exit": None, "timed_out": True}, green), "timeout")
        self.assertEqual(qm.classify({"exit": qm.NOT_COMPILED}, green), "not compiled")
        self.assertEqual(qm.classify({"exit": 1, "output": red["output"]}, red), "survived")
        self.assertEqual(qm.classify({"exit": 1, "output": red["output"] + "ERROR: test_b (t.T.test_b)\n"}, red),
                         "killed")
        js_red = {"exit": 1, "output": "Success: a in 1ms\nFailure: map tests in 7.86ms\n"}
        self.assertEqual(qm.failing(js_red), {"map tests"})
        self.assertEqual(qm.classify({"exit": 1, "output": js_red["output"] + "Failure: undo in 310.2\u03bcs\n"},
                                     js_red), "killed")
        self.assertEqual(qm.score([{"result": "killed", "covered": True}, {"result": "survived", "covered": False,
                                   "path": "a", "line": 1, "operator": "x", "original": "<", "mutated": ">"},
                                   {"result": "not compiled", "covered": True}])["score"], 0.5)


class MeasureTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="dbq-mut-test-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        self.lot, self.units = build_lot(self.root, {"pkg/m.py": "x = 1\n"}, {"pkg/m.py": SOURCE})
        self.scene = {"language": "python", "image": "img", "timeout_seconds": 100}
        self.runs = []

    def fake(self, baseline_exit=0, baseline_output="FAIL: t (a.b)\n"):
        def runner(image, script, work, timeout, scene):
            self.runs.append((script, timeout))
            text = (work / "pkg/m.py").read_text()
            if len(self.runs) == 1:
                return {"exit": baseline_exit, "seconds": 50.0, "output": baseline_output if baseline_exit else ""}
            return {"exit": 0 if "a * 2" in text and "a + b" in text else 1, "seconds": 1.0}
        return runner

    def test_uncovered_lines_survive_without_running(self):
        cov = coverage({"pkg/m.py": ([2, 3], [4, 5])})
        record = qm.measure(self.lot, self.units[0], self.scene, cov, limit=50, jobs=2, runner=self.fake())
        self.assertEqual(record["status"], "ok", record)
        ran = [m for m in record["mutants"] if m["covered"]]
        self.assertTrue(all(m["line"] in (2, 3) for m in ran))
        self.assertTrue(all(m["result"] == "survived" for m in record["mutants"] if not m["covered"]))
        self.assertEqual(len(self.runs), 1 + len(ran))
        self.assertIn("-f", self.runs[1][0])
        self.assertEqual(self.runs[1][1], 150.0)  # three times the baseline, under twice the scenario's
        self.assertLess(record["score"], record["covered_score"])

    def test_without_coverage_or_with_a_broken_suite(self):
        self.assertEqual(qm.measure(self.lot, self.units[0], self.scene, None)["status"], "error")
        c_scene = {**self.scene, "language": "c"}
        cov = coverage({"pkg/m.py": ([2], [])})
        record = qm.measure(self.lot, self.units[0], c_scene, cov,  # all.lua names no test: it just stops
                            runner=self.fake(baseline_exit=1, baseline_output="lua: all.lua:3: assertion failed!\n"))
        self.assertEqual((record["status"], len(self.runs)), ("n/a", 1))


@unittest.skipUnless(os.environ.get("DBENCH_DOCKER_SMOKE") == "1", "Docker smoke: set DBENCH_DOCKER_SMOKE=1")
class DockerSmokeTests(unittest.TestCase):
    def test_python_in_the_scenario_image(self):
        root = Path(tempfile.mkdtemp(prefix="dbq-mut-smoke-"))
        self.addCleanup(shutil.rmtree, root, True)
        test = ("import unittest\nfrom pkg.m import f\n\n\nclass T(unittest.TestCase):\n"
                "    def test_f(self):\n        self.assertEqual(f(1, 2), 3)\n")
        lot, units = build_lot(root, {"pkg/__init__.py": ""}, {"pkg/__init__.py": "", "pkg/m.py": SOURCE,
                                                              "tests/__init__.py": "", "tests/test_m.py": test})
        scene = {"language": "python", "image": "dbench-sql-engine:1", "timeout_seconds": 300, "cpus": 2}
        cov = qc.measure(lot, units[0], scene)
        record = qm.measure(lot, units[0], scene, cov, limit=6)
        print(record.get("counts"), record.get("survivors"))
        self.assertEqual(record["status"], "ok", record)
        self.assertGreater(record["counts"]["killed"], 0, record)


if __name__ == "__main__":
    unittest.main()
