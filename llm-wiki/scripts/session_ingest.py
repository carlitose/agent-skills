#!/usr/bin/env python3
"""Ingest agent sessions as a pointer plus a digest, never as content.

The size constraint is the whole design. A single agent transcript runs from a few megabytes to
nearly two gigabytes, and every session adds more. The skill's raw-file policy already forbids
copying sources at that scale, so each session yields two small artefacts instead:

* a **pointer** in ``raw/refs/`` carrying ``external_path``, size, provider, session id, the
  time span, and the staleness signal — no transcript content;
* a **digest page** of 200-400 words recording what the session did: tickets touched, files
  touched, decisions.

Reading is therefore bounded per record, not per file: see ``MAX_RECORD_BYTES``. A transcript
whose records fit is ingested whole however large the file is; one whose records do not is
refused by name, because dropping the largest session quietly would delete the most history and
leave no mark.

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
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from session_catalog import (  # noqa: E402
    refresh_session_catalog,
    require_session_catalog,
)
from project_binding import BindingError, read_binding  # noqa: E402
from session_discovery import (  # noqa: E402
    DEFAULT_PROVIDERS,
    claude_transcripts,
    codex_session_cwd,
    codex_transcripts,
    pi_transcripts,
    require_known_providers,
)

@dataclass(frozen=True)
class Provider:
    """Everything that differs between providers, in one place per provider.

    ``record_kinds`` is the part that bites. The vocabularies genuinely differ, and reading one
    provider with another's words fails silently: a Pi transcript scanned for ``compacted``
    reports ``complete`` while the provider has already discarded detail, claiming the digest
    is missing nothing precisely when it is.
    """

    report_key: str
    record_kinds: dict[str, str]
    transcripts: Callable[[Path], tuple[list[Path], list[Path]]]


#: Every provider this module can compile. Adding a fourth is one entry, not four edits.
PROVIDERS: dict[str, Provider] = {
    # Claude's identity is its store directory, so a transcript there never fails to resolve.
    "claude-code": Provider(
        "claude", {}, lambda root: (claude_transcripts(root), [])
    ),
    "codex": Provider(
        "codex",
        {"session": "session_meta", "compacted": "compacted"},
        lambda root: codex_transcripts(root),
    ),
    "pi": Provider(
        "pi",
        {"session": "session", "compacted": "compaction"},
        lambda root: pi_transcripts(root),
    ),
}

#: The largest single record this module will hold in memory, in bytes.
#:
#: What memory tracks is the longest record and the cost of parsing it, not the size of the
#: file. Measured: a 574,039,077-byte transcript whose longest record is 4,949,825 bytes peaks
#: at 44.7 MB, about nine times that record and 7.8% of the file. The multiple is decoding and
#: JSON parsing, and it is why the bound is well above any record seen in the wild rather than
#: snug against it. Without a bound at all, one unterminated line is a whole-file read wearing
#: a stream's clothes: 64 MiB is roughly thirteen times the largest record ever observed here,
#: which leaves room to grow while still refusing a file that is one endless line.
MAX_RECORD_BYTES = 64 * 1024 * 1024
#: How much is read from disk at a time. Small enough to be free, large enough to be few reads.
READ_CHUNK_BYTES = 1024 * 1024


class TranscriptTooLarge(RuntimeError):
    """One record of a transcript exceeds the per-record bound, so the file cannot be streamed."""


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


def _prose(value: object) -> list[str]:
    """Return the strings one field carries, leaving every other shape undecoded.

    A block with no ``text`` is an attachment, a tool call, an image: it has a payload, not
    prose. Decoding it would put bytes into a digest that read as something the session
    said.
    """

    if isinstance(value, str):
        return [value]
    if not isinstance(value, list):
        return []
    pieces: list[str] = []
    for item in value:
        if isinstance(item, str):
            pieces.append(item)
        elif isinstance(item, dict) and isinstance(item.get("text"), str):
            pieces.append(item["text"])
    return pieces


def _text_of(record: dict) -> str:
    """Return the human-readable text a record carries, without decoding attachments.

    Providers wrap a turn at different depths. Some put the text at the top, some hand over
    a list of blocks, and some wrap the whole turn first: ``{"message": {"role": …,
    "content": [block, …]}}``. The walk therefore descends at most one dict and then one
    list, and stops. A block that itself holds a list is payload rather than prose, and
    guessing at it would invent text that nothing in the transcript ever said.
    """

    pieces: list[str] = []
    for key in ("text", "content", "message", "summary"):
        value = record.get(key)
        if isinstance(value, dict):
            for nested in ("text", "content"):
                pieces.extend(_prose(value.get(nested)))
        else:
            pieces.extend(_prose(value))
    payload = record.get("payload")
    if isinstance(payload, dict):
        for key in ("text", "message", "summary"):
            pieces.extend(_prose(payload.get(key)))
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


def _cwd_of(record: dict) -> str | None:
    """Return the startup directory a session record carries, at either depth providers use."""

    for candidate in (record, record.get("payload")):
        if isinstance(candidate, dict) and isinstance(candidate.get("cwd"), str):
            return candidate["cwd"]
    return None


def transcript_records(path: Path) -> Iterator[str]:
    """Yield one transcript line at a time, holding at most one record plus a chunk.

    ``for line in handle`` looks like a stream and is one, until a file has no newline in it:
    then it quietly becomes a whole-file read. Reading fixed chunks and splitting them makes the
    ceiling explicit, so a record past ``MAX_RECORD_BYTES`` is refused instead of swallowed.
    """

    pending = b""
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(READ_CHUNK_BYTES)
            if not chunk:
                break
            parts = (pending + chunk).split(b"\n")
            pending = parts.pop()
            for part in parts:
                yield part.decode("utf-8", "replace")
            if len(pending) > MAX_RECORD_BYTES:
                raise TranscriptTooLarge(
                    f"{path.name}: one record exceeds the {MAX_RECORD_BYTES}-byte bound "
                    f"({len(pending)} bytes read with no record boundary, in a "
                    f"{path.stat().st_size}-byte transcript). Nothing was truncated and "
                    f"nothing was skipped silently: this session was refused."
                )
    if pending:
        yield pending.decode("utf-8", "replace")


def extract(path: Path, provider: str) -> SessionFacts:
    """Stream one transcript and return its facts. The file is never loaded whole.

    Raises ``TranscriptTooLarge`` if a single record exceeds ``MAX_RECORD_BYTES``.
    """

    kinds = PROVIDERS[provider].record_kinds if provider in PROVIDERS else {}
    facts = SessionFacts(
        provider=provider,
        session_id=_session_id(path, provider),
        path=path,
        size_bytes=path.stat().st_size,
    )
    for line in transcript_records(path):
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(record, dict):
            continue
        facts.record_count += 1
        kind = str(record.get("type"))
        facts.record_types[kind] = facts.record_types.get(kind, 0) + 1
        if kind == kinds.get("compacted"):
            facts.compacted_records += 1
        if kind == kinds.get("session"):
            facts.cwd = _cwd_of(record) or facts.cwd
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
    if provider == "pi":
        # Pi names a transcript ``<iso-timestamp>_<id>.jsonl``; the timestamp is not identity.
        _, separator, identifier = path.stem.partition("_")
        return identifier if separator and identifier else path.stem
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
            "it: transcripts run from megabytes to gigabytes, so copying them would violate the",
            "raw file policy and make the wiki unusable in Git.",
            "",
            "`size_bytes`, `record_count` and `last_record_timestamp` together are the staleness",
            "signal. A resumed session appends to the same file under the same id, so the digest",
            "must be rebuilt when any of the three changes.",
            "",
        )
    )


class SessionDigestError(RuntimeError):
    """A session cannot be represented inside the bounded digest contract."""


def digest_document(facts: SessionFacts) -> str:
    """A 200-400 word page recording what the session did, attributed to the session.

    The band is enforced rather than hoped for. A session that names many files and reaches
    many decisions overruns it, so the lists are trimmed — the longest first — until the page
    fits, and the trimming is stated on the page instead of being silent. If complete identity
    metadata still pushes the shortest normal form over the limit, a compact attributed footer
    replaces explanatory prose; an impossible page fails closed instead of growing unbounded.
    """

    ladder = (
        (24, 20, 6), (24, 12, 4), (24, 8, 3), (18, 5, 2),
        (12, 4, 2), (8, 3, 1), (5, 2, 1),
    )
    for ticket_limit, file_limit, decision_limit in ladder:
        document = _digest_at(facts, ticket_limit, file_limit, decision_limit)
        if word_count(document) <= MAX_DIGEST_WORDS:
            return document
    compact = _compact_digest(_digest_at(facts, 3, 2, 1))
    if word_count(compact) <= MAX_DIGEST_WORDS:
        return compact
    raise SessionDigestError(
        f"session digest exceeds {MAX_DIGEST_WORDS} words after bounded compaction: "
        f"{facts.provider}:{facts.session_id}"
    )


def _compact_digest(document: str) -> str:
    """Replace optional explanatory sections while retaining identity and attribution."""

    prefix, marker, _ = document.partition("\n## What the transcript is made of\n")
    if not marker:
        return document
    return prefix.rstrip() + "\n\n" + "\n".join(
        (
            "## Reading this page",
            "",
            "This is the session's attributed account, not an assertion of project truth. "
            "Ticket mentions date attention rather than completion, and the complete set still "
            "feeds the provenance resolver even when the visible lists are trimmed.",
            "",
            "The matching pointer under `raw/refs/` records the external transcript path and "
            "staleness signals. The transcript remains external and is not copied into the wiki.",
            "",
        )
    )


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


def binding_providers(wiki_root: Path) -> tuple[str, ...]:
    """Return the providers a wiki's binding names, or the default set when it has no binding.

    An unbound wiki keeps the behaviour it had before the field was read; a bound one is
    obeyed literally, including when it names a provider that does not exist.
    """

    try:
        document = read_binding(wiki_root)
    except BindingError:
        return DEFAULT_PROVIDERS
    providers = document.get("session_providers")
    if not isinstance(providers, list) or not providers:
        return DEFAULT_PROVIDERS
    return tuple(str(name) for name in providers)


def ingest(
    project_root: Path,
    wiki_root: Path,
    *,
    dry_run: bool = False,
    providers: tuple[str, ...] | list[str] | None = None,
) -> dict[str, object]:
    """Write one pointer and one digest per session, for the providers the binding names.

    A provider the binding omits is not consulted and contributes no key to the report. Saying
    ``pi: 0`` would state that Pi's store was read and found empty, which is a different claim
    than never having looked at it at all.
    """

    names = require_known_providers(
        providers if providers is not None else binding_providers(wiki_root)
    )
    sessions: list[tuple[Path, str]] = []
    found: dict[str, list[Path]] = {}
    unresolved: dict[str, list[Path]] = {}
    for name in names:
        mine, cannot_resolve = PROVIDERS[name].transcripts(project_root)
        found[name] = list(mine)
        unresolved[name] = list(cannot_resolve)
        sessions.extend((path, name) for path in mine)
    if not dry_run:
        require_session_catalog(wiki_root)

    pointer_dir = wiki_root.joinpath(*POINTER_DIRECTORY)
    digest_dir = wiki_root.joinpath(*DIGEST_DIRECTORY)
    written: list[str] = []
    skipped: list[str] = []
    refused: list[dict[str, object]] = []
    mentions: dict[str, dict[str, dict[str, str]]] = {}
    for path, provider in sessions:
        try:
            facts = extract(path, provider)
        except TranscriptTooLarge as refusal:
            # One unreadable session costs that session and nothing else. Aborting the run
            # here would let the largest transcript decide whether the others get a history.
            refused.append(
                {
                    "provider": provider,
                    "session_id": _session_id(path, provider),
                    "path": path.as_posix(),
                    "size_bytes": path.stat().st_size,
                    "reason": str(refusal),
                }
            )
            continue
        mentions[f"{provider}:{facts.session_id}"] = facts.dated_mentions()
        pointer = pointer_dir / f"{provider}-{facts.session_id}.md"
        digest = digest_dir / f"session-{provider}-{facts.session_id}.md"
        pointer_text = pointer_document(facts)
        digest_text = digest_document(facts)
        if _is_current(pointer, pointer_text):
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
    report: dict[str, object] = {
        "providers": list(names),
        "sessions": len(sessions),
        "written": written,
        "skipped": skipped,
        "refused": refused,
        "catalog_updated": catalog_updated,
        "transcript_bytes": sum(path.stat().st_size for path, _ in sessions),
        "dated_ticket_mentions": mentions,
    }
    for name in names:
        key = PROVIDERS[name].report_key
        report[key] = len(found[name])
        report[f"unresolved_{key}"] = len(unresolved[name])
    return report


def _is_current(pointer: Path, expected: str) -> bool:
    """Whether the pointer on disk is exactly what this version would write for this transcript.

    Comparing the whole document, rather than the three staleness fields inside it, is what lets
    a corrected pointer reach wikis that already exist: a pointer written by an older version
    is a claim that version made, and it is rewritten on the next run rather than kept because
    its numbers happen to still match.
    """

    if not pointer.is_file():
        return False
    try:
        return pointer.read_text(encoding="utf-8") == expected
    except OSError:
        return False


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[0] in {"-h", "--help"}:
        print(__doc__)
        return 0
    report = ingest(Path(argv[0]), Path(argv[1]), dry_run="--dry-run" in argv[2:])
    providers = ", ".join(
        f"{name} {report[PROVIDERS[name].report_key]}" for name in report["providers"]
    )
    print(f"sessions          {report['sessions']} ({providers})")
    print(f"transcript bytes  {report['transcript_bytes']:,} (not copied)")
    print(f"written           {len(report['written'])}")
    print(f"skipped unchanged {len(report['skipped'])}")
    print(f"catalog updated   {report['catalog_updated']}")
    for name in report["providers"]:
        key = PROVIDERS[name].report_key
        print(f"unresolved {name:<12} {report[f'unresolved_{key}']}")
    tickets = sorted({t for m in report["dated_ticket_mentions"].values() for t in m})
    print(f"tickets mentioned {len(tickets)}: {', '.join(tickets[:12])}"
          f"{' ...' if len(tickets) > 12 else ''}")
    for refusal in report["refused"]:
        print(f"REFUSED           {refusal['reason']}")
    # A refused session is a non-zero exit: a caller that ignores the text still learns.
    return 1 if report["refused"] else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
