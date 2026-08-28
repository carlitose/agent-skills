#!/usr/bin/env python3
"""Validate one emitted ticket batch, then synchronize its project wiki once.

This is the post-batch composition boundary owned by ``to-tickets``.  Ticket parsing,
dependency inventory, Artifact Graph validation, and wiki compilation remain owned by their
canonical modules; this adapter fixes their order and returns one durable-shaped report.

Usage:
    python3 finalize_batch.py <project-root> <ticket-folder> [<ticket-path> ...]
        [--wiki-root <path>]... [--autopilot-root <path>] [--attempt <number>]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence


SKILL_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = SKILL_ROOT.parent
AUTOPILOT_ROOT = SKILLS_ROOT / "ticket-autopilot"
AUTOPILOT_SCRIPTS = AUTOPILOT_ROOT / "scripts"
LLM_WIKI_SCRIPTS = SKILLS_ROOT / "llm-wiki" / "scripts"
for scripts_root in (AUTOPILOT_SCRIPTS, LLM_WIKI_SCRIPTS):
    if str(scripts_root) not in sys.path:
        sys.path.insert(0, str(scripts_root))

from autopilot.artifact_audit import audit_artifacts  # noqa: E402
from autopilot.ticket_contract import (  # noqa: E402
    ContractError,
    parse_ticket,
    parse_ticket_folder,
)
from autopilot.ticket_inventory import inventory_tickets  # noqa: E402
from sync_project import sync_project  # noqa: E402


CONTRACT_VERSION = "ticket-batch-finalize-v1"
SyncOperation = Callable[..., Mapping[str, Any]]


class BatchValidationError(ValueError):
    """The caller has not supplied one complete, validated post-emission batch."""


def _canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _directory(path: Path, *, label: str) -> Path:
    try:
        resolved = path.expanduser().resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise BatchValidationError(f"{label} does not resolve: {path}: {error}") from error
    if not resolved.is_dir():
        raise BatchValidationError(f"{label} is not a directory: {resolved}")
    return resolved


def _batch_paths(
    project_root: Path,
    ticket_folder: Path,
    emitted_ticket_paths: Sequence[Path],
) -> list[Path]:
    if isinstance(emitted_ticket_paths, (str, bytes, os.PathLike)):
        raise BatchValidationError("emitted_ticket_paths must be a sequence of paths")
    paths: list[Path] = []
    for raw in emitted_ticket_paths:
        if not isinstance(raw, (str, os.PathLike)):
            raise BatchValidationError("each emitted ticket path must be a filesystem path")
        candidate = Path(raw)
        if not candidate.is_absolute():
            candidate = project_root / candidate
        try:
            resolved = candidate.expanduser().resolve(strict=True)
        except (OSError, RuntimeError) as error:
            raise BatchValidationError(
                f"emitted ticket does not resolve: {candidate}: {error}"
            ) from error
        if (
            resolved.parent != ticket_folder
            or resolved.suffix != ".md"
            or not resolved.is_file()
        ):
            raise BatchValidationError(
                f"emitted ticket must be a Markdown file directly in {ticket_folder}: {resolved}"
            )
        paths.append(resolved)
    if len(paths) != len(set(paths)):
        raise BatchValidationError("emitted ticket paths must be unique")
    normalized = sorted(paths, key=lambda path: path.name)
    folder_tickets = sorted(
        (path.resolve() for path in ticket_folder.glob("*.md") if path.is_file()),
        key=lambda path: path.name,
    )
    if normalized != folder_tickets:
        missing = [str(path) for path in folder_tickets if path not in normalized]
        raise BatchValidationError(
            "emitted ticket paths must name the complete top-level batch"
            + (": missing " + ", ".join(missing) if missing else "")
        )
    return normalized


def _batch_identity(
    project_root: Path, ticket_folder: Path, ticket_paths: Sequence[Path]
) -> tuple[str, list[dict[str, str]]]:
    tickets = [parse_ticket(path) for path in ticket_paths]
    normalized = [
        {
            "ticket_id": ticket.ticket_id,
            "path": ticket.path.relative_to(project_root).as_posix(),
            "sha256": ticket.digest,
        }
        for ticket in sorted(tickets, key=lambda item: item.path.as_posix())
    ]
    identity = {
        "contract_version": CONTRACT_VERSION,
        "ticket_folder": ticket_folder.relative_to(project_root).as_posix(),
        "tickets": normalized,
    }
    return hashlib.sha256(_canonical_bytes(identity)).hexdigest(), normalized


def _validate_batch_graph(
    project_root: Path, ticket_folder: Path, ticket_paths: Sequence[Path]
) -> None:
    if ticket_paths:
        try:
            graph = parse_ticket_folder(ticket_folder)
        except ContractError as error:
            raise BatchValidationError(str(error)) from error
        graph_paths = {ticket.path for ticket in graph.tickets.values()}
        missing = [path for path in ticket_paths if path not in graph_paths]
        if missing:
            raise BatchValidationError(
                "emitted ticket is absent from the canonical folder graph: "
                + ", ".join(str(path) for path in missing)
            )

    report = audit_artifacts(project_root)
    relative_paths = {
        path.relative_to(project_root).as_posix() for path in ticket_paths
    }
    node_paths = {node["path"] for node in report["nodes"]}
    missing_nodes = sorted(relative_paths - node_paths)
    if missing_nodes:
        raise BatchValidationError(
            "emitted ticket has no strict Artifact Graph node: "
            + ", ".join(missing_nodes)
        )
    invalid = [
        error
        for error in report["errors"]
        if error["path"] in relative_paths
        or bool(relative_paths.intersection(error.get("paths", [])))
    ]
    if invalid:
        detail = "; ".join(
            f"{item['path']}: {item['code']}: {item['message']}" for item in invalid
        )
        raise BatchValidationError(f"emitted ticket Artifact Graph is invalid: {detail}")


def _batch_inventory(
    project_root: Path,
    ticket_folder: Path,
    normalized_tickets: Sequence[Mapping[str, str]],
) -> dict[str, Any]:
    inventory = inventory_tickets(ticket_folder)
    batch_paths = {ticket["path"] for ticket in normalized_tickets}
    tickets = [
        item
        for item in inventory["tickets"]
        if (ticket_folder / item["path"]).relative_to(project_root).as_posix()
        in batch_paths
    ]
    return {
        "ready_frontier": sorted(
            item["id"] for item in tickets if item["readiness"] == "ready"
        ),
        "blocked_tickets": [
            {
                "ticket_id": item["id"],
                "readiness": item["readiness"],
                "causes": item["readiness_causes"],
            }
            for item in tickets
            if item["readiness"] in {"blocked", "not-schedulable", "unknown"}
        ],
        "hitl_decisions": [
            {
                "ticket_id": item["id"],
                "state": item["readiness"],
            }
            for item in tickets
            if item["mode"] == "HITL"
        ],
    }


def finalize_ticket_batch(
    project_root: Path,
    ticket_folder: Path,
    emitted_ticket_paths: Sequence[Path],
    *,
    wiki_roots: Sequence[Path] = (),
    autopilot_root: Path | None = None,
    attempt: int = 1,
    sync_operation: SyncOperation = sync_project,
) -> dict[str, Any]:
    """Validate a complete ticket batch and invoke the project wiki sync exactly once.

    An empty batch is valid and still gets one normalized sync result.  This keeps the
    composition point deterministic for callers that conclude a spec emits no work.
    """

    project_input = Path(project_root).expanduser()
    lexical_project = Path(os.path.abspath(project_input))
    project = _directory(project_input, label="project_root")
    folder_input = Path(ticket_folder)
    if not folder_input.is_absolute():
        folder_input = project / folder_input
    folder = _directory(folder_input, label="ticket_folder")
    lexical_folder = Path(os.path.abspath(folder_input.expanduser()))
    relative_folder = next(
        (
            lexical_folder.relative_to(root)
            for root in (lexical_project, project)
            if lexical_folder.is_relative_to(root)
        ),
        None,
    )
    if relative_folder is None or project / relative_folder != folder:
        raise BatchValidationError(
            f"ticket_folder may not resolve through a symlink: {lexical_folder}"
        )
    managed_tickets = (project / "docs" / "tickets").resolve()
    if not folder.is_relative_to(managed_tickets):
        raise BatchValidationError(
            f"ticket_folder must be below {managed_tickets}: {folder}"
        )
    paths = _batch_paths(project, folder, emitted_ticket_paths)
    _validate_batch_graph(project, folder, paths)
    batch_id, normalized_tickets = _batch_identity(project, folder, paths)
    frontier = _batch_inventory(project, folder, normalized_tickets)

    wiki_sync = dict(
        sync_operation(
            project,
            wiki_roots,
            origin_kind="ticket-batch",
            origin_id=batch_id,
            triggers=("post-ticket-batch",),
            attempt=attempt,
            autopilot_root=autopilot_root or AUTOPILOT_ROOT,
        )
    )
    return {
        "contract_version": CONTRACT_VERSION,
        "project_root": str(project),
        "ticket_folder": folder.relative_to(project).as_posix(),
        "ticket_paths": [ticket["path"] for ticket in normalized_tickets],
        "batch_id": batch_id,
        **frontier,
        "wiki_sync": wiki_sync,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("ticket_folder", type=Path)
    parser.add_argument("ticket_paths", nargs="*", type=Path)
    parser.add_argument("--wiki-root", action="append", type=Path, default=[])
    parser.add_argument("--autopilot-root", type=Path)
    parser.add_argument("--attempt", type=int, default=1)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        report = finalize_ticket_batch(
            arguments.project_root,
            arguments.ticket_folder,
            arguments.ticket_paths,
            wiki_roots=arguments.wiki_root,
            autopilot_root=arguments.autopilot_root,
            attempt=arguments.attempt,
        )
    except BatchValidationError as error:
        print(
            json.dumps(
                {
                    "contract_version": CONTRACT_VERSION,
                    "error": {"type": type(error).__name__, "message": str(error)},
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    return 1 if report["wiki_sync"]["status"] == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
