from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from .git_ops import (
    GitError,
    assert_ticket_folder_at_ref,
    common_git_dir,
    repository_root,
    run_git,
)
from .ticket_contract import (
    ContractError,
    Ticket,
    TicketGraph,
    parse_ticket_markdown,
    read_ticket_text,
    serialize_ticket_markdown,
    validate_ticket_graph,
)


SNAPSHOT_SCHEMA = 2


class TicketSourceError(GitError):
    """Ticket input cannot be safely classified or snapshotted."""


@dataclass(frozen=True)
class TicketSource:
    repository: Path
    folder: Path
    source_mode: str
    graph: TicketGraph
    folder_identity: dict[str, int]
    manifest: dict[str, Any]
    manifest_digest: str


def _canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _digest(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _inside(path: Path, parent: Path, *, description: str) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(parent.resolve())
    except ValueError as error:
        raise TicketSourceError(f"{description} escapes its accepted folder") from error
    return resolved


def _safe_ticket_paths(folder: Path) -> tuple[Path, ...]:
    if not folder.is_dir():
        raise ContractError(f"ticket folder does not exist: {folder}")
    if folder.is_symlink():
        raise TicketSourceError("ticket folder cannot be a symlink")
    pending = sorted(folder.glob("*.md"), key=lambda path: path.name)
    disposed: list[Path] = []
    for directory in ("hold", "canceled", "done"):
        disposition_folder = folder / directory
        if disposition_folder.is_symlink():
            raise TicketSourceError(
                f"ticket {directory} folder cannot be a symlink"
            )
        if disposition_folder.is_dir():
            disposed.extend(
                sorted(disposition_folder.glob("*.md"), key=lambda path: path.name)
            )
    paths = (*pending, *disposed)
    if not paths:
        raise ContractError(f"no ticket files in {folder}")
    for path in paths:
        if path.is_symlink():
            raise TicketSourceError(f"ticket source cannot be a symlink: {path}")
        if not path.is_file():
            raise TicketSourceError(f"ticket source is not a regular file: {path}")
        _inside(path, folder, description="ticket source")
    return paths


def _git_probe(repo: Path, *args: str) -> int:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        check=False,
    ).returncode


def _classify(
    repo: Path,
    folder: Path,
    graph: TicketGraph,
    *,
    base_ref: str,
) -> tuple[str, str]:
    base_sha = run_git(repo, "rev-parse", "--verify", f"{base_ref}^{{commit}}")
    relative_paths = [
        ticket.path.relative_to(repo).as_posix()
        for ticket in graph.tickets.values()
    ]
    tracked = [
        _git_probe(repo, "cat-file", "-e", f"{base_sha}:{path}") == 0
        for path in relative_paths
    ]
    ignored = [
        _git_probe(repo, "check-ignore", "-q", "--", path) == 0
        for path in relative_paths
    ]
    if all(tracked):
        assert_ticket_folder_at_ref(repo, folder, base_ref=base_sha)
        return "tracked", base_sha
    if any(tracked) and any(ignored):
        raise TicketSourceError("ticket input mixes tracked and ignored sources")
    if any(tracked):
        raise TicketSourceError(
            "ticket input mixes tracked and untracked non-ignored sources"
        )
    if all(ignored):
        return "ignored", base_sha
    raise TicketSourceError("ticket input is untracked and not ignored")


def inspect_ticket_source(
    repo: Path,
    folder: Path,
    *,
    base_ref: str = "HEAD",
) -> TicketSource:
    root = repository_root(repo)
    if folder.is_symlink():
        raise TicketSourceError("ticket folder cannot be a symlink")
    resolved_folder = folder.resolve()
    try:
        folder_relative = resolved_folder.relative_to(root)
    except ValueError as error:
        raise TicketSourceError("ticket folder must be inside the repository") from error
    if not folder_relative.parts:
        raise TicketSourceError("repository root cannot be used as the ticket folder")
    paths = _safe_ticket_paths(resolved_folder)
    ticket_texts = {
        path.resolve(): read_ticket_text(path) for path in paths
    }
    graph = validate_ticket_graph(
        resolved_folder,
        ticket_texts,
        disposition_paths={
            path: {
                "hold": "on-hold",
                "canceled": "canceled",
                "done": "completed",
            }.get(path.parent.name, "open")
            for path in paths
        },
    )
    source_mode, base_sha = _classify(
        root,
        resolved_folder,
        graph,
        base_ref=base_ref,
    )
    folder_stat = resolved_folder.stat(follow_symlinks=False)
    folder_identity = {
        "device": folder_stat.st_dev,
        "inode": folder_stat.st_ino,
    }
    items: list[dict[str, Any]] = []
    for ticket_id in graph.order:
        ticket = graph.tickets[ticket_id]
        text = ticket_texts[ticket.path]
        parsed = parse_ticket_markdown(text, source=str(ticket.path))
        items.append(
            {
                "relative_path": ticket.path.relative_to(resolved_folder).as_posix(),
                "envelope": parsed.envelope,
                "body": parsed.body,
                "content_digest": ticket.digest,
                "disposition": graph.dispositions[ticket_id],
            }
        )
    manifest = {
        "snapshot_schema": SNAPSHOT_SCHEMA,
        "source_mode": source_mode,
        "repository_relative_folder": folder_relative.as_posix(),
        "source_folder_identity": folder_identity,
        "selected_base_sha": base_sha,
        "tickets": items,
    }
    return TicketSource(
        repository=root,
        folder=resolved_folder,
        source_mode=source_mode,
        graph=graph,
        folder_identity=folder_identity,
        manifest=manifest,
        manifest_digest=_digest(manifest),
    )


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, raw_temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(raw_temporary)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        if os.name != "nt":
            directory = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
    finally:
        temporary.unlink(missing_ok=True)


def persist_ticket_snapshot(run_dir: Path, source: TicketSource) -> Path:
    path = run_dir / "ticket-source" / "manifest.json"
    managed_runs = (
        common_git_dir(source.repository) / "ticket-autopilot" / "runs"
    ).resolve()
    try:
        path.resolve(strict=False).relative_to(managed_runs)
    except ValueError as error:
        raise TicketSourceError(
            "managed ticket snapshot path escapes Git common state"
        ) from error
    document = {
        "manifest": source.manifest,
        "manifest_digest": source.manifest_digest,
    }
    content = _canonical_bytes(document) + b"\n"
    if path.exists():
        if path.read_bytes() != content:
            raise TicketSourceError("managed ticket snapshot is contradictory")
        return path
    _atomic_write(path, content)
    return path


def _safe_relative_path(value: Any) -> PurePosixPath:
    if not isinstance(value, str) or not value:
        raise TicketSourceError("snapshot ticket relative_path must be text")
    relative = PurePosixPath(value)
    if relative.is_absolute() or ".." in relative.parts or "." in relative.parts:
        raise TicketSourceError("snapshot ticket relative_path escapes its folder")
    if len(relative.parts) not in {1, 2} or (
        len(relative.parts) == 2
        and relative.parts[0] not in {"hold", "canceled", "done"}
    ):
        raise TicketSourceError("snapshot ticket relative_path is outside ticket layout")
    return relative


def _safe_repository_relative(value: Any) -> PurePosixPath:
    if not isinstance(value, str) or not value:
        raise TicketSourceError("snapshot repository-relative folder must be text")
    relative = PurePosixPath(value)
    if relative.is_absolute() or ".." in relative.parts or "." in relative.parts:
        raise TicketSourceError("snapshot ticket folder escapes repository")
    return relative


def load_ticket_snapshot(path: Path, repo: Path) -> TicketSource:
    root = repository_root(repo)
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise TicketSourceError(f"managed ticket snapshot is unreadable: {path}") from error
    if not isinstance(document, dict) or set(document) != {
        "manifest",
        "manifest_digest",
    }:
        raise TicketSourceError("managed ticket snapshot shape is invalid")
    manifest = document["manifest"]
    digest = document["manifest_digest"]
    if (
        not isinstance(manifest, dict)
        or not isinstance(digest, str)
        or _digest(manifest) != digest
    ):
        raise TicketSourceError("managed ticket snapshot digest is invalid")
    if set(manifest) != {
        "snapshot_schema",
        "source_mode",
        "repository_relative_folder",
        "source_folder_identity",
        "selected_base_sha",
        "tickets",
    }:
        raise TicketSourceError("managed ticket manifest shape is invalid")
    snapshot_schema = manifest["snapshot_schema"]
    if type(snapshot_schema) is not int or snapshot_schema not in {1, SNAPSHOT_SCHEMA}:
        raise TicketSourceError("managed ticket snapshot schema is unsupported")
    if (
        not isinstance(manifest["selected_base_sha"], str)
        or not manifest["selected_base_sha"]
    ):
        raise TicketSourceError("managed ticket snapshot base SHA is invalid")
    folder_identity = manifest["source_folder_identity"]
    if (
        not isinstance(folder_identity, dict)
        or set(folder_identity) != {"device", "inode"}
        or any(type(folder_identity[field]) is not int for field in folder_identity)
        or any(folder_identity[field] < 0 for field in folder_identity)
    ):
        raise TicketSourceError("managed ticket source folder identity is invalid")
    source_mode = manifest["source_mode"]
    if source_mode not in {"tracked", "ignored"}:
        raise TicketSourceError("managed ticket source mode is invalid")
    folder_relative = _safe_repository_relative(
        manifest["repository_relative_folder"]
    )
    folder = root.joinpath(*folder_relative.parts)
    items = manifest["tickets"]
    if not isinstance(items, list) or not items:
        raise TicketSourceError("managed ticket snapshot has no tickets")
    texts: dict[Path, str] = {}
    digests: dict[Path, str] = {}
    source_paths: dict[Path, Path] = {}
    disposition_paths: dict[Path, str] = {}
    seen_paths: set[PurePosixPath] = set()
    for item in items:
        expected_item_fields = {
            "relative_path",
            "envelope",
            "body",
            "content_digest",
            "completed" if snapshot_schema == 1 else "disposition",
        }
        if not isinstance(item, dict) or set(item) != expected_item_fields:
            raise TicketSourceError("managed snapshot ticket shape is invalid")
        relative = _safe_relative_path(item["relative_path"])
        if relative in seen_paths:
            raise TicketSourceError("managed snapshot contains duplicate ticket paths")
        seen_paths.add(relative)
        target = path.parent / "normalized" / Path(*relative.parts)
        content_digest = item["content_digest"]
        if (
            not isinstance(content_digest, str)
            or len(content_digest) != 64
            or any(character not in "0123456789abcdef" for character in content_digest)
        ):
            raise TicketSourceError("managed snapshot ticket digest is invalid")
        if snapshot_schema == 1:
            if not isinstance(item["completed"], bool):
                raise TicketSourceError("managed snapshot completed flag is invalid")
            disposition = "completed" if item["completed"] else "open"
        else:
            disposition = item["disposition"]
            if disposition not in {"open", "on-hold", "canceled", "completed"}:
                raise TicketSourceError("managed snapshot disposition is invalid")
        try:
            texts[target] = serialize_ticket_markdown(item["envelope"], item["body"])
        except ContractError as error:
            raise TicketSourceError(str(error)) from error
        digests[target.resolve()] = content_digest
        source_paths[target.resolve()] = folder.joinpath(*relative.parts)
        disposition_paths[target] = disposition
    canonical = validate_ticket_graph(
        folder, texts, disposition_paths=disposition_paths
    )
    tickets = {
        ticket_id: Ticket(
            ticket_id=ticket.ticket_id,
            execution_mode=ticket.execution_mode,
            blocked_by=ticket.blocked_by,
            path=source_paths[ticket.path],
            digest=digests[ticket.path],
        )
        for ticket_id, ticket in canonical.tickets.items()
    }
    graph = TicketGraph(
        folder=folder,
        tickets=tickets,
        order=canonical.order,
        completed_ids=canonical.completed_ids,
        dispositions=dict(canonical.dispositions),
    )
    return TicketSource(
        repository=root,
        folder=folder,
        source_mode=source_mode,
        graph=graph,
        folder_identity=dict(folder_identity),
        manifest=manifest,
        manifest_digest=digest,
    )
