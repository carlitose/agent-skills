#!/usr/bin/env python3
"""Build the wiki's temporal axis: when each thing happened, and how we know.

Three artefact kinds under ``wiki/timeline/``:

``index.md``
    The axis itself, listing every period that has an event.
``<yyyy-mm>.md``
    One page per month in which something happened, with a mermaid timeline.
``tickets/<identity>.md``
    One lifecycle record per ticket: disposition, dates, provenance, run id, and the sessions
    that named it.

**A date is never invented here.** The resolver already refuses to guess, and this module
refuses to hide the refusal: an unresolved date renders as the word ``unknown`` with the reason,
never as a plausible-looking value, and a low-confidence ``mtime`` date is marked in the text
rather than only in a field. A reader who cannot tell a recorded fact from a filesystem
timestamp has no reason to trust the axis at all.

No period is fabricated. A month with no event gets no page, and the index says how many months
the axis spans versus how many carry events, so a gap reads as a gap.

Usage:
    python3 build_timeline.py <wiki-root> [--dry-run] [--json]
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ingest_docs import SOURCES_DIRECTORY, read_page_front_matter  # noqa: E402
from project_binding import resolve_project_root  # noqa: E402

TIMELINE_DIRECTORY = ("wiki", "timeline")
TICKETS_SUBDIRECTORY = "tickets"
PROVENANCE_LABEL = {
    "git-rename": "a rename recorded in Git",
    "git-commit": "a commit touching the file",
    "frontmatter": "a date written in the artefact",
    "session-observed": "a dated mention in a transcript",
    "mtime": "a filesystem timestamp",
    "unknown": "no witness at all",
}
LOW_CONFIDENCE = frozenset({"mtime"})
MONTH = re.compile(r"^(\d{4}-\d{2})")


@dataclass(frozen=True)
class Event:
    """One dated thing that happened, carrying the rung that dated it."""

    date: str
    kind: str
    identity: str
    title: str
    provenance: str

    @property
    def month(self) -> str | None:
        match = MONTH.match(self.date)
        return match.group(1) if match else None

    @property
    def low_confidence(self) -> bool:
        return self.provenance in LOW_CONFIDENCE


def _sessions(wiki_root: Path) -> list[dict[str, object]]:
    """Read the session digests LW-08 wrote, if any."""

    sources = wiki_root.joinpath(*SOURCES_DIRECTORY)
    if not sources.is_dir():
        return []
    found = []
    for page in sorted(sources.glob("session-*.md")):
        matter = read_page_front_matter(page)
        if matter.get("type") != "session":
            continue
        tickets = [
            item.strip()
            for item in matter.get("tickets_touched", "").strip("[]").split(",")
            if item.strip()
        ]
        found.append(
            {
                "page": page.stem,
                "provider": matter.get("provider", "unknown"),
                "session_id": matter.get("session_id", page.stem),
                "span": matter.get("span", "unknown"),
                "tickets": tickets,
            }
        )
    return found


def collect(wiki_root: Path) -> dict[str, object]:
    """Read the source pages and turn their dates into events."""

    sources = wiki_root.joinpath(*SOURCES_DIRECTORY)
    events: list[Event] = []
    records: list[dict[str, object]] = []
    unknown_dates: list[dict[str, str]] = []
    if sources.is_dir():
        for page in sorted(sources.glob("*.md")):
            matter = read_page_front_matter(page)
            if matter.get("type") != "source":
                continue
            identity = matter.get("identity_key", page.stem)
            title = matter.get("title", "").strip('"') or identity
            for field, provenance_field, kind in (
                ("created", "created_provenance", "created"),
                (
                    "disposition_changed",
                    "disposition_changed_provenance",
                    "disposition-changed",
                ),
            ):
                value = (matter.get(field) or "").strip()
                provenance = (matter.get(provenance_field) or "unknown").strip()
                if value:
                    events.append(Event(value, kind, identity, title, provenance))
                elif kind == "created" or matter.get("disposition") not in {
                    None,
                    "",
                    "open",
                    "not-applicable",
                }:
                    unknown_dates.append(
                        {"identity": identity, "event": kind, "reason": provenance}
                    )
            records.append(
                {
                    "identity": identity,
                    "title": title,
                    "page": page.stem,
                    "kind": matter.get("artefact_kind", "unknown"),
                    "disposition": matter.get("disposition", "unknown"),
                    "source_path": matter.get("source_path", ""),
                    "source_status": matter.get("source_status", "present"),
                    "run_id": matter.get("run_id"),
                    "created": (matter.get("created") or "").strip(),
                    "created_provenance": (matter.get("created_provenance") or "unknown").strip(),
                    "changed": (matter.get("disposition_changed") or "").strip(),
                    "changed_provenance": (
                        matter.get("disposition_changed_provenance") or "unknown"
                    ).strip(),
                }
            )
    sessions = _sessions(wiki_root)
    # A digest records the bare identifier a transcript wrote — ``WT-01`` — while a lifecycle
    # record is keyed on the full identity — ``ticket:windows-text-fidelity/WT-01``. Joining
    # them on the bare form silently linked nothing, so the join is on the identity's own
    # suffix. Two folders could in principle carry the same bare id; that would over-link
    # rather than under-link, and the digest names the provider and span so a reader can tell.
    identity_by_bare: dict[str, list[str]] = defaultdict(list)
    for record in records:
        identity = str(record["identity"])
        identity_by_bare[identity.rsplit("/", 1)[-1]].append(identity)
    by_ticket: dict[str, list[dict[str, object]]] = defaultdict(list)
    for session in sessions:
        for ticket in session["tickets"]:  # type: ignore[index]
            for identity in identity_by_bare.get(str(ticket), []):
                by_ticket[identity].append(session)
    return {
        "events": events,
        "records": records,
        "sessions": sessions,
        "sessions_by_ticket": dict(by_ticket),
        "unknown_dates": unknown_dates,
    }


def _date_phrase(value: str, provenance: str) -> str:
    if not value:
        return f"**unknown** — {PROVENANCE_LABEL.get(provenance, provenance)}"
    label = PROVENANCE_LABEL.get(provenance, provenance)
    if provenance in LOW_CONFIDENCE:
        return f"**{value}** — low confidence, from {label}"
    return f"**{value}** — from {label}"


def render_lifecycle(record: dict[str, object], sessions: list[dict[str, object]]) -> str:
    """One ticket's lifecycle record, keyed on identity so a move updates it."""

    identity = str(record["identity"])
    lines = [
        "---",
        "type: lifecycle",
        f"identity_key: {identity}",
        f"disposition: {record['disposition']}",
        f"created: {record['created']}",
        f"created_provenance: {record['created_provenance']}",
        f"disposition_changed: {record['changed']}",
        f"disposition_changed_provenance: {record['changed_provenance']}",
        f"source_status: {record['source_status']}",
    ]
    if record.get("run_id"):
        lines.append(f"run_id: {record['run_id']}")
    lines += [
        "---",
        "",
        f"# {record['title']}",
        "",
        f"Lifecycle of `{identity}`, currently **{record['disposition']}**.",
        "",
        "## Dates",
        "",
        f"- Created: {_date_phrase(str(record['created']), str(record['created_provenance']))}",
        f"- Disposition changed: "
        f"{_date_phrase(str(record['changed']), str(record['changed_provenance']))}",
        "",
    ]
    if record["source_status"] == "missing":
        lines += [
            "The source artefact no longer exists. This record is kept because the artefact did",
            "exist: deleting it would make the axis claim otherwise.",
            "",
        ]
    lines += ["## Sessions that named it", ""]
    if sessions:
        for session in sessions:
            lines.append(
                f"- [[sources/{session['page']}]] — {session['provider']}, {session['span']}"
            )
        lines += [
            "",
            "A session naming a ticket dates *attention*, not completion. One that argued about",
            "it and changed nothing leaves the same trace as one that finished it.",
        ]
    else:
        lines.append("- None. No transcript names this identifier.")
    if record.get("run_id"):
        lines += [
            "",
            "## Run",
            "",
            f"Completed under autopilot run `{record['run_id']}`. That sidecar carries no date,",
            "so nothing here is dated from it.",
        ]
    lines += ["", f"Source page: [[sources/{record['page']}]]", ""]
    # Cite the periods this record's own dates fall in. The timeline catalog links down
    # to a period page, but a catalog entry is not a citation, so without this a period
    # page reads as an orphan even when the axis is complete.
    periods = sorted(
        {
            str(value)[:7]
            for value in (record.get("created"), record.get("changed"))
            if isinstance(value, str) and len(value) >= 7 and value[:4].isdigit()
        }
    )
    if periods:
        joined = ", ".join(f"[[timeline/{period}]]" for period in periods)
        lines += [f"Period: {joined}", ""]
    return "\n".join(lines)


def render_period(month: str, events: list[Event]) -> str:
    """One month, as a mermaid timeline. Never ASCII art."""

    ordered = sorted(events, key=lambda event: (event.date, event.identity))
    lines = [
        "---",
        "type: period",
        f"period: {month}",
        f"event_count: {len(ordered)}",
        "---",
        "",
        f"# {month}",
        "",
        f"{len(ordered)} dated event(s). Every date carries the rung that produced it; a date",
        "the resolver could not establish is absent from this page rather than guessed onto it.",
        "",
        "```mermaid",
        "timeline",
        f"    title Events in {month}",
    ]
    by_day: dict[str, list[Event]] = defaultdict(list)
    for event in ordered:
        by_day[event.date].append(event)
    for day in sorted(by_day):
        labels = " : ".join(
            f"{event.kind} {event.identity}" for event in by_day[day][:4]
        )
        if len(by_day[day]) > 4:
            labels += f" : and {len(by_day[day]) - 4} more"
        lines.append(f"    {day} : {labels}")
    lines += ["```", "", "## Events", ""]
    for event in ordered:
        marker = " *(low confidence)*" if event.low_confidence else ""
        lines.append(
            f"- `{event.date}` — {event.kind} of {event.title} "
            f"(`{event.identity}`), from {PROVENANCE_LABEL.get(event.provenance, event.provenance)}"
            f"{marker}"
        )
    lines.append("")
    return "\n".join(lines)


def lifecycle_stem(identity: str) -> str:
    """The lifecycle record's filename, derived from identity exactly as `build` derives it."""

    return re.sub(r"[^a-z0-9]+", "-", identity.casefold()).strip("-")


def render_index(
    months: dict[str, list[Event]],
    records: list[dict[str, object]],
    sessions: list[dict[str, object]],
    unknown_dates: list[dict[str, str]],
) -> str:
    ordered = sorted(months)
    span = ""
    if ordered:
        span = f"{ordered[0]} to {ordered[-1]}"
    total_events = sum(len(items) for items in months.values())
    provenance_counts: dict[str, int] = defaultdict(int)
    for items in months.values():
        for event in items:
            provenance_counts[event.provenance] += 1
    lines = [
        "---",
        "type: timeline",
        f"periods: {len(ordered)}",
        f"events: {total_events}",
        "---",
        "",
        "# Timeline",
        "",
        f"{total_events} dated event(s) across {len(ordered)} period(s), {span}.",
        "",
        "A month appears here only if something happened in it. An empty month has no page,",
        "because inventing one would make the axis look complete where it is merely quiet.",
        "",
        "## Periods",
        "",
    ]
    for month in ordered:
        lines.append(f"- [[timeline/{month}]] — {len(months[month])} event(s)")
    lines += ["", "## How these dates were established", ""]
    for provenance in sorted(provenance_counts, key=lambda key: -provenance_counts[key]):
        lines.append(
            f"- `{provenance}` — {provenance_counts[provenance]} event(s), "
            f"{PROVENANCE_LABEL.get(provenance, provenance)}"
        )
    if unknown_dates:
        lines += [
            "",
            "## Dates that could not be established",
            "",
            f"{len(unknown_dates)} event(s) have no date. They are listed rather than omitted,",
            "because a silent gap is indistinguishable from an absence of history.",
            "",
        ]
        for item in unknown_dates[:20]:
            lines.append(f"- `{item['identity']}` — {item['event']}: {item['reason']}")
        if len(unknown_dates) > 20:
            lines.append(f"- and {len(unknown_dates) - 20} more")
    lines += ["", "## Lifecycle records", ""]
    tickets = [record for record in records if record["kind"] == "ticket"]
    lines.append(f"{len(tickets)} ticket(s) with a lifecycle record.")
    lines.append("")
    for record in sorted(tickets, key=lambda item: str(item["identity"])):
        stem = lifecycle_stem(str(record["identity"]))
        lines.append(
            f"- [[timeline/tickets/{stem}]] — `{record['identity']}`, "
            f"{record.get('disposition') or 'disposition unknown'}"
        )
    lines += ["", "## Sessions", ""]
    lines.append(
        f"{len(sessions)} session digest(s) feed this axis."
        if sessions
        else "No session digests are present; run the session ingest first."
    )
    lines.append("")
    return "\n".join(lines)


def ensure_indexed(wiki_root: Path) -> bool:
    """Add the timeline to `wiki/index.md` if it is not there yet.

    `ingest_docs` writes this entry too, but only when the timeline already exists — so on the
    first build the catalog would not mention the axis until the next ingest. Both writers are
    idempotent and agree on the line.
    """

    index = wiki_root / "wiki" / "index.md"
    if not index.is_file():
        return False
    text = index.read_text(encoding="utf-8")
    if "[[timeline/index]]" in text:
        return False
    if not text.endswith("\n"):
        text += "\n"
    index.write_text(
        text
        + "\n## Timeline\n\n"
        + "- [[timeline/index]] — when each artefact happened, and how each date is known\n",
        encoding="utf-8",
    )
    return True


def build(wiki_root: Path, *, dry_run: bool = False) -> dict[str, object]:
    collected = collect(wiki_root)
    events: list[Event] = collected["events"]  # type: ignore[assignment]
    records = collected["records"]
    sessions = collected["sessions"]
    by_ticket = collected["sessions_by_ticket"]

    months: dict[str, list[Event]] = defaultdict(list)
    for event in events:
        if event.month:
            months[event.month].append(event)

    timeline = wiki_root.joinpath(*TIMELINE_DIRECTORY)
    tickets_dir = timeline / TICKETS_SUBDIRECTORY
    written: list[str] = []
    if not dry_run:
        timeline.mkdir(parents=True, exist_ok=True)
        tickets_dir.mkdir(parents=True, exist_ok=True)
    for month, items in sorted(months.items()):
        target = timeline / f"{month}.md"
        if not dry_run:
            target.write_text(render_period(month, items), encoding="utf-8")
        written.append(target.name)
    for record in records:  # type: ignore[union-attr]
        if record["kind"] != "ticket":
            continue
        stem = lifecycle_stem(str(record["identity"]))
        target = tickets_dir / f"{stem}.md"
        if not dry_run:
            target.write_text(
                render_lifecycle(record, by_ticket.get(str(record["identity"]), [])),  # type: ignore[union-attr]
                encoding="utf-8",
            )
        written.append(f"{TICKETS_SUBDIRECTORY}/{target.name}")
    index = timeline / "index.md"
    if not dry_run:
        index.write_text(
            render_index(months, records, sessions, collected["unknown_dates"]),  # type: ignore[arg-type]
            encoding="utf-8",
        )
    written.append(index.name)
    if not dry_run and ensure_indexed(wiki_root):
        written.append("index.md")
    return {
        "events": len(events),
        "periods": sorted(months),
        "lifecycle_records": sum(1 for r in records if r["kind"] == "ticket"),  # type: ignore[union-attr]
        "sessions": len(sessions),  # type: ignore[arg-type]
        "unknown_dates": len(collected["unknown_dates"]),  # type: ignore[arg-type]
        "provenance": {
            provenance: sum(
                1 for event in events if event.provenance == provenance
            )
            for provenance in sorted({event.provenance for event in events})
        },
        "written": written,
    }


def main(argv: list[str]) -> int:
    if not argv or argv[0] in {"-h", "--help"}:
        print(__doc__)
        return 0
    wiki_root = Path(argv[0])
    resolve_project_root(wiki_root)
    report = build(wiki_root, dry_run="--dry-run" in argv[1:])
    if "--json" in argv[1:]:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    print(f"events            {report['events']}")
    print(f"periods           {len(report['periods'])}: {', '.join(report['periods'])}")
    print(f"lifecycle records {report['lifecycle_records']}")
    print(f"sessions          {report['sessions']}")
    print(f"unknown dates     {report['unknown_dates']}")
    for provenance, count in report["provenance"].items():
        print(f"  {provenance:18} {count}")
    print(f"written           {len(report['written'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
