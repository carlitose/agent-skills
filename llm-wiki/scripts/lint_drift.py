#!/usr/bin/env python3
"""
lint_drift.py — The passes that look at a page and the artefact it came from.

`lint_wiki.py`'s structural passes read the wiki alone. Not one of them looks at the
relationship between a wiki page and the repository artefact it was compiled from, and that
relationship is what rots: a source moves, a spec is edited, two pages are minted for one
ticket, a transcript keeps growing after its digest was written.

Seven passes here:

  dangling-source        the page's `source_path` no longer exists, or no longer matches the
                         binding's globs
  stale-page             the artefact's content digest differs from the page's recorded one
  un-ingested-artefact   a file the globs match has no page yet
  duplicate-identity     two pages carry one `identity_key`
  timeline-coverage      a ticket with no lifecycle record, or a dated page with no event
  provenance-validity    a date whose rung is absent, unrecognised, or contradicts its value
  stale-session-pointer  a transcript grew, moved, or vanished since its pointer was written

Two rules govern all of them.

**No pass may assume Git.** A project's `docs/` may be untracked and the host may not be a
repository at all; both are supported. A missing history is not drift. `provenance-validity`
therefore checks that a date's rung is *coherent* — never that the rung is a good one. An
`mtime` date is a valid date, and flagging it would make this useless on exactly the
configuration the ladder exists to serve.

**Severity is not decoration.** `un-ingested-artefact` fires on everything added to `docs/`
since the last ingest, which is the normal steady state rather than a defect, so it is
informational. `duplicate-identity` and `stale-page` are corruptions, so they are errors.
Reporting both at one volume teaches the reader to skip the output.

Usage: this module is called by `lint_wiki.py`. Run that.
"""

from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from date_provenance import PROVENANCE_RUNGS  # noqa: E402
from ingest_docs import source_digest  # noqa: E402
from lint_wiki import (  # noqa: E402
    ERROR,
    INFO,
    WARNING,
    PassResult,
    parse_frontmatter,
    posix,
)
from project_binding import (  # noqa: E402
    config_path,
    discover_artefacts,
    resolve_project_root,
)

SOURCES = ("wiki", "sources")
TIMELINE = ("wiki", "timeline")
DATE_FIELDS = (("created", "created_provenance"), ("disposition_changed", "disposition_changed_provenance"))
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def lifecycle_stem(identity: str) -> str:
    """The lifecycle record's filename. Must agree with `build_timeline.lifecycle_stem`."""

    return re.sub(r"[^a-z0-9]+", "-", identity.casefold()).strip("-")


class Page:
    """One wiki page and its front matter, read once."""

    def __init__(self, path: Path, wiki_root: Path) -> None:
        self.path = path
        self.relative = posix(path, wiki_root)
        self.text = path.read_text(encoding="utf-8", errors="replace")
        self.matter = parse_frontmatter(self.text) or {}

    def get(self, key: str, default: str = "") -> str:
        value = self.matter.get(key, default)
        return value if isinstance(value, str) else str(value)


def source_pages(wiki_root: Path) -> list[Page]:
    directory = wiki_root.joinpath(*SOURCES)
    if not directory.is_dir():
        return []
    return [Page(path, wiki_root) for path in sorted(directory.glob("*.md"))]


def not_applicable(reason: str) -> list[PassResult]:
    """One informational line rather than seven silently green passes."""

    return [
        PassResult(
            "project-drift",
            issues=[f"   {reason}"],
            severity=INFO,
            fix=(
                "Bind the wiki with `scaffold.py <wiki-root> \"<Title>\" --project-root <path>`, "
                "then run `ingest_docs.py`."
            ),
        )
    ]


# -- dangling-source ------------------------------------------------------------


def check_dangling_source(
    wiki_root: Path, project_root: Path, pages: list[Page], matched: set[str]
) -> PassResult:
    result = PassResult(
        "dangling-source",
        clean_message="Every page's source is where the page says it is",
        severity=ERROR,
        fix="Run `ingest_docs.py`; it tombstones a removed artefact and follows a moved one.",
    )
    for page in pages:
        relative = page.get("source_path")
        if not relative or page.get("source_status") == "missing":
            # A tombstone is deliberate: the page records that the artefact is gone. Reporting
            # it would make the record of a deletion look like a defect.
            continue
        if not (project_root / relative).is_file():
            result.issues.append(
                f"   {page.relative} — `{relative}` does not exist, and the page is not "
                "marked missing"
            )
        elif relative not in matched:
            result.issues.append(
                f"   {page.relative} — `{relative}` exists but no longer matches the "
                "binding's globs, so the next ingest will tombstone it"
            )
    return result


# -- stale-page ----------------------------------------------------------------


def check_stale_page(
    wiki_root: Path, project_root: Path, pages: list[Page]
) -> PassResult:
    """Content digests, never timestamps.

    `WT-06` recorded that hashing raw bytes and hashing normalised text disagree on a CRLF
    checkout, so this reuses `ingest_docs.source_digest` rather than computing its own. A file
    whose mtime moved but whose content did not is not stale, and that is the whole point.
    """

    result = PassResult(
        "stale-page",
        clean_message="Every page matches its artefact's current content",
        severity=ERROR,
        fix="Run `ingest_docs.py` to recompile the changed artefacts.",
    )
    for page in pages:
        relative, recorded = page.get("source_path"), page.get("source_digest")
        if not relative or not recorded or page.get("source_status") == "missing":
            continue
        target = project_root / relative
        if not target.is_file():
            continue  # dangling-source owns this
        current = source_digest(target)
        if current != recorded:
            result.issues.append(
                f"   {page.relative} — `{relative}` now digests to "
                f"{current.split(':')[-1][:12]}, the page records "
                f"{recorded.split(':')[-1][:12]}"
            )
    return result


# -- un-ingested-artefact ------------------------------------------------------


def check_un_ingested(pages: list[Page], matched: set[str]) -> PassResult:
    """Informational. Everything added since the last ingest lands here, which is normal."""

    result = PassResult(
        "un-ingested-artefact",
        clean_message="Every artefact the globs match has a page",
        severity=INFO,
        fix="Run `ingest_docs.py` when you want these compiled.",
    )
    ingested = {page.get("source_path") for page in pages if page.get("source_path")}
    awaiting = sorted(matched - ingested)
    for relative in awaiting[:20]:
        result.issues.append(f"   {relative} — awaiting ingest")
    if len(awaiting) > 20:
        result.issues.append(f"   and {len(awaiting) - 20} more awaiting ingest")
    return result


# -- duplicate-identity --------------------------------------------------------


def check_duplicate_identity(pages: list[Page]) -> PassResult:
    """The exact corruption the identity contract exists to prevent.

    Two pages for one ticket, minted before and after its move into `done/`, is what a
    path-derived page name produces. If it ever happens again, the reader learns it here and
    not by noticing two half-complete histories of the same work.
    """

    result = PassResult(
        "duplicate-identity",
        clean_message="No identity has more than one page",
        severity=ERROR,
        fix=(
            "Delete the page whose name does not match the identity's slug, then run "
            "`ingest_docs.py`. Two pages for one artefact means one of them was named from a "
            "path."
        ),
    )
    by_identity: dict[str, list[str]] = {}
    for page in pages:
        identity = page.get("identity_key")
        if identity:
            by_identity.setdefault(identity, []).append(page.relative)
    for identity, relatives in sorted(by_identity.items()):
        if len(relatives) > 1:
            result.issues.append(f"   `{identity}` — {len(relatives)} pages: {', '.join(sorted(relatives))}")
    return result


# -- timeline-coverage ---------------------------------------------------------


def check_timeline_coverage(wiki_root: Path, pages: list[Page]) -> PassResult:
    """A warning, not an error: an ingest without a rebuild lands here, and that is normal."""

    result = PassResult(
        "timeline-coverage",
        clean_message="Every ticket has a lifecycle record and every dated page an event",
        severity=WARNING,
        fix="Run `build_timeline.py` to rebuild the axis over the current pages.",
    )
    timeline = wiki_root.joinpath(*TIMELINE)
    if not timeline.is_dir():
        result.issues.append("   wiki/timeline/ — the axis has never been built")
        return result

    records = {path.stem for path in (timeline / "tickets").glob("*.md")}
    periods = {
        path.stem: path.read_text(encoding="utf-8", errors="replace")
        for path in timeline.glob("*.md")
        if path.name != "index.md"
    }
    for page in pages:
        identity = page.get("identity_key")
        if not identity:
            continue
        if page.get("artefact_kind") == "ticket" and lifecycle_stem(identity) not in records:
            result.issues.append(f"   `{identity}` — a ticket with no lifecycle record")
        value = page.get("created")
        if not ISO_DATE.match(value):
            continue
        month = value[:7]
        if month not in periods:
            result.issues.append(
                f"   `{identity}` — created {value}, and there is no page for {month}"
            )
        elif identity not in periods[month]:
            result.issues.append(
                f"   `{identity}` — created {value}, and {month} records no event for it"
            )
    return result


# -- provenance-validity ------------------------------------------------------


def check_provenance(pages: list[Page]) -> PassResult:
    """Coherence, never quality.

    An `mtime` date is valid. So is `unknown` with no date. What is not valid is a date with no
    rung, a rung this ladder does not have, a date the rung says does not exist, or a rung that
    claims a witness for a date that is absent.
    """

    result = PassResult(
        "provenance-validity",
        clean_message="Every date carries a coherent rung",
        severity=ERROR,
        fix=(
            "Run `ingest_docs.py` to re-resolve the dates. A date the ladder cannot establish "
            "must be written as empty with the rung `unknown`, never as a plausible value."
        ),
    )
    for page in pages:
        if not page.get("identity_key"):
            continue
        for value_key, rung_key in DATE_FIELDS:
            if rung_key not in page.matter:
                result.issues.append(f"   {page.relative} — `{value_key}` has no `{rung_key}`")
                continue
            value, rung = page.get(value_key), page.get(rung_key)
            if rung not in PROVENANCE_RUNGS:
                result.issues.append(
                    f"   {page.relative} — `{rung_key}` is `{rung}`, which is not a rung of "
                    "the ladder"
                )
                continue
            if value and rung == "unknown":
                result.issues.append(
                    f"   {page.relative} — `{value_key}` is `{value}` but its rung is "
                    "`unknown`, so the value has no witness"
                )
            elif not value and rung != "unknown":
                result.issues.append(
                    f"   {page.relative} — `{rung_key}` is `{rung}` but `{value_key}` is "
                    "empty, so a witness is claimed for nothing"
                )
            elif value and not ISO_DATE.match(value):
                result.issues.append(
                    f"   {page.relative} — `{value_key}` is `{value}`, which is not an ISO date"
                )
            elif value:
                try:
                    date.fromisoformat(value)
                except ValueError:
                    result.issues.append(
                        f"   {page.relative} — `{value_key}` is `{value}`, which is not a "
                        "real date"
                    )
    return result


# -- stale-session-pointer ----------------------------------------------------


def check_session_pointers(wiki_root: Path, pages: list[Page]) -> PassResult:
    """A warning: a live session grows, and that is not a defect until you rely on its digest."""

    result = PassResult(
        "stale-session-pointer",
        clean_message="Every session pointer matches its transcript",
        severity=WARNING,
        fix="Run `session_ingest.py` to rebuild the digests over the current transcripts.",
    )
    for page in pages:
        if page.get("kind") != "ref":
            continue
        external = page.get("external_path")
        if not external:
            result.issues.append(f"   {page.relative} — a pointer with no `external_path`")
            continue
        target = Path(external)
        if not target.is_file():
            result.issues.append(
                f"   {page.relative} — `{external}` is gone, so the digest describes a "
                "transcript nothing can check"
            )
            continue
        recorded = page.get("size_bytes")
        if not recorded.isdigit():
            result.issues.append(f"   {page.relative} — `size_bytes` is `{recorded}`")
            continue
        actual = target.stat().st_size
        if actual != int(recorded):
            direction = "grew" if actual > int(recorded) else "shrank"
            result.issues.append(
                f"   {page.relative} — the transcript {direction} from {recorded} to "
                f"{actual} bytes since the digest was written"
            )
    return result


# -- Driver -------------------------------------------------------------------


def run_drift_passes(wiki_root: Path) -> list[PassResult]:
    """Seven passes, or one informational line saying they do not apply."""

    if not config_path(wiki_root).is_file():
        return not_applicable(
            "no project binding, so the project-history passes do not apply"
        )
    try:
        project_root = resolve_project_root(wiki_root)
        matched = set(discover_artefacts(wiki_root))
    except (OSError, ValueError, KeyError) as error:
        return not_applicable(f"the binding could not be read: {error}")

    pages = source_pages(wiki_root)
    return [
        check_dangling_source(wiki_root, project_root, pages, matched),
        check_stale_page(wiki_root, project_root, pages),
        check_duplicate_identity(pages),
        check_provenance(pages),
        check_timeline_coverage(wiki_root, pages),
        check_session_pointers(wiki_root, pages),
        check_un_ingested(pages, matched),
    ]


if __name__ == "__main__":
    print(__doc__)
