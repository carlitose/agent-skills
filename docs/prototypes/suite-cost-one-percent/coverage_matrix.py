"""Which product lines does each `test_cli` case execute, and which case is redundant?

Uses `trace` from the standard library, so nothing has to be installed. Each case runs in its
own interpreter and reports the set of `ticket-autopilot/scripts/autopilot/*.py` lines it
executed. A case whose set is a strict subset of another's executes no product line the other
does not; a group with identical sets executes exactly the same lines.

Line coverage is not behaviour coverage: a subset case can still assert something its
superset does not. The output names candidates, never verdicts.

Tracking policy: `coverage/report.json` is the versioned aggregate evidence. Per-test
`coverage/test_*.json` files are regenerable inputs and are ignored by Git.

Usage:
    python docs/prototypes/suite-cost-one-percent/coverage_matrix.py --list
    python docs/prototypes/suite-cost-one-percent/coverage_matrix.py <case> [<case>...]
    python docs/prototypes/suite-cost-one-percent/coverage_matrix.py --all
    python docs/prototypes/suite-cost-one-percent/coverage_matrix.py --report
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TESTS = ROOT / "ticket-autopilot" / "tests"
SCRIPTS = ROOT / "ticket-autopilot" / "scripts"
PRODUCT = SCRIPTS / "autopilot"
OUTPUT = HERE / "coverage"

RUNNER = """
import json, sys, trace, unittest
from pathlib import Path
sys.path[:0] = [{tests!r}, {scripts!r}]
import test_cli
product = Path({product!r})
tracer = trace.Trace(count=1, trace=0, ignoredirs=[sys.prefix, sys.exec_prefix])
suite = unittest.TestSuite([test_cli.CliTests({case!r})])
holder = {{}}
tracer.runfunc(lambda: holder.update(result=unittest.TextTestRunner(verbosity=0).run(suite)))
lines = sorted(
    f"{{Path(filename).name}}:{{number}}"
    for (filename, number) in tracer.results().counts
    if Path(filename).parent == product
)
Path({sink!r}).write_text(json.dumps({{"ok": holder["result"].wasSuccessful(), "lines": lines}}), encoding="utf-8")
sys.exit(0)
"""


def cases() -> list[str]:
    listing = subprocess.run(
        [sys.executable, "-B", "-c",
         "import sys, unittest;"
         f"sys.path[:0] = [{str(TESTS)!r}, {str(SCRIPTS)!r}];"
         "import test_cli;"
         "print('\\n'.join(sorted(t.id().split('.')[-1] for t in "
         "unittest.defaultTestLoader.loadTestsFromTestCase(test_cli.CliTests))))"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
    )
    if listing.returncode:
        raise SystemExit(listing.stderr[-800:])
    return [line.strip() for line in listing.stdout.splitlines() if line.strip()]


def measure(case: str) -> dict:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    sink = OUTPUT / f"{case}.json"
    if sink.exists():
        return json.loads(sink.read_text(encoding="utf-8"))
    started = time.perf_counter()
    completed = subprocess.run(
        [sys.executable, "-B", "-c", RUNNER.format(
            tests=str(TESTS), scripts=str(SCRIPTS), product=str(PRODUCT), case=case, sink=str(sink))],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    if not sink.exists():
        payload = {"ok": False, "lines": [], "error": completed.stderr[-600:]}
        sink.write_text(json.dumps(payload), encoding="utf-8", newline="\n")
        return payload
    payload = json.loads(sink.read_text(encoding="utf-8"))
    payload["seconds"] = round(time.perf_counter() - started, 1)
    sink.write_text(json.dumps(payload), encoding="utf-8", newline="\n")
    return payload


def history() -> dict[str, int]:
    cache = Path(os.environ.get("AGENT_SKILLS_TEST_HISTORY", Path(os.environ.get("TEMP", "/tmp")) / "agent-skills-test-durations.json"))
    if not cache.exists():
        return {}
    suites = json.loads(cache.read_text(encoding="utf-8")).get("suites", {})
    units = suites.get("ticket-autopilot/tests/test_cli.py", {}).get("unit_ms", {})
    return {key.split(".")[-1]: value for key, value in units.items()}


def report() -> dict:
    measured = {
        path.stem: json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(OUTPUT.glob("*.json"))
        if path.name != "report.json"
    }
    sets = {case: frozenset(payload["lines"]) for case, payload in measured.items() if payload.get("lines")}
    durations = history()
    identical: dict[frozenset, list[str]] = {}
    for case, lines in sets.items():
        identical.setdefault(lines, []).append(case)

    subsets = []
    for case, lines in sets.items():
        if len(identical[lines]) > 1:
            continue
        supersets = sorted(
            other for other, other_lines in sets.items()
            if other != case and lines < other_lines
        )
        if supersets:
            subsets.append({"case": case, "lines": len(lines), "covered_by": supersets[:3],
                            "ms": durations.get(case, 0)})

    groups = [
        {"cases": sorted(group), "lines": len(lines),
         "ms": sum(durations.get(case, 0) for case in sorted(group)[1:])}
        for lines, group in identical.items() if len(group) > 1
    ]
    own = sorted(set(sets) - {item["case"] for item in subsets} - {case for group in groups for case in group["cases"]})
    return {
        "measured_cases": len(sets),
        "failed_cases": sorted(case for case, payload in measured.items() if not payload.get("ok", False)),
        "strict_subsets": sorted(subsets, key=lambda item: -item["ms"]),
        "identical_groups": sorted(groups, key=lambda item: -item["ms"]),
        "own_coverage": own,
        "savings_seconds": {
            "delete_strict_subsets": round(sum(item["ms"] for item in subsets) / 1000),
            "merge_identical_groups": round(sum(group["ms"] for group in groups) / 1000),
        },
        "caveat": "Line coverage is not behaviour coverage. Every entry is a candidate for human review.",
    }


def main(argv: list[str]) -> int:
    if argv[:1] == ["--list"]:
        print("\n".join(cases()))
        return 0
    if argv[:1] == ["--report"]:
        payload = report()
        (OUTPUT / "report.json").write_text(json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8", newline="\n")
        print(json.dumps({key: value for key, value in payload.items() if key != "strict_subsets"}, indent=1)[:2000])
        return 0
    selected = cases() if argv[:1] == ["--all"] else argv
    if not selected:
        print(__doc__)
        return 2
    for index, case in enumerate(selected, start=1):
        payload = measure(case)
        print(f"[{index}/{len(selected)}] {case}: ok={payload.get('ok')} lines={len(payload.get('lines', []))}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
