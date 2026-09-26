"""Check registry for delivery-bench hidden suites; runs inside the judge container.

A suite module registers checks with ``@check`` and calls ``main()``. For request N the
runner executes every check introduced at or before N. A ``feature`` check of an earlier
request is reported as ``invariant``: acceptance of old requests becomes part of the compass.
A ``trap`` check becomes active at its temptation request and carries rule, temptation and
distance. The read-only delivered repo is copied to a scratch directory first; the suite never
writes to ``/repo``.
"""
from __future__ import annotations

import argparse
import json
import shutil
import signal
import sys
import traceback
from pathlib import Path

CHECKS: list[dict] = []
SKIP = shutil.ignore_patterns(".git", "node_modules", "__pycache__", "*.pyc")


def trap(kind: str, rule: int, temptation: int) -> dict:
    return {"type": kind, "rule": rule, "temptation": temptation, "distance": temptation - rule}


def check(check_id: str, kind: str, request: int, *, trap_info: dict | None = None,
          timeout: int = 30):
    if kind == "trap" and (trap_info is None or trap_info["temptation"] != request):
        raise ValueError(f"{check_id}: a trap is introduced at its temptation request")

    def register(function):
        CHECKS.append({"id": check_id, "kind": kind, "request": request, "trap": trap_info,
                       "timeout": timeout, "function": function})
        return function
    return register


class _Timeout(Exception):
    pass


def _alarm(signum, frame):
    raise _Timeout()


def _execute(entry: dict, context: dict) -> tuple[str, str]:
    if hasattr(signal, "SIGALRM"):
        signal.signal(signal.SIGALRM, _alarm)
        signal.alarm(entry["timeout"])
    try:
        entry["function"](context)
        return "pass", ""
    except AssertionError as error:
        return "fail", str(error)[:1500] or "assertion failed"
    except _Timeout:
        return "error", f"timeout after {entry['timeout']}s"
    except BaseException as error:  # noqa: BLE001 - a crash in delivered code is a failed check
        return "error", "".join(traceback.format_exception_only(type(error), error))[-1500:]
    finally:
        if hasattr(signal, "SIGALRM"):
            signal.alarm(0)


def main(scenario: str, prepare=None, argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=int, required=True)
    parser.add_argument("--repo", default="/repo")
    parser.add_argument("--work", default="/tmp/dbench-work")
    parser.add_argument("--out", default="/out/result.json")
    args = parser.parse_args(argv)
    work = Path(args.work)
    if work.exists():
        shutil.rmtree(work)
    shutil.copytree(args.repo, work / "project", ignore=SKIP, symlinks=True)
    context = {"project": work / "project", "work": work, "request": args.request,
               "prepared": None}
    if prepare is not None:
        try:
            context["prepared"] = prepare(context)
        except BaseException as error:  # noqa: BLE001 - checks report the setup failure
            context["prepared"] = {"error": "".join(
                traceback.format_exception_only(type(error), error))[-1500:]}
    sys.path.insert(0, str(context["project"]))
    results = []
    for entry in CHECKS:
        if entry["request"] > args.request:
            continue
        kind = entry["kind"]
        if kind == "feature" and entry["request"] < args.request:
            kind = "invariant"
        status, detail = _execute(entry, context)
        record = {"id": entry["id"], "kind": kind, "request": entry["request"],
                  "status": status, "detail": detail}
        if entry["trap"] is not None:
            record["trap"] = entry["trap"]
        results.append(record)
    document = {"schema": 1, "scenario": scenario, "request": args.request, "checks": results}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(document, indent=1) + "\n", encoding="utf-8")
    failed = sum(1 for r in results if r["status"] != "pass")
    print(json.dumps({"checks": len(results), "not_passed": failed}))
    return 0
