"""DBH-29: coverage over the added lines. Readers run on canned tool output; the Docker smoke on
toy projects in the real images runs only with DBENCH_DOCKER_SMOKE=1."""
from __future__ import annotations

import gzip
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import quality
import quality_coverage as qc
import runner


def git(project: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(project), "-c", "core.autocrlf=false", *args],
                          capture_output=True, text=True, check=True).stdout.strip()


def build_lot(root: Path, before: dict, after: dict) -> tuple[Path, dict]:
    """A one-cell lot whose single request turned ``before`` into ``after`` and committed it."""
    lot, cell = root / "lot", root / "lot" / "cells" / "toy.bare.r1"
    project = root / "arm" / "project"
    project.mkdir(parents=True)
    git(project, "init", "-q")
    for files in (before, after):
        for path, data in files.items():
            (project / path).parent.mkdir(parents=True, exist_ok=True)
            (project / path).write_bytes(data.encode("utf-8"))
        git(project, "add", "-A")
        git(project, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "step", "--allow-empty")
        if files is before:
            base = git(project, "rev-parse", "HEAD")
            shutil.copytree(project, cell / "snapshot" / "project")
    diff = runner.request_diff(project, base, cell / "diffs" / "01.diff", cell / "diffs" / "objects")
    (lot / "lot.json").write_bytes(json.dumps({"cells": {"toy.bare.r1": {"arm_dir": str(project.parent)}}}).encode())
    (cell / "cell.json").write_bytes(json.dumps({"arm": "bare", "scenario": "toy", "lot": "lot", "requests": [
        {"request": 1, "status": "judged", "diff": diff}, {"request": 2, "status": "running"}]}).encode())
    return lot, quality.units(lot)


class AddedLinesTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="dbq-cov-test-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_only_added_source_lines_count(self):
        lot, units = build_lot(self.root, {"pkg/a.py": "a = 1\nb = 2\nc = 3\n", "pkg/gone.py": "x = 1\n"},
                               {"pkg/a.py": "a = 1\nb = 20\nc = 3\nd = 4\n", "pkg/gone.py": "",
                                "tests/test_a.py": "t = 1\n", "pkg/a_test.py": "t = 1\n",
                                "docs/specs/s.md": "spec\n", "pkg/new.py": "n = 1\nm = 2\n"})
        self.assertEqual(qc.added_lines(lot, units[0], "python"), {"pkg/a.py": [2, 4], "pkg/new.py": [1, 2]})

    def test_source_classification(self):
        for path, language, expected in (("src/lapi.c", "c", True), ("testes/x.c", "c", False),
                                         ("src/y.tests.js", "javascript", False),
                                         ("tests/y-map.tests.js", "javascript", False), ("dist/yjs.cjs", "javascript", False),
                                         ("sqlglot/executor/python.py", "python", True),
                                         ("tests/test_executor.py", "python", False), ("src/a.h", "c", False)):
            with self.subTest(path=path):
                self.assertEqual(qc.is_source(path, language), expected)


class ReaderTests(unittest.TestCase):
    def setUp(self):
        self.work = Path(tempfile.mkdtemp(prefix="dbq-cov-read-"))
        self.addCleanup(shutil.rmtree, self.work, True)
        self.raw = self.work / qc.RAW
        self.raw.mkdir()

    def test_gcov_json_lines_and_counts(self):
        report = {"files": [{"file": "lapi.c", "lines": [{"line_number": 3, "count": 2}, {"line_number": 4, "count": 0}]},
                            {"file": "lua.h", "lines": [{"line_number": 9, "count": 1}]}]}
        (self.raw / "lapi.c.gcov.json.gz").write_bytes(gzip.compress(json.dumps(report).encode()))
        self.assertEqual(qc.read_c(self.raw, self.work, {})["src/lapi.c"], ({3, 4}, {3}))

    def test_coverage_py_json(self):
        report = {"files": {"sqlglot/x.py": {"executed_lines": [1, 2], "missing_lines": [5]},
                            "/work/sqlglot/y.py": {"executed_lines": [], "missing_lines": [1]}}}
        (self.raw / "coverage.json").write_text(json.dumps(report))
        seen = qc.read_python(self.raw, self.work, {})
        self.assertEqual(seen["sqlglot/x.py"], ({1, 2, 5}, {1, 2}))
        self.assertEqual(seen["sqlglot/y.py"], ({1}, set()))

    def test_v8_innermost_range_decides_and_offsets_are_utf16(self):
        source = "const s = '\U0001F600'\nexport function f () {\n  if (s) {\n    return 1\n  }\n  return 2\n}\n// note\n"
        (self.work / "src").mkdir()
        (self.work / "src" / "a.js").write_bytes(source.encode("utf-8"))
        line = [0]
        for text in source.splitlines(keepends=True):
            line.append(line[-1] + qc._utf16(text))
        body_start = line[1]
        report = {"result": [{"url": "file:///work/src/a.js", "functions": [
            {"ranges": [{"startOffset": 0, "endOffset": line[-1], "count": 1}]},
            {"ranges": [{"startOffset": body_start, "endOffset": line[7], "count": 1},
                        {"startOffset": line[3] - 2,  # `{ return 1 }`, never taken
                         "endOffset": line[5], "count": 0}]}]}]}
        (self.raw / "coverage-1-2-3.json").write_text(json.dumps(report))
        executable, covered = qc.read_javascript(self.raw, self.work, {"src/a.js": [1, 2, 3, 4, 5, 6, 7, 8]})["src/a.js"]
        self.assertEqual(executable, {1, 2, 3, 4, 6})  # `}` and the comment are not code
        self.assertEqual(covered, {1, 2, 3, 6})  # line 4 is inside the untaken block

    def test_no_report_means_no_data(self):
        self.assertEqual(qc.read_python(self.raw, self.work, {}), {})
        self.assertEqual(qc.read_javascript(self.raw, self.work, {"src/a.js": [1]}), {})


class MeasureTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="dbq-cov-measure-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        self.lot, self.units = build_lot(self.root, {"pkg/a.py": "a = 1\n"},
                                         {"pkg/a.py": "a = 1\nb = 2\nc = 3\n", "pkg/doc.py": "# only\n"})
        self.scene = {"language": "python", "image": "toy:1", "timeout_seconds": 10}
        self.images = []
        patcher = mock.patch.object(qc, "coverage_image", lambda s: self.images.append(s) or "toy-cov:1")
        patcher.start()
        self.addCleanup(patcher.stop)

    def fake(self, files):
        def run(image, command, work, timeout, cpus, memory):
            self.call = (image, command, sorted(p.name for p in work.iterdir()), timeout)
            if files is not None:
                (work / qc.RAW).mkdir()
                (work / qc.RAW / "coverage.json").write_text(json.dumps({"files": files}))
            return {"exit": 1, "timed_out": False, "seconds": 0.1, "tail": ""}
        return run

    def test_share_of_executable_added_lines_run_by_the_tests(self):
        record = qc.measure(self.lot, self.units[0], self.scene, self.fake(
            {"pkg/a.py": {"executed_lines": [1, 2], "missing_lines": [3]}, "pkg/doc.py": {"executed_lines": [],
                                                                                          "missing_lines": []}}))
        self.assertEqual((record["status"], record["added"], record["executable"], record["covered"]), ("ok", 3, 2, 1))
        self.assertEqual(record["score"], 0.5)
        self.assertEqual(record["files"]["pkg/a.py"]["missed"], [3])
        self.assertEqual(self.call[0], "toy-cov:1")
        self.assertIn("pkg", self.call[2])  # the unit's tree, rebuilt in a throwaway copy
        self.assertEqual(self.call[3], 20)  # twice the scenario's timeout: coverage slows the suite

    def test_no_code_and_no_data(self):
        self.assertEqual(qc.measure(self.lot, self.units[1], self.scene, self.fake({}))["reason"], "no code")
        record = qc.measure(self.lot, self.units[0], self.scene, self.fake(None))
        self.assertEqual((record["status"], record["score"]), ("error", None))


@unittest.skipUnless(os.environ.get("DBENCH_DOCKER_SMOKE") == "1", "Docker smoke: set DBENCH_DOCKER_SMOKE=1")
class DockerSmokeTests(unittest.TestCase):
    """Each language's real command and image on a toy project: one used and one unused function."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="dbq-cov-smoke-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def check(self, scene, before, after, path, covered, missed):
        lot, units = build_lot(self.root, before, after)
        record = qc.measure(lot, units[0], scene)
        self.assertEqual(record["status"], "ok", record)
        self.assertTrue(set(covered) <= set(record["files"][path]["covered"]), record["files"])
        self.assertTrue(set(missed) <= set(record["files"][path]["missed"]), record["files"])

    def test_c_in_gcc(self):
        make = "linux:\n\t$(MAKE) -C src linux\n"
        src_make = ("CFLAGS= -O2 $(MYCFLAGS)\nlinux: lua\nlua: toy.o\n\t$(CC) -o lua toy.o $(MYLDFLAGS)\n"
                    "toy.o: toy.c\n\t$(CC) $(CFLAGS) -c toy.c\nclean:\n\trm -f lua *.o *.gcno *.gcda\n")
        toy = ("#include <stdio.h>\nint used(int x) {\n  return x + 1;\n}\nint unused(int x) {\n  return x * 2;\n}\n"
               "int main(void) {\n  printf(\"%d\\n\", used(1));\n  return 0;\n}\n")
        self.check({"language": "c", "image": "gcc:14", "timeout_seconds": 300},
                   {"Makefile": make, "src/Makefile": src_make, "testes/all.lua": "print(1)\n"},
                   {"src/toy.c": toy}, "src/toy.c", [3, 9], [6])

    def test_python_in_the_derived_image(self):
        mod = "def used():\n    return 1\n\n\ndef unused():\n    return 2\n"
        test = "import unittest\nfrom sqlglot import mod\n\n\nclass T(unittest.TestCase):\n" \
               "    def test_used(self):\n        self.assertEqual(mod.used(), 1)\n"
        self.check({"language": "python", "image": "dbench-sql-engine:1", "timeout_seconds": 300},
                   {"sqlglot/__init__.py": "", "tests/__init__.py": ""},
                   {"sqlglot/mod.py": mod, "tests/test_mod.py": test}, "sqlglot/mod.py", [2], [6])

    def test_javascript_from_src(self):
        src = "export const used = () => {\n  return 1\n}\nexport const unused = () => {\n  return 2\n}\n"
        test = "import { used } from '../src/index.js'\nif (used() !== 1) process.exit(1)\n"
        self.check({"language": "javascript", "image": "dbench-crdt-yjs:1", "timeout_seconds": 300},
                   {"package.json": '{"type": "module"}\n'},
                   {"src/index.js": src, "tests/index.js": test}, "src/index.js", [2], [5])


if __name__ == "__main__":
    unittest.main()
