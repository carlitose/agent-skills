"""One human-authorized admission exception; never an observed cost receipt."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from pilot_ledger import GateError, PilotLedger

MANIFEST = Path(__file__).with_name("manifest.json")


class PilotExceptionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "pilot.jsonl"
        self.ledger = PilotLedger(self.path, MANIFEST, standard=True)
        self.ledger.reserve("html-js-filter", "pi-bare", "60")
        self.ledger.start("html-js-filter", "pi-bare")
        self.ledger.settle("html-js-filter", "pi-bare", status="valid", cost_usd="1.25",
                           input_tokens=10, output_tokens=5, elapsed_seconds="2",
                           verifier_pass=False, receipt_sha256="a" * 64)
        self.ledger.reserve("interleaved-vigenere", "pi-bare", "60")
        self.ledger.start("interleaved-vigenere", "pi-bare")
        with self.assertRaisesRegex(GateError, "unknown cost"):
            self.ledger.settle("interleaved-vigenere", "pi-bare", status="failed",
                               cost_usd=None, input_tokens=None, output_tokens=None,
                               elapsed_seconds=None, verifier_pass=None, receipt_sha256=None)
        self.prefix = self.path.read_bytes()
        self.args = dict(expected_ledger_sha256=hashlib.sha256(self.prefix).hexdigest(),
                         actor="human user", authorization_sha256="b" * 64,
                         failed_result_sha256="c" * 64)

    def test_assumption_keeps_unknown_cost_but_admits_only_unused_third_cell(self):
        self.ledger.assume_second_start_reservation(**self.args)
        state = self.ledger.state()
        self.assertEqual(state["spent_usd"], "unknown")
        self.assertEqual(state["remaining_usd"], "unknown")
        self.assertEqual(state["known_spent_usd"], "1.25")
        self.assertEqual(state["assumed_usd"], "60")
        self.assertEqual(state["admission_spent_usd"], "61.25")
        self.assertEqual(state["admission_remaining_usd"], "188.75")
        self.assertFalse(state["ambiguous"])
        self.assertEqual(PilotLedger(self.path, MANIFEST, standard=True).state(), state)
        self.assertTrue(self.path.read_bytes().startswith(self.prefix))
        self.ledger.reserve("wal-recovery-ordering", "pi-bare", "60")
        self.ledger.start("wal-recovery-ordering", "pi-bare")
        self.ledger.settle("wal-recovery-ordering", "pi-bare", status="valid", cost_usd="2",
                           input_tokens=10, output_tokens=5, elapsed_seconds="2",
                           verifier_pass=True, receipt_sha256="d" * 64)
        state = self.ledger.state()
        self.assertEqual(state["starts"], 3)
        self.assertEqual(state["spent_usd"], "unknown")
        self.assertEqual(state["known_spent_usd"], "3.25")
        self.assertEqual(state["admission_spent_usd"], "63.25")

    def test_no_authority_or_stale_prefix_never_appends(self):
        for key, value in (("actor", ""), ("authorization_sha256", ""),
                           ("failed_result_sha256", "invalid"),
                           ("expected_ledger_sha256", "f" * 64)):
            with self.subTest(key=key), self.assertRaises(GateError):
                self.ledger.assume_second_start_reservation(**{**self.args, key: value})
            self.assertEqual(self.path.read_bytes(), self.prefix)

    def test_duplicate_exception_and_retries_are_forbidden(self):
        self.ledger.assume_second_start_reservation(**self.args)
        with self.assertRaises(GateError):
            self.ledger.assume_second_start_reservation(**self.args)
        for name in ("html-js-filter", "interleaved-vigenere"):
            with self.assertRaisesRegex(GateError, "already used"):
                self.ledger.reserve(name, "pi-bare", "60")

    def test_no_exception_for_modified_method(self):
        modified = PilotLedger(Path(self.temp.name) / "modified.jsonl", MANIFEST)
        with self.assertRaises(GateError):
            modified.assume_second_start_reservation(**self.args)

    def test_no_exception_before_the_exact_failed_second_start(self):
        before = self.prefix.splitlines(keepends=True)
        self.path.write_bytes(b"".join(before[:-1]))
        args = {**self.args, "expected_ledger_sha256": hashlib.sha256(self.path.read_bytes()).hexdigest()}
        with self.assertRaises(GateError):
            self.ledger.assume_second_start_reservation(**args)

    def test_third_unknown_still_blocks_and_cannot_receive_same_exception(self):
        self.ledger.assume_second_start_reservation(**self.args)
        self.ledger.reserve("wal-recovery-ordering", "pi-bare", "60")
        self.ledger.start("wal-recovery-ordering", "pi-bare")
        with self.assertRaisesRegex(GateError, "unknown cost"):
            self.ledger.settle("wal-recovery-ordering", "pi-bare", status="failed",
                               cost_usd=None, input_tokens=None, output_tokens=None,
                               elapsed_seconds=None, verifier_pass=None, receipt_sha256=None)
        self.assertTrue(self.ledger.state()["ambiguous"])
        self.assertEqual(self.ledger.state()["admission_remaining_usd"], "unknown")
        args = {**self.args, "expected_ledger_sha256": hashlib.sha256(self.path.read_bytes()).hexdigest()}
        with self.assertRaises(GateError):
            self.ledger.assume_second_start_reservation(**args)

    def test_replayed_event_cannot_lower_reserve_or_change_authority(self):
        self.ledger.assume_second_start_reservation(**self.args)
        event = json.loads(self.path.read_bytes().splitlines()[-1])
        for key, value in (("assumed_usd", "0"), ("actor", ""),
                           ("task", "wal-recovery-ordering"),
                           ("expected_ledger_sha256", "f" * 64)):
            with self.subTest(key=key):
                self.path.write_bytes(self.prefix + json.dumps({**event, key: value}).encode() + b"\n")
                with self.assertRaises(GateError):
                    self.ledger.state()


if __name__ == "__main__":
    unittest.main()
