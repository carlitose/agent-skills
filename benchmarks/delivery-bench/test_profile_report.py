"""Offline tests for the profile report: axes, paired rule, and no hidden check names.

    python -B -m unittest test_profile_report
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from profile_report import (
    holm,
    mcnemar_exact,
    paired,
    profile,
    render,
    report,
)


def request(n, accepted, *, trap=None, latent=(1, 2), cost=0.5, seconds=100.0, attempts=None,
            status="judged", timed_out=False):
    violated = [{"id": f"r{n}.trap.secret-name", "type": trap[0], "rule": 1, "temptation": n,
                 "distance": trap[1]}] if trap else []
    return {"request": n, "status": status, "timed_out": timed_out, "seconds": seconds,
            "attempts": attempts or [{"class": "agent"}], "infra_exhausted": False,
            "usage": {"input": 1000, "output": 200, "cacheRead": 5000, "cacheWrite": 0, "cost_usd": cost},
            "infra_usage": {"cost_usd": 0.0}, "jev": {"calls": 0, "usd_estimate": 0.0},
            "axes": {"acceptance": {"passed": 3 if accepted else 1, "total": 3, "accepted": accepted,
                                    "failed": [] if accepted else ["r1.feature.hidden-a"]},
                     "robustness": {"latent_found": latent[0], "latent_total": latent[1],
                                    "missed": ["r1.latent.hidden-b"]},
                     "compass": {"invariants": {"passed": 4, "total": 5, "failed": ["r1.inv.hidden-c"]},
                                 "traps_total": 2, "traps_violated": violated}}}


def cell(arm, rep, requests, scenario="python-billing", **extra):
    return {"schema": 1, "cell": f"{scenario}.{arm}.r{rep}", "arm": arm, "scenario": scenario,
            "rep": rep, "requests": requests, "invalid": False, "audit_hits": [],
            "chain_cap_hit": False, **extra}


class StatisticsTests(unittest.TestCase):
    def test_mcnemar_exact_two_sided(self):
        self.assertEqual(mcnemar_exact(0, 0), 1.0)
        self.assertAlmostEqual(mcnemar_exact(5, 0), 0.0625)
        self.assertAlmostEqual(mcnemar_exact(1, 4), 0.375)
        self.assertAlmostEqual(mcnemar_exact(10, 0), 2 / 1024)

    def test_holm_is_monotone_and_capped(self):
        self.assertEqual(holm({"a": 0.01, "b": 0.04, "c": 0.03}), {"a": 0.03, "b": 0.06, "c": 0.06})
        self.assertEqual(holm({"a": 0.9, "b": 0.8}), {"a": 1.0, "b": 1.0})


class ProfileTests(unittest.TestCase):
    def cells(self):
        return [
            cell("bare", 1, [request(1, False), request(2, False, trap=("convention", 1))]),
            cell("bare", 2, [request(1, True), request(2, False)]),
            cell("skills-only", 1, [request(1, True, cost=1.5), request(2, True, trap=("deprecated", 3))]),
            cell("skills-only", 2, [request(1, True, attempts=[{"class": "infra:provider"}, {"class": "agent"}]),
                                    request(2, True, timed_out=True)]),
            cell("autopilot", 1, [request(1, True)], invalid=True,
                 audit_hits=[{"pattern": "canary", "file": "sessions/x.jsonl", "request": 1}]),
        ]

    def test_axes_are_aggregated_per_request_and_per_arm(self):
        prof = profile(self.cells())
        row = next(r for r in prof["rows"] if r["arm"] == "skills-only" and r["request"] == 2)
        self.assertEqual((row["accepted"], row["reps"], row["traps_violated"]), (2, 2, 1))
        self.assertEqual(dict(row["trap_distance"]), {3: 1})
        self.assertEqual(row["timeouts"], 1)
        totals = {r["arm"]: r for r in prof["totals"]}
        self.assertEqual(totals["skills-only"]["infra_retries"], 1)
        self.assertAlmostEqual(totals["skills-only"]["cost_usd"], 3.0)
        self.assertEqual(totals["bare"]["invariants_broken"], 4)
        self.assertNotIn("autopilot", totals)
        self.assertEqual(prof["invalid"], [{"cell": "python-billing.autopilot.r1", "patterns": ["canary"]}])
        self.assertEqual(prof["infra_classes"], {"infra:provider": 1})

    def test_paired_rule_needs_a_difference_above_three(self):
        comparison = paired(self.cells())
        skills = comparison["versus"]["skills-only"]
        self.assertEqual((skills["pairs"], skills["only_arm"], skills["only_base"]), (4, 3, 0))
        self.assertEqual(skills["decision"], "indistinguishable")
        many = [cell("bare", r, [request(n, False) for n in (1, 2, 3)]) for r in (1, 2)]
        many += [cell("skills-only", r, [request(n, True) for n in (1, 2, 3)]) for r in (1, 2)]
        many += [cell("bare", 1, [request(1, False)], scenario="c-recq"),
                 cell("skills-only", 1, [request(1, True)], scenario="c-recq")]
        decided = paired(many)["versus"]["skills-only"]
        self.assertEqual((decided["difference"], decided["decision"]), (7, "better"))
        self.assertAlmostEqual(decided["p_holm"], 2 / 128)

    def test_markdown_never_names_a_hidden_check(self):
        text = render(profile(self.cells()), paired(self.cells()))
        for secret in ("secret-name", "hidden-a", "hidden-b", "hidden-c", "r1.", "r2."):
            self.assertNotIn(secret, text)
        self.assertIn("| python-billing | skills-only | 2 | 2/2 |", text)
        self.assertIn("d3×1", text)
        self.assertIn("python-billing.autopilot.r1", text)

    def test_report_reads_a_lot_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            for record in self.cells():
                path = Path(tmp) / "cells" / record["cell"] / "cell.json"
                path.parent.mkdir(parents=True)
                path.write_text(json.dumps(record), encoding="utf-8")
            prof, comparison, text = report(Path(tmp))
        self.assertEqual(len(prof["rows"]), 4)
        self.assertIn("skills-only", comparison["versus"])
        self.assertTrue(text.startswith("## Profile per request"))


if __name__ == "__main__":
    unittest.main()
