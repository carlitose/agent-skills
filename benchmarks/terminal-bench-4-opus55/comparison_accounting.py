"""Offline admission and attributable usage for the separate modified lot.

No launching, scheduling, billing claims, retries, or new unknown-cost waivers.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
from contextlib import contextmanager
from decimal import Decimal
from pathlib import Path

from freeze_manifest import PILOT
from pilot_ledger import ARMS, GateError as AccountingError, amount


def _sha(value):
    if not isinstance(value, str) or not re.fullmatch(r"[a-f0-9]{64}", value):
        raise AccountingError("invalid evidence hash")
    return value


def _rows(path):
    try:
        if path.is_symlink() or not 0 < path.stat().st_size <= 2097152:
            raise AccountingError("unsafe or oversized receipt")
        raw = path.read_bytes()
        if not raw.endswith(b"\n"):
            raise AccountingError("partial receipt record")
        rows = [json.loads(line) for line in raw.splitlines()]
        if not rows or any(not isinstance(row, dict) for row in rows):
            raise AccountingError("invalid receipt records")
        return raw, rows
    except (OSError, UnicodeError, ValueError) as error:
        raise AccountingError("unreadable receipt") from error


def _append(path, row, mode="a"):
    with path.open(mode, encoding="utf8", newline="\n") as file:
        file.write(json.dumps(row, sort_keys=True) + "\n")
        file.flush()
        os.fsync(file.fileno())


class ComparisonLedger:
    tasks = PILOT
    arms = ARMS

    def __init__(self, path, *, binding_sha256, authority_sha256, prior_ledger_sha256,
                 prior_commitment_usd):
        self.path = Path(path)
        self.lock = self.path.with_name(self.path.name + ".lock")
        prior = amount(prior_commitment_usd)
        if prior + Decimal("720") > Decimal("1000"):
            raise AccountingError("project admission exceeds estimated ceiling")
        if self.path.resolve().is_relative_to(Path(__file__).resolve().parents[2]):
            raise AccountingError("comparison ledger must remain outside Git")
        self.header = {"event": "comparison", "schema": 1, "method": "git-overlay-v1",
                       "binding_sha256": _sha(binding_sha256), "authority_sha256": _sha(authority_sha256),
                       "prior_ledger_sha256": _sha(prior_ledger_sha256),
                       "prior_commitment_usd": str(prior), "prior_observed_usd": "unknown",
                       "cap_usd": "720", "per_start_usd": "60", "max_starts": 12,
                       "tasks": list(self.tasks), "arms": list(self.arms)}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._exclusive():
            if not self.path.exists():
                _append(self.path, self.header, "x")
            self._reduce(self._events())

    @contextmanager
    def _exclusive(self):
        try:
            self.lock.mkdir()
        except FileExistsError as error:
            raise AccountingError("ledger busy or interrupted mutation") from error
        try:
            if self.path.is_symlink():
                raise AccountingError("linked ledger")
            yield
        finally:
            self.lock.rmdir()

    def _events(self):
        _, rows = _rows(self.path)
        if rows[0] != self.header:
            raise AccountingError("comparison binding or authority drift")
        return rows[1:]

    def _reduce(self, events):
        cells, spent, starts = {}, Decimal(0), 0
        blocked = unknown = False
        for event in events:
            try:
                cell = event["task"], event["arm"]
                kind = event["event"]
                if cell[0] not in self.tasks or cell[1] not in self.arms:
                    raise AccountingError("unbound comparison cell")
                pending = any(stage in ("reserved", "started") for stage in cells.values())
                if kind == "reserved":
                    if (set(event) != {"event", "task", "arm"} or blocked or pending or
                            cell in cells or spent + Decimal("60") > Decimal("720")):
                        raise AccountingError("cell already consumed, blocked or budget unavailable")
                    cells[cell] = "reserved"
                elif kind == "started":
                    if set(event) != {"event", "task", "arm"} or blocked or cells.get(cell) != "reserved":
                        raise AccountingError("start lacks an unused reservation")
                    cells[cell] = "started"
                    starts += 1
                elif kind == "settled":
                    if (set(event) != {"event", "task", "arm", "cost_usd", "receipt_sha256"}
                            or cells.get(cell) != "started"):
                        raise AccountingError("settlement lacks an unresolved start")
                    _sha(event["receipt_sha256"])
                    if event["cost_usd"] is None:
                        unknown = blocked = True
                    else:
                        cost = amount(event["cost_usd"], allow_zero=True)
                        spent += cost
                        blocked = blocked or cost > Decimal("60") or spent > Decimal("720")
                    cells[cell] = "settled"
                else:
                    raise AccountingError("unknown comparison event; waivers are not supported")
            except (KeyError, TypeError) as error:
                raise AccountingError("invalid comparison record") from error
        if starts > 12:
            raise AccountingError("start limit exceeded")
        pending_count = sum(stage in ("reserved", "started") for stage in cells.values())
        return {"starts": starts, "spent_usd": "unknown" if unknown else str(spent),
                "known_spent_usd": str(spent), "blocked": blocked, "pending": pending_count,
                "remaining_usd": "unknown" if blocked else str(Decimal("720") - spent - 60 * pending_count),
                "prior_observed_usd": "unknown", "prior_commitment_usd": self.header["prior_commitment_usd"]}

    def state(self):
        with self._exclusive():
            return self._reduce(self._events())

    def _record(self, event):
        with self._exclusive():
            self._reduce(self._events() + [event])
            _append(self.path, event)

    def reserve(self, task, arm):
        self._record({"event": "reserved", "task": task, "arm": arm})

    def start(self, task, arm):
        self._record({"event": "started", "task": task, "arm": arm})

    def settle(self, task, arm, cost_usd, receipt_sha256):
        self._record({"event": "settled", "task": task, "arm": arm,
                      "cost_usd": cost_usd, "receipt_sha256": receipt_sha256})


def _number(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def read_model_journal(path: Path, identity: dict) -> dict:
    """Read only after the endpoint exited. A committed prefix can prove partial use.

    Missing/truncated records are errors, not zero. A final request without its
    usage remains unknown, even when prior requests have complete usage.
    """
    raw, rows = _rows(Path(path))
    if len(rows) > 256:
        raise AccountingError("journal record bound exceeded")
    previous = None
    settled = 0
    unknown = terminal = False
    for seq, row in enumerate(rows):
        budget = row.get("budget", {})
        if (terminal or type(row.get("schema")) is not int or row["schema"] != 1
                or type(row.get("seq")) is not int or row["seq"] != seq or row.get("identity") != identity
                or not isinstance(budget, dict) or budget.get("maxRequests") != 48
                or budget.get("limitUsd") != "57" or budget.get("maxPerRequestUsd") != 8.2
                or type(budget.get("ambiguous")) is not bool
                or any(type(budget.get(k)) is not int or budget[k] < 0 for k in ("requests", "pendingRequests"))
                or budget["requests"] > 48 or budget["pendingRequests"] > 1
                or any(not _number(budget.get(k)) for k in ("observedUsd", "reservedUsd"))
                or any(type(row.get(k)) is not int or row[k] < 0 for k in ("input_tokens", "output_tokens"))
                or abs(budget["reservedUsd"] - budget["observedUsd"] - 8.2 * budget["pendingRequests"]) > 1e-6):
            raise AccountingError("invalid journal identity, sequence or budget")
        event = row.get("event")
        if previous is None:
            if (event != "initial" or budget["requests"] or budget["pendingRequests"] or
                    budget["observedUsd"] or row["input_tokens"] or row["output_tokens"]):
                raise AccountingError("missing journal origin")
        else:
            old = previous["budget"]
            if (budget["observedUsd"] < old["observedUsd"] or
                    row["input_tokens"] < previous["input_tokens"] or row["output_tokens"] < previous["output_tokens"]):
                raise AccountingError("journal usage decreased")
            if event == "request":
                if (unknown or old["pendingRequests"] or budget["requests"] != old["requests"] + 1
                        or budget["pendingRequests"] != 1 or budget["observedUsd"] != old["observedUsd"]
                        or any(row[k] != previous[k] for k in ("input_tokens", "output_tokens"))):
                    raise AccountingError("invalid request reservation")
            elif event == "usage":
                if (old["pendingRequests"] != 1 or budget["requests"] != old["requests"]
                        or budget["pendingRequests"] != 0 or budget["observedUsd"] <= old["observedUsd"]
                        or row["input_tokens"] + row["output_tokens"] <= previous["input_tokens"] + previous["output_tokens"]):
                    raise AccountingError("invalid usage settlement")
                settled += 1
            elif event == "unknown-usage":
                unknown = True
                if budget["requests"] != old["requests"]:
                    raise AccountingError("unknown usage changed request count")
            elif event in ("phase", "synthetic-error", "terminal"):
                if budget != old or any(row[k] != previous[k] for k in ("input_tokens", "output_tokens")):
                    raise AccountingError("non-usage event changed accounting")
                if event == "terminal":
                    terminal = True
                    if row.get("status") not in ("completed", "failed"):
                        raise AccountingError("invalid terminal status")
            else:
                raise AccountingError("invalid journal event")
        known = not unknown and not budget["ambiguous"] and not budget["pendingRequests"] and settled == budget["requests"]
        expected_cost = budget["observedUsd"] if known else None
        if (type(row.get("known")) is not bool or row["known"] != known or row.get("cost_usd") != expected_cost
                or (known and (not _number(row.get("cost_usd")) or budget["observedUsd"] > 57))
                or (budget["reservedUsd"] > 57 + 1e-6 and not budget["ambiguous"])):
            raise AccountingError("journal invents known cost or exceeds its reservation")
        previous = row
    return {"known": previous["known"], "cost_usd": previous["cost_usd"],
            "input_tokens": previous["input_tokens"], "output_tokens": previous["output_tokens"],
            "budget": previous["budget"], "terminal": terminal,
            "sha256": hashlib.sha256(raw).hexdigest()}
