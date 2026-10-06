"""DBH-31: the blind review. A real Opus call on a toy unit runs only with DBENCH_OPUS_SMOKE=1."""
from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import quality_review as qr
from test_quality_coverage import build_lot

REAL_FIND = qr.anthropic_extension
GOOD = json.dumps({"bugs": [{"severity": "high", "file": "pkg/a.py", "line": 2, "why": "off by one"}],
                   "scores": {"correctness": 2, "tests": 3, "design": 4, "readability": 5}, "summary": "ok"})
USAGE = {"usage": {"cost_usd": 0.25}}


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="dbq-review-test-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        self.lot, self.units = build_lot(self.root, {"pkg/a.py": "a = 1\n", "TASK.md": "old\n"}, {
            "pkg/a.py": "a = 1\nb = 2  # written by pi-full in lot dbh-luna3d\n",
            "TASK.md": "Add b. (cell toy.bare.r1)\n", "docs/specs/b.md": "spec of the skills lane\n",
            "docs/tickets/b/01.md": "ticket\n", ".pi/settings.json": "{}\n"})
        lot = json.loads((self.lot / "lot.json").read_text())
        (self.lot / "lot.json").write_text(json.dumps({**lot, "pi_command": ["pi"]}))
        self.unit = dict(self.units[0], lot="dbh-luna3d", arm="pi-full")
        self.seen = []
        self.ext = {"path": "anthropic/index.ts", "version": "0", "sha256": "x"}
        patcher = mock.patch.object(qr, "anthropic_extension", lambda: self.ext)
        patcher.start()
        self.addCleanup(patcher.stop)

    def fake(self, *answers):
        answers = list(answers)

        def call(pi_command, tree, sessions, extension):
            root = tree.parent
            self.seen.append({"files": sorted(p.relative_to(tree).as_posix() for p in tree.rglob("*") if p.is_file()),
                              "request": (root / qr.REQUEST_FILE).read_text(encoding="utf-8"),
                              "change": (root / qr.CHANGE_FILE).read_text(encoding="utf-8"),
                              "neutral": tree.parent.name, "command": pi_command,
                              "extension": extension})
            return answers.pop(0), USAGE, {"exit": 0, "seconds": 1.0}
        return call

    def test_the_reviewer_sees_code_and_tests_only_with_names_redacted(self):
        record = qr.measure(self.lot, self.unit, call=self.fake(GOOD))
        seen = self.seen[0]
        self.assertEqual(seen["files"], ["TASK.md", "pkg/a.py"])  # no specs, tickets or .pi
        self.assertIn("+b = 2", seen["change"])
        self.assertNotIn("docs/specs", seen["change"])
        self.assertNotIn("TASK.md", seen["change"])
        everything = seen["request"] + seen["change"] + qr.PROMPT + seen["neutral"]
        for name in ("pi-full", "dbh-luna3d", "toy.bare.r1", "pi-tools", "bare-goal"):
            self.assertNotIn(name, everything.lower())
        self.assertEqual((seen["command"], seen["extension"]), (["pi"], "anthropic/index.ts"))
        self.assertEqual(record["extension"], self.ext)
        self.assertEqual((record["status"], record["score"], record["cost_usd"]), ("ok", 3.5, 0.25))

    def test_an_unreadable_answer_is_asked_once_more_then_recorded(self):
        record = qr.measure(self.lot, self.unit, call=self.fake("no json here", GOOD))
        self.assertEqual([t["status"] for t in record["reviews"][0]["tries"]], ["error", "ok"])
        self.assertEqual(record["cost_usd"], 0.5)
        record = qr.measure(self.lot, self.unit, call=self.fake("{}", "still {not json"))
        self.assertEqual((record["status"], record["score"]), ("error", None))
        self.assertEqual(len(record["reviews"][0]["tries"]), 2)

    def test_several_reviews_average_and_no_code_is_not_reviewed(self):
        other = GOOD.replace('"correctness": 2', '"correctness": 4')
        record = qr.measure(self.lot, self.unit, reviews=2, call=self.fake(GOOD, other))
        self.assertEqual((len(record["reviews"]), record["score"]), (2, 3.75))
        self.assertEqual(qr.measure(self.lot, self.units[1], call=self.fake())["reason"], "no code")

    def test_the_anthropic_extension_is_found_in_the_pi_packages(self):
        folder = self.root / "pkgs" / "anthropic"
        folder.mkdir(parents=True)
        (folder / "package.json").write_text(json.dumps({"name": qr.ANTHROPIC_PACKAGE, "version": "0.2.3"}))
        (folder / "index.ts").write_text("export default {}\n")
        settings = self.root / "agent" / "settings.json"
        settings.parent.mkdir()
        settings.write_text(json.dumps({"packages": ["npm:other", {"source": "../pkgs/anthropic"}]}))
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("DBENCH_ANTHROPIC_EXTENSION", None)
            found = REAL_FIND(settings)
        self.assertEqual((Path(found["path"]), found["version"]), ((folder / "index.ts").resolve(), "0.2.3"))
        settings.write_text(json.dumps({"packages": ["npm:other"]}))
        with self.assertRaises(FileNotFoundError):
            REAL_FIND(settings)

    def test_rubric(self):
        self.assertEqual(qr.parse_review("```json\n" + GOOD + "\n```")["scores"]["design"], 4)
        for bad in (('{"bugs": [], "scores": {"correctness": 6, "tests": 1, "design": 1, "readability": 1}, '
                     '"summary": ""}'),
                    '{"bugs": [{"severity": "fatal", "file": "a", "line": 1, "why": "x"}], "scores": {}, "summary": ""}',
                    '{"bugs": [], "scores": {"correctness": 1}, "summary": ""}', "nothing"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                qr.parse_review(bad)


@unittest.skipUnless(os.environ.get("DBENCH_OPUS_SMOKE") == "1", "real Opus call: set DBENCH_OPUS_SMOKE=1")
class OpusSmokeTests(unittest.TestCase):
    def test_a_real_review_of_a_planted_bug(self):
        root = Path(tempfile.mkdtemp(prefix="dbq-review-smoke-"))
        self.addCleanup(shutil.rmtree, root, True)
        code = ("def average(values):\n    \"\"\"Mean of a non-empty list.\"\"\"\n"
                "    return sum(values) / (len(values) - 1)\n")
        test = "from stats import average\n\n\ndef test_average():\n    assert average([2, 2, 2]) > 0\n"
        lot, units = build_lot(root, {"TASK.md": "x\n"}, {
            "TASK.md": "Add stats.average(values): the arithmetic mean of a non-empty list.\n",
            "stats.py": code, "tests/test_stats.py": test})
        record = json.loads((lot / "lot.json").read_text())
        pi = ["node", os.environ.get("PI_CLI", r"C:\Users\CGS03\AppData\Roaming\npm\node_modules"
                                     r"\@earendil-works\pi-coding-agent\dist\bundle\cli.js")]
        (lot / "lot.json").write_text(json.dumps({**record, "pi_command": pi}))
        result = qr.measure(lot, units[0])
        print(json.dumps(result, indent=1)[:3000])
        self.assertEqual(result["status"], "ok", result)
        review = result["reviews"][0]["review"]
        self.assertTrue(any(b["file"].endswith("stats.py") for b in review["bugs"]), review)
        self.assertGreater(result["cost_usd"], 0)


if __name__ == "__main__":
    unittest.main()
