import hashlib
import tempfile
import unittest
from pathlib import Path

from harbor.models.trial.result import TrialResult
from pilot_ledger import GateError
from standard_receipt import attributable_result


class StandardReceiptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.task_dir = Path(self.temp.name) / "html-js-filter"
        self.ledger = Path(self.temp.name) / "ledger.jsonl"
        self.instruction = "synthetic public task instruction"
        self.binding = {"tasks": [{"name": self.task_dir.name,
            "harbor_instruction_sha256": hashlib.sha256(self.instruction.encode()).hexdigest()}]}
        self.trial = {
            "task_name": "terminal-bench/html-js-filter", "trial_name": "offline-fixture",
            "trial_uri": "file:///synthetic", "task_id": {"path": str(self.task_dir)},
            "task_checksum": "fixture-checksum",
            "config": {"task": {"path": str(self.task_dir)}, "agent": {
                "import_path": "harbor_pi_agent:StandardPiHarborAgent",
                "model_name": "openai-codex/gpt-6-sol", "skills": [],
                "kwargs": {"task_name": "html-js-filter", "ledger_path": str(self.ledger)}}},
            "agent_info": {"name": "pi-harbor-standard", "version": "0.2.0-standard",
                           "model_info": {"provider": "openai-codex", "name": "gpt-6-sol"}},
            "agent_result": {"n_input_tokens": 8, "n_output_tokens": 4, "cost_usd": 0.01,
                "metadata": {"method": "original-harbor-pi-bare", "task_name": "html-js-filter",
                             "offline_probe": False}},
            "verifier_result": {"rewards": {"reward": 1}},
            "verifier_environment_mode": "separate",
            "agent_execution": {"started_at": "2026-09-24T10:00:00Z",
                                "finished_at": "2026-09-24T10:00:20Z"},
        }
        self.trajectory = {"method": "standard", "arm": "pi-bare",
            "task_name": "html-js-filter", "instruction": self.instruction,
            "usage": {"input_tokens": 8, "output_tokens": 4, "cost_usd": 0.01},
            "budget": {"ambiguous": False, "limitUsd": "60", "maxRequests": 16,
                       "requests": 1, "pendingRequests": 0, "maxPerRequestUsd": 8.2,
                       "reservedUsd": 0.01, "observedUsd": 0.01}}

    def parse(self):
        return attributable_result(TrialResult.model_validate(self.trial), self.trajectory,
            name="html-js-filter", task_dir=self.task_dir, ledger_path=self.ledger,
            binding=self.binding, original_checksum="fixture-checksum")

    def test_completed_original_trial_binds_verifier_cost_and_duration(self):
        metrics = self.parse()
        self.assertEqual(metrics["elapsed_seconds"], "20.0")
        self.assertTrue(metrics["verifier_pass"])
        self.assertEqual(metrics["cost_usd"], "0.01")
        self.trial["verifier_result"]["rewards"]["reward"] = 0
        self.assertFalse(self.parse()["verifier_pass"])

    def test_missing_verifier_and_ambiguous_cost_stop_settlement(self):
        self.trial["verifier_result"] = None
        with self.assertRaisesRegex(GateError, "verifier"):
            self.parse()
        self.trial["verifier_result"] = {"rewards": {"reward": 1}}
        self.trajectory["budget"]["ambiguous"] = True
        with self.assertRaisesRegex(GateError, "receipt"):
            self.parse()
        self.trajectory["budget"]["ambiguous"] = False
        self.trajectory["budget"]["pendingRequests"] = 1
        with self.assertRaisesRegex(GateError, "receipt"):
            self.parse()

    def test_task_image_method_and_trial_override_cannot_be_mixed(self):
        self.trial["config"]["agent"]["skills"] = ["other"]
        with self.assertRaisesRegex(GateError, "identity"):
            self.parse()
        self.trial["config"]["agent"]["skills"] = []
        self.trial["config"]["environment"] = {"mounts": [{"type": "bind", "source": "/host", "target": "/app"}]}
        with self.assertRaisesRegex(GateError, "identity"):
            self.parse()
        self.trial["config"]["environment"] = {}
        self.trial["config"]["timeout_multiplier"] = 2
        with self.assertRaisesRegex(GateError, "identity"):
            self.parse()

    def test_wrong_task_cost_or_unsupported_error_cannot_be_attributed(self):
        self.trajectory["task_name"] = "interleaved-vigenere"
        with self.assertRaisesRegex(GateError, "receipt"):
            self.parse()
        self.trajectory["task_name"] = "html-js-filter"
        self.trajectory["usage"]["cost_usd"] = 0
        with self.assertRaisesRegex(GateError, "receipt"):
            self.parse()
        self.trajectory["usage"]["cost_usd"] = 0.01
        self.trajectory["usage"]["output_tokens"] = 0
        self.trial["agent_result"]["n_output_tokens"] = 0
        self.trajectory["usage"]["cost_usd"] = 0
        self.trial["agent_result"]["cost_usd"] = 0
        self.trajectory["budget"]["observedUsd"] = 0
        with self.assertRaisesRegex(GateError, "receipt"):
            self.parse()
        self.trajectory["usage"]["cost_usd"] = 0.01
        self.trial["agent_result"]["cost_usd"] = 0.01
        self.trajectory["budget"]["observedUsd"] = 0.01
        self.trial["exception_info"] = {"exception_type": "RuntimeError", "exception_message": "failed",
            "exception_traceback": "", "occurred_at": "2026-09-24T10:00:21Z"}
        with self.assertRaisesRegex(GateError, "receipt"):
            self.parse()


if __name__ == "__main__":
    unittest.main()
