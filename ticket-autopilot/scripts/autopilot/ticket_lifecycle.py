from __future__ import annotations

import hashlib
import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from .file_lock import acquire_file_lock, release_file_lock
from .ticket_contract import (
    ContractError,
    parse_ticket_markdown,
    read_ticket_text,
    ticket_source_digest,
)


LIFECYCLE_RECEIPT_SCHEMA = 1
SOURCE_DISPOSITIONS = ("open", "on-hold", "canceled", "completed")
_DIRECTORIES = {
    "open": None,
    "on-hold": "hold",
    "canceled": "canceled",
    "completed": "done",
}


class LifecycleError(RuntimeError):
    """A durable ticket lifecycle transition cannot be proven safe."""


def _canonical_bytes(value: dict[str, Any]) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _digest(path: Path) -> str:
    return ticket_source_digest(path)


def _fsync_directory(path: Path) -> None:
    if os.name == "nt":
        return
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _atomic_write(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, raw_temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(raw_temporary)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(_canonical_bytes(document) + b"\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        _fsync_directory(path.parent)
    finally:
        temporary.unlink(missing_ok=True)


@contextmanager
def _folder_lock(state_dir: Path) -> Iterator[None]:
    """Exclusive lock over the lifecycle folder, on every platform.

    Blocking, unlike the ledger's lock: a lifecycle transition waits its turn rather than
    failing immediately. On Windows that wait is bounded at roughly ten seconds by
    `msvcrt`, after which `OSError` means the folder really is held by someone else — which
    is what the error below now says, and did not when `import fcntl` raised `ImportError`
    on a lock that had never been taken.
    """
    state_dir.mkdir(parents=True, exist_ok=True)
    lock_path = state_dir / "lifecycle.lock"
    with lock_path.open("a+", encoding="ascii") as handle:
        try:
            acquire_file_lock(handle, blocking=True)
        except OSError as error:
            raise LifecycleError(f"ticket lifecycle folder is locked: {state_dir}") from error
        try:
            yield
        finally:
            release_file_lock(handle)


def _accepted_folder(folder: Path) -> Path:
    if folder.is_symlink() or not folder.is_dir():
        raise LifecycleError("ticket folder must be a real directory")
    resolved = folder.resolve()
    for directory in ("hold", "canceled", "done"):
        child = resolved / directory
        if child.is_symlink():
            raise LifecycleError(f"ticket {directory} folder cannot be a symlink")
    return resolved


def _ticket_sources(folder: Path, ticket_id: str) -> list[tuple[Path, str]]:
    matches: list[tuple[Path, str]] = []
    for disposition in SOURCE_DISPOSITIONS:
        directory = _DIRECTORIES[disposition]
        parent = folder if directory is None else folder / directory
        if not parent.is_dir():
            continue
        for path in sorted(parent.glob("*.md"), key=lambda item: item.name):
            if path.is_symlink() or not path.is_file():
                raise LifecycleError(f"ticket source is not a regular file: {path}")
            try:
                parsed = parse_ticket_markdown(
                    read_ticket_text(path), source=str(path)
                )
            except (ContractError, UnicodeDecodeError) as error:
                raise LifecycleError(str(error)) from error
            if parsed.envelope["ticket_id"] == ticket_id:
                matches.append((path, disposition))
    if not matches:
        raise LifecycleError(f"unknown ticket {ticket_id!r}")
    if len(matches) != 1:
        raise LifecycleError(f"ticket {ticket_id!r} has contradictory source locations")
    return matches


def _destination(folder: Path, source: Path, disposition: str) -> Path:
    directory = _DIRECTORIES[disposition]
    parent = folder if directory is None else folder / directory
    if parent.is_symlink():
        raise LifecycleError("ticket disposition destination cannot be a symlink")
    parent.mkdir(parents=True, exist_ok=True)
    destination = parent / source.name
    try:
        destination.resolve(strict=False).relative_to(folder)
    except ValueError as error:
        raise LifecycleError("ticket disposition destination escapes its folder") from error
    return destination


def _receipt_path(folder: Path, value: Any) -> Path:
    if not isinstance(value, str) or not value:
        raise LifecycleError("lifecycle receipt path is invalid")
    candidate = (folder / value).resolve(strict=False)
    try:
        candidate.relative_to(folder)
    except ValueError as error:
        raise LifecycleError("lifecycle receipt path escapes its folder") from error
    return candidate


def _move_no_replace(source: Path, destination: Path) -> None:
    try:
        os.link(source, destination, follow_symlinks=False)
    except FileExistsError as error:
        raise LifecycleError("ticket disposition destination already exists") from error
    try:
        source.unlink()
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    _fsync_directory(source.parent)
    if destination.parent != source.parent:
        _fsync_directory(destination.parent)


def _request(
    ticket_id: str,
    disposition: str,
    *,
    actor: str,
    reason: str,
    authority_ref: str,
    authority_gate_id: str | None,
    expected_digest: str,
) -> dict[str, Any]:
    if disposition not in {"open", "on-hold", "canceled"}:
        raise LifecycleError("lifecycle target disposition is invalid")
    values = {
        "ticket_id": ticket_id,
        "to_disposition": disposition,
        "actor": actor,
        "reason": reason,
        "authority_ref": authority_ref,
        "expected_digest": expected_digest,
    }
    if any(not isinstance(value, str) or not value.strip() for value in values.values()):
        raise LifecycleError("lifecycle transition requires identity, reason, authority, and digest")
    if len(expected_digest) != 64 or any(
        character not in "0123456789abcdef" for character in expected_digest
    ):
        raise LifecycleError("lifecycle transition expected digest is invalid")
    if disposition == "open":
        if not isinstance(authority_gate_id, str) or not authority_gate_id:
            raise LifecycleError("ticket reopen requires a passed human gate")
    elif authority_gate_id is not None:
        raise LifecycleError("hold and cancel cannot consume a reopen gate")
    values["authority_gate_id"] = authority_gate_id
    return values


def assert_ticket_source_state(
    folder: Path,
    ticket_id: str,
    disposition: str,
    expected_digest: str,
) -> None:
    """Reject unreceipted source disposition or content drift."""

    accepted = _accepted_folder(folder)
    source, observed = _ticket_sources(accepted, ticket_id)[0]
    if observed != disposition:
        raise LifecycleError(
            f"ticket {ticket_id!r} source disposition drift: "
            f"expected {disposition}, observed {observed}"
        )
    if _digest(source) != expected_digest:
        raise LifecycleError(
            f"ticket {ticket_id!r} content differs from managed snapshot"
        )


def transition_ticket_source(
    folder: Path,
    state_dir: Path,
    ticket_id: str,
    disposition: str,
    *,
    actor: str,
    reason: str,
    authority_ref: str,
    expected_digest: str,
    authority_gate_id: str | None = None,
) -> dict[str, Any]:
    """Apply or replay one receipted, no-clobber source disposition transition."""

    request = _request(
        ticket_id,
        disposition,
        actor=actor,
        reason=reason,
        authority_ref=authority_ref,
        authority_gate_id=authority_gate_id,
        expected_digest=expected_digest,
    )
    transition_id = hashlib.sha256(_canonical_bytes(request)).hexdigest()
    journal_path = state_dir / f"{transition_id}.json"
    with _folder_lock(state_dir):
        existing: dict[str, Any] | None = None
        if journal_path.exists():
            try:
                existing = json.loads(journal_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as error:
                raise LifecycleError("lifecycle transition journal is unreadable") from error
            if any(existing.get(key) != value for key, value in request.items()):
                raise LifecycleError("lifecycle transition journal is contradictory")
            if existing.get("transition_id") != transition_id:
                raise LifecycleError("lifecycle transition identity is contradictory")
            if existing.get("state") not in {"intent", "applied"}:
                raise LifecycleError("lifecycle transition journal state is invalid")

        accepted = _accepted_folder(folder)
        if existing is not None and existing["state"] == "applied":
            original = _receipt_path(accepted, existing.get("source_relative_path"))
            target = _receipt_path(
                accepted, existing.get("destination_relative_path")
            )
            if original.exists() or not target.is_file() or _digest(target) != expected_digest:
                raise LifecycleError("applied lifecycle receipt has source drift")
            return existing
        matches = _ticket_sources(accepted, ticket_id)
        source, from_disposition = matches[0]
        if _digest(source) != expected_digest:
            raise LifecycleError("ticket source digest differs from managed snapshot")
        if from_disposition == "completed":
            raise LifecycleError("completed tickets cannot change administrative disposition")
        if from_disposition == disposition and existing is None:
            raise LifecycleError("ticket disposition lacks a matching receipt")
        destination = _destination(accepted, source, disposition)
        receipt = {
            "schema": LIFECYCLE_RECEIPT_SCHEMA,
            "transition_id": transition_id,
            **request,
            "from_disposition": (
                existing["from_disposition"] if existing else from_disposition
            ),
            "source_relative_path": (
                existing["source_relative_path"]
                if existing
                else source.relative_to(accepted).as_posix()
            ),
            "destination_relative_path": (
                existing["destination_relative_path"]
                if existing
                else destination.relative_to(accepted).as_posix()
            ),
            "state": "intent",
        }
        if existing is None:
            _atomic_write(journal_path, receipt)

        original = _receipt_path(accepted, receipt["source_relative_path"])
        target = _receipt_path(accepted, receipt["destination_relative_path"])
        original_exists = original.is_file()
        target_exists = target.is_file()
        if original_exists and target_exists:
            if _digest(original) != expected_digest or _digest(target) != expected_digest:
                raise LifecycleError("ticket source and destination are contradictory")
            original.unlink()
            _fsync_directory(original.parent)
        elif original_exists:
            if _digest(original) != expected_digest:
                raise LifecycleError("ticket source digest differs from managed snapshot")
            _move_no_replace(original, target)
        elif not target_exists or _digest(target) != expected_digest:
            raise LifecycleError("ticket source move is missing or contradictory")

        receipt["state"] = "applied"
        _atomic_write(journal_path, receipt)
        return receipt
