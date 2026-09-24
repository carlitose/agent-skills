"""Append-only, offline pilot attempt and budget admission; not a benchmark launcher.

A persisted start consumes its task/arm cell even after failure. An unresolved or
ambiguous result prevents further spending. This module does not enforce the
project-wide ceiling or live streaming cut-off; those remain TBF-03 gates.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from contextlib import contextmanager
from decimal import Decimal, InvalidOperation
from pathlib import Path

from freeze_manifest import PILOT

MODEL = "openai-codex/gpt-6-sol"
ARMS = ("pi-bare", "skills-only", "ticket-driver-c1a", "ticket-driver-c3a")
CAP = Decimal("250")
MAX_STARTS = len(PILOT) * len(ARMS)


class GateError(ValueError):
    """Admission cannot prove a safe next attempt."""


def amount(value, *, allow_zero=False) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (str, Decimal)):
        raise GateError("cost must be a decimal string")
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise GateError("invalid cost") from exc
    if not number.is_finite() or number < 0 or (not allow_zero and number == 0):
        raise GateError("invalid cost")
    return number


class PilotLedger:
    def __init__(self, path: Path, manifest_path: Path):
        self.path = Path(path)
        self.lock = self.path.with_name(self.path.name + ".lock")
        manifest_raw = Path(manifest_path).read_bytes()
        manifest = json.loads(manifest_raw)
        tasks = manifest.get("tasks", [])
        pilot = {t["name"]: t for t in tasks if t["name"] in PILOT}
        if (manifest.get("schema") != 1 or manifest.get("pilot_tasks") != list(PILOT)
            or manifest.get("dataset_task_count") != len(tasks)
            or len(pilot) != len(PILOT)
            or any(pilot[name]["agent_gpus"] or pilot[name]["verifier_gpus"] for name in PILOT)):
            raise GateError("invalid pilot manifest")
        self.header = {"event": "pilot", "schema": 1,
                       "manifest_sha256": hashlib.sha256(manifest_raw).hexdigest(),
                       "dataset_ref": manifest["dataset_ref"], "model": MODEL,
                       "tasks": list(PILOT), "arms": list(ARMS),
                       "max_starts": MAX_STARTS, "cap_usd": str(CAP)}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._exclusive():
            if not self.path.exists():
                with self.path.open("x", encoding="utf-8", newline="\n") as output:
                    output.write(json.dumps(self.header, sort_keys=True) + "\n")
                    output.flush()
                    os.fsync(output.fileno())
            self._state()

    @contextmanager
    def _exclusive(self):
        try:
            self.lock.mkdir()
        except FileExistsError as exc:
            raise GateError("ledger busy or previous operation unresolved") from exc
        try:
            if self.path.is_symlink():
                raise GateError("linked ledger is forbidden")
            yield
        finally:
            self.lock.rmdir()

    def _read_events(self) -> list[dict]:
        try:
            with self.path.open("r", encoding="utf-8") as source:
                records = [json.loads(line) for line in source]
        except (OSError, UnicodeError, ValueError) as exc:
            raise GateError("corrupt pilot ledger") from exc
        if not records or records[0] != self.header:
            raise GateError("manifest or model binding differs from pilot ledger")
        if any(not isinstance(record, dict) for record in records):
            raise GateError("corrupt pilot ledger")
        return records[1:]

    def _state(self) -> dict:
        attempts = {}
        starts = 0
        spent = Decimal(0)
        ambiguous = False
        unknown_cost = False
        for event in self._read_events():
            try:
                ident = (event["task"], event["arm"])
                kind = event["event"]
                if ident[0] not in PILOT or ident[1] not in ARMS:
                    raise ValueError("invalid cell")
                if kind == "reserved":
                    if ident in attempts or any(row["stage"] in ("reserved", "started") for row in attempts.values()):
                        raise ValueError("duplicate or concurrent attempt")
                    limit = amount(event["max_cost_usd"])
                    attempts[ident] = {"stage": "reserved", "limit": limit}
                elif kind == "started":
                    if attempts[ident]["stage"] != "reserved":
                        raise ValueError("start without reservation")
                    starts += 1
                    attempts[ident]["stage"] = "started"
                elif kind in ("settled", "overrun"):
                    if attempts[ident]["stage"] != "started":
                        raise ValueError("result without start")
                    cost = amount(event["cost_usd"], allow_zero=True)
                    spent += cost
                    attempts[ident]["stage"] = kind
                    if kind == "overrun" or cost > attempts[ident]["limit"]:
                        ambiguous = True
                elif kind == "unknown_cost":
                    if attempts[ident]["stage"] != "started":
                        raise ValueError("unknown cost without start")
                    attempts[ident]["stage"] = kind
                    ambiguous = True
                    unknown_cost = True
                else:
                    raise ValueError("unknown event")
            except (KeyError, TypeError, ValueError) as exc:
                raise GateError("corrupt pilot ledger") from exc
        if starts > MAX_STARTS:
            raise GateError("corrupt pilot ledger: too many starts")
        if spent > CAP:
            ambiguous = True
        return {"starts": starts,
                "spent_usd": "unknown" if unknown_cost else str(spent),
                "known_spent_usd": str(spent),
                "remaining_usd": "unknown" if ambiguous else str(CAP - spent),
                "ambiguous": ambiguous, "attempts": attempts}

    def state(self) -> dict:
        """Safe readback; Decimal values in attempts are internal, never serialized."""
        state = self._state()
        return {key: value for key, value in state.items() if key != "attempts"}

    def _append(self, event: dict) -> None:
        with self.path.open("a", encoding="utf-8", newline="\n") as output:
            output.write(json.dumps(event, sort_keys=True) + "\n")
            output.flush()
            os.fsync(output.fileno())

    def reserve(self, task: str, arm: str, max_cost_usd: str) -> None:
        with self._exclusive():
            state = self._state()
            if state["ambiguous"]:
                raise GateError("ambiguous previous attempt or cost")
            if task not in PILOT or arm not in ARMS:
                raise GateError("task/arm is not in the frozen pilot")
            if (task, arm) in state["attempts"]:
                raise GateError("attempt cell already used")
            if any(row["stage"] in ("reserved", "started") for row in state["attempts"].values()):
                raise GateError("unresolved previous attempt")
            if state["starts"] >= MAX_STARTS:
                raise GateError("pilot start limit reached")
            limit = amount(max_cost_usd)
            if Decimal(state["spent_usd"]) + limit > CAP:
                raise GateError("pilot budget exhausted")
            self._append({"event": "reserved", "task": task, "arm": arm,
                          "max_cost_usd": str(limit)})

    def start(self, task: str, arm: str) -> None:
        with self._exclusive():
            state = self._state()
            row = state["attempts"].get((task, arm))
            if state["ambiguous"] or not row or row["stage"] != "reserved":
                raise GateError("start requires one outstanding reservation")
            self._append({"event": "started", "task": task, "arm": arm})

    def settle(self, task: str, arm: str, *, status: str, cost_usd: str | None,
               input_tokens: int | None, output_tokens: int | None,
               elapsed_seconds: str | None, verifier_pass: bool | None,
               receipt_sha256: str | None) -> None:
        with self._exclusive():
            state = self._state()
            row = state["attempts"].get((task, arm))
            if state["ambiguous"] or not row or row["stage"] != "started":
                raise GateError("result requires one unresolved start")
            if status not in ("valid", "failed", "gated"):
                raise GateError("invalid result status")
            if cost_usd is None:
                self._append({"event": "unknown_cost", "task": task, "arm": arm,
                              "status": status})
                raise GateError("unknown cost blocks future starts")
            cost = amount(cost_usd, allow_zero=True)
            if type(output_tokens) is int and output_tokens > 0 and cost == 0:
                self._append({"event": "unknown_cost", "task": task, "arm": arm,
                              "status": status})
                raise GateError("unknown cost blocks future starts")
            if status != "gated" and verifier_pass is None:
                raise GateError("missing verifier observation")
            if (any(type(token) is not int or token < 0 for token in (input_tokens, output_tokens))
                or elapsed_seconds is None or amount(elapsed_seconds, allow_zero=True) < 0
                or verifier_pass is not None and type(verifier_pass) is not bool
                or not isinstance(receipt_sha256, str)
                or not re.fullmatch(r"[a-f0-9]{64}", receipt_sha256)):
                raise GateError("invalid usage, duration, verifier or receipt evidence")
            overrun = cost > row["limit"] or Decimal(state["spent_usd"]) + cost > CAP
            self._append({"event": "overrun" if overrun else "settled", "task": task,
                          "arm": arm, "status": status, "cost_usd": str(cost),
                          "input_tokens": input_tokens, "output_tokens": output_tokens,
                          "elapsed_seconds": str(amount(elapsed_seconds, allow_zero=True)),
                          "verifier_pass": verifier_pass, "receipt_sha256": receipt_sha256})
            if overrun:
                raise GateError("cost overrun blocks future starts")
