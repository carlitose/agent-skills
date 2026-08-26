#!/usr/bin/env python3
"""Resolve when an artefact happened, and always say how we know.

Every date this module returns carries the rung of the ladder that produced it. A date
without provenance is not representable, because the failure this module exists to prevent is
a filesystem timestamp being read as a recorded fact.

The ladder, strongest first:

``git-rename``
    A rename-detected move into a disposition directory. The strongest witness to a
    disposition change, and the only one that is unambiguous.
``git-commit``
    The first commit touching the file, for creation; the last, for modification.
``frontmatter``
    An explicit date already written in the artefact.
``session-observed``
    The earliest or latest dated mention of the artefact's identity in a project transcript.
    Declared here and populated by ``LW-08``: it is the only witness left when ``docs/`` is
    untracked, because a transcript records a timestamp whatever Git knows.
``mtime``
    A filesystem timestamp. Always flagged low confidence, and never used for a disposition
    change: a disposition change has no filesystem witness at all, so substituting one would
    invent a fact.
``unknown``
    No rung produced an answer. This is a valid, expected result.

Usage:
    python3 date_provenance.py <project-root> <relative-path> [--json]
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

PROVENANCE_RUNGS = (
    "git-rename",
    "git-commit",
    "frontmatter",
    "session-observed",
    "mtime",
    "unknown",
)
LOW_CONFIDENCE_RUNGS = frozenset({"mtime"})
DISPOSITION_DIRECTORIES = ("done", "canceled", "hold")
DISPOSITION_BY_DIRECTORY = {
    "done": "completed",
    "canceled": "canceled",
    "hold": "on-hold",
}
_FRONTMATTER_DATE = re.compile(
    r"(?m)^(?P<key>created|updated|completed|date)\s*:\s*[\"']?(?P<value>\d{4}-\d{2}-\d{2})"
)
_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass(frozen=True)
class ResolvedDate:
    """A date and the rung that produced it. Provenance is never optional."""

    value: str | None
    provenance: str
    detail: str | None = None

    def __post_init__(self) -> None:
        if self.provenance not in PROVENANCE_RUNGS:
            raise ValueError(f"unknown provenance rung: {self.provenance!r}")
        if self.provenance == "unknown":
            if self.value is not None:
                raise ValueError("an unknown date cannot carry a value")
        else:
            if self.value is None:
                raise ValueError(f"{self.provenance} must carry a value")
            if not _ISO_DATE.match(self.value):
                raise ValueError(f"date must be ISO yyyy-mm-dd, got {self.value!r}")

    @property
    def low_confidence(self) -> bool:
        return self.provenance in LOW_CONFIDENCE_RUNGS

    @property
    def known(self) -> bool:
        return self.provenance != "unknown"


UNKNOWN = ResolvedDate(None, "unknown")


def _git(project_root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(project_root), *arguments],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def _is_repository(project_root: Path) -> bool:
    result = _git(project_root, "rev-parse", "--is-inside-work-tree")
    return result.returncode == 0 and result.stdout.strip() == "true"


def _is_tracked(project_root: Path, relative_path: str) -> bool:
    if not _is_repository(project_root):
        return False
    return (
        _git(
            project_root, "ls-files", "--error-unmatch", "--", relative_path
        ).returncode
        == 0
    )


def disposition_of(relative_path: str) -> str:
    """Return the administrative disposition implied by an artefact's location."""

    parts = Path(relative_path).parts
    if len(parts) >= 2 and parts[-2] in DISPOSITION_BY_DIRECTORY:
        return DISPOSITION_BY_DIRECTORY[parts[-2]]
    return "open"


def resolve_created(
    project_root: Path,
    relative_path: str,
    *,
    session_mentions: tuple[str, ...] = (),
) -> ResolvedDate:
    """When the artefact first appeared."""

    if _is_tracked(project_root, relative_path):
        result = _git(
            project_root,
            "log",
            "--follow",
            "--format=%h %ad",
            "--date=short",
            "--",
            relative_path,
        )
        lines = [line for line in result.stdout.splitlines() if line.strip()]
        if result.returncode == 0 and lines:
            commit, date = lines[-1].split(maxsplit=1)
            return ResolvedDate(date.strip(), "git-commit", f"first commit {commit}")

    matter = _frontmatter_date(project_root / relative_path, ("created", "date"))
    if matter is not None:
        return ResolvedDate(matter[1], "frontmatter", f"front matter {matter[0]}")

    if session_mentions:
        return ResolvedDate(
            min(session_mentions), "session-observed", "earliest transcript mention"
        )

    stamp = _mtime(project_root / relative_path)
    if stamp is not None:
        return ResolvedDate(stamp, "mtime", "filesystem timestamp, low confidence")
    return UNKNOWN


def resolve_disposition_change(
    project_root: Path,
    relative_path: str,
    *,
    session_mentions: tuple[str, ...] = (),
    identity_key: str | None = None,
) -> ResolvedDate:
    """When the artefact reached its current disposition.

    Returns ``unknown`` for an artefact still in the folder root: there is no change to date.

    **mtime is deliberately absent from this ladder.** A disposition change is a move, and a
    move leaves no filesystem trace distinguishable from an edit, so an mtime here would be an
    invented fact rather than a weak one.
    """

    if disposition_of(relative_path) == "open":
        return UNKNOWN

    if _is_tracked(project_root, relative_path):
        renamed = _rename_into_disposition(project_root, relative_path)
        if renamed is not None:
            commit, date, similarity = renamed
            return ResolvedDate(
                date, "git-rename", f"{commit} detected as {similarity}"
            )
        paired = _delete_add_pair(project_root, relative_path, identity_key)
        if paired is not None:
            commit, date = paired
            return ResolvedDate(
                date,
                "git-rename",
                f"{commit} recovered from a delete-plus-add pair",
            )

    matter = _frontmatter_date(project_root / relative_path, ("completed",))
    if matter is not None:
        return ResolvedDate(matter[1], "frontmatter", f"front matter {matter[0]}")

    if session_mentions:
        return ResolvedDate(
            max(session_mentions), "session-observed", "latest transcript mention"
        )

    return UNKNOWN


def _rename_into_disposition(
    project_root: Path, relative_path: str
) -> tuple[str, str, str] | None:
    result = _git(
        project_root,
        "log",
        "--follow",
        "--diff-filter=R",
        "--find-renames",
        "--format=%x00%h %ad",
        "--date=short",
        "--name-status",
        "--",
        relative_path,
    )
    if result.returncode != 0:
        return None
    target = Path(relative_path).as_posix()
    for block in result.stdout.split("\x00"):
        block = block.strip()
        if not block:
            continue
        header, *rest = block.splitlines()
        commit, _, date = header.partition(" ")
        for line in rest:
            fields = line.split("\t")
            if len(fields) != 3 or not fields[0].startswith("R"):
                continue
            similarity, source, destination = fields
            if destination.strip() == target:
                if Path(source).parent != Path(destination).parent:
                    return commit.strip(), date.strip(), similarity.strip()
    return None


def _delete_add_pair(
    project_root: Path, relative_path: str, identity_key: str | None
) -> tuple[str, str] | None:
    """Recover a move that Git recorded as a delete plus an add.

    A commit that moves a ticket into ``done/`` *and* edits it can fall below the rename
    similarity threshold. The pair is reunited on the artefact's own filename inside the same
    ticket folder, which is stable across the move; ``identity_key`` is accepted so a caller
    can record what it matched on.
    """

    destination = Path(relative_path)
    folder = destination.parent.parent
    origin = (folder / destination.name).as_posix()
    result = _git(
        project_root,
        "log",
        "--diff-filter=A",
        "--format=%h %ad",
        "--date=short",
        "--",
        destination.as_posix(),
    )
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        commit, _, date = line.partition(" ")
        commit = commit.strip()
        touched = _git(
            project_root,
            "show",
            "--diff-filter=D",
            "--format=",
            "--name-only",
            commit,
        )
        if origin in touched.stdout.split():
            return commit, date.strip()
    return None


def _frontmatter_date(
    path: Path, keys: tuple[str, ...]
) -> tuple[str, str] | None:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    block = text[:end] if end != -1 else text
    for match in _FRONTMATTER_DATE.finditer(block):
        if match.group("key") in keys:
            return match.group("key"), match.group("value")
    return None


def _mtime(path: Path) -> str | None:
    try:
        stamp = path.stat().st_mtime
    except OSError:
        return None
    import datetime

    return datetime.datetime.fromtimestamp(stamp).date().isoformat()


def resolve_artefact_dates(
    project_root: Path,
    relative_path: str,
    *,
    session_mentions: tuple[str, ...] = (),
    identity_key: str | None = None,
) -> dict[str, object]:
    """Return both dates as flat scalars, each beside its own provenance.

    Flat rather than nested on purpose: the LLM Wiki application reads a nested front-matter
    value back as a JSON string, so provenance travels as sibling keys.
    """

    created = resolve_created(
        project_root, relative_path, session_mentions=session_mentions
    )
    changed = resolve_disposition_change(
        project_root,
        relative_path,
        session_mentions=session_mentions,
        identity_key=identity_key,
    )
    return {
        "disposition": disposition_of(relative_path),
        "created": created.value,
        "created_provenance": created.provenance,
        "created_detail": created.detail,
        "created_low_confidence": created.low_confidence,
        "disposition_changed": changed.value,
        "disposition_changed_provenance": changed.provenance,
        "disposition_changed_detail": changed.detail,
        "disposition_changed_low_confidence": changed.low_confidence,
    }


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[0] in {"-h", "--help"}:
        print(__doc__)
        return 0
    report = resolve_artefact_dates(Path(argv[0]), argv[1])
    if "--json" in argv[2:]:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    for key, value in report.items():
        print(f"{key:38} {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
