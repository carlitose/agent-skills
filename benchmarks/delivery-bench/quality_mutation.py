"""Strength of the arm's own tests: mutation of the source lines one request added (DBH-30).

Mutants are small textual changes (relational, arithmetic and boolean operators, integer
constants, return values, deleted statements) on the executable lines the request added, as the
coverage record (DBH-29) lists them. A fixed seed picks at most ``limit`` of them per unit. A
mutant on a line the tests never execute is counted as survived without running. The others run
the unit's suite in the scenario's image, offline, each in its own copy of the tree:

- killed: the suite fails (with a failing baseline: a named test fails that did not);
- survived: the suite passes (or fails only where the baseline already failed);
- timeout: the suite ran past three times the baseline's time;
- not compiled: the mutated file does not build or parse; excluded from the share.

Score = killed / (killed + survived + timeout). ``covered_score`` is the same share over the
mutants on covered lines only, so test strength reads apart from coverage. A unit whose own suite
already fails without naming the failed tests is ``n/a``: Lua's ``all.lua`` stops at the first one.
"""
from __future__ import annotations

import json
import random
import re
import shutil
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import quality
import quality_coverage as qc

SEED = 30
LIMIT = 8
NOT_COMPILED = 97
SANITIZE = "-fsanitize=address,undefined -fno-sanitize-recover=undefined -g"
# {failfast} is set only on a green baseline.
COMMANDS = {
    "c": ('make -s -C src clean >/dev/null 2>&1; '
          f'make -s -j2 linux MYCFLAGS="{SANITIZE}" MYLDFLAGS="{SANITIZE}" >/tmp/build.log 2>&1 '
          f'|| exit {NOT_COMPILED}; cd testes && ../src/lua -e"_U=true" all.lua'),
    "python": "python -m unittest {failfast}",
    "javascript": "NODE_ENV=development node tests/index.js --repetition-time 50",
}
# A mutant's file must still parse; C finds out at build time, inside its command.
CHECKS = {"python": "python -m py_compile {file}", "javascript": "node --check {file}"}
FAILED_TEST = re.compile(r"^(?:(?:FAIL|ERROR): (\S+ \(\S+\))|Failure: (.+) in [\d.]+\S*s)$", re.MULTILINE)
STRING = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|`(?:\\.|[^`\\])*`')
COMMENT = {"c": re.compile(r"//.*|/\*.*?(\*/|$)"), "javascript": re.compile(r"//.*|/\*.*?(\*/|$)"),
           "python": re.compile(r"#.*")}
SPACED = {" + ": " - ", " - ": " + ", " * ": " / ", " / ": " * "}
RELATIONAL = [(r"===", "!=="), (r"!==", "==="), (r"(?<![=!<>])==(?!=)", "!="), (r"!=(?!=)", "=="),
              (r"<=", "<"), (r">=", ">"), (r"(?<![<\-=])<(?![<=])", "<="), (r"(?<![>\-=])>(?![>=])", ">=")]
BOOLEAN = {"python": [(r"\band\b", "or"), (r"\bor\b", "and"), (r"\bTrue\b", "False"), (r"\bFalse\b", "True"),
                      (r"(?<!\bis )\bnot (?!in\b)", "")],
           "c": [(r"&&", "||"), (r"\|\|", "&&"), (r"!(?!=)", "")],
           "javascript": [(r"&&", "||"), (r"\|\|", "&&"), (r"\btrue\b", "false"), (r"\bfalse\b", "true"),
                          (r"!(?!=)", "")]}
NONE = {"python": "None", "c": "0", "javascript": "undefined"}
BLOCK_START = re.compile(r"^(def|class|if|elif|else|for|while|try|except|finally|with|return|async|@|case|"
                         r"switch|do|break|continue|goto|default|function|export|import|from|const|let|var)\b")


def masked(text: str, language: str) -> str:
    """The line with strings and comments blanked, so operators are only found in code."""
    text = STRING.sub(lambda m: " " * len(m[0]), text)
    return COMMENT[language].sub(lambda m: " " * len(m[0]), text)


def balanced(code: str) -> bool:
    return all(code.count(a) == code.count(b) for a, b in ("()", "[]", "{}"))


def line_mutants(text: str, language: str) -> list[tuple[str, int, str, str]]:
    """Every mutant of one line: (operator, column, original, replacement)."""
    if language == "c" and text.lstrip().startswith("#"):
        return []
    code = masked(text, language)
    found = []
    for old, new in SPACED.items():
        found += [("arithmetic", m.start(), old, new) for m in re.finditer(re.escape(old), code)]
    for pattern, new in RELATIONAL:
        found += [("relational", m.start(), m[0], new) for m in re.finditer(pattern, code)]
    for pattern, new in BOOLEAN[language]:
        found += [("boolean", m.start(), m[0], new) for m in re.finditer(pattern, code)]
    found += [("constant", m.start(), m[0], str(int(m[0]) + 1))
              for m in re.finditer(r"(?<![\w.])\d+(?![\w.])", code)]
    stripped = code.strip()
    if (m := re.match(r"(\s*return\s+)(.+?)(;?\s*)$", code)) and m[2].strip() not in (NONE[language], ""):
        found.append(("return", m.end(1), text[m.start(2):m.end(2)], NONE[language]))
    deletable = (stripped and balanced(stripped) and not BLOCK_START.match(stripped)
                 and (stripped.endswith(";") if language != "python" else not stripped.endswith((":", ",", "\\"))))
    if deletable:
        indent = text[:len(text) - len(text.lstrip())]
        found.append(("delete", len(indent), text.strip(), "pass" if language == "python" else ";"))
    return found


def candidates(work: Path, lines: dict[str, list[int]], language: str) -> list[dict]:
    """Every mutant on the given lines, in a stable order."""
    found = []
    for path, numbers in sorted(lines.items()):
        source = (work / path).read_text(encoding="utf-8", errors="replace").splitlines()
        for number in sorted(numbers):
            if 0 < number <= len(source):
                found += [{"path": path, "line": number, "operator": op, "column": col, "original": old,
                           "mutated": new} for op, col, old, new in line_mutants(source[number - 1], language)]
    return found


def pick(found: list[dict], unit_id: str, limit: int = LIMIT, seed: int = SEED) -> list[dict]:
    """The same seed and unit always give the same mutants."""
    chosen = random.Random(f"{seed}:{unit_id}").sample(found, min(limit, len(found)))
    return sorted(chosen, key=lambda m: (m["path"], m["line"], m["column"], m["operator"]))


def apply(work: Path, mutant: dict) -> None:
    target = work / mutant["path"]
    data = target.read_bytes().decode("utf-8", errors="surrogateescape")
    lines = data.splitlines(keepends=True)
    line, col = lines[mutant["line"] - 1], mutant["column"]
    if line[col:col + len(mutant["original"])] != mutant["original"]:
        raise ValueError(f"mutant does not match {mutant['path']}:{mutant['line']}")
    lines[mutant["line"] - 1] = line[:col] + mutant["mutated"] + line[col + len(mutant["original"]):]
    target.write_bytes("".join(lines).encode("utf-8", errors="surrogateescape"))


def failing(run: dict) -> set[str]:
    return {a or b for a, b in FAILED_TEST.findall(run.get("output", ""))}


def classify(run: dict, baseline: dict) -> str:
    if run.get("timed_out"):
        return "timeout"
    if run["exit"] == NOT_COMPILED:
        return "not compiled"
    if run["exit"] == 0:
        return "survived"
    if baseline["exit"] == 0:
        return "killed"
    return "killed" if failing(run) - failing(baseline) else "survived"


def command(language: str, path: str = "", failfast: bool = False) -> str:
    run = COMMANDS[language].format(failfast="-f" if failfast else "")
    check = CHECKS.get(language) if path else None
    return f"{check.format(file=path)} || exit {NOT_COMPILED}; {run}" if check else run


def run_suite(image: str, script: str, work: Path, timeout: float, scene: dict) -> dict:
    """The coverage runner, keeping the whole output for the Python failure list."""
    run = qc.run_container(image, f"{script} > /work/.dbq-out 2>&1", work, timeout,
                           scene.get("cpus", 2), scene.get("memory", "4g"))
    out = work / ".dbq-out"
    run["output"] = out.read_text(encoding="utf-8", errors="replace") if out.is_file() else ""
    run["tail"] = run["output"][-800:]
    return run


def measure(lot_dir: Path, unit: dict, scene: dict, coverage: dict | None, limit: int = LIMIT, jobs: int = 4,
            runner=run_suite) -> dict:
    language = scene["language"]
    record = {"schema": 1, "measure": "mutation", "unit": unit["unit"], "language": language, "seed": SEED,
              "limit": limit}
    if not unit["code"]:
        return {**record, "status": "n/a", "reason": "no code", "score": None}
    if not coverage or coverage.get("status") != "ok":
        return {**record, "status": "n/a" if coverage and coverage.get("status") == "n/a" else "error",
                "reason": "needs a coverage record with executable lines (run coverage first)", "score": None}
    files = coverage["files"]
    lines = {p: f["covered"] + f["missed"] for p, f in files.items()}
    covered = {(p, n) for p, f in files.items() for n in f["covered"]}
    with tempfile.TemporaryDirectory(prefix="dbq-mut-") as scratch:
        base = quality.materialize(lot_dir, unit, Path(scratch) / "base")
        chosen = pick(candidates(base, lines, language), unit["unit"], limit)
        if not chosen:
            return {**record, "status": "n/a", "reason": "no mutant on the added lines", "score": None, "mutants": []}
        image, ceiling = scene["image"], 2 * scene.get("timeout_seconds", 1200)
        copy = Path(scratch) / "baseline"
        shutil.copytree(base, copy, symlinks=True)
        baseline = runner(image, command(language), copy, ceiling, scene)
        record["baseline"] = {k: baseline.get(k) for k in ("exit", "timed_out", "seconds")}
        if baseline.get("timed_out") or (baseline["exit"] != 0 and not failing(baseline)):
            return {**record, "status": "n/a", "reason": "the unit's own suite fails or hangs without mutants",
                    "score": None, "mutants": chosen, "baseline_tail": baseline.get("tail", "")}
        record["baseline"]["failing"] = sorted(failing(baseline))
        timeout = min(ceiling, max(120.0, 3 * baseline["seconds"]))

        def one(index_mutant):
            index, mutant = index_mutant
            if (mutant["path"], mutant["line"]) not in covered:
                return {**mutant, "result": "survived", "covered": False}
            work = Path(scratch) / f"m{index}"
            shutil.copytree(base, work, symlinks=True)
            apply(work, mutant)
            run = runner(image, command(language, mutant["path"], failfast=baseline["exit"] == 0), work, timeout, scene)
            shutil.rmtree(work, ignore_errors=True)
            return {**mutant, "covered": True, "result": classify(run, baseline), "exit": run["exit"],
                    "seconds": run["seconds"], "tail": run.get("tail", "")[-300:]}

        with ThreadPoolExecutor(max_workers=max(1, jobs)) as pool:
            results = list(pool.map(one, enumerate(chosen)))
    return {**record, **score(results), "mutants": results}


def score(results: list[dict]) -> dict:
    counts = {k: sum(r["result"] == k for r in results) for k in ("killed", "survived", "timeout", "not compiled")}
    counted = counts["killed"] + counts["survived"] + counts["timeout"]
    run = [r for r in results if r["covered"] and r["result"] != "not compiled"]
    if not counted:
        return {"status": "n/a", "reason": "no mutant compiled", "counts": counts, "score": None,
                "covered_score": None}
    return {"status": "ok", "counts": counts, "score": counts["killed"] / counted,
            "covered_score": sum(r["result"] == "killed" for r in run) / len(run) if run else None,
            "survivors": [f"{r['path']}:{r['line']} {r['operator']} {r['original']!r}->{r['mutated']!r}"
                          for r in results if r["result"] == "survived"]}


def coverage_record(lot_dir: Path, unit_id: str) -> dict | None:
    path = Path(lot_dir) / "quality" / "coverage" / f"{unit_id}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None
