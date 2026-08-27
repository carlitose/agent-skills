#!/usr/bin/env python3
"""Find the Claude Code and Codex transcripts that belong to one project.

The two providers identify a project in completely different ways, and getting either wrong
yields zero sessions — which reads as "this project has no history" rather than as an error.

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

Usage:
    python3 session_discovery.py <project-root> [--json]
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

CLAUDE_ROOT = Path.home() / ".claude" / "projects"
CODEX_ROOT = Path.home() / ".codex" / "sessions"
NON_ALPHANUMERIC = re.compile(r"[^A-Za-z0-9]")
CLAUDE_TIMESTAMP_FIELD = "timestamp"
CODEX_TIMESTAMP_FIELDS = ("timestamp", "payload.timestamp")


class DiscoveryError(RuntimeError):
    """A provider store is absent or a project directory cannot be accounted for."""


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


def discover(project_root: Path) -> dict[str, object]:
    """Return every transcript for one project, plus what could not be accounted for."""

    claude = claude_transcripts(project_root)
    codex, unresolved = codex_transcripts(project_root)
    return {
        "project_root": str(project_root),
        "claude": {
            "directory": str(claude_project_directory(project_root)),
            "transcripts": [str(path) for path in claude],
            "count": len(claude),
            "bytes": sum(path.stat().st_size for path in claude),
            "identity": "store directory name, from the startup cwd",
            "timestamp_field": CLAUDE_TIMESTAMP_FIELD,
        },
        "codex": {
            "transcripts": [str(path) for path in codex],
            "count": len(codex),
            "bytes": sum(path.stat().st_size for path in codex),
            "identity": "session_meta.payload.cwd",
            "timestamp_fields": list(CODEX_TIMESTAMP_FIELDS),
        },
        "unresolved_codex_sessions": [str(path) for path in unresolved],
        "unaccounted_claude_directories": unaccounted_claude_directories(),
    }


def main(argv: list[str]) -> int:
    if not argv or argv[0] in {"-h", "--help"}:
        print(__doc__)
        return 0
    report = discover(Path(argv[0]))
    if "--json" in argv[1:]:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    print(f"project   {report['project_root']}")
    claude, codex = report["claude"], report["codex"]
    print(f"claude    {claude['count']} transcripts, {claude['bytes']} bytes")
    print(f"          {claude['directory']}")
    print(f"codex     {codex['count']} transcripts, {codex['bytes']} bytes")
    print(f"unresolved codex sessions   {len(report['unresolved_codex_sessions'])}")
    print(f"unaccounted claude dirs     {report['unaccounted_claude_directories']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
