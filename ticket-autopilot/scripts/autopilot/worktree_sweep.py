"""Plan or apply cleanup without losing runner-owned or live temporary work."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Iterator, Mapping

from .file_lock import acquire_file_lock, release_file_lock
from .git_ops import GitError, common_git_dir, repository_root, run_git
from .repository_authority import canonical_bytes
from .worktree_gc import (
    _parse_worktree_inventory,
    _validate_envelope,
    _write_envelope,
    apply_worktree_gc,
    plan_worktree_gc,
)


SWEEP_CONTRACT = "worktree-sweep-v1"
LEASE_CONTRACT = "wiki-temporary-worktree-lease-v1"
ENTRY_RECEIPT_CONTRACT = "worktree-sweep-entry-v1"
COMPLETION_RECEIPT_CONTRACT = "worktree-sweep-completion-v1"
_WIKI_PREFIXES = ("ticket-wiki-source-", "ticket-wiki-delivery-")


class WorktreeSweepError(ValueError):
    """A sweep input or temporary-worktree claim was unsafe or contradictory."""


def _digest(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _strict_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise WorktreeSweepError(f"{label} must be a non-empty string")
    return value.strip()


def _canonical(path: Path, label: str, *, must_exist: bool = True) -> Path:
    if not path.is_absolute():
        raise WorktreeSweepError(f"{label} must be absolute")
    resolved = path.resolve(strict=must_exist)
    if Path(os.path.normpath(str(path))) != path or resolved != path:
        raise WorktreeSweepError(f"{label} must be canonical")
    return resolved


def _lease_key(path: Path) -> str:
    spelling = os.path.normcase(os.path.normpath(str(path))).encode("utf-8")
    return hashlib.sha256(spelling).hexdigest()


def _lease_paths(repository: Path, path: Path) -> tuple[Path, Path]:
    root = common_git_dir(repository) / "ticket-autopilot" / "wiki-temporary-worktrees"
    key = _lease_key(path)
    return root / f"{key}.json", root / f"{key}.lock"


def _validate_lease(payload: object, *, repository: Path, path: Path) -> dict[str, Any]:
    fields = {
        "schema", "contract_version", "repository_root", "git_common_dir",
        "worktree_path", "run_id", "ticket_id", "ledger_path", "kind",
    }
    if not isinstance(payload, dict) or set(payload) != fields:
        raise WorktreeSweepError("wiki temporary lease fields are invalid")
    if payload.get("schema") != 1 or payload.get("contract_version") != LEASE_CONTRACT:
        raise WorktreeSweepError("wiki temporary lease contract is invalid")
    root = repository_root(repository)
    if payload.get("repository_root") != str(root):
        raise WorktreeSweepError("wiki temporary lease repository differs")
    if payload.get("git_common_dir") != str(common_git_dir(root)):
        raise WorktreeSweepError("wiki temporary lease Git common directory differs")
    if payload.get("worktree_path") != str(path):
        raise WorktreeSweepError("wiki temporary lease path differs")
    _strict_text(payload.get("run_id"), "wiki temporary lease run ID")
    _strict_text(payload.get("ticket_id"), "wiki temporary lease ticket ID")
    ledger = Path(_strict_text(payload.get("ledger_path"), "wiki temporary lease ledger"))
    if not ledger.is_absolute():
        raise WorktreeSweepError("wiki temporary lease ledger must be absolute")
    if payload.get("kind") not in {"source", "delivery"}:
        raise WorktreeSweepError("wiki temporary lease kind is invalid")
    return dict(payload)


@contextmanager
def wiki_temporary_lease(
    repository: Path,
    worktree: Path,
    *,
    run_id: str,
    ticket_id: str,
    ledger_path: Path,
    kind: str,
    observer: Callable[[str, Mapping[str, Any]], None] | None = None,
) -> Iterator[dict[str, Any]]:
    """Hold a crash-releasing lease while one disposable wiki worktree is live."""

    root = repository_root(repository)
    path = _canonical(worktree, "wiki temporary worktree")
    ledger = _canonical(ledger_path, "wiki temporary ledger", must_exist=False)
    payload = {
        "schema": 1,
        "contract_version": LEASE_CONTRACT,
        "repository_root": str(root),
        "git_common_dir": str(common_git_dir(root)),
        "worktree_path": str(path),
        "run_id": _strict_text(run_id, "wiki temporary run ID"),
        "ticket_id": _strict_text(ticket_id, "wiki temporary ticket ID"),
        "ledger_path": str(ledger),
        "kind": kind,
    }
    _validate_lease(payload, repository=root, path=path)
    lease_path, lock_path = _lease_paths(root, path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="ascii") as handle:
        acquire_file_lock(handle, blocking=True)
        observer_added = False
        try:
            _write_envelope(lease_path, payload)
            if observer is not None:
                observer("add", payload)
                observer_added = True
            try:
                yield payload
            finally:
                try:
                    if observer is not None and observer_added:
                        observer("remove", payload)
                finally:
                    lease_path.unlink(missing_ok=True)
        except Exception:
            lease_path.unlink(missing_ok=True)
            raise
        finally:
            release_file_lock(handle)
    lock_path.unlink(missing_ok=True)


def _temporary_root(value: Path | None) -> Path:
    root = value if value is not None else Path(tempfile.gettempdir())
    return root.resolve(strict=True)


def _is_wiki_temporary(path: Path, temporary_root: Path) -> bool:
    return (
        path.parent == temporary_root
        and any(path.name.startswith(prefix) for prefix in _WIKI_PREFIXES)
    )


def _lease_disposition(repository: Path, path: Path) -> tuple[str, list[str]]:
    lease_path, lock_path = _lease_paths(repository, path)
    if not lease_path.exists():
        return "eligible", ["wiki-temporary-unleased"]
    try:
        document = json.loads(lease_path.read_text(encoding="utf-8"))
        payload = _validate_envelope(document, label="wiki temporary lease")
        _validate_lease(payload, repository=repository, path=path)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        return "protected", ["wiki-temporary-lease-invalid"]
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="ascii") as handle:
        try:
            acquire_file_lock(handle, blocking=False)
        except OSError:
            return "protected", ["wiki-temporary-live"]
        else:
            release_file_lock(handle)
    return "eligible", ["wiki-temporary-orphaned"]


def _classify_wiki_temporaries(
    repository: Path,
    unmanaged: list[str],
    *,
    temporary_root: Path,
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for spelling in unmanaged:
        path = Path(spelling).resolve(strict=False)
        if not _is_wiki_temporary(path, temporary_root):
            continue
        disposition, reasons = _lease_disposition(repository, path)
        entries.append({
            "kind": "wiki-temporary",
            "worktree_path": str(path),
            "disposition": disposition,
            "reasons": reasons,
        })
    return sorted(entries, key=lambda item: item["worktree_path"])


def _sweep_projection(
    repository: Path,
    *,
    invocation_path: Path,
    temporary_root: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    gc_plan = plan_worktree_gc(repository, invocation_path=invocation_path)
    owned = [{
        "kind": "owned",
        "run_id": entry["run_id"],
        "worktree_path": entry["worktree_path"],
        "disposition": entry["disposition"],
        "reasons": entry["reasons"] or (["gc-plan-eligible"] if entry["disposition"] == "eligible" else []),
    } for entry in gc_plan["entries"]]
    temporaries = _classify_wiki_temporaries(
        repository,
        list(gc_plan["unmanaged_worktrees"]),
        temporary_root=temporary_root,
    )
    entries = sorted([*owned, *temporaries], key=lambda item: (item["worktree_path"], item["kind"]))
    would_remove = []
    protected = []
    for entry in entries:
        if entry["disposition"] == "eligible":
            reason = entry["reasons"][0] if entry["reasons"] else "gc-plan-eligible"
            would_remove.append({**entry, "reason": reason})
        else:
            protected.append(entry)
    projection = {
        "schema": 1,
        "contract_version": SWEEP_CONTRACT,
        "repository_root": str(repository_root(repository)),
        "git_common_dir": str(common_git_dir(repository)),
        "temporary_root": str(temporary_root),
        "gc_plan_path": gc_plan["plan_path"],
        "gc_plan_sha256": gc_plan["plan_sha256"],
        "would_remove": would_remove,
        "protected": protected,
        "authority": {"cleanup": False, "merge": False, "provider": False, "publication": False},
    }
    projection["sweep_sha256"] = _digest(projection)
    return projection, gc_plan


def _remove_wiki_temporary(repository: Path, entry: Mapping[str, Any]) -> None:
    path = Path(str(entry["worktree_path"]))
    run_git(repository, "worktree", "remove", "--force", str(path))
    shutil.rmtree(path, ignore_errors=True)
    inventory = {item["worktree"] for item in _parse_worktree_inventory(repository)}
    if path.exists() or str(path) in inventory:
        raise WorktreeSweepError("wiki temporary removal absence readback failed")
    lease_path, lock_path = _lease_paths(repository, path)
    lease_path.unlink(missing_ok=True)
    lock_path.unlink(missing_ok=True)


def sweep_worktrees(
    repository: Path,
    *,
    apply: bool,
    actor: str | None = None,
    evidence: str | None = None,
    invocation_path: Path | None = None,
    temporary_root: Path | None = None,
) -> dict[str, Any]:
    """Report exact sweep candidates, or remove them under explicit local authority."""

    root = repository_root(repository)
    invocation = (invocation_path or Path.cwd()).resolve()
    temp_root = _temporary_root(temporary_root)
    projection, gc_plan = _sweep_projection(
        root, invocation_path=invocation, temporary_root=temp_root
    )
    if not apply:
        return {**projection, "applied": False, "removed_this_invocation": [], "receipts": []}

    cleanup_actor = _strict_text(actor, "cleanup actor")
    cleanup_evidence = _strict_text(evidence, "cleanup evidence")
    managed = apply_worktree_gc(
        root,
        Path(gc_plan["plan_path"]),
        expected_plan_sha256=str(gc_plan["plan_sha256"]),
        actor=cleanup_actor,
        evidence=cleanup_evidence,
        invocation_path=invocation,
    )
    removed = list(managed["removed_this_invocation"])
    receipt_paths: list[str] = []
    receipt_root = common_git_dir(root) / "ticket-autopilot" / "worktree-sweep" / "receipts" / projection["sweep_sha256"]
    wiki_candidates = [item for item in projection["would_remove"] if item["kind"] == "wiki-temporary"]
    for ordinal, entry in enumerate(wiki_candidates, start=1):
        path = Path(entry["worktree_path"])
        inventory = {item["worktree"] for item in _parse_worktree_inventory(root)}
        if str(path) not in inventory:
            raise WorktreeSweepError("wiki temporary inventory changed before removal")
        disposition, reasons = _lease_disposition(root, path)
        if disposition != "eligible" or reasons[0] != entry["reason"]:
            raise WorktreeSweepError("wiki temporary eligibility changed before removal")
        _remove_wiki_temporary(root, entry)
        removed.append(str(path))
        receipt = {
            "schema": 1,
            "contract_version": ENTRY_RECEIPT_CONTRACT,
            "sweep_sha256": projection["sweep_sha256"],
            "ordinal": ordinal,
            "kind": "wiki-temporary",
            "worktree_path": str(path),
            "reason": entry["reason"],
            "result": "removed",
            "actor": cleanup_actor,
            "evidence": cleanup_evidence,
        }
        receipt_path = receipt_root / f"{ordinal:04d}-{_lease_key(path)}.json"
        _write_envelope(receipt_path, receipt)
        receipt_paths.append(str(receipt_path))

    completion = {
        "schema": 1,
        "contract_version": COMPLETION_RECEIPT_CONTRACT,
        "sweep_sha256": projection["sweep_sha256"],
        "gc_completion_path": managed["completion_path"],
        "removed_this_invocation": removed,
        "wiki_receipts": receipt_paths,
        "actor": cleanup_actor,
        "evidence": cleanup_evidence,
        "complete": True,
    }
    completion_path = receipt_root / "completion.json"
    _write_envelope(completion_path, completion)
    return {
        **projection,
        "applied": True,
        "removed_this_invocation": removed,
        "receipts": receipt_paths,
        "completion_receipt": str(completion_path),
        "gc_apply": managed,
    }
