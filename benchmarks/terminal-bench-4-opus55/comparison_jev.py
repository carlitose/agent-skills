"""Task-bound host-only Jev metering; the original driver's allowlist is untouched."""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import urllib.request
from decimal import Decimal
from pathlib import Path

from comparison_accounting import _append, _rows, AccountingError
from freeze_manifest import PILOT

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("tbf_comparison_arbiter", ROOT / "ticket-driver/scripts/arbiter.py")
arbiter = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(arbiter)
RATE = Decimal("0.000000042")  # Published $0.042/M input; output free, estimate not invoice.
MODEL = "jev-1.13.0"


class JevFailure(RuntimeError):
    pass


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # Never forward the credential to a redirected origin.


class ComparisonJev:
    def __init__(self, path: Path, identity: dict, *, admit, transport=None,
                 tasks=PILOT, method="git-overlay-v1"):
        # The overlay comparison binds pilot tasks; the original adapter passes its lot's tasks.
        if (identity.get("method") != method or identity.get("task") not in tasks
                or identity.get("arm") != "ticket-driver-c3a" or not identity.get("trial")
                or not callable(admit)):
            raise JevFailure("Jev lacks an authorized comparison cell")
        self.path = Path(path)
        if self.path.resolve().is_relative_to(ROOT):
            raise JevFailure("Jev receipts must remain outside Git")
        self.identity = dict(identity)
        self.admit = admit
        self.transport = transport or urllib.request.build_opener(_NoRedirect()).open
        self.requests = self.settled = self.input_tokens = self.output_tokens = 0
        self.observed = Decimal(0)
        self.unknown = self.failed = False
        self.seq = 0
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._persist("initial", mode="x")

    def receipt(self):
        known = not self.unknown and self.requests == self.settled
        return {"identity": self.identity, "model_requested": MODEL,
                "input_rate_usd_per_token": str(RATE), "requests": self.requests,
                "settled": self.settled, "input_tokens": self.input_tokens, "output_tokens": self.output_tokens,
                "observed_usd": str(self.observed), "known": known,
                "cost_usd": str(self.observed) if known else None}

    def _persist(self, event, *, mode="a", **extra):
        _append(self.path, {"schema": 1, "seq": self.seq, "event": event, **self.receipt(), **extra}, mode)
        self.seq += 1

    def _transport(self, request, *, timeout):
        if len(request.data) > 24576:
            raise JevFailure("Jev state/questions exceed conservative byte bound")
        self.admit()
        self.requests += 1
        self._persist("request", payload_sha256=hashlib.sha256(request.data).hexdigest())
        with self.transport(request, timeout=timeout) as response:
            raw = response.read(1048577)
        if len(raw) > 1048576:
            raise JevFailure("oversized Jev response")
        result = json.loads(raw)
        usage = result.get("usage", {}) if isinstance(result, dict) else {}
        if (any(type(usage.get(k)) is not int or usage[k] < 0 for k in ("input_tokens", "output_tokens"))
                or not 0 < usage["input_tokens"] <= 65536
                or result.get("model", MODEL) != MODEL):
            raise JevFailure("unknown Jev usage or model drift")
        self.input_tokens += usage["input_tokens"]
        self.output_tokens += usage["output_tokens"]
        self.observed += usage["input_tokens"] * RATE
        self.settled += 1
        self._persist("usage", response_sha256=hashlib.sha256(raw).hexdigest(),
                      model_reported=result.get("model"))
        # Let the existing typed contract validate answers after preserving usage.
        return io.BytesIO(raw)

    def ask(self, state: dict, selected: dict):
        if self.failed or self.unknown or self.requests >= 16 or self.observed + Decimal("0.01") > 3:
            raise JevFailure("Jev request budget or previous failure blocks judgment")
        if not selected or not isinstance(selected, dict) or not isinstance(state, dict):
            raise JevFailure("missing typed questions or state")
        try:
            payload = json.dumps({"state": state, "questions": selected, "model": MODEL},
                                 allow_nan=False, ensure_ascii=False).encode("utf8")
            if len(payload) > 24576:
                raise JevFailure("Jev input exceeds conservative byte bound")
            answers, _ = arbiter.ask(state, selected, {
                "endpoint": "https://api.typesafe.ai/v1/systemone", "model": MODEL,
                "max_attempts": 1, "timeout_seconds": 30}, transport=self._transport)
            return answers
        except Exception:
            self.failed = True
            self.unknown = self.requests != self.settled
            self._persist("failure")
            raise JevFailure("Jev judgment unavailable; inspect attributable usage receipt") from None


def read_jev_journal(path: Path, identity: dict):
    raw, rows = _rows(Path(path))
    previous = None
    for seq, row in enumerate(rows):
        if (row.get("schema") != 1 or row.get("seq") != seq or row.get("identity") != identity
                or row.get("model_requested") != MODEL or row.get("input_rate_usd_per_token") != str(RATE)
                or any(type(row.get(k)) is not int or row[k] < 0
                       for k in ("requests", "settled", "input_tokens", "output_tokens"))
                or row["requests"] > 16 or not 0 <= row["requests"] - row["settled"] <= 1):
            raise AccountingError("invalid Jev journal binding or counters")
        observed = Decimal(row.get("observed_usd", "NaN"))
        if not observed.is_finite() or observed != row["input_tokens"] * RATE:
            raise AccountingError("Jev token/cost mismatch")
        known = row["requests"] == row["settled"]
        if type(row.get("known")) is not bool or row["known"] != known or row.get("cost_usd") != (str(observed) if known else None):
            raise AccountingError("Jev invented known cost")
        event = row.get("event")
        if previous is None:
            if event != "initial" or any(row[k] for k in ("requests", "settled", "input_tokens", "output_tokens")):
                raise AccountingError("missing Jev origin")
        elif event == "request":
            if (not previous["known"] or previous["event"] == "failure" or row["requests"] != previous["requests"] + 1
                    or any(row[k] != previous[k] for k in ("settled", "input_tokens", "output_tokens"))):
                raise AccountingError("invalid Jev request")
        elif event == "usage":
            if (previous["known"] or row["requests"] != previous["requests"] or row["settled"] != previous["settled"] + 1
                    or not 0 < row["input_tokens"] - previous["input_tokens"] <= 65536
                    or row["output_tokens"] < previous["output_tokens"]):
                raise AccountingError("invalid Jev settlement")
        elif event == "failure":
            if any(row[k] != previous[k] for k in ("requests", "settled", "input_tokens", "output_tokens")):
                raise AccountingError("Jev failure changed usage")
        else:
            raise AccountingError("invalid Jev event")
        previous = row
    return {key: previous[key] for key in ("known", "cost_usd", "input_tokens", "output_tokens", "requests")} | {
        "sha256": hashlib.sha256(raw).hexdigest()}
