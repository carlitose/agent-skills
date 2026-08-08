from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .ticket_contract import ContractError, parse_ticket_markdown


INVENTORY_SCHEMA = 1
INVENTORY_STATES = (
    "open",
    "completed",
    "ready",
    "blocked",
    "human-gated",
    "unknown",
)


def _relative(path: Path, root: Path) -> str:
    relative = path.relative_to(root).as_posix()
    return relative or "."


def _title(body: str, path: Path) -> str:
    match = re.search(r"(?m)^#\s+(.+?)\s*$", body)
    return match.group(1) if match else path.stem


def _find_cycles(items: dict[str, dict[str, Any]]) -> list[list[str]]:
    visiting: list[str] = []
    visited: set[str] = set()
    cycles: list[list[str]] = []

    def visit(ticket_id: str) -> None:
        if ticket_id in visiting:
            start = visiting.index(ticket_id)
            cycles.append([*visiting[start:], ticket_id])
            return
        if ticket_id in visited:
            return
        visiting.append(ticket_id)
        for blocker in items[ticket_id]["blockers"]:
            if blocker in items:
                visit(blocker)
        visiting.pop()
        visited.add(ticket_id)

    for ticket_id in sorted(items):
        visit(ticket_id)
    return cycles


def inventory_tickets(root: Path, *, state: str | None = None) -> dict[str, Any]:
    """Read canonical tickets below *root* without provider or repository access."""

    resolved = root.resolve()
    if not resolved.is_dir():
        raise ContractError(f"ticket inventory root does not exist: {resolved}")

    paths = sorted(
        (path for path in resolved.rglob("*.md") if path.is_file()),
        key=lambda path: path.relative_to(resolved).as_posix(),
    )
    tickets: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    for path in paths:
        relative_path = _relative(path, resolved)
        completed = path.parent.name == "done"
        folder_path = path.parent.parent if completed else path.parent
        folder = _relative(folder_path, resolved)
        try:
            parsed = parse_ticket_markdown(
                path.read_text(encoding="utf-8"), source=relative_path
            )
        except (ContractError, UnicodeDecodeError) as error:
            diagnostics.append(
                {
                    "code": "malformed-ticket",
                    "folder": folder,
                    "message": str(error),
                    "path": relative_path,
                }
            )
            continue
        envelope = parsed.envelope
        tickets.append(
            {
                "folder": folder,
                "id": envelope["ticket_id"],
                "title": _title(parsed.body, path),
                "path": relative_path,
                "disposition": "completed" if completed else "open",
                "mode": envelope["execution_mode"],
                "blockers": list(envelope["blocked_by"]),
                "readiness": "completed" if completed else "ready",
            }
        )
    by_qualified_id: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for item in tickets:
        by_qualified_id.setdefault((item["folder"], item["id"]), []).append(item)
    for (folder, ticket_id), duplicates in sorted(by_qualified_id.items()):
        if len(duplicates) < 2:
            continue
        duplicate_paths = [item["path"] for item in duplicates]
        diagnostics.append(
            {
                "code": "duplicate-id",
                "folder": folder,
                "ticket_id": ticket_id,
                "message": (
                    f"duplicate ticket_id {ticket_id!r}: "
                    + ", ".join(duplicate_paths)
                ),
            }
        )
        for item in duplicates:
            item["readiness"] = "unknown"
    for item in tickets:
        for blocker in item["blockers"]:
            if (item["folder"], blocker) in by_qualified_id:
                continue
            diagnostics.append(
                {
                    "code": "missing-dependency",
                    "folder": item["folder"],
                    "ticket_id": item["id"],
                    "dependency_id": blocker,
                    "message": (
                        f"ticket {item['id']!r} has missing dependency {blocker!r}"
                    ),
                }
            )
            item["readiness"] = "unknown"
    folders = sorted({item["folder"] for item in tickets})
    for folder in folders:
        unique = {
            ticket_id: matches[0]
            for (item_folder, ticket_id), matches in by_qualified_id.items()
            if item_folder == folder and len(matches) == 1
        }
        for cycle in _find_cycles(unique):
            diagnostics.append(
                {
                    "code": "cycle",
                    "folder": folder,
                    "cycle": cycle,
                    "message": "dependency cycle: " + " -> ".join(cycle),
                }
            )
            for ticket_id in cycle[:-1]:
                unique[ticket_id]["readiness"] = "unknown"
    changed = True
    while changed:
        changed = False
        for item in tickets:
            if item["disposition"] == "completed" or item["readiness"] == "unknown":
                continue
            dependencies = [
                by_qualified_id.get((item["folder"], blocker), [])
                for blocker in item["blockers"]
            ]
            if any(len(matches) != 1 for matches in dependencies) or any(
                matches[0]["readiness"] == "unknown"
                for matches in dependencies
            ):
                item["readiness"] = "unknown"
                changed = True
    for item in tickets:
        if item["disposition"] == "completed" or item["readiness"] == "unknown":
            continue
        dependencies = [
            by_qualified_id[(item["folder"], blocker)][0]
            for blocker in item["blockers"]
        ]
        if any(dependency["disposition"] == "open" for dependency in dependencies):
            item["readiness"] = "blocked"
        elif item["mode"] == "HITL":
            item["readiness"] = "human-gated"
        else:
            item["readiness"] = "ready"
    diagnostics.sort(
        key=lambda item: (
            item.get("folder", ""),
            item.get("path", ""),
            item["code"],
            item.get("ticket_id", ""),
        )
    )
    visible = (
        tickets
        if state is None
        else [
            item
            for item in tickets
            if item["disposition"] == state or item["readiness"] == state
        ]
    )
    return {
        "schema": INVENTORY_SCHEMA,
        "root": str(resolved),
        "state": state or "all",
        "tickets": visible,
        "diagnostics": diagnostics,
    }


def _cell(value: object) -> str:
    return " ".join(str(value).split())


def render_ticket_inventory(result: dict[str, Any]) -> str:
    """Render the versioned inventory as deterministic tab-separated human text."""

    lines = [
        f"Ticket inventory: {result['root']} (state={result['state']})",
        "FOLDER\tID\tDISPOSITION\tMODE\tREADINESS\tBLOCKERS\tPATH\tTITLE",
    ]
    lines.extend(
        "\t".join(
            (
                _cell(item["folder"]),
                _cell(item["id"]),
                item["disposition"],
                item["mode"],
                item["readiness"],
                ",".join(item["blockers"]) or "-",
                _cell(item["path"]),
                _cell(item["title"]),
            )
        )
        for item in result["tickets"]
    )
    if result["diagnostics"]:
        lines.append("DIAGNOSTICS")
        lines.extend(
            f"{item['code']}\t{_cell(item['message'])}"
            for item in result["diagnostics"]
        )
    return "\n".join(lines) + "\n"
