"""Exact, authority-bound recovery for incompatible legacy run ledgers.

Preparation is read-only and provider-free. Application is serialized against aggregate
merge scheduling, persists immutable intent before effects, and can replay a crash after an
effect without duplicating either a schema migration or a retirement receipt.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Iterator

from .file_lock import acquire_file_lock, release_file_lock
from .git_ops import common_git_dir, repository_root
from .ledger import AtomicLedger, ENVELOPE_VERSION, LEDGER_VERSION, LedgerError


MANIFEST_SCHEMA = 1
INTENT_SCHEMA = 1
PROGRESS_SCHEMA = 1
RETIREMENT_SCHEMA = 1
RECOVERY_STATE_RELATIVE_PATH = Path("ticket-autopilot/legacy-recovery")
SCHEDULER_LOCK_RELATIVE_PATH = Path("ticket-autopilot/repository-merge-all.lock")
RECOVERY_LOCK_RELATIVE_PATH = Path("ticket-autopilot/legacy-recovery.lock")
RETIREMENT_FILE = "legacy-retirement.json"
_HEX_64 = re.compile(r"^[0-9a-f]{64}$")
_RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class LegacyRecoveryError(LedgerError):
    """A recovery manifest, authority, receipt, or input is unsafe or contradictory."""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _require_text(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise LegacyRecoveryError(
            f"legacy recovery {field} must be non-empty and trimmed"
        )
    return value


def _require_digest(value: object, *, field: str) -> str:
    if not isinstance(value, str) or _HEX_64.fullmatch(value) is None:
        raise LegacyRecoveryError(
            f"legacy recovery {field} must be a lowercase SHA-256"
        )
    return value


def _binding(repository: str | Path) -> tuple[Path, dict[str, str]]:
    root = repository_root(Path(repository)).resolve()
    raw_common = common_git_dir(root)
    if raw_common.is_symlink():
        raise LegacyRecoveryError("legacy recovery Git common directory is unsafe")
    common = raw_common.resolve()
    if not common.is_dir():
        raise LegacyRecoveryError("legacy recovery Git common directory is unsafe")
    return root, {
        "repository_identity": str(root),
        "git_common_dir": str(common),
    }


def _safe_run_id(value: object) -> str:
    run_id = _require_text(value, field="run_id")
    if _RUN_ID.fullmatch(run_id) is None or run_id in {".", ".."}:
        raise LegacyRecoveryError("legacy recovery run_id is unsafe")
    return run_id


def _assert_git_state_path(binding: dict[str, str], path: Path) -> None:
    common = Path(binding["git_common_dir"])
    try:
        path.resolve(strict=False).relative_to(common)
        relative = path.relative_to(common)
    except ValueError as error:
        raise LegacyRecoveryError("legacy recovery state escapes Git common state") from error
    current = common
    for part in relative.parts:
        current = current / part
        if current.exists() and current.is_symlink():
            raise LegacyRecoveryError(
                "legacy recovery Git-common state must not contain symbolic links"
            )


def _ledger_path(binding: dict[str, str], run_id: str) -> Path:
    common = Path(binding["git_common_dir"])
    runs = common / "ticket-autopilot" / "runs"
    run = runs / run_id
    ledger = run / "ledger.json"
    if runs.is_symlink() or run.is_symlink() or ledger.is_symlink():
        raise LegacyRecoveryError("legacy recovery run paths must not be symbolic links")
    try:
        ledger.resolve().relative_to(runs.resolve())
    except ValueError as error:
        raise LegacyRecoveryError("legacy recovery ledger escapes run state") from error
    return ledger


def _read_enveloped_ledger(path: Path) -> tuple[bytes, dict[str, Any], dict[str, Any]]:
    if not path.is_file() or path.is_symlink():
        raise LegacyRecoveryError(f"legacy recovery ledger is not a safe file: {path}")
    try:
        content = path.read_bytes()
        envelope = json.loads(content)
    except (OSError, json.JSONDecodeError) as error:
        raise LegacyRecoveryError(f"legacy recovery ledger is unreadable: {path}") from error
    if (
        not isinstance(envelope, dict)
        or set(envelope) != {"envelope_schema", "integrity", "payload"}
        or type(envelope.get("envelope_schema")) is not int
        or envelope.get("envelope_schema") != ENVELOPE_VERSION
        or not isinstance(envelope.get("payload"), dict)
    ):
        raise LegacyRecoveryError("legacy recovery ledger integrity envelope is invalid")
    payload = envelope["payload"]
    if hashlib.sha256(_canonical_bytes(payload)).hexdigest() != envelope.get(
        "integrity"
    ):
        raise LegacyRecoveryError("legacy recovery ledger integrity mismatch")
    return content, envelope, payload


def _write_atomic(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink() or path.is_symlink():
        raise LegacyRecoveryError("legacy recovery state path is unsafe")
    descriptor, raw = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(raw)
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


def _wrapped(payload: dict[str, Any]) -> bytes:
    body = _canonical_bytes(payload)
    return _canonical_bytes(
        {
            "envelope_schema": 1,
            "integrity": hashlib.sha256(body).hexdigest(),
            "payload": payload,
        }
    ) + b"\n"


def _load_wrapped(path: Path, *, label: str) -> dict[str, Any] | None:
    if not path.exists():
        return None
    if not path.is_file() or path.is_symlink():
        raise LegacyRecoveryError(f"legacy recovery {label} is not a safe file")
    try:
        envelope = json.loads(path.read_bytes())
    except (OSError, json.JSONDecodeError) as error:
        raise LegacyRecoveryError(f"legacy recovery {label} is unreadable") from error
    if (
        not isinstance(envelope, dict)
        or set(envelope) != {"envelope_schema", "integrity", "payload"}
        or envelope.get("envelope_schema") != 1
        or not isinstance(envelope.get("payload"), dict)
        or hashlib.sha256(_canonical_bytes(envelope["payload"])).hexdigest()
        != envelope.get("integrity")
    ):
        raise LegacyRecoveryError(
            f"legacy recovery {label} integrity envelope is invalid"
        )
    return envelope["payload"]


@contextmanager
def _locked(path: Path, *, label: str, blocking: bool = False) -> Iterator[None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink() or path.is_symlink():
        raise LegacyRecoveryError(f"legacy recovery {label} lock path is unsafe")
    with path.open("a+", encoding="ascii") as handle:
        try:
            acquire_file_lock(handle, blocking=blocking)
        except OSError as error:
            raise LegacyRecoveryError(f"legacy recovery {label} is locked: {path}") from error
        try:
            handle.seek(0)
            handle.truncate()
            handle.write(f"{os.getpid()}\n")
            handle.flush()
            os.fsync(handle.fileno())
            yield
        finally:
            release_file_lock(handle)


def _load_inventory(path: Path) -> list[dict[str, Any]]:
    try:
        inventory = json.loads(path.read_bytes())
    except (OSError, json.JSONDecodeError) as error:
        raise LegacyRecoveryError("legacy recovery inventory is unreadable") from error
    if (
        not isinstance(inventory, dict)
        or set(inventory) != {"schema", "runs"}
        or inventory.get("schema") != 1
        or not isinstance(inventory.get("runs"), list)
        or not inventory["runs"]
    ):
        raise LegacyRecoveryError("legacy recovery inventory contract is invalid")
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for entry in inventory["runs"]:
        if not isinstance(entry, dict) or set(entry) != {
            "run_id",
            "action",
            "reason",
            "successor_run_id",
        }:
            raise LegacyRecoveryError("legacy recovery inventory entry is invalid")
        run_id = _safe_run_id(entry.get("run_id"))
        if run_id in seen:
            raise LegacyRecoveryError("legacy recovery inventory repeats a run_id")
        action = entry.get("action")
        if action not in {"migrate", "retire"}:
            raise LegacyRecoveryError("legacy recovery inventory action is invalid")
        reason = _require_text(entry.get("reason"), field="reason")
        successor = entry.get("successor_run_id")
        if successor is not None:
            successor = _safe_run_id(successor)
            if successor == run_id:
                raise LegacyRecoveryError(
                    "legacy recovery successor_run_id cannot equal run_id"
                )
        if action == "migrate" and successor is not None:
            raise LegacyRecoveryError(
                "legacy recovery migration cannot declare a successor"
            )
        normalized.append(
            {
                "run_id": run_id,
                "action": action,
                "reason": reason,
                "successor_run_id": successor,
            }
        )
        seen.add(run_id)
    return normalized


def _manifest_body(manifest: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in manifest.items() if key != "manifest_digest"}


def _validate_manifest(
    manifest: object,
    *,
    binding: dict[str, str],
    expected_digest: str,
) -> dict[str, Any]:
    expected_digest = _require_digest(expected_digest, field="manifest digest")
    if (
        not isinstance(manifest, dict)
        or set(manifest)
        != {"schema", "repository_binding", "actions", "manifest_digest"}
        or manifest.get("schema") != MANIFEST_SCHEMA
        or manifest.get("repository_binding") != binding
        or not isinstance(manifest.get("actions"), list)
        or not manifest["actions"]
    ):
        raise LegacyRecoveryError("legacy recovery manifest contract is invalid")
    actual_digest = _digest(_manifest_body(manifest))
    if manifest.get("manifest_digest") != actual_digest:
        raise LegacyRecoveryError("legacy recovery manifest self-digest is invalid")
    if expected_digest != actual_digest:
        raise LegacyRecoveryError("legacy recovery manifest digest was not authorized")
    seen: set[str] = set()
    for sequence, action in enumerate(manifest["actions"], 1):
        if not isinstance(action, dict) or set(action) != {
            "sequence",
            "run_id",
            "action",
            "ledger_schema",
            "input_ledger_sha256",
            "reason",
            "successor_run_id",
        }:
            raise LegacyRecoveryError("legacy recovery manifest action is invalid")
        run_id = _safe_run_id(action.get("run_id"))
        if run_id in seen or action.get("sequence") != sequence:
            raise LegacyRecoveryError(
                "legacy recovery manifest actions are duplicated or reordered"
            )
        operation = action.get("action")
        ledger_schema = action.get("ledger_schema")
        if operation == "migrate":
            if ledger_schema != 3 or action.get("successor_run_id") is not None:
                raise LegacyRecoveryError(
                    "legacy recovery migration action contradicts its schema"
                )
        elif operation == "retire":
            if ledger_schema not in {1, 2}:
                raise LegacyRecoveryError(
                    "legacy recovery retirement action contradicts its schema"
                )
            successor = action.get("successor_run_id")
            if successor is not None:
                _safe_run_id(successor)
                if successor == run_id:
                    raise LegacyRecoveryError(
                        "legacy recovery successor_run_id cannot equal run_id"
                    )
        else:
            raise LegacyRecoveryError("legacy recovery manifest action is invalid")
        _require_digest(
            action.get("input_ledger_sha256"), field="input ledger digest"
        )
        _require_text(action.get("reason"), field="reason")
        seen.add(run_id)
    return copy.deepcopy(manifest)


def prepare_recovery_manifest(
    *,
    repository: str | Path,
    inventory_path: str | Path,
    output_path: str | Path,
) -> dict[str, Any]:
    """Inspect explicit runs and write one canonical provider-free manifest."""

    root, binding = _binding(repository)
    output = Path(output_path).expanduser().resolve()
    try:
        output.relative_to(root)
    except ValueError:
        pass
    else:
        raise LegacyRecoveryError(
            "legacy recovery manifest output must be outside the repository"
        )
    actions: list[dict[str, Any]] = []
    for sequence, requested in enumerate(_load_inventory(Path(inventory_path)), 1):
        ledger = _ledger_path(binding, requested["run_id"])
        content, _envelope, payload = _read_enveloped_ledger(ledger)
        if payload.get("run_id") != requested["run_id"]:
            raise LegacyRecoveryError(
                "legacy recovery ledger directory contradicts run identity"
            )
        schema = payload.get("schema")
        if type(schema) is not int:
            raise LegacyRecoveryError("legacy recovery ledger schema is invalid")
        if requested["action"] == "migrate" and schema != 3:
            raise LegacyRecoveryError(
                "legacy recovery requested migration for a non-schema-3 ledger"
            )
        if requested["action"] == "retire" and schema not in {1, 2}:
            raise LegacyRecoveryError(
                "legacy recovery requested retirement for a non-schema-1/2 ledger"
            )
        actions.append(
            {
                "sequence": sequence,
                "run_id": requested["run_id"],
                "action": requested["action"],
                "ledger_schema": schema,
                "input_ledger_sha256": hashlib.sha256(content).hexdigest(),
                "reason": requested["reason"],
                "successor_run_id": requested["successor_run_id"],
            }
        )
    body = {
        "schema": MANIFEST_SCHEMA,
        "repository_binding": binding,
        "actions": actions,
    }
    manifest = {**body, "manifest_digest": _digest(body)}
    content = _canonical_bytes(manifest) + b"\n"
    if output.exists():
        if output.is_symlink() or not output.is_file() or output.read_bytes() != content:
            raise LegacyRecoveryError(
                "legacy recovery manifest output already exists with different content"
            )
        replayed = True
    else:
        _write_atomic(output, content)
        replayed = False
    return {
        "manifest_path": str(output),
        "manifest_digest": manifest["manifest_digest"],
        "repository_binding": binding,
        "actions": copy.deepcopy(actions),
        "replayed": replayed,
        "mutation_scope": "manifest-only",
    }


def load_recovery_manifest(
    *,
    repository: str | Path,
    manifest_path: str | Path,
    manifest_digest: str,
) -> tuple[Path, dict[str, str], dict[str, Any]]:
    root, binding = _binding(repository)
    try:
        value = json.loads(Path(manifest_path).read_bytes())
    except (OSError, json.JSONDecodeError) as error:
        raise LegacyRecoveryError("legacy recovery manifest is unreadable") from error
    return root, binding, _validate_manifest(
        value, binding=binding, expected_digest=manifest_digest
    )


class RetirementStore:
    """Integrity-wrapped append-only retirement lineage beside one legacy ledger."""

    def __init__(self, ledger_path: Path, binding: dict[str, str]):
        self.ledger_path = ledger_path
        self.path = ledger_path.parent / RETIREMENT_FILE
        self.binding = copy.deepcopy(binding)
        _assert_git_state_path(self.binding, self.path)

    @staticmethod
    def _event_hash(event: dict[str, Any]) -> str:
        return _digest({key: value for key, value in event.items() if key != "event_hash"})

    def _validate(self, state: dict[str, Any]) -> None:
        if (
            set(state) != {"schema", "repository_binding", "run_id", "events"}
            or state.get("schema") != RETIREMENT_SCHEMA
            or state.get("repository_binding") != self.binding
            or state.get("run_id") != self.ledger_path.parent.name
            or not isinstance(state.get("events"), list)
            or not state["events"]
        ):
            raise LegacyRecoveryError("legacy retirement state contract is invalid")
        previous_hash = "0" * 64
        retirement_hashes: set[str] = set()
        for sequence, event in enumerate(state["events"], 1):
            common_keys = {
                "schema",
                "sequence",
                "operation",
                "previous_event_hash",
                "actor",
                "evidence",
                "event_hash",
            }
            if not isinstance(event, dict) or event.get("schema") != 1:
                raise LegacyRecoveryError("legacy retirement event is invalid")
            if (
                event.get("sequence") != sequence
                or event.get("previous_event_hash") != previous_hash
                or event.get("event_hash") != self._event_hash(event)
            ):
                raise LegacyRecoveryError("legacy retirement event lineage is invalid")
            _require_text(event.get("actor"), field="retirement actor")
            _require_text(event.get("evidence"), field="retirement evidence")
            if event.get("operation") == "retire":
                if set(event) != common_keys | {
                    "ledger_sha256",
                    "ledger_schema",
                    "reason",
                    "successor_run_id",
                    "manifest_digest",
                    "action_sequence",
                }:
                    raise LegacyRecoveryError("legacy retirement receipt is invalid")
                _require_digest(event.get("ledger_sha256"), field="retired ledger digest")
                _require_digest(event.get("manifest_digest"), field="manifest digest")
                if event.get("ledger_schema") not in {1, 2}:
                    raise LegacyRecoveryError("legacy retirement schema is invalid")
                _require_text(event.get("reason"), field="retirement reason")
                successor = event.get("successor_run_id")
                if successor is not None:
                    _safe_run_id(successor)
                    if successor == state["run_id"]:
                        raise LegacyRecoveryError(
                            "legacy retirement successor cannot equal run_id"
                        )
                if type(event.get("action_sequence")) is not int or event[
                    "action_sequence"
                ] <= 0:
                    raise LegacyRecoveryError(
                        "legacy retirement action sequence is invalid"
                    )
                retirement_hashes.add(event["event_hash"])
            elif event.get("operation") == "revoke":
                if set(event) != common_keys | {"target_event_hash", "reason"}:
                    raise LegacyRecoveryError("legacy retirement revocation is invalid")
                prior = state["events"][sequence - 2] if sequence > 1 else None
                if (
                    event.get("target_event_hash") not in retirement_hashes
                    or not isinstance(prior, dict)
                    or prior.get("operation") != "retire"
                    or event.get("target_event_hash") != prior.get("event_hash")
                ):
                    raise LegacyRecoveryError(
                        "legacy retirement revocation target is invalid"
                    )
                _require_text(event.get("reason"), field="revocation reason")
            else:
                raise LegacyRecoveryError("legacy retirement operation is invalid")
            previous_hash = event["event_hash"]

    def load(self) -> dict[str, Any] | None:
        state = _load_wrapped(self.path, label="retirement state")
        if state is not None:
            self._validate(state)
        return state

    def active(self) -> dict[str, Any] | None:
        state = self.load()
        if state is None or state["events"][-1]["operation"] == "revoke":
            return None
        event = state["events"][-1]
        content, _envelope, payload = _read_enveloped_ledger(self.ledger_path)
        if (
            hashlib.sha256(content).hexdigest() != event["ledger_sha256"]
            or payload.get("schema") != event["ledger_schema"]
            or payload.get("run_id") != state["run_id"]
        ):
            raise LegacyRecoveryError(
                "legacy retirement receipt does not match the current ledger"
            )
        return copy.deepcopy(event)

    def retire(
        self,
        *,
        ledger_sha256: str,
        ledger_schema: int,
        actor: str,
        evidence: str,
        reason: str,
        successor_run_id: str | None,
        manifest_digest: str,
        action_sequence: int,
    ) -> tuple[dict[str, Any], bool]:
        state = self.load()
        expected = {
            "ledger_sha256": ledger_sha256,
            "ledger_schema": ledger_schema,
            "actor": actor,
            "evidence": evidence,
            "reason": reason,
            "successor_run_id": successor_run_id,
            "manifest_digest": manifest_digest,
            "action_sequence": action_sequence,
        }
        if state is not None and state["events"][-1]["operation"] == "retire":
            active = self.active()
            assert active is not None
            if all(active.get(key) == value for key, value in expected.items()):
                return active, True
            raise LegacyRecoveryError(
                "legacy retirement contradicts an active retirement receipt"
            )
        if state is not None:
            revoked_manifests = {
                prior.get("manifest_digest")
                for prior in state["events"]
                if prior.get("operation") == "retire"
                and any(
                    later.get("operation") == "revoke"
                    and later.get("target_event_hash") == prior.get("event_hash")
                    for later in state["events"]
                )
            }
            if manifest_digest in revoked_manifests:
                raise LegacyRecoveryError(
                    "legacy retirement authority was revoked; a new manifest is required"
                )
        events = [] if state is None else copy.deepcopy(state["events"])
        event = {
            "schema": 1,
            "sequence": len(events) + 1,
            "operation": "retire",
            "previous_event_hash": events[-1]["event_hash"] if events else "0" * 64,
            **expected,
        }
        event["event_hash"] = self._event_hash(event)
        events.append(event)
        updated = {
            "schema": RETIREMENT_SCHEMA,
            "repository_binding": copy.deepcopy(self.binding),
            "run_id": self.ledger_path.parent.name,
            "events": events,
        }
        self._validate(updated)
        _write_atomic(self.path, _wrapped(updated))
        return copy.deepcopy(event), False

    def revoke(self, *, actor: str, evidence: str, reason: str) -> dict[str, Any]:
        state = self.load()
        active = self.active()
        if state is None or active is None:
            raise LegacyRecoveryError("legacy retirement has no active receipt to revoke")
        events = copy.deepcopy(state["events"])
        event = {
            "schema": 1,
            "sequence": len(events) + 1,
            "operation": "revoke",
            "previous_event_hash": events[-1]["event_hash"],
            "target_event_hash": active["event_hash"],
            "actor": _require_text(actor, field="revocation actor"),
            "evidence": _require_text(evidence, field="revocation evidence"),
            "reason": _require_text(reason, field="revocation reason"),
        }
        event["event_hash"] = self._event_hash(event)
        events.append(event)
        updated = {**state, "events": events}
        self._validate(updated)
        _write_atomic(self.path, _wrapped(updated))
        return copy.deepcopy(event)


def active_legacy_retirement(
    repository: str | Path, ledger_path: Path
) -> dict[str, Any] | None:
    """Return the only aggregate-skip capability: an exact active retirement."""

    _root, binding = _binding(repository)
    expected = _ledger_path(binding, ledger_path.parent.name)
    if expected.resolve() != ledger_path.resolve():
        raise LegacyRecoveryError("legacy retirement ledger path is outside run state")
    return RetirementStore(expected, binding).active()


def _intent_payload(
    manifest: dict[str, Any], *, actor: str, evidence: str
) -> dict[str, Any]:
    return {
        "schema": INTENT_SCHEMA,
        "repository_binding": copy.deepcopy(manifest["repository_binding"]),
        "manifest_digest": manifest["manifest_digest"],
        "actions": copy.deepcopy(manifest["actions"]),
        "actor": _require_text(actor, field="actor"),
        "evidence": _require_text(evidence, field="evidence"),
    }


def _validate_intent(intent: dict[str, Any], manifest: dict[str, Any]) -> None:
    if (
        set(intent)
        != {
            "schema",
            "repository_binding",
            "manifest_digest",
            "actions",
            "actor",
            "evidence",
        }
        or intent.get("schema") != INTENT_SCHEMA
        or intent.get("repository_binding") != manifest["repository_binding"]
        or intent.get("manifest_digest") != manifest["manifest_digest"]
        or intent.get("actions") != manifest["actions"]
    ):
        raise LegacyRecoveryError("legacy recovery application intent is invalid")
    _require_text(intent.get("actor"), field="actor")
    _require_text(intent.get("evidence"), field="evidence")


def _persist_intent(
    path: Path, intent: dict[str, Any], manifest: dict[str, Any]
) -> bool:
    _validate_intent(intent, manifest)
    existing = _load_wrapped(path, label="application intent")
    if existing is not None:
        if existing != intent:
            raise LegacyRecoveryError(
                "legacy recovery manifest already has contradictory application intent"
            )
        return True
    _write_atomic(path, _wrapped(intent))
    return False


def _receipt_hash(receipt: dict[str, Any]) -> str:
    return _digest({key: value for key, value in receipt.items() if key != "receipt_hash"})


def _validate_progress(
    progress: dict[str, Any], *, intent_digest: str, actions: list[dict[str, Any]]
) -> None:
    if (
        set(progress) != {"schema", "intent_digest", "receipts"}
        or progress.get("schema") != PROGRESS_SCHEMA
        or progress.get("intent_digest") != intent_digest
        or not isinstance(progress.get("receipts"), list)
        or len(progress["receipts"]) > len(actions)
    ):
        raise LegacyRecoveryError("legacy recovery progress contract is invalid")
    previous_hash = "0" * 64
    for sequence, receipt in enumerate(progress["receipts"], 1):
        action = actions[sequence - 1]
        if (
            not isinstance(receipt, dict)
            or set(receipt)
            != {
                "schema",
                "sequence",
                "run_id",
                "action",
                "input_ledger_sha256",
                "result_identity",
                "previous_receipt_hash",
                "receipt_hash",
            }
            or receipt.get("schema") != 1
            or receipt.get("sequence") != sequence
            or receipt.get("run_id") != action["run_id"]
            or receipt.get("action") != action["action"]
            or receipt.get("input_ledger_sha256")
            != action["input_ledger_sha256"]
            or receipt.get("previous_receipt_hash") != previous_hash
            or receipt.get("receipt_hash") != _receipt_hash(receipt)
            or not isinstance(receipt.get("result_identity"), dict)
        ):
            raise LegacyRecoveryError("legacy recovery progress receipt is invalid")
        previous_hash = receipt["receipt_hash"]


def _migration_matches(
    document: dict[str, Any],
    *,
    action: dict[str, Any],
    actor: str,
    evidence: str,
    manifest_digest: str,
) -> bool:
    migration = document.get("legacy_lifecycle_migration")
    if not isinstance(migration, dict):
        return False
    return migration == {
        "from_schema": 3,
        "original_integrity": migration.get("original_integrity"),
        "original_history_head": migration.get("original_history_head"),
        "input_ledger_sha256": action["input_ledger_sha256"],
        "actor": actor,
        "evidence": evidence,
        "recovery_manifest_digest": manifest_digest,
        "action_sequence": action["sequence"],
    }


def _migration_identity(document: dict[str, Any], ledger_path: Path) -> dict[str, Any]:
    migration = document["legacy_lifecycle_migration"]
    return {
        "ledger_sha256": _file_sha256(ledger_path),
        "migration_event_hash": document["history"][-1]["hash"],
        "original_integrity": migration["original_integrity"],
        "original_history_head": migration["original_history_head"],
    }


def _verify_action_state(
    *,
    binding: dict[str, str],
    action: dict[str, Any],
    actor: str,
    evidence: str,
    manifest_digest: str,
    expected_identity: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ledger_path = _ledger_path(binding, action["run_id"])
    if action["action"] == "migrate":
        document = AtomicLedger(ledger_path).load()
        if not _migration_matches(
            document,
            action=action,
            actor=actor,
            evidence=evidence,
            manifest_digest=manifest_digest,
        ):
            raise LegacyRecoveryError(
                "legacy migration receipt does not match application intent"
            )
        identity = _migration_identity(document, ledger_path)
    else:
        active = RetirementStore(ledger_path, binding).active()
        if active is None or any(
            active.get(key) != value
            for key, value in {
                "ledger_sha256": action["input_ledger_sha256"],
                "ledger_schema": action["ledger_schema"],
                "actor": actor,
                "evidence": evidence,
                "reason": action["reason"],
                "successor_run_id": action["successor_run_id"],
                "manifest_digest": manifest_digest,
                "action_sequence": action["sequence"],
            }.items()
        ):
            raise LegacyRecoveryError(
                "legacy retirement receipt does not match application intent"
            )
        identity = {
            "ledger_sha256": action["input_ledger_sha256"],
            "retirement_event_hash": active["event_hash"],
        }
    if expected_identity is not None and identity != expected_identity:
        raise LegacyRecoveryError(
            "legacy recovery progress contradicts current exact readback"
        )
    return identity


def _apply_action(
    *,
    binding: dict[str, str],
    action: dict[str, Any],
    actor: str,
    evidence: str,
    manifest_digest: str,
) -> dict[str, Any]:
    ledger_path = _ledger_path(binding, action["run_id"])
    store = AtomicLedger(ledger_path)
    with store.run_locked():
        current_sha = _file_sha256(ledger_path)
        if action["action"] == "migrate":
            document = store.migrate_lifecycle_v3(
                actor=actor,
                evidence=evidence,
                input_ledger_sha256=action["input_ledger_sha256"],
                recovery_manifest_digest=manifest_digest,
                action_sequence=action["sequence"],
            )
            return _migration_identity(document, ledger_path)
        if current_sha != action["input_ledger_sha256"]:
            raise LegacyRecoveryError(
                f"legacy recovery input digest changed for {action['run_id']}"
            )
        _content, _envelope, payload = _read_enveloped_ledger(ledger_path)
        if (
            payload.get("schema") != action["ledger_schema"]
            or payload.get("run_id") != action["run_id"]
        ):
            raise LegacyRecoveryError(
                "legacy recovery retirement input contradicts manifest"
            )
        retired, _replayed = RetirementStore(ledger_path, binding).retire(
            ledger_sha256=action["input_ledger_sha256"],
            ledger_schema=action["ledger_schema"],
            actor=actor,
            evidence=evidence,
            reason=action["reason"],
            successor_run_id=action["successor_run_id"],
            manifest_digest=manifest_digest,
            action_sequence=action["sequence"],
        )
        return {
            "ledger_sha256": current_sha,
            "retirement_event_hash": retired["event_hash"],
        }


def apply_recovery_manifest(
    *,
    repository: str | Path,
    manifest_path: str | Path,
    manifest_digest: str,
    actor: str,
    evidence: str,
    crash_hook: Callable[[str, int | None], None] | None = None,
) -> dict[str, Any]:
    """Apply or exactly replay one immutable recovery intent."""

    _root, binding, manifest = load_recovery_manifest(
        repository=repository,
        manifest_path=manifest_path,
        manifest_digest=manifest_digest,
    )
    common = Path(binding["git_common_dir"])
    scheduler_lock = common / SCHEDULER_LOCK_RELATIVE_PATH
    recovery_lock = common / RECOVERY_LOCK_RELATIVE_PATH
    state_root = common / RECOVERY_STATE_RELATIVE_PATH
    intent_path = state_root / "intents" / f"{manifest_digest}.json"
    progress_path = state_root / "progress" / f"{manifest_digest}.json"
    for state_path in (scheduler_lock, recovery_lock, intent_path, progress_path):
        _assert_git_state_path(binding, state_path)
    actor = _require_text(actor, field="actor")
    evidence = _require_text(evidence, field="evidence")
    hook = crash_hook or (lambda _phase, _sequence: None)
    with _locked(scheduler_lock, label="repository scheduler"), _locked(
        recovery_lock, label="application"
    ):
        intent = _intent_payload(manifest, actor=actor, evidence=evidence)
        intent_replayed = _persist_intent(intent_path, intent, manifest)
        hook("after-intent", None)
        intent_digest = _digest(intent)
        progress = _load_wrapped(progress_path, label="application progress")
        if progress is None:
            progress = {
                "schema": PROGRESS_SCHEMA,
                "intent_digest": intent_digest,
                "receipts": [],
            }
        _validate_progress(
            progress, intent_digest=intent_digest, actions=manifest["actions"]
        )
        receipts = progress["receipts"]
        for action in manifest["actions"]:
            sequence = action["sequence"]
            if sequence <= len(receipts):
                _verify_action_state(
                    binding=binding,
                    action=action,
                    actor=actor,
                    evidence=evidence,
                    manifest_digest=manifest_digest,
                    expected_identity=receipts[sequence - 1]["result_identity"],
                )
                continue
            hook("before-action-write", sequence)
            identity = _apply_action(
                binding=binding,
                action=action,
                actor=actor,
                evidence=evidence,
                manifest_digest=manifest_digest,
            )
            hook("after-action-write", sequence)
            receipt = {
                "schema": 1,
                "sequence": sequence,
                "run_id": action["run_id"],
                "action": action["action"],
                "input_ledger_sha256": action["input_ledger_sha256"],
                "result_identity": identity,
                "previous_receipt_hash": (
                    receipts[-1]["receipt_hash"] if receipts else "0" * 64
                ),
            }
            receipt["receipt_hash"] = _receipt_hash(receipt)
            receipts.append(receipt)
            _validate_progress(
                progress,
                intent_digest=intent_digest,
                actions=manifest["actions"],
            )
            _write_atomic(progress_path, _wrapped(progress))
            hook("after-progress-write", sequence)
        return {
            "manifest_digest": manifest_digest,
            "intent_path": str(intent_path),
            "intent_replayed": intent_replayed,
            "progress_path": str(progress_path),
            "status": "completed",
            "receipts": copy.deepcopy(receipts),
            "summary": {
                "migrated": sum(
                    action["action"] == "migrate" for action in manifest["actions"]
                ),
                "retired": sum(
                    action["action"] == "retire" for action in manifest["actions"]
                ),
            },
        }


def recovery_manifest_status(
    *,
    repository: str | Path,
    manifest_path: str | Path,
    manifest_digest: str,
) -> dict[str, Any]:
    """Project migrated, retired, failed, and untouched without mutation."""

    _root, binding, manifest = load_recovery_manifest(
        repository=repository,
        manifest_path=manifest_path,
        manifest_digest=manifest_digest,
    )
    common = Path(binding["git_common_dir"])
    intent_path = (
        common / RECOVERY_STATE_RELATIVE_PATH / "intents" / f"{manifest_digest}.json"
    )
    intent = _load_wrapped(intent_path, label="application intent")
    if intent is not None:
        _validate_intent(intent, manifest)
    actor = intent.get("actor") if isinstance(intent, dict) else None
    evidence = intent.get("evidence") if isinstance(intent, dict) else None
    results: list[dict[str, Any]] = []
    for action in manifest["actions"]:
        ledger_path = _ledger_path(binding, action["run_id"])
        try:
            current_sha = _file_sha256(ledger_path)
            if intent is not None:
                try:
                    identity = _verify_action_state(
                        binding=binding,
                        action=action,
                        actor=actor,
                        evidence=evidence,
                        manifest_digest=manifest_digest,
                    )
                except (LegacyRecoveryError, LedgerError, OSError):
                    _content, _envelope, payload = _read_enveloped_ledger(ledger_path)
                    sidecar = ledger_path.parent / RETIREMENT_FILE
                    untouched = (
                        current_sha == action["input_ledger_sha256"]
                        and payload.get("schema") == action["ledger_schema"]
                        and (
                            action["action"] == "migrate"
                            or not sidecar.exists()
                        )
                    )
                    if not untouched:
                        raise
                    results.append(
                        {"run_id": action["run_id"], "status": "untouched"}
                    )
                    continue
                state = "migrated" if action["action"] == "migrate" else "retired"
                results.append(
                    {"run_id": action["run_id"], "status": state, "identity": identity}
                )
            elif current_sha == action["input_ledger_sha256"]:
                if (
                    action["action"] == "retire"
                    and (ledger_path.parent / RETIREMENT_FILE).exists()
                ):
                    raise LegacyRecoveryError(
                        "retirement exists without this exact recovery intent"
                    )
                results.append({"run_id": action["run_id"], "status": "untouched"})
            else:
                raise LegacyRecoveryError("ledger changed without exact recovery intent")
        except (LegacyRecoveryError, LedgerError, OSError) as error:
            results.append(
                {"run_id": action["run_id"], "status": "failed", "reason": str(error)}
            )
    return {
        "manifest_digest": manifest_digest,
        "intent": "persisted" if intent is not None else "absent",
        "runs": results,
        "summary": {
            state: sum(item["status"] == state for item in results)
            for state in ("migrated", "retired", "failed", "untouched")
        },
    }


def revoke_legacy_retirement(
    *,
    repository: str | Path,
    run_id: str,
    actor: str,
    evidence: str,
    reason: str,
) -> dict[str, Any]:
    """Append one explicit revocation; it grants no replacement authority."""

    _root, binding = _binding(repository)
    run_id = _safe_run_id(run_id)
    common = Path(binding["git_common_dir"])
    ledger_path = _ledger_path(binding, run_id)
    for state_path in (
        common / SCHEDULER_LOCK_RELATIVE_PATH,
        common / RECOVERY_LOCK_RELATIVE_PATH,
        ledger_path.parent / RETIREMENT_FILE,
    ):
        _assert_git_state_path(binding, state_path)
    with _locked(
        common / SCHEDULER_LOCK_RELATIVE_PATH, label="repository scheduler"
    ), _locked(common / RECOVERY_LOCK_RELATIVE_PATH, label="application"), AtomicLedger(
        ledger_path
    ).run_locked():
        event = RetirementStore(ledger_path, binding).revoke(
            actor=actor, evidence=evidence, reason=reason
        )
    return {
        "run_id": run_id,
        "status": "revoked",
        "revocation": event,
        "ledger_sha256": _file_sha256(ledger_path),
    }
