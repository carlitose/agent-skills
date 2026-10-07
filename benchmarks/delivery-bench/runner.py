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
                                  [--pi-extension FILE] [--timeout S] [--vague]

``init-lot --vague`` (DBH-38) hands the arms the short requests of ``requests-vague/`` and the
tool ``ask_user``; a simulated user (``--simulator-model``) answers from the precise requests.

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
from autopilot.command_capture import (
    MAX_TIMEOUT_SECONDS,
    CaptureFailure,
    capture_command,
)

import crew_messenger
import judge
import simulator

# Defaults for a lot that names no model; a lot records its own and every arm reads it from there.
PROVIDER, MODEL, THINKING = "openai-codex", "gpt-6-sol", "high"
PROMPT = ("Lee TASK.md en la raiz del repositorio y haz lo que pide, hasta el final. "
          "Trabaja solo en este directorio. Lo que cuenta es el estado de esta carpeta cuando termines.")
# A continued session saw the previous TASK.md: without this a model that gave up on request N-1
# finished N-1 again instead of reading N (DBH-25, lot dbh-luna3b).
NEXT_PROMPT = ("TASK.md ha cambiado: ahora contiene un encargo nuevo, distinto del anterior. "
               "Vuelve a leerlo y haz lo que pide ahora, hasta el final. Trabaja solo en este "
               "directorio. Lo que cuenta es el estado de esta carpeta cuando termines.")
SKILLS_ONLY_SUFFIX = (" Trabaja en modo skills-only: usa las skills instaladas de forma inline y no "
                      "arranques el runner, el scheduler ni ningun driver de Autopilot.")
AUTOPILOT_SUFFIX = (" Usa el flujo completo de ticket-autopilot, incluido su runner, para llevar este "
                    "trabajo de principio a fin. `origin` es un repositorio local sin proveedor de PR: "
                    "usa el runner con `--provider github --provider-mode simulated`; cuando el runner "
                    "no pueda fusionar, integra tú la rama en `main` de esta carpeta.")
# DBH-34: the Crew arms are pi-tools plus a patched pi-messenger copy (DBH-33) and its workers.
# crew-1's main works and has one worker; crew-2's main only manages two workers.
CREW_1_SUFFIX = (" Tienes un worker: con la herramienta pi_messenger creas tareas (`task.create`) y las "
                 "lanzas con `work`; el worker las hace en este mismo directorio. Usalo cuando te ayude.")
CREW_2_SUFFIX = (" Eres el coordinador y no modificas archivos tu mismo: divide el trabajo en tareas con la "
                 "herramienta pi_messenger (`task.create`) y lanzalas con `work`; dos workers las hacen en "
                 "este mismo directorio. Revisa lo que entregan y repite hasta terminar.")
CREW_ARMS = {"crew-1": 1, "crew-2": 2}  # arm -> workers
CREW_SKILLS = ("pi-messenger-crew",)  # the copy's guide to its own tool, loaded with it despite --no-skills
ARMS = ("bare", "skills-only", "autopilot", "driver-c1a", "driver-c3a", "pi-tools", "pi-full", "bare-goal",
        *CREW_ARMS)
PI_ARMS = {"bare": (["--no-skills"], ""), "skills-only": ([], SKILLS_ONLY_SUFFIX),
           "autopilot": ([], AUTOPILOT_SUFFIX), "pi-tools": (["--no-skills"], ""), "pi-full": ([], ""),
           "bare-goal": (["--no-skills"], ""), "crew-1": (["--no-skills"], CREW_1_SUFFIX),
           "crew-2": (["--no-skills"], CREW_2_SUFFIX)}
# The closed list of extensions an arm loads with -e despite --no-extensions, relative to the
# installed pi-personal-config (DBH-21). Memory, Telegram, Messenger, MCP, subagents and the
# other personal extensions stay out of every arm: they would skew or soil the measure.
# DBH-27: `bare-goal` is bare Pi plus the goal alone, so the goal's effect is measured apart from tools.
GOAL_EXTENSION = "node_modules/pi-code/extensions/goal.ts"
TOOL_PROFILE = ("extensions/pi-code-tool/index.ts", "node_modules/pi-code/extensions/todo.ts",
                "node_modules/pi-code/extensions/plan-mode", "node_modules/pi-code/extensions/web.ts",
                GOAL_EXTENSION)
# DBH-26: the profiled arms work under `/goal`: after every turn an evaluator (the session model)
# checks the condition and, while it does not hold, sends the model back to work. In dbh-luna3c
# luna stopped mid-plan ("no he podido") on almost every request. `pi -p` takes the usual request
# first, so pi-full's input is still routed through ask-skills (a slash command is not), then
# `/goal`, which holds the process open until the goal is achieved, judged impossible, or paused
# after repeated idle turns.
# The evaluator's own calls are not session messages: their tokens reach only the goal summary.
GOAL_ARMS = ("pi-tools", "pi-full", "bare-goal", *CREW_ARMS)  # a Crew main, not its workers
GOAL_CONDITION = ("Lo que pide TASK.md (en la raiz del repositorio) esta hecho por completo, trabajando solo "
                  "en este directorio, y la ultima salida de las pruebas y comprobaciones que indica el "
                  "repositorio muestra que pasan.")
NEXT_GOAL_CONDITION = ("TASK.md ha cambiado: ahora contiene un encargo nuevo, distinto del anterior. "
                       + GOAL_CONDITION.replace("Lo que pide", "Lo que pide ahora"))
MANDATORY_EXTENSION = "node_modules/carlitose-agent-skills-pi/extensions/mandatory-agent-skills.ts"
ARM_PROFILES = {"pi-tools": TOOL_PROFILE, "pi-full": (*TOOL_PROFILE, MANDATORY_EXTENSION),
                "bare-goal": (GOAL_EXTENSION,), "crew-1": TOOL_PROFILE, "crew-2": TOOL_PROFILE}
MESSENGER_PACKAGE = "node_modules/pi-messenger"
# A worker gets pi-tools' tools without the goal; pi-messenger's worker agent allows only the first five.
WORKER_TOOLS = "read, write, edit, bash, pi_messenger, code, todo, plan_mode_complete, web_search, web_fetch"
WORKER_AGENT_ANCHORS = ("tools: read, write, edit, bash, pi_messenger\n", "model: anthropic/claude-haiku-4-5\n")
# What the preflight expects each extension to add, and which arms must see the skills.
EXTENSION_TOOLS = dict(zip(ARM_PROFILES["pi-full"], (
    ("code",), ("todo",), ("plan_mode_complete",), ("web_search", "web_fetch"), (), ())))
BUILTIN_TOOLS = ("read", "bash", "edit", "write")
ARM_SKILLS = {"bare": False, "skills-only": True, "autopilot": True, "pi-tools": False, "pi-full": True,
              "bare-goal": False, "crew-1": False, "crew-2": False}
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
CREW_PREFLIGHT_TASK = PREFLIGHT_TASK.replace("3. Reply `done`.", """3. With the `pi_messenger` tool create one task
   (`task.create`) whose work is to write the text `ok` to the file `worker.txt`, then run it
   (`work`) so that a worker does it. Do not write `worker.txt` yourself.
4. Reply `done`.""")
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
                "TICKET_DRIVER_PI_EXTENSION", "PI_MESSENGER_DIR", crew_messenger.HOME_ENV,
                crew_messenger.ARGV_ENV, simulator.ENV)
# DBH-38: a vague-request lot hands the arm a short request (requests-vague/) and the tool
# `ask_user`, which every Pi arm loads; a simulated user answers it from the precise requests.
ASK_USER_EXTENSION = HERE / "ask_user" / "index.ts"
SIMULATOR_SCRIPT = HERE / "simulator.py"
SIMULATOR_MODEL, SIMULATOR_THINKING = "openai-codex/gpt-6-sol", "medium"
VAGUE_REQUESTS = "requests-vague"
PREFLIGHT_BRIEF = "# Encargo\n\nMe llamo Ana y soy quien ha pedido este trabajo.\n"
PREFLIGHT_QUESTION = "¿Cómo te llamas?"
VAGUE_PREFLIGHT_STEP = (f"3. Call the tool `ask_user` once with the question `{PREFLIGHT_QUESTION}`.\n"
                        "4. Reply `done`.")
# a provider failure that can end a session after the model worked: quota, overload, server or
# network, never a request the arm made invalid (DBH-19)
TRANSIENT_PROVIDER = re.compile(
    r"rate[_ ]limit|overloaded|\b(429|500|502|503|504|529)\b|service unavailable|bad gateway|"
    r"gateway timeout|internal server error|\bapi_error\b|websocket closed|econnreset|etimedout|"
    r"socket hang up|connection (reset|closed|refused)|fetch failed",
    re.IGNORECASE)
# goal.ts reports each evaluator verdict as a `goal` custom message ("Goal not yet met (turn 2 ...")
GOAL_VERDICT = re.compile(r"Goal (not yet met|achieved|could not be achieved)")
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


def bind_crew_messenger(arms: list, dest: Path, root: Path | None = None) -> dict | None:
    """The patched pi-messenger copy the Crew arms load (DBH-33), made once per lot."""
    if not any(arm in CREW_ARMS for arm in arms):
        return None
    root = Path(root).resolve() if root else installed_pi_config()
    try:
        manifest = crew_messenger.prepare(root / MESSENGER_PACKAGE, dest)
    except (crew_messenger.PatchError, OSError, ValueError) as error:
        raise LotError(f"cannot prepare the pi-messenger copy: {error}") from None
    return {"path": str(Path(dest).resolve()), "version": manifest["version"],
            "sha256": judge.tree_digest(Path(dest))["sha256"]}


def crew_extension(lot: dict, arm: str) -> list:
    if arm not in CREW_ARMS:
        return []
    copy = lot.get("crew_messenger")
    if not copy:
        raise LotError(f"the lot binds no pi-messenger copy for arm {arm}")
    return [copy]


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
    for entry in crew_extension(lot, arm):  # a whole package folder
        path = Path(entry["path"])
        if not path.is_dir() or judge.tree_digest(path)["sha256"] != entry["sha256"]:
            raise LotError(f"the pi-messenger copy {path} changed or disappeared after the lot was bound")
    return bound + crew_extension(lot, arm)


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
             pi_config_root: Path | None = None, vague: bool = False,
             simulator_model: str = SIMULATOR_MODEL, simulator_thinking: str = SIMULATOR_THINKING,
             simulator_command: list | None = None) -> dict:
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
    if vague != (grant.get("variant") == "vague"):
        raise LotError("a vague-request lot needs an authority with variant 'vague', and only it")
    if vague and not set(arms) <= set(PI_ARMS):
        raise LotError("a vague-request lot runs Pi arms only: the tool is a Pi extension")
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
        if vague:
            length = min(document["requests"], grant["max_length"])
            missing = [n for n in range(1, length + 1) if not (path / VAGUE_REQUESTS / f"{n:02d}.md").is_file()]
            if missing:
                raise LotError(f"scenario {name} has no vague request {missing[0]:02d}")
            described[name].update(requests_dir=VAGUE_REQUESTS,
                                   vague_sha256=judge.tree_digest(path / VAGUE_REQUESTS)["sha256"],
                                   requests_sha256=judge.tree_digest(path / "requests")["sha256"])
    # outside the lot folder and the private tree: the arms' sessions name this path (audit)
    crew = bind_crew_messenger(arms, runs_root / lot_id / "pi-messenger", pi_config_root)
    ask = None
    if vague:
        sim_provider, _, sim_model = simulator_model.partition("/")
        if not sim_provider or not sim_model or not simulator_thinking:
            raise LotError("the simulated user's model is PROVIDER/ID and needs a thinking level")
        tool = {"path": str(ASK_USER_EXTENSION), "sha256": _folder_digest(ASK_USER_EXTENSION)}
        arm_extensions = {arm: [*arm_extensions.get(arm, []), tool] for arm in arms}
        ask = {"limit": simulator.LIMIT, "provider": sim_provider, "model": sim_model,
               "thinking": simulator_thinking, "script_sha256": sha256_file(SIMULATOR_SCRIPT),
               "pi_command": list(simulator_command) if simulator_command else None}
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
           "arm_extensions": arm_extensions, "crew_messenger": crew, "scenarios": described, "cells": cells, "driver_copies": {},
           **({"vague": ask} if ask else {})}
    if ask and not ask["pi_command"]:
        ask["pi_command"] = lot["pi_command"]
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
        if "vague_sha256" in scenario and (
                judge.tree_digest(path / VAGUE_REQUESTS)["sha256"] != scenario["vague_sha256"]
                or judge.tree_digest(path / "requests")["sha256"] != scenario["requests_sha256"]):
            raise LotError(f"the requests of scenario {name} changed after the lot was bound")
    if lot.get("vague") and sha256_file(SIMULATOR_SCRIPT) != lot["vague"]["script_sha256"]:
        raise LotError("the simulated user's script changed after the lot was bound")
    extension = lot.get("pi_extension")
    if extension and (not Path(extension["path"]).is_file()
                      or judge.tree_digest(Path(extension["path"]).parent)["sha256"] != extension["sha256"]):
        raise LotError("the Pi extension changed or disappeared after the lot was bound")
    for arm in lot.get("arm_extensions") or {}:
        check_arm_extensions(lot, arm)  # the Crew arms' pi-messenger copy too
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
    folder = scenario.get("requests_dir", "requests")
    raw = (Path(scenario["path"]) / folder / f"{n:02d}.md").read_text(encoding="utf-8")
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
        messages = [(NEXT_PROMPT if n > 1 else PROMPT) + suffix]
        if info["arm"] in GOAL_ARMS:  # the request first, as before (pi-full routes it), then the goal
            messages.append("/goal " + (NEXT_GOAL_CONDITION if n > 1 else GOAL_CONDITION))
        return [*argv, *(["--continue"] if n > 1 else []), "--", *messages]
    return [*lot["scenarios"][info["scenario"]]["driver"], "run",
            "--candidate", info["arm"].split("-", 1)[1], "--task", str(project / "TASK.md"),
            "--repo", str(project), "--live-authorization",
            str((arm_dir / "driver-authorization.json").resolve())]


def extension_args(lot: dict) -> list[str]:
    return ["-e", lot["pi_extension"]["path"]] if lot.get("pi_extension") else []


def profile_args(lot: dict, arm: str) -> list[str]:
    entries = bound_extensions(lot, arm) + crew_extension(lot, arm)
    return [flag for entry in entries for flag in ("-e", entry["path"])]


def worker_argv(lot: dict, arm: str, arm_dir: Path) -> list[str]:
    """What a Crew worker runs after the main's own Node (DBH-33): Pi's script, its own session
    folder, the arm's profile without the goal. pi-messenger adds the model, the tools, the copy
    itself and the task."""
    if len(lot["pi_command"]) < 2:
        raise LotError("a Crew arm needs a Pi command of the form NODE SCRIPT")
    goal = GOAL_EXTENSION.split("node_modules/", 1)[1]
    flags = [flag for entry in bound_extensions(lot, arm)
             if not Path(entry["path"]).as_posix().endswith(goal) for flag in ("-e", entry["path"])]
    return [*lot["pi_command"][1:], "--session-dir", str(Path(arm_dir) / "worker-sessions"),
            "--no-extensions", "--no-skills", "--no-context-files", "--approve", *extension_args(lot), *flags]


def arm_environment(lot: dict, arm: str, arm_dir: Path | None = None) -> dict:
    env = {key: value for key, value in os.environ.items() if key not in STRIPPED_ENV}
    if arm in CREW_ARMS:  # the arm's own mesh and home: nothing reaches the user's ~/.pi/agent
        arm_dir = Path(arm_dir).resolve()
        env["PI_MESSENGER_DIR"] = str(arm_dir / "messenger")
        env[crew_messenger.HOME_ENV] = str(arm_dir / "messenger-home")
        env[crew_messenger.ARGV_ENV] = json.dumps(worker_argv(lot, arm, arm_dir))
    if arm.startswith("driver-") and lot.get("pi_extension"):
        env["TICKET_DRIVER_PI_EXTENSION"] = lot["pi_extension"]["path"]  # the leaf adds it with -e
    if arm == "driver-c3a":
        env["TYPESAFE_API_KEY"] = read_jev_key(Path(lot["jev_key_file"]))
    return env


def prepare_crew(lot: dict, arm: str, arm_dir: Path, n: int) -> dict:
    """Before request n: an empty plan holding TASK.md, the Crew config and the worker agent.

    The previous request's Crew folder (its tasks) is kept in crew-history. Planner and reviewer
    stay off: the main creates the tasks itself.
    """
    project = Path(arm_dir) / "project"
    crew = project / ".pi" / "messenger" / "crew"
    archived = None
    if crew.exists():
        try:
            earlier = json.loads((crew / "plan.json").read_text(encoding="utf-8")).get("dbench_request")
        except (OSError, ValueError):
            earlier = None
        if earlier == n:  # this request's own setup, written before a host stop: write it again
            rmtree(crew)
        else:
            target = Path(arm_dir) / "crew-history" / (f"{earlier:02d}" if isinstance(earlier, int) else "unknown")
            if target.exists():
                rmtree(target)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(native_path(crew), native_path(target))
            archived = target.name
    source = Path(crew_extension(lot, arm)[0]["path"]) / "crew" / "agents" / "crew-worker.md"
    agent = source.read_text(encoding="utf-8")
    tools, model = WORKER_AGENT_ANCHORS
    if agent.count(tools) != 1 or agent.count(model) != 1:
        raise LotError(f"{source} no longer has the worker's tools and model lines")
    agent = agent.replace(tools, f"tools: {WORKER_TOOLS}\n").replace(
        model, f"model: {lot['provider']}/{lot['model']}\nthinking: {lot['thinking']}\n")
    workers, stamp = CREW_ARMS[arm], now()
    (crew / "agents").mkdir(parents=True)
    (crew / "agents" / "crew-worker.md").write_text(agent, encoding="utf-8")
    (crew / "plan.md").write_text((project / "TASK.md").read_text(encoding="utf-8"), encoding="utf-8")
    dump(crew / "plan.json", {"prd": "TASK.md", "created_at": stamp, "updated_at": stamp, "task_count": 0,
                              "completed_count": 0, "dbench_request": n})
    dump(crew / "config.json", {
        "models": {"worker": f"{lot['provider']}/{lot['model']}"}, "thinking": {"worker": lot["thinking"]},
        "concurrency": {"workers": workers, "max": workers},  # max caps a `work` that asks for more
        "review": {"enabled": False, "maxIterations": 0}, "planSync": {"enabled": False},
        "memory": {"enabled": False}})
    return {"workers": workers, "archived": archived}


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
    goal = {"rounds": 0, "sent_back": 0, "end": None}
    last, last_ts = {}, None
    for event in events:
        stamp = _timestamp(event.get("timestamp"))
        if stamp is not None:
            last_ts = stamp if last_ts is None else max(last_ts, stamp)
        if event.get("type") == "custom_message" and event.get("customType") == "goal":
            verdict = GOAL_VERDICT.match(_text(event.get("content")))
            if verdict:  # one evaluator round: the goal sent the model back, or ended
                goal["rounds"] += 1
                if verdict.group(1) == "not yet met":
                    goal["sent_back"] += 1
                else:
                    goal["end"] = "achieved" if verdict.group(1) == "achieved" else "impossible"
            continue
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
    return {"usage": usage, "compaction": compaction, "goal": goal, "assistant_messages": assistant,
            "with_output": with_output,
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
    workers_root = [arm_dir / "worker-sessions"]
    workers_before = cursor(workers_root)
    argv, env = arm_argv(lot, info, n), arm_environment(lot, info["arm"], arm_dir)
    ask_log = None
    if lot.get("vague"):
        ask_log = logs.parent / "ask-user" / f"{n:02d}-a{number}.jsonl"
        env[simulator.ENV] = ask_user_setup(lot, info["scenario"], n, ask_log)
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
    crew = {}
    if info["arm"] in CREW_ARMS:  # the workers' spend is the request's too, and reported apart
        crew = crew_spend(summary, workers_root, workers_before)
    facts, jev = driver_facts(project, sorted(driver_runs(project) - runs_before))
    last = summary.pop("last_ts")
    seconds = round(last - started, 3) if last is not None and started <= last <= started + wall + 1 else wall
    kind = classify(code, failure, summary)
    ask = {}
    if ask_log is not None:  # the simulated user's spend is its own, never the arm's
        ask = {"ask_user": simulator.summarize_log(ask_log)}
        if kind == "agent" and ask["ask_user"]["errors"]:  # a question it could not answer
            kind = "infra:simulator"
    return {"attempt": number, "class": kind, **ask, "exit": code,
            "failure": failure, "timeout_seconds": round(timeout, 3), "wall_seconds": wall,
            "seconds": seconds, **summary, **crew, "jev": jev,
            **({"driver": facts} if info["arm"].startswith("driver-") else {})}


def forbidden_names(scenario: dict) -> list[str]:
    """What an answer of the simulated user must never name: the canary and the hidden suite's own
    file names (the seed's are public)."""
    path = Path(scenario["path"])
    seed = {p.name for p in (path / "seed").rglob("*") if p.is_file()}
    hidden = {p.name for p in (path / "hidden").rglob("*") if p.is_file()}
    return sorted(name for name in hidden - seed if len(name) > 4) + [scenario["canary"]]


def ask_user_setup(lot: dict, scenario_name: str, n: int, log: Path, *, cache: Path | None = None,
                   brief: list | None = None) -> str:
    """Write the attempt's simulator config into the lot folder; return the value of DBENCH_ASK_USER.

    The config holds the canary: an arm that reads it is caught by the audit. The brief is the
    chain's precise requests so far; the cache is shared by every arm and repetition.
    """
    scenario, ask = lot["scenarios"].get(scenario_name), lot["vague"]
    simulated = Path(lot["dir"]) / "simulator"
    config = {"brief": brief or [str(Path(scenario["path"]) / "requests" / f"{k:02d}.md") for k in range(1, n + 1)],
              "cache": str(cache or simulated / "cache" / f"{scenario_name}-{n:02d}.json"),
              "log": str(log), "sessions": str(simulated / "sessions"), "limit": ask["limit"],
              "retry_seconds": list(ask.get("retry_seconds", simulator.RETRY_SECONDS)),
              "forbidden": forbidden_names(scenario) if scenario else [],
              **{key: ask[key] for key in ("provider", "model", "thinking", "pi_command")}}
    path = Path(log).with_suffix(".config.json")
    dump(path, config)
    return json.dumps({"python": sys.executable, "script": str(SIMULATOR_SCRIPT), "config": str(path)})


def crew_spend(summary: dict, roots: list[Path], before: dict) -> dict:
    """Add the workers' sessions to the main's usage; return both apart. The main alone decides
    the attempt's class and time."""
    started = [path for path in cursor(roots) if path not in before]
    workers = summarize(new_events(roots, before))
    workers.pop("last_ts")
    main = dict(summary["usage"])
    summary["usage"] = {key: round(main[key] + workers["usage"][key], 6) if key == "cost_usd"
                        else main[key] + workers["usage"][key] for key in main}
    return {"main_usage": main, "workers": {"sessions": len(started), **{key: workers[key] for key in (
        "usage", "compaction", "assistant_messages", "tool_calls", "last_stop", "last_error")}}}


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


def keep_objects(run, store: Path, base: str, tree: str) -> None:
    """Pack into `store` the objects of `base` (commit or tree) and `tree` that it does not hold."""
    wanted = {base, tree}
    for start in (f"{base}^{{tree}}", tree):
        wanted.add(run("rev-parse", start).decode().strip())
        wanted.update(run("ls-tree", "-r", "-t", "--object-only", start).decode().split())
    own = {**os.environ, "GIT_OBJECT_DIRECTORY": str(store), "GIT_ALTERNATE_OBJECT_DIRECTORIES": ""}
    listing = subprocess.run(["git", "cat-file", "--batch-check=%(objectname)"], input="\n".join(sorted(wanted)).encode(),
                             env=own, capture_output=True, check=True, timeout=600).stdout.decode()
    missing = [line.split()[0] for line in listing.splitlines() if line.endswith(" missing")]
    if missing:
        (store / "pack").mkdir(exist_ok=True)
        run("pack-objects", "-q", str(store / "pack" / "pack"), input=("\n".join(missing) + "\n").encode())


def request_diff(project: Path, base: str, target: Path, store: Path) -> dict:
    """What the arm changed during one request, kept for a later review (DBH-24).

    `base` is the tree the previous request left (or the delivered commit): an arm that never
    commits still gets one request's work per diff. The work tree is written as a tree into the
    cell's own object `store`, with a temporary index: the arm's repository is untouched. The
    request text itself (`TASK.md`) is left out. The store then receives every object of `base`
    and of the tree that it still lacks, so both trees can be rebuilt from the store alone, even
    after the arm's repository is gone.
    """
    project, store = Path(project).resolve(), Path(store).resolve()
    try:
        store.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="dbench-diff-") as scratch:
            env = {**os.environ, "GIT_INDEX_FILE": str(Path(scratch) / "index"),
                   "GIT_OBJECT_DIRECTORY": str(store),
                   "GIT_ALTERNATE_OBJECT_DIRECTORIES": str(project / ".git" / "objects")}

            def run(*args: str, input: bytes | None = None) -> bytes:
                return subprocess.run(["git", "-C", str(project), "-c", "core.quotepath=false", *args],
                                      env=env, input=input, capture_output=True, check=True, timeout=600).stdout
            run("read-tree", base)
            run("add", "-A")
            tree = run("write-tree").decode().strip()
            scope = ("--", ".", ":(exclude)TASK.md")
            files = run("diff", "--name-only", base, tree, *scope).decode("utf-8", "replace").splitlines()
            diff = run("diff", "--no-color", "--no-ext-diff", base, tree, *scope)
            keep_objects(run, store, base, tree)
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
            if info["arm"] in CREW_ARMS:  # before the snapshot: a repeated attempt starts from it too
                request["crew"] = prepare_crew(lot, info["arm"], arm_dir, n)
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
                   cost_usd=attempt["usage"]["cost_usd"], goal_rounds=attempt["goal"]["rounds"],
                   **({"main_cost_usd": attempt["main_usage"]["cost_usd"],
                       "worker_cost_usd": attempt["workers"]["usage"]["cost_usd"],
                       "worker_sessions": attempt["workers"]["sessions"]} if "workers" in attempt else {}),
                   **({"questions": attempt["ask_user"]["questions"],
                       "simulator_cost_usd": attempt["ask_user"]["cost_usd"]} if "ask_user" in attempt else {}))
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
            goal=last.get("goal") or {"rounds": 0, "sent_back": 0, "end": None},
            **({key: last[key] for key in ("main_usage", "workers")} if "workers" in last else {}),
            **({"ask_user": last["ask_user"]} if "ask_user" in last else {}),
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
                       timeout: float, vague: bool = False) -> list[str]:
    profile = ARM_PROFILES.get(arm, ())
    expected = sorted({*BUILTIN_TOOLS, *(t for e in profile for t in EXTENSION_TOOLS[e]),
                       *(["pi_messenger"] if arm in CREW_ARMS else []), *(["ask_user"] if vague else [])})
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
    stray = [s for s in observed["skills"] if not (arm in CREW_ARMS and s in CREW_SKILLS)]
    if not ARM_SKILLS[arm] and stray:
        problems.append(f"skills visible in an arm without skills: {stray[:5]}")
    if observed["routed"] != (MANDATORY_EXTENSION in profile):
        problems.append("the mandatory rule " + ("did not route" if MANDATORY_EXTENSION in profile
                                                 else "routed an arm without it"))
    if "code" in expected and observed["code_write"] != "ok":
        problems.append(f"the `code` write did not succeed in -p: {observed['code_write']}")
    return problems


HOST_MESSENGER = (Path.home() / ".pi" / "agent" / "messenger", Path.home() / ".pi" / "agent" / "pi-messenger.json")


def host_messenger_state() -> dict:
    """The user's own pi-messenger state, which a Crew arm must leave as it found it."""
    state = {}
    for path in HOST_MESSENGER:
        if path.is_dir():
            state[str(path)] = judge.tree_digest(path)["sha256"]
        else:
            state[str(path)] = sha256_file(path) if path.is_file() else None
    return state


def preflight(arms: list[str], *, model: str = f"{PROVIDER}/{MODEL}", thinking: str = THINKING,
              pi_command: list | None = None, pi_extension: Path | None = None,
              pi_config_root: Path | None = None, timeout_seconds: float = PREFLIGHT_SECONDS,
              vague: bool = False, simulator_model: str = SIMULATOR_MODEL,
              simulator_thinking: str = SIMULATOR_THINKING, simulator_command: list | None = None) -> dict:
    """One minimal request per arm in a temporary folder, with the argv a lot would use (DBH-21).

    It belongs to no lot and counts as no attempt; it spends a few cents on a real model. With
    `vague` every arm also asks the simulated user one real question (DBH-38).
    """
    provider, _, model_id = model.partition("/")
    if not provider or not model_id or not set(arms) <= set(PI_ARMS):
        raise LotError(f"preflight needs PROVIDER/ID and Pi arms only: {sorted(PI_ARMS)}")
    report = {}
    with tempfile.TemporaryDirectory(prefix="dbench-preflight-", ignore_cleanup_errors=True) as folder:
        lot = {"provider": provider, "model": model_id, "thinking": thinking,
               "pi_command": list(pi_command) if pi_command else resolve_pi(),
               "pi_extension": bind_extension(pi_extension),
               "arm_extensions": bind_arm_extensions(arms, pi_config_root),
               "crew_messenger": bind_crew_messenger(arms, Path(folder) / "pi-messenger", pi_config_root)}
        if vague:
            sim_provider, _, sim_model = simulator_model.partition("/")
            tool = {"path": str(ASK_USER_EXTENSION), "sha256": _folder_digest(ASK_USER_EXTENSION)}
            lot.update(dir=folder, scenarios={}, vague={
                "limit": simulator.LIMIT, "provider": sim_provider, "model": sim_model,
                "thinking": simulator_thinking,
                "pi_command": list(simulator_command) if simulator_command else lot["pi_command"]})
            lot["arm_extensions"] = {arm: [*lot["arm_extensions"].get(arm, []), tool] for arm in arms}
            (Path(folder) / "brief.md").write_text(PREFLIGHT_BRIEF, encoding="utf-8")
        for arm in arms:
            arm_dir = Path(folder) / arm
            project = arm_dir / "project"
            project.mkdir(parents=True)
            crew = arm in CREW_ARMS
            task = CREW_PREFLIGHT_TASK if crew else PREFLIGHT_TASK
            if vague and not crew:
                task = task.replace("3. Reply `done`.", VAGUE_PREFLIGHT_STEP)
            (project / "TASK.md").write_text(task, encoding="utf-8")
            dump(project / ".pi" / "settings.json", PI_SETTINGS)
            if crew:
                prepare_crew(lot, arm, arm_dir, 1)
            host = host_messenger_state()
            argv = arm_argv(lot, {"arm": arm, "arm_dir": str(arm_dir)}, 1)
            code, failure, err = None, None, b""
            env = arm_environment(lot, arm, arm_dir)
            ask_log = arm_dir / "ask-user.jsonl"
            if vague:
                env[simulator.ENV] = ask_user_setup(lot, "preflight", 1, ask_log, cache=arm_dir / "cache.json",
                                                    brief=[str(Path(folder) / "brief.md")])
            try:
                with environment(env):
                    _out, err, code = capture_command(argv, cwd=project, timeout_seconds=timeout_seconds,
                                                      max_output_bytes=OUTPUT_LIMIT)
            except CaptureFailure as error:
                failure, err = error.reason, error.stderr
            events = new_events([arm_dir / "sessions"], {})
            observed = read_session(events, project)
            problems = preflight_problems(arm, observed, code, failure, timeout_seconds, vague)
            summary = summarize(events)
            extra = {}
            if vague:
                extra["ask_user"] = simulator.summarize_log(ask_log)
                answers = [json.loads(line).get("answer") or "" for line in
                           (ask_log.read_text(encoding="utf-8").splitlines() if ask_log.is_file() else [])]
                if not answers:
                    problems.append("ask_user was not called")
                elif not any("ana" in answer.lower() for answer in answers):
                    problems.append(f"the simulated user did not answer from its brief: {answers[0][:200]!r}")
            if crew:
                extra = crew_spend(summary, [arm_dir / "worker-sessions"], {})
                workers = extra["workers"]
                if not workers["sessions"]:
                    problems.append("no worker started")
                elif not workers["usage"]["cost_usd"] > 0:
                    problems.append("the workers' cost was not read from their sessions")
                extra["host_messenger_unchanged"] = host_messenger_state() == host
                if not extra["host_messenger_unchanged"]:
                    problems.append("~/.pi/agent/messenger or pi-messenger.json changed")
            report[arm] = {"ok": not problems, "problems": problems, "exit": code, "failure": failure,
                           **observed, "cost_usd": summary["usage"]["cost_usd"], **extra,
                           "extensions": lot["arm_extensions"][arm] + crew_extension(lot, arm),
                           "stderr_tail": err[-2000:].decode("utf-8", "replace")}
    return {"ok": all(arm["ok"] for arm in report.values()), "model": model, "thinking": thinking,
            **({"simulator": {"model": simulator_model, "thinking": simulator_thinking}} if vague else {}),
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
    init.add_argument("--vague", action="store_true", help="vague requests and the simulated user (DBH-38)")
    init.add_argument("--simulator-model", default=SIMULATOR_MODEL, help="PROVIDER/ID of the simulated user")
    init.add_argument("--simulator-thinking", default=SIMULATOR_THINKING)
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
                       help="arms to check (default: bare, pi-tools, pi-full, bare-goal)")
    check.add_argument("--model", default=f"{PROVIDER}/{MODEL}")
    check.add_argument("--thinking", default=THINKING)
    check.add_argument("--pi-extension", help="the extension every arm loads, as in init-lot")
    check.add_argument("--timeout", type=int, default=PREFLIGHT_SECONDS, help="seconds per arm")
    check.add_argument("--vague", action="store_true", help="also ask the simulated user one real question")
    check.add_argument("--simulator-model", default=SIMULATOR_MODEL)
    check.add_argument("--simulator-thinking", default=SIMULATOR_THINKING)
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
                           pi_extension=Path(args.pi_extension) if args.pi_extension else None,
                           vague=args.vague, simulator_model=args.simulator_model,
                           simulator_thinking=args.simulator_thinking)
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
            result = preflight(args.arm or ["bare", "pi-tools", "pi-full", "bare-goal"], model=args.model,
                               thinking=args.thinking, timeout_seconds=args.timeout,
                               pi_extension=Path(args.pi_extension) if args.pi_extension else None,
                               vague=args.vague, simulator_model=args.simulator_model,
                               simulator_thinking=args.simulator_thinking)
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
