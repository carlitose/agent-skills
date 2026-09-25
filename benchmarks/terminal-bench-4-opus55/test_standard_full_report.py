"""Offline: reduce original-harness lots (with infrastructure retries) into one report."""
import json
import tempfile
import unittest
from pathlib import Path

from standard_full_report import reduce_lots, render_markdown
from test_retry_classification import trial


def cell(jobs, task, *, cost=0.1, requests=5, known=True, **kwargs):
    d = trial(Path(jobs) / f"{task}__abc123", **kwargs)
    receipt = json.loads((d / "agent/standard-receipt.json").read_text())
    receipt["model"] = {"known": known, "cost_usd": cost if known else None,
                        "budget": {"requests": requests, "observedUsd": cost}}
    (d / "agent/standard-receipt.json").write_text(json.dumps(receipt))
    return d


class StandardFullReportTests(unittest.TestCase):
    def test_retries_replace_only_infrastructure_attempts_and_costs_add_up(self):
        with tempfile.TemporaryDirectory() as temp:
            b, r1 = Path(temp) / "b", Path(temp) / "r1"
            cell(b, "t-pass", reward=1.0, cost=0.5, requests=10)
            cell(b, "t-fail", reward=0.0, cost=0.2)
            cell(b, "t-net", reward=None, exc="ValueError", cost=0.3)
            cell(b, "t-drop", reward=0.0, exc="NonZeroAgentExitCodeError", agent_status="failed",
                 stop="error", error="WebSocket closed 1012", known=False, cost=2.0)
            cell(r1, "t-net", reward=1.0, cost=0.4)
            cell(r1, "t-drop", reward=0.0, cost=0.6)
            summary = reduce_lots([("B", b), ("retry-1", r1)],
                                  ["t-pass", "t-fail", "t-net", "t-drop", "t-missing"])
        rows = {row["task"]: row for row in summary["rows"]}
        self.assertEqual(rows["t-net"]["final_lot"], "retry-1")
        self.assertEqual(rows["t-net"]["reward"], 1.0)
        self.assertEqual(rows["t-drop"]["attempts"], ["infra:provider", "agent"])
        self.assertEqual(rows["t-fail"]["final_lot"], "B")
        self.assertEqual(rows["t-missing"]["status"], "not-run")
        self.assertEqual(summary["passed"], 2)
        self.assertEqual(summary["scored"], 4)
        self.assertEqual(summary["planned"], 5)
        self.assertAlmostEqual(summary["known_usd"], 0.5 + 0.2 + 0.3 + 0.4 + 0.6)
        self.assertEqual(summary["unknown_cost_attempts"], 1)
        self.assertEqual(summary["attempts"], 6)

    def test_pending_retry_and_exhausted_cells_are_not_scored(self):
        with tempfile.TemporaryDirectory() as temp:
            b, r1, r2 = (Path(temp) / n for n in ("b", "r1", "r2"))
            for lot in (b, r1, r2):
                cell(lot, "t-net", reward=None, exc="ValueError")
            cell(b, "t-wait", reward=None, exc="ValueError")
            summary = reduce_lots([("B", b), ("retry-1", r1), ("retry-2", r2)], ["t-net", "t-wait"])
        rows = {row["task"]: row for row in summary["rows"]}
        self.assertEqual(rows["t-net"]["status"], "exhausted")
        self.assertEqual(rows["t-wait"]["status"], "retry-pending")
        self.assertEqual(summary["scored"], 0)
        self.assertEqual(summary["retry"], ["t-wait"])

    def test_markdown_states_coverage_and_never_calls_a_partial_run_full(self):
        with tempfile.TemporaryDirectory() as temp:
            b = Path(temp) / "b"
            cell(b, "t-pass", reward=1.0)
            summary = reduce_lots([("B", b)], ["t-pass"])
        text = render_markdown(summary, excluded=["gpu-a", "gpu-b", "gpu-c"], dataset_total=66)
        self.assertIn("| t-pass | B | agent | 1 |", text)
        self.assertIn("1/1 scored", text)
        self.assertIn("partial", text)
        self.assertIn("gpu-a", text)


if __name__ == "__main__":
    unittest.main()
