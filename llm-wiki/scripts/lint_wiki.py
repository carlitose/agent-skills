#!/usr/bin/env python3
"""
lint_wiki.py — Health check for a wiki against the skill's single layout.

Usage:
    python3 lint_wiki.py <wiki-root>

Passes:
  1. Layout            — every directory and file the layout declares exists
  2. Dead wikilinks    — [[Target]] where Target.md does not exist
  3. Orphan pages      — pages with no inbound wikilink
  4. Index coverage    — every page listed in wiki/index.md
  5. Unlinked concepts — terms linked 3+ times with no page of their own
  6. Log shape         — wiki/log.md: newest first, one entry per operation
  7. Audit shape       — every audit file parses as a valid entry
  8. Audit targets     — every open audit's `target` file exists

Every pass reports rather than skips. A pass that cannot fail is worse than no pass, so a
missing directory is an issue in pass 1 and not a silent success in the pass that would have
read it.

Exit codes:
  0 — no issues found
  1 — issues found (printed to stdout)

On Windows `python3` may resolve to a Microsoft Store alias that does not run Python. Use
`python` there.
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from console import utf8_stdout

WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:[|#][^\]]*)?\]\]")
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
LOG_DATE_RE = re.compile(r"^## (\d{4}-\d{2}-\d{2})\s*$")
LOG_ENTRY_RE = re.compile(r"^- (\d{2}):(\d{2}) (\S+)\s+\S")

# The layout. One layout, not a profile: see
# docs/specs/llm-wiki-app-independence-decision.md.
LAYOUT_DIRECTORIES = (
    "audit",
    "audit/resolved",
    "raw/sources",
    "raw/refs",
    "raw/assets",
    "wiki/concepts",
    "wiki/entities",
    "wiki/sources",
    "wiki/queries",
    "wiki/comparisons",
    "wiki/synthesis",
    "wiki/timeline",
    "wiki/timeline/tickets",
)
LAYOUT_FILES = ("purpose.md", "schema.md", "wiki/index.md", "wiki/log.md")

# Files under wiki/ that are machinery rather than pages: neither indexed nor expected to
# carry inbound links.
NON_PAGE_RELATIVE_PATHS = {"index.md", "log.md"}

LOG_OPERATIONS = {
    "compile",
    "ingest",
    "query",
    "lint",
    "audit",
    "promote",
    "split",
    "scaffold",
    "ingest-docs",
    "timeline",
    "sessions",
}

AUDIT_REQUIRED_FIELDS = {
    "id",
    "target",
    "target_lines",
    "anchor_before",
    "anchor_text",
    "anchor_after",
    "severity",
    "author",
    "source",
    "created",
    "status",
}
VALID_SEVERITIES = {"info", "suggest", "warn", "error"}
VALID_STATUSES = {"open", "resolved"}
VALID_SOURCES = {"obsidian-plugin", "web-viewer", "manual"}

# audit/README.md documents the directory; it is not a correction.
AUDIT_NON_ENTRY_NAMES = {"README.md"}


@dataclass
class PassResult:
    """One lint pass. An empty `issues` list means the pass is green."""

    name: str
    issues: list[str] = field(default_factory=list)
    clean_message: str = ""

    @property
    def ok(self) -> bool:
        return not self.issues


def load_pages(wiki_dir: Path) -> dict[str, Path]:
    pages: dict[str, Path] = {}
    for page in wiki_dir.rglob("*.md"):
        pages[page.stem] = page
        relative = page.relative_to(wiki_dir)
        pages[str(relative.with_suffix("")).replace("\\", "/")] = page
    return pages


def extract_wikilinks(text: str) -> list[str]:
    return WIKILINK_RE.findall(text)


def parse_frontmatter(text: str) -> dict | None:
    """Flat scalars and one-level lists, which is all an audit entry uses.

    Deliberately not a YAML parser: the skill carries no third-party dependency.
    """

    match = FRONTMATTER_RE.match(text)
    if not match:
        return None
    result: dict = {}
    for line in match.group(1).split("\n"):
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, _, rest = line.partition(":")
        key = key.strip()
        value = rest.strip()
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            items = [part.strip() for part in inner.split(",")] if inner else []
            parsed: list = []
            for item in items:
                if item.lstrip("-").isdigit():
                    parsed.append(int(item))
                else:
                    parsed.append(item.strip('"').strip("'"))
            result[key] = parsed
        elif value.startswith('"') and value.endswith('"'):
            result[key] = value[1:-1].replace("\\n", "\n").replace('\\"', '"')
        elif value.startswith("'") and value.endswith("'"):
            result[key] = value[1:-1]
        else:
            result[key] = value
    return result


def posix(path: Path, root: Path) -> str:
    """Forward slashes in every message, so Windows output reads like the layout."""

    return path.relative_to(root).as_posix()


def wiki_pages(wiki_path: Path) -> list[Path]:
    """The pages, excluding the machinery files."""

    return [
        page
        for page in sorted(wiki_path.rglob("*.md"))
        if str(page.relative_to(wiki_path)).replace("\\", "/") not in NON_PAGE_RELATIVE_PATHS
    ]


# -- Pass 1 --------------------------------------------------------------------


def check_layout(root: Path) -> PassResult:
    result = PassResult("layout", clean_message="Layout complete")
    for relative in LAYOUT_DIRECTORIES:
        if not (root / relative).is_dir():
            result.issues.append(f"   {relative}/ — missing directory")
    for relative in LAYOUT_FILES:
        if not (root / relative).is_file():
            result.issues.append(f"   {relative} — missing file")
    return result


# -- Passes 2, 3 and 5 ---------------------------------------------------------


def check_links(root: Path, wiki_path: Path) -> tuple[PassResult, PassResult, PassResult]:
    """Dead links, orphans and frequently-linked missing pages share one traversal."""

    pages = load_pages(wiki_path)
    inbound: dict[str, list[str]] = defaultdict(list)
    link_counts: dict[str, int] = defaultdict(int)

    dead = PassResult("dead-wikilinks", clean_message="No dead wikilinks")
    for md_file in sorted(wiki_path.rglob("*.md")):
        relative = str(md_file.relative_to(wiki_path)).replace("\\", "/")
        catalogue = relative in NON_PAGE_RELATIVE_PATHS
        for raw_link in extract_wikilinks(md_file.read_text(encoding="utf-8")):
            link = raw_link.strip()
            link_counts[link] += 1
            target = pages.get(link) or pages.get(Path(link).stem)
            if target is None:
                dead.issues.append(f"   {posix(md_file, root)} -> [[{link}]]")
            elif not catalogue:
                # index.md and log.md are catalogues. A page listed there is covered by
                # the index pass; being listed is not the same as being cited, so their
                # links do not rescue a page from the orphan pass.
                inbound[target.stem].append(md_file.stem)

    orphans = PassResult("orphan-pages", clean_message="No orphan pages")
    for page in wiki_pages(wiki_path):
        if page.stem not in inbound:
            orphans.issues.append(f"   {posix(page, root)}")

    unlinked = PassResult(
        "unlinked-concepts", clean_message="No frequently-linked missing pages"
    )
    for link, count in sorted(link_counts.items(), key=lambda item: -item[1]):
        if count >= 3 and link not in pages and Path(link).stem not in pages:
            unlinked.issues.append(f"   [[{link}]] — linked {count}x, no page")

    return dead, orphans, unlinked


# -- Pass 4 --------------------------------------------------------------------


def check_index(root: Path, wiki_path: Path) -> PassResult:
    result = PassResult("index-coverage", clean_message="Every page is in wiki/index.md")
    index_path = wiki_path / "index.md"
    if not index_path.is_file():
        result.issues.append("   wiki/index.md — missing, so no page can be listed")
        return result
    index_text = index_path.read_text(encoding="utf-8")
    for page in wiki_pages(wiki_path):
        relative = str(page.relative_to(wiki_path).with_suffix("")).replace("\\", "/")
        if f"[[{page.stem}]]" in index_text or relative in index_text:
            continue
        result.issues.append(f"   {posix(page, root)} — not listed")
    return result


# -- Pass 6 --------------------------------------------------------------------


def check_log(root: Path) -> PassResult:
    """wiki/log.md is one file, newest first. The layout note in scaffold.py says why."""

    result = PassResult("log-shape", clean_message="wiki/log.md shape OK")
    log_path = root / "wiki" / "log.md"
    if not log_path.is_file():
        result.issues.append("   wiki/log.md — missing")
        return result

    lines = log_path.read_text(encoding="utf-8").splitlines()
    heading = next((line for line in lines if line.strip()), "")
    if not heading.startswith("# "):
        result.issues.append("   wiki/log.md — first line is not an H1 title")

    dates: list[date] = []
    for number, line in enumerate(lines, start=1):
        if line.startswith("## "):
            match = LOG_DATE_RE.match(line)
            if not match:
                result.issues.append(
                    f"   wiki/log.md:{number} — H2 is not a '## YYYY-MM-DD' date"
                )
                continue
            try:
                dates.append(date.fromisoformat(match.group(1)))
            except ValueError:
                result.issues.append(
                    f"   wiki/log.md:{number} — '{match.group(1)}' is not a real date"
                )
        elif line.startswith("- "):
            entry = LOG_ENTRY_RE.match(line)
            if not entry:
                result.issues.append(
                    f"   wiki/log.md:{number} — entry is not '- HH:MM <op> <description>'"
                )
                continue
            hour, minute, operation = entry.groups()
            if int(hour) > 23 or int(minute) > 59:
                result.issues.append(
                    f"   wiki/log.md:{number} — '{hour}:{minute}' is not a real time"
                )
            if operation not in LOG_OPERATIONS:
                result.issues.append(
                    f"   wiki/log.md:{number} — unknown operation '{operation}'"
                )

    if not dates:
        result.issues.append("   wiki/log.md — no dated entry at all")
    for earlier, later in zip(dates, dates[1:]):
        if later >= earlier:
            result.issues.append(
                f"   wiki/log.md — {later} follows {earlier}; the log is newest first"
            )
    return result


# -- Passes 7 and 8 ------------------------------------------------------------


def check_audit(root: Path) -> tuple[PassResult, PassResult]:
    """The human-to-agent channel. Kept unconditionally; LW-01 settled that."""

    shape = PassResult("audit-shape", clean_message="audit/ shape OK")
    targets = PassResult("audit-targets", clean_message="All open-audit targets exist")

    audit_path = root / "audit"
    if not audit_path.is_dir():
        shape.issues.append("   audit/ — missing, so no correction can be filed")
        return shape, targets

    open_targets: list[tuple[str, str]] = []
    for entry in sorted(audit_path.rglob("*.md")):
        if entry.name in AUDIT_NON_ENTRY_NAMES:
            continue
        relative = posix(entry, root)
        front_matter = parse_frontmatter(entry.read_text(encoding="utf-8"))
        if front_matter is None:
            shape.issues.append(f"   {relative} — missing YAML frontmatter")
            continue
        missing = AUDIT_REQUIRED_FIELDS - set(front_matter)
        if missing:
            shape.issues.append(
                f"   {relative} — missing fields: {', '.join(sorted(missing))}"
            )
            continue
        if front_matter["severity"] not in VALID_SEVERITIES:
            shape.issues.append(
                f"   {relative} — invalid severity '{front_matter['severity']}' "
                f"(expected {sorted(VALID_SEVERITIES)})"
            )
        if front_matter["source"] not in VALID_SOURCES:
            shape.issues.append(f"   {relative} — invalid source '{front_matter['source']}'")
        expected_status = "resolved" if "resolved" in entry.parts else "open"
        if front_matter["status"] not in VALID_STATUSES:
            shape.issues.append(f"   {relative} — invalid status '{front_matter['status']}'")
        elif front_matter["status"] != expected_status:
            shape.issues.append(
                f"   {relative} — status '{front_matter['status']}' does not match its "
                f"directory (expected '{expected_status}')"
            )
        if front_matter["status"] == "open":
            open_targets.append((front_matter["id"], front_matter["target"]))

    for audit_id, target in open_targets:
        if not (root / target).exists() and not (root / "wiki" / target).exists():
            targets.issues.append(f"   {audit_id} -> {target}")
    return shape, targets


# -- Driver --------------------------------------------------------------------


def run_passes(root: Path) -> list[PassResult]:
    wiki_path = root / "wiki"
    results = [check_layout(root)]
    if wiki_path.is_dir():
        dead, orphans, unlinked = check_links(root, wiki_path)
        results += [dead, orphans, check_index(root, wiki_path), unlinked]
    results.append(check_log(root))
    shape, targets = check_audit(root)
    results += [shape, targets]
    return results


def lint(root: str | Path) -> int:
    root_path = Path(root)
    if not root_path.is_dir():
        print(f"ERROR: no wiki at {root_path}", file=sys.stderr)
        return 1

    results = run_passes(root_path)
    total = 0
    for result in results:
        if result.ok:
            print(f"OK   {result.name} — {result.clean_message}")
            continue
        total += len(result.issues)
        print(f"\nFAIL {result.name} ({len(result.issues)}):")
        for issue in result.issues:
            print(issue)

    print(f"\n{'-' * 40}")
    if total == 0:
        print("Wiki is healthy — no issues found")
    else:
        print(f"{total} issue(s) found — fix before the next ingest")
    return 0 if total == 0 else 1


if __name__ == "__main__":
    utf8_stdout()
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    sys.exit(lint(sys.argv[1]))
