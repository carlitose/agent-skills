"""DBH-28: quality units, rebuilt trees and the robustness report, on a toy lot."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import quality
import runner


def git(project: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(project), "-c", "core.autocrlf=false", *args],
                          capture_output=True, text=True, check=True).stdout.strip()


def digest_tree(root: Path) -> dict:
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()}


class ToyLot:
    """One cell, two requests: the first changed code, the second left none.

    As in the runner, the snapshot is taken before the request and the arm commits its work,
    so the diff store gets none of the new objects: they are only in the arm's repository.
    """

    def __init__(self, root: Path):
        self.lot = root / "toy-lot"
        cell = self.lot / "cells" / "toy.pi-full.r1"
        project = root / "arm" / "project"
        project.mkdir(parents=True)
        git(project, "init", "-q")
        (project / "TASK.md").write_bytes(b"request 1\n")
        (project / "app.py").write_bytes(b"x = 1\n")
        git(project, "add", "-A")
        git(project, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "base")
        base = git(project, "rev-parse", "HEAD")
        shutil.copytree(project, cell / "snapshot" / "project")
        (project / "app.py").write_bytes(b"x = 2\n")
        (project / "lib").mkdir()
        (project / "lib" / "new.py").write_bytes(b"def f():\n    return 1\n")
        git(project, "add", "-A")
        git(project, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "work")
        diff = runner.request_diff(project, base, cell / "diffs" / "01.diff", cell / "diffs" / "objects")
        assert "tree" in diff, diff
        self.arm_dir = project.parent
        (self.lot / "lot.json").write_bytes(json.dumps(
            {"cells": {"toy.pi-full.r1": {"arm_dir": str(self.arm_dir)}}}).encode("utf-8"))
        self.expected = {"app.py": b"x = 2\n", "lib/new.py": b"def f():\n    return 1\n", "TASK.md": b"request 1\n"}
        axes = {"acceptance": {"accepted": True, "passed": 2, "total": 2},
                "robustness": {"latent_found": 1, "latent_total": 3, "missed": ["r1.latent.secret-name"]},
                "compass": {"invariants": {"failed": [], "passed": 1, "total": 1}, "traps_total": 1,
                            "traps_violated": [{"trap": "r1.trap.secret", "distance": 0}]}}
        cell_record = {"arm": "pi-full", "scenario": "toy", "rep": 1, "lot": "toy-lot",
                       "requests": [{"request": 1, "status": "judged", "diff": diff, "axes": axes},
                                    {"request": 2, "status": "running"}]}
        (cell / "cell.json").write_bytes(json.dumps(cell_record).encode("utf-8"))
        (self.lot / "ledger.jsonl").write_bytes(b'{"event": "launch"}\n')


class QualityTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="dbench-quality-test-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        self.toy = ToyLot(self.root)

    def test_every_request_is_a_unit_with_or_without_code(self):
        found = quality.units(self.toy.lot)
        self.assertEqual([(u["request"], u["status"], u["code"]) for u in found],
                         [(1, "judged", True), (2, "running", False)])
        self.assertEqual(found[0]["arm"], "pi-full")
        self.assertNotIn("pi-full", found[0]["unit"])
        self.assertEqual(found[0]["unit"], quality.unit_id("toy-lot", "toy.pi-full.r1", 1))

    def test_materialized_tree_is_the_recorded_tree_byte_for_byte(self):
        unit = quality.units(self.toy.lot)[0]
        dest = quality.materialize(self.toy.lot, unit, self.root / "out" / unit["unit"])
        for path, data in self.toy.expected.items():
            self.assertEqual((dest / path).read_bytes(), data, path)  # LF kept, whatever autocrlf says
        self.assertEqual(sorted(str(p.relative_to(dest).as_posix()) for p in dest.rglob("*") if p.is_file()),
                         sorted(self.toy.expected))

    def test_materialize_refuses_a_unit_without_code_or_an_existing_folder(self):
        no_code, unit = quality.units(self.toy.lot)[1], quality.units(self.toy.lot)[0]
        with self.assertRaises(ValueError):
            quality.materialize(self.toy.lot, no_code, self.root / "a")
        (self.root / "b").mkdir()
        with self.assertRaises(FileExistsError):
            quality.materialize(self.toy.lot, unit, self.root / "b")

    def test_work_committed_in_the_last_request_needs_the_arm_repository(self):
        store = self.toy.lot / "cells" / "toy.pi-full.r1" / "diffs" / "objects"
        self.assertEqual([p for p in store.rglob("*") if p.is_file()], [])  # the runner kept nothing
        self.toy.arm_dir.rename(self.root / "arm-gone")
        unit = quality.units(self.toy.lot)[0]
        with self.assertRaises(subprocess.CalledProcessError):
            quality.materialize(self.toy.lot, unit, self.root / "c")
        self.assertFalse((self.root / "c").exists())

    def test_report_counts_without_naming_hidden_checks_and_writes_only_under_quality(self):
        before = digest_tree(self.toy.lot)
        quality.main(["units", "--lot", str(self.toy.lot)])
        result = quality.report([self.toy.lot], self.toy.lot / "quality")
        row = next(r for r in result["rows"] if r["scenario"] == "toy")
        self.assertEqual((row["units"], row["with_code"], row["accepted"], row["judged"]), (2, 1, 1, 1))
        self.assertEqual((row["latent_found"], row["latent_total"], row["traps_violated"]), (1, 3, 1))
        self.assertEqual(row["latent_share"]["median"], 1 / 3)
        self.assertIsNone(row["coverage"]["score"])
        text = (self.toy.lot / "quality" / "report.md").read_text(encoding="utf-8")
        self.assertNotIn("secret", text)
        self.assertNotIn("secret", (self.toy.lot / "quality" / "report.json").read_text(encoding="utf-8"))
        after = {k: v for k, v in digest_tree(self.toy.lot).items() if not k.startswith("quality")}
        self.assertEqual(after, before)

    def test_measure_records_fill_their_column(self):
        unit = quality.units(self.toy.lot)[0]["unit"]
        folder = self.toy.lot / "quality" / "coverage"
        folder.mkdir(parents=True)
        (folder / f"{unit}.json").write_bytes(json.dumps({"score": 0.5}).encode())
        result = quality.report([self.toy.lot], self.root / "out")
        row = next(r for r in result["rows"] if r["scenario"] == "toy")
        self.assertEqual(row["coverage"], {"units": 1, "score": {"n": 1, "median": 0.5, "q1": 0.5, "q3": 0.5}})
        self.assertIn("50% [50%–50%] n=1", (self.root / "out" / "report.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
