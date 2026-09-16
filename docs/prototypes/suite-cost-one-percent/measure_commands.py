"""Run one `test_cli` case under the command probe and aggregate what it spawned.

Usage:
    python docs/prototypes/suite-cost-one-percent/measure_commands.py <case> [<case>...]

Each case runs in its own interpreter with `sitecustomize.py` first on `PYTHONPATH`, so the
CLI subprocesses it spawns are measured too. Output: one JSON document per case under
`docs/prototypes/suite-cost-one-percent/measurements/`.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TESTS = ROOT / "ticket-autopilot" / "tests"
SCRIPTS = ROOT / "ticket-autopilot" / "scripts"
OUTPUT = HERE / "measurements"

RUNNER = """
import sys, unittest
sys.path[:0] = [{tests!r}, {scripts!r}]
import test_cli
suite = unittest.TestSuite([test_cli.CliTests({case!r})])
result = unittest.TextTestRunner(verbosity=0).run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
"""


def measure(case: str, *, baseline: bool = False) -> dict:
    logs = OUTPUT / f"{case}-raw"
    shutil.rmtree(logs, ignore_errors=True)
    logs.mkdir(parents=True)
    environment = {
        **os.environ,
        "AUTOPILOT_CMD_LOG_DIR": str(logs),
        "PYTHONPATH": os.pathsep.join([str(HERE), str(TESTS), str(SCRIPTS)]),
        "PYTHONIOENCODING": "utf-8",
        **({"AUTOPILOT_DISABLE_SCOPE": "1"} if baseline else {}),
    }
    started = time.perf_counter()
    completed = subprocess.run(
        [sys.executable, "-B", "-c", RUNNER.format(tests=str(TESTS), scripts=str(SCRIPTS), case=case)],
        cwd=ROOT, env=environment, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    duration = time.perf_counter() - started

    records = [
        json.loads(line)
        for path in sorted(logs.glob("*.jsonl"))
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return summarize(case, records, duration, completed)


def summarize(case: str, records: list[dict], duration: float, completed) -> dict:
    families: dict[tuple, dict] = defaultdict(lambda: {"count": 0, "ms": 0.0, "operations": defaultdict(int)})
    within_operation: dict[tuple, int] = defaultdict(int)
    git_ms = other_ms = 0.0
    for record in records:
        argv = record["argv"]
        key = tuple(argv[:4])
        entry = families[key]
        entry["count"] += 1
        entry["ms"] += record["ms"]
        entry["operations"][record["operation"]] += 1
        if argv and argv[0].startswith("git"):
            git_ms += record["ms"]
        else:
            other_ms += record["ms"]
        # A repeat is the same question, to the same directory, inside one invocation.
        within_operation[(record["pid"], record["operation_instance"], record["operation"], key, record["cwd"])] += 1

    repeated_in_operation = sum(count - 1 for count in within_operation.values() if count > 1)
    table = sorted(
        (
            {
                "argv": " ".join(key),
                "count": entry["count"],
                "total_ms": round(entry["ms"], 1),
                "mean_ms": round(entry["ms"] / entry["count"], 1),
                "operations": dict(sorted(entry["operations"].items(), key=lambda item: -item[1])[:4]),
            }
            for key, entry in families.items()
        ),
        key=lambda item: -item["total_ms"],
    )
    repeats = sorted(
        (
            {"operation": operation, "argv": " ".join(key), "extra_calls": count - 1}
            for (_pid, _instance, operation, key, _cwd), count in within_operation.items()
            if count > 1
        ),
        key=lambda item: -item["extra_calls"],
    )
    merged: dict[tuple, int] = defaultdict(int)
    for item in repeats:
        merged[(item["operation"], item["argv"])] += item["extra_calls"]

    return {
        "case": case,
        "ok": completed.returncode == 0,
        "case_seconds": round(duration, 1),
        "commands": len(records),
        "git_seconds": round(git_ms / 1000, 1),
        "other_seconds": round(other_ms / 1000, 1),
        "repeated_calls_within_one_operation": repeated_in_operation,
        "families": table,
        "repeats_within_operation": [
            {"operation": operation, "argv": argv, "extra_calls": extra}
            for (operation, argv), extra in sorted(merged.items(), key=lambda item: -item[1])
        ],
        "stderr_tail": completed.stderr[-400:],
    }


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    baseline = argv[:1] == ["--baseline"]
    argv = argv[1:] if baseline else argv
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for case in argv:
        report = measure(case, baseline=baseline)
        (OUTPUT / f"{case}{'-baseline' if baseline else ''}.json").write_text(
            json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8", newline="\n"
        )
        print(
            f"{case}: {report['case_seconds']}s ok={report['ok']} commands={report['commands']} "
            f"git={report['git_seconds']}s repeats-in-operation={report['repeated_calls_within_one_operation']}",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
