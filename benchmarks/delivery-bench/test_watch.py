"""The live viewer reads a lot and its sessions and never writes (DBH-22)."""
from __future__ import annotations

import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import watch

CELL = "lua-vm.bare.r1"
OTHER = "lua-vm.pi-full.r1"


def assistant(parts: list, cost: float = 0.0, **extra) -> dict:
    return {"type": "message", "message": {"role": "assistant", "content": parts,
                                           "usage": {"cost": {"total": cost}}, **extra}}


SESSION = [
    {"type": "session", "id": "s1", "cwd": "/arm/project"},
    {"type": "message", "message": {"role": "user", "content": [{"type": "text", "text": "Lee TASK.md"}]}},
    assistant([{"type": "thinking", "thinking": "secret plan"},
               {"type": "toolCall", "name": "bash", "arguments": {"command": "python dev.py test"}}], 0.0125),
    {"type": "message", "message": {"role": "toolResult", "toolName": "bash",
                                    "content": [{"type": "text", "text": "12 passed"}]}},
    {"type": "message", "message": {"role": "toolResult", "toolName": "edit", "isError": True,
                                    "content": [{"type": "text", "text": "no match"}]}},
    assistant([{"type": "text", "text": "Done."}], 0.5, stopReason="error", errorMessage="rate limited"),
]


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        digest.update(str(path.relative_to(root)).encode())
        if path.is_file():
            digest.update(path.read_bytes())
    return digest.hexdigest()


def write_lines(path: Path, events: list, mode: str = "w") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, mode, encoding="utf-8", newline="\n") as handle:
        for event in events:
            handle.write(json.dumps(event) + "\n")


class LotFixture(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(self.tmp, ignore_errors=True))
        self.lot_dir = self.tmp / "lot"
        authority = self.tmp / "authority.json"
        authority.write_text(json.dumps({"schema": 1, "caps": {"usd": 50}}), encoding="utf-8")
        cells = {}
        for name in (CELL, OTHER):
            scenario, arm, rep = name.split(".")
            cells[name] = {"scenario": scenario, "arm": arm, "rep": int(rep[1:]),
                           "arm_dir": str(self.tmp / "runs" / arm)}
        self.lot = {"lot": "dbh-luna3", "provider": "openai-codex", "model": "gpt-6-luna",
                    "thinking": "medium", "authority": {"path": str(authority), "sha256": "a1"},
                    "cells": cells}
        self.lot_dir.mkdir()
        (self.lot_dir / "lot.json").write_text(json.dumps(self.lot), encoding="utf-8")
        self.session = Path(cells[CELL]["arm_dir"]) / "sessions" / "2026-10-05T10-00-00Z_s1.jsonl"


class CellTest(LotFixture):
    def test_renders_message_tool_call_result_error_and_cost_in_order(self):
        write_lines(self.session, SESSION)
        out = io.StringIO()
        total = watch.follow_cell(self.lot_dir, CELL, once=True, width=80, color=False, out=out)
        text = out.getvalue()
        order = ["── session s1", "▶ USER Lee TASK.md", "→ bash python dev.py test",
                 "$ 0.0125 · Σ cell $ 0.0125", "← bash: 12 passed", "✖ edit: no match", "• Done.",
                 "✖ ERROR rate limited", "$ 0.5000 · Σ cell $ 0.5125"]
        positions = [text.index(item) for item in order]
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn("secret plan", text)
        self.assertAlmostEqual(total, 0.5125)

    def test_lines_appended_later_appear_and_a_partial_line_waits(self):
        write_lines(self.session, SESSION[:2])
        sessions = watch.Sessions(self.session.parent.parent)
        self.assertEqual(len(sessions.read()[0][1]), 2)
        with open(self.session, "a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(SESSION[2]) + "\n" + json.dumps(SESSION[3])[:20])
        self.assertEqual([e["type"] for e in sessions.read()[0][1]], ["message"])
        with open(self.session, "a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(SESSION[3])[20:] + "\n")
        self.assertEqual(sessions.read()[0][1][0]["message"]["role"], "toolResult")

    def test_a_restored_session_is_replayed_from_the_start(self):
        write_lines(self.session, SESSION)
        tail = watch.Tail(self.session)
        self.assertEqual(len(tail.read()), len(SESSION))
        write_lines(self.session, SESSION[:1])
        self.assertEqual(len(tail.read()), 1)
        self.assertTrue(tail.reset)

    def test_restoring_one_file_keeps_the_spend_of_the_others(self):
        arm = Path(self.lot["cells"][CELL]["arm_dir"])
        leaf = arm / "project" / ".git" / "ticket-driver" / "runs" / "leaf.jsonl"
        write_lines(self.session, [assistant([], 1.0), assistant([], 2.0)])
        write_lines(leaf, [assistant([], 4.0)])
        live = watch.LiveSpend(self.lot)
        self.assertEqual(live.read()[CELL], 7.0)
        write_lines(self.session, [assistant([], 1.0)])  # the snapshot had only the first turn
        self.assertEqual(live.read()[CELL], 5.0)

    def test_thinking_is_shown_only_on_request(self):
        event = SESSION[2]
        self.assertFalse(any("secret plan" in line for line in watch.render(event)))
        self.assertTrue(any(line.startswith("\u2234 secret plan") for line in watch.render(event, thinking=True)))

    def test_long_arguments_are_shortened(self):
        line = watch.render(assistant([{"type": "toolCall", "name": "write",
                                        "arguments": {"path": "a", "content": "x" * 500}}]), width=40)[0]
        self.assertLessEqual(len(line), 40 + len("→ write "))
        self.assertTrue(line.endswith("…"))

    def test_compaction_counts_as_spend_like_the_runner(self):
        event = {"type": "compaction", "tokensBefore": 200000, "usage": {"cost": {"total": 0.3}}}
        self.assertEqual(watch.event_cost(event), 0.3)
        self.assertIn("compaction", watch.render(event)[0])
        self.assertEqual(watch.event_cost({"type": "usage", "usage": {"cost": {"total": 9}}}), 0.0)

    def test_unknown_cell_is_refused(self):
        with self.assertRaises(SystemExit):
            watch.follow_cell(self.lot_dir, "nope", once=True, width=80, color=False, out=io.StringIO())


class LotTest(LotFixture):
    def write_ledger(self):
        write_lines(self.lot_dir / "ledger.jsonl", [
            {"event": "launch", "cell": CELL, "through": 4},
            {"event": "launch", "cell": OTHER, "through": 4},
            {"event": "attempt", "cell": CELL, "request": 1, "cost_usd": 0.25},
            {"event": "judged", "cell": CELL, "request": 1, "accepted": True},
            {"event": "attempt", "cell": OTHER, "request": 1, "cost_usd": 1.5},
            {"event": "cell", "cell": OTHER, "length": 1, "error": None},
        ])
        cell_dir = self.lot_dir / "cells" / CELL
        cell_dir.mkdir(parents=True)
        (cell_dir / "cell.json").write_text(json.dumps({"requests": [
            {"request": 1, "status": "judged", "axes": {"acceptance": {"accepted": True}}}]}), encoding="utf-8")

    def test_state_reads_cells_ledger_and_cap(self):
        self.write_ledger()
        state = watch.lot_state(self.lot_dir)
        rows = {row["cell"]: row for row in state["rows"]}
        self.assertEqual(state["cap_usd"], 50)
        self.assertEqual(state["spend_usd"], 1.75)
        self.assertEqual(state["running"], [CELL])
        self.assertEqual((rows[CELL]["judged"], rows[CELL]["accepted"], rows[CELL]["request"]), (1, 1, 2))
        self.assertEqual(rows[OTHER]["state"], "stopped")

    def test_table_shows_spend_against_the_cap(self):
        self.write_ledger()
        write_lines(self.session, SESSION)
        out = io.StringIO()
        watch.watch_lot(self.lot_dir, once=True, every=0, color=False, out=out)
        text = out.getvalue()
        self.assertIn(CELL, text)
        self.assertIn("1.75 $ closed attempts", text)
        self.assertIn("1.75 $ at least = 3.5% of the 50 $ cap", text)

    def test_live_spend_includes_the_driver_leaves_and_counts_against_the_cap(self):
        arm = Path(self.lot["cells"][OTHER]["arm_dir"])
        write_lines(arm / "project" / ".git" / "ticket-driver" / "runs" / "r1" / "leaf.jsonl",
                    [assistant([{"type": "text", "text": "leaf"}], 40.0)])
        live = watch.LiveSpend(self.lot).read()
        self.assertEqual(live[OTHER], 40.0)
        line = watch.render_lot(watch.lot_state(self.lot_dir), live=live)[-1]
        self.assertIn("40.00 $ at least = 80.0% of the 50 $ cap", line)

    def test_an_amendment_citing_the_bound_authority_raises_the_cap(self):
        def amend(n, lot, sha, usd):
            (self.tmp / f"authority-amendment-{n}.json").write_text(json.dumps(
                {"lot": lot, "amends": {"sha256": sha}, "caps": {"usd": usd}}), encoding="utf-8")
        amend(1, "dbh-luna3", "a1", 80)
        amend(2, "dbh-luna3", "other", 900)
        amend(3, "another-lot", "a1", 900)
        state = watch.lot_state(self.lot_dir)
        self.assertEqual((state["cap_usd"], state["cap_source"]), (80, "authority-amendment-1.json"))

    def test_a_lot_that_has_not_started_has_no_running_cells(self):
        state = watch.lot_state(self.lot_dir)
        self.assertEqual(state["running"], [])
        self.assertEqual(state["spend_usd"], 0)


class OpenTest(LotFixture):
    def test_argv_has_the_lot_table_and_one_tab_per_cell(self):
        argv = watch.open_argv(self.lot_dir, [CELL, OTHER], python="py")
        self.assertEqual(argv[:4], ["wt.exe", "-w", "dbh-dbh-luna3", "new-tab"])
        self.assertEqual(argv.count("new-tab"), 3)
        self.assertEqual(argv.count(";"), 2)
        self.assertIn("lot", argv)
        self.assertEqual([argv[i + 1] for i, a in enumerate(argv) if a == "--cell"], [CELL, OTHER])

    def test_without_windows_terminal_it_prints_the_commands(self):
        out = io.StringIO()
        with mock.patch.object(watch, "windows_terminal", return_value=None), \
                mock.patch("subprocess.Popen") as popen:
            watch.open_tabs(self.lot_dir, all_cells=True, rep=1, print_only=False, out=out)
        popen.assert_not_called()
        lines = out.getvalue().splitlines()
        self.assertEqual(len(lines), 3)
        self.assertIn("--cell", lines[1])

    def test_with_windows_terminal_it_launches_one_window(self):
        with mock.patch.object(watch, "windows_terminal", return_value="C:/wt.exe"), \
                mock.patch("subprocess.Popen") as popen:
            argv = watch.open_tabs(self.lot_dir, all_cells=True, rep=None, print_only=False, out=io.StringIO())
        popen.assert_called_once()
        self.assertEqual(popen.call_args.args[0][0], "C:/wt.exe")
        self.assertEqual(popen.call_args.args[0][1:], argv[1:])


class ReadOnlyTest(LotFixture):
    def test_no_command_writes_into_the_lot_or_the_sessions(self):
        LotTest.write_ledger(self)
        write_lines(self.session, SESSION)
        before = tree_digest(self.tmp)
        out = io.StringIO()
        watch.follow_cell(self.lot_dir, CELL, once=True, width=80, color=False, out=out)
        watch.watch_lot(self.lot_dir, once=True, every=0, color=False, out=out)
        with mock.patch.object(watch, "windows_terminal", return_value=None):
            watch.open_tabs(self.lot_dir, all_cells=True, rep=None, print_only=True, out=out)
        with mock.patch("sys.stdout", io.StringIO()):
            self.assertEqual(watch.main(["lot", "--lot", str(self.lot_dir), "--once", "--no-color"]), 0)
            self.assertEqual(watch.main(["cell", "--lot", str(self.lot_dir), "--cell", CELL, "--once"]), 0)
        self.assertEqual(tree_digest(self.tmp), before)


if __name__ == "__main__":
    unittest.main()
