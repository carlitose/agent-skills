"""Offline tests for the simulated user of a vague-request lot (DBH-38).

    python -B -m unittest test_simulator
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import simulator


class AskTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="dbench-sim-")
        self.root = Path(self.tmp.name)
        (self.root / "01.md").write_text("# Encargo\n\nEl error dice `frozen table`.\n", encoding="utf-8")
        (self.root / "02.md").write_text("# Encargo\n\nAhora descongelar.\n", encoding="utf-8")
        self.calls = []
        self.answer = "El error dice `frozen table`."
        self.waits = []
        patcher = mock.patch.object(simulator, "pause", self.waits.append)
        patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        self.tmp.cleanup()

    def model(self, config, text):
        self.calls.append(text)
        if isinstance(self.answer, Exception):
            raise self.answer
        return {"answer": self.answer, "usage": {"totalTokens": 30, "cost_usd": 0.004}, "session": "s"}

    def config(self, log="a.jsonl", **extra) -> dict:
        return {"brief": [str(self.root / "01.md"), str(self.root / "02.md")],
                "cache": str(self.root / "cache" / "toy-02.json"), "log": str(self.root / log),
                "limit": 10, "forbidden": ["secret_checks.lua", "dbench-canary-toy"], **extra}

    def test_the_same_question_gets_the_same_answer_in_every_arm_without_a_new_call(self):
        first = simulator.ask(self.config("pi-tools.jsonl"), "¿Qué dice el error?", model=self.model)
        again = simulator.ask(self.config("pi-full.jsonl"), "  ¿qué   DICE el error? ", model=self.model)
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(first["answer"], again["answer"])
        self.assertEqual((first["cached"], again["cached"]), (False, True))
        self.assertEqual((first["cost_usd"], again["cost_usd"]), (0.004, 0.0))
        other = simulator.ask(self.config("pi-full.jsonl"), "¿Y si no es una tabla?", model=self.model)
        self.assertFalse(other["cached"])
        self.assertEqual(len(self.calls), 2)

    def test_the_brief_is_the_chain_and_the_question_and_nothing_else(self):
        simulator.ask(self.config(), "¿Qué dice el error?", model=self.model)
        text = self.calls[0]
        self.assertIn("## Encargo anterior 1", text)
        self.assertIn("## Encargo actual", text)
        self.assertTrue(text.endswith("¿Qué dice el error?"))
        self.assertIn("frozen table", text)
        for word in ("pi-tools", "pi-full", "bare-goal", "arm", "brazo"):
            self.assertNotIn(word, text)
        self.assertIn("respondes igual a cualquiera", simulator.SYSTEM)

    def test_past_the_limit_the_tool_answers_without_calling_the_model(self):
        config = self.config(limit=2)
        for question in ("a?", "b?"):
            simulator.ask(config, question, model=self.model)
        third = simulator.ask(config, "c?", model=self.model)
        self.assertEqual(len(self.calls), 2)
        self.assertTrue(third["limited"])
        self.assertEqual(third["answer"], simulator.LIMIT_TEXT)
        self.assertEqual(simulator.summarize_log(Path(config["log"]))["limited"], 1)

    def test_an_answer_that_names_a_hidden_test_or_the_canary_is_replaced_and_recorded(self):
        self.answer = "Lo comprueba Secret_Checks.lua, mira dbench-canary-toy."
        entry = simulator.ask(self.config(), "¿Cómo lo probáis?", model=self.model)
        self.assertEqual(entry["answer"], simulator.UNKNOWN)
        self.assertEqual(entry["rejected"], ["dbench-canary-toy", "secret_checks.lua"])
        self.assertIn("Secret_Checks", entry["rejected_answer"])
        cached = simulator.ask(self.config("b.jsonl"), "¿Cómo lo probáis?", model=self.model)
        self.assertEqual((cached["answer"], cached["cached"]), (simulator.UNKNOWN, True))
        self.assertEqual(simulator.summarize_log(Path(self.root / "a.jsonl"))["rejected"], 1)

    def test_a_provider_that_keeps_failing_is_retried_then_reported(self):
        self.answer = simulator.SimulatorError("exit 1: 503")
        with self.assertRaises(simulator.SimulatorError):
            simulator.ask(self.config(), "¿Qué dice el error?", model=self.model)
        self.assertEqual(self.waits, list(simulator.RETRY_SECONDS))
        self.assertEqual(len(self.calls), 4)
        summary = simulator.summarize_log(Path(self.root / "a.jsonl"))
        self.assertEqual((summary["questions"], summary["errors"]), (1, 1))
        self.assertFalse((self.root / "cache" / "toy-02.json").exists())  # nothing cached

    def test_the_log_summary_keeps_the_simulator_cost_apart(self):
        simulator.ask(self.config(), "a?", model=self.model)
        simulator.ask(self.config(), "a?", model=self.model)
        summary = simulator.summarize_log(Path(self.root / "a.jsonl"))
        self.assertEqual(summary, {"questions": 2, "cached": 1, "rejected": 0, "limited": 0, "errors": 0,
                                   "cost_usd": 0.004, "total_tokens": 30})
        stored = json.loads((self.root / "cache" / "toy-02.json").read_text(encoding="utf-8"))
        self.assertEqual(list(stored), ["a?"])


if __name__ == "__main__":
    unittest.main()
