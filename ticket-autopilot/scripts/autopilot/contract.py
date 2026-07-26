from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


CONTRACT_VERSION = 1
ALLOWED_MODES = frozenset({"AFK", "HITL"})
REQUIRED_KEYS = frozenset(
    {"ticket_schema", "ticket_id", "execution_mode", "blocked_by"}
)


class ContractError(ValueError):
    """A ticket folder does not satisfy the public ticket contract."""


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


def parse_ticket(path: Path) -> Ticket:
    text = path.read_text(encoding="utf-8")
    data = _parse_front_matter(text, path)
    try:
        schema = int(data["ticket_schema"])
    except (TypeError, ValueError) as error:
        raise ContractError(f"{path}: ticket_schema must be an integer") from error
    if schema != CONTRACT_VERSION:
        raise ContractError(
            f"{path}: unsupported ticket_schema {schema}; expected {CONTRACT_VERSION}"
        )
    ticket_id = str(data["ticket_id"])
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", ticket_id):
        raise ContractError(f"{path}: invalid ticket_id {ticket_id!r}")
    mode = str(data["execution_mode"]).upper()
    if mode not in ALLOWED_MODES:
        raise ContractError(f"{path}: execution_mode must be AFK or HITL")
    blockers = tuple(str(value) for value in data["blocked_by"])
    if len(blockers) != len(set(blockers)):
        raise ContractError(f"{path}: duplicate blocker")
    if ticket_id in blockers:
        raise ContractError(f"{path}: ticket cannot block itself")
    return Ticket(
        ticket_id=ticket_id,
        execution_mode=mode,
        blocked_by=blockers,
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
    if not pending_paths:
        raise ContractError(f"no pending ticket files in {resolved}")
    completed_paths = sorted(
        (path for path in (resolved / "done").glob("*.md") if path.is_file()),
        key=lambda path: path.name,
    )
    paths = [*pending_paths, *completed_paths]
    tickets: dict[str, Ticket] = {}
    completed_ids: set[str] = set()
    for path in paths:
        ticket = parse_ticket(path)
        if ticket.ticket_id in tickets:
            raise ContractError(
                f"duplicate ticket_id {ticket.ticket_id!r}: "
                f"{tickets[ticket.ticket_id].path} and {path}"
            )
        tickets[ticket.ticket_id] = ticket
        if path in completed_paths:
            completed_ids.add(ticket.ticket_id)
    for ticket in tickets.values():
        for blocker in ticket.blocked_by:
            if blocker not in tickets:
                raise ContractError(
                    f"{ticket.path}: missing dependency {blocker!r}"
                )
    _validate_acyclic(tickets)
    order = tuple(sorted(tickets, key=_sort_key))
    return TicketGraph(
        folder=resolved,
        tickets=tickets,
        order=order,
        completed_ids=frozenset(completed_ids),
    )


def migrate_ticket_text(text: str, fallback_id: str | None = None) -> str:
    if text.startswith("---\n"):
        raise ContractError("ticket already uses versioned front matter")

    section_pattern = re.compile(
        r"(?ms)^## (?P<title>[^\n]+)\n+(?P<body>.*?)(?=^## |\Z)"
    )
    sections = {
        match.group("title").strip(): match.group("body").strip()
        for match in section_pattern.finditer(text)
    }
    ticket_id = sections.get("Ticket ID", fallback_id)
    if not ticket_id:
        raise ContractError("legacy ticket has no explicit Ticket ID")
    mode = sections.get("Execution Mode", "AFK").strip().upper()
    if mode not in ALLOWED_MODES:
        raise ContractError("legacy Execution Mode must be AFK or HITL")
    blockers: list[str] = []
    for line in sections.get("Blocked By", "").splitlines():
        if not line.lstrip().startswith("-"):
            continue
        value = line.lstrip()[1:].strip()
        link = re.search(r"\((?:[^)]*/)?([A-Za-z0-9][A-Za-z0-9._-]*)\.md\)", value)
        plain = re.fullmatch(r"[`'\"]?([A-Za-z0-9][A-Za-z0-9._-]*)[`'\"]?", value)
        candidate = link.group(1) if link else plain.group(1) if plain else None
        if candidate:
            numeric_prefix = re.match(r"^(\d+)-", candidate) if link else None
            blockers.append(numeric_prefix.group(1) if numeric_prefix else candidate)

    removable = {"Ticket ID", "Execution Mode", "Blocked By"}
    body = section_pattern.sub(
        lambda match: "" if match.group("title").strip() in removable else match.group(0),
        text,
    ).lstrip()
    blocker_lines = "\n".join(f'  - "{value}"' for value in blockers)
    blocker_field = (
        f"blocked_by:\n{blocker_lines}\n" if blocker_lines else "blocked_by: []\n"
    )
    front_matter = (
        "---\n"
        f"ticket_schema: {CONTRACT_VERSION}\n"
        f'ticket_id: "{ticket_id.strip()}"\n'
        f"execution_mode: {mode}\n"
        f"{blocker_field}"
        "---\n\n"
    )
    return front_matter + body
