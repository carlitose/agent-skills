"""Offline-only budget and attempt identity tests; no model or Harbor starts."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from pilot_ledger import GateError, PilotLedger

MANIFEST = Path(__file__).with_name("manifest.json")


class PilotLedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "pilot.jsonl"
        self.ledger = PilotLedger(self.path, MANIFEST)

    def test_one_cell_is_reserved_started_and_settled_once(self):
        self.ledger.reserve("html-js-filter", "pi-bare", "20")
        self.ledger.start("html-js-filter", "pi-bare")
        self.ledger.settle("html-js-filter", "pi-bare", status="valid", cost_usd="1.25",
                           input_tokens=100, output_tokens=30, elapsed_seconds="1.2",
                           verifier_pass=True, receipt_sha256="a" * 64)
        state = self.ledger.state()
        self.assertEqual(state["starts"], 1)
        self.assertEqual(state["spent_usd"], "1.25")
        self.assertEqual(state["remaining_usd"], "248.75")
        with self.assertRaisesRegex(GateError, "already used"):
            self.ledger.reserve("html-js-filter", "pi-bare", "1")
        # A new process must read the same immutable identity and cost.
        self.assertEqual(PilotLedger(self.path, MANIFEST).state(), state)

    def test_invalid_cell_or_cost_cannot_reserve(self):
        for task, arm, limit in (("not-a-pilot-task", "pi-bare", "1"),
                                 ("html-js-filter", "other-arm", "1"),
                                 ("html-js-filter", "pi-bare", "251"),
                                 ("html-js-filter", "pi-bare", "NaN")):
            with self.subTest(task=task, arm=arm, limit=limit), self.assertRaises(GateError):
                self.ledger.reserve(task, arm, limit)
        self.assertEqual(self.ledger.state()["starts"], 0)

    def test_next_cell_waits_for_attributable_cost_and_unknown_remains_unknown(self):
        self.ledger.reserve("html-js-filter", "pi-bare", "20")
        self.ledger.start("html-js-filter", "pi-bare")
        with self.assertRaisesRegex(GateError, "unresolved"):
            self.ledger.reserve("interleaved-vigenere", "skills-only", "1")
        with self.assertRaisesRegex(GateError, "unknown cost"):
            self.ledger.settle("html-js-filter", "pi-bare", status="failed", cost_usd=None,
                               input_tokens=None, output_tokens=None, elapsed_seconds=None,
                               verifier_pass=None, receipt_sha256=None)
        state = self.ledger.state()
        self.assertTrue(state["ambiguous"])
        self.assertEqual(state["spent_usd"], "unknown")
        self.assertEqual(state["known_spent_usd"], "0")
        self.assertEqual(state["starts"], 1)
        with self.assertRaisesRegex(GateError, "ambiguous"):
            self.ledger.reserve("interleaved-vigenere", "skills-only", "1")

    def test_budget_is_cumulative_and_overrun_blocks_new_spending(self):
        self.ledger.reserve("html-js-filter", "pi-bare", "240")
        self.ledger.start("html-js-filter", "pi-bare")
        self.ledger.settle("html-js-filter", "pi-bare", status="failed", cost_usd="240",
                           input_tokens=100, output_tokens=40, elapsed_seconds="1",
                           verifier_pass=False, receipt_sha256="b" * 64)
        with self.assertRaisesRegex(GateError, "budget"):
            self.ledger.reserve("interleaved-vigenere", "skills-only", "11")
        self.ledger.reserve("interleaved-vigenere", "skills-only", "10")
        self.ledger.start("interleaved-vigenere", "skills-only")
        with self.assertRaisesRegex(GateError, "overrun"):
            self.ledger.settle("interleaved-vigenere", "skills-only", status="failed",
                               cost_usd="10.5", input_tokens=100, output_tokens=40,
                               elapsed_seconds="2", verifier_pass=False,
                               receipt_sha256="c" * 64)
        self.assertEqual(self.ledger.state()["spent_usd"], "250.5")
        with self.assertRaisesRegex(GateError, "ambiguous"):
            self.ledger.reserve("wal-recovery-ordering", "pi-bare", "1")

    def test_new_ledger_can_create_a_nested_logs_directory(self):
        nested = Path(self.temp.name) / "logs" / "pilot.jsonl"
        self.assertEqual(PilotLedger(nested, MANIFEST).state()["starts"], 0)

    def test_manifest_with_pilot_verifier_gpu_fails_closed(self):
        altered = Path(self.temp.name) / "gpu-manifest.json"
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        next(t for t in manifest["tasks"] if t["name"] == "html-js-filter")["verifier_gpus"] = 1
        altered.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(GateError, "manifest"):
            PilotLedger(Path(self.temp.name) / "gpu.jsonl", altered)

    def test_zero_reported_cost_with_output_tokens_is_unattributable(self):
        self.ledger.reserve("html-js-filter", "pi-bare", "1")
        self.ledger.start("html-js-filter", "pi-bare")
        with self.assertRaisesRegex(GateError, "unknown cost"):
            self.ledger.settle("html-js-filter", "pi-bare", status="failed", cost_usd="0",
                               input_tokens=100, output_tokens=3, elapsed_seconds="1",
                               verifier_pass=False, receipt_sha256="e" * 64)
        self.assertEqual(self.ledger.state()["spent_usd"], "unknown")

    def test_completed_result_requires_verifier_observation(self):
        self.ledger.reserve("html-js-filter", "pi-bare", "1")
        self.ledger.start("html-js-filter", "pi-bare")
        with self.assertRaisesRegex(GateError, "verifier"):
            self.ledger.settle("html-js-filter", "pi-bare", status="valid", cost_usd="0",
                               input_tokens=0, output_tokens=0, elapsed_seconds="1",
                               verifier_pass=None, receipt_sha256="d" * 64)
        with self.assertRaisesRegex(GateError, "unresolved"):
            self.ledger.reserve("interleaved-vigenere", "pi-bare", "1")

    def test_standard_frozen_hashes_ignore_checkout_newline_conversion(self):
        data = MANIFEST.read_bytes().replace(b"\r\n", b"\n")
        lf = Path(self.temp.name) / "lf.json"
        crlf = Path(self.temp.name) / "crlf.json"
        lf.write_bytes(data)
        crlf.write_bytes(data.replace(b"\n", b"\r\n"))
        first = PilotLedger(Path(self.temp.name) / "lf.jsonl", lf, standard=True)
        second = PilotLedger(Path(self.temp.name) / "crlf.jsonl", crlf, standard=True)
        self.assertEqual(first.header["manifest_sha256"], second.header["manifest_sha256"])
        self.assertEqual(first.header["manifest_sha256"], hashlib.sha256(data).hexdigest())
        frozen = Path(__file__).with_name("standard-pilot.json").read_bytes().replace(b"\r\n", b"\n")
        self.assertEqual(first.header["standard_binding_sha256"], hashlib.sha256(frozen).hexdigest())

    def test_standard_pilot_is_three_original_task_cells_and_one_method(self):
        standard = PilotLedger(Path(self.temp.name) / "standard.jsonl", MANIFEST, standard=True)
        self.assertEqual(standard.header["method"], "original-harbor-pi-bare")
        self.assertEqual(standard.header["max_starts"], 3)
        self.assertEqual(standard.header["arms"], ["pi-bare"])
        with self.assertRaisesRegex(GateError, "frozen pilot"):
            standard.reserve("html-js-filter", "skills-only", "60")
        with self.assertRaisesRegex(GateError, "standard.*reservation"):
            standard.reserve("html-js-filter", "pi-bare", "61")
        standard.reserve("html-js-filter", "pi-bare", "60")
        standard.start("html-js-filter", "pi-bare")
        standard.settle("html-js-filter", "pi-bare", status="failed", cost_usd="0.2",
                        input_tokens=200, output_tokens=20, elapsed_seconds="1",
                        verifier_pass=False, receipt_sha256="a" * 64)
        self.assertEqual(standard.state()["starts"], 1)
        with self.assertRaisesRegex(GateError, "manifest or model binding"):
            PilotLedger(standard.path, MANIFEST)

    def test_corrupted_or_different_manifest_fails_closed(self):
        self.ledger.reserve("html-js-filter", "pi-bare", "1")
        with self.path.open("a", encoding="utf-8") as output:
            output.write("{bad json\n")
        with self.assertRaisesRegex(GateError, "corrupt"):
            self.ledger.state()
        altered = Path(self.temp.name) / "other-manifest.json"
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        manifest["pilot_tasks"].reverse()
        altered.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(GateError, "manifest"):
            PilotLedger(self.path, altered)


if __name__ == "__main__":
    unittest.main()
