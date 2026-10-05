#!/usr/bin/env python3
"""Watch a delivery-bench lot while it runs, without writing anything (DBH-22).

    watch.py cell --lot DIR --cell CELL [--once] [--width N]   follow one cell's Pi session live
    watch.py lot  --lot DIR [--once] [--every S]               cell table and spend against the cap
    watch.py open --lot DIR [--all] [--rep N] [--print]        one Windows Terminal tab per cell

The viewer only reads `lot.json`, `ledger.jsonl`, `cells/*/cell.json`, the authority and the
session JSONL files under each arm's `sessions` folder. Spend is counted the way the runner counts
it: assistant messages and compactions at Pi's list price.
"""
from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import sys
import time
from pathlib import Path

PREVIEW = 160
COLORS = {"dim": "2", "red": "31", "green": "32", "yellow": "33", "blue": "34", "cyan": "36", "bold": "1"}


def paint(text: str, color: str, enabled: bool) -> str:
    return f"\x1b[{COLORS[color]}m{text}\x1b[0m" if enabled else text


def short(value, width: int = PREVIEW) -> str:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    text = " ".join(text.split())
    return text if len(text) <= width else text[: width - 1] + "…"


# --- reading -------------------------------------------------------------------------------------

def read_json(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


class Tail:
    """Complete JSON lines appended to one file since the last read; a partial line waits."""

    def __init__(self, path: Path):
        self.path, self.offset, self.reset = Path(path), 0, False

    def read(self) -> list[dict]:
        try:
            size = self.path.stat().st_size
        except FileNotFoundError:
            return []
        if size < self.offset:  # the runner restored the arm from its snapshot
            self.offset, self.reset = 0, True
        if size == self.offset:
            return []
        with open(self.path, "rb") as handle:
            handle.seek(self.offset)
            chunk = handle.read(size - self.offset)
        end = chunk.rfind(b"\n")
        if end < 0:
            return []
        self.offset += end + 1
        events = []
        for line in chunk[: end + 1].splitlines():
            try:
                events.append(json.loads(line))
            except ValueError:
                events.append({"type": "unreadable", "line": line.decode("utf-8", "replace")})
        return events


def session_roots(arm_dir: Path) -> list[Path]:
    """Where the runner reads an arm's sessions: Pi's own, and the driver leaves' runs."""
    return [Path(arm_dir) / "sessions", Path(arm_dir) / "project" / ".git" / "ticket-driver" / "runs"]


class Sessions:
    """Every session file of one arm, in name order (Pi names them by start time)."""

    def __init__(self, arm_dir: Path):
        self.roots, self.tails = session_roots(arm_dir), {}

    def read(self) -> list[tuple[Tail, list[dict]]]:
        for root in self.roots:
            if root.is_dir():
                for path in sorted(root.rglob("*.jsonl")):
                    self.tails.setdefault(path, Tail(path))
        return [(tail, tail.read()) for _, tail in sorted(self.tails.items())]


def event_cost(event: dict) -> float:
    if event.get("type") == "compaction":
        usage = event.get("usage")
    else:
        message = event.get("message")
        if not isinstance(message, dict) or message.get("role") != "assistant":
            return 0.0
        usage = message.get("usage")
    cost = usage.get("cost") if isinstance(usage, dict) else None
    total = cost.get("total") if isinstance(cost, dict) else None
    return float(total) if isinstance(total, (int, float)) else 0.0


# --- one cell ------------------------------------------------------------------------------------

def render(event: dict, *, width: int = PREVIEW, color: bool = False, thinking: bool = False) -> list[str]:
    """Lines for one session event: messages, tool calls and results, errors; thinking on request."""
    kind = event.get("type")
    if kind == "session":
        return [paint(f"── session {event.get('id', '?')} · {event.get('cwd', '')}", "dim", color)]
    if kind == "model_change":
        return [paint(f"── model {event.get('provider')}/{event.get('modelId')}", "dim", color)]
    if kind == "compaction":
        return [paint(f"⟳ compaction (tokens before {event.get('tokensBefore', '?')})", "yellow", color)]
    if kind == "unreadable":
        return [paint(f"? {short(event.get('line', ''), width)}", "red", color)]
    message = event.get("message")
    if kind != "message" or not isinstance(message, dict):
        return []
    role, content = message.get("role"), message.get("content")
    parts = content if isinstance(content, list) else [{"type": "text", "text": content or ""}]
    parts = [part for part in parts if isinstance(part, dict)]
    lines: list[str] = []
    if role == "user":
        text = " ".join(str(p.get("text", "")) for p in parts if p.get("type") == "text")
        return [paint(f"▶ USER {short(text, width)}", "cyan", color)]
    if role == "toolResult":
        text = " ".join(str(p.get("text", "")) for p in parts if p.get("type") == "text")
        name = message.get("toolName", "?")
        if message.get("isError"):
            return [paint(f"  ✖ {name}: {short(text, width)}", "red", color)]
        return [paint(f"  ← {name}: {short(text, width)}", "dim", color)]
    if role != "assistant":
        return []
    for part in parts:
        if thinking and part.get("type") == "thinking" and str(part.get("thinking", "")).strip():
            lines.append(paint(f"\u2234 {short(part['thinking'], width)}", "dim", color))
        elif part.get("type") == "text" and str(part.get("text", "")).strip():
            lines.append(f"• {short(part['text'], width)}")
        elif part.get("type") in ("toolCall", "tool_use"):
            arguments = part.get("arguments", part.get("input"))
            if isinstance(arguments, dict) and isinstance(arguments.get("command"), str):
                arguments = arguments["command"]
            lines.append(paint(f"→ {part.get('name', '?')} {short(arguments, width)}", "blue", color))
    if message.get("stopReason") == "error" or message.get("errorMessage"):
        lines.append(paint(f"✖ ERROR {short(str(message.get('errorMessage') or 'stop: error'), width)}",
                           "red", color))
    return lines


def follow_cell(lot_dir: Path, cell: str, *, once: bool, width: int, color: bool, out=None,
                every: float = 1.0, thinking: bool = False) -> float:
    out = out or sys.stdout
    lot = read_json(Path(lot_dir) / "lot.json")
    if cell not in lot["cells"]:
        raise SystemExit(f"cell {cell} is not in lot {lot['lot']}")
    info = lot["cells"][cell]
    sessions = Sessions(info["arm_dir"])
    print(paint(f"{cell} · {lot['provider']}/{lot['model']} {lot['thinking']} · {info['arm_dir']}", "bold",
                color), file=out, flush=True)
    spent: dict[Path, float] = {}  # per file: a restored file restarts its own count only
    while True:
        for tail, events in sessions.read():
            if tail.reset:
                tail.reset, spent[tail.path] = False, 0.0
                print(paint(f"↺ {tail.path.name} restored from the snapshot; replaying", "yellow", color),
                      file=out)
            for event in events:
                for line in render(event, width=width, color=color, thinking=thinking):
                    print(line, file=out)
                cost = event_cost(event)
                if cost:
                    spent[tail.path] = spent.get(tail.path, 0.0) + cost
                    total = sum(spent.values())
                    print(paint(f"  $ {cost:.4f} · Σ cell $ {total:.4f}", "dim", color), file=out)
        out.flush()
        if once:
            return sum(spent.values())
        time.sleep(every)


# --- the lot -------------------------------------------------------------------------------------

def ledger(lot_dir: Path) -> list[dict]:
    path = Path(lot_dir) / "ledger.jsonl"
    if not path.is_file():
        return []
    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            events.append(json.loads(line))
        except ValueError:
            continue  # the runner is writing this line right now
    return events


def spend_cap(lot: dict) -> tuple[float | None, str]:
    """The authority's usd cap, or the last amendment's: one that names this lot and cites the
    bound authority by hash, filed next to it (as `dbh-opus-authority-amendment-1.json` is)."""
    path = Path(lot["authority"]["path"])
    cap, source = (read_json(path).get("caps") or {}).get("usd"), path.name
    for candidate in sorted(path.parent.glob(f"{path.stem}-amendment-*.json")):
        try:
            amendment = read_json(candidate)
        except ValueError:
            continue
        if (amendment.get("lot") == lot["lot"]
                and (amendment.get("amends") or {}).get("sha256") == lot["authority"].get("sha256")
                and isinstance((amendment.get("caps") or {}).get("usd"), (int, float))):
            cap, source = amendment["caps"]["usd"], candidate.name
    return cap, source


def lot_state(lot_dir: Path) -> dict:
    lot_dir = Path(lot_dir)
    lot = read_json(lot_dir / "lot.json")
    cap, cap_source = spend_cap(lot)
    rows, running = {}, set()
    for name in lot["cells"]:
        rows[name] = {"cell": name, "judged": 0, "accepted": 0, "requests": 0, "spend": 0.0,
                      "state": "pending", "request": None, "error": None}
        path = lot_dir / "cells" / name / "cell.json"
        if path.is_file():
            record = read_json(path)
            requests = record.get("requests") or []
            rows[name]["requests"] = len(requests)
            rows[name]["judged"] = sum(1 for r in requests if r.get("status") == "judged")
            rows[name]["accepted"] = sum(
                1 for r in requests if ((r.get("axes") or {}).get("acceptance") or {}).get("accepted"))
            rows[name]["error"] = record.get("error") or ("invalid" if record.get("invalid") else None)
    for event in ledger(lot_dir):
        row = rows.get(event.get("cell"))
        if row is None:
            continue
        if event.get("event") == "launch":
            row["state"], row["through"] = "running", event.get("through")
            running.add(row["cell"])
        elif event.get("event") == "cell":
            row["state"] = "stopped"
            running.discard(row["cell"])
        elif event.get("event") == "attempt":
            row["spend"] += float(event.get("cost_usd") or 0)
            row["request"] = event.get("request")
        elif event.get("event") == "infra-wait":
            row["request"] = event.get("request")
    for name in running:  # the request in progress is the one after the last judged one
        rows[name]["request"] = rows[name]["judged"] + 1
    spend = round(sum(row["spend"] for row in rows.values()), 6)
    return {"lot": lot["lot"], "cap_usd": cap, "cap_source": cap_source, "spend_usd": spend,
            "rows": list(rows.values()), "running": sorted(running)}


def render_lot(state: dict, *, live: dict | None = None, color: bool = False) -> list[str]:
    lines = [paint(f"lot {state['lot']} · {len(state['running'])} running", "bold", color),
             f"{'cell':34} {'state':8} {'req':>4} {'judged':>6} {'accepted':>8} {'$ done':>8} {'$ live':>8}"]
    for row in state["rows"]:
        tone = {"running": "green", "stopped": "dim"}.get(row["state"], "dim")
        now = live.get(row["cell"]) if live else None
        line = (f"{row['cell']:34} {row['state']:8} {row['request'] or '-':>4} {row['judged']:>6} "
                f"{row['accepted']:>8} {row['spend']:>8.2f} {'' if now is None else f'{now:.2f}':>8}")
        lines.append(paint(line, tone, color))
        if row["error"]:
            lines.append(paint(f"    ✖ {short(str(row['error']))}", "red", color))
    cap = state["cap_usd"]
    # the closed attempts include work the sessions may no longer hold (a restored snapshot)
    total = max(sum(live.values()) if live else 0.0, state["spend_usd"])
    share = (f" = {100 * total / cap:.1f}% of the {cap} $ cap ({state['cap_source']})"
             if isinstance(cap, (int, float)) and cap else "")
    lines.append(paint(f"spend {state['spend_usd']:.2f} $ closed attempts · {total:.2f} $ at least{share}",
                       "yellow" if share and total > 0.8 * cap else "bold", color))
    return lines


class LiveSpend:
    """Spend read from every cell's sessions, so the attempt in progress counts too."""

    def __init__(self, lot: dict):
        self.cells = {name: Sessions(info["arm_dir"]) for name, info in lot["cells"].items()}
        self.spent: dict[str, dict[Path, float]] = {name: {} for name in lot["cells"]}

    def read(self) -> dict:
        for name, sessions in self.cells.items():
            spent = self.spent[name]
            for tail, events in sessions.read():
                if tail.reset:
                    tail.reset, spent[tail.path] = False, 0.0
                spent[tail.path] = spent.get(tail.path, 0.0) + sum(event_cost(event) for event in events)
        return {name: sum(spent.values()) for name, spent in self.spent.items()}


def watch_lot(lot_dir: Path, *, once: bool, every: float, color: bool, out=None) -> dict:
    out = out or sys.stdout
    live = LiveSpend(read_json(Path(lot_dir) / "lot.json"))
    while True:
        state = lot_state(lot_dir)
        totals = live.read()
        if not once and out.isatty():
            out.write("\x1b[2J\x1b[H")
        print(time.strftime("%H:%M:%S"), file=out)
        for line in render_lot(state, live=totals, color=color):
            print(line, file=out)
        out.flush()
        if once:
            return state
        time.sleep(every)


# --- tabs ----------------------------------------------------------------------------------------

def tab_cells(lot_dir: Path, *, all_cells: bool, rep: int | None) -> list[str]:
    state = lot_state(lot_dir)
    lot = read_json(Path(lot_dir) / "lot.json")
    names = list(lot["cells"]) if all_cells else state["running"]
    return [name for name in names if rep is None or lot["cells"][name]["rep"] == rep]


def open_argv(lot_dir: Path, cells: list[str], *, python: str = sys.executable) -> list[str]:
    """One Windows Terminal window: the lot table first, then one tab per cell."""
    script, lot_dir = str(Path(__file__).resolve()), str(Path(lot_dir).resolve())
    lot = read_json(Path(lot_dir) / "lot.json")["lot"]
    argv = ["wt.exe", "-w", f"dbh-{lot}", "new-tab", "--title", f"{lot} · lot", python, "-B", script,
            "lot", "--lot", lot_dir]
    for cell in cells:
        argv += [";", "new-tab", "--title", cell, python, "-B", script, "cell", "--lot", lot_dir, "--cell", cell]
    return argv


def commands(lot_dir: Path, cells: list[str], *, python: str = sys.executable) -> list[str]:
    import subprocess

    join = subprocess.list2cmdline if os.name == "nt" else shlex.join
    script, lot_dir = str(Path(__file__).resolve()), str(Path(lot_dir).resolve())
    lines = [join([python, "-B", script, "lot", "--lot", lot_dir])]
    return lines + [join([python, "-B", script, "cell", "--lot", lot_dir, "--cell", c]) for c in cells]


def windows_terminal() -> str | None:
    return shutil.which("wt.exe") if os.name == "nt" else None


def open_tabs(lot_dir: Path, *, all_cells: bool, rep: int | None, print_only: bool, out=None) -> list[str]:
    import subprocess

    out = out or sys.stdout

    cells = tab_cells(lot_dir, all_cells=all_cells, rep=rep)
    terminal = windows_terminal()
    if print_only or terminal is None:
        for line in commands(lot_dir, cells):
            print(line, file=out)
        return []
    argv = open_argv(lot_dir, cells)
    subprocess.Popen([terminal, *argv[1:]], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL)
    print(f"opened {len(cells)} cell tabs and the lot table", file=out)
    return argv


# --- command line --------------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    cell = sub.add_parser("cell", help="follow one cell's Pi session")
    cell.add_argument("--lot", required=True, type=Path)
    cell.add_argument("--cell", required=True)
    cell.add_argument("--width", type=int, default=PREVIEW)
    cell.add_argument("--thinking", action="store_true", help="also show the model's thinking, shortened")
    lot = sub.add_parser("lot", help="cell table and spend against the cap")
    lot.add_argument("--lot", required=True, type=Path)
    lot.add_argument("--every", type=float, default=10.0)
    for command in (cell, lot):
        command.add_argument("--once", action="store_true", help="print what is there and exit")
        command.add_argument("--no-color", action="store_true")
    tabs = sub.add_parser("open", help="one Windows Terminal tab per running cell")
    tabs.add_argument("--lot", required=True, type=Path)
    tabs.add_argument("--all", action="store_true", help="every cell of the lot, not only the running ones")
    tabs.add_argument("--rep", type=int)
    tabs.add_argument("--print", action="store_true", help="print the commands instead of opening tabs")
    args = parser.parse_args(argv)
    color = not getattr(args, "no_color", True) and sys.stdout.isatty() and "NO_COLOR" not in os.environ
    try:
        if args.command == "cell":
            follow_cell(args.lot, args.cell, once=args.once, width=args.width, color=color,
                        thinking=args.thinking)
        elif args.command == "lot":
            watch_lot(args.lot, once=args.once, every=args.every, color=color)
        else:
            open_tabs(args.lot, all_cells=args.all, rep=args.rep, print_only=args.print)
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
