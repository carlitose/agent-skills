"""Disposable shared policy model for the cross-host rollover tracer bullets."""

from __future__ import annotations

from dataclasses import dataclass
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
from typing import Any


POLICY_SCHEMA = 1
THRESHOLD_TOKENS = 150_000
HANDOFF_TTL_SECONDS = 3_600
MAX_RESTORE_ATTEMPTS = 3


class PrototypeError(RuntimeError):
    """Fail-closed prototype error raised before an unauthorized side effect."""


def digest_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def workspace_key(workspace: Path) -> str:
    return digest_text(str(workspace.resolve()))


def source_session_key(source_session_id: str) -> str:
    if not isinstance(source_session_id, str) or not source_session_id:
        raise PrototypeError("source session identity must be non-empty")
    return digest_text(source_session_id)


def _require_exact_keys(value: Any, expected: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != expected:
        raise PrototypeError(f"invalid {label} shape")
    return value


def _require_private(path: Path, mode: int, label: str) -> None:
    try:
        actual = stat.S_IMODE(path.stat().st_mode)
    except OSError as error:
        raise PrototypeError(f"{label} is unavailable") from error
    if actual != mode:
        raise PrototypeError(f"{label} must use mode {mode:04o}")


def _write_private_json(path: Path, value: dict[str, Any]) -> None:
    encoded = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


@dataclass(frozen=True)
class DurablePointers:
    wayfinder_path: str
    ticket_folder: str
    run_id: str | None
    next_frontier: str

    def to_document(self) -> dict[str, Any]:
        return {
            "wayfinder_path": self.wayfinder_path,
            "ticket_folder": self.ticket_folder,
            "run_id": self.run_id,
            "next_frontier": self.next_frontier,
        }


@dataclass(frozen=True)
class ValidatedHandoff:
    path: Path
    digest: str
    rollover_id: str
    workspace_key: str
    source_session_key: str
    pointers: DurablePointers
    expires_at: int


def create_handoff(
    private_root: Path,
    *,
    workspace: Path,
    host_adapter_id: str,
    source_session_id: str,
    generation: int,
    rollover_id: str,
    pointers: DurablePointers,
    now: int,
) -> ValidatedHandoff:
    if generation < 1 or not rollover_id or not host_adapter_id:
        raise PrototypeError("invalid rollover identity")
    workspace = workspace.resolve()
    private_root.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(private_root, 0o700)
    if private_root.resolve().is_relative_to(workspace):
        raise PrototypeError("handoff root must be outside the workspace")

    handoff_dir = private_root / rollover_id
    handoff_dir.mkdir(mode=0o700)
    handoff_path = handoff_dir / "HANDOFF.md"
    document = {
        "schema": POLICY_SCHEMA,
        "rollover_id": rollover_id,
        "host_adapter_id": host_adapter_id,
        "generation": generation,
        "workspace_key": workspace_key(workspace),
        "source_session_key": source_session_key(source_session_id),
        "created_at": now,
        "expires_at": now + HANDOFF_TTL_SECONDS,
        "redacted": True,
        "transcript_included": False,
        "consumed": False,
        "pointers": pointers.to_document(),
    }
    descriptor = os.open(handoff_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return validate_handoff(
        handoff_path,
        workspace=workspace,
        host_adapter_id=host_adapter_id,
        source_session_id=source_session_id,
        generation=generation,
        now=now,
    )


def validate_handoff(
    path: Path,
    *,
    workspace: Path,
    host_adapter_id: str,
    source_session_id: str,
    generation: int,
    now: int,
) -> ValidatedHandoff:
    path = path.resolve()
    workspace = workspace.resolve()
    if path.is_relative_to(workspace):
        raise PrototypeError("handoff must remain outside the workspace")
    _require_private(path.parent, 0o700, "handoff directory")
    _require_private(path, 0o600, "handoff file")
    try:
        raw = path.read_text(encoding="utf-8")
        document = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise PrototypeError("handoff is malformed") from error

    expected = {
        "schema",
        "rollover_id",
        "host_adapter_id",
        "generation",
        "workspace_key",
        "source_session_key",
        "created_at",
        "expires_at",
        "redacted",
        "transcript_included",
        "consumed",
        "pointers",
    }
    document = _require_exact_keys(document, expected, "handoff")
    pointers_raw = _require_exact_keys(
        document["pointers"],
        {"wayfinder_path", "ticket_folder", "run_id", "next_frontier"},
        "durable pointers",
    )
    if type(document["schema"]) is not int or document["schema"] != POLICY_SCHEMA:
        raise PrototypeError("unsupported handoff schema")
    if not isinstance(document["rollover_id"], str) or not document["rollover_id"]:
        raise PrototypeError("handoff rollover identity must be non-empty")
    if (
        not isinstance(document["host_adapter_id"], str)
        or document["host_adapter_id"] != host_adapter_id
    ):
        raise PrototypeError("handoff host adapter mismatch")
    if type(document["generation"]) is not int or document["generation"] != generation:
        raise PrototypeError("handoff generation mismatch")
    if (
        not isinstance(document["workspace_key"], str)
        or document["workspace_key"] != workspace_key(workspace)
    ):
        raise PrototypeError("handoff workspace mismatch")
    if (
        not isinstance(document["source_session_key"], str)
        or document["source_session_key"] != source_session_key(source_session_id)
    ):
        raise PrototypeError("handoff source session mismatch")
    if document["redacted"] is not True or document["transcript_included"] is not False:
        raise PrototypeError("handoff violates the redaction contract")
    if document["consumed"] is not False:
        raise PrototypeError("handoff was already consumed")
    if type(document["created_at"]) is not int or type(document["expires_at"]) is not int:
        raise PrototypeError("handoff timestamps must be integers")
    if document["expires_at"] != document["created_at"] + HANDOFF_TTL_SECONDS:
        raise PrototypeError("handoff expiry must be exactly one hour")
    if now >= document["expires_at"]:
        raise PrototypeError("handoff is expired")

    for field in ("wayfinder_path", "ticket_folder", "next_frontier"):
        if not isinstance(pointers_raw[field], str) or not pointers_raw[field]:
            raise PrototypeError(f"handoff pointer {field} must be non-empty")
    if pointers_raw["run_id"] is not None and (
        not isinstance(pointers_raw["run_id"], str) or not pointers_raw["run_id"]
    ):
        raise PrototypeError("handoff run_id must be null or non-empty")
    pointer_paths = {
        field: Path(pointers_raw[field]).resolve()
        for field in ("wayfinder_path", "ticket_folder")
    }
    for field, candidate in pointer_paths.items():
        if not candidate.is_relative_to(workspace) or not candidate.exists():
            raise PrototypeError(f"handoff pointer {field} is not workspace-bound")
    if not pointer_paths["wayfinder_path"].is_file():
        raise PrototypeError("handoff Wayfinder pointer must be a file")
    if not pointer_paths["ticket_folder"].is_dir():
        raise PrototypeError("handoff ticket-folder pointer must be a directory")

    pointers = DurablePointers(**pointers_raw)
    return ValidatedHandoff(
        path=path,
        digest=hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        rollover_id=document["rollover_id"],
        workspace_key=document["workspace_key"],
        source_session_key=document["source_session_key"],
        pointers=pointers,
        expires_at=document["expires_at"],
    )


class PrivateRegistry:
    """Small locked registry model; entries are private JSON outside the workspace."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(self.root, 0o700)
        self.lock_path = self.root / ".lock"
        descriptor = os.open(self.lock_path, os.O_RDWR | os.O_CREAT, 0o600)
        os.close(descriptor)

    @staticmethod
    def _entry_name(
        workspace_digest: str,
        host_adapter_id: str,
        source_digest: str,
        generation: int,
    ) -> str:
        return digest_text(
            "\0".join(
                (workspace_digest, host_adapter_id, source_digest, str(generation))
            )
        )

    def create_or_read(
        self,
        *,
        handoff: ValidatedHandoff,
        host_adapter_id: str,
        generation: int,
    ) -> dict[str, Any]:
        name = self._entry_name(
            handoff.workspace_key,
            host_adapter_id,
            handoff.source_session_key,
            generation,
        )
        path = self.root / f"{name}.json"
        with self.lock_path.open("r+") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            if path.exists():
                existing = json.loads(path.read_text(encoding="utf-8"))
                if (
                    existing.get("rollover_id") != handoff.rollover_id
                    or existing.get("handoff_digest") != handoff.digest
                ):
                    raise PrototypeError("registry generation collision")
                return existing
            document = {
                "schema": POLICY_SCHEMA,
                "rollover_id": handoff.rollover_id,
                "workspace_key": handoff.workspace_key,
                "host_adapter_id": host_adapter_id,
                "source_session_key": handoff.source_session_key,
                "generation": generation,
                "handoff_path": str(handoff.path),
                "handoff_digest": handoff.digest,
                "expires_at": handoff.expires_at,
                "state": "handoff-validated",
                "attempt_count": 0,
                "target_thread_id": None,
                "bootstrap_turn_id": None,
                "consumed": False,
            }
            _write_private_json(path, document)
            return document

    def _path_for(self, entry: dict[str, Any]) -> Path:
        return self.root / (
            self._entry_name(
                entry["workspace_key"],
                entry["host_adapter_id"],
                entry["source_session_key"],
                entry["generation"],
            )
            + ".json"
        )

    def _locked_current(self, path: Path, expected: dict[str, Any]) -> dict[str, Any]:
        try:
            current = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise PrototypeError("registry entry is unavailable or malformed") from error
        if current != expected:
            raise PrototypeError("registry transition used stale state")
        return current

    @staticmethod
    def _require_same_identity(
        current: dict[str, Any], expected: dict[str, Any]
    ) -> None:
        identity = {
            "schema",
            "rollover_id",
            "workspace_key",
            "host_adapter_id",
            "source_session_key",
            "generation",
            "handoff_path",
            "handoff_digest",
            "expires_at",
        }
        if any(current.get(field) != expected.get(field) for field in identity):
            raise PrototypeError("registry transition used another generation")

    def begin_attempt(self, entry: dict[str, Any]) -> dict[str, Any]:
        path = self._path_for(entry)
        with self.lock_path.open("r+") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            try:
                current = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as error:
                raise PrototypeError("registry entry is unavailable or malformed") from error
            self._require_same_identity(current, entry)
            if current["consumed"]:
                raise PrototypeError("registry entry is consumed")
            if current["state"] == "restore-attempt":
                return current
            if current["state"] not in {"handoff-validated", "attempt-failed"}:
                raise PrototypeError("registry entry cannot begin a restore attempt")
            if current["attempt_count"] >= MAX_RESTORE_ATTEMPTS:
                raise PrototypeError("restore attempt limit reached")
            updated = dict(current)
            updated["attempt_count"] += 1
            updated["state"] = "restore-attempt"
            updated["target_thread_id"] = None
            updated["bootstrap_turn_id"] = None
            _write_private_json(path, updated)
            return updated

    def record_target(
        self, entry: dict[str, Any], target_thread_id: str
    ) -> dict[str, Any]:
        if not target_thread_id:
            raise PrototypeError("target thread receipt must be non-empty")
        path = self._path_for(entry)
        with self.lock_path.open("r+") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            current = json.loads(path.read_text(encoding="utf-8"))
            self._require_same_identity(current, entry)
            if current["consumed"] or current["attempt_count"] < 1:
                raise PrototypeError("target receipt has no active restore attempt")
            if current["state"] != "restore-attempt":
                raise PrototypeError("target receipt has no active restore phase")
            if current["target_thread_id"] == target_thread_id:
                return current
            if current["target_thread_id"] is not None:
                raise PrototypeError("restore attempt already owns another target")
            updated = dict(current)
            updated["target_thread_id"] = target_thread_id
            _write_private_json(path, updated)
            return updated

    def record_bootstrap(
        self, entry: dict[str, Any], bootstrap_turn_id: str
    ) -> dict[str, Any]:
        if not bootstrap_turn_id:
            raise PrototypeError("bootstrap receipt must be non-empty")
        path = self._path_for(entry)
        with self.lock_path.open("r+") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            current = json.loads(path.read_text(encoding="utf-8"))
            self._require_same_identity(current, entry)
            if current["state"] != "restore-attempt" or not current["target_thread_id"]:
                raise PrototypeError("bootstrap receipt has no active target")
            if current["bootstrap_turn_id"] == bootstrap_turn_id:
                return current
            if current["bootstrap_turn_id"] is not None:
                raise PrototypeError("restore attempt already owns another bootstrap")
            updated = dict(current)
            updated["bootstrap_turn_id"] = bootstrap_turn_id
            _write_private_json(path, updated)
            return updated

    def fail_attempt(self, entry: dict[str, Any]) -> dict[str, Any]:
        path = self._path_for(entry)
        with self.lock_path.open("r+") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            current = json.loads(path.read_text(encoding="utf-8"))
            self._require_same_identity(current, entry)
            if current["state"] == "attempt-failed":
                return current
            if current["state"] != "restore-attempt" or current["consumed"]:
                raise PrototypeError("no active attempt can be failed")
            updated = dict(current)
            updated["state"] = "attempt-failed"
            _write_private_json(path, updated)
            return updated

    def consume(self, entry: dict[str, Any], target_thread_id: str) -> dict[str, Any]:
        path = self._path_for(entry)
        with self.lock_path.open("r+") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            current = self._locked_current(path, entry)
            if (
                current["consumed"]
                or current["target_thread_id"] != target_thread_id
                or current["bootstrap_turn_id"] is None
            ):
                raise PrototypeError("invalid one-shot consumption receipt")
            updated = dict(current)
            updated["state"] = "restored"
            updated["consumed"] = True
            _write_private_json(path, updated)
            return updated
