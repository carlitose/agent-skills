"""The integrated chain code must not change the distributed driver's findings or questions."""
import hashlib
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent / "scripts"))
from findings import parse_findings  # noqa: E402

DISTRIBUTED_QUESTIONS = {
    "qa.evidence_class.json", "retry.recoverable.json", "review.findings_block.json",
    "review.scope_complete.json", "risk.semantic_change.json", "verify.claim_supported.json",
}
SCOPE_COMPLETE_SHA256 = "086ad6fb2b78a8580e4d49d90046f65e107942bb3d1931c6db21da46f943e1bc"


class DistributedFindingsTests(unittest.TestCase):
    def test_default_keeps_python_only_locations(self):
        self.assertEqual(parse_findings("[blocker] src/a.py:3 - Broken.")["state"], "parsed")
        for path in ("src/parser.c", "src/type.ts", "test.lua", "docs/a.md"):
            with self.subTest(path=path):
                self.assertEqual(parse_findings(f"[blocker] {path}:3 - Broken.")["state"], "unparsed")

    def test_any_extension_is_opt_in(self):
        parsed = parse_findings("[blocker] test.lua:3 - Broken.", any_extension=True)
        self.assertEqual(parsed["findings"], [
            {"severity": "blocker", "path": "test.lua", "line": 3, "text": "Broken."}])


class DistributedQuestionTests(unittest.TestCase):
    def test_question_registry_is_unchanged(self):
        folder = ROOT / "ticket-driver" / "questions"
        self.assertEqual({p.name for p in folder.glob("*.json")}, DISTRIBUTED_QUESTIONS)
        digest = hashlib.sha256((folder / "review.scope_complete.json").read_bytes()).hexdigest()
        self.assertEqual(digest, SCOPE_COMPLETE_SHA256)

    def test_benchmark_variant_lives_outside_the_registry(self):
        variant = ROOT / "benchmarks" / "delivery-bench" / "questions" / "review.scope_complete.json"
        self.assertEqual(json.loads(variant.read_text(encoding="utf-8"))["id"], "review.scope_complete")


if __name__ == "__main__":
    unittest.main()
