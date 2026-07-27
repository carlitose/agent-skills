from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "ticket-autopilot" / "scripts"
FORWARD_TEST = SCRIPTS / "forward_test.py"
sys.path.insert(0, str(SCRIPTS))

import forward_test


REQUIRED_SCENARIOS = {
    "audit-evidence-gap",
    "azure-devops-adapter",
    "child-rebase-retarget",
    "cycle",
    "dependency-chain",
    "dirty-caller-worktree",
    "explicit-hitl",
    "full-new-schema-pipeline",
    "git-finalization-failure",
    "github-adapter",
    "independent-ticket-set",
    "interruption-resume",
    "invalid-pr-body",
    "merge-authorization-invalidation",
    "merge-gated-multi-blocker-join",
    "missing-dependency",
    "parent-merge",
    "qa-implementation-failure",
    "remote-divergence",
    "review-fix-loop",
    "safe-force-with-lease",
    "stacked-single-parent-pr",
    "unavailable-credentials",
    "waiting-vs-completed",
}


class ForwardTestRunnerTests(unittest.TestCase):
    def test_matrix_covers_the_accepted_forward_scenarios(self) -> None:
        self.assertEqual(REQUIRED_SCENARIOS, set(forward_test.SCENARIOS))
        for scenario_id, scenario in forward_test.SCENARIOS.items():
            with self.subTest(scenario=scenario_id):
                self.assertTrue(scenario["prompt"])
                self.assertTrue(scenario["tests"])
                self.assertNotIn("expected", scenario["prompt"].casefold())
                self.assertEqual(
                    {
                        "artifact",
                        "command",
                        "final_report",
                        "ledger",
                    },
                    set(scenario["retained_evidence"]),
                )

    def test_list_is_stable_machine_readable_and_does_not_run_tests(self) -> None:
        first = subprocess.run(
            [sys.executable, "-B", str(FORWARD_TEST), "--list"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        second = subprocess.run(
            [sys.executable, "-B", str(FORWARD_TEST), "--list"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertEqual(first.stdout, second.stdout)
        payload = json.loads(first.stdout)
        self.assertEqual(1, payload["schema"])
        self.assertEqual(sorted(REQUIRED_SCENARIOS), payload["scenario_ids"])
        self.assertNotIn("results", payload)

    def test_one_scenario_retains_command_artifact_and_final_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "cycle.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(FORWARD_TEST),
                    "--scenario",
                    "cycle",
                    "--output",
                    str(artifact),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload, json.loads(artifact.read_text()))
            self.assertEqual("pass", payload["result"])
            self.assertEqual(["cycle"], list(payload["scenarios"]))
            scenario = payload["scenarios"]["cycle"]
            self.assertEqual("pass", scenario["result"])
            self.assertTrue(scenario["commands"])
            self.assertTrue(scenario["ledger_assertions"])
            self.assertEqual(str(artifact), scenario["artifact"])
            self.assertIn("limitations", scenario)


if __name__ == "__main__":
    unittest.main()
