from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_ROOT.parent
SCRIPTS = SKILL_ROOT / "scripts"
CLI = SCRIPTS / "ticket-autopilot.py"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from autopilot.ticket_contract import parse_ticket_markdown, serialize_ticket_markdown  # noqa: E402
from autopilot.ticket_inventory import inventory_tickets  # noqa: E402


def ticket(ticket_id: str, *, mode: str = "AFK", blockers: list[str] | None = None) -> str:
    return serialize_ticket_markdown(
        {
            "ticket_schema": 1,
            "ticket_id": ticket_id,
            "execution_mode": mode,
            "blocked_by": blockers or [],
        },
        f"# Ticket {ticket_id}\n",
    )


class TicketInventoryTests(unittest.TestCase):
    def test_dependency_disposition_causes_are_order_independent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            folder = root / "series"
            hold = folder / "hold"
            hold.mkdir(parents=True)
            (folder / "00-descendant.md").write_text(
                ticket("03", blockers=["02"]), encoding="utf-8"
            )
            (folder / "01-middle.md").write_text(
                ticket("02", blockers=["01"]), encoding="utf-8"
            )
            (hold / "99-root.md").write_text(ticket("01"), encoding="utf-8")

            result = inventory_tickets(root)

        by_id = {item["id"]: item for item in result["tickets"]}
        cause = [{"ticket_id": "01", "reason": "dependency-on-hold"}]
        self.assertEqual(cause, by_id["02"]["readiness_causes"])
        self.assertEqual(cause, by_id["03"]["readiness_causes"])

    def test_dispositions_and_dependency_causes_are_orthogonal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            folder = root / "series"
            hold = folder / "hold"
            canceled = folder / "canceled"
            hold.mkdir(parents=True)
            canceled.mkdir()
            (hold / "01-held.md").write_text(ticket("01"), encoding="utf-8")
            (folder / "02-descendant.md").write_text(
                ticket("02", blockers=["01"]), encoding="utf-8"
            )
            (folder / "03-transitive.md").write_text(
                ticket("03", blockers=["02"]), encoding="utf-8"
            )
            (canceled / "04-canceled.md").write_text(
                ticket("04"), encoding="utf-8"
            )
            (folder / "05-canceled-dependent.md").write_text(
                ticket("05", blockers=["04"]), encoding="utf-8"
            )

            result = inventory_tickets(root)

        self.assertEqual(2, result["schema"])
        by_id = {item["id"]: item for item in result["tickets"]}
        self.assertEqual("on-hold", by_id["01"]["disposition"])
        self.assertEqual("canceled", by_id["04"]["disposition"])
        self.assertEqual("unknown", by_id["01"]["lifecycle"])
        self.assertIsNone(by_id["01"]["stop_reason"])
        self.assertEqual("not-schedulable", by_id["01"]["readiness"])
        self.assertEqual(
            [{"ticket_id": "01", "reason": "dependency-on-hold"}],
            by_id["02"]["readiness_causes"],
        )
        self.assertEqual(
            by_id["02"]["readiness_causes"],
            by_id["03"]["readiness_causes"],
        )
        self.assertEqual(
            [{"ticket_id": "04", "reason": "dependency-canceled"}],
            by_id["05"]["readiness_causes"],
        )
        self.assertEqual("open", by_id["05"]["disposition"])

    def test_empty_root_is_a_valid_empty_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = inventory_tickets(Path(temporary))

        self.assertEqual([], result["tickets"])
        self.assertEqual([], result["diagnostics"])

    def test_completed_only_folder_is_valid_inventory_input(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            completed = root / "release" / "done"
            completed.mkdir(parents=True)
            path = completed / "01-finished.md"
            path.write_text(ticket("01"), encoding="utf-8")

            result = inventory_tickets(root)

        self.assertEqual(2, result["schema"])
        self.assertEqual([], result["diagnostics"])
        self.assertEqual(
            [
                {
                    "folder": "release",
                    "id": "01",
                    "title": "Ticket 01",
                    "path": "release/done/01-finished.md",
                    "disposition": "completed",
                    "lifecycle": "completed",
                    "attempt_outcome": None,
                    "mode": "AFK",
                    "blockers": [],
                    "readiness": "completed",
                    "readiness_causes": [],
                    "stop_reason": None,
                }
            ],
            result["tickets"],
        )

    def test_duplicate_ids_are_reported_without_hiding_valid_envelopes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            folder = root / "series"
            folder.mkdir()
            (folder / "01-first.md").write_text(ticket("01"), encoding="utf-8")
            (folder / "01-second.md").write_text(ticket("01"), encoding="utf-8")

            result = inventory_tickets(root)

        self.assertEqual(2, len(result["tickets"]))
        self.assertEqual(
            ["duplicate-id"],
            [diagnostic["code"] for diagnostic in result["diagnostics"]],
        )
        self.assertEqual(
            ["unknown", "unknown"],
            [item["readiness"] for item in result["tickets"]],
        )

    def test_missing_dependencies_are_explicit_and_make_readiness_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            folder = root / "series"
            folder.mkdir()
            (folder / "02-dependent.md").write_text(
                ticket("02", blockers=["01"]), encoding="utf-8"
            )

            result = inventory_tickets(root)

        self.assertEqual("unknown", result["tickets"][0]["readiness"])
        self.assertEqual("missing-dependency", result["diagnostics"][0]["code"])
        self.assertEqual("01", result["diagnostics"][0]["dependency_id"])

    def test_unknown_readiness_propagates_transitively_independent_of_file_order(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            folder = root / "series"
            folder.mkdir()
            (folder / "01-first.md").write_text(
                ticket("01", blockers=["02"]), encoding="utf-8"
            )
            (folder / "02-second.md").write_text(
                ticket("02", blockers=["03"]), encoding="utf-8"
            )
            (folder / "03-third.md").write_text(
                ticket("03", blockers=["missing"]), encoding="utf-8"
            )

            result = inventory_tickets(root)

        self.assertEqual(
            {"01": "unknown", "02": "unknown", "03": "unknown"},
            {item["id"]: item["readiness"] for item in result["tickets"]},
        )

    def test_dependency_cycles_are_diagnostic_instead_of_fatal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            folder = root / "series"
            folder.mkdir()
            (folder / "01-one.md").write_text(
                ticket("01", blockers=["02"]), encoding="utf-8"
            )
            (folder / "02-two.md").write_text(
                ticket("02", blockers=["01"]), encoding="utf-8"
            )

            result = inventory_tickets(root)

        self.assertEqual(["cycle"], [item["code"] for item in result["diagnostics"]])
        self.assertEqual(
            ["unknown", "unknown"],
            [item["readiness"] for item in result["tickets"]],
        )
        self.assertEqual(["01", "02", "01"], result["diagnostics"][0]["cycle"])

    def test_readiness_is_derived_from_disposition_dependencies_and_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            folder = root / "series"
            completed = folder / "done"
            completed.mkdir(parents=True)
            (completed / "01-base.md").write_text(ticket("01"), encoding="utf-8")
            (folder / "02-ready.md").write_text(
                ticket("02", blockers=["01"]), encoding="utf-8"
            )
            (folder / "03-human.md").write_text(
                ticket("03", mode="HITL", blockers=["01"]), encoding="utf-8"
            )
            (folder / "04-blocked.md").write_text(
                ticket("04", blockers=["02"]), encoding="utf-8"
            )

            result = inventory_tickets(root)

        self.assertEqual(
            {
                "01": "completed",
                "02": "ready",
                "03": "human-gated",
                "04": "blocked",
            },
            {item["id"]: item["readiness"] for item in result["tickets"]},
        )

    def test_malformed_ticket_is_reported_alongside_valid_items(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            folder = root / "series"
            folder.mkdir()
            (folder / "01-valid.md").write_text(ticket("01"), encoding="utf-8")
            (folder / "02-malformed.md").write_text("# Legacy\n", encoding="utf-8")

            result = inventory_tickets(root)

        self.assertEqual(["01"], [item["id"] for item in result["tickets"]])
        self.assertEqual("malformed-ticket", result["diagnostics"][0]["code"])
        self.assertEqual("series/02-malformed.md", result["diagnostics"][0]["path"])

    def test_invalid_utf8_is_diagnostic_and_does_not_hide_valid_ticket(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            folder = root / "series"
            folder.mkdir()
            (folder / "01-valid.md").write_text(ticket("01"), encoding="utf-8")
            (folder / "02-invalid.md").write_bytes(b"\xff\xfe\n")

            result = inventory_tickets(root)

        self.assertEqual(["01"], [item["id"] for item in result["tickets"]])
        self.assertEqual("malformed-ticket", result["diagnostics"][0]["code"])
        self.assertEqual("series/02-invalid.md", result["diagnostics"][0]["path"])

    def test_ticket_list_json_is_provider_free_and_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            folder = root / "series"
            folder.mkdir()
            path = folder / "01-open.md"
            path.write_text(ticket("01"), encoding="utf-8")
            before = path.read_bytes()

            completed = subprocess.run(
                [sys.executable, "-B", str(CLI), "ticket-list", str(root), "--json"],
                text=True,
                capture_output=True,
                check=False,
            )

            after = path.read_bytes()
        self.assertEqual(0, completed.returncode, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual("ticket-list", payload["command"])
        self.assertEqual(2, payload["data"]["schema"])
        self.assertEqual(["01"], [item["id"] for item in payload["data"]["tickets"]])
        self.assertEqual(before, after)

    def test_ticket_list_filters_by_disposition_or_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            folder = root / "series"
            done = folder / "done"
            done.mkdir(parents=True)
            (done / "01-done.md").write_text(ticket("01"), encoding="utf-8")
            (folder / "02-ready.md").write_text(
                ticket("02", blockers=["01"]), encoding="utf-8"
            )
            (folder / "03-blocked.md").write_text(
                ticket("03", blockers=["02"]), encoding="utf-8"
            )

            ready = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(CLI),
                    "ticket-list",
                    str(root),
                    "--state",
                    "ready",
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(0, ready.returncode, ready.stderr)
        payload = json.loads(ready.stdout)
        self.assertEqual(["02"], [item["id"] for item in payload["data"]["tickets"]])

    def test_ticket_list_default_view_is_stable_human_text(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            folder = root / "series"
            folder.mkdir()
            (folder / "01-open.md").write_text(ticket("01"), encoding="utf-8")

            completed = subprocess.run(
                [sys.executable, "-B", str(CLI), "ticket-list", str(root)],
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn(
            "FOLDER\tID\tDISPOSITION\tLIFECYCLE\tATTEMPT_OUTCOME\tMODE\tREADINESS\tCAUSES\tSTOP_REASON\tBLOCKERS\tPATH\tTITLE",
            completed.stdout,
        )
        self.assertIn(
            "series\t01\topen\tunknown\t-\tAFK\tready\t-\t-\t-\tseries/01-open.md\tTicket 01",
            completed.stdout,
        )
        self.assertNotIn('"ok":', completed.stdout)

    def test_repository_inventory_tracks_current_open_ticket_folder(self) -> None:
        folder = REPO_ROOT / "docs" / "tickets" / "bounded-ticket-autopilot-leaves"
        result = inventory_tickets(folder, state="open")
        expected = [
            parse_ticket_markdown(path.read_text(encoding="utf-8")).envelope["ticket_id"]
            for path in sorted(folder.glob("*.md"))
        ]

        self.assertEqual(
            expected,
            [item["id"] for item in result["tickets"]],
        )


if __name__ == "__main__":
    unittest.main()
