from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping


CONTRACT_VERSION = 1
ALLOWED_MODES = frozenset({"AFK", "HITL"})
REQUIRED_KEYS = frozenset(
    {"ticket_schema", "ticket_id", "execution_mode", "blocked_by"}
)


class ContractError(ValueError):
    """A ticket folder does not satisfy the public ticket contract."""

    def __init__(self, message: str, *, path: str = "ticket") -> None:
        self.path = path
        super().__init__(message)


@dataclass(frozen=True)
class ParsedTicket:
    """A normalized Ticket Envelope and its Markdown body."""

    envelope: dict[str, Any]
    body: str


@dataclass(frozen=True)
class Ticket:
    ticket_id: str
    execution_mode: str
    blocked_by: tuple[str, ...]
    path: Path
    digest: str


@dataclass(frozen=True)
class TicketGraph:
    folder: Path
    tickets: dict[str, Ticket]
    order: tuple[str, ...]
    completed_ids: frozenset[str]
    dispositions: dict[str, str] = field(default_factory=dict)


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def _parse_front_matter(text: str, path: Path) -> dict[str, Any]:
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise ContractError(f"{path}: missing versioned front matter")
    try:
        end = lines.index("---", 1)
    except ValueError as error:
        raise ContractError(f"{path}: unterminated front matter") from error

    data: dict[str, Any] = {}
    current_list: str | None = None
    for number, raw_line in enumerate(lines[1:end], start=2):
        if not raw_line.strip():
            continue
        list_match = re.fullmatch(r"\s+-\s+(.+)", raw_line)
        if list_match:
            if current_list is None:
                raise ContractError(f"{path}:{number}: list item without a key")
            data[current_list].append(_unquote(list_match.group(1)))
            continue
        if current_list is not None and raw_line.strip() == "[]":
            current_list = None
            continue
        key_match = re.fullmatch(r"([a-z][a-z0-9_]*):(?:\s*(.*))?", raw_line)
        if not key_match:
            raise ContractError(f"{path}:{number}: unsupported front matter syntax")
        key, raw_value = key_match.groups()
        if key in data:
            raise ContractError(f"{path}:{number}: duplicate key {key!r}")
        if key not in REQUIRED_KEYS:
            raise ContractError(f"{path}:{number}: undeclared key {key!r}")
        raw_value = (raw_value or "").strip()
        if key == "blocked_by":
            if raw_value not in ("", "[]"):
                raise ContractError(f"{path}:{number}: blocked_by must be a list")
            data[key] = []
            current_list = key if raw_value == "" else None
        else:
            if not raw_value:
                raise ContractError(f"{path}:{number}: {key} requires a value")
            data[key] = _unquote(raw_value)
            current_list = None
    if set(data) != REQUIRED_KEYS:
        missing = ", ".join(sorted(REQUIRED_KEYS - set(data)))
        raise ContractError(f"{path}: missing keys: {missing}")
    return data


def normalize_ticket_envelope(
    value: Mapping[str, Any],
    *,
    source: str = "ticket",
) -> dict[str, Any]:
    """Validate and normalize one versioned Ticket Envelope."""

    if not isinstance(value, Mapping):
        raise ContractError(f"{source}: Ticket Envelope must be a mapping")
    unknown = sorted(set(value) - REQUIRED_KEYS)
    if unknown:
        raise ContractError(f"{source}: unknown field: {', '.join(unknown)}")
    missing = sorted(REQUIRED_KEYS - set(value))
    if missing:
        raise ContractError(f"{source}: missing required field: {', '.join(missing)}")

    raw_schema = value["ticket_schema"]
    if isinstance(raw_schema, bool) or not (
        isinstance(raw_schema, int)
        or (isinstance(raw_schema, str) and re.fullmatch(r"[0-9]+", raw_schema))
    ):
        raise ContractError(f"{source}: ticket_schema must be an integer")
    schema = int(raw_schema)
    if schema != CONTRACT_VERSION:
        raise ContractError(
            f"{source}: unsupported ticket_schema {schema}; expected {CONTRACT_VERSION}"
        )

    if not isinstance(value["ticket_id"], str):
        raise ContractError(f"{source}: ticket_id must be text")
    ticket_id = value["ticket_id"]
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", ticket_id):
        raise ContractError(f"{source}: invalid ticket_id {ticket_id!r}")

    if not isinstance(value["execution_mode"], str):
        raise ContractError(f"{source}: execution_mode must be text")
    mode = value["execution_mode"].upper()
    if mode not in ALLOWED_MODES:
        raise ContractError(f"{source}: execution_mode must be AFK or HITL")

    raw_blockers = value["blocked_by"]
    if not isinstance(raw_blockers, (list, tuple)):
        raise ContractError(f"{source}: blocked_by must be a list")
    if any(not isinstance(blocker, str) for blocker in raw_blockers):
        raise ContractError(f"{source}: blocker must be text")
    blockers = list(raw_blockers)
    invalid = [
        blocker
        for blocker in blockers
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", blocker)
    ]
    if invalid:
        raise ContractError(f"{source}: invalid blocker {invalid[0]!r}")
    if len(blockers) != len(set(blockers)):
        raise ContractError(f"{source}: duplicate blocker")
    if ticket_id in blockers:
        raise ContractError(f"{source}: ticket cannot block itself")

    return {
        "ticket_schema": schema,
        "ticket_id": ticket_id,
        "execution_mode": mode,
        "blocked_by": blockers,
    }


def parse_ticket_markdown(
    markdown: str,
    *,
    source: str = "ticket",
) -> ParsedTicket:
    """Parse canonical Markdown; legacy text is accepted only by migration."""

    if not isinstance(markdown, str):
        raise ContractError(f"{source}: ticket must be text")
    lines = markdown.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\r\n") != "---":
        raise ContractError(f"{source}: missing versioned front matter")
    closing_index = next(
        (
            index
            for index, line in enumerate(lines[1:], start=1)
            if line.rstrip("\r\n") == "---"
        ),
        None,
    )
    if closing_index is None:
        raise ContractError(f"{source}: unterminated front matter")
    body_lines = lines[closing_index + 1 :]
    blank_lines = {"\n", "\r\n"}
    if (
        not body_lines
        or body_lines[0] not in blank_lines
        or (len(body_lines) > 1 and body_lines[1] in blank_lines)
    ):
        raise ContractError(
            f"{source}: closing front matter must be followed by exactly one blank line"
        )

    envelope = normalize_ticket_envelope(
        _parse_front_matter(markdown, Path(source)),
        source=source,
    )
    body = "".join(body_lines[1:])
    return ParsedTicket(envelope=envelope, body=body)


def serialize_ticket_markdown(
    envelope: Mapping[str, Any],
    body: str,
) -> str:
    """Serialize canonical front matter with stable field and dependency order."""

    normalized = normalize_ticket_envelope(envelope)
    if not isinstance(body, str):
        raise ContractError("ticket: body must be text")
    if body.startswith(("\n", "\r")):
        raise ContractError("ticket: body must not start with a blank line")

    blockers = normalized["blocked_by"]
    if blockers:
        blocked_by = "blocked_by:\n" + "".join(
            f"  - {json.dumps(blocker, ensure_ascii=False)}\n"
            for blocker in blockers
        )
    else:
        blocked_by = "blocked_by: []\n"
    front_matter = (
        "---\n"
        f'ticket_schema: {normalized["ticket_schema"]}\n'
        f'ticket_id: {json.dumps(normalized["ticket_id"], ensure_ascii=False)}\n'
        f'execution_mode: {normalized["execution_mode"]}\n'
        f"{blocked_by}"
        "---\n"
    )
    return f"{front_matter}\n{body}"


def read_ticket_text(path: Path) -> str:
    """Read ticket text using the newline normalization bound into its digest."""

    with path.open("r", encoding="utf-8", newline=None) as source:
        return source.read()


def ticket_source_digest(path: Path) -> str:
    """Return the canonical digest used by snapshots, ledgers, and CandidateRef."""

    return hashlib.sha256(read_ticket_text(path).encode("utf-8")).hexdigest()


def parse_ticket(path: Path) -> Ticket:
    text = read_ticket_text(path)
    return _ticket_from_text(path, text)


def _ticket_from_text(path: Path, text: str) -> Ticket:
    data = parse_ticket_markdown(text, source=str(path)).envelope
    return Ticket(
        ticket_id=data["ticket_id"],
        execution_mode=data["execution_mode"],
        blocked_by=tuple(data["blocked_by"]),
        path=path.resolve(),
        digest=hashlib.sha256(text.encode("utf-8")).hexdigest(),
    )


def _sort_key(ticket_id: str) -> tuple[tuple[int, object], ...]:
    return tuple(
        (0, int(part)) if part.isdigit() else (1, part.casefold())
        for part in re.split(r"(\d+)", ticket_id)
        if part
    )


def _validate_acyclic(tickets: dict[str, Ticket]) -> None:
    visiting: list[str] = []
    visited: set[str] = set()

    def visit(ticket_id: str) -> None:
        if ticket_id in visiting:
            start = visiting.index(ticket_id)
            cycle = " -> ".join((*visiting[start:], ticket_id))
            raise ContractError(f"dependency cycle: {cycle}")
        if ticket_id in visited:
            return
        visiting.append(ticket_id)
        for blocker in tickets[ticket_id].blocked_by:
            visit(blocker)
        visiting.pop()
        visited.add(ticket_id)

    for ticket_id in sorted(tickets, key=_sort_key):
        visit(ticket_id)


def validate_ticket_graph(
    folder: Path,
    ticket_texts: Mapping[Path, str],
    *,
    completed_paths: Iterable[Path] = (),
    disposition_paths: Mapping[Path, str] | None = None,
) -> TicketGraph:
    """Validate one complete canonical ticket set without reading or mutating files."""

    resolved = folder.resolve()
    completed = {path.resolve() for path in completed_paths}
    by_path = {
        path.resolve(): disposition
        for path, disposition in (disposition_paths or {}).items()
    }
    if any(
        disposition not in {"open", "on-hold", "canceled", "completed"}
        for disposition in by_path.values()
    ):
        raise ContractError("ticket source disposition is invalid")
    tickets: dict[str, Ticket] = {}
    completed_ids: set[str] = set()
    dispositions: dict[str, str] = {}
    for raw_path in sorted(ticket_texts, key=lambda path: str(path.resolve())):
        path = raw_path.resolve()
        ticket = _ticket_from_text(path, ticket_texts[raw_path])
        if ticket.ticket_id in tickets:
            raise ContractError(
                f"duplicate ticket_id {ticket.ticket_id!r}: "
                f"{tickets[ticket.ticket_id].path} and {path}"
            )
        tickets[ticket.ticket_id] = ticket
        disposition = by_path.get(path, "completed" if path in completed else "open")
        dispositions[ticket.ticket_id] = disposition
        if disposition == "completed":
            completed_ids.add(ticket.ticket_id)
    for ticket in tickets.values():
        for blocker in ticket.blocked_by:
            if blocker not in tickets:
                raise ContractError(
                    f"{ticket.path}: missing dependency {blocker!r}"
                )
    _validate_acyclic(tickets)
    return TicketGraph(
        folder=resolved,
        tickets=tickets,
        order=tuple(sorted(tickets, key=_sort_key)),
        completed_ids=frozenset(completed_ids),
        dispositions=dispositions,
    )


def parse_ticket_folder(folder: Path) -> TicketGraph:
    resolved = folder.resolve()
    if not resolved.is_dir():
        raise ContractError(f"ticket folder does not exist: {resolved}")
    pending_paths = sorted(
        (
            path
            for path in resolved.glob("*.md")
            if path.is_file()
        ),
        key=lambda path: path.name,
    )
    disposition_paths = {
        path: disposition
        for directory, disposition in (
            ("hold", "on-hold"),
            ("canceled", "canceled"),
            ("done", "completed"),
        )
        for path in sorted(
            (item for item in (resolved / directory).glob("*.md") if item.is_file()),
            key=lambda item: item.name,
        )
    }
    paths = [*pending_paths, *disposition_paths]
    if not paths:
        raise ContractError(f"no ticket files in {resolved}")
    return validate_ticket_graph(
        resolved,
        {path: read_ticket_text(path) for path in paths},
        disposition_paths={
            **{path: "open" for path in pending_paths},
            **disposition_paths,
        },
    )


def _legacy_blockers(section: str, *, source: str) -> list[str]:
    blockers: list[str] = []
    saw_none = False
    none_entries = {"None", "None - can start immediately."}
    for line_number, line in enumerate(section.splitlines(), start=1):
        entry = line.strip()
        if not entry:
            continue
        if not entry.startswith("- "):
            raise ContractError(
                f"{source}: legacy Blocked By line {line_number}: "
                f"unsupported entry {entry!r}",
                path=source,
            )
        value = entry[2:].strip()
        if value in none_entries:
            if blockers or saw_none:
                raise ContractError(
                    f"{source}: legacy Blocked By line {line_number}: "
                    f"unsupported entry {entry!r}",
                    path=source,
                )
            saw_none = True
            continue
        if saw_none:
            raise ContractError(
                f"{source}: legacy Blocked By line {line_number}: "
                f"unsupported entry {entry!r}",
                path=source,
            )

        link = re.fullmatch(
            r"\[([^][]+\.md)\]\(([^()\s]+)\)(?: — completed\.)?",
            value,
        )
        candidate: str | None = None
        if link is not None:
            label, target = link.groups()
            target_name = target.rsplit("/", 1)[-1]
            if (
                target.startswith("/")
                or "://" in target
                or target_name != label
            ):
                link = None
            else:
                stem = target_name[:-3]
                numeric_prefix = re.match(r"^(\d+)-", stem)
                candidate = (
                    numeric_prefix.group(1) if numeric_prefix is not None else stem
                )
        else:
            plain = re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", value)
            quoted = re.fullmatch(
                r"(?P<quote>[`'\"])(?P<id>[A-Za-z0-9][A-Za-z0-9._-]*)"
                r"(?P=quote)",
                value,
            )
            if plain is not None:
                candidate = plain.group(0)
            elif quoted is not None:
                candidate = quoted.group("id")
        if candidate is None:
            raise ContractError(
                f"{source}: legacy Blocked By line {line_number}: "
                f"unsupported entry {entry!r}",
                path=source,
            )
        blockers.append(candidate)
    return blockers


def migrate_ticket_text(
    text: str,
    fallback_id: str | None = None,
    *,
    source: str = "ticket",
) -> str:
    if text.startswith(("---\n", "---\r\n")):
        parse_ticket_markdown(text, source=source)
        raise ContractError(
            f"{source}: ticket already uses versioned front matter",
            path=source,
        )

    section_pattern = re.compile(
        r"(?ms)^## (?P<title>[^\n]+)\n+(?P<body>.*?)(?=^## |\Z)"
    )
    removable = {"Ticket ID", "Execution Mode", "Blocked By"}
    sections: dict[str, str] = {}
    for match in section_pattern.finditer(text):
        title = match.group("title").strip()
        if title in removable and title in sections:
            raise ContractError(
                f"{source}: duplicate legacy section {title!r}",
                path=source,
            )
        sections[title] = match.group("body").strip()
    ticket_id = sections.get("Ticket ID", fallback_id)
    if not ticket_id:
        raise ContractError(
            f"{source}: legacy ticket has no explicit Ticket ID",
            path=source,
        )
    blockers = _legacy_blockers(sections.get("Blocked By", ""), source=source)

    if "Execution Mode" not in sections:
        raise ContractError(
            f"{source}: legacy Execution Mode section is required",
            path=source,
        )
    mode = sections["Execution Mode"].strip().upper()
    if mode not in ALLOWED_MODES:
        raise ContractError(
            f"{source}: legacy Execution Mode must be AFK or HITL",
            path=source,
        )
    body = section_pattern.sub(
        lambda match: "" if match.group("title").strip() in removable else match.group(0),
        text,
    ).lstrip()
    envelope = normalize_ticket_envelope(
        {
            "ticket_schema": CONTRACT_VERSION,
            "ticket_id": ticket_id.strip(),
            "execution_mode": mode,
            "blocked_by": blockers,
        },
        source=source,
    )
    candidate = serialize_ticket_markdown(
        envelope,
        body,
    )
    parse_ticket_markdown(candidate, source=source)
    return candidate
