"""Blind review of one request's change by Opus 5.5 (DBH-31).

Each review is a fresh ``pi -p`` with no extensions, skills or context files and read-only
tools, in a throwaway copy of the unit's tree under a neutral name. The reviewer gets the
request text and the change (code and tests only: specs, tickets and ``.pi/`` would reveal the
arm) through two files next to the tree, and answers with one JSON object on a fixed rubric.
Arm, lot and cell names are redacted from everything it sees. Cost comes from the review's own
session files, read the way the runner reads an arm's.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import statistics
import subprocess
import tempfile
import time
from pathlib import Path

import quality
import runner

REVIEW_MODEL = "anthropic/claude-opus-5-5"
REVIEW_THINKING = "high"
REVIEW_TOOLS = "read,grep,find,ls"
REVIEW_TIMEOUT = 1800
# Opus is reachable only through the Claude Pro/Max OAuth provider extension; plain Pi is billed
# as a third-party app and refused ("Third-party apps now draw from extra usage").
ANTHROPIC_PACKAGE = "@wierdbytes/pi-anthropic"
PI_SETTINGS = Path.home() / ".pi" / "agent" / "settings.json"
DIFF_CAP = 400_000
HIDDEN = ("docs/specs", "docs/tickets", ".pi")
SCORES = ("correctness", "tests", "design", "readability")
SEVERITIES = ("high", "medium", "low")
REQUEST_FILE, CHANGE_FILE = "REVIEW_REQUEST.md", "REVIEW_CHANGE.diff"
PROMPT = f"""You review one change to the repository in the current directory, as a senior engineer.
Read ../{REQUEST_FILE} (what was asked) and ../{CHANGE_FILE} (the change: code and tests). You may read
any file of the repository to understand the change. Do not modify anything and do not run anything.

Judge only this change against this request. Look for bugs the change introduces or leaves: wrong
results, missed cases the request implies, crashes, edge cases, regressions of existing behavior.
Report only bugs you can point to in the code, with the reason; do not report style as a bug.

Answer with one JSON object and nothing else:
{{"bugs": [{{"severity": "high|medium|low", "file": "path", "line": 0, "why": "one or two sentences"}}],
 "scores": {{"correctness": 1, "tests": 1, "design": 1, "readability": 1}},
 "summary": "two or three sentences"}}
Scores go from 1 (very poor) to 5 (excellent): correctness = how likely the change does what the
request asks without bugs; tests = how well the change's own tests would catch a regression of it;
design = fit with the existing code; readability = how easy it is to follow."""


def anthropic_extension(settings: Path = PI_SETTINGS) -> dict:
    """The installed Anthropic OAuth extension, found among the user's Pi packages, with its digest."""
    override = os.environ.get("DBENCH_ANTHROPIC_EXTENSION")
    candidates = [Path(override)] if override else []
    if not override and settings.is_file():
        for package in json.loads(settings.read_text(encoding="utf-8")).get("packages", []):
            source = package if isinstance(package, str) else package.get("source", "")
            folder = (settings.parent / source).resolve() if source and not source.startswith("npm:") else None
            if folder and (folder / "package.json").is_file():
                candidates.append(folder)
    for folder in candidates:
        manifest = folder / "package.json"
        if manifest.is_file() and json.loads(manifest.read_text(encoding="utf-8")).get("name") == ANTHROPIC_PACKAGE:
            entry = folder / "index.ts"
            digest = hashlib.sha256(b"".join(f.read_bytes() for f in sorted(folder.glob("*.ts")))).hexdigest()
            return {"path": str(entry), "version": json.loads(manifest.read_text(encoding="utf-8"))["version"],
                    "sha256": digest}
    raise FileNotFoundError(f"{ANTHROPIC_PACKAGE} is not among the Pi packages in {settings}")


def blind_terms(unit: dict) -> list[str]:
    """Names that would tell the reviewer which arm wrote the change."""
    terms = {unit["lot"], unit["cell"], unit["arm"], *runner.ARMS}
    return sorted((t for t in terms if "-" in t or "." in t), key=len, reverse=True)


def redact(text: str, terms: list[str]) -> str:
    for term in terms:
        text = re.sub(re.escape(term), "[redacted]", text, flags=re.IGNORECASE)
    return text


def change(lot_dir: Path, unit: dict) -> str:
    excluded = [f":(exclude){path}" for path in (*HIDDEN, "TASK.md")]
    diff = quality.git_read(lot_dir, unit["cell"], ["diff", "--no-color", "--no-ext-diff", unit["base"], unit["tree"],
                                                    "--", ".", *excluded]).decode("utf-8", "replace")
    if len(diff) > DIFF_CAP:
        diff = diff[:DIFF_CAP] + "\n[the change is longer; read the files themselves for the rest]\n"
    return redact(diff, blind_terms(unit))


def parse_review(text: str) -> dict:
    """The reviewer's JSON object, checked against the rubric; ValueError otherwise."""
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("no JSON object")
    value = json.loads(text[start:end + 1])
    bugs, scores = value.get("bugs"), value.get("scores")
    if not isinstance(bugs, list) or not isinstance(scores, dict) or not isinstance(value.get("summary"), str):
        raise ValueError("bugs, scores and summary are required")  # noqa: TRY004 - any malformed answer is one retry
    for bug in bugs:
        if not (isinstance(bug, dict) and bug.get("severity") in SEVERITIES and isinstance(bug.get("file"), str)
                and isinstance(bug.get("line"), int) and isinstance(bug.get("why"), str)):
            raise ValueError(f"bad bug entry: {bug!r}"[:200])
    if set(scores) != set(SCORES) or not all(type(scores[k]) is int and 1 <= scores[k] <= 5 for k in SCORES):
        raise ValueError(f"scores must be {SCORES} from 1 to 5")
    return {"bugs": bugs, "scores": {k: scores[k] for k in SCORES}, "summary": value["summary"]}


def run_pi(pi_command: list[str], tree: Path, sessions: Path, extension: str) -> tuple[str, dict, dict]:
    """One review call: the last assistant text, the session summary and the process outcome."""
    argv = [*pi_command, "-p", "--model", REVIEW_MODEL, "--thinking", REVIEW_THINKING, "--no-extensions",
            "-e", extension, "--no-skills", "--no-context-files", "--tools", REVIEW_TOOLS, "--session-dir", str(sessions),
            "--", PROMPT]
    env = {k: v for k, v in os.environ.items() if k not in runner.STRIPPED_ENV}
    start = time.monotonic()
    try:
        done = subprocess.run(argv, cwd=tree, env=env, capture_output=True, timeout=REVIEW_TIMEOUT, check=False)
        outcome = {"exit": done.returncode, "stderr_tail": done.stderr[-800:].decode("utf-8", "replace")}
    except subprocess.TimeoutExpired:
        outcome = {"exit": None, "timed_out": True}
    outcome["seconds"] = round(time.monotonic() - start, 1)
    events = runner.new_events([sessions], {})
    texts = [c.get("text", "") for e in events if (e.get("message") or {}).get("role") == "assistant"
             for c in e["message"].get("content") or [] if isinstance(c, dict) and c.get("type") == "text"]
    return (texts[-1] if texts else ""), runner.summarize(events), outcome


def review_once(lot_dir: Path, unit: dict, pi_command: list[str], extension: str, call=run_pi) -> dict:
    with tempfile.TemporaryDirectory(prefix="dbq-review-") as scratch:
        root = Path(scratch) / unit["unit"]
        tree = quality.materialize(lot_dir, unit, root / "repo")
        for hidden in HIDDEN:
            shutil.rmtree(tree / hidden, ignore_errors=True)
        task = tree / "TASK.md"
        request = task.read_text(encoding="utf-8", errors="replace") if task.is_file() else "(no TASK.md)"
        (root / REQUEST_FILE).write_bytes(redact(request, blind_terms(unit)).encode("utf-8"))
        (root / CHANGE_FILE).write_bytes(change(lot_dir, unit).encode("utf-8"))
        tries = []
        for attempt in (1, 2):  # an unreadable answer is asked once more, then recorded as an error
            text, summary, outcome = call(pi_command, tree, root / f"sessions-{attempt}", extension)
            entry = {"attempt": attempt, "usage": summary["usage"], **outcome}
            try:
                tries.append({**entry, "status": "ok", "review": parse_review(text)})
                break
            except (ValueError, json.JSONDecodeError) as error:
                reason = (f"pi exit {outcome.get('exit')}: {outcome.get('stderr_tail', '').strip()}"
                          if not text and outcome.get("exit") != 0 else str(error))
                tries.append({**entry, "status": "error", "error": reason[:300], "text_tail": text[-500:]})
    last = tries[-1]
    return {"status": last["status"], "review": last.get("review"), "tries": tries,
            "cost_usd": round(sum(t["usage"]["cost_usd"] for t in tries), 6)}


def measure(lot_dir: Path, unit: dict, reviews: int = 1, call=run_pi, extension: dict | None = None) -> dict:
    record = {"schema": 1, "measure": "review", "unit": unit["unit"], "model": REVIEW_MODEL,
              "thinking": REVIEW_THINKING}
    if not unit["code"]:
        return {**record, "status": "n/a", "reason": "no code", "score": None, "reviews": []}
    pi_command = json.loads((Path(lot_dir) / "lot.json").read_text(encoding="utf-8"))["pi_command"]
    extension = extension or anthropic_extension()
    record["extension"] = extension
    done = [review_once(lot_dir, unit, pi_command, extension["path"], call) for _ in range(reviews)]
    good = [r["review"] for r in done if r["status"] == "ok"]
    means = [sum(r["scores"].values()) / len(SCORES) for r in good]
    return {**record, "status": "ok" if good else "error", "reviews": done,
            "score": statistics.median(means) if means else None,  # the pilot rule: median of the reviews
            "cost_usd": round(sum(r["cost_usd"] for r in done), 6)}
