#!/usr/bin/env python3
"""Find the transcripts that belong to one project, for the providers a binding names.

Each provider identifies a project in a completely different way, and getting any of them
wrong yields zero sessions — which reads as "this project has no history" rather than as an
error. Which providers are consulted is the binding's decision: a provider a binding does not
name is not computed at all, because a zero beside its name would be a claim about a store
nothing looked at.

Claude Code
    Sessions live in ``~/.claude/projects/<mangled>/*.jsonl``, where ``<mangled>`` is the
    session's **startup** working directory with every single non-alphanumeric character
    replaced by ``-``. That is why ``C:\\Users\\Ada`` becomes ``C--Users-Ada``: the colon
    and the separator each contribute one dash. Collapsing runs of separators into a single
    dash is a different rule and loses that Windows drive-prefix distinction.

    The directory name is the project identity. The ``cwd`` recorded *inside* a transcript is
    not: it changes as the session moves around, so one project directory holds records whose
    ``cwd`` points at subdirectories. Filtering Claude sessions by in-file ``cwd`` would
    silently drop most of them.

Codex
    Sessions live in ``~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl``, undivided by project,
    and identity is a field: ``session_meta.payload.cwd``. Here the ``cwd`` *is* the session's
    startup directory, so filtering on it is correct — the mirror image of Claude.

Pi
    Sessions live under a **configured** root, by default ``~/.pi/agent/sessions``, in a
    ``--<mangled-cwd>--`` directory per project. Identity is the ``cwd`` of the first
    ``type: "session"`` record, not the directory: Pi rotates an oversized transcript into
    ``_oversized-backup/``, which strips its project directory and keeps its ``cwd``. Reading
    the file rather than its parent therefore needs no special case for rotation, and the
    directory is only a place, never an identity.

Usage:
    python3 session_discovery.py <project-root> [--json] [--providers a,b]
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

CLAUDE_ROOT = Path.home() / ".claude" / "projects"
CODEX_ROOT = Path.home() / ".codex" / "sessions"
NON_ALPHANUMERIC = re.compile(r"[^A-Za-z0-9]")
CLAUDE_TIMESTAMP_FIELD = "timestamp"
CODEX_TIMESTAMP_FIELDS = ("timestamp", "payload.timestamp")
PI_TIMESTAMP_FIELD = "timestamp"
#: Pi's own names, read from its resolver rather than assumed.
PI_AGENT_DIR_ENV = "PI_CODING_AGENT_DIR"
PI_SESSION_DIR_ENV = "PI_CODING_AGENT_SESSION_DIR"
PI_CONFIG_DIR_NAME = ".pi"
PI_SESSION_RECORD = "session"
#: Providers this module can discover, and the set a binding gets when it names none.
KNOWN_PROVIDERS = ("claude-code", "codex", "pi")
DEFAULT_PROVIDERS = ("claude-code", "codex")


class DiscoveryError(RuntimeError):
    """A provider store is absent, unknown, or a project directory cannot be accounted for."""


def mangle_path(path: str | Path) -> str:
    """Return the Claude project-directory name for an absolute path.

    Every single non-alphanumeric character becomes one dash. Collapsing a run into one dash
    is a different rule: it loses the double dash produced by a Windows drive prefix.
    """

    return NON_ALPHANUMERIC.sub("-", str(path))


def claude_project_directory(project_root: Path) -> Path:
    """Return the Claude store directory for a project root, whether or not it exists."""

    return CLAUDE_ROOT / mangle_path(project_root)


def claude_transcripts(project_root: Path) -> list[Path]:
    """Return this project's Claude transcripts, sorted.

    Only ``*.jsonl`` files directly inside the project directory are transcripts. Everything
    else is excluded by an explicit rule rather than by a glob that happens to miss it:
    ``memory/`` holds durable notes, and the UUID-named directories hold per-session tool
    results and task output.
    """

    directory = claude_project_directory(project_root)
    if not directory.is_dir():
        return []
    return sorted(
        path for path in directory.iterdir() if path.is_file() and path.suffix == ".jsonl"
    )


def unaccounted_claude_directories() -> list[str]:
    """Return store directories no absolute path could have produced.

    Reported rather than skipped. A name the rule cannot reproduce is either a store from a
    different naming scheme or a directory that does not belong here, and silently ignoring it
    would hide both.
    """

    if not CLAUDE_ROOT.is_dir():
        return []
    unaccounted = []
    for directory in sorted(CLAUDE_ROOT.iterdir()):
        if not directory.is_dir():
            continue
        name = directory.name
        # A mangled absolute Windows path always begins <letter>-- ; a POSIX one begins -.
        if not re.match(r"^[A-Za-z]--", name) and not name.startswith("-"):
            unaccounted.append(name)
    return unaccounted


def _git_common_dir(path: Path) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "--path-format=absolute", "--git-common-dir"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def same_project(project_root: Path, candidate: Path) -> bool:
    """Whether a session's directory belongs to the project.

    A path inside the project tree obviously belongs. So does a **linked worktree** of the same
    repository: the work recorded there is the project's history, and excluding it would lose
    exactly the sessions in which the project was changed. Sameness is decided by Git's common
    directory, not by string prefix, because a worktree lives outside the project tree.
    """

    try:
        resolved = candidate.resolve()
        root = project_root.resolve()
    except OSError:
        return False
    if resolved == root or root in resolved.parents:
        return True
    common = _git_common_dir(resolved) if resolved.is_dir() else None
    if common is None:
        return False
    return common == _git_common_dir(root)


def codex_session_cwd(transcript: Path) -> str | None:
    """Return the startup directory a Codex rollout records, or None if it records none."""

    try:
        with transcript.open(encoding="utf-8", errors="replace") as handle:
            for line in handle:
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if record.get("type") == "session_meta":
                    payload = record.get("payload") or {}
                    cwd = payload.get("cwd")
                    return cwd if isinstance(cwd, str) and cwd else None
    except OSError:
        return None
    return None


def pi_agent_directory() -> Path:
    """Return Pi's agent directory, honouring the variable Pi itself honours."""

    configured = os.environ.get(PI_AGENT_DIR_ENV)
    if configured:
        return Path(configured)
    return Path.home() / PI_CONFIG_DIR_NAME / "agent"


def pi_sessions_root() -> Path:
    """Return the Pi session store, resolved the way Pi resolves it.

    Pi takes the first of: ``--session-dir`` on the command line, the session-directory
    variable, ``sessionDir`` in the agent's settings, and finally ``<agent-dir>/sessions``.
    The command-line form is deliberately not honoured here: it applies to one invocation and
    leaves nothing behind for anyone to read afterwards. The other three are durable, so a
    moved store is found instead of silently reported as no history at all.
    """

    configured = os.environ.get(PI_SESSION_DIR_ENV)
    if configured:
        return Path(configured)
    settings = pi_agent_directory() / "settings.json"
    try:
        document = json.loads(settings.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        document = {}
    if isinstance(document, dict):
        directory = document.get("sessionDir")
        if isinstance(directory, str) and directory:
            return Path(directory)
    return pi_agent_directory() / "sessions"


def pi_session_header(transcript: Path) -> dict | None:
    """Return the ``session`` record a Pi transcript opens with, or None if it opens without one.

    Only the first record is read. Pi writes the header first and never elsewhere, so scanning
    further would buy nothing and cost the whole file — and this store holds transcripts in the
    hundreds of megabytes.
    """

    try:
        with transcript.open(encoding="utf-8", errors="replace") as handle:
            first = handle.readline()
    except OSError:
        return None
    try:
        record = json.loads(first)
    except json.JSONDecodeError:
        return None
    if not isinstance(record, dict) or record.get("type") != PI_SESSION_RECORD:
        return None
    return record


def pi_filename_session_id(transcript: Path) -> str | None:
    """Return the identifier Pi encoded in a transcript's name: ``<iso>_<id>.jsonl``."""

    _, separator, identifier = transcript.stem.partition("_")
    return identifier if separator and identifier else None


def pi_transcripts(project_root: Path) -> tuple[list[Path], list[Path]]:
    """Return this project's Pi transcripts and the ones whose identity does not resolve.

    A transcript is unresolved when it carries no ``session`` record, when that record names no
    ``cwd``, or when the identifier in its name disagrees with the identifier inside it. The
    last one is a contradiction rather than a preference: choosing either half would file this
    session's history under an identifier the other half of the store does not use.
    """

    root = pi_sessions_root()
    if not root.is_dir():
        return [], []
    mine: list[Path] = []
    unresolved: list[Path] = []
    for transcript in sorted({*root.glob("*.jsonl"), *root.glob("*/*.jsonl")}):
        header = pi_session_header(transcript)
        cwd = header.get("cwd") if isinstance(header, dict) else None
        named = pi_filename_session_id(transcript)
        recorded = header.get("id") if isinstance(header, dict) else None
        if not isinstance(cwd, str) or not cwd:
            unresolved.append(transcript)
        elif named is not None and isinstance(recorded, str) and named != recorded:
            unresolved.append(transcript)
        elif same_project(project_root, Path(cwd)):
            mine.append(transcript)
    return mine, unresolved


def codex_transcripts(project_root: Path) -> tuple[list[Path], list[Path]]:
    """Return this project's Codex transcripts and the ones with no resolvable project.

    A rollout without a ``session_meta`` cwd is returned separately rather than attributed to
    the project being asked about: guessing would put another project's history in this wiki.
    """

    if not CODEX_ROOT.is_dir():
        return [], []
    mine: list[Path] = []
    unresolved: list[Path] = []
    for transcript in sorted(CODEX_ROOT.rglob("rollout-*.jsonl")):
        cwd = codex_session_cwd(transcript)
        if cwd is None:
            unresolved.append(transcript)
        elif same_project(project_root, Path(cwd)):
            mine.append(transcript)
    return mine, unresolved


def require_known_providers(providers: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    """Return the requested providers, or raise naming the value that is not one.

    A misspelled provider must not read as an empty store. ``"cladue-code"`` finds nothing for
    exactly the same reason a correctly spelled provider with no sessions finds nothing, and
    only the error tells the two apart.
    """

    unknown = [name for name in providers if name not in KNOWN_PROVIDERS]
    if unknown:
        raise DiscoveryError(
            f"unknown session provider(s): {', '.join(unknown)}; "
            f"known providers are {', '.join(KNOWN_PROVIDERS)}"
        )
    return tuple(providers)


def discover(
    project_root: Path, providers: tuple[str, ...] | list[str] = DEFAULT_PROVIDERS
) -> dict[str, object]:
    """Return every transcript for one project, for the named providers only.

    A provider that is not named contributes no key at all. Reporting it as zero would state
    that its store was read and found empty, which is a different fact from not looking.
    """

    names = require_known_providers(providers)
    report: dict[str, object] = {
        "project_root": str(project_root),
        "providers": list(names),
    }
    if "claude-code" in names:
        claude = claude_transcripts(project_root)
        report["claude"] = {
            "directory": str(claude_project_directory(project_root)),
            "transcripts": [str(path) for path in claude],
            "count": len(claude),
            "bytes": sum(path.stat().st_size for path in claude),
            "identity": "store directory name, from the startup cwd",
            "timestamp_field": CLAUDE_TIMESTAMP_FIELD,
        }
        report["unaccounted_claude_directories"] = unaccounted_claude_directories()
    if "codex" in names:
        codex, unresolved = codex_transcripts(project_root)
        report["codex"] = {
            "transcripts": [str(path) for path in codex],
            "count": len(codex),
            "bytes": sum(path.stat().st_size for path in codex),
            "identity": "session_meta.payload.cwd",
            "timestamp_fields": list(CODEX_TIMESTAMP_FIELDS),
        }
        report["unresolved_codex_sessions"] = [str(path) for path in unresolved]
    if "pi" in names:
        pi, unresolved_pi = pi_transcripts(project_root)
        report["pi"] = {
            "directory": str(pi_sessions_root()),
            "transcripts": [str(path) for path in pi],
            "count": len(pi),
            "bytes": sum(path.stat().st_size for path in pi),
            "identity": "session.cwd, read from the transcript",
            "timestamp_field": PI_TIMESTAMP_FIELD,
        }
        report["unresolved_pi_sessions"] = [str(path) for path in unresolved_pi]
    return report


def main(argv: list[str]) -> int:
    if not argv or argv[0] in {"-h", "--help"}:
        print(__doc__)
        return 0
    providers = DEFAULT_PROVIDERS
    for index, argument in enumerate(argv[1:]):
        if argument == "--providers" and index + 2 <= len(argv[1:]):
            providers = tuple(argv[index + 2].split(","))
    report = discover(Path(argv[0]), providers)
    if "--json" in argv[1:]:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    print(f"project   {report['project_root']}")
    print(f"providers {', '.join(report['providers'])}")
    for name, key in (("claude-code", "claude"), ("codex", "codex"), ("pi", "pi")):
        block = report.get(key)
        if block is None:
            continue
        print(f"{name:<12} {block['count']} transcripts, {block['bytes']} bytes")
        if "directory" in block:
            print(f"             {block['directory']}")
    for key, label in (
        ("unresolved_codex_sessions", "unresolved codex sessions"),
        ("unresolved_pi_sessions", "unresolved pi sessions"),
        ("unaccounted_claude_directories", "unaccounted claude dirs"),
    ):
        if key in report:
            value = report[key]
            print(f"{label:<28} {len(value) if isinstance(value, list) else value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
