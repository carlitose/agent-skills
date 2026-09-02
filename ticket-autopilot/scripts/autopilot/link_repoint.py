"""Repoint documentation links when the lifecycle moves a ticket.

A ticket's location is lifecycle state: the runner moves the file between its open location
and ``done/``, ``canceled/`` or ``hold/``, and every document that linked the old path goes
stale in the same instant. The ticket itself cannot be corrected — its bytes are digest-frozen
across the move — but the documents that link *to* it are ordinary writable Markdown, and the
delivery tree is recomputed after the move mutates it, so a staged repoint rides the same
commit as the move.

This module owns the rewrite rule; `finalize_done` and the hold/cancel/reopen path call it,
and `repair_disposition_links.py` reuses its primitives for the after-the-fact repair. One
implementation, several callers: a second copy of link semantics is how the audit and the
docs-only gate came to disagree in the first place.

The rules, shared with the repair script and each load-bearing:

* only writable documents are rewritten — nothing under ``docs/tickets/`` is ever touched;
* fenced code is skipped, because the Artifact Graph decision teaches the format with example
  links inside fences;
* fragments survive: ``path.md#section`` is repointed on the path and keeps the fragment;
* line endings survive: files are rewritten with their own bytes' endings.
"""

from __future__ import annotations

import re
from pathlib import Path, PurePosixPath

LINK = re.compile(r"(\[[^\]]*\]\()([^)]+)(\))")
FENCE = re.compile(r"^\s*(```|~~~)")

#: Documents whose bytes the lifecycle contract freezes. Never rewritten.
FROZEN_PREFIX = "docs/tickets/"

#: The tree the rewrite may touch.
DOCUMENT_ROOT = "docs"


def split_fragment(target: str) -> tuple[str, str]:
    if "#" in target:
        path, fragment = target.split("#", 1)
        return path, "#" + fragment
    return target, ""


def is_candidate_link(target: str) -> bool:
    stripped = target.strip()
    if not stripped or stripped.startswith("#"):
        return False
    if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", stripped):
        return False  # http:, mailto:, and friends
    path, _ = split_fragment(stripped)
    return path.endswith(".md")


def normalize(source_directory: PurePosixPath, target_path: str) -> str | None:
    """Repository-relative POSIX path for a link, or None when it climbs out."""

    combined = (
        PurePosixPath(target_path)
        if target_path.startswith("/")
        else source_directory / target_path
    )
    parts: list[str] = []
    for part in combined.parts:
        if part in {"", ".", "/"}:
            continue
        if part == "..":
            if not parts:
                return None
            parts.pop()
        else:
            parts.append(part)
    return PurePosixPath(*parts).as_posix() if parts else None


def relative_link(source_directory: PurePosixPath, repo_target: str) -> str:
    """The link text that reaches ``repo_target`` from ``source_directory``."""

    source_parts = list(source_directory.parts)
    target_parts = list(PurePosixPath(repo_target).parts)
    shared = 0
    for ours, theirs in zip(source_parts, target_parts):
        if ours != theirs:
            break
        shared += 1
    climbs = [".."] * (len(source_parts) - shared)
    return "/".join(climbs + target_parts[shared:])


def _repoint_text(
    relative: str, text: str, old_repo: str, new_repo: str
) -> tuple[str, bool]:
    source_directory = PurePosixPath(relative).parent
    fenced = False
    changed = False
    lines = text.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if FENCE.match(line):
            fenced = not fenced
            continue
        if fenced or "](" not in line:
            continue

        def substitute(match: re.Match[str]) -> str:
            nonlocal changed
            target = match.group(2).strip()
            if not is_candidate_link(target):
                return match.group(0)
            path_part, fragment = split_fragment(target)
            if normalize(source_directory, path_part) != old_repo:
                return match.group(0)
            changed = True
            return (
                f"{match.group(1)}"
                f"{relative_link(source_directory, new_repo)}{fragment}"
                f"{match.group(3)}"
            )

        lines[index] = LINK.sub(substitute, line)
    return "".join(lines), changed


def plan_repoints(
    worktree: Path, old_repo: str, new_repo: str
) -> dict[str, bytes]:
    """Return the complete sorted link-repoint plan without mutating the worktree."""

    documents = worktree / DOCUMENT_ROOT
    if not documents.is_dir():
        return {}
    planned: dict[str, bytes] = {}
    for path in sorted(documents.rglob("*.md")):
        relative = path.relative_to(worktree).as_posix()
        if relative.startswith(FROZEN_PREFIX):
            continue
        raw = path.read_bytes()
        text = raw.decode("utf-8", errors="replace")
        if "](" not in text:
            continue
        rewritten, changed = _repoint_text(relative, text, old_repo, new_repo)
        if changed:
            planned[relative] = rewritten.encode("utf-8")
    return planned


def repoint_moved_file(worktree: Path, old_repo: str, new_repo: str) -> list[str]:
    """Rewrite every writable docs link that names ``old_repo`` to name ``new_repo``.

    Returns the repository-relative paths of the files changed, sorted, so the caller can
    stage them into the same tree as the move itself. A replay is a no-op: once repointed,
    no link resolves to the old path any more.
    """

    planned = plan_repoints(worktree, old_repo, new_repo)
    for relative, content in planned.items():
        (worktree / relative).write_bytes(content)
    return list(planned)
