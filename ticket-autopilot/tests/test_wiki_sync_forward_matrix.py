from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORT = (
    ROOT
    / "docs"
    / "research"
    / "llm-wiki-docs-only-autosync-forward-test.json"
)


class WikiSyncForwardMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def test_report_covers_both_triggers_and_the_decision_matrix(self) -> None:
        self.assertEqual(1, self.report["schema"])
        self.assertEqual("pass", self.report["status"])
        scenarios = self.report["scenarios"]
        self.assertEqual(10, len(scenarios))
        self.assertEqual(
            {"after-ticket-batch", "post-integration", "both"},
            {scenario["trigger"] for scenario in scenarios},
        )
        states = " ".join(scenario["wiki_state"] for scenario in scenarios)
        for required in (
            "absent",
            "untracked",
            "tracked",
            "external",
            "ambiguous",
            "broken",
            "partial",
            "mixed",
            "stale",
            "concurrent",
        ):
            self.assertIn(required, states)

    def test_report_keeps_docs_only_authority_and_claims_bounded(self) -> None:
        invariants = "\n".join(self.report["invariants"])
        self.assertIn("no scenario scaffolds a missing wiki", invariants)
        self.assertIn("never primary evidence", invariants)
        self.assertIn("CandidateRefs are not mutated or reused", invariants)
        self.assertIn("exact-head authorized", invariants)
        self.assertTrue(
            all(
                scenario.get("claim_ceiling") == "implementation-complete"
                for scenario in self.report["scenarios"]
                if scenario["wiki_state"] == "internal-tracked"
            )
        )
        limitations = "\n".join(self.report["limitations"])
        self.assertIn("no live provider mutation is claimed", limitations)
        self.assertIn("implementation-complete", limitations)

    def test_reported_public_boundary_suites_pass(self) -> None:
        command_ids = {command["id"] for command in self.report["commands"]}
        self.assertEqual(
            command_ids,
            {scenario["command_id"] for scenario in self.report["scenarios"]},
        )
        for command in self.report["commands"]:
            with self.subTest(command=command["id"]):
                completed = subprocess.run(
                    [sys.executable, *command["argv"]],
                    cwd=ROOT,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    check=False,
                )
                self.assertEqual(0, completed.returncode, completed.stdout)
                self.assertIn(
                    f"Ran {command['expected_tests']} tests",
                    completed.stdout,
                )


if __name__ == "__main__":
    unittest.main()
