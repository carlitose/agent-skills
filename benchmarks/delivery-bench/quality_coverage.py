"""Coverage of the arm's own tests over the source lines one request added (DBH-29).

The unit's tree runs its own test suite in the scenario's image, offline, with the scenario's
CPU and memory limits, in a throwaway copy. Only lines the request added to source files
(not tests, docs, specs or tickets) count:

- C (lua-vm): built with ``--coverage -O0``, the suite of ``testes/``, then ``gcov -j``;
  executable lines are the ones gcov lists.
- Python (sql-engine): ``coverage run --source=. -m unittest`` in an image derived from the
  scenario's with ``coverage`` pinned; executable lines are coverage.py's.
- JavaScript (crdt-yjs): ``node tests/index.js`` straight from ``src/`` (the tests are ESM and
  import ``../src``), under ``NODE_V8_COVERAGE``; a line is covered when the innermost V8 range
  around its first character ran. Executable lines are a heuristic: not blank, not a comment,
  not only brackets.

A failing suite still yields coverage: the share says what the arm's tests executed, not
whether they passed (that is the official verdict).
"""
from __future__ import annotations

import gzip
import json
import re
import subprocess
import tempfile
import time
import uuid
from pathlib import Path

import quality

COVERAGE_VERSION = "7.16.2"
RAW = ".dbq-coverage"
TEST_DIRS = {"test", "tests", "testes", "__tests__"}
SKIP_DIRS = {"docs", ".pi", "dist", "node_modules", ".git"}
SUFFIXES = {"c": (".c",), "python": (".py",), "javascript": (".js", ".mjs", ".cjs")}
TEST_FILE = re.compile(r"(^test_.*\.py$|_test\.py$|\.tests?\.[cm]?js$)")
COMMANDS = {
    "c": ('make -s -C src clean >/dev/null 2>&1; make -s linux MYCFLAGS="--coverage -O0 -g" '
          'MYLDFLAGS="--coverage" && (cd testes && ../src/lua -e"_U=true" all.lua); status=$?; '
          f'mkdir -p /work/{RAW} && cd src && gcov -j -o . *.c >/dev/null 2>&1; '
          f'mv *.gcov.json.gz /work/{RAW}/ 2>/dev/null; exit $status'),
    "python": ("coverage run --source=. --data-file=/tmp/dbq.cov -m unittest; status=$?; "
               f"mkdir -p /work/{RAW}; coverage json -q --data-file=/tmp/dbq.cov -o /work/{RAW}/coverage.json; "
               "exit $status"),
    "javascript": f"NODE_ENV=development NODE_V8_COVERAGE=/work/{RAW} node tests/index.js --repetition-time 50",
}
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
NOT_CODE = re.compile(r"^[\s{}()\[\];,]*$")


def is_source(path: str, language: str) -> bool:
    parts = path.split("/")
    return (path.endswith(SUFFIXES[language]) and not set(parts[:-1]) & (TEST_DIRS | SKIP_DIRS)
            and not TEST_FILE.search(parts[-1]))


def parse_added(diff: str, language: str) -> dict[str, list[int]]:
    """New-side line numbers of every added line, per source file, from a ``-U0`` diff."""
    added, path = {}, None
    for line in diff.splitlines():
        if line.startswith("+++ "):
            name = line[4:]
            path = name[2:] if name.startswith("b/") and is_source(name[2:], language) else None
        elif path and (match := HUNK.match(line)):
            start, count = int(match[1]), int(match[2] if match[2] is not None else 1)
            added.setdefault(path, []).extend(range(start, start + count))
    return {path: lines for path, lines in added.items() if lines}


def added_lines(lot_dir: Path, unit: dict, language: str) -> dict[str, list[int]]:
    diff = quality.git_read(lot_dir, unit["cell"], ["diff", "-U0", "--no-color", "--no-renames", "--no-ext-diff",
                                                     unit["base"], unit["tree"]])
    return parse_added(diff.decode("utf-8", "replace"), language)


def read_c(raw: Path, work: Path, added: dict) -> dict[str, tuple[set, set]]:
    seen: dict[str, tuple[set, set]] = {}
    for report in sorted(raw.glob("*.gcov.json.gz")):
        for entry in json.loads(gzip.decompress(report.read_bytes())).get("files", []):
            name = entry["file"]
            path = name[len("/work/"):] if name.startswith("/work/") else f"src/{name}"
            executable, covered = seen.setdefault(path, (set(), set()))
            for line in entry.get("lines", []):
                executable.add(line["line_number"])
                if line.get("count", 0) > 0:
                    covered.add(line["line_number"])
    return seen


def read_python(raw: Path, work: Path, added: dict) -> dict[str, tuple[set, set]]:
    report = raw / "coverage.json"
    if not report.is_file():
        return {}
    seen = {}
    for name, entry in json.loads(report.read_text(encoding="utf-8")).get("files", {}).items():
        path = name.replace("\\", "/").removeprefix("/work/").removeprefix("./")
        executed = set(entry.get("executed_lines", []))
        seen[path] = (executed | set(entry.get("missing_lines", [])), executed)
    return seen


def _utf16(text: str) -> int:
    return len(text.encode("utf-16-le")) // 2


def read_javascript(raw: Path, work: Path, added: dict) -> dict[str, tuple[set, set]]:
    """V8 block coverage turned into lines; offsets are UTF-16 units of the source text."""
    ranges: dict[str, list[dict]] = {}
    for report in sorted(raw.glob("coverage-*.json")):
        for script in json.loads(report.read_text(encoding="utf-8")).get("result", []):
            url = script.get("url", "")
            if url.startswith("file:///work/"):
                ranges.setdefault(url[len("file:///work/"):], []).append(
                    [r for function in script.get("functions", []) for r in function.get("ranges", [])])
    if not ranges:
        return {}
    seen = {}
    for path, lines in added.items():
        source = work / path
        if not source.is_file():
            continue
        text = source.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
        executable, covered, offset, wanted = set(), set(), 0, set(lines)
        for number, line in enumerate(text, 1):
            stripped = line.strip()
            if number in wanted and stripped and not stripped.startswith(("//", "/*", "*")) \
                    and not NOT_CODE.match(stripped):
                executable.add(number)
                at = offset + _utf16(line[:len(line) - len(line.lstrip())])
                for run in ranges.get(path, []):  # one list per process; covered in any counts
                    inside = [r for r in run if r["startOffset"] <= at < r["endOffset"]]
                    if inside and min(inside, key=lambda r: r["endOffset"] - r["startOffset"])["count"] > 0:
                        covered.add(number)
                        break
            offset += _utf16(line)
        seen[path] = (executable, covered)
    return seen


READERS = {"c": read_c, "python": read_python, "javascript": read_javascript}


def coverage_image(scenario: dict) -> str:
    """The image the suite runs in; Python needs coverage.py, built once from the scenario's."""
    if scenario["language"] != "python":
        return scenario["image"]
    tag = f"{scenario['image'].split(':')[0]}-coverage:{COVERAGE_VERSION}"
    if subprocess.run(["docker", "image", "inspect", tag], capture_output=True, check=False).returncode:
        dockerfile = f"FROM {scenario['image']}\nRUN pip install --no-cache-dir coverage=={COVERAGE_VERSION}\n"
        subprocess.run(["docker", "build", "-q", "-t", tag, "-"], input=dockerfile.encode(), check=True,
                       capture_output=True)
    return tag


def run_container(image: str, command: str, work: Path, timeout: float, cpus=2, memory="4g") -> dict:
    name = f"dbq-{uuid.uuid4().hex[:12]}"
    argv = ["docker", "run", "--rm", "--name", name, "--network", "none", "--cpus", str(cpus), "--memory", memory,
            "-e", "ASAN_OPTIONS=detect_leaks=0", "--mount", f"type=bind,source={Path(work).resolve()},target=/work",
            "-w", "/work", image, "sh", "-c", command]
    start = time.monotonic()
    try:
        done = subprocess.run(argv, capture_output=True, timeout=timeout, check=False)
    except subprocess.TimeoutExpired:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True, check=False)
        return {"exit": None, "timed_out": True, "seconds": round(time.monotonic() - start, 1), "tail": ""}
    return {"exit": done.returncode, "timed_out": False, "seconds": round(time.monotonic() - start, 1),
            "tail": (done.stdout + done.stderr)[-1500:].decode("utf-8", "replace")}


def summarize(record: dict, added: dict, seen: dict) -> dict:
    files, unmeasured = {}, []
    for path, lines in sorted(added.items()):
        if path not in seen:
            unmeasured.append(path)
            continue
        executable, covered = seen[path]
        exe = sorted(set(lines) & executable)
        files[path] = {"added": len(lines), "executable": len(exe), "covered": sorted(set(exe) & covered),
                       "missed": sorted(set(exe) - covered)}
    executable = sum(f["executable"] for f in files.values())
    covered = sum(len(f["covered"]) for f in files.values())
    record.update(added=sum(map(len, added.values())), executable=executable, covered=covered,
                  files=files, unmeasured=unmeasured)
    if not seen:
        return {**record, "status": "error", "reason": "no coverage data", "score": None}
    if not executable:
        return {**record, "status": "n/a", "reason": "no executable added line was measured", "score": None}
    return {**record, "status": "ok", "score": covered / executable}


def measure(lot_dir: Path, unit: dict, scene: dict, runner=run_container) -> dict:
    language = scene["language"]
    record = {"schema": 1, "measure": "coverage", "unit": unit["unit"], "language": language}
    if not unit["code"]:
        return {**record, "status": "n/a", "reason": "no code", "score": None}
    added = added_lines(lot_dir, unit, language)
    if not added:
        return {**record, "status": "n/a", "reason": "no source line added", "score": None, "added": 0}
    image = coverage_image(scene)
    with tempfile.TemporaryDirectory(prefix="dbq-cov-") as scratch:
        work = quality.materialize(lot_dir, unit, Path(scratch) / "work")
        run = runner(image, COMMANDS[language], work, 2 * scene.get("timeout_seconds", 1200),
                     scene.get("cpus", 2), scene.get("memory", "4g"))
        seen = READERS[language](work / RAW, work, added)
    return summarize({**record, "image": image, "run": run}, added, seen)
