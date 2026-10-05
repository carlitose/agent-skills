"""delivery-bench runner: hand one arm a scenario's requests in order and judge every delivery.

    python -B runner.py init-lot --lot DIR --lot-id ID --authority FILE --scenario NAME=PATH ...
                                 --arm ARM ... --repetitions R [--runs-root DIR] [--arms-root DIR]
                                 [--jev-key-file FILE] [--model PROVIDER/ID] [--thinking LEVEL]
                                 [--request-cap S] [--chain-cap S]
    python -B runner.py prepare-drivers --lot DIR [--source CLEAN-CHECKOUT]
    python -B runner.py run --lot DIR --cell CELL --through L
    python -B runner.py run-lot --lot DIR --through L [--jobs 4] [--rep R ...] [--arm ARM ...]
    python -B runner.py judge-gated --lot DIR
    python -B runner.py amend-suite --lot DIR --scenario NAME --reason TEXT
    python -B runner.py status --lot DIR
    python -B runner.py preflight --lot-free [--arm ARM ...] [--model PROVIDER/ID] [--thinking LEVEL]
                                  [--pi-extension FILE] [--timeout S]

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
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "ticket-autopilot" / "scripts"))
import judge
from autopilot.command_capture import (
    MAX_TIMEOUT_SECONDS,
    CaptureFailure,
    capture_command,
)

# Defaults for a lot that names no model; a lot records its own and every arm reads it from there.
PROVIDER, MODEL, THINKING = "openai-codex", "gpt-6-sol", "high"
PROMPT = ("Lee TASK.md en la raiz del repositorio y haz lo que pide, hasta el final. "
          "Trabaja solo en este directorio. Lo que cuenta es el estado de esta carpeta cuando termines.")
SKILLS_ONLY_SUFFIX = (" Trabaja en modo skills-only: usa las skills instaladas de forma inline y no "
                      "arranques el runner, el scheduler ni ningun driver de Autopilot.")
AUTOPILOT_SUFFIX = (" Usa el flujo completo de ticket-autopilot, incluido su runner, para llevar este "
                    "trabajo de principio a fin. `origin` es un repositorio local sin proveedor de PR: "
                    "usa el runner con `--provider github --provider-mode simulated`; cuando el runner "
                    "no pueda fusionar, integra tú la rama en `main` de esta carpeta.")
ARMS = ("bare", "skills-only", "autopilot", "driver-c1a", "driver-c3a", "pi-tools", "pi-full")
PI_ARMS = {"bare": (["--no-skills"], ""), "skills-only": ([], SKILLS_ONLY_SUFFIX),
           "autopilot": ([], AUTOPILOT_SUFFIX), "pi-tools": (["--no-skills"], ""), "pi-full": ([], "")}
# The closed list of extensions an arm loads with -e despite --no-extensions, relative to the
# installed pi-personal-config (DBH-21). Memory, Telegram, Messenger, MCP, subagents and the
# other personal extensions stay out of every arm: they would skew or soil the measure.
TOOL_PROFILE = ("extensions/pi-code-tool/index.ts", "node_modules/pi-code/extensions/todo.ts",
                "node_modules/pi-code/extensions/plan-mode", "node_modules/pi-code/extensions/web.ts")
MANDATORY_EXTENSION = "node_modules/carlitose-agent-skills-pi/extensions/mandatory-agent-skills.ts"
ARM_PROFILES = {"pi-tools": TOOL_PROFILE, "pi-full": (*TOOL_PROFILE, MANDATORY_EXTENSION)}
# What the preflight expects each extension to add, and which arms must see the skills.
EXTENSION_TOOLS = dict(zip(ARM_PROFILES["pi-full"], (
    ("code",), ("todo",), ("plan_mode_complete",), ("web_search", "web_fetch"), ())))
BUILTIN_TOOLS = ("read", "bash", "edit", "write")
ARM_SKILLS = {"bare": False, "skills-only": True, "autopilot": True, "pi-tools": False, "pi-full": True}
REQUIRED_SKILLS = ("ask-skills", "change-status-ticket", "to-spec", "to-tickets", "execute-ticket")
PI_AGENT_SETTINGS = Path.home() / ".pi" / "agent" / "settings.json"
PI_CONFIG_PACKAGE = "pi-personal-config"
PREFLIGHT_TASK = """# Preflight

This is a harness check, not a task. Do exactly this and nothing else:

1. If a tool named `code` is available, call it once with Python that writes the text `ok` to the
   file `preflight.txt` in the current directory, for example `write("preflight.txt", "ok")`.
2. If there is no `code` tool, create no file.
3. Reply `done`.
"""
PREFLIGHT_SECONDS = 600
# The global settings disable compaction; a chain of 8 in one session needs it (contract §6).
PI_SETTINGS = {"compaction": {"enabled": True, "reserveTokens": 65536}}
REQUEST_CAP_SECONDS = 3600
MAX_INFRA_RETRIES = 5
# The wait before each infrastructure retry (DBH-14, DBH-15). A blip passes in a minute; the
# waits add up to almost two hours, beyond the nine-minute outage of lot `dbh` and the
# 42-minute one of lot `dbh-drivers`. A failed attempt in an outage costs ~25 s and nothing in
# tokens. Waiting is not arm time: it counts toward neither the request cap nor the chain cap.
INFRA_WAIT_SECONDS = (60.0, 300.0, 900.0, 1800.0, 3600.0)
pause = time.sleep  # the one wait the tests record instead of sleeping
# The arms see the skills installed on this host. Their installer writes this manifest; a lot binds
# it, so an update during a lot stops it instead of passing unrecorded (DBH-17).
SKILLS_MANIFEST = Path.home() / ".agents" / "skills" / ".agent-skills-install-manifest.json"
JUDGE_ATTEMPTS = 3
JUDGE_BACKOFF_SECONDS = 5.0
JUDGE_READY_SECONDS = 60  # one `docker version` probe
DIFF_LIMIT = 20_000_000  # bytes of a request's diff kept for review
JEV_USD_PER_INPUT_TOKEN = 0.042e-6  # published input rate; output is free; an estimate, not a bill
OUTPUT_LIMIT = 16 * 1024 * 1024
BENCH = ["-c", "user.name=bench", "-c", "user.email=bench@example.invalid"]
STRIPPED_ENV = ("TYPESAFE_API_KEY", "PI_CODING_AGENT", "PI_CODING_AGENT_SESSION_DIR",
                "TICKET_DRIVER_PI_EXTENSION")
# a provider failure that can end a session after the model worked: quota, overload, server or
# network, never a request the arm made invalid (DBH-19)
TRANSIENT_PROVIDER = re.compile(
    r"rate[_ ]limit|overloaded|\b(429|500|502|503|504|529)\b|service unavailable|bad gateway|"
    r"gateway timeout|internal server error|\bapi_error\b|websocket closed|econnreset|etimedout|"
    r"socket hang up|connection (reset|closed|refused)|fetch failed",
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


def native_path(path: Path) -> str:
    """On Windows, the extended form of an absolute path: it also reaches files an arm names like a
    device (a build redirected to NUL from a POSIX shell leaves a file called NUL)."""
    text = os.fspath(path)
    if os.name != "nt":
        return os.path.abspath(text)
    if text.startswith("\\\\?\\"):
        return text
    # lexical, not abspath: Windows turns an absolute path ending in NUL into the device \\.\NUL
    text = os.path.normpath(os.path.join(os.getcwd(), text))
    return "\\\\?\\UNC\\" + text[2:] if text.startswith("\\\\") else "\\\\?\\" + text


def rmtree(path: Path) -> None:
    if sys.version_info >= (3, 12):
        shutil.rmtree(native_path(path), onexc=_force_remove)
    else:  # pragma: no cover
        shutil.rmtree(native_path(path), onerror=_force_remove)


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


def installed_skills() -> dict:
    """The skills the arms see on this host, as their installer's manifest records them."""
    if not SKILLS_MANIFEST.is_file():
        return {"manifest": str(SKILLS_MANIFEST), "sha256": None, "head": None, "tree": None}
    document = json.loads(SKILLS_MANIFEST.read_text(encoding="utf-8"))
    return {"manifest": str(SKILLS_MANIFEST), "sha256": sha256_file(SKILLS_MANIFEST),
            "head": document.get("head"), "tree": document.get("tree")}


def check_installed_skills(lot: dict) -> str | None:
    """The digest an attempt runs with; a lot bound to other skills stops first (DBH-17).

    Lots bound before DBH-17 carry no binding and are not checked.
    """
    observed = installed_skills()["sha256"]
    bound = lot.get("installed_skills")
    if bound is not None and observed != bound["sha256"]:
        raise LotError("the installed skills changed after the lot was bound")
    return observed


def bind_extension(pi_extension: Path | None) -> dict | None:
    """The one extension every arm and driver leaf loads with -e despite --no-extensions (DBH-18).

    A provider may work only through one, as Anthropic's OAuth does. Its whole folder is digested:
    an extension imports its siblings.
    """
    if pi_extension is None:
        return None
    path = Path(pi_extension).resolve()
    if not path.is_file():
        raise LotError(f"the Pi extension {path} is not a file")
    return {"path": str(path), "sha256": judge.tree_digest(path.parent)["sha256"]}


def installed_pi_config() -> Path:
    """The pi-personal-config Pi loads, as its settings name the package, not a development checkout."""
    try:
        settings = json.loads(PI_AGENT_SETTINGS.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise LotError(f"cannot read the Pi settings {PI_AGENT_SETTINGS}: {error}") from None
    for entry in settings.get("packages") or []:
        source = entry.get("source") if isinstance(entry, dict) else entry
        if not isinstance(source, str) or source.startswith(("npm:", "git:")) or "://" in source:
            continue
        try:  # a local source is relative to the agent folder, as Pi resolves it
            root = (PI_AGENT_SETTINGS.parent / Path(source).expanduser()).resolve()
            name = json.loads((root / "package.json").read_text(encoding="utf-8")).get("name")
        except (OSError, ValueError, AttributeError):
            continue
        if name == PI_CONFIG_PACKAGE:
            return root
    raise LotError(f"{PI_CONFIG_PACKAGE} is not installed as a local Pi package in {PI_AGENT_SETTINGS}")


def _folder_digest(path: Path) -> str:
    # the folder holding the extension: it imports its siblings (plan-mode reads ../internal)
    return judge.tree_digest(Path(path).parent)["sha256"]


def bind_arm_extensions(arms: list, root: Path | None = None) -> dict:
    """Each arm's extensions with path and folder digest (DBH-21); a missing one stops init-lot."""
    if not any(arm in ARM_PROFILES for arm in arms):
        return {arm: [] for arm in arms}
    root = Path(root).resolve() if root else installed_pi_config()
    bound = {}
    for arm in arms:
        bound[arm] = []
        for relative in ARM_PROFILES.get(arm, ()):
            path = (root / relative).resolve()
            if not path.exists():
                raise LotError(f"the extension {relative} of arm {arm} is missing from {root}")
            bound[arm].append({"path": str(path), "sha256": _folder_digest(path)})
    return bound


def bound_extensions(lot: dict, arm: str) -> list:
    bound = (lot.get("arm_extensions") or {}).get(arm)
    if bound is None and arm in ARM_PROFILES:  # never run a profiled arm without its extensions
        raise LotError(f"the lot binds no extensions for arm {arm}")
    return bound or []


def check_arm_extensions(lot: dict, arm: str) -> list:
    """The extensions an attempt of this arm starts with; a changed or vanished one stops it.

    Lots bound before DBH-21 carry no binding and their arms load no profile.
    """
    bound = bound_extensions(lot, arm)
    for entry in bound:
        path = Path(entry["path"])
        if not path.exists() or _folder_digest(path) != entry["sha256"]:
            raise LotError(f"the extension {path} of arm {arm} changed or disappeared after the lot was bound")
    return bound


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
             driver_command: list | None = None, model: str = f"{PROVIDER}/{MODEL}",
             thinking: str = THINKING, pi_extension: Path | None = None,
             pi_config_root: Path | None = None) -> dict:
    lot_dir, runs_root = Path(lot_dir).resolve(), Path(runs_root).resolve()
    provider, _, model_id = model.partition("/")
    if not provider or not model_id or not thinking:
        raise LotError("the model is PROVIDER/ID and needs a thinking level")
    if not 1 <= request_cap_seconds <= MAX_TIMEOUT_SECONDS:  # every attempt would be refused
        raise LotError(f"the request cap must be from 1 to {MAX_TIMEOUT_SECONDS} seconds")
    if chain_cap_seconds is not None and chain_cap_seconds < 1:
        raise LotError("the chain cap must be at least 1 second")
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
    named = grant.get("model")
    if named is not None and named != {"provider": provider, "id": model_id, "thinking": thinking}:
        raise LotError("authority names another model or thinking level")
    if "driver-c3a" in arms and not (grant.get("jev_spend_authorized") is True and jev_key_file):
        raise LotError("driver-c3a needs Jev spend authorization and a key file")
    arms_root = Path(arms_root).resolve() if arms_root else runs_root.parent / "arms"
    extension = bind_extension(pi_extension)
    arm_extensions = bind_arm_extensions(arms, pi_config_root)
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
            "driver_test_command": document.get("driver_test_command"),
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
           "provider": provider, "model": model_id, "thinking": thinking, "arms": list(arms),
           "repetitions": repetitions, "runs_root": str(runs_root), "arms_root": str(arms_root),
           "request_cap_seconds": request_cap_seconds, "chain_cap_seconds": chain_cap_seconds,
           "jev_key_file": str(Path(jev_key_file).resolve()) if jev_key_file else None,
           "pi_command": list(pi_command) if pi_command else resolve_pi(),
           "installed_skills": installed_skills(), "pi_extension": extension,
           "arm_extensions": arm_extensions, "scenarios": described, "cells": cells, "driver_copies": {}}
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
    extension = lot.get("pi_extension")
    if extension and (not Path(extension["path"]).is_file()
                      or judge.tree_digest(Path(extension["path"]).parent)["sha256"] != extension["sha256"]):
        raise LotError("the Pi extension changed or disappeared after the lot was bound")
    for arm in lot.get("arm_extensions") or {}:
        check_arm_extensions(lot, arm)
    lot["dir"] = str(lot_dir)
    lot["grant"] = _authority(authority)
    return lot


def amend_suite(lot_dir: Path, scenario: str, reason: str) -> dict:
    """Bind a corrected hidden suite to a lot, on the record: old and new digest, reason, time.

    Only the suite may change (an oracle defect found while measuring), never the seed, and never
    while a cell runs. Judgments already recorded stay as they are until corrected on the record.
    """
    lot_dir = Path(lot_dir).resolve()
    lot = json.loads((lot_dir / "lot.json").read_text(encoding="utf-8"))
    if not reason.strip():
        raise LotError("an amendment needs a reason")
    if scenario not in lot["scenarios"]:
        raise LotError(f"unknown scenario {scenario}")
    authority = Path(lot["authority"]["path"])
    if not authority.is_file() or sha256_file(authority) != lot["authority"]["sha256"]:
        raise LotError("the human authority changed or disappeared after the lot was bound")
    for lock in lot_dir.glob("cells/*/lock"):
        owner = lock.read_text(encoding="utf-8").strip()
        if owner.isdigit() and _alive(int(owner)):
            raise LotError(f"cell {lock.parent.name} is running")
    described = lot["scenarios"][scenario]
    path = Path(described["path"])
    if judge.tree_digest(path / "seed")["sha256"] != described["seed_sha256"]:
        raise LotError(f"the seed of {scenario} changed: a lot never amends a seed")
    new = judge.tree_digest(path / "hidden")["sha256"]
    if new == described["suite_sha256"]:
        raise LotError(f"the suite of {scenario} did not change")
    amendment = {"scenario": scenario, "from": described["suite_sha256"], "to": new,
                 "reason": reason.strip(), "at": now()}
    lot.setdefault("amendments", []).append(amendment)
    described["suite_sha256"] = new
    dump(lot_dir / "lot.json", lot)
    ledger({**lot, "dir": str(lot_dir)}, event="amend-suite", **amendment)
    return amendment


def ledger(lot: dict, **event) -> None:
    line = json.dumps({"at": now(), **event}, sort_keys=True) + "\n"
    with open(Path(lot["dir"]) / "ledger.jsonl", "a", encoding="utf-8") as handle:
        handle.write(line)


# --- cell setup and delivery -----------------------------------------------------------------

def driver_test_command(language: str) -> list[str]:
    if language == "c":
        return ["python", "dev.py", "test"]
    if language in ("typescript", "javascript"):
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
    if scenario["language"] in ("typescript", "javascript"):
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
    # already committed when the cell stopped between this delivery and its snapshot: resume it
    if git(project, "diff", "--cached", "--quiet", "--", "TASK.md", check=False).returncode:
        git(project, *BENCH, "commit", "-q", "--no-verify", "-m", f"TASK {n}", "--", "TASK.md")
    pushed = git(project, "push", "-q", "origin", "HEAD:main", check=False).returncode == 0
    branch = git(project, "symbolic-ref", "--short", "-q", "HEAD", check=False).stdout.strip()
    return {"commit": git(project, "rev-parse", "HEAD").stdout.strip(), "branch": branch or None,
            "pushed": pushed, "removed_index_lock": removed_lock}


def snapshot(arm_dir: Path, target: Path) -> None:
    if target.exists():
        rmtree(target)
    source = native_path(arm_dir)
    shutil.copytree(source, native_path(target), symlinks=True,
                    ignore=lambda folder, names: ["node_modules"] if folder == source else [])


def restore(target: Path, arm_dir: Path) -> None:
    for child in Path(native_path(arm_dir)).iterdir():
        if child.name == "node_modules":
            continue
        rmtree(child) if child.is_dir() and not child.is_symlink() else child.unlink()
    shutil.copytree(native_path(target), native_path(arm_dir), symlinks=True, dirs_exist_ok=True)


# --- one attempt -----------------------------------------------------------------------------

def arm_argv(lot: dict, info: dict, n: int) -> list[str]:
    arm_dir = Path(info["arm_dir"])
    project = (arm_dir / "project").resolve()
    if info["arm"] in PI_ARMS:
        options, suffix = PI_ARMS[info["arm"]]
        argv = [*lot["pi_command"], "-p", "--provider", lot["provider"], "--model", lot["model"],
                "--thinking", lot["thinking"], "--no-extensions", "--no-context-files", "--approve",
                *extension_args(lot), *profile_args(lot, info["arm"]), *options,
                "--session-dir", str(arm_dir / "sessions")]
        return [*argv, *(["--continue"] if n > 1 else []), "--", PROMPT + suffix]
    return [*lot["scenarios"][info["scenario"]]["driver"], "run",
            "--candidate", info["arm"].split("-", 1)[1], "--task", str(project / "TASK.md"),
            "--repo", str(project), "--live-authorization",
            str((arm_dir / "driver-authorization.json").resolve())]


def extension_args(lot: dict) -> list[str]:
    return ["-e", lot["pi_extension"]["path"]] if lot.get("pi_extension") else []


def profile_args(lot: dict, arm: str) -> list[str]:
    return [flag for entry in bound_extensions(lot, arm) for flag in ("-e", entry["path"])]


def arm_environment(lot: dict, arm: str) -> dict:
    env = {key: value for key, value in os.environ.items() if key not in STRIPPED_ENV}
    if arm.startswith("driver-") and lot.get("pi_extension"):
        env["TICKET_DRIVER_PI_EXTENSION"] = lot["pi_extension"]["path"]  # the leaf adds it with -e
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
    compaction = {"count": 0, "tokens_before": [], "cost_usd": 0.0}
    assistant = with_output = tool_calls = 0
    last, last_ts = {}, None
    for event in events:
        stamp = _timestamp(event.get("timestamp"))
        if stamp is not None:
            last_ts = stamp if last_ts is None else max(last_ts, stamp)
        if event.get("type") == "compaction":  # Pi summarised the session; its call is spend too
            compaction["count"] += 1
            if isinstance(event.get("tokensBefore"), int):
                compaction["tokens_before"].append(event["tokensBefore"])
            cost = (event.get("usage") or {}).get("cost") if isinstance(event.get("usage"), dict) else None
            if isinstance(cost, dict) and isinstance(cost.get("total"), (int, float)):
                compaction["cost_usd"] += cost["total"]
            continue
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
    compaction["cost_usd"] = round(compaction["cost_usd"], 6)
    return {"usage": usage, "compaction": compaction, "assistant_messages": assistant, "with_output": with_output,
            "tool_calls": tool_calls, "last_stop": last.get("stopReason"),
            "last_error": str(last.get("errorMessage") or "")[:300], "last_ts": last_ts}


def classify(code: int | None, failure: str | None, summary: dict) -> str:
    """An agent's own outcome counts; a failure before the agent could work is repeated."""
    if failure == "timeout":
        return "agent"
    if failure is not None:
        return "infra:harness"
    if summary["with_output"] == 0 and summary["last_stop"] == "error":
        # the model never answered: network, quota, credential or billing (DBH-18: Opus 5.5 without
        # its OAuth extension gets a 400 and Pi exits 0)
        return "infra:provider"
    if summary["last_stop"] == "error" and TRANSIENT_PROVIDER.search(summary["last_error"]):
        # the provider ended a session the model was working in (lot dbh-opus: the Claude plan's
        # rate limit and an overload); the half work is not the arm's outcome (DBH-19)
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


def docker_ready() -> bool:
    """The Docker judge's daemon answers (DBH-24). A stopped Docker Desktop is infrastructure,
    not a verdict on the delivery."""
    docker = shutil.which("docker")
    if docker is None:
        return False
    try:
        done = subprocess.run([docker, "version", "--format", "{{.Server.Version}}"],
                              capture_output=True, timeout=JUDGE_READY_SECONDS, check=False)
    except (OSError, subprocess.SubprocessError):
        return False
    return done.returncode == 0 and bool(done.stdout.strip())


def wait_for_judge(lot: dict, cell: str, n: int, ready) -> float:
    """Wait for the judge like for an outage; past the last wait the cell stops, unjudged."""
    waited = 0.0
    for wait in INFRA_WAIT_SECONDS:
        if ready():
            return waited
        ledger(lot, event="judge-wait", cell=cell, request=n, seconds=wait)
        pause(wait)
        waited += wait
    if ready():
        return waited
    raise LotError("the judge's Docker did not answer after every wait: the request stays unjudged")


def request_diff(project: Path, base: str, target: Path, store: Path) -> dict:
    """What the arm changed during one request, kept for a later review (DBH-24).

    `base` is the tree the previous request left (or the delivered commit): an arm that never
    commits still gets one request's work per diff. The work tree is written as a tree into the
    cell's own object `store`, with a temporary index: the arm's repository is untouched. The
    request text itself (`TASK.md`) is left out.
    """
    project, store = Path(project).resolve(), Path(store).resolve()
    try:
        store.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="dbench-diff-") as scratch:
            env = {**os.environ, "GIT_INDEX_FILE": str(Path(scratch) / "index"),
                   "GIT_OBJECT_DIRECTORY": str(store),
                   "GIT_ALTERNATE_OBJECT_DIRECTORIES": str(project / ".git" / "objects")}

            def run(*args: str) -> bytes:
                return subprocess.run(["git", "-C", str(project), "-c", "core.quotepath=false", *args],
                                      env=env, capture_output=True, check=True, timeout=600).stdout
            run("read-tree", base)
            run("add", "-A")
            tree = run("write-tree").decode().strip()
            scope = ("--", ".", ":(exclude)TASK.md")
            files = run("diff", "--name-only", base, tree, *scope).decode("utf-8", "replace").splitlines()
            diff = run("diff", "--no-color", "--no-ext-diff", base, tree, *scope)
    except (OSError, subprocess.SubprocessError) as error:
        return {"error": f"{type(error).__name__}: {error}"[:300]}
    truncated = len(diff) > DIFF_LIMIT
    body = diff[:DIFF_LIMIT] + (b"\n[runner] diff truncated\n" if truncated else b"")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(body)
    return {"path": str(target), "base": base, "tree": tree, "bytes": len(diff), "truncated": truncated,
            "sha256": hashlib.sha256(body).hexdigest(), "files": files[:200], "file_count": len(files)}


def _judge(lot: dict, info: dict, n: int, judge_fn, cell_dir: Path, ready=None) -> dict:
    scenario = Path(lot["scenarios"][info["scenario"]]["path"])
    project = Path(info["arm_dir"]) / "project"
    errors, waited = [], 0.0
    for attempt in range(1, JUDGE_ATTEMPTS + 1):
        if ready is not None:  # an unreachable judge costs no attempt (DBH-24)
            waited += wait_for_judge(lot, cell_dir.name, n, ready)
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
            "identical": record["identical"], "wait_seconds": waited}}
    return {"status": "judge-error", "axes": None,
            "judge": {"attempts": JUDGE_ATTEMPTS, "errors": errors, "wait_seconds": waited}}


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
            "model": f"{lot['provider']}/{lot['model']}", "thinking": lot["thinking"], "length": 0, "requests": [],
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
    interrupted = lambda: (record["requests"] and record["requests"][-1]["status"] in ("running", "unjudged")
                           and record["requests"][-1]["request"] <= through)
    ready = docker_ready if judge_fn is judge.judge else None  # only the Docker judge needs Docker
    while (len(record["requests"]) < through or interrupted()) and not record["invalid"]:
        check_installed_skills(lot)
        pending = record["requests"][-1] if interrupted() else None
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
        elif pending["status"] == "unjudged":  # the work is done and kept; only its judgment is missing
            request = pending
        else:  # the host stopped mid-request: the attempt is lost, its state is not trusted
            request = pending
            request["attempts"].append({"attempt": len(request["attempts"]) + 1, "class": "infra:host",
                                        "wall_seconds": 0, "usage": {}})
            restore(cell_dir / "snapshot", arm_dir)
        while request["status"] == "running":
            timeout = min(request_cap, chain_cap - used())
            if timeout < 0.5:
                record["chain_cap_hit"] = True
                break
            skills = check_installed_skills(lot)
            extensions = check_arm_extensions(lot, info["arm"])
            attempt = run_attempt(lot, info, n, len(request["attempts"]) + 1, timeout, cell_dir / "arm")
            attempt["installed_skills"] = skills
            attempt["arm_extensions"] = extensions
            request["attempts"].append(attempt)
            save()
            ledger(lot, event="attempt", cell=record["cell"], request=n, attempt=attempt["attempt"],
                   **{k: attempt[k] for k in ("class", "exit", "failure", "wall_seconds")},
                   cost_usd=attempt["usage"]["cost_usd"])
            if not attempt["class"].startswith("infra:"):
                break
            infra = sum(a["class"].startswith("infra:") for a in request["attempts"])
            if infra > MAX_INFRA_RETRIES:
                request["infra_exhausted"] = True
                restore(cell_dir / "snapshot", arm_dir)  # a cut attempt's half work is not judged
                break
            wait = INFRA_WAIT_SECONDS[min(infra, len(INFRA_WAIT_SECONDS)) - 1]
            request["infra_wait_seconds"] = request.get("infra_wait_seconds", 0) + wait
            save()
            ledger(lot, event="infra-wait", cell=record["cell"], request=n, seconds=wait)
            pause(wait)
            restore(cell_dir / "snapshot", arm_dir)
        counted = [a for a in request["attempts"] if "exit" in a]
        last = counted[-1] if counted else {}
        request.update(
            exit=last.get("exit"), timed_out=last.get("failure") == "timeout",
            seconds=last.get("seconds"), wall_seconds=last.get("wall_seconds"),
            usage=last.get("usage") or _sum_usage([]), jev=last.get("jev"),
            compaction=last.get("compaction") or {"count": 0, "tokens_before": [], "cost_usd": 0.0},
            # every attempt but the counted one, even a finished one a host stop superseded
            infra_usage=_sum_usage([a for a in request["attempts"] if a is not last]),
            infra_exhausted=request.get("infra_exhausted", False),
            infra_wait_seconds=request.get("infra_wait_seconds", 0),
            **({"driver": last["driver"]} if "driver" in last else {}))
        if "diff" not in request:
            left = [r["diff"]["tree"] for r in record["requests"][:-1] if (r.get("diff") or {}).get("tree")]
            request["diff"] = request_diff(arm_dir / "project", left[-1] if left else request["task"]["commit"],
                                           cell_dir / "diffs" / f"{n:02d}.diff", cell_dir / "diffs" / "objects")
        request["status"] = "unjudged"  # a judge that never answers leaves the work to judge on resume
        save()
        request.update(_judge(lot, info, n, judge_fn, cell_dir, ready))
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
            or (len(record["requests"]) >= through
                and record["requests"][-1]["status"] not in ("running", "unjudged")))


def select_cells(lot: dict, through: int, reps: list[int] | None = None,
                 arms: list[str] | None = None) -> list[str]:
    """Cells still short of `through`, optionally only some repetitions and arms, in launch order."""
    cells = lot["cells"]
    order = sorted(cells, key=lambda c: (list(lot["scenarios"]).index(cells[c]["scenario"]),
                                         cells[c]["rep"], ARMS.index(cells[c]["arm"])))
    return [c for c in order if not cell_done(lot, c, through)
            and (not reps or cells[c]["rep"] in reps) and (not arms or cells[c]["arm"] in arms)]


def run_lot(lot_dir: Path, through: int, jobs: int = 4, reps: list[int] | None = None,
            arms: list[str] | None = None) -> list[dict]:
    lot = load_lot(lot_dir)
    check_installed_skills(lot)
    pending = select_cells(lot, through, reps, arms)
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


# --- preflight -------------------------------------------------------------------------------

def _text(content) -> str:
    if isinstance(content, str):
        return content
    return "".join(c.get("text", "") for c in content or [] if isinstance(c, dict))


def read_session(events: list[dict], project: Path) -> dict:
    """Replay a session's system messages into the active tools and visible skills; find the write.

    Pi does not record a prompt an extension forces in before_agent_start, so the mandatory rule
    shows only in its routing: the first user message opens with the ask-skills skill.
    """
    tools, sections, first_user, results = set(), {}, None, []
    for event in events:
        message = event.get("message") if event.get("type") == "message" else None
        if not isinstance(message, dict):
            continue
        if message.get("role") == "system":
            for key in ("toolsAdded", "toolsRemoved"):
                names = {t.get("name") if isinstance(t, dict) else t for t in message.get(key) or []}
                tools = tools | names if key == "toolsAdded" else tools - names
            for name, value in (message.get("sections") or {}).items():
                if value is None:  # a patch removes a section
                    sections.pop(name, None)
                else:
                    sections[name] = value
        elif message.get("role") == "user" and first_user is None:
            first_user = _text(message.get("content"))
        elif message.get("role") == "toolResult" and message.get("toolName") == "code":
            results.append(not message.get("isError"))
    written = project / "preflight.txt"
    wrote = written.is_file() and written.read_text(encoding="utf-8", errors="replace").strip() == "ok"
    if results:
        code_write = "ok" if any(results) and wrote else "failed"
    else:
        code_write = "not-called" if "code" in tools else "n/a"
    return {"tools": sorted(t for t in tools if t),
            "skills": re.findall(r"<name>([^<]+)</name>", sections.get("skills") or ""),
            "routed": (first_user or "").startswith('<skill name="ask-skills"'), "code_write": code_write}


def preflight_problems(arm: str, observed: dict, code: int | None, failure: str | None,
                       timeout: float) -> list[str]:
    profile = ARM_PROFILES.get(arm, ())
    expected = sorted({*BUILTIN_TOOLS, *(t for e in profile for t in EXTENSION_TOOLS[e])})
    problems = []
    if failure == "timeout":
        problems.append(f"timeout after {timeout:g} s: is `code` waiting for a human approval?")
    elif failure:
        problems.append(f"the request did not run: {failure}")
    elif code != 0:
        problems.append(f"Pi exit {code} (an extension that fails to load exits 1)")
    if observed["tools"] != expected:
        seen = set(observed["tools"])
        problems.append(f"tools differ from the profile: missing {sorted(set(expected) - seen)}, "
                        f"unexpected {sorted(seen - set(expected))}")
    if ARM_SKILLS[arm] and not set(REQUIRED_SKILLS) <= set(observed["skills"]):
        problems.append(f"skills missing: {sorted(set(REQUIRED_SKILLS) - set(observed['skills']))}")
    if not ARM_SKILLS[arm] and observed["skills"]:
        problems.append(f"skills visible in an arm without skills: {observed['skills'][:5]}")
    if observed["routed"] != (MANDATORY_EXTENSION in profile):
        problems.append("the mandatory rule " + ("did not route" if MANDATORY_EXTENSION in profile
                                                 else "routed an arm without it"))
    if "code" in expected and observed["code_write"] != "ok":
        problems.append(f"the `code` write did not succeed in -p: {observed['code_write']}")
    return problems


def preflight(arms: list[str], *, model: str = f"{PROVIDER}/{MODEL}", thinking: str = THINKING,
              pi_command: list | None = None, pi_extension: Path | None = None,
              pi_config_root: Path | None = None, timeout_seconds: float = PREFLIGHT_SECONDS) -> dict:
    """One minimal request per arm in a temporary folder, with the argv a lot would use (DBH-21).

    It belongs to no lot and counts as no attempt; it spends a few cents on a real model.
    """
    provider, _, model_id = model.partition("/")
    if not provider or not model_id or not set(arms) <= set(PI_ARMS):
        raise LotError(f"preflight needs PROVIDER/ID and Pi arms only: {sorted(PI_ARMS)}")
    lot = {"provider": provider, "model": model_id, "thinking": thinking,
           "pi_command": list(pi_command) if pi_command else resolve_pi(),
           "pi_extension": bind_extension(pi_extension),
           "arm_extensions": bind_arm_extensions(arms, pi_config_root)}
    report = {}
    with tempfile.TemporaryDirectory(prefix="dbench-preflight-", ignore_cleanup_errors=True) as folder:
        for arm in arms:
            arm_dir = Path(folder) / arm
            project = arm_dir / "project"
            project.mkdir(parents=True)
            (project / "TASK.md").write_text(PREFLIGHT_TASK, encoding="utf-8")
            dump(project / ".pi" / "settings.json", PI_SETTINGS)
            argv = arm_argv(lot, {"arm": arm, "arm_dir": str(arm_dir)}, 1)
            code, failure, err = None, None, b""
            try:
                with environment(arm_environment(lot, arm)):
                    _out, err, code = capture_command(argv, cwd=project, timeout_seconds=timeout_seconds,
                                                      max_output_bytes=OUTPUT_LIMIT)
            except CaptureFailure as error:
                failure, err = error.reason, error.stderr
            events = new_events([arm_dir / "sessions"], {})
            observed = read_session(events, project)
            problems = preflight_problems(arm, observed, code, failure, timeout_seconds)
            report[arm] = {"ok": not problems, "problems": problems, "exit": code, "failure": failure,
                           **observed, "cost_usd": summarize(events)["usage"]["cost_usd"],
                           "extensions": lot["arm_extensions"][arm],
                           "stderr_tail": err[-2000:].decode("utf-8", "replace")}
    return {"ok": all(arm["ok"] for arm in report.values()), "model": model, "thinking": thinking,
            "arms": report}


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


def source_identity(source: Path) -> dict:
    """Exact commit and tree of a driver source checkout; a dirty or non-root checkout is refused."""
    top = git(source, "rev-parse", "--show-toplevel", check=False)
    if top.returncode != 0 or Path(top.stdout.strip()).resolve() != Path(source).resolve():
        raise LotError(f"{source} is not the root of a Git checkout")
    if git(source, "status", "--porcelain", "--untracked-files=all").stdout.strip():
        raise LotError(f"{source} has uncommitted changes: copy drivers only from an exact commit")
    return {"source_commit": git(source, "rev-parse", "HEAD").stdout.strip(),
            "source_tree": git(source, "rev-parse", "HEAD^{tree}").stdout.strip()}


def prepare_drivers(lot_dir: Path, source: Path | None = None, *, exact: bool = False) -> dict:
    """One configuration-only copy of the installed driver per scenario (contract §6).

    `exact` copies from a clean agent-skills checkout instead and records its commit and tree.
    """
    source = Path(source) if source else Path.home() / ".agents" / "skills"
    identity = source_identity(source) if exact else {}
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
        policy.update(provider=lot["provider"], model=lot["model"], thinking=lot["thinking"],
                      test_command=scenario.get("driver_test_command")
                      or driver_test_command(scenario["language"]))
        policy["arbiter"]["external_judgment_allowed"]["benchmark_root"] = lot["runs_root"]
        dump(driver / "policy.json", policy)
        _replace_once(driver / "scripts" / "leaf.py", LEAF_OLD, LEAF_NEW)
        _replace_once(driver / "scripts" / "arbiter.py", ARBITER_OLD, ARBITER_NEW)
        copies[name] = {"path": str(target), "source": str(source), **identity, **{
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
    init.add_argument("--model", default=f"{PROVIDER}/{MODEL}", help="PROVIDER/ID for every arm")
    init.add_argument("--thinking", default=THINKING)
    init.add_argument("--request-cap", type=int, default=REQUEST_CAP_SECONDS, help="seconds per request")
    init.add_argument("--chain-cap", type=int, help="seconds per chain (default: request cap x L)")
    init.add_argument("--pi-extension", help="extension file every arm and driver leaf loads with -e")
    for name in ("status", "judge-gated"):
        sub.add_parser(name).add_argument("--lot", required=True)
    prepare = sub.add_parser("prepare-drivers")
    prepare.add_argument("--lot", required=True)
    prepare.add_argument("--source", help="clean agent-skills checkout to copy instead of the install")
    amend = sub.add_parser("amend-suite")
    amend.add_argument("--lot", required=True)
    amend.add_argument("--scenario", required=True)
    amend.add_argument("--reason", required=True)
    run = sub.add_parser("run")
    run.add_argument("--lot", required=True)
    run.add_argument("--cell", required=True)
    run.add_argument("--through", type=int, required=True)
    many = sub.add_parser("run-lot")
    many.add_argument("--lot", required=True)
    many.add_argument("--through", type=int, required=True)
    many.add_argument("--jobs", type=int, default=4)
    many.add_argument("--rep", type=int, action="append", help="only these repetitions (repeatable)")
    many.add_argument("--arm", action="append", choices=ARMS, help="only these arms (repeatable)")
    check = sub.add_parser("preflight", help="one minimal request per arm, outside any lot")
    check.add_argument("--lot-free", action="store_true", required=True,
                       help="acknowledge that it runs in a temporary folder and binds no lot")
    check.add_argument("--arm", action="append", choices=sorted(PI_ARMS),
                       help="arms to check (default: bare, pi-tools, pi-full)")
    check.add_argument("--model", default=f"{PROVIDER}/{MODEL}")
    check.add_argument("--thinking", default=THINKING)
    check.add_argument("--pi-extension", help="the extension every arm loads, as in init-lot")
    check.add_argument("--timeout", type=int, default=PREFLIGHT_SECONDS, help="seconds per arm")
    args = parser.parse_args(argv)
    try:
        if args.action == "init-lot":
            scenarios = dict(item.split("=", 1) for item in args.scenario)
            lot = init_lot(Path(args.lot), lot_id=args.lot_id, authority=Path(args.authority),
                           scenarios=scenarios, arms=args.arm, repetitions=args.repetitions,
                           runs_root=Path(args.runs_root), arms_root=Path(args.arms_root),
                           jev_key_file=Path(args.jev_key_file) if args.jev_key_file else None,
                           model=args.model, thinking=args.thinking,
                           request_cap_seconds=args.request_cap, chain_cap_seconds=args.chain_cap,
                           pi_extension=Path(args.pi_extension) if args.pi_extension else None)
            result = {"lot": lot["lot"], "cells": len(lot["cells"])}
        elif args.action == "prepare-drivers":
            result = prepare_drivers(Path(args.lot), Path(args.source) if args.source else None,
                                     exact=bool(args.source))
        elif args.action == "run":
            record = run_cell(Path(args.lot), args.cell, args.through)
            result = {"cell": args.cell, "length": record["length"], "invalid": record["invalid"]}
        elif args.action == "judge-gated":
            result = judge_gated(Path(args.lot))
        elif args.action == "amend-suite":
            result = amend_suite(Path(args.lot), args.scenario, args.reason)
        elif args.action == "run-lot":
            result = run_lot(Path(args.lot), args.through, args.jobs, args.rep, args.arm)
        elif args.action == "preflight":
            result = preflight(args.arm or ["bare", "pi-tools", "pi-full"], model=args.model,
                               thinking=args.thinking, timeout_seconds=args.timeout,
                               pi_extension=Path(args.pi_extension) if args.pi_extension else None)
            print(json.dumps(result, indent=1, sort_keys=True))
            return 0 if result["ok"] else 1
        else:
            result = status(Path(args.lot))
    except (LotError, judge.JudgeError, OSError, subprocess.SubprocessError) as error:
        print(json.dumps({"ok": False, "error": f"{type(error).__name__}: {error}"}))
        return 2
    print(json.dumps(result, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
