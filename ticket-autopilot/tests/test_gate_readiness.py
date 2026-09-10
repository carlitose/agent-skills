from __future__ import annotations

import copy
from pathlib import Path
import tempfile
import unittest

if __package__:
    from . import test_kernel as support
else:
    import test_kernel as support


class GateReadinessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = support.KernelTests()
        self.addCleanup(self.fixture.doCleanups)

    def test_environment_blocker_is_not_a_human_decision(self) -> None:
        kernel = self.fixture.make_kernel(
            (support.ticket_text("01"), support.ticket_text("02", mode="HITL"))
        )
        candidate = self.fixture.candidate()
        kernel.activate("01", candidate)
        kernel.record_stage(
            "01", "implement", "gated", candidate, reason="Build dependency unavailable."
        )

        report = kernel.report()
        self.assertEqual("environment-gated", report["tickets"]["01"]["readiness"])
        self.assertEqual("human-gated", report["tickets"]["02"]["readiness"])
        self.assertEqual(2, len(report["open_gates"]))
        self.assertEqual("gated", report["tickets"]["01"]["state"])

    def test_human_gate_query_does_not_include_environment_blockers(self) -> None:
        kernel = self.fixture.make_kernel(
            (support.ticket_text("01"), support.ticket_text("02", mode="HITL"))
        )
        human_gates = kernel.human_gated_ids()
        self.assertEqual(1, len(human_gates))
        candidate = self.fixture.candidate()
        kernel.activate("01", candidate)
        kernel.record_stage(
            "01", "implement", "gated", candidate, reason="Compiler unavailable."
        )

        self.assertEqual(human_gates, kernel.human_gated_ids())
        self.assertEqual(2, len(kernel.report()["open_gates"]))

    def test_persisted_categories_control_classification_not_reason_text(self) -> None:
        cases = (
            (("environment",), "environment-gated"),
            (("human",), "human-gated"),
            (("environment", "human"), "human-gated"),
            (("human", "environment"), "human-gated"),
            (("environment", "credentials"), "gated"),
            (("provider-merge",), "gated"),
            (("future-category",), "gated"),
        )
        for categories, expected in cases:
            with self.subTest(categories=categories):
                kernel = self.fixture.make_kernel((support.ticket_text("01"),))
                gate_ids = [
                    kernel.open_gate(
                        "01", category, scope="ticket", reason="Human approval required."
                    )
                    for category in categories
                ]
                before = copy.deepcopy(kernel.ledger)

                report = kernel.report()
                self.assertEqual(expected, report["tickets"]["01"]["readiness"])
                self.assertEqual(gate_ids, report["open_gates"])
                self.assertEqual(gate_ids, kernel.open_gate_ids())
                self.assertEqual(
                    gate_ids,
                    [gate["gate_id"] for gate in report["open_gate_records"]["records"]],
                )
                self.assertEqual(before, kernel.ledger)

    def test_run_gate_applies_without_releasing_other_ready_work(self) -> None:
        for category, expected in (
            ("human", "human-gated"),
            ("credentials", "gated"),
            ("environment", "environment-gated"),
        ):
            with self.subTest(category=category):
                kernel = self.fixture.make_kernel(
                    (support.ticket_text("01"), support.ticket_text("02"))
                )
                ticket_gate = kernel.open_gate(
                    "01", "environment", scope="ticket", reason="Dependency unavailable."
                )
                run_gate = kernel.open_gate(
                    None, category, scope="run", reason="Run prerequisite remains open."
                )

                report = kernel.report()
                self.assertEqual(expected, report["tickets"]["01"]["readiness"])
                self.assertEqual([ticket_gate, run_gate], report["open_gates"])
                self.assertEqual([], kernel.ready_ids())
                self.assertEqual("waiting", report["run_state"])

    def test_legacy_gate_readback_is_pure_and_keeps_unrelated_frontier(self) -> None:
        kernel = self.fixture.make_kernel(
            (support.ticket_text("01"), support.ticket_text("02"))
        )
        candidate = self.fixture.candidate()
        kernel.activate("01", candidate)
        kernel.record_stage(
            "01", "implement", "gated", candidate, reason="implement reported a gate"
        )
        with tempfile.TemporaryDirectory() as directory:
            store = support.AtomicLedger(Path(directory) / "ledger.json")
            store.save(kernel.ledger)
            original_bytes = store.path.read_bytes()
            restored = support.Kernel(store.load())
            original = copy.deepcopy(restored.ledger)
            first = restored.report()
            expected_ids = list(first["open_gates"])
            first["open_gates"].clear()
            first["open_gate_records"]["records"][0]["reason"] = "invented recovery"

            second = restored.report()
            self.assertEqual(expected_ids, second["open_gates"])
            self.assertEqual(
                "implement reported a gate",
                second["open_gate_records"]["records"][0]["reason"],
            )
            self.assertEqual("environment-gated", second["tickets"]["01"]["readiness"])
            self.assertEqual(["02"], second["ready"])
            self.assertEqual(original, restored.ledger)
            self.assertEqual(original_bytes, store.path.read_bytes())

    def test_existing_resolution_reenters_stage_without_a_quality_pass(self) -> None:
        kernel = self.fixture.make_kernel(
            (support.ticket_text("01", mode="HITL"), support.ticket_text("02", mode="HITL"))
        )
        start_gate, unrelated_gate = kernel.human_gated_ids()
        authority = {
            "actor": "fixture-human",
            "evidence": "decision://fixture/continue-ticket-01",
        }
        kernel.approve_gate(start_gate, **authority)
        candidate = self.fixture.candidate()
        kernel.activate("01", candidate)
        kernel.record_stage(
            "01", "implement", "gated", candidate, reason="Dependency unavailable."
        )
        before = kernel.report()
        self.assertEqual("environment-gated", before["tickets"]["01"]["readiness"])
        self.assertEqual([unrelated_gate], kernel.human_gated_ids())
        technical_gate = next(
            gate["gate_id"]
            for gate in before["open_gate_records"]["records"]
            if gate["ticket_id"] == "01"
        )

        # Synthetic prior authority proves API mechanics, not live scope validation.
        kernel.approve_gate(technical_gate, **authority)
        after = kernel.report()
        self.assertEqual("active", after["tickets"]["01"]["state"])
        self.assertEqual("implement", after["tickets"]["01"]["stage"])
        self.assertEqual([], after["tickets"]["01"]["validated_stages"])
        self.assertEqual(
            before["tickets"]["01"]["candidate_ref"],
            after["tickets"]["01"]["candidate_ref"],
        )
        self.assertEqual([unrelated_gate], after["open_gates"])
        self.assertEqual("human-gated", after["tickets"]["02"]["readiness"])


if __name__ == "__main__":
    unittest.main()
