#!/usr/bin/env python3
"""Repair disposition drift in the repository's documentation, once and repeatably.

A ticket's location is lifecycle state: the runner moves the file into ``done/``,
``canceled/`` or ``hold/`` when its disposition changes, and every document that linked the
old path goes stale. This script repoints those links. It exists because the stock of drift
accumulated before the movers learned to repoint at move time, and it is kept — with
``--dry-run`` — because the stock can accumulate again until that lands.

Usage:
    python3 repair_disposition_links.py <repository-root> [--dry-run] [--json]

Rules, each one load-bearing:

* **Only writable documents are rewritten.** Nothing under ``docs/tickets/`` is ever touched:
  a ticket's bytes are digest-frozen across its lifecycle
  (``transition_ticket_source`` verifies the digest on both sides of every move), so links
  inside tickets stay stale forever and are resolved by ``artifact_audit``'s reader
  tolerance, which exists for exactly them.
* **Fenced code is skipped.** ``docs/specs/artifact-graph-decision.md`` teaches the Artifact
  Graph format with example links inside code fences; a scanner that reads them as links
  miscounts them as dead, and a repair that rewrites them corrupts the lesson.
* **Exactly one candidate, or no rewrite.** A dead link whose target exists under more than
  one disposition candidate is reported as ambiguous; a dead link whose target exists nowhere
  is reported as dead. Neither is guessed at.
* **Anchors survive.** ``path.md#section`` is repointed on the path and keeps the fragment.
* **Line endings survive.** Files are read and written with their bytes' own endings.

On Windows ``python3`` may resolve to a Microsoft Store alias that does not run Python. Use
``python`` there.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parent))

from autopilot.ticket_lifecycle import DISPOSITION_DIRECTORIES  # noqa: E402

LINK = re.compile(r"(\[[^\]]*\]\()([^)]+)(\))")
FENCE = re.compile(r"^\s*(```|~~~)")

#: Documents whose bytes the lifecycle contract freezes. Never rewritten.
FROZEN_PREFIX = "docs/tickets/"


@dataclass
class Report:
    """What one run saw and did. Counts first, receipts behind them."""

    scanned_files: int = 0
    links_seen: int = 0
    dead: int = 0
    repointed: list[dict[str, str]] = field(default_factory=list)
    ambiguous: list[dict[str, str]] = field(default_factory=list)
    unresolved: list[dict[str, str]] = field(default_factory=list)
    frozen_skipped: int = 0
    changed_files: list[str] = field(default_factory=list)

    def to_document(self) -> dict[str, object]:
        return {
            "scanned_files": self.scanned_files,
            "links_seen": self.links_seen,
            "dead": self.dead,
            "repointed": self.repointed,
            "ambiguous": self.ambiguous,
            "unresolved": self.unresolved,
            "frozen_sources_skipped": self.frozen_skipped,
            "changed_files": sorted(self.changed_files),
        }


def _split_fragment(target: str) -> tuple[str, str]:
    if "#" in target:
        path, fragment = target.split("#", 1)
        return path, "#" + fragment
    return target, ""


def _is_candidate_link(target: str) -> bool:
    stripped = target.strip()
    if not stripped or stripped.startswith("#"):
        return False
    if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", stripped):
        return False  # http:, mailto:, and friends
    path, _ = _split_fragment(stripped)
    return path.endswith(".md")


def _normalize(source_directory: PurePosixPath, target_path: str) -> str | None:
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


def _relative_link(source_directory: PurePosixPath, repo_target: str) -> str:
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


def _disposition_candidates(source_relative: str, repo_target: str) -> list[str]:
    """Where the target may have gone: into a disposition directory, or out of one."""

    target = PurePosixPath(repo_target)
    found: list[str] = []
    for directory in DISPOSITION_DIRECTORIES:
        found.append((target.parent / directory / target.name).as_posix())
    if target.parent.name in DISPOSITION_DIRECTORIES:
        found.append((target.parent.parent / target.name).as_posix())
    ordered: list[str] = []
    for candidate in found:
        if candidate != repo_target and candidate not in ordered:
            ordered.append(candidate)
    return ordered


def repair_file(root: Path, relative: str, report: Report, *, dry_run: bool) -> None:
    source = root / relative
    raw = source.read_bytes()
    text = raw.decode("utf-8", errors="replace")
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
            if not _is_candidate_link(target):
                return match.group(0)
            path_part, fragment = _split_fragment(target)
            report.links_seen += 1
            literal = _normalize(source_directory, path_part)
            if literal is None or (root / literal).is_file():
                return match.group(0)
            report.dead += 1
            existing = [
                candidate
                for candidate in _disposition_candidates(relative, literal)
                if (root / candidate).is_file()
            ]
            record = {"source": relative, "link": target, "target": literal}
            if not existing:
                report.unresolved.append(record)
                return match.group(0)
            if len(existing) > 1:
                report.ambiguous.append({**record, "candidates": ", ".join(existing)})
                return match.group(0)
            new_target = _relative_link(source_directory, existing[0]) + fragment
            report.repointed.append({**record, "repointed_to": new_target})
            changed = True
            return f"{match.group(1)}{new_target}{match.group(3)}"

        lines[index] = LINK.sub(substitute, line)

    if changed:
        report.changed_files.append(relative)
        if not dry_run:
            source.write_bytes("".join(lines).encode("utf-8"))


def repair(root: Path, *, dry_run: bool = False) -> Report:
    report = Report()
    for path in sorted((root / "docs").rglob("*.md")):
        relative = path.relative_to(root).as_posix()
        if relative.startswith(FROZEN_PREFIX):
            report.frozen_skipped += 1
            continue
        report.scanned_files += 1
        repair_file(root, relative, report, dry_run=dry_run)
    return report


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", help="repository root containing docs/")
    parser.add_argument("--dry-run", action="store_true", help="report without writing")
    parser.add_argument("--json", action="store_true", help="emit the report as JSON")
    arguments = parser.parse_args(argv)

    root = Path(arguments.root).resolve()
    if not (root / "docs").is_dir():
        print(f"ERROR: no docs/ under {root}", file=sys.stderr)
        return 2
    report = repair(root, dry_run=arguments.dry_run)

    if arguments.json:
        print(json.dumps(report.to_document(), indent=1))
    else:
        mode = "dry-run" if arguments.dry_run else "applied"
        print(f"{mode}: {report.scanned_files} writable file(s) scanned, "
              f"{report.frozen_skipped} frozen source(s) skipped")
        print(f"links seen {report.links_seen}, dead {report.dead}, "
              f"repointed {len(report.repointed)}, ambiguous {len(report.ambiguous)}, "
              f"still dead {len(report.unresolved)}")
        for item in report.unresolved:
            print(f"  DEAD      {item['source']} -> {item['link']}")
        for item in report.ambiguous:
            print(f"  AMBIGUOUS {item['source']} -> {item['link']} ({item['candidates']})")
        if report.changed_files:
            print("changed files:")
            for name in sorted(report.changed_files):
                print(f"  {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
