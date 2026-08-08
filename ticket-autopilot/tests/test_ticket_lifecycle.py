from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from autopilot.ticket_contract import serialize_ticket_markdown  # noqa: E402
from autopilot.ticket_lifecycle import (  # noqa: E402
    LifecycleError,
    transition_ticket_source,
)


def ticket(ticket_id: str) -> str:
    return serialize_ticket_markdown(
        {
            "ticket_schema": 1,
            "ticket_id": ticket_id,
            "execution_mode": "AFK",
            "blocked_by": [],
        },
        f"# Ticket {ticket_id}\n",
    )


class TicketLifecycleTests(unittest.TestCase):
    def test_hold_is_receipted_atomic_and_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            folder = root / "tickets"
            journal = root / "state"
            folder.mkdir()
            source = folder / "01-work.md"
            source.write_text(ticket("01"), encoding="utf-8")
            digest = hashlib.sha256(source.read_bytes()).hexdigest()

            first = transition_ticket_source(
                folder,
                journal,
                "01",
                "on-hold",
                actor="user:alice",
                reason="waiting for product decision",
                authority_ref="decision:hold-01",
                expected_digest=digest,
            )
            replay = transition_ticket_source(
                folder,
                journal,
                "01",
                "on-hold",
                actor="user:alice",
                reason="waiting for product decision",
                authority_ref="decision:hold-01",
                expected_digest=digest,
            )

            self.assertEqual(first, replay)
            self.assertEqual("applied", first["state"])
            self.assertEqual("open", first["from_disposition"])
            self.assertEqual("on-hold", first["to_disposition"])
            self.assertFalse(source.exists())
            self.assertEqual(
                ticket("01"),
                (folder / "hold" / source.name).read_text(encoding="utf-8"),
            )
            self.assertTrue(
                (journal / f"{first['transition_id']}.json").is_file()
            )

            with self.assertRaisesRegex(LifecycleError, "matching receipt"):
                transition_ticket_source(
                    folder,
                    journal,
                    "01",
                    "on-hold",
                    actor="user:alice",
                    reason="different request",
                    authority_ref="decision:hold-01-other",
                    expected_digest=digest,
                )

    def test_applied_replay_rejects_destination_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            folder = root / "tickets"
            journal = root / "state"
            folder.mkdir()
            source = folder / "01-work.md"
            source.write_text(ticket("01"), encoding="utf-8")
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            transition_ticket_source(
                folder,
                journal,
                "01",
                "canceled",
                actor="user:alice",
                reason="superseded",
                authority_ref="decision:cancel-01",
                expected_digest=digest,
            )
            (folder / "canceled" / source.name).write_text(
                ticket("different"), encoding="utf-8"
            )

            with self.assertRaisesRegex(LifecycleError, "digest|drift"):
                transition_ticket_source(
                    folder,
                    journal,
                    "01",
                    "canceled",
                    actor="user:alice",
                    reason="superseded",
                    authority_ref="decision:cancel-01",
                    expected_digest=digest,
                )

    def test_intent_recovers_after_move_before_applied_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            folder = root / "tickets"
            journal = root / "state"
            folder.mkdir()
            source = folder / "01-work.md"
            source.write_text(ticket("01"), encoding="utf-8")
            digest = hashlib.sha256(source.read_bytes()).hexdigest()

            from autopilot import ticket_lifecycle

            real_move = ticket_lifecycle._move_no_replace

            def move_then_crash(source_path: Path, destination: Path) -> None:
                real_move(source_path, destination)
                raise RuntimeError("simulated process crash")

            with mock.patch.object(
                ticket_lifecycle, "_move_no_replace", side_effect=move_then_crash
            ), self.assertRaisesRegex(RuntimeError, "simulated process crash"):
                transition_ticket_source(
                    folder,
                    journal,
                    "01",
                    "on-hold",
                    actor="user:alice",
                    reason="waiting for product decision",
                    authority_ref="decision:hold-01",
                    expected_digest=digest,
                )

            receipt = transition_ticket_source(
                folder,
                journal,
                "01",
                "on-hold",
                actor="user:alice",
                reason="waiting for product decision",
                authority_ref="decision:hold-01",
                expected_digest=digest,
            )

            self.assertEqual("applied", receipt["state"])
            self.assertFalse(source.exists())
            self.assertTrue((folder / "hold" / source.name).is_file())

    def test_reopen_requires_a_passed_gate_reference(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            folder = root / "tickets"
            journal = root / "state"
            held = folder / "hold"
            held.mkdir(parents=True)
            source = held / "01-work.md"
            source.write_text(ticket("01"), encoding="utf-8")
            digest = hashlib.sha256(source.read_bytes()).hexdigest()

            with self.assertRaisesRegex(LifecycleError, "passed human gate"):
                transition_ticket_source(
                    folder,
                    journal,
                    "01",
                    "open",
                    actor="runner",
                    reason="resume work",
                    authority_ref="decision:reopen-01",
                    expected_digest=digest,
                )

            receipt = transition_ticket_source(
                folder,
                journal,
                "01",
                "open",
                actor="user:alice",
                reason="resume work",
                authority_ref="decision:reopen-01",
                expected_digest=digest,
                authority_gate_id="gate-reopen-01",
            )

            self.assertEqual("on-hold", receipt["from_disposition"])
            self.assertEqual("open", receipt["to_disposition"])
            self.assertEqual("gate-reopen-01", receipt["authority_gate_id"])


if __name__ == "__main__":
    unittest.main()
