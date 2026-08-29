#!/usr/bin/env python3
"""Ingest agent sessions as a pointer plus a digest, never as content.

The size constraint is the whole design. This project's transcripts are ~52 MB across eleven
sessions and grow with every one. The skill's raw-file policy already forbids copying sources
at that scale, so each session yields two small artefacts instead:

* a **pointer** in ``raw/refs/`` carrying ``external_path``, size, provider, session id, the
  time span, and the staleness signal — no transcript content;
* a **digest page** of 200-400 words recording what the session did: tickets touched, files
  touched, decisions.

Two things this module refuses to do, because both would quietly corrupt the wiki:

Guess a ticket reference
    A bare ``01`` in prose is not a ticket. Only a prefixed identifier such as ``WT-01`` is,
    because that is the form this repository's ticket ids actually take. The rule is one
    regular expression and it is tested against text containing both.

Assert a session's claims as facts
    A digest summarises an agent's own output, so it will confidently restate whatever the
    session got wrong. Every line is attributed to the session rather than stated as project
    truth.

Usage:
    python3 session_ingest.py <project-root> <wiki-root> [--dry-run]
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from session_catalog import (  # noqa: E402
    refresh_session_catalog,
    require_session_catalog,
)
from session_discovery import (  # noqa: E402
    claude_transcripts,
    codex_session_cwd,
    codex_transcripts,
)

#: A ticket reference is an uppercase prefix, a hyphen, and **at least two** digits.
#:
#: ``01`` alone is prose, and so is a glob: this project's own transcripts contain the
#: instruction "vai avanti con AG-0* con /ticket-autopilot", where ``AG-0*`` is a shell
#: pattern. A one-digit rule read that as the ticket ``AG-0``, which does not exist. Every
#: ticket id in this repository carries two digits, so requiring them costs nothing and
#: removes the whole class of false positive.
TICKET_REFERENCE = re.compile(r"\b([A-Z]{2,6}-\d{2,4})\b")
#: A repository-relative path with a known source or documentation extension.
FILE_REFERENCE = re.compile(
    r"\b((?:docs|llm-wiki|ticket-autopilot|scripts|tests)/[A-Za-z0-9_./-]+"
    r"\.(?:md|py|json|ts|tsx|rs|yaml|yml))\b"
)
DECISION_MARKERS = (
    "decided", "decision", "we chose", "rejected", "instead of", "root cause",
    "confirmed", "verified", "concluded",
)
POINTER_DIRECTORY = ("raw", "refs")
DIGEST_DIRECTORY = ("wiki", "sources")
MIN_DIGEST_WORDS = 200
MAX_DIGEST_WORDS = 400


@dataclass
class SessionFacts:
    """What one transcript records, extracted without copying it."""

    provider: str
    session_id: str
    path: Path
    size_bytes: int
    record_count: int = 0
    first_timestamp: str | None = None
    last_timestamp: str | None = None
    compacted_records: int = 0
    record_types: dict[str, int] = field(default_factory=dict)
    ticket_mentions: dict[str, list[str]] = field(default_factory=dict)
    files_touched: set[str] = field(default_factory=set)
    decision_lines: list[str] = field(default_factory=list)
    cwd: str | None = None

    @property
    def span(self) -> str:
        if self.first_timestamp and self.last_timestamp:
            return f"{self.first_timestamp[:10]} to {self.last_timestamp[:10]}"
        return "unknown"

    def dated_mentions(self) -> dict[str, dict[str, str]]:
        """Earliest and latest dated mention per ticket, for LW-04's session-observed rung."""

        return {
            ticket: {"earliest": min(dates), "latest": max(dates)}
            for ticket, dates in sorted(self.ticket_mentions.items())
            if dates
        }


def _text_of(record: dict) -> str:
    """Return the human-readable text a record carries, without decoding attachments."""

    pieces: list[str] = []
    for key in ("text", "content", "message", "summary"):
        value = record.get(key)
        if isinstance(value, str):
            pieces.append(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    pieces.append(item)
                elif isinstance(item, dict) and isinstance(item.get("text"), str):
                    pieces.append(item["text"])
        elif isinstance(value, dict):
            for nested in ("text", "content"):
                if isinstance(value.get(nested), str):
                    pieces.append(value[nested])
    payload = record.get("payload")
    if isinstance(payload, dict):
        for key in ("text", "message", "summary"):
            if isinstance(payload.get(key), str):
                pieces.append(payload[key])
    return "\n".join(pieces)


def _timestamp_of(record: dict) -> str | None:
    stamp = record.get("timestamp")
    if isinstance(stamp, str) and stamp:
        return stamp
    payload = record.get("payload")
    if isinstance(payload, dict):
        stamp = payload.get("timestamp")
        if isinstance(stamp, str) and stamp:
            return stamp
    return None


def extract(path: Path, provider: str) -> SessionFacts:
    """Stream one transcript and return its facts. The file is never loaded whole."""

    facts = SessionFacts(
        provider=provider,
        session_id=_session_id(path, provider),
        path=path,
        size_bytes=path.stat().st_size,
    )
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(record, dict):
                continue
            facts.record_count += 1
            kind = str(record.get("type"))
            facts.record_types[kind] = facts.record_types.get(kind, 0) + 1
            if kind == "compacted":
                facts.compacted_records += 1
            if kind == "session_meta":
                payload = record.get("payload") or {}
                if isinstance(payload.get("cwd"), str):
                    facts.cwd = payload["cwd"]
            stamp = _timestamp_of(record)
            if stamp:
                if facts.first_timestamp is None or stamp < facts.first_timestamp:
                    facts.first_timestamp = stamp
                if facts.last_timestamp is None or stamp > facts.last_timestamp:
                    facts.last_timestamp = stamp
            text = _text_of(record)
            if not text:
                continue
            day = stamp[:10] if stamp else None
            for ticket in set(TICKET_REFERENCE.findall(text)):
                dates = facts.ticket_mentions.setdefault(ticket, [])
                if day and day not in dates:
                    dates.append(day)
            facts.files_touched.update(FILE_REFERENCE.findall(text))
            lowered = text.casefold()
            if any(marker in lowered for marker in DECISION_MARKERS):
                for sentence in re.split(r"(?<=[.!?])\s+", text):
                    stripped = sentence.strip()
                    if 40 <= len(stripped) <= 240 and any(
                        marker in stripped.casefold() for marker in DECISION_MARKERS
                    ):
                        if stripped not in facts.decision_lines:
                            facts.decision_lines.append(stripped)
                        break
    return facts


def _session_id(path: Path, provider: str) -> str:
    if provider == "codex":
        match = re.search(r"rollout-.*?-([0-9a-f-]{36})\.jsonl$", path.name)
        return match.group(1) if match else path.stem
    return path.stem


def pointer_document(facts: SessionFacts) -> str:
    """The pointer. Carries no transcript content, only how to find it and whether it moved."""

    return "\n".join(
        (
            "---",
            "kind: ref",
            f"provider: {facts.provider}",
            f"session_id: {facts.session_id}",
            f"external_path: {facts.path.as_posix()}",
            f"size_bytes: {facts.size_bytes}",
            f"record_count: {facts.record_count}",
            f"last_record_timestamp: {facts.last_timestamp or 'unknown'}",
            f"span: {facts.span}",
            "---",
            "",
            f"# Session {facts.session_id} ({facts.provider})",
            "",
            "This file is a pointer, not a copy. The transcript stays where the provider wrote",
            "it: at ~52 MB across this project's sessions, copying them would violate the raw",
            "file policy and make the wiki unusable in Git.",
            "",
            "`size_bytes`, `record_count` and `last_record_timestamp` together are the staleness",
            "signal. A resumed session appends to the same file under the same id, so the digest",
            "must be rebuilt when any of the three changes.",
            "",
        )
    )


def digest_document(facts: SessionFacts) -> str:
    """A 200-400 word page recording what the session did, attributed to the session.

    The band is enforced rather than hoped for. A session that names many files and reaches
    many decisions overruns it, so the lists are trimmed — the longest first — until the page
    fits, and the trimming is stated on the page instead of being silent.
    """

    ladder = (
        (24, 20, 6), (24, 12, 4), (24, 8, 3), (18, 5, 2),
        (12, 4, 2), (8, 3, 1), (5, 2, 1),
    )
    for ticket_limit, file_limit, decision_limit in ladder:
        document = _digest_at(facts, ticket_limit, file_limit, decision_limit)
        if word_count(document) <= MAX_DIGEST_WORDS:
            return document
    return _digest_at(facts, 3, 2, 1)


def _digest_at(
    facts: SessionFacts, ticket_limit: int, file_limit: int, decision_limit: int
) -> str:
    tickets = sorted(facts.ticket_mentions)
    files = sorted(facts.files_touched)
    body: list[str] = [
        "---",
        "type: session",
        f"provider: {facts.provider}",
        f"session_id: {facts.session_id}",
        f"span: {facts.span}",
        f"record_count: {facts.record_count}",
        f"tickets_touched: [{', '.join(tickets)}]",
        f"source_status: {'compacted' if facts.compacted_records else 'complete'}",
        "---",
        "",
        f"# {facts.provider} session {facts.session_id}",
        "",
        f"A {facts.provider} session recorded between {facts.span}, holding "
        f"{facts.record_count} records in {facts.size_bytes:,} bytes. Everything below is what "
        "the session itself recorded doing; none of it is asserted as project truth, because a "
        "session's own account of its work can be wrong in exactly the ways the work was.",
        "",
    ]
    if facts.compacted_records:
        body += [
            f"**This transcript was compacted {facts.compacted_records} time(s).** Detail was "
            "discarded by the provider before this digest was written, so the account below is "
            "incomplete by construction rather than by omission.",
            "",
        ]
    body += ["## Tickets the session names", ""]
    if tickets:
        for ticket in tickets[:ticket_limit]:
            dates = facts.ticket_mentions[ticket]
            window = f"{min(dates)} to {max(dates)}" if dates else "no dated mention"
            body.append(f"- `{ticket}` — mentioned {len(dates)} day(s), {window}")
        if len(tickets) > ticket_limit:
            body.append(
                f"- and {len(tickets) - ticket_limit} more, trimmed for length; the full set "
                "reaches the date resolver regardless of what this page shows"
            )
    else:
        body.append("- None. The session names no ticket identifier.")
    body += ["", "## Files the session names", ""]
    if files:
        for path in files[:file_limit]:
            body.append(f"- `{path}`")
        if len(files) > file_limit:
            body.append(
                f"- and {len(files) - file_limit} more, trimmed to keep this page inside its "
                "word band"
            )
    else:
        body.append("- None recognised by the path rule.")
    body += ["", "## Decisions the session reports", ""]
    if facts.decision_lines:
        for line in facts.decision_lines[:decision_limit]:
            body.append(f"- {line}")
        if len(facts.decision_lines) > decision_limit:
            body.append(
                f"- and {len(facts.decision_lines) - decision_limit} more, trimmed for length"
            )
    else:
        body.append("- None matched the decision markers. Absence here is weak evidence.")
    body += ["", "## What the transcript is made of", ""]
    body.append(
        "Record counts, which say something about the shape of the session even where its "
        "prose says little:"
    )
    body.append("")
    for kind, count in sorted(
        facts.record_types.items(), key=lambda item: (-item[1], item[0])
    )[:8]:
        body.append(f"- `{kind}` — {count}")
    body += [
        "",
        "## Reading this page",
        "",
        "The dated ticket mentions above are the input to the date resolver's",
        "`session-observed` rung: on a project whose `docs/` is untracked they are the only",
        "witness to when a ticket was worked on. They date *attention*, not completion — a",
        "session that argues about a ticket and changes nothing leaves the same trace as one",
        "that finishes it.",
        "",
        "A ticket appears here only if the transcript names it in the repository's identifier",
        "form. A bare number, a glob, or a description in prose does not count, deliberately:",
        "a loose rule turns ordinary sentences into false history, and false history is worse",
        "than a gap, because nothing marks it as missing.",
        "",
        "The pointer beside this page in `raw/refs/` records where the transcript lives and how",
        "large it was when this digest was written. If any of that changes the digest is stale,",
        "because a resumed session appends to the same file under the same identifier.",
        "",
    ]
    return "\n".join(body)


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))


def ingest(
    project_root: Path, wiki_root: Path, *, dry_run: bool = False
) -> dict[str, object]:
    """Write one pointer and one digest per session, skipping unchanged ones."""

    claude = [(path, "claude-code") for path in claude_transcripts(project_root)]
    codex, unresolved = codex_transcripts(project_root)
    sessions = claude + [(path, "codex") for path in codex]
    if not dry_run:
        require_session_catalog(wiki_root)

    pointer_dir = wiki_root.joinpath(*POINTER_DIRECTORY)
    digest_dir = wiki_root.joinpath(*DIGEST_DIRECTORY)
    written: list[str] = []
    skipped: list[str] = []
    mentions: dict[str, dict[str, dict[str, str]]] = {}
    for path, provider in sessions:
        facts = extract(path, provider)
        mentions[f"{provider}:{facts.session_id}"] = facts.dated_mentions()
        pointer = pointer_dir / f"{provider}-{facts.session_id}.md"
        digest = digest_dir / f"session-{provider}-{facts.session_id}.md"
        pointer_text = pointer_document(facts)
        digest_text = digest_document(facts)
        if _is_current(pointer, facts):
            skipped.append(digest.name)
            continue
        if not dry_run:
            pointer_dir.mkdir(parents=True, exist_ok=True)
            digest_dir.mkdir(parents=True, exist_ok=True)
            pointer.write_text(pointer_text, encoding="utf-8")
            digest.write_text(digest_text, encoding="utf-8")
        written.append(digest.name)
    catalog_updated = False
    if not dry_run:
        catalog_updated = refresh_session_catalog(wiki_root)
    return {
        "sessions": len(sessions),
        "claude": len(claude),
        "codex": len(codex),
        "unresolved_codex": len(unresolved),
        "written": written,
        "skipped": skipped,
        "catalog_updated": catalog_updated,
        "transcript_bytes": sum(path.stat().st_size for path, _ in sessions),
        "dated_ticket_mentions": mentions,
    }


def _is_current(pointer: Path, facts: SessionFacts) -> bool:
    """Whether an existing pointer already describes this exact transcript state."""

    if not pointer.is_file():
        return False
    try:
        existing = pointer.read_text(encoding="utf-8")
    except OSError:
        return False
    for key, value in (
        ("size_bytes", facts.size_bytes),
        ("record_count", facts.record_count),
        ("last_record_timestamp", facts.last_timestamp or "unknown"),
    ):
        if f"{key}: {value}" not in existing:
            return False
    return True


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[0] in {"-h", "--help"}:
        print(__doc__)
        return 0
    report = ingest(Path(argv[0]), Path(argv[1]), dry_run="--dry-run" in argv[2:])
    print(f"sessions          {report['sessions']} "
          f"(claude {report['claude']}, codex {report['codex']})")
    print(f"transcript bytes  {report['transcript_bytes']:,} (not copied)")
    print(f"written           {len(report['written'])}")
    print(f"skipped unchanged {len(report['skipped'])}")
    print(f"catalog updated   {report['catalog_updated']}")
    print(f"unresolved codex  {report['unresolved_codex']}")
    tickets = sorted({t for m in report["dated_ticket_mentions"].values() for t in m})
    print(f"tickets mentioned {len(tickets)}: {', '.join(tickets[:12])}"
          f"{' ...' if len(tickets) > 12 else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
