"""A benchmark-only patched copy of pi-messenger for the Crew arms (DBH-33).

The installed pi-messenger cannot start Crew workers on Windows: it spawns ``pi.cmd`` without a
shell (``spawn EINVAL``). It also reads and writes the user's ``~/.pi/agent`` (config, feed,
agents, team profiles) and runs workers with ``--no-session``, so their cost is lost. The
runner never touches the user's package: it copies it and patches the copy at exact anchors.

- Workers start as ``process.execPath`` plus the argv in ``DBENCH_WORKER_ARGV`` (a JSON list:
  Pi's ``cli.js``, ``--session-dir`` and the profile flags), then pi-messenger's own arguments.
- ``--no-session`` leaves the workers' arguments: their sessions are kept and costed.
- Every home directory lookup reads ``DBENCH_MESSENGER_HOME`` first.
- The start-up deletion of ``messenger/feed.jsonl`` is gone.
- The npx installer ``install.mjs`` is not copied.

Each anchor must occur exactly the expected number of times; otherwise nothing is left at the
destination. A successful copy carries ``dbench-patch.json``.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
from pathlib import Path

MANIFEST = "dbench-patch.json"
HOME_ENV = "DBENCH_MESSENGER_HOME"
ARGV_ENV = "DBENCH_WORKER_ARGV"
HOME_IMPORT = 'import { homedir } from "node:os";'
HOME_WRAPPER = ('import { homedir as osHomedir } from "node:os";\n'
                f"const homedir = () => process.env.{HOME_ENV} || osHomedir();")
OS_HOME = "os.homedir()"
OS_HOME_WRAPPED = f"(process.env.{HOME_ENV} || os.homedir())"
ARGV_HELPER = f"""export function dbenchWorkerArgv(): string[] {{
  const raw = process.env.{ARGV_ENV};
  if (!raw) throw new Error("{ARGV_ENV} is not set: this pi-messenger copy only runs in the benchmark");
  return JSON.parse(raw) as string[];
}}

"""
WORKER_ARGS = 'const args = ["--mode", "json", "--no-session", "-p"];'
WORKER_ARGS_KEPT = 'const args = ["--mode", "json", "-p"];'
LOBBY_IMPORT = ("import { resolveThinking, modelHasThinkingSuffix, pushModelArgs, getPiCommand, "
                'resolveModel } from "./agents.ts";')

# (file, old, new, occurrences)
PATCHES: tuple[tuple[str, str, str, int], ...] = (
    ("crew/agents.ts", "export function getPiCommand(): string {",
     ARGV_HELPER + "export function getPiCommand(): string {", 1),
    ("crew/agents.ts", "spawn(getPiCommand(), args, {",
     "spawn(process.execPath, [...dbenchWorkerArgv(), ...args], {", 1),
    ("crew/agents.ts", WORKER_ARGS, WORKER_ARGS_KEPT, 1),
    ("crew/lobby.ts", LOBBY_IMPORT, LOBBY_IMPORT.replace("resolveModel }", "resolveModel, dbenchWorkerArgv }"), 1),
    ("crew/lobby.ts", "spawn(getPiCommand(), args, {",
     "spawn(process.execPath, [...dbenchWorkerArgv(), ...args], {", 1),
    ("crew/lobby.ts", WORKER_ARGS, WORKER_ARGS_KEPT, 1),
    ("index.ts", '    try { fs.rmSync(join(homedir(), ".pi/agent/messenger/feed.jsonl"), { force: true }); } catch {}\n',
     "", 1),
    ("index.ts", HOME_IMPORT, HOME_WRAPPER, 1),
    ("config.ts", HOME_IMPORT, HOME_WRAPPER, 1),
    ("crew/team/store.ts", HOME_IMPORT, HOME_WRAPPER, 1),
    ("crew/team/subagent-roles.ts", HOME_IMPORT, HOME_WRAPPER, 1),
    ("crew/utils/install.ts", HOME_IMPORT, HOME_WRAPPER, 1),
    ("crew/utils/config.ts", OS_HOME, OS_HOME_WRAPPED, 1),
    ("crew/utils/discover.ts", OS_HOME, OS_HOME_WRAPPED, 1),
)
RAW_HOME_IMPORT = re.compile(r'import\s*\{[^}]*\bhomedir\b[^}]*\}\s*from\s*["\'](node:)?os["\']')
# the package's npx installer (its "bin"): Pi never loads it and it writes the real ~/.pi
NOT_COPIED = ("node_modules", ".git", "install.mjs")
LEFTOVERS = ("getPiCommand(), args", '"--no-session"', "feed.jsonl\"), { force")


class PatchError(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*") if p.is_file() and "node_modules" not in p.relative_to(root).parts)


def _check_home(root: Path) -> None:
    """No home lookup may bypass the redirect, including ones a newer package adds."""
    for path in _files(root):
        if path.suffix not in {".ts", ".js", ".mjs", ".cjs"}:
            continue
        text = path.read_text(encoding="utf-8")
        rest = text.replace(HOME_WRAPPER, "").replace(OS_HOME_WRAPPED, "")
        rel = path.relative_to(root).as_posix()
        if RAW_HOME_IMPORT.search(rest) or OS_HOME in rest:
            raise PatchError(f"{rel} still reads the real home directory")
        if "homedir()" in rest and HOME_WRAPPER not in text:
            raise PatchError(f"{rel} calls homedir() without the {HOME_ENV} redirect")


def _patch(root: Path) -> list[dict]:
    applied = []
    for rel, old, new, count in PATCHES:
        path = root / rel
        if not path.is_file():
            raise PatchError(f"{rel} is missing")
        text = path.read_text(encoding="utf-8")
        found = text.count(old)
        if found != count:
            raise PatchError(f"{rel}: anchor {old[:60]!r} occurs {found} times, expected {count}")
        path.write_text(text.replace(old, new), encoding="utf-8", newline="")
        applied.append({"file": rel, "anchor": old, "occurrences": count})
    for path in _files(root):
        if path.suffix == ".ts":
            text = path.read_text(encoding="utf-8")
            for leftover in LEFTOVERS:
                if leftover in text:
                    raise PatchError(f"{path.relative_to(root).as_posix()} still contains {leftover!r}")
    _check_home(root)
    return applied


def prepare(source: Path, dest: Path) -> dict:
    """Copy ``source`` (an installed pi-messenger) to ``dest`` and patch it; return the manifest."""
    source, dest = Path(source).resolve(), Path(dest)
    if dest.exists():
        raise PatchError(f"{dest} already exists")
    package = json.loads((source / "package.json").read_text(encoding="utf-8"))
    if package.get("name") != "pi-messenger":
        raise PatchError(f"{source} is not pi-messenger")
    staging = dest.with_name(f"{dest.name}.tmp-{os.getpid()}")
    shutil.rmtree(staging, ignore_errors=True)
    try:
        shutil.copytree(source, staging, ignore=shutil.ignore_patterns(*NOT_COPIED))
        sources = {p.relative_to(staging).as_posix(): _sha256(p) for p in _files(staging)}
        applied = _patch(staging)
        manifest = {
            "package": "pi-messenger",
            "version": package.get("version"),
            "source": str(source),
            "source_sha256": sources,
            "patches": applied,
            "patched_sha256": {rel: _sha256(staging / rel) for rel in sorted({p[0] for p in PATCHES})},
        }
        (staging / MANIFEST).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        dest.parent.mkdir(parents=True, exist_ok=True)
        os.replace(staging, dest)
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    return manifest
