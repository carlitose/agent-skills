"""delivery-bench runner: hand one arm a scenario's requests in order and judge every delivery.

    python -B runner.py init-lot --lot DIR --lot-id ID --authority FILE --scenario NAME=PATH ...
                                 --arm ARM ... --repetitions R [--runs-root DIR] [--arms-root DIR]
                                 [--jev-key-file FILE]
    python -B runner.py prepare-drivers --lot DIR
    python -B runner.py run --lot DIR --cell CELL --through L
    python -B runner.py run-lot --lot DIR --through L [--jobs 4]
    python -B runner.py status --lot DIR

A lot directory holds judge records that name hidden checks: it lives outside Git (or in an
ignored folder of the private oracle repo) and outside the runs root the arms work in. Each cell
is one arm x scenario x repetition; its working folder is ``<runs-root>/<lot>/<token>/<arm>/``
with ``project/`` (the only judged tree), a bare ``origin.git`` and the arm's sessions. A cell is
extended, never replayed: ``run --through 3`` after ``--through 1`` delivers requests 2 and 3.
Protocol: docs/research/delivery-bench-oracle-contract.md.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import secrets
import shutil
import stat
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "ticket-autopilot" / "scripts"))
from autopilot.command_capture import CaptureFailure, capture_command

import judge

PROVIDER, MODEL, THINKING = "openai-codex", "gpt-6-sol", "high"
PROMPT = ("Lee TASK.md en la raiz del repositorio y haz lo que pide, hasta el final. "
          "Trabaja solo en este directorio. Lo que cuenta es el estado de esta carpeta cuando termines.")
SKILLS_ONLY_SUFFIX = (" Trabaja en modo skills-only: usa las skills instaladas de forma inline y no "
                      "arranques el runner, el scheduler ni ningun driver de Autopilot.")
AUTOPILOT_SUFFIX = (" Usa el flujo completo de ticket-autopilot, incluido su runner, para llevar este "
                    "trabajo de principio a fin. `origin` es un repositorio local sin proveedor de PR: "
                    "usa el runner con `--provider github --provider-mode simulated`; cuando el runner "
                    "no pueda fusionar, integra tú la rama en `main` de esta carpeta.")
ARMS = ("bare", "skills-only", "autopilot", "driver-c1a", "driver-c3a")
PI_ARMS = {"bare": (["--no-skills"], ""), "skills-only": ([], SKILLS_ONLY_SUFFIX),
           "autopilot": ([], AUTOPILOT_SUFFIX)}
# The global settings disable compaction; a chain of 8 in one session needs it (contract §6).
PI_SETTINGS = {"compaction": {"enabled": True, "reserveTokens": 65536}}
REQUEST_CAP_SECONDS = 3600
MAX_INFRA_RETRIES = 2
JUDGE_ATTEMPTS = 3
JUDGE_BACKOFF_SECONDS = 5.0
JEV_USD_PER_INPUT_TOKEN = 0.042e-6  # published input rate; output is free; an estimate, not a bill
OUTPUT_LIMIT = 16 * 1024 * 1024
BENCH = ["-c", "user.name=bench", "-c", "user.email=bench@example.invalid"]
STRIPPED_ENV = ("TYPESAFE_API_KEY", "PI_CODING_AGENT", "PI_CODING_AGENT_SESSION_DIR",
                "TICKET_DRIVER_PI_EXTENSION")
PROVIDER_ERROR = re.compile(
    r"websocket closed|econnreset|socket hang up|connection (reset|closed|refused)|"
    r"\b5\d\d\b|service unavailable|overloaded|bad gateway|gateway timeout|rate limit|\b429\b",
    re.IGNORECASE)
LOT_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,40}$")
USAGE_KEYS = ("input", "output", "cacheRead", "cacheWrite", "totalTokens")


class LotError(ValueError):
    """The lot, its authority or the requested cell cannot be run as asked."""


# --- small helpers ---------------------------------------------------------------------------

def now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                         encoding="utf-8")
    os.replace(temporary, path)


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                          check=check, timeout=300)


def _force_remove(function, path, _info) -> None:
    os.chmod(path, stat.S_IWRITE)
    function(path)


def rmtree(path: Path) -> None:
    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=_force_remove)
    else:  # pragma: no cover
        shutil.rmtree(path, onerror=_force_remove)


def inside_git(path: Path) -> bool:
    """True when path would be tracked by some Git work tree (ignored folders do not count)."""
    probe = Path(path)
    while not probe.exists():
        probe = probe.parent
    if git(probe if probe.is_dir() else probe.parent, "rev-parse", "--show-toplevel",
           check=False).returncode != 0:
        return False
    base = probe if probe.is_dir() else probe.parent
    return git(base, "check-ignore", "-q", str(Path(path).resolve()), check=False).returncode != 0


def read_jev_key(path: Path) -> str:
    """One raw token or one TYPESAFE_API_KEY assignment; never logged, only injected."""
    lines = [row.strip() for row in Path(path).read_text(encoding="utf-8-sig").splitlines()
             if row.strip() and not row.lstrip().startswith("#")]
    if len(lines) != 1:
        raise LotError("the Jev key file must hold exactly one credential")
    value = lines[0].split("=", 1)[1].strip().strip("'\"") if lines[0].startswith(
        "TYPESAFE_API_KEY=") else lines[0]
    if not (16 <= len(value) <= 2048 and value.isascii() and value.isprintable()
            and not any(char.isspace() for char in value)):
        raise LotError("the Jev key has an invalid shape")
    return value


def _alive(pid: int) -> bool:
    if os.name == "nt":
        import ctypes
        kernel = ctypes.WinDLL("kernel32")
        handle = kernel.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            return False
        code = ctypes.c_ulong()
        kernel.GetExitCodeProcess(handle, ctypes.byref(code))
        kernel.CloseHandle(handle)
        return code.value == 259  # STILL_ACTIVE
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


@contextmanager
def cell_lock(directory: Path):
    directory.mkdir(parents=True, exist_ok=True)
    lock = directory / "lock"
    try:
        handle = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        owner = lock.read_text(encoding="utf-8").strip()
        if owner.isdigit() and _alive(int(owner)):
            raise LotError(f"cell is already running in process {owner}") from None
        lock.unlink()
        handle = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.write(handle, str(os.getpid()).encode())
    os.close(handle)
    try:
        yield
    finally:
        lock.unlink(missing_ok=True)


@contextmanager
def environment(values: dict):
    """capture_command passes the process environment on; one cell runs per process."""
    saved = dict(os.environ)
    os.environ.clear()
    os.environ.update(values)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(saved)


# --- lot -------------------------------------------------------------------------------------

def resolve_pi() -> list[str]:
    sys.path.insert(0, str(ROOT / "ticket-driver" / "scripts"))
    from leaf import pi_command  # the driver's own native resolution of the npm shim
    return pi_command()


def _authority(path: Path) -> dict:
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    required = {"schema", "lot", "authorized_by", "statement", "arms", "scenarios",
                "repetitions", "max_length"}
    if not isinstance(document, dict) or document.get("schema") != 1 or not required <= set(document):
        raise LotError("authority file lacks schema 1 fields")
    return document


def init_lot(lot_dir: Path, *, lot_id: str, authority: Path, scenarios: dict, arms: list,
             repetitions: int, runs_root: Path, arms_root: Path | None = None,
             request_cap_seconds: int = REQUEST_CAP_SECONDS, chain_cap_seconds: int | None = None,
             jev_key_file: Path | None = None, pi_command: list | None = None,
             driver_command: list | None = None) -> dict:
    lot_dir, runs_root = Path(lot_dir).resolve(), Path(runs_root).resolve()
    if not LOT_ID.match(lot_id) or "delivery-bench" in lot_id:
        raise LotError("lot id must be short lowercase words and must not name the benchmark")
    if lot_dir.exists() and any(lot_dir.iterdir()):
        raise LotError("lot directory already exists: inspect it instead of replacing it")
    if (lot_dir.is_relative_to(runs_root) or runs_root.is_relative_to(lot_dir)
            or lot_dir.is_relative_to(ROOT) or inside_git(lot_dir)):
        raise LotError("the lot must stay outside Git and apart from the runs root")
    grant = _authority(authority)
    if grant["lot"] != lot_id or not set(arms) <= set(grant["arms"]) or not set(arms) <= set(ARMS):
        raise LotError("authority does not cover this lot and these arms")
    if not set(scenarios) <= set(grant["scenarios"]) or repetitions > grant["repetitions"]:
        raise LotError("authority does not cover these scenarios and repetitions")
    if "driver-c3a" in arms and not (grant.get("jev_spend_authorized") is True and jev_key_file):
        raise LotError("driver-c3a needs Jev spend authorization and a key file")
    arms_root = Path(arms_root).resolve() if arms_root else runs_root.parent / "arms"
    described = {}
    for name, path in scenarios.items():
        path = Path(path).resolve()
        document = judge.load_scenario(path)
        if document["id"] != name or not document.get("canary") or path.is_relative_to(runs_root):
            raise LotError(f"scenario {name} is not usable (id, canary or location)")
        described[name] = {
            "path": str(path), "requests": document["requests"],
            "language": document.get("language", ""), "canary": document["canary"],
            "suite_sha256": judge.tree_digest(path / "hidden")["sha256"],
            "seed_sha256": judge.tree_digest(path / "seed")["sha256"],
            "driver": list(driver_command) if driver_command else [
                sys.executable, "-B", str(arms_root / name / "ticket-driver" / "scripts" / "ticket_driver.py")],
        }
    cells = {}
    for name in scenarios:
        for rep in range(1, repetitions + 1):
            for arm in arms:
                token = secrets.token_hex(5)
                cells[f"{name}.{arm}.r{rep}"] = {
                    "scenario": name, "arm": arm, "rep": rep, "token": token,
                    "arm_dir": str(runs_root / lot_id / token / arm)}
    lot = {"schema": 1, "lot": lot_id, "created": now(),
           "authority": {"path": str(Path(authority).resolve()), "sha256": sha256_file(authority)},
           "provider": PROVIDER, "model": MODEL, "thinking": THINKING, "arms": list(arms),
           "repetitions": repetitions, "runs_root": str(runs_root), "arms_root": str(arms_root),
           "request_cap_seconds": request_cap_seconds, "chain_cap_seconds": chain_cap_seconds,
           "jev_key_file": str(Path(jev_key_file).resolve()) if jev_key_file else None,
           "pi_command": list(pi_command) if pi_command else resolve_pi(),
           "scenarios": described, "cells": cells, "driver_copies": {}}
    dump(lot_dir / "lot.json", lot)
    return lot


def load_lot(lot_dir: Path) -> dict:
    lot_dir = Path(lot_dir).resolve()
    lot = json.loads((lot_dir / "lot.json").read_text(encoding="utf-8"))
    authority = Path(lot["authority"]["path"])
    if not authority.is_file() or sha256_file(authority) != lot["authority"]["sha256"]:
        raise LotError("the human authority changed or disappeared after the lot was bound")
    for name, scenario in lot["scenarios"].items():
        path = Path(scenario["path"])
        if (judge.tree_digest(path / "hidden")["sha256"] != scenario["suite_sha256"]
                or judge.tree_digest(path / "seed")["sha256"] != scenario["seed_sha256"]):
            raise LotError(f"scenario {name} changed after the lot was bound")
    lot["dir"] = str(lot_dir)
    lot["grant"] = _authority(authority)
    return lot


def ledger(lot: dict, **event) -> None:
    line = json.dumps({"at": now(), **event}, sort_keys=True) + "\n"
    with open(Path(lot["dir"]) / "ledger.jsonl", "a", encoding="utf-8") as handle:
        handle.write(line)


# --- cell setup and delivery -----------------------------------------------------------------

def driver_test_command(language: str) -> list[str]:
    if language == "c":
        return ["python", "dev.py", "test"]
    if language == "typescript":
        return ["cmd", "/c", "npm", "test"] if os.name == "nt" else ["npm", "test"]
    return ["python", "-B", "-m", "unittest", "discover", "-s", "tests", "-t", "."]


def setup_cell(lot: dict, info: dict) -> None:
    arm_dir = Path(info["arm_dir"])
    project, scenario = arm_dir / "project", lot["scenarios"][info["scenario"]]
    if (project / ".git").exists():
        return
    if arm_dir.exists():
        rmtree(arm_dir)  # a setup interrupted before its seed commit leaves nothing worth keeping
    arm_dir.mkdir(parents=True)
    shutil.copytree(Path(scenario["path"]) / "seed", project,
                    ignore=shutil.ignore_patterns("node_modules", "__pycache__", "dist"))
    git(project, "init", "-q", "-b", "main")
    git(project, "config", "core.autocrlf", "false")
    if info["arm"] in PI_ARMS:
        with open(project / ".git" / "info" / "exclude", "a", encoding="utf-8") as exclude:
            exclude.write(".pi/\n")
        dump(project / ".pi" / "settings.json", PI_SETTINGS)
    git(project, "add", "-A")
    git(project, *BENCH, "commit", "-q", "--no-verify", "-m", "seed")
    git(arm_dir, "init", "-q", "--bare", "-b", "main", "origin.git")
    git(project, "remote", "add", "origin", str((arm_dir / "origin.git").resolve()))
    git(project, "push", "-q", "-u", "origin", "main")
    if info["arm"].startswith("driver-"):
        candidate = info["arm"].split("-", 1)[1]
        dump(arm_dir / "driver-authorization.json", {
            "schema": 1, "batch_id": f"{lot['lot']}-{info['token']}",
            "repository": str(project.resolve()), "candidates": [candidate],
            "jev_spend_authorized": candidate == "c3a" and lot["grant"].get("jev_spend_authorized") is True,
            "authority_sha256": lot["authority"]["sha256"]})
    if scenario["language"] == "typescript":
        seed = Path(scenario["path"]) / "seed"
        for name in ("package.json", "package-lock.json"):
            shutil.copyfile(seed / name, arm_dir / name)
        npm = ["cmd", "/c", "npm"] if os.name == "nt" else ["npm"]
        subprocess.run([*npm, "ci", "--no-audit", "--no-fund", "--loglevel=error"], cwd=arm_dir,
                       check=True, capture_output=True, timeout=900)
        for name in ("package.json", "package-lock.json"):
            (arm_dir / name).unlink()


def request_text(scenario: dict, n: int) -> bytes:
    raw = (Path(scenario["path"]) / "requests" / f"{n:02d}.md").read_text(encoding="utf-8")
    text = "".join(line for line in raw.splitlines(keepends=True) if scenario["canary"] not in line)
    if "dbench-canary" in text:
        raise LotError("a request still carries a canary after stripping")
    return text.encode("utf-8")


def deliver_task(project: Path, text: bytes, n: int) -> dict:
    stale = project / ".git" / "index.lock"
    removed_lock = stale.exists()
    if removed_lock:  # the arm's process tree is gone; nothing else can own it
        stale.unlink()
    (project / "TASK.md").write_bytes(text)
    git(project, "add", "-f", "--", "TASK.md")
    git(project, *BENCH, "commit", "-q", "--no-verify", "-m", f"TASK {n}", "--", "TASK.md")
    pushed = git(project, "push", "-q", "origin", "HEAD:main", check=False).returncode == 0
    branch = git(project, "symbolic-ref", "--short", "-q", "HEAD", check=False).stdout.strip()
    return {"commit": git(project, "rev-parse", "HEAD").stdout.strip(), "branch": branch or None,
            "pushed": pushed, "removed_index_lock": removed_lock}


def snapshot(arm_dir: Path, target: Path) -> None:
    if target.exists():
        rmtree(target)
    shutil.copytree(arm_dir, target, symlinks=True,
                    ignore=lambda folder, names: ["node_modules"] if Path(folder) == arm_dir else [])


def restore(target: Path, arm_dir: Path) -> None:
    for child in arm_dir.iterdir():
        if child.name == "node_modules":
            continue
        rmtree(child) if child.is_dir() and not child.is_symlink() else child.unlink()
    shutil.copytree(target, arm_dir, symlinks=True, dirs_exist_ok=True)


# --- one attempt -----------------------------------------------------------------------------

def arm_argv(lot: dict, info: dict, n: int) -> list[str]:
    arm_dir = Path(info["arm_dir"])
    project = (arm_dir / "project").resolve()
    if info["arm"] in PI_ARMS:
        options, suffix = PI_ARMS[info["arm"]]
        argv = [*lot["pi_command"], "-p", "--provider", PROVIDER, "--model", MODEL,
                "--thinking", THINKING, "--no-extensions", "--no-context-files", "--approve",
                *options, "--session-dir", str(arm_dir / "sessions")]
        return [*argv, *(["--continue"] if n > 1 else []), "--", PROMPT + suffix]
    return [*lot["scenarios"][info["scenario"]]["driver"], "run",
            "--candidate", info["arm"].split("-", 1)[1], "--task", str(project / "TASK.md"),
            "--repo", str(project), "--live-authorization",
            str((arm_dir / "driver-authorization.json").resolve())]


def arm_environment(lot: dict, arm: str) -> dict:
    env = {key: value for key, value in os.environ.items() if key not in STRIPPED_ENV}
    if arm == "driver-c3a":
        env["TYPESAFE_API_KEY"] = read_jev_key(Path(lot["jev_key_file"]))
    return env


def session_roots(arm_dir: Path) -> list[Path]:
    return [arm_dir / "sessions", arm_dir / "project" / ".git" / "ticket-driver" / "runs"]


def cursor(roots: list[Path]) -> dict:
    return {str(path): path.stat().st_size for root in roots if root.is_dir()
            for path in root.rglob("*.jsonl")}


def new_events(roots: list[Path], before: dict) -> list[dict]:
    events = []
    for path, size in sorted(cursor(roots).items()):
        start = before.get(path, 0)
        if size <= start:
            continue
        with open(path, "rb") as handle:
            handle.seek(start)
            chunk = handle.read(size - start).decode("utf-8", "replace")
        for line in chunk.splitlines():
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if isinstance(event, dict):
                events.append(event)
    return events


def _timestamp(value) -> float | None:
    if isinstance(value, str):
        try:
            return datetime.datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
        except ValueError:
            return None
    return None


def summarize(events: list[dict]) -> dict:
    usage = {key: 0 for key in USAGE_KEYS} | {"cost_usd": 0.0}
    assistant = with_output = tool_calls = 0
    last, last_ts = {}, None
    for event in events:
        stamp = _timestamp(event.get("timestamp"))
        if stamp is not None:
            last_ts = stamp if last_ts is None else max(last_ts, stamp)
        message = event.get("message")
        if not isinstance(message, dict) or message.get("role") != "assistant":
            continue
        assistant += 1
        last = message
        value = message.get("usage") if isinstance(message.get("usage"), dict) else {}
        for key in USAGE_KEYS:
            if isinstance(value.get(key), (int, float)):
                usage[key] += value[key]
        cost = value.get("cost")
        if isinstance(cost, dict) and isinstance(cost.get("total"), (int, float)):
            usage["cost_usd"] += cost["total"]
        content = [c for c in (message.get("content") or []) if isinstance(c, dict)]
        calls = sum(1 for c in content if c.get("type") in ("toolCall", "tool_use"))
        tool_calls += calls
        if calls or any(c.get("type") == "text" and str(c.get("text", "")).strip() for c in content):
            with_output += 1
    usage["cost_usd"] = round(usage["cost_usd"], 6)
    return {"usage": usage, "assistant_messages": assistant, "with_output": with_output,
            "tool_calls": tool_calls, "last_stop": last.get("stopReason"),
            "last_error": str(last.get("errorMessage") or "")[:300], "last_ts": last_ts}


def classify(code: int | None, failure: str | None, summary: dict) -> str:
    """An agent's own outcome counts; a failure before the agent could work is repeated."""
    if failure == "timeout":
        return "agent"
    if failure is not None:
        return "infra:harness"
    if (summary["with_output"] == 0 and summary["last_stop"] == "error"
            and PROVIDER_ERROR.search(summary["last_error"])):
        return "infra:provider"
    if code != 0 and summary["tool_calls"] == 0:
        return "infra:pi-crash"
    return "agent"


def driver_runs(project: Path) -> set[str]:
    runs = project / ".git" / "ticket-driver" / "runs"
    return {path.name for path in runs.iterdir() if path.is_dir()} if runs.is_dir() else set()


def driver_facts(project: Path, names: list[str]) -> tuple[dict, dict]:
    jev = {"calls": 0, "input_tokens": 0, "output_tokens": 0}
    facts = {"runs": names, "status": [], "failure": []}
    for name in names:
        path = project / ".git" / "ticket-driver" / "runs" / name / "summary.json"
        summary = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
        facts["status"].append(summary.get("status", "no-summary"))
        facts["failure"].append(summary.get("failure"))
        for key in jev:
            jev[key] += int((summary.get("jev_usage") or {}).get(key, 0) or 0)
    jev["usd_estimate"] = round(jev["input_tokens"] * JEV_USD_PER_INPUT_TOKEN, 6)
    return facts, jev


def run_attempt(lot: dict, info: dict, n: int, number: int, timeout: float, logs: Path) -> dict:
    arm_dir = Path(info["arm_dir"])
    project = arm_dir / "project"
    roots, runs_before = session_roots(arm_dir), driver_runs(project)
    before = cursor(roots)
    argv, env = arm_argv(lot, info, n), arm_environment(lot, info["arm"])
    started, clock = time.time(), time.monotonic()
    code, failure, out, err = None, None, b"", b""
    try:
        with environment(env):
            out, err, code = capture_command(argv, cwd=project, timeout_seconds=timeout,
                                             max_output_bytes=OUTPUT_LIMIT)
    except CaptureFailure as error:
        failure, err = error.reason, error.stderr + f"\n[runner] {error.reason}: {error}".encode()
    wall = round(time.monotonic() - clock, 3)
    logs.mkdir(parents=True, exist_ok=True)
    (logs / f"{n:02d}-a{number}.out.txt").write_bytes(out[-200000:])
    (logs / f"{n:02d}-a{number}.err.txt").write_bytes(err[-200000:])
    summary = summarize(new_events(roots, before))
    facts, jev = driver_facts(project, sorted(driver_runs(project) - runs_before))
    last = summary.pop("last_ts")
    seconds = round(last - started, 3) if last is not None and started <= last <= started + wall + 1 else wall
    return {"attempt": number, "class": classify(code, failure, summary), "exit": code,
            "failure": failure, "timeout_seconds": round(timeout, 3), "wall_seconds": wall,
            "seconds": seconds, **summary, "jev": jev,
            **({"driver": facts} if info["arm"].startswith("driver-") else {})}


# --- audit -----------------------------------------------------------------------------------

def audit(lot: dict, info: dict) -> list[dict]:
    """Find hidden material or other cells in anything the arm wrote or read back."""
    arm_dir = Path(info["arm_dir"])
    canaries = [s["canary"].lower() for s in lot["scenarios"].values()]
    others = {c["token"] for c in lot["cells"].values()} - {info["token"]}
    token = re.compile(r"runs/" + re.escape(lot["lot"]) + r"/([0-9a-f]{10})")
    hits = []
    for folder, subdirs, files in os.walk(arm_dir):
        subdirs[:] = [d for d in subdirs if d != "node_modules"
                      and not (d == "objects" and Path(folder).name == ".git")]
        for name in files:
            path = Path(folder) / name
            try:
                if path.stat().st_size > 32 * 1024 * 1024:
                    continue
                text = path.read_bytes().decode("utf-8", "replace").lower()
            except OSError:
                continue
            text = text.replace("\\\\", "/").replace("\\", "/")
            found = [kind for kind, needle in (("private-path", "dbench-private"), ("map", "delivery-bench"))
                     if needle in text]
            found += ["canary"] if any(c in text for c in canaries) else []
            found += ["cross-cell"] if any(m in others for m in token.findall(text)) else []
            hits += [{"pattern": kind, "file": path.relative_to(arm_dir).as_posix()} for kind in found]
    return hits


# --- the chain -------------------------------------------------------------------------------

def _sum_usage(attempts: list[dict]) -> dict:
    total = {key: 0 for key in USAGE_KEYS} | {"cost_usd": 0.0}
    for attempt in attempts:
        for key in total:
            total[key] += attempt.get("usage", {}).get(key, 0)
    total["cost_usd"] = round(total["cost_usd"], 6)
    return total


def _undelivered(n: int) -> dict:
    return {"request": n, "status": "not-delivered", "attempts": [], "timed_out": False,
            "axes": {"acceptance": {"passed": 0, "total": 0, "failed": [], "accepted": False},
                     "robustness": None, "compass": None}}


def _judge(lot: dict, info: dict, n: int, judge_fn, cell_dir: Path) -> dict:
    scenario = Path(lot["scenarios"][info["scenario"]]["path"])
    project = Path(info["arm_dir"]) / "project"
    errors = []
    for attempt in range(1, JUDGE_ATTEMPTS + 1):
        try:
            record = judge_fn(project, scenario, n)
        except judge.JudgeError as error:
            errors.append(str(error)[:300])
            time.sleep(JUDGE_BACKOFF_SECONDS * attempt)
            continue
        path = cell_dir / "judge" / f"{n:02d}.json"
        dump(path, record)
        return {"status": "judged", "axes": record["axes"], "judge": {
            "path": str(path), "attempts": attempt, "errors": errors,
            "suite_sha256": record["suite_sha256"], "tree_sha256": record["tree_before"]["sha256"],
            "identical": record["identical"]}}
    return {"status": "judge-error", "axes": None, "judge": {"attempts": JUDGE_ATTEMPTS, "errors": errors}}


def run_cell(lot_dir: Path, cell_id: str, through: int, *, judge_fn=judge.judge) -> dict:
    lot = load_lot(lot_dir)
    info = lot["cells"].get(cell_id)
    if info is None:
        raise LotError(f"unknown cell {cell_id}")
    scenario = lot["scenarios"][info["scenario"]]
    if not 1 <= through <= min(scenario["requests"], lot["grant"]["max_length"]):
        raise LotError("chain length outside the scenario or the authority")
    cell_dir = Path(lot["dir"]) / "cells" / cell_id
    with cell_lock(cell_dir):
        path = cell_dir / "cell.json"
        record = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {
            "schema": 1, "lot": lot["lot"], "cell": cell_id, "arm": info["arm"],
            "scenario": info["scenario"], "rep": info["rep"], "token": info["token"],
            "model": f"{PROVIDER}/{MODEL}", "thinking": THINKING, "length": 0, "requests": [],
            "chain_cap_hit": False, "invalid": False, "audit_hits": []}
        record.pop("error", None)
        try:
            _extend(lot, info, record, through, judge_fn, cell_dir)
        except (OSError, subprocess.SubprocessError, LotError) as error:
            record["error"] = f"{type(error).__name__}: {error}"[:500]
            raise
        finally:
            record["length"] = len(record["requests"])
            dump(path, record)
            ledger(lot, event="cell", cell=cell_id, length=record["length"], invalid=record["invalid"],
                   chain_cap_hit=record["chain_cap_hit"], error=record.get("error"))
    return record


def _extend(lot, info, record, through, judge_fn, cell_dir) -> None:
    save = lambda: dump(cell_dir / "cell.json", record)
    setup_cell(lot, info)
    arm_dir = Path(info["arm_dir"])
    request_cap = lot["request_cap_seconds"]
    chain_cap = lot["chain_cap_seconds"] or request_cap * through
    used = lambda: sum(a.get("wall_seconds", 0) for r in record["requests"] for a in r["attempts"])
    while len(record["requests"]) < through and not record["invalid"]:
        pending = record["requests"][-1] if record["requests"] and record["requests"][-1]["status"] == "running" else None
        n = pending["request"] if pending else len(record["requests"]) + 1
        if pending is None:
            if chain_cap - used() < 0.5:
                record["chain_cap_hit"] = True
                record["requests"] += [_undelivered(k) for k in range(n, through + 1)]
                break
            request = {"request": n, "status": "running", "attempts": [],
                       "task": deliver_task(arm_dir / "project", request_text(lot["scenarios"][info["scenario"]], n), n)}
            snapshot(arm_dir, cell_dir / "snapshot")
            record["requests"].append(request)
            save()
        else:  # the host stopped mid-request: the attempt is lost, its state is not trusted
            request = pending
            request["attempts"].append({"attempt": len(request["attempts"]) + 1, "class": "infra:host",
                                        "wall_seconds": 0, "usage": {}})
            restore(cell_dir / "snapshot", arm_dir)
        while True:
            timeout = min(request_cap, chain_cap - used())
            if timeout < 0.5:
                record["chain_cap_hit"] = True
                break
            attempt = run_attempt(lot, info, n, len(request["attempts"]) + 1, timeout, cell_dir / "arm")
            request["attempts"].append(attempt)
            save()
            ledger(lot, event="attempt", cell=record["cell"], request=n, attempt=attempt["attempt"],
                   **{k: attempt[k] for k in ("class", "exit", "failure", "wall_seconds")},
                   cost_usd=attempt["usage"]["cost_usd"])
            if not attempt["class"].startswith("infra:"):
                break
            if sum(a["class"].startswith("infra:") for a in request["attempts"]) > MAX_INFRA_RETRIES:
                request["infra_exhausted"] = True
                break
            restore(cell_dir / "snapshot", arm_dir)
        counted = [a for a in request["attempts"] if "exit" in a]
        last = counted[-1] if counted else {}
        request.update(
            exit=last.get("exit"), timed_out=last.get("failure") == "timeout",
            seconds=last.get("seconds"), wall_seconds=last.get("wall_seconds"),
            usage=last.get("usage") or _sum_usage([]), jev=last.get("jev"),
            infra_usage=_sum_usage([a for a in request["attempts"][:-1] if a["class"].startswith("infra:")]),
            infra_exhausted=request.get("infra_exhausted", False),
            **({"driver": last["driver"]} if "driver" in last else {}))
        request.update(_judge(lot, info, n, judge_fn, cell_dir))
        hits = [dict(hit, request=n) for hit in audit(lot, info)]
        known = {(h["pattern"], h["file"]) for h in record["audit_hits"]}
        record["audit_hits"] += [h for h in hits if (h["pattern"], h["file"]) not in known]
        record["invalid"] = bool(record["audit_hits"])
        save()
        ledger(lot, event="judged", cell=record["cell"], request=n, status=request["status"],
               accepted=(request["axes"] or {}).get("acceptance", {}).get("accepted"),
               invalid=record["invalid"])
        if record["chain_cap_hit"]:
            record["requests"] += [_undelivered(k) for k in range(n + 1, through + 1)]
            break


# --- lots ------------------------------------------------------------------------------------

def cell_done(lot: dict, cell_id: str, through: int) -> bool:
    path = Path(lot["dir"]) / "cells" / cell_id / "cell.json"
    if not path.is_file():
        return False
    record = json.loads(path.read_text(encoding="utf-8"))
    return (record["invalid"] or record["chain_cap_hit"]
            or (len(record["requests"]) >= through and record["requests"][-1]["status"] != "running"))


def run_lot(lot_dir: Path, through: int, jobs: int = 4, reps: list[int] | None = None) -> list[dict]:
    lot = load_lot(lot_dir)
    order = sorted(lot["cells"], key=lambda c: (list(lot["scenarios"]).index(lot["cells"][c]["scenario"]),
                                                lot["cells"][c]["rep"], ARMS.index(lot["cells"][c]["arm"])))
    pending = [c for c in order if not cell_done(lot, c, through)
               and (not reps or lot["cells"][c]["rep"] in reps)]
    running: dict[str, subprocess.Popen] = {}
    finished = []
    while pending or running:
        while pending and len(running) < jobs:
            cell = pending.pop(0)
            log = Path(lot["dir"]) / "cells" / cell / f"run-through-{through}.log"
            log.parent.mkdir(parents=True, exist_ok=True)
            with open(log, "ab") as handle:
                running[cell] = subprocess.Popen(
                    [sys.executable, "-B", str(Path(__file__).resolve()), "run", "--lot", str(lot["dir"]),
                     "--cell", cell, "--through", str(through)],
                    stdout=handle, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
            ledger(lot, event="launch", cell=cell, through=through, pid=running[cell].pid)
        time.sleep(5)
        for cell, process in list(running.items()):
            if process.poll() is not None:
                finished.append({"cell": cell, "exit": process.returncode})
                del running[cell]
    return finished


def status(lot_dir: Path) -> list[dict]:
    lot = load_lot(lot_dir)
    rows = []
    for cell in lot["cells"]:
        path = Path(lot["dir"]) / "cells" / cell / "cell.json"
        record = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {"requests": []}
        rows.append({"cell": cell, "requests": [
            f"{r['request']}:{r['status']}:{'A' if (r.get('axes') or {}).get('acceptance', {}).get('accepted') else '-'}"
            for r in record["requests"]], "invalid": record.get("invalid"), "error": record.get("error")})
    return rows


def judge_gated(lot_dir: Path, *, judge_fn=judge.judge) -> list[dict]:
    """Counterfactual only: judge the candidate a gated driver run left in its worktree.

    A driver stops on an uncertain semantic gate and waits for a human, who must not be faked in
    an AFK lot. The chain keeps what the arm delivered; this asks whether it stopped on good work.
    """
    lot = load_lot(lot_dir)
    judged = []
    for cell_id, info in lot["cells"].items():
        path = Path(lot["dir"]) / "cells" / cell_id / "cell.json"
        if not info["arm"].startswith("driver-") or not path.is_file():
            continue
        with cell_lock(path.parent):
            record = json.loads(path.read_text(encoding="utf-8"))
            project = Path(info["arm_dir"]) / "project"
            for request in record["requests"]:
                driver = request.get("driver") or {}
                if "gated" not in driver.get("status", []) or "counterfactual" in request:
                    continue
                run = [r for r, s in zip(driver["runs"], driver["status"]) if s == "gated"][-1]
                summary_path = project / ".git" / "ticket-driver" / "runs" / run / "summary.json"
                summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.is_file() else {}
                worktree = Path(summary.get("worktree") or "")
                entry = {"source": "gated driver worktree", "run": run, "status": "no-worktree"}
                if summary.get("worktree") and worktree.is_dir():
                    try:
                        result = judge_fn(worktree, Path(lot["scenarios"][info["scenario"]]["path"]),
                                          request["request"])
                    except judge.JudgeError as error:
                        entry.update(status="judge-error", error=str(error)[:300])
                    else:
                        out = path.parent / "judge" / f"{request['request']:02d}-gated-candidate.json"
                        dump(out, result)
                        entry.update(status="judged", axes=result["axes"], judge={
                            "path": str(out), "tree_sha256": result["tree_before"]["sha256"]})
                request["counterfactual"] = entry
                judged.append({"cell": cell_id, "request": request["request"], "status": entry["status"]})
            dump(path, record)
    return judged


# --- driver copies ---------------------------------------------------------------------------

ARBITER_OLD = '''    return (repo.parent.parent == bench and repo.name == "project"
            and repo.parent.name.startswith("driver-") and (repo / "billing" / "money.py").is_file()
            and (repo / "TASK.md").is_file())'''
ARBITER_NEW = '''    return (repo.is_relative_to(bench) and repo.name == "project"
            and repo.parent.name.startswith("driver-") and (repo / "TASK.md").is_file())'''
LEAF_OLD = '"--thinking", policy["thinking"], "--session-dir", str(session)]'
LEAF_NEW = '"--thinking", policy["thinking"], "--no-extensions", "--no-context-files", "--session-dir", str(session)]'


def _replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise LotError(f"{path.name} no longer has the expected text; review the driver copy by hand")
    path.write_text(text.replace(old, new), encoding="utf-8")


def prepare_drivers(lot_dir: Path, source: Path | None = None) -> dict:
    """One configuration-only copy of the installed driver per scenario (contract §6)."""
    source = Path(source) if source else Path.home() / ".agents" / "skills"
    lot = load_lot(lot_dir)
    copies = {}
    for name, scenario in lot["scenarios"].items():
        target = Path(lot["arms_root"]) / name
        if target.exists():
            raise LotError(f"{target} exists: a driver copy is never overwritten")
        for skill in ("ticket-driver", "ticket-autopilot"):
            shutil.copytree(source / skill, target / skill,
                            ignore=shutil.ignore_patterns("__pycache__", "tests"))
        driver = target / "ticket-driver"
        policy = json.loads((driver / "policy.json").read_text(encoding="utf-8"))
        policy.update(provider=PROVIDER, model=MODEL, thinking=THINKING,
                      test_command=driver_test_command(scenario["language"]))
        policy["arbiter"]["external_judgment_allowed"]["benchmark_root"] = lot["runs_root"]
        dump(driver / "policy.json", policy)
        _replace_once(driver / "scripts" / "leaf.py", LEAF_OLD, LEAF_NEW)
        _replace_once(driver / "scripts" / "arbiter.py", ARBITER_OLD, ARBITER_NEW)
        copies[name] = {"path": str(target), "source": str(source), **{
            f"{file.replace('/', '_')}_sha256": sha256_file(driver / file)
            for file in ("policy.json", "scripts/leaf.py", "scripts/arbiter.py")}}
    stored = json.loads((Path(lot["dir"]) / "lot.json").read_text(encoding="utf-8"))
    stored["driver_copies"] = copies
    dump(Path(lot["dir"]) / "lot.json", stored)
    return copies


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="action", required=True)
    init = sub.add_parser("init-lot")
    init.add_argument("--lot", required=True)
    init.add_argument("--lot-id", required=True)
    init.add_argument("--authority", required=True)
    init.add_argument("--scenario", action="append", required=True, help="NAME=PATH")
    init.add_argument("--arm", action="append", required=True, choices=ARMS)
    init.add_argument("--repetitions", type=int, required=True)
    init.add_argument("--runs-root", default="C:/dbench/runs")
    init.add_argument("--arms-root", default="C:/dbench/arms")
    init.add_argument("--jev-key-file")
    for name in ("prepare-drivers", "status", "judge-gated"):
        sub.add_parser(name).add_argument("--lot", required=True)
    run = sub.add_parser("run")
    run.add_argument("--lot", required=True)
    run.add_argument("--cell", required=True)
    run.add_argument("--through", type=int, required=True)
    many = sub.add_parser("run-lot")
    many.add_argument("--lot", required=True)
    many.add_argument("--through", type=int, required=True)
    many.add_argument("--jobs", type=int, default=4)
    many.add_argument("--rep", type=int, action="append", help="only these repetitions (repeatable)")
    args = parser.parse_args(argv)
    try:
        if args.action == "init-lot":
            scenarios = dict(item.split("=", 1) for item in args.scenario)
            lot = init_lot(Path(args.lot), lot_id=args.lot_id, authority=Path(args.authority),
                           scenarios=scenarios, arms=args.arm, repetitions=args.repetitions,
                           runs_root=Path(args.runs_root), arms_root=Path(args.arms_root),
                           jev_key_file=Path(args.jev_key_file) if args.jev_key_file else None)
            result = {"lot": lot["lot"], "cells": len(lot["cells"])}
        elif args.action == "prepare-drivers":
            result = prepare_drivers(Path(args.lot))
        elif args.action == "run":
            record = run_cell(Path(args.lot), args.cell, args.through)
            result = {"cell": args.cell, "length": record["length"], "invalid": record["invalid"]}
        elif args.action == "judge-gated":
            result = judge_gated(Path(args.lot))
        elif args.action == "run-lot":
            result = run_lot(Path(args.lot), args.through, args.jobs, args.rep)
        else:
            result = status(Path(args.lot))
    except (LotError, judge.JudgeError, OSError, subprocess.SubprocessError) as error:
        print(json.dumps({"ok": False, "error": f"{type(error).__name__}: {error}"}))
        return 2
    print(json.dumps(result, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
