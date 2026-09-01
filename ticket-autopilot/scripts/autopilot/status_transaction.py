from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import subprocess
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterator, Mapping

from .file_lock import acquire_file_lock, release_file_lock
from .git_ops import GitError, common_git_dir, repository_root, run_git
from .kernel import Kernel, TransitionError
from .ledger import AtomicLedger, LedgerError
from .legacy_recovery import LegacyRecoveryError, active_legacy_retirement
from .providers import ProviderError
from .ticket_contract import (
    ContractError,
    parse_ticket_markdown,
    read_ticket_text,
    ticket_source_digest,
)
from .ticket_lifecycle import LifecycleError, transition_ticket_source
from .tracked_status_delivery import (
    MergeGuardFactory,
    StatusProviderExecutor,
    TrackedStatusDeliveryError,
    drive_tracked_status_delivery,
)


STATUS_TRANSACTION_SCHEMA = 1
STATUS_TRANSACTION_OUTPUT_SCHEMA = 1
STATUS_TRANSACTION_DIR = "status-transactions"
_TARGET_DISPOSITIONS = {"open", "on-hold", "canceled"}
_DISPOSITION_FOLDERS = {
    "open": None,
    "on-hold": "hold",
    "canceled": "canceled",
    "completed": "done",
}
_ARTIFACT_ID = re.compile(r"^- Artifact ID:\s*`([^`]+)`\s*$", re.MULTILINE)
_ARTIFACT_ROLE = re.compile(r"^- Role:\s*`?([^`\s]+)`?\s*$", re.MULTILINE)
_SAFE_BRANCH = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,199}")
_HEX_DIGEST = re.compile(r"[0-9a-f]{64}")
_SECRET_MATERIAL = re.compile(
    r"(?i)(?:password|passwd|secret|token|api[_-]?key)\s*[:=]\s*\S+"
    r"|\b(?:gh[pousr]|github_pat)_[A-Za-z0-9_]{20,}\b"
)
_ZERO_HASH = "0" * 64
_EVENT_PHASES = {
    "transaction-intent": "lifecycle-intent",
    "transaction-gated": "gated",
    "tracked-handoff-ready": "tracked-handoff",
    "safe-boundary-armed": "safe-boundary",
    "target-refreshed": "target-refreshed",
    "source-applied": "source-applied",
    "candidate-frozen": "candidate-frozen",
    "commit-intent": "commit-intent",
    "committed": "committed",
    "push-intent": "push-intent",
    "push-armed": "push-armed",
    "pushed": "pushed",
    "provider-intent": "provider-intent",
    "provider-armed": "provider-armed",
    "pr-read-back": "pr-read-back",
    "merge-gated": "merge-gated",
    "merge-intent": "merge-intent",
    "merge-armed": "merge-armed",
    "provider-merged": "provider-merged",
    "terminal-proved": "terminal-proved",
    "projected": "projected",
    "tracked-complete": "complete",
    "external-unpublished": "external-unpublished",
}
_REPLAY_KEY_FIELDS = (
    "repository_identity",
    "git_common_dir",
    "ticket_id",
    "artifact_id",
    "ticket_digest",
    "ticket_source_relative_path",
    "ticket_folder_relative_path",
    "from_disposition",
    "to_disposition",
    "actor",
    "reason",
    "authority_ref",
    "reopen_gate_id",
    "source_mode",
    "target_branch",
)
_REQUEST_FIELDS = {
    "schema",
    *_REPLAY_KEY_FIELDS,
    "target_ref",
    "target_sha",
    "projection_run_id",
    "projection_ticket_state",
    "projection_execution_lifecycle",
    "projection_readiness",
    "projection_stop_reason",
    "retired_run_ids",
    "ambiguous_run_ids",
    "conflicting_run_ids",
}


class StatusTransactionError(LifecycleError):
    """A repository-owned administrative transaction cannot be proven safe."""


class _OwnerGate(StatusTransactionError):
    def __init__(self, gate: str):
        super().__init__(gate)
        self.gate = gate


@dataclass(frozen=True)
class StatusChangeRequest:
    ticket_source: Path
    ticket_id: str
    artifact_id: str
    ticket_digest: str
    from_disposition: str
    to_disposition: str
    source_mode: str
    actor: str
    reason: str
    authority_ref: str
    reopen_gate_id: str | None = None
    target_branch: str = "main"


@dataclass(frozen=True)
class OwnerResolution:
    projection_run_id: str | None
    projection_ledger: Path | None
    ticket_state: str
    retired_run_ids: tuple[str, ...]
    execution_lifecycle: str = "not-started"
    readiness: str = "ready"
    stop_reason: str | None = None
    resolution_gate: str | None = None
    ambiguous_run_ids: tuple[str, ...] = ()
    conflicting_run_ids: tuple[str, ...] = ()

    def public(self) -> dict[str, Any]:
        return {
            "transaction_owner": "repository-lifecycle",
            "projection_run_id": self.projection_run_id,
            "retired_run_ids": list(self.retired_run_ids),
            "ambiguous_run_ids": list(self.ambiguous_run_ids),
            "conflicting_run_ids": list(self.conflicting_run_ids),
            "execution_lifecycle": self.execution_lifecycle,
            "readiness": self.readiness,
            "stop_reason": self.stop_reason,
        }


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _require_text(value: Any, *, field: str, limit: int = 2048) -> str:
    if not isinstance(value, str) or not value.strip():
        raise StatusTransactionError(f"{field} must be a non-empty string")
    normalized = value.strip()
    if len(normalized) > limit or any(ord(character) < 32 for character in normalized):
        raise StatusTransactionError(f"{field} contains unsupported content")
    if _SECRET_MATERIAL.search(normalized):
        raise StatusTransactionError(f"{field} contains secret-shaped material")
    return normalized


def _validate_expected_request(request: StatusChangeRequest) -> StatusChangeRequest:
    ticket_id = _require_text(request.ticket_id, field="ticket_id", limit=200)
    artifact_id = _require_text(request.artifact_id, field="artifact_id", limit=300)
    digest = _require_text(request.ticket_digest, field="ticket_digest", limit=64)
    if _HEX_DIGEST.fullmatch(digest) is None:
        raise StatusTransactionError("ticket_digest must be lowercase sha256")
    if request.from_disposition not in _DISPOSITION_FOLDERS:
        raise StatusTransactionError("prior administrative disposition is invalid")
    if request.from_disposition == "completed":
        raise StatusTransactionError("completed tickets cannot change disposition")
    if request.to_disposition not in _TARGET_DISPOSITIONS:
        raise StatusTransactionError("target administrative disposition is invalid")
    if request.from_disposition == request.to_disposition:
        raise StatusTransactionError("source already has the requested disposition")
    if request.source_mode not in {"tracked", "ignored"}:
        raise StatusTransactionError("source_mode must be tracked or ignored")
    actor = _require_text(request.actor, field="actor", limit=300)
    reason = _require_text(request.reason, field="reason")
    authority_ref = _require_text(
        request.authority_ref, field="authority_ref", limit=1000
    )
    branch = _require_text(request.target_branch, field="target_branch", limit=200)
    if _SAFE_BRANCH.fullmatch(branch) is None or ".." in branch or branch.endswith("/"):
        raise StatusTransactionError("target_branch is unsafe")
    gate = request.reopen_gate_id
    if request.to_disposition == "open":
        gate = _require_text(gate, field="reopen_gate_id", limit=300)
    elif gate is not None:
        raise StatusTransactionError("hold and cancel cannot consume a reopen gate")
    return StatusChangeRequest(
        ticket_source=Path(request.ticket_source),
        ticket_id=ticket_id,
        artifact_id=artifact_id,
        ticket_digest=digest,
        from_disposition=request.from_disposition,
        to_disposition=request.to_disposition,
        source_mode=request.source_mode,
        actor=actor,
        reason=reason,
        authority_ref=authority_ref,
        reopen_gate_id=gate,
        target_branch=branch,
    )


def _binding(repository: Path) -> tuple[Path, Path]:
    lexical = Path(os.path.abspath(repository))
    current = Path(lexical.anchor)
    for part in lexical.parts[1:]:
        current = current / part
        if current.exists() and current.is_symlink():
            raise StatusTransactionError("repository_identity aliases are not accepted")
    supplied = lexical.resolve()
    root = repository_root(supplied)
    if root != supplied:
        raise StatusTransactionError("repository_identity must be the canonical root")
    common = common_git_dir(root)
    expected = root / ".git"
    if (
        expected.is_symlink()
        or not expected.is_dir()
        or common != expected.resolve()
        or common.is_symlink()
    ):
        raise StatusTransactionError(
            "status transaction requires the canonical primary worktree"
        )
    return root, common


def _assert_state_path(common: Path, path: Path) -> None:
    try:
        relative = path.relative_to(common)
        path.resolve(strict=False).relative_to(common)
    except ValueError as error:
        raise StatusTransactionError(
            "status transaction state escapes Git common state"
        ) from error
    current = common
    for part in relative.parts:
        current = current / part
        if current.exists() and current.is_symlink():
            raise StatusTransactionError("status transaction state contains a symbolic link")


def _safe_relative(root: Path, path: Path, *, field: str) -> tuple[Path, str]:
    candidate = path if path.is_absolute() else root / path
    lexical = Path(os.path.abspath(candidate))
    try:
        lexical_relative = lexical.relative_to(root)
    except ValueError as error:
        raise StatusTransactionError(f"{field} escapes repository") from error
    current = root
    for part in lexical_relative.parts:
        current = current / part
        if current.exists() and current.is_symlink():
            raise StatusTransactionError(f"{field} contains a symbolic link")
    resolved = lexical.resolve(strict=False)
    try:
        relative = resolved.relative_to(root)
    except ValueError as error:
        raise StatusTransactionError(f"{field} escapes repository") from error
    return resolved, relative.as_posix()


def _source_location(source: Path) -> tuple[Path, str, str]:
    parent = source.parent
    disposition = "open"
    for name, directory in _DISPOSITION_FOLDERS.items():
        if directory is not None and parent.name == directory:
            disposition = name
            parent = parent.parent
            break
    try:
        relative = source.relative_to(parent).as_posix()
    except ValueError as error:  # pragma: no cover - defensive after resolved paths
        raise StatusTransactionError("ticket source folder is invalid") from error
    return parent, relative, disposition


def _git_exit(root: Path, *arguments: str) -> int:
    return subprocess.run(
        ["git", *arguments], cwd=root, capture_output=True, check=False
    ).returncode


def _source_mode(root: Path, source_relative: str) -> str:
    if _git_exit(root, "ls-files", "--error-unmatch", "--", source_relative) == 0:
        return "tracked"
    if _git_exit(root, "check-ignore", "--quiet", "--", source_relative) == 0:
        return "ignored"
    raise StatusTransactionError(
        "ticket source must be tracked or explicitly ignored"
    )


def _target(root: Path, branch: str) -> tuple[str, str]:
    for reference in (
        f"refs/remotes/origin/{branch}",
        f"refs/heads/{branch}",
    ):
        try:
            sha = run_git(
                root,
                "--no-replace-objects",
                "rev-parse",
                "--verify",
                f"{reference}^{{commit}}",
            )
        except GitError:
            continue
        if not re.fullmatch(r"[0-9a-f]{40,64}", sha):
            raise StatusTransactionError("target commit identity is invalid")
        return reference, sha
    raise StatusTransactionError(f"target branch {branch!r} is unavailable")


def _artifact_identity(text: str) -> tuple[str, str]:
    artifact_ids = _ARTIFACT_ID.findall(text)
    roles = _ARTIFACT_ROLE.findall(text)
    if len(artifact_ids) != 1 or len(roles) != 1 or roles[0] != "ticket":
        raise StatusTransactionError(
            "ticket source requires one Artifact ID and Role: ticket"
        )
    return artifact_ids[0], roles[0]


def _assert_unique_ticket_identity(
    root: Path,
    source: Path,
    *,
    ticket_id: str,
    artifact_id: str,
) -> None:
    candidates: set[Path] = set()
    excluded_parts = {"fixtures", "prototypes", "tests"}
    for candidate in root.rglob("*.md"):
        relative_parts = candidate.relative_to(root).parts
        if excluded_parts.intersection(relative_parts) or candidate.is_symlink():
            continue
        candidates.add(candidate.resolve())
    for candidate in sorted(candidates, key=lambda item: item.as_posix()):
        if candidate == source:
            continue
        try:
            text = read_ticket_text(candidate)
            parsed = parse_ticket_markdown(text, source=str(candidate))
        except (ContractError, OSError, UnicodeDecodeError):
            continue
        if parsed.envelope["ticket_id"] == ticket_id:
            raise StatusTransactionError(
                "short ticket_id is not globally unique after fixture exclusion"
            )
        try:
            observed_artifact_id, _role = _artifact_identity(text)
        except StatusTransactionError:
            continue
        if observed_artifact_id == artifact_id:
            raise StatusTransactionError("ticket Artifact ID is not globally unique")


def _validate_source(
    root: Path,
    source: Path,
    source_relative: str,
    expected: StatusChangeRequest,
    *,
    target_sha: str,
) -> tuple[Path, str]:
    if source.is_symlink() or not source.is_file():
        raise StatusTransactionError("ticket source is not a regular file")
    try:
        text = read_ticket_text(source)
        parsed = parse_ticket_markdown(text, source=str(source))
    except (ContractError, UnicodeDecodeError) as error:
        raise StatusTransactionError(str(error)) from error
    artifact_id, _role = _artifact_identity(text)
    folder, source_in_folder, disposition = _source_location(source)
    observed = {
        "ticket_id": parsed.envelope["ticket_id"],
        "artifact_id": artifact_id,
        "ticket_digest": ticket_source_digest(source),
        "from_disposition": disposition,
        "source_mode": _source_mode(root, source_relative),
    }
    wanted = {
        "ticket_id": expected.ticket_id,
        "artifact_id": expected.artifact_id,
        "ticket_digest": expected.ticket_digest,
        "from_disposition": expected.from_disposition,
        "source_mode": expected.source_mode,
    }
    if observed != wanted:
        raise StatusTransactionError("ticket identity or source disposition drifted")
    if expected.source_mode == "tracked":
        if run_git(
            root,
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "--",
            source_relative,
        ):
            raise StatusTransactionError("tracked ticket source has worktree drift")
        try:
            expected_blob = run_git(
                root,
                "--no-replace-objects",
                "rev-parse",
                f"{target_sha}:{source_relative}",
            )
            observed_blob = run_git(
                root,
                "hash-object",
                "--path",
                source_relative,
                "--",
                source_relative,
            )
        except GitError as error:
            raise StatusTransactionError(
                "tracked ticket source is absent from the target commit"
            ) from error
        if expected_blob != observed_blob:
            raise StatusTransactionError(
                "tracked ticket source differs from the target commit"
            )
    return folder, source_in_folder


def _unwrap_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise StatusTransactionError(f"run state is unreadable: {path}") from error
    if (
        isinstance(value, dict)
        and set(value) == {"envelope_schema", "integrity", "payload"}
        and value.get("envelope_schema") == 1
        and isinstance(value.get("payload"), dict)
    ):
        if _digest(value["payload"]) != value.get("integrity"):
            raise StatusTransactionError(f"run state integrity failed: {path}")
        return value["payload"]
    if not isinstance(value, dict):
        raise StatusTransactionError(f"run state shape is invalid: {path}")
    return value


def _ticket_at_source(
    document: Mapping[str, Any],
    *,
    root: Path,
    ticket_id: str,
    source: Path,
) -> Mapping[str, Any] | None:
    if document.get("repo") != str(root):
        return None
    tickets = document.get("tickets")
    ticket = tickets.get(ticket_id) if isinstance(tickets, Mapping) else None
    if not isinstance(ticket, Mapping):
        return None
    folder = document.get("ticket_folder")
    current = ticket.get("current_source_relative_path")
    if isinstance(folder, str) and isinstance(current, str):
        candidate = (Path(folder) / current).resolve(strict=False)
    elif isinstance(ticket.get("path"), str):
        candidate = Path(ticket["path"]).resolve(strict=False)
    else:
        raise StatusTransactionError("matching run lacks exact ticket source identity")
    return ticket if candidate == source else None


def _matching_ticket(
    document: Mapping[str, Any],
    *,
    root: Path,
    ticket_id: str,
    ticket_digest: str,
    source: Path,
) -> Mapping[str, Any] | None:
    ticket = _ticket_at_source(
        document, root=root, ticket_id=ticket_id, source=source
    )
    if ticket is None or ticket.get("ticket_digest") != ticket_digest:
        return None
    return ticket


def _active_retirement(run: Path, root: Path) -> bool:
    if not (run / "legacy-retirement.json").exists():
        return False
    try:
        return active_legacy_retirement(root, run / "ledger.json") is not None
    except LegacyRecoveryError as error:
        raise StatusTransactionError("legacy retirement state is contradictory") from error


def _ticket_axes(
    document: Mapping[str, Any], ticket_id: str, ticket: Mapping[str, Any]
) -> tuple[str, str, str, str | None]:
    state = ticket.get("state")
    if not isinstance(state, str):
        raise StatusTransactionError("projection run ticket state is invalid")
    try:
        report = Kernel(dict(document)).report()["tickets"][ticket_id]
        lifecycle = report["lifecycle"]
        readiness = report["readiness"]
        stop_reason = report["stop_reason"]
    except (KeyError, TransitionError) as error:
        raise StatusTransactionError(
            "projection run execution axes are contradictory"
        ) from error
    effective_state = state
    if state == "gated":
        gates = document.get("gates", {})
        delivery_gate = any(
            isinstance(gate, Mapping)
            and gate.get("ticket_id") == ticket_id
            and gate.get("state") == "open"
            and gate.get("resume_state") in {"verified", "pr-open", "integrated"}
            for gate in gates.values()
        ) if isinstance(gates, Mapping) else False
        if delivery_gate or ticket.get("pr") is not None:
            effective_state = "delivery-in-progress"
    if (
        state == "pending"
        and ticket.get("disposition", "open") == "open"
        and readiness != "ready"
    ):
        effective_state = "waiting"
    return effective_state, lifecycle, readiness, stop_reason


def _resolve_owner(
    root: Path,
    common: Path,
    *,
    ticket_id: str,
    ticket_digest: str,
    source: Path,
) -> OwnerResolution:
    runs = common / "ticket-autopilot" / "runs"
    if runs.is_symlink():
        raise StatusTransactionError("run inventory is unsafe")
    usable: list[
        tuple[str, Path, Mapping[str, Any], str, str, str, str | None]
    ] = []
    retired: list[str] = []
    conflicting: list[str] = []
    if runs.is_dir():
        for run in sorted(runs.iterdir(), key=lambda item: item.name):
            ledger_path = run / "ledger.json"
            if run.is_symlink() or ledger_path.is_symlink() or not ledger_path.is_file():
                continue
            raw = _unwrap_json(ledger_path)
            ticket = _ticket_at_source(
                raw, root=root, ticket_id=ticket_id, source=source
            )
            if ticket is None:
                continue
            retired_run = _active_retirement(run, root)
            if ticket.get("ticket_digest") != ticket_digest:
                if not retired_run:
                    conflicting.append(run.name)
                continue
            if retired_run:
                retired.append(run.name)
                continue
            if raw.get("schema") != 4:
                raise StatusTransactionError(
                    f"matching legacy run {run.name!r} is not retired"
                )
            try:
                store = AtomicLedger(ledger_path)
                with store.run_locked():
                    document = store.load()
            except LedgerError as error:
                raise StatusTransactionError(
                    f"matching run {run.name!r} is invalid"
                ) from error
            current = _matching_ticket(
                document,
                root=root,
                ticket_id=ticket_id,
                ticket_digest=ticket_digest,
                source=source,
            )
            if current is None:
                raise StatusTransactionError("matching run changed during owner resolution")
            state, lifecycle, readiness, stop_reason = _ticket_axes(
                document, ticket_id, current
            )
            usable.append(
                (
                    run.name,
                    ledger_path,
                    current,
                    state,
                    lifecycle,
                    readiness,
                    stop_reason,
                )
            )
    if conflicting:
        return OwnerResolution(
            None,
            None,
            "pending",
            tuple(retired),
            execution_lifecycle="contradictory",
            readiness="contradictory",
            resolution_gate="run-source-drift",
            conflicting_run_ids=tuple(conflicting),
        )
    if len(usable) > 1:
        return OwnerResolution(
            None,
            None,
            "pending",
            tuple(retired),
            execution_lifecycle="ambiguous",
            readiness="ambiguous",
            resolution_gate="ambiguous-run-ownership",
            ambiguous_run_ids=tuple(item[0] for item in usable),
        )
    if not usable:
        return OwnerResolution(None, None, "pending", tuple(retired))
    run_id, ledger_path, _ticket, state, lifecycle, readiness, stop_reason = usable[0]
    return OwnerResolution(
        run_id,
        ledger_path,
        state,
        tuple(retired),
        execution_lifecycle=lifecycle,
        readiness=readiness,
        stop_reason=stop_reason,
    )


def _fsync_directory(path: Path) -> None:
    if os.name == "nt":
        return
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _atomic_write(path: Path, document: Mapping[str, Any]) -> None:
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
def _transaction_lock(root: Path) -> Iterator[None]:
    root.mkdir(parents=True, exist_ok=True)
    if root.is_symlink():
        raise StatusTransactionError("status transaction state is unsafe")
    path = root / "transactions.lock"
    if path.is_symlink():
        raise StatusTransactionError("status transaction lock is unsafe")
    with path.open("a+", encoding="ascii") as handle:
        try:
            acquire_file_lock(handle, blocking=True)
        except OSError as error:
            raise StatusTransactionError("status transaction state is locked") from error
        try:
            yield
        finally:
            release_file_lock(handle)


def _event_hash(event: Mapping[str, Any]) -> str:
    return _digest({key: value for key, value in event.items() if key != "event_hash"})


def _validated_document(value: Any, *, expected_path: Path | None = None) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != {
        "schema",
        "transaction_id",
        "request",
        "history",
    }:
        raise StatusTransactionError("status transaction journal shape is invalid")
    request = value.get("request")
    if (
        value.get("schema") != STATUS_TRANSACTION_SCHEMA
        or not isinstance(request, Mapping)
        or set(request) != _REQUEST_FIELDS
        or request.get("schema") != STATUS_TRANSACTION_SCHEMA
        or not isinstance(value.get("history"), list)
        or not value["history"]
    ):
        raise StatusTransactionError("status transaction journal is invalid")
    transaction_id = _digest(dict(request))
    if value.get("transaction_id") != transaction_id:
        raise StatusTransactionError("status transaction identity is contradictory")
    if expected_path is not None and expected_path.name != f"{transaction_id}.json":
        raise StatusTransactionError("status transaction path is contradictory")
    previous = _ZERO_HASH
    history: list[dict[str, Any]] = []
    for index, raw_event in enumerate(value["history"], 1):
        if not isinstance(raw_event, Mapping) or set(raw_event) != {
            "schema",
            "sequence",
            "event",
            "details",
            "previous_event_hash",
            "event_hash",
        }:
            raise StatusTransactionError("status transaction history shape is invalid")
        event = dict(raw_event)
        if (
            event.get("schema") != 1
            or event.get("sequence") != index
            or event.get("event") not in _EVENT_PHASES
            or not isinstance(event.get("details"), Mapping)
            or event.get("previous_event_hash") != previous
            or event.get("event_hash") != _event_hash(event)
        ):
            raise StatusTransactionError("status transaction history is invalid")
        previous = event["event_hash"]
        history.append(copy.deepcopy(event))
    allowed_next = {
        "transaction-intent": {
            "transaction-gated",
            "tracked-handoff-ready",
            "safe-boundary-armed",
            "source-applied",
        },
        "tracked-handoff-ready": {
            "transaction-gated",
            "safe-boundary-armed",
            "target-refreshed",
            "source-applied",
        },
        "safe-boundary-armed": {
            "transaction-gated",
            "target-refreshed",
            "source-applied",
        },
        "target-refreshed": {"source-applied"},
        "source-applied": {"external-unpublished", "candidate-frozen"},
        "candidate-frozen": {"commit-intent"},
        "commit-intent": {"committed"},
        "committed": {"push-intent"},
        "push-intent": {"push-armed"},
        "push-armed": {"pushed"},
        "pushed": {"provider-intent"},
        "provider-intent": {"provider-armed", "pr-read-back"},
        "provider-armed": {"pr-read-back"},
        "pr-read-back": {"merge-gated", "merge-intent", "provider-merged"},
        "merge-gated": {"merge-gated", "merge-intent", "provider-merged"},
        "merge-intent": {"merge-armed"},
        "merge-armed": {"provider-merged"},
        "provider-merged": {"terminal-proved"},
        "terminal-proved": {"projected"},
        "projected": {"tracked-complete"},
        "transaction-gated": set(),
        "external-unpublished": set(),
        "tracked-complete": set(),
    }
    for previous_event, next_event in zip(history, history[1:]):
        if next_event["event"] not in allowed_next.get(previous_event["event"], set()):
            raise StatusTransactionError("status transaction phase lineage is invalid")
    if history[0]["event"] != "transaction-intent" or history[0]["details"] != {}:
        raise StatusTransactionError("status transaction intent details are invalid")
    oid = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")
    for event in history[1:]:
        details = event["details"]
        name = event["event"]
        if name == "transaction-gated":
            valid = set(details) == {"gate"} and isinstance(details.get("gate"), str)
        elif name == "tracked-handoff-ready":
            valid = details == {
                "source_effect_applied": False,
                "provider_effect_applied": False,
            }
        elif name == "safe-boundary-armed":
            valid = (
                set(details)
                == {
                    "projection_run_id",
                    "ticket_state",
                    "execution_lifecycle",
                    "readiness",
                    "stop_reason",
                    "atomic_effect_settled",
                    "run_barrier_receipt_digest",
                }
                and details.get("projection_run_id")
                == request.get("projection_run_id")
                and isinstance(details.get("ticket_state"), str)
                and isinstance(details.get("execution_lifecycle"), str)
                and isinstance(details.get("readiness"), str)
                and (
                    details.get("stop_reason") is None
                    or isinstance(details.get("stop_reason"), str)
                )
                and details.get("atomic_effect_settled") is True
                and isinstance(details.get("run_barrier_receipt_digest"), str)
                and _HEX_DIGEST.fullmatch(
                    details["run_barrier_receipt_digest"]
                )
                is not None
            )
        elif name == "target-refreshed":
            valid = (
                set(details) == {"target_ref", "target_sha"}
                and isinstance(details.get("target_ref"), str)
                and isinstance(details.get("target_sha"), str)
                and oid.fullmatch(details["target_sha"]) is not None
            )
        elif name == "source-applied":
            valid = (
                set(details) == {"receipt", "source_readback_relative_path"}
                and isinstance(details.get("receipt"), Mapping)
                and isinstance(details.get("source_readback_relative_path"), str)
            )
        elif name == "candidate-frozen":
            valid = set(details) == {"candidate"} and isinstance(
                details.get("candidate"), Mapping
            )
        elif name in {"commit-intent", "committed"}:
            valid = set(details) == {"commit"} and isinstance(
                details.get("commit"), Mapping
            )
        elif name in {"push-intent", "push-armed"}:
            valid = (
                set(details) == {"branch", "head_sha"}
                and isinstance(details.get("branch"), str)
                and isinstance(details.get("head_sha"), str)
                and oid.fullmatch(details["head_sha"]) is not None
            )
        elif name == "pushed":
            valid = (
                set(details) == {"branch", "head_sha", "remote_sha"}
                and isinstance(details.get("branch"), str)
                and details.get("head_sha") == details.get("remote_sha")
                and isinstance(details.get("head_sha"), str)
                and oid.fullmatch(details["head_sha"]) is not None
            )
        elif name in {"provider-intent", "provider-armed"}:
            valid = (
                set(details)
                == {"provider", "branch", "base", "head_sha", "body_sha256"}
                and all(
                    isinstance(details.get(field), str) and details[field]
                    for field in ("provider", "branch", "base", "head_sha")
                )
                and oid.fullmatch(details["head_sha"]) is not None
                and isinstance(details.get("body_sha256"), str)
                and _HEX_DIGEST.fullmatch(details["body_sha256"]) is not None
            )
        elif name == "pr-read-back":
            valid = set(details) == {"observation"} and isinstance(
                details.get("observation"), Mapping
            )
        elif name == "merge-gated":
            valid = set(details) == {"gate"} and isinstance(details.get("gate"), str)
        elif name == "merge-intent":
            valid = (
                set(details)
                == {"provider", "pr_id", "head_sha", "actor", "evidence", "intent_key"}
                and all(isinstance(value, str) and value for value in details.values())
                and oid.fullmatch(details["head_sha"]) is not None
                and _HEX_DIGEST.fullmatch(details["intent_key"]) is not None
            )
        elif name == "merge-armed":
            valid = (
                set(details)
                == {
                    "provider",
                    "pr_id",
                    "head_sha",
                    "actor",
                    "evidence",
                    "intent_key",
                    "merge_mode",
                }
                and all(isinstance(value, str) and value for value in details.values())
                and details.get("merge_mode") in {"direct", "queue"}
                and oid.fullmatch(details["head_sha"]) is not None
                and _HEX_DIGEST.fullmatch(details["intent_key"]) is not None
            )
        elif name == "provider-merged":
            valid = (
                set(details) == {"observation", "provenance"}
                and isinstance(details.get("observation"), Mapping)
                and details.get("provenance") in {"runner-merge", "external-readback"}
            )
        elif name == "terminal-proved":
            valid = (
                set(details) == {"proof", "source_relative_path"}
                and isinstance(details.get("proof"), Mapping)
                and isinstance(details.get("source_relative_path"), str)
            )
        elif name == "projected":
            valid = (
                set(details)
                == {"projection_run_id", "source_relative_path", "ticket_digest"}
                and details.get("projection_run_id") == request.get("projection_run_id")
                and isinstance(details.get("source_relative_path"), str)
                and details.get("ticket_digest") == request.get("ticket_digest")
            )
        else:
            valid = (
                set(details) == {"projection_run_id", "tracked_delivery"}
                and details.get("projection_run_id")
                == request.get("projection_run_id")
                and details.get("tracked_delivery") is (name == "tracked-complete")
            )
        if not valid:
            raise StatusTransactionError("status transaction event details are invalid")
    return {
        "schema": STATUS_TRANSACTION_SCHEMA,
        "transaction_id": transaction_id,
        "request": copy.deepcopy(dict(request)),
        "history": history,
    }


def _load_document(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise StatusTransactionError("status transaction journal is unsafe")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise StatusTransactionError("status transaction journal is unreadable") from error
    return _validated_document(value, expected_path=path)


def _append(document: dict[str, Any], event_name: str, details: Mapping[str, Any]) -> None:
    history = document["history"]
    event = {
        "schema": 1,
        "sequence": len(history) + 1,
        "event": event_name,
        "details": copy.deepcopy(dict(details)),
        "previous_event_hash": history[-1]["event_hash"] if history else _ZERO_HASH,
    }
    event["event_hash"] = _event_hash(event)
    history.append(event)
    _validated_document(document)


def _phase(document: Mapping[str, Any]) -> str:
    return _EVENT_PHASES[document["history"][-1]["event"]]


def _request_key(request: Mapping[str, Any]) -> dict[str, Any]:
    return {field: request.get(field) for field in _REPLAY_KEY_FIELDS}


def _find_replay(root: Path, key: Mapping[str, Any]) -> tuple[Path, dict[str, Any]] | None:
    matches: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(root.glob("*.json"), key=lambda item: item.name):
        document = _load_document(path)
        if _request_key(document["request"]) == dict(key):
            matches.append((path, document))
    if len(matches) > 1:
        raise StatusTransactionError("status transaction replay identity is ambiguous")
    return matches[0] if matches else None


def _new_document(request: Mapping[str, Any]) -> dict[str, Any]:
    document = {
        "schema": STATUS_TRANSACTION_SCHEMA,
        "transaction_id": _digest(dict(request)),
        "request": copy.deepcopy(dict(request)),
        "history": [],
    }
    _append(document, "transaction-intent", {})
    return document


def _gate_for_owner(
    owner: OwnerResolution,
    target: str,
    *,
    safe_boundary_supported: bool = False,
) -> str | None:
    if owner.resolution_gate is not None:
        return owner.resolution_gate
    if target == "open" and owner.projection_ledger is None:
        return "reopen-gate-unavailable"
    if owner.ticket_state != "pending":
        if owner.ticket_state in {"active", "gated", "waiting"}:
            return (
                None
                if safe_boundary_supported
                else "safe-boundary-projection-unavailable"
            )
        return f"execution-state-unsupported:{owner.ticket_state}"
    return None


def _owner_binding(owner: OwnerResolution) -> tuple[Any, ...]:
    return (
        owner.projection_run_id,
        owner.retired_run_ids,
        owner.resolution_gate,
        owner.ambiguous_run_ids,
        owner.conflicting_run_ids,
    )


def _record_gate(
    transaction_root: Path, document: dict[str, Any], gate: str
) -> None:
    phase = _phase(document)
    if phase == "gated":
        if document["history"][-1]["details"].get("gate") != gate:
            raise StatusTransactionError("status transaction gate is contradictory")
        return
    if phase not in {"lifecycle-intent", "tracked-handoff", "safe-boundary"}:
        raise StatusTransactionError("status transaction cannot gate after a source effect")
    _append(document, "transaction-gated", {"gate": gate})
    _atomic_write(transaction_root / f"{document['transaction_id']}.json", document)


def _owner_kernel(
    owner: OwnerResolution,
    request: Mapping[str, Any],
    *,
    source: Path,
    store: AtomicLedger | None = None,
) -> tuple[AtomicLedger, Kernel] | None:
    if owner.projection_ledger is None:
        return None
    store = store or AtomicLedger(owner.projection_ledger)
    document = store.load()
    ticket = document.get("tickets", {}).get(request["ticket_id"])
    if (
        document.get("schema") != 4
        or document.get("repo") != request["repository_identity"]
        or not isinstance(ticket, Mapping)
    ):
        raise StatusTransactionError("projection run changed after owner resolution")
    if (
        document.get("ticket_source_mode") != request["source_mode"]
        or ticket.get("ticket_digest") != request["ticket_digest"]
        or ticket.get("disposition", "open") != request["from_disposition"]
        or (
            Path(document["ticket_folder"])
            / str(ticket.get("current_source_relative_path", ""))
        ).resolve(strict=False)
        != source
    ):
        raise _OwnerGate("run-source-drift")
    effective_state, lifecycle, readiness, stop_reason = _ticket_axes(
        document, request["ticket_id"], ticket
    )
    gate = _gate_for_owner(
        OwnerResolution(
            owner.projection_run_id,
            owner.projection_ledger,
            effective_state,
            owner.retired_run_ids,
            execution_lifecycle=lifecycle,
            readiness=readiness,
            stop_reason=stop_reason,
        ),
        request["to_disposition"],
        safe_boundary_supported=True,
    )
    if gate is not None:
        raise _OwnerGate(gate)
    kernel = Kernel(document)
    try:
        if request["to_disposition"] == "open":
            kernel.preflight_disposition_transition(
                request["ticket_id"],
                "open",
                actor=request["actor"],
                reason=request["reason"],
                authority_ref=request["authority_ref"],
                authority_gate_id=request["reopen_gate_id"],
            )
        else:
            kernel.preflight_disposition_transition(
                request["ticket_id"],
                request["to_disposition"],
                actor=request["actor"],
                reason=request["reason"],
                authority_ref=request["authority_ref"],
            )
    except TransitionError as error:
        raise StatusTransactionError(str(error)) from error
    return store, kernel


def _safe_boundary_receipt(
    document: Mapping[str, Any],
    owner: OwnerResolution,
    run_document: Mapping[str, Any],
    ticket: Mapping[str, Any],
) -> dict[str, Any]:
    request = document["request"]
    report = Kernel(dict(run_document)).report()["tickets"][request["ticket_id"]]
    prior_state = owner.ticket_state
    if prior_state == "active":
        outcome = "stopped-at-safe-boundary"
    elif prior_state in {"gated", "waiting"}:
        outcome = "preserved-at-safe-boundary"
    else:
        outcome = "inactive-safe-boundary"
    boundary_reason = request["reason"]
    gates = run_document.get("gates", {})
    gate_ids = sorted(
        gate_id
        for gate_id, gate in gates.items()
        if isinstance(gate_id, str)
        and isinstance(gate, Mapping)
        and gate.get("ticket_id") == request["ticket_id"]
        and gate.get("state") == "open"
    ) if isinstance(gates, Mapping) else []
    return {
        "schema": 1,
        "transaction_id": document["transaction_id"],
        "ticket_id": request["ticket_id"],
        "from_disposition": request["from_disposition"],
        "to_disposition": request["to_disposition"],
        "actor": request["actor"],
        "reason": boundary_reason,
        "authority_ref": request["authority_ref"],
        "prior_state": prior_state,
        "execution_lifecycle": owner.execution_lifecycle,
        "readiness": owner.readiness,
        "prior_stop_reason": owner.stop_reason,
        "outcome": outcome,
        "gate_ids": gate_ids,
        "readiness_causes": copy.deepcopy(report.get("readiness_causes", [])),
        "evidence_preserved": True,
    }


def _prepare_safe_boundary(
    transaction_root: Path,
    document: dict[str, Any],
    owner: OwnerResolution,
    *,
    source: Path,
) -> OwnerResolution:
    phase = _phase(document)
    if phase == "safe-boundary":
        return owner
    if phase not in {"lifecycle-intent", "tracked-handoff"}:
        # Historical schema-1 journals may already be beyond the CST-03 seam.
        # Replay them literally; never synthesize a retroactive safe boundary.
        return owner
    request = document["request"]
    receipt: dict[str, Any] | None = None
    updated_owner = owner
    if owner.projection_ledger is not None:
        store = AtomicLedger(owner.projection_ledger)
        try:
            with store.run_locked():
                run_document = store.load()
                ticket = _matching_ticket(
                    run_document,
                    root=Path(request["repository_identity"]),
                    ticket_id=request["ticket_id"],
                    ticket_digest=request["ticket_digest"],
                    source=source,
                )
                if (
                    run_document.get("schema") != 4
                    or run_document.get("repo") != request["repository_identity"]
                    or run_document.get("ticket_source_mode")
                    != request["source_mode"]
                    or not isinstance(ticket, Mapping)
                    or ticket.get("disposition", "open")
                    != request["from_disposition"]
                ):
                    raise _OwnerGate("run-source-drift")
                effective_state, lifecycle, readiness, stop_reason = _ticket_axes(
                    run_document, request["ticket_id"], ticket
                )
                current_owner = OwnerResolution(
                    owner.projection_run_id,
                    owner.projection_ledger,
                    effective_state,
                    owner.retired_run_ids,
                    execution_lifecycle=lifecycle,
                    readiness=readiness,
                    stop_reason=stop_reason,
                )
                gate = _gate_for_owner(
                    current_owner,
                    request["to_disposition"],
                    safe_boundary_supported=True,
                )
                if gate is not None:
                    raise _OwnerGate(gate)
                kernel = Kernel(run_document)
                current_barrier = ticket.get("status_barrier")
                if isinstance(current_barrier, Mapping):
                    if current_barrier.get("transaction_id") != document["transaction_id"]:
                        raise _OwnerGate("status-barrier-conflict")
                    receipt = copy.deepcopy(dict(current_barrier))
                else:
                    if request["to_disposition"] == "open":
                        kernel.preflight_disposition_transition(
                            request["ticket_id"],
                            "open",
                            actor=request["actor"],
                            reason=request["reason"],
                            authority_ref=request["authority_ref"],
                            authority_gate_id=request["reopen_gate_id"],
                        )
                    elif effective_state != "gated":
                        kernel.preflight_disposition_transition(
                            request["ticket_id"],
                            request["to_disposition"],
                            actor=request["actor"],
                            reason=request["reason"],
                            authority_ref=request["authority_ref"],
                        )
                    receipt = _safe_boundary_receipt(
                        document, current_owner, run_document, ticket
                    )
                    kernel.arm_status_barrier(request["ticket_id"], receipt)
                    store.save(kernel.ledger)
                report = kernel.report()["tickets"][request["ticket_id"]]
                updated_owner = OwnerResolution(
                    owner.projection_run_id,
                    owner.projection_ledger,
                    report["state"],
                    owner.retired_run_ids,
                    execution_lifecycle=report["lifecycle"],
                    readiness=report["readiness"],
                    stop_reason=report["stop_reason"],
                )
        except (LedgerError, TransitionError) as error:
            raise StatusTransactionError(
                "projection run safe-boundary preparation failed: " + str(error)
            ) from error
    receipt_digest = _digest(
        receipt
        if receipt is not None
        else {
            "transaction_id": document["transaction_id"],
            "projection_run_id": None,
        }
    )
    _append(
        document,
        "safe-boundary-armed",
        {
            "projection_run_id": owner.projection_run_id,
            "ticket_state": (
                receipt["prior_state"] if receipt is not None else owner.ticket_state
            ),
            "execution_lifecycle": (
                receipt["execution_lifecycle"]
                if receipt is not None
                else owner.execution_lifecycle
            ),
            "readiness": (
                receipt["readiness"] if receipt is not None else owner.readiness
            ),
            "stop_reason": (
                receipt["prior_stop_reason"] if receipt is not None else owner.stop_reason
            ),
            "atomic_effect_settled": True,
            "run_barrier_receipt_digest": receipt_digest,
        },
    )
    _atomic_write(transaction_root / f"{document['transaction_id']}.json", document)
    return updated_owner


def _readback_source(
    folder: Path, receipt: Mapping[str, Any], expected_digest: str
) -> Path:
    target = (folder / str(receipt.get("destination_relative_path", ""))).resolve(
        strict=False
    )
    try:
        target.relative_to(folder.resolve())
    except ValueError as error:
        raise StatusTransactionError("source receipt destination escapes folder") from error
    if target.is_symlink() or not target.is_file():
        raise StatusTransactionError("source receipt destination is missing")
    if ticket_source_digest(target) != expected_digest:
        raise StatusTransactionError("source receipt destination digest drifted")
    return target


def _apply_ignored(
    transaction_root: Path,
    document: dict[str, Any],
    owner: OwnerResolution,
    *,
    source: Path,
    checkpoint: Callable[[str], None] | None,
) -> dict[str, Any]:
    request = document["request"]
    folder = Path(request["repository_identity"]) / request[
        "ticket_folder_relative_path"
    ]
    source_receipts = transaction_root / "source-receipts"
    if source_receipts.is_symlink():
        raise StatusTransactionError("source receipt state is unsafe")
    if owner.projection_ledger is None:
        receipt = transition_ticket_source(
            folder,
            source_receipts,
            request["ticket_id"],
            request["to_disposition"],
            actor=request["actor"],
            reason=request["reason"],
            authority_ref=request["authority_ref"],
            authority_gate_id=request["reopen_gate_id"],
            expected_digest=request["ticket_digest"],
        )
    else:
        store = AtomicLedger(owner.projection_ledger)
        with store.run_locked():
            run_document = store.load()
            ticket = run_document.get("tickets", {}).get(request["ticket_id"])
            if not isinstance(ticket, Mapping):
                raise StatusTransactionError("projection run ticket disappeared")
            current_disposition = ticket.get("disposition", "open")
            if current_disposition == request["from_disposition"]:
                loaded = _owner_kernel(owner, request, source=source, store=store)
                if loaded is None:  # pragma: no cover - guarded by owner path
                    raise StatusTransactionError("projection run disappeared")
                _loaded_store, kernel = loaded
                receipt = transition_ticket_source(
                    folder,
                    source_receipts,
                    request["ticket_id"],
                    request["to_disposition"],
                    actor=request["actor"],
                    reason=request["reason"],
                    authority_ref=request["authority_ref"],
                    authority_gate_id=request["reopen_gate_id"],
                    expected_digest=request["ticket_digest"],
                )
                kernel.record_disposition_transition(request["ticket_id"], receipt)
                store.save(kernel.ledger)
            elif current_disposition == request["to_disposition"]:
                receipt = transition_ticket_source(
                    folder,
                    source_receipts,
                    request["ticket_id"],
                    request["to_disposition"],
                    actor=request["actor"],
                    reason=request["reason"],
                    authority_ref=request["authority_ref"],
                    authority_gate_id=request["reopen_gate_id"],
                    expected_digest=request["ticket_digest"],
                )
                recorded = ticket.get("disposition_receipt")
                if not isinstance(recorded, Mapping) or recorded != receipt:
                    raise StatusTransactionError(
                        "projection run disposition receipt is contradictory"
                    )
            else:
                raise _OwnerGate("run-source-drift")
    if checkpoint is not None:
        checkpoint("source-effect-applied")
    target = _readback_source(folder, receipt, request["ticket_digest"])
    if _phase(document) in {"lifecycle-intent", "safe-boundary"}:
        _append(
            document,
            "source-applied",
            {
                "receipt": receipt,
                "source_readback_relative_path": target.relative_to(
                    Path(request["repository_identity"])
                ).as_posix(),
            },
        )
        _atomic_write(
            transaction_root / f"{document['transaction_id']}.json", document
        )
        if checkpoint is not None:
            checkpoint("source-applied")
    if _phase(document) == "source-applied":
        _append(
            document,
            "external-unpublished",
            {
                "projection_run_id": owner.projection_run_id,
                "tracked_delivery": False,
            },
        )
        _atomic_write(
            transaction_root / f"{document['transaction_id']}.json", document
        )
        if checkpoint is not None:
            checkpoint("external-unpublished")
    return receipt


def _receipt_from_history(document: Mapping[str, Any]) -> Mapping[str, Any] | None:
    for event in document["history"]:
        receipt = event["details"].get("receipt")
        if isinstance(receipt, Mapping):
            return receipt
    return None


def _readback_projection(
    owner: OwnerResolution,
    request: Mapping[str, Any],
    receipt: Mapping[str, Any],
) -> None:
    if owner.projection_ledger is None:
        return
    store = AtomicLedger(owner.projection_ledger)
    try:
        with store.run_locked():
            document = store.load()
    except LedgerError as error:
        raise StatusTransactionError("projection run readback is unavailable") from error
    ticket = document.get("tickets", {}).get(request["ticket_id"])
    if (
        document.get("schema") != 4
        or document.get("repo") != request["repository_identity"]
        or not isinstance(ticket, Mapping)
        or ticket.get("ticket_digest") != request["ticket_digest"]
        or ticket.get("disposition") != request["to_disposition"]
        or ticket.get("current_source_relative_path")
        != receipt.get("destination_relative_path")
        or ticket.get("disposition_receipt") != receipt
    ):
        raise StatusTransactionError("projection run readback is contradictory")


def _project_tracked_owner(
    owner: OwnerResolution,
    request: Mapping[str, Any],
    receipt: Mapping[str, Any],
    terminal_relative_path: str,
) -> None:
    expected_terminal = (
        Path(str(request["ticket_folder_relative_path"]))
        / str(receipt.get("destination_relative_path", ""))
    ).as_posix()
    if terminal_relative_path != expected_terminal:
        raise StatusTransactionError("terminal source path is contradictory")
    if owner.projection_ledger is None:
        return
    store = AtomicLedger(owner.projection_ledger)
    try:
        with store.run_locked():
            document = store.load()
            ticket = document.get("tickets", {}).get(request["ticket_id"])
            if (
                document.get("schema") != 4
                or document.get("repo") != request["repository_identity"]
                or not isinstance(ticket, Mapping)
                or ticket.get("ticket_digest") != request["ticket_digest"]
            ):
                raise StatusTransactionError(
                    "projection run changed before terminal projection"
                )
            disposition = ticket.get("disposition", "open")
            if disposition == request["from_disposition"]:
                if ticket.get("current_source_relative_path") != receipt.get(
                    "source_relative_path"
                ):
                    raise StatusTransactionError(
                        "projection run source path drifted before terminal projection"
                    )
                kernel = Kernel(document)
                try:
                    if request["to_disposition"] == "open":
                        kernel.preflight_disposition_transition(
                            request["ticket_id"],
                            "open",
                            actor=request["actor"],
                            reason=request["reason"],
                            authority_ref=request["authority_ref"],
                            authority_gate_id=request["reopen_gate_id"],
                        )
                    else:
                        kernel.preflight_disposition_transition(
                            request["ticket_id"],
                            request["to_disposition"],
                            actor=request["actor"],
                            reason=request["reason"],
                            authority_ref=request["authority_ref"],
                        )
                    kernel.record_disposition_transition(request["ticket_id"], receipt)
                except TransitionError as error:
                    raise StatusTransactionError(str(error)) from error
                store.save(kernel.ledger)
            elif disposition == request["to_disposition"]:
                if (
                    ticket.get("current_source_relative_path")
                    != receipt.get("destination_relative_path")
                    or ticket.get("disposition_receipt") != receipt
                ):
                    raise StatusTransactionError(
                        "projection run terminal receipt is contradictory"
                    )
            else:
                raise StatusTransactionError(
                    "projection run disposition drifted before terminal projection"
                )
    except LedgerError as error:
        raise StatusTransactionError("projection run is unavailable") from error
    _readback_projection(owner, request, receipt)


def _result(
    document: Mapping[str, Any],
    owner: OwnerResolution,
    *,
    replayed: bool,
    already_applied: bool = False,
    gate_override: str | None = None,
) -> dict[str, Any]:
    request = document["request"]
    phase = _phase(document)
    event = document["history"][-1]
    gate = gate_override or (
        event["details"].get("gate")
        if phase in {"gated", "merge-gated"}
        else None
    )
    if phase == "external-unpublished":
        status = "already-applied" if already_applied else "external-unpublished"
    elif phase == "complete":
        status = "already-applied" if already_applied else "changed-integrated"
    elif gate is not None:
        status = "gated"
    elif phase == "tracked-handoff":
        status = "tracked-handoff"
    else:
        status = "in-progress"
    delivery_events = {
        item["event"]: copy.deepcopy(item["details"])
        for item in document["history"]
        if item["event"]
        in {
            "candidate-frozen",
            "committed",
            "pushed",
            "pr-read-back",
            "provider-merged",
            "terminal-proved",
            "projected",
        }
    }
    non_authorities = [
        "target-ticket-implementation",
        "tracked-completion",
        "issue-mutation",
        "wiki",
        "pi-sync",
        "cleanup",
    ]
    if phase not in {"provider-merged", "terminal-proved", "projected", "complete"}:
        non_authorities.append("merge")
    if phase not in {"terminal-proved", "projected", "complete"}:
        non_authorities.append("terminal-integration")
    if request["source_mode"] == "ignored":
        non_authorities.extend(["tracked-provider-delivery", "publication"])
    return {
        "schema": STATUS_TRANSACTION_OUTPUT_SCHEMA,
        "transaction_id": document["transaction_id"],
        "status": status,
        "phase": phase,
        "replayed": replayed,
        "repository_identity": request["repository_identity"],
        "git_common_dir": request["git_common_dir"],
        "ticket": {
            "ticket_id": request["ticket_id"],
            "artifact_id": request["artifact_id"],
            "ticket_digest": request["ticket_digest"],
            "source_relative_path": request["ticket_source_relative_path"],
        },
        "disposition": {
            "from": request["from_disposition"],
            "to": request["to_disposition"],
            "actor": request["actor"],
            "reason": request["reason"],
            "authority_ref": request["authority_ref"],
            "reopen_gate_id": request["reopen_gate_id"],
        },
        "source_mode": request["source_mode"],
        "target": {
            "branch": request["target_branch"],
            "ref": next(
                (
                    item["details"]["target_ref"]
                    for item in reversed(document["history"])
                    if item["event"] == "target-refreshed"
                ),
                request["target_ref"],
            ),
            "sha": next(
                (
                    item["details"]["target_sha"]
                    for item in reversed(document["history"])
                    if item["event"] == "target-refreshed"
                ),
                request["target_sha"],
            ),
        },
        "owner": owner.public(),
        "gate": gate,
        "source_receipt": copy.deepcopy(_receipt_from_history(document)),
        "delivery": delivery_events,
        "non_authorities": non_authorities,
    }


def _readback_tracked_terminal(
    root: Path,
    document: Mapping[str, Any],
    owner: OwnerResolution,
) -> None:
    request = document["request"]
    receipt = _receipt_from_history(document)
    if receipt is None:
        raise StatusTransactionError("completed tracked transaction lacks source receipt")
    terminal_event = next(
        (
            event["details"]
            for event in document["history"]
            if event["event"] == "terminal-proved"
        ),
        None,
    )
    committed_event = next(
        (
            event["details"]
            for event in document["history"]
            if event["event"] == "committed"
        ),
        None,
    )
    merged_event = next(
        (
            event["details"]
            for event in document["history"]
            if event["event"] == "provider-merged"
        ),
        None,
    )
    if (
        not isinstance(terminal_event, Mapping)
        or not isinstance(terminal_event.get("proof"), Mapping)
        or not isinstance(committed_event, Mapping)
        or not isinstance(committed_event.get("commit"), Mapping)
        or not isinstance(merged_event, Mapping)
        or not isinstance(merged_event.get("observation"), Mapping)
    ):
        raise StatusTransactionError("completed tracked delivery evidence is missing")
    proof = terminal_event["proof"]
    commit = committed_event["commit"]
    observation = merged_event["observation"]
    lineage = {
        "provider": observation.get("provider"),
        "pr_id": observation.get("pr_id"),
        "head_sha": commit.get("head_sha"),
        "base_branch": request["target_branch"],
    }
    expected_proof = {
        "schema": 1,
        "repository_identity": str(root),
        "provider": observation.get("provider"),
        "pr_id": observation.get("pr_id"),
        "head_sha": commit.get("head_sha"),
        "pr_base": request["target_branch"],
        "terminal_branch": request["target_branch"],
        "merge_commit_sha": observation.get("merge_commit_sha"),
        "provider_observation_digest": _digest(observation),
        "delivery_lineage_digest": _digest(lineage),
        "provenance": merged_event.get("provenance"),
    }
    proof_fields = {
        "schema",
        "repository_identity",
        "provider",
        "pr_id",
        "head_sha",
        "pr_base",
        "terminal_branch",
        "terminal_sha",
        "terminal_tree_oid",
        "merge_commit_sha",
        "reachable_kind",
        "reachable_sha",
        "provider_observation_digest",
        "delivery_lineage_digest",
        "provenance",
    }
    reachable_kind = proof.get("reachable_kind")
    expected_reachable = commit.get("head_sha") if reachable_kind == "head" else None
    if (
        set(proof) != proof_fields
        or any(proof.get(key) != value for key, value in expected_proof.items())
        or proof.get("reachable_sha") != expected_reachable
        or observation.get("operation") != "get-pr-state"
        or observation.get("evidence_class") != "live"
        or observation.get("observed") is not True
        or observation.get("state") != "merged"
        or observation.get("head_sha") != commit.get("head_sha")
        or proof.get("reachable_sha") != commit.get("head_sha")
    ):
        raise StatusTransactionError("completed tracked terminal proof is contradictory")
    terminal_sha = proof.get("terminal_sha")
    reachable_sha = proof.get("reachable_sha")
    if not isinstance(terminal_sha, str) or not isinstance(reachable_sha, str):
        raise StatusTransactionError("completed tracked terminal identity is malformed")
    ancestry = _git_exit(
        root,
        "--no-replace-objects",
        "merge-base",
        "--is-ancestor",
        reachable_sha,
        terminal_sha,
    )
    if ancestry != 0:
        raise StatusTransactionError("completed tracked head is not terminal-reachable")
    try:
        terminal_tree = run_git(
            root,
            "--no-replace-objects",
            "rev-parse",
            f"{terminal_sha}^{{tree}}",
        )
    except GitError as error:
        raise StatusTransactionError("completed terminal tree is unavailable") from error
    if terminal_tree != proof.get("terminal_tree_oid"):
        raise StatusTransactionError("completed terminal tree is contradictory")
    terminal_relative = terminal_event.get("source_relative_path")
    if not isinstance(terminal_relative, str):
        raise StatusTransactionError("completed tracked terminal source path is malformed")
    process = subprocess.run(
        ["git", "--no-replace-objects", "show", f"{terminal_sha}:{terminal_relative}"],
        cwd=root,
        capture_output=True,
        check=False,
        env={**os.environ, "GIT_NO_REPLACE_OBJECTS": "1"},
    )
    if (
        process.returncode
        or hashlib.sha256(process.stdout).hexdigest() != request["ticket_digest"]
    ):
        raise StatusTransactionError("completed tracked terminal source drifted")
    expected_terminal = (
        Path(str(request["ticket_folder_relative_path"]))
        / str(receipt.get("destination_relative_path", ""))
    ).as_posix()
    if terminal_relative != expected_terminal:
        raise StatusTransactionError("completed tracked terminal path is contradictory")
    old_relative = (
        Path(str(request["ticket_folder_relative_path"]))
        / str(receipt.get("source_relative_path", ""))
    ).as_posix()
    if (
        _git_exit(
            root,
            "--no-replace-objects",
            "cat-file",
            "-e",
            f"{terminal_sha}:{old_relative}",
        )
        == 0
    ):
        raise StatusTransactionError("completed terminal source still exists at prior path")
    _readback_projection(owner, request, receipt)


def execute_status_transaction(
    repository: Path,
    request: StatusChangeRequest,
    *,
    checkpoint: Callable[[str], None] | None = None,
    tracked_delivery: bool = False,
    provider_executor: StatusProviderExecutor | None = None,
    merge_guard_factory: MergeGuardFactory | None = None,
) -> dict[str, Any]:
    """Prepare tracked delivery or finish one pending ignored-source transition."""

    expected = _validate_expected_request(request)
    root, common = _binding(Path(repository))
    source, source_relative = _safe_relative(
        root, expected.ticket_source, field="ticket_source"
    )
    folder, _source_in_folder, disposition_from_path = _source_location(source)
    try:
        folder_relative = folder.relative_to(root).as_posix()
    except ValueError as error:
        raise StatusTransactionError("ticket folder escapes repository") from error
    transaction_root = common / "ticket-autopilot" / STATUS_TRANSACTION_DIR
    _assert_state_path(common, transaction_root)
    key = {
        "repository_identity": str(root),
        "git_common_dir": str(common),
        "ticket_id": expected.ticket_id,
        "artifact_id": expected.artifact_id,
        "ticket_digest": expected.ticket_digest,
        "ticket_source_relative_path": source_relative,
        "ticket_folder_relative_path": folder_relative,
        "from_disposition": expected.from_disposition,
        "to_disposition": expected.to_disposition,
        "actor": expected.actor,
        "reason": expected.reason,
        "authority_ref": expected.authority_ref,
        "reopen_gate_id": expected.reopen_gate_id,
        "source_mode": expected.source_mode,
        "target_branch": expected.target_branch,
    }
    with _transaction_lock(transaction_root):
        replay = _find_replay(transaction_root, key)
        if replay is not None:
            _path, document = replay
            owner = OwnerResolution(
                document["request"]["projection_run_id"],
                (
                    common
                    / "ticket-autopilot"
                    / "runs"
                    / document["request"]["projection_run_id"]
                    / "ledger.json"
                    if document["request"]["projection_run_id"] is not None
                    else None
                ),
                document["request"]["projection_ticket_state"],
                tuple(document["request"]["retired_run_ids"]),
                execution_lifecycle=document["request"][
                    "projection_execution_lifecycle"
                ],
                readiness=document["request"]["projection_readiness"],
                stop_reason=document["request"]["projection_stop_reason"],
                resolution_gate=(
                    "run-source-drift"
                    if document["request"]["conflicting_run_ids"]
                    else "ambiguous-run-ownership"
                    if document["request"]["ambiguous_run_ids"]
                    else None
                ),
                ambiguous_run_ids=tuple(
                    document["request"]["ambiguous_run_ids"]
                ),
                conflicting_run_ids=tuple(
                    document["request"]["conflicting_run_ids"]
                ),
            )
            phase = _phase(document)
            if phase in {"external-unpublished", "gated", "complete"} or (
                phase == "tracked-handoff" and not tracked_delivery
            ):
                if phase == "external-unpublished":
                    receipt = _receipt_from_history(document)
                    if receipt is None:
                        raise StatusTransactionError(
                            "completed status transaction lacks source receipt"
                        )
                    _readback_source(
                        root / document["request"]["ticket_folder_relative_path"],
                        receipt,
                        document["request"]["ticket_digest"],
                    )
                    _readback_projection(owner, document["request"], receipt)
                elif phase == "complete":
                    _readback_tracked_terminal(root, document, owner)
                else:
                    _validate_source(
                        root,
                        source,
                        source_relative,
                        expected,
                        target_sha=document["request"]["target_sha"],
                    )
                return _result(
                    document,
                    owner,
                    replayed=True,
                    already_applied=phase in {"external-unpublished", "complete"},
                )
        else:
            if disposition_from_path != expected.from_disposition:
                raise StatusTransactionError("ticket source disposition drifted")
            target_ref, target_sha = _target(root, expected.target_branch)
            source_folder, source_in_folder = _validate_source(
                root,
                source,
                source_relative,
                expected,
                target_sha=target_sha,
            )
            if (
                source_folder != folder
                or source_in_folder != source.relative_to(folder).as_posix()
            ):
                raise StatusTransactionError("ticket source root changed during validation")
            _assert_unique_ticket_identity(
                root,
                source,
                ticket_id=expected.ticket_id,
                artifact_id=expected.artifact_id,
            )
            owner = _resolve_owner(
                root,
                common,
                ticket_id=expected.ticket_id,
                ticket_digest=expected.ticket_digest,
                source=source,
            )
            request_document = {
                "schema": STATUS_TRANSACTION_SCHEMA,
                **key,
                "target_ref": target_ref,
                "target_sha": target_sha,
                "projection_run_id": owner.projection_run_id,
                "projection_ticket_state": owner.ticket_state,
                "projection_execution_lifecycle": owner.execution_lifecycle,
                "projection_readiness": owner.readiness,
                "projection_stop_reason": owner.stop_reason,
                "retired_run_ids": list(owner.retired_run_ids),
                "ambiguous_run_ids": list(owner.ambiguous_run_ids),
                "conflicting_run_ids": list(owner.conflicting_run_ids),
            }
            document = _new_document(request_document)
            if checkpoint is not None:
                checkpoint("before-intent")
            _atomic_write(
                transaction_root / f"{document['transaction_id']}.json", document
            )
            if checkpoint is not None:
                checkpoint("lifecycle-intent")
        if source.is_file() and _phase(document) in {
            "lifecycle-intent",
            "tracked-handoff",
        }:
            refreshed_owner = _resolve_owner(
                root,
                common,
                ticket_id=expected.ticket_id,
                ticket_digest=expected.ticket_digest,
                source=source,
            )
            if _owner_binding(refreshed_owner) != _owner_binding(owner):
                owner = OwnerResolution(
                    owner.projection_run_id,
                    owner.projection_ledger,
                    owner.ticket_state,
                    owner.retired_run_ids,
                    execution_lifecycle=owner.execution_lifecycle,
                    readiness=owner.readiness,
                    stop_reason=owner.stop_reason,
                    resolution_gate="run-source-drift",
                    ambiguous_run_ids=owner.ambiguous_run_ids,
                    conflicting_run_ids=owner.conflicting_run_ids,
                )
            else:
                owner = refreshed_owner
        safe_boundary_supported = expected.source_mode == "ignored" or tracked_delivery
        gate = _gate_for_owner(
            owner,
            expected.to_disposition,
            safe_boundary_supported=safe_boundary_supported,
        )
        if gate is not None:
            _record_gate(transaction_root, document, gate)
            return _result(document, owner, replayed=replay is not None)
        if expected.source_mode == "tracked":
            try:
                if (
                    not tracked_delivery
                    and owner.projection_ledger is not None
                    and _phase(document) in {"lifecycle-intent", "tracked-handoff"}
                ):
                    store = AtomicLedger(owner.projection_ledger)
                    with store.run_locked():
                        _owner_kernel(
                            owner, document["request"], source=source, store=store
                        )
            except _OwnerGate as error:
                _record_gate(transaction_root, document, error.gate)
                return _result(document, owner, replayed=replay is not None)
            if _phase(document) == "lifecycle-intent":
                _append(
                    document,
                    "tracked-handoff-ready",
                    {
                        "source_effect_applied": False,
                        "provider_effect_applied": False,
                    },
                )
                _atomic_write(
                    transaction_root / f"{document['transaction_id']}.json", document
                )
                if checkpoint is not None:
                    checkpoint("tracked-handoff")
            if not tracked_delivery:
                return _result(document, owner, replayed=replay is not None)
            try:
                owner = _prepare_safe_boundary(
                    transaction_root, document, owner, source=source
                )
            except _OwnerGate as error:
                _record_gate(transaction_root, document, error.gate)
                return _result(document, owner, replayed=replay is not None)
            if checkpoint is not None:
                checkpoint("safe-boundary")

            def record(event_name: str, details: Mapping[str, Any]) -> None:
                _append(document, event_name, details)
                _atomic_write(
                    transaction_root / f"{document['transaction_id']}.json", document
                )

            def project(
                receipt: Mapping[str, Any], terminal_relative_path: str
            ) -> None:
                _project_tracked_owner(
                    owner,
                    document["request"],
                    receipt,
                    terminal_relative_path,
                )

            try:
                outcome = drive_tracked_status_delivery(
                    root,
                    transaction_root,
                    document,
                    record=record,
                    project=project,
                    checkpoint=checkpoint,
                    provider_executor=provider_executor,
                    merge_guard_factory=merge_guard_factory,
                )
            except (TrackedStatusDeliveryError, ProviderError) as error:
                raise StatusTransactionError(str(error)) from error
            return _result(
                document,
                owner,
                replayed=replay is not None,
                gate_override=outcome.get("gate"),
            )
        try:
            owner = _prepare_safe_boundary(
                transaction_root, document, owner, source=source
            )
            if checkpoint is not None:
                checkpoint("safe-boundary")
            _apply_ignored(
                transaction_root,
                document,
                owner,
                source=source,
                checkpoint=checkpoint,
            )
        except _OwnerGate as error:
            _record_gate(transaction_root, document, error.gate)
            return _result(document, owner, replayed=replay is not None)
        return _result(document, owner, replayed=replay is not None)
