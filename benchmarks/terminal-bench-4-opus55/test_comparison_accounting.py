import json
import tempfile
import unittest
from pathlib import Path

from comparison_accounting import ComparisonLedger, AccountingError, read_model_journal


class ComparisonLedgerTests(unittest.TestCase):
    def ledger(self, path):
        return ComparisonLedger(path, binding_sha256="a" * 64, authority_sha256="b" * 64,
                                prior_ledger_sha256="c" * 64,
                                prior_commitment_usd="120.17657720000000002")

    def test_separate_twelve_cells_and_project_admission(self):
        with tempfile.TemporaryDirectory() as temp:
            ledger = self.ledger(Path(temp) / "lot.jsonl")
            for task in ledger.tasks:
                for arm in ledger.arms:
                    ledger.reserve(task, arm)
                    ledger.start(task, arm)
                    ledger.settle(task, arm, "0.50", "d" * 64)
            state = ledger.state()
            self.assertEqual(state["starts"], 12)
            self.assertEqual(state["spent_usd"], "6.00")
            self.assertEqual(state["prior_observed_usd"], "unknown")
            self.assertEqual(state["remaining_usd"], "714.00")
            with self.assertRaises(AccountingError):
                ledger.reserve(ledger.tasks[0], ledger.arms[0])

    def test_new_unknown_cost_blocks_all_further_starts_with_no_waiver(self):
        with tempfile.TemporaryDirectory() as temp:
            ledger = self.ledger(Path(temp) / "lot.jsonl")
            task, arm = ledger.tasks[0], ledger.arms[0]
            ledger.reserve(task, arm)
            ledger.start(task, arm)
            ledger.settle(task, arm, None, "d" * 64)
            self.assertEqual(ledger.state()["spent_usd"], "unknown")
            with self.assertRaises(AccountingError):
                ledger.reserve(ledger.tasks[1], arm)
            self.assertFalse(hasattr(ledger, "assume_reservation"))

    def test_pending_start_reservation_and_binding_drift_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "lot.jsonl"
            ledger = self.ledger(path)
            task, arm = ledger.tasks[0], ledger.arms[0]
            ledger.reserve(task, arm)
            with self.assertRaises(AccountingError):
                ledger.reserve(ledger.tasks[1], arm)
            ledger.start(task, arm)
            with self.assertRaises(AccountingError):
                ledger.start(task, arm)
            ledger.settle(task, arm, "61", "d" * 64)
            self.assertTrue(ledger.state()["blocked"])
            with self.assertRaises(AccountingError):
                ComparisonLedger(path, binding_sha256="e" * 64, authority_sha256="b" * 64,
                                 prior_ledger_sha256="c" * 64,
                                 prior_commitment_usd="120.17657720000000002")


class JournalTests(unittest.TestCase):
    identity = {"task": "fixture", "arm": "pi-bare"}

    def rows(self):
        budget = dict(requests=0, pendingRequests=0, maxPerRequestUsd=8.2, reservedUsd=0,
                      observedUsd=0, ambiguous=False, maxRequests=48, limitUsd="57")
        initial = dict(schema=1, seq=0, event="initial", phase="initial", identity=self.identity,
                       budget=budget, known=True, cost_usd=0, input_tokens=0, output_tokens=0)
        request = {**initial, "seq": 1, "event": "request", "known": False, "cost_usd": None,
                   "budget": {**budget, "requests": 1, "pendingRequests": 1, "reservedUsd": 8.2}}
        usage = {**initial, "seq": 2, "event": "usage", "cost_usd": 0.01,
                 "input_tokens": 12, "output_tokens": 3,
                 "budget": {**budget, "requests": 1, "observedUsd": 0.01, "reservedUsd": 0.01}}
        return [initial, request, usage]

    def read_rows(self, rows, identity=None):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "usage.jsonl"
            path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf8")
            return read_model_journal(path, identity or self.identity)

    def test_completed_prefix_cost_is_known_even_if_parent_later_failed(self):
        receipt = self.read_rows(self.rows())
        self.assertEqual(receipt["cost_usd"], 0.01)
        self.assertEqual(receipt["input_tokens"], 12)
        self.assertFalse(receipt["terminal"])

    def test_pending_request_never_becomes_free(self):
        receipt = self.read_rows(self.rows()[:2])
        self.assertIsNone(receipt["cost_usd"])
        self.assertFalse(receipt["known"])

    def test_wrong_identity_forged_settlement_sequence_and_tariff_are_rejected(self):
        rows = self.rows()
        with self.assertRaises(AccountingError):
            self.read_rows(rows, {"task": "other"})
        for mutation in (lambda r: r[2].update(seq=9),
                         lambda r: r[1].update(known=True, cost_usd=0),
                         lambda r: r[2]["budget"].update(observedUsd=0),
                         lambda r: r[2]["budget"].update(maxRequests=49)):
            mutated = self.rows()
            mutation(mutated)
            with self.assertRaises(AccountingError):
                self.read_rows(mutated)


if __name__ == "__main__":
    unittest.main()
