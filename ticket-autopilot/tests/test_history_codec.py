from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from autopilot.history_codec import (
    HistoryCodecError,
    apply_snapshot_delta,
    compact_event_history,
    decode_history,
    diff_snapshots,
)
from autopilot.kernel import Kernel
from autopilot.ledger import AtomicLedger, LedgerError
from autopilot.ticket_contract import parse_ticket_folder


def ticket_text(ticket_id: str, *, mode: str = "AFK") -> str:
    return (
        "---\n"
        "ticket_schema: 1\n"
        f'ticket_id: "{ticket_id}"\n'
        f"execution_mode: {mode}\n"
        "blocked_by: []\n"
        "---\n\n"
        f"# Ticket {ticket_id}\n"
    )


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


class SnapshotDeltaTests(unittest.TestCase):
    def assert_round_trip(
        self, before: dict[str, object], after: dict[str, object]
    ) -> dict[str, object]:
        delta = diff_snapshots(before, after)
        self.assertEqual(after, apply_snapshot_delta(before, delta))
        return delta

    def test_dictionary_add_remove_replace_and_escaped_components(self) -> None:
        before = {
            "keep": {"a/b": 1, "~key": "old", "remove": True},
            "replace": "scalar",
        }
        after = {
            "keep": {"a/b": 2, "~key": "old", "": "added"},
            "replace": {"nested": True},
        }

        first = self.assert_round_trip(before, after)
        second = diff_snapshots(copy.deepcopy(before), copy.deepcopy(after))

        self.assertEqual(first, second)
        self.assertIn(["keep", "a/b"], [op["path"] for op in first["operations"]])
        self.assertIn(["keep", ""], [op["path"] for op in first["operations"]])

    def test_lists_append_when_possible_and_replace_otherwise(self) -> None:
        appended = self.assert_round_trip(
            {"items": [1, {"nested": "value"}]},
            {"items": [1, {"nested": "value"}, 3, 4]},
        )
        replaced = self.assert_round_trip(
            {"items": [1, 2, 3]},
            {"items": [1, 9, 3]},
        )

        self.assertEqual("append", appended["operations"][0]["op"])
        self.assertEqual("set", replaced["operations"][0]["op"])

    def test_empty_delta_and_malformed_or_noncanonical_operations(self) -> None:
        snapshot = {"a": {"b": 1}, "items": [1]}
        empty = diff_snapshots(snapshot, copy.deepcopy(snapshot))
        self.assertEqual({"schema": 1, "operations": []}, empty)
        self.assertEqual(snapshot, apply_snapshot_delta(snapshot, empty))

        malformed = (
            {},
            {"schema": 2, "operations": []},
            {"schema": 1, "operations": "nope"},
            {"schema": 1, "operations": [{"op": "remove", "path": []}]},
            {
                "schema": 1,
                "operations": [
                    {"op": "append", "path": ["items"], "values": []}
                ],
            },
            {
                "schema": 1,
                "operations": [
                    {"op": "set", "path": ["a", "b"], "value": 1}
                ],
            },
        )
        for delta in malformed:
            with self.subTest(delta=delta), self.assertRaises(HistoryCodecError):
                apply_snapshot_delta(snapshot, delta)


class CompactHistoryTests(unittest.TestCase):
    def make_kernel(self, folder: Path, count: int = 1) -> Kernel:
        tickets = folder / "tickets"
        tickets.mkdir()
        for index in range(1, count + 1):
            (tickets / f"{index:02d}.md").write_text(
                ticket_text(f"{index:02d}", mode="HITL"), encoding="utf-8"
            )
        return Kernel.new("compact-history", parse_ticket_folder(tickets))

    def test_compaction_preserves_virtual_snapshots_and_original_hash_chain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            kernel = self.make_kernel(Path(tmp), count=3)
            original = decode_history(kernel.ledger["history"])
            compact = compact_event_history(original)

            self.assertIn("snapshot", compact[0])
            self.assertTrue(all("snapshot_delta" in event for event in compact[1:]))
            self.assertEqual(
                [event["hash"] for event in original],
                [event["hash"] for event in compact],
            )
            self.assertEqual(
                [event["previous_hash"] for event in original],
                [event["previous_hash"] for event in compact],
            )
            decoded = decode_history(compact)
            self.assertEqual(
                [event["snapshot"] for event in original],
                [event["snapshot"] for event in decoded],
            )
            self.assertEqual(compact, compact_event_history(compact))

    def test_full_prefix_compact_suffix_loads_but_full_after_delta_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            kernel = self.make_kernel(root, count=3)
            document = copy.deepcopy(kernel.ledger)
            full_history = decode_history(document["history"])
            compact = compact_event_history(full_history)
            compact[1] = copy.deepcopy(full_history[1])
            document["history"] = compact
            path = root / "ledger.json"

            AtomicLedger(path).save(document)
            self.assertEqual(document, AtomicLedger(path).load())

            invalid = copy.deepcopy(document)
            invalid["history"][-1] = copy.deepcopy(full_history[-1])
            with self.assertRaises(LedgerError):
                AtomicLedger._validate(invalid)

    def test_delta_corruption_cannot_be_hidden_by_resigning_the_envelope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            kernel = self.make_kernel(root, count=2)
            document = copy.deepcopy(kernel.ledger)
            document["history"] = compact_event_history(document["history"])
            path = root / "ledger.json"
            AtomicLedger(path).save(document)
            envelope = json.loads(path.read_text(encoding="utf-8"))
            delta_event = envelope["payload"]["history"][-1]
            delta_event["snapshot_delta"]["operations"].append(
                {"op": "set", "path": ["run_state"], "value": "failed"}
            )
            envelope["integrity"] = hashlib.sha256(
                canonical_bytes(envelope["payload"])
            ).hexdigest()
            path.write_bytes(canonical_bytes(envelope) + b"\n")

            with self.assertRaises(LedgerError):
                AtomicLedger(path).load()
            corrupted_bytes = path.read_bytes()
            with self.assertRaises(LedgerError):
                AtomicLedger(path).compact_history()
            self.assertEqual(corrupted_bytes, path.read_bytes())

    def test_explicit_compaction_is_atomic_idempotent_and_materially_smaller(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            kernel = self.make_kernel(root, count=12)
            for index in range(8):
                reason = f"{index}:" + "x" * ((index + 1) * 2_000)
                kernel.pause_run(actor="test", reason=reason)
                kernel.unpause_run(actor="test", reason=f"resume:{index}")
            path = root / "ledger.json"
            store = AtomicLedger(path)
            kernel.ledger["history"] = decode_history(kernel.ledger["history"])
            store.save(kernel.ledger)
            original_hashes = [event["hash"] for event in kernel.ledger["history"]]
            full_size = len(path.read_bytes())
            full_bytes = path.read_bytes()

            compacted = store.compact_history()
            compact_size = len(path.read_bytes())
            compact_bytes = path.read_bytes()

            self.assertLess(compact_size, full_size * 0.5)
            self.assertEqual(
                original_hashes,
                [event["hash"] for event in compacted["history"]],
            )
            self.assertEqual(compacted, store.compact_history())
            self.assertEqual(compact_bytes, path.read_bytes())

            path.write_bytes(full_bytes)
            before_failure = path.read_bytes()
            store = AtomicLedger(path)
            with mock.patch.object(
                store, "_atomic_write", side_effect=OSError("write failed")
            ):
                with self.assertRaises(OSError):
                    store.compact_history()
            self.assertEqual(before_failure, path.read_bytes())


if __name__ == "__main__":
    unittest.main()
