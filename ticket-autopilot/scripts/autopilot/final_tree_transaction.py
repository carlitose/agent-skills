from __future__ import annotations

import hashlib
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Callable, Mapping

from .final_tree_projection import (
    NON_AUTHORITY,
    _git,
    _git_text,
    _raw_diff_rows,
    canonical_bytes,
    canonical_digest,
    copy_json,
    validate_manifest,
)
from .link_repoint import repoint_bytes


TRANSACTION_CONTRACT = "tracked-final-tree-projection-transaction-v1"
TRANSACTION_CONTRACT_VERSION = 1
TRANSACTION_STEP = "final-tree-projection-transaction"
QUALITY_STEP = "final-tree-projection-quality"
PROJECTION_HISTORY_STEP = "final-tree-projection-history"
QUALITY_CONTRACT = "tracked-final-tree-projection-quality-v1"
FINAL_QUALITY_STAGES = (
    "review",
    "qa-plan",
    "qa-execute",
    "verify",
    "finalize",
)
CHECKPOINTS = ("intent-persisted", "effects-read-back", "final-tree-bound")
_OID = re.compile(r"^[0-9a-f]{40,64}$")


class FinalTreeTransactionError(RuntimeError):
    pass


def _checkpoint_key(
    transaction_id: str, name: str, payload: Mapping[str, Any]
) -> str:
    return canonical_digest(
        {
            "transaction_id": transaction_id,
            "name": name,
            "payload": dict(payload),
        }
    )


def _manifest_reference(value: object) -> dict[str, Any]:
    fields = {
        "schema",
        "artifact",
        "sha256",
        "manifest_digest",
        "mode",
        "contract_version",
        "implementation_candidate_ref",
        "planned_delivery_candidate_ref",
    }
    if (
        not isinstance(value, dict)
        or set(value) != fields
        or value.get("schema") != 1
        or not isinstance(value.get("artifact"), str)
        or not value["artifact"]
        or not re.fullmatch(r"[0-9a-f]{64}", str(value.get("sha256")))
        or not re.fullmatch(
            r"[0-9a-f]{64}", str(value.get("manifest_digest"))
        )
        or value.get("mode") != "enabled"
        or value.get("contract_version") != 1
        or not isinstance(value.get("implementation_candidate_ref"), dict)
        or not isinstance(value.get("planned_delivery_candidate_ref"), dict)
    ):
        raise FinalTreeTransactionError(
            "projection transaction manifest reference is invalid"
        )
    return copy_json(value)


def projection_transaction_reference(
    manifest: Mapping[str, Any], *, artifact: str, sha256: str
) -> dict[str, Any]:
    normalized = validate_manifest(dict(manifest))
    if normalized["configuration"]["mode"] != "enabled":
        raise FinalTreeTransactionError(
            "projection transaction requires enabled mode"
        )
    return _manifest_reference(
        {
            "schema": 1,
            "artifact": artifact,
            "sha256": sha256,
            "manifest_digest": normalized["manifest_digest"],
            "mode": "enabled",
            "contract_version": normalized["contract_version"],
            "implementation_candidate_ref": normalized[
                "implementation_candidate_ref"
            ],
            "planned_delivery_candidate_ref": normalized[
                "planned_delivery_candidate_ref"
            ],
        }
    )


_EFFECT_BINDING_FIELDS = (
    "effect_key",
    "kind",
    "path",
    "old_mode",
    "new_mode",
    "old_oid",
    "new_oid",
)
_EFFECT_EXTRA_FIELDS = {
    "ticket-delete": ("destination",),
    "ticket-add": ("source",),
    "completion-receipt-add": (),
    "link-repoint": ("source", "destination"),
}


def _effect_binding(effect: Mapping[str, Any]) -> dict[str, Any]:
    fields = _EFFECT_BINDING_FIELDS + _EFFECT_EXTRA_FIELDS[effect["kind"]]
    return {key: effect[key] for key in fields}


def _valid_effect_binding(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    kind = value.get("kind")
    if not isinstance(kind, str) or kind not in _EFFECT_EXTRA_FIELDS:
        return False
    fields = set(_EFFECT_BINDING_FIELDS)
    fields.update(_EFFECT_EXTRA_FIELDS[kind])
    payload = {key: item for key, item in value.items() if key != "effect_key"}
    return (
        set(value) == fields
        and re.fullmatch(r"[0-9a-f]{64}", str(value.get("effect_key")))
        is not None
        and isinstance(value.get("path"), str)
        and bool(value["path"])
        and re.fullmatch(r"[0-7]{6}", str(value.get("old_mode"))) is not None
        and re.fullmatch(r"[0-7]{6}", str(value.get("new_mode"))) is not None
        and _OID.fullmatch(str(value.get("old_oid"))) is not None
        and _OID.fullmatch(str(value.get("new_oid"))) is not None
        and all(
            isinstance(value.get(field), str) and bool(value[field])
            for field in _EFFECT_EXTRA_FIELDS.get(kind, ())
        )
        and value["effect_key"] == canonical_digest(payload)
    )


def new_projection_transaction(
    manifest_reference: Mapping[str, Any], manifest_value: Mapping[str, Any]
) -> dict[str, Any]:
    manifest = validate_manifest(dict(manifest_value))
    reference = _manifest_reference(dict(manifest_reference))
    if (
        manifest["configuration"]["mode"] != "enabled"
        or reference["manifest_digest"] != manifest["manifest_digest"]
        or reference["implementation_candidate_ref"]
        != manifest["implementation_candidate_ref"]
        or reference["planned_delivery_candidate_ref"]
        != manifest["planned_delivery_candidate_ref"]
    ):
        raise FinalTreeTransactionError(
            "projection transaction manifest binding is contradictory"
        )
    bindings = [_effect_binding(effect) for effect in manifest["effects"]]
    identity = {
        "contract": TRANSACTION_CONTRACT,
        "contract_version": TRANSACTION_CONTRACT_VERSION,
        "run_id": manifest["run_id"],
        "ticket_id": manifest["ticket_id"],
        "artifact_generation": manifest["artifact_generation"],
        "manifest_digest": manifest["manifest_digest"],
        "expected_diff_digest": canonical_digest(manifest["expected_diff"]),
        "implementation_candidate_ref": manifest[
            "implementation_candidate_ref"
        ],
        "planned_delivery_candidate_ref": manifest[
            "planned_delivery_candidate_ref"
        ],
        "effect_keys": [item["effect_key"] for item in bindings],
    }
    transaction_id = canonical_digest(identity)
    intent_payload = {
        "manifest_digest": manifest["manifest_digest"],
        "expected_index_tree_oid": manifest[
            "implementation_candidate_ref"
        ]["candidate_tree_oid"],
        "source_path": manifest["ticket"]["source_path"],
        "destination_path": manifest["ticket"]["destination_path"],
    }
    intent = {
        **intent_payload,
        "checkpoint_key": _checkpoint_key(
            transaction_id, "intent-persisted", intent_payload
        ),
    }
    document = {
        "schema": 1,
        "contract": TRANSACTION_CONTRACT,
        "contract_version": TRANSACTION_CONTRACT_VERSION,
        "transaction_id": transaction_id,
        "run_id": manifest["run_id"],
        "ticket_id": manifest["ticket_id"],
        "artifact_generation": manifest["artifact_generation"],
        "manifest": reference,
        "implementation_candidate_ref": manifest[
            "implementation_candidate_ref"
        ],
        "planned_delivery_candidate_ref": manifest[
            "planned_delivery_candidate_ref"
        ],
        "expected_index_tree_oid": manifest[
            "implementation_candidate_ref"
        ]["candidate_tree_oid"],
        "expected_diff_digest": canonical_digest(manifest["expected_diff"]),
        "effect_bindings": bindings,
        "effects_applied": [],
        "active_effect": None,
        "checkpoints": {
            "intent-persisted": intent,
            "effects-read-back": None,
            "final-tree-bound": None,
        },
        "status": "intent-persisted",
        "authority": dict(NON_AUTHORITY),
    }
    return validate_projection_transaction(document)


def _validate_candidate(value: object, field: str) -> dict[str, Any]:
    required = {
        "contract_version",
        "base_tree_oid",
        "candidate_tree_oid",
        "ticket_digest",
    }
    if (
        not isinstance(value, dict)
        or set(value) != required
        or value.get("contract_version") != 2
        or not _OID.fullmatch(str(value.get("base_tree_oid")))
        or not _OID.fullmatch(str(value.get("candidate_tree_oid")))
        or not re.fullmatch(r"[0-9a-f]{64}", str(value.get("ticket_digest")))
    ):
        raise FinalTreeTransactionError(f"{field} is invalid")
    return value


def validate_projection_transaction(value: object) -> dict[str, Any]:
    fields = {
        "schema",
        "contract",
        "contract_version",
        "transaction_id",
        "run_id",
        "ticket_id",
        "artifact_generation",
        "manifest",
        "implementation_candidate_ref",
        "planned_delivery_candidate_ref",
        "expected_index_tree_oid",
        "expected_diff_digest",
        "effect_bindings",
        "effects_applied",
        "active_effect",
        "checkpoints",
        "status",
        "authority",
    }
    if not isinstance(value, dict) or set(value) != fields:
        raise FinalTreeTransactionError(
            "projection transaction shape is invalid"
        )
    if (
        value.get("schema") != 1
        or value.get("contract") != TRANSACTION_CONTRACT
        or value.get("contract_version") != TRANSACTION_CONTRACT_VERSION
        or not re.fullmatch(r"[0-9a-f]{64}", str(value.get("transaction_id")))
        or not isinstance(value.get("run_id"), str)
        or not value["run_id"]
        or not isinstance(value.get("ticket_id"), str)
        or not value["ticket_id"]
        or not isinstance(value.get("artifact_generation"), int)
        or value["artifact_generation"] < 0
        or value.get("authority") != NON_AUTHORITY
    ):
        raise FinalTreeTransactionError(
            "projection transaction identity is invalid"
        )
    reference = _manifest_reference(value.get("manifest"))
    implementation = _validate_candidate(
        value.get("implementation_candidate_ref"),
        "projection transaction implementation CandidateRef",
    )
    delivery = _validate_candidate(
        value.get("planned_delivery_candidate_ref"),
        "projection transaction delivery CandidateRef",
    )
    if (
        reference["implementation_candidate_ref"] != implementation
        or reference["planned_delivery_candidate_ref"] != delivery
        or value.get("expected_index_tree_oid")
        != implementation["candidate_tree_oid"]
        or not re.fullmatch(
            r"[0-9a-f]{64}", str(value.get("expected_diff_digest"))
        )
        or implementation["base_tree_oid"] != delivery["base_tree_oid"]
        or implementation["ticket_digest"] != delivery["ticket_digest"]
    ):
        raise FinalTreeTransactionError(
            "projection transaction CandidateRef binding is invalid"
        )
    bindings = value.get("effect_bindings")
    if (
        not isinstance(bindings, list)
        or not bindings
        or any(not _valid_effect_binding(item) for item in bindings)
        or len({item["effect_key"] for item in bindings}) != len(bindings)
    ):
        raise FinalTreeTransactionError(
            "projection transaction effect bindings are invalid"
        )
    identity = {
        "contract": TRANSACTION_CONTRACT,
        "contract_version": TRANSACTION_CONTRACT_VERSION,
        "run_id": value["run_id"],
        "ticket_id": value["ticket_id"],
        "artifact_generation": value["artifact_generation"],
        "manifest_digest": reference["manifest_digest"],
        "expected_diff_digest": value["expected_diff_digest"],
        "implementation_candidate_ref": implementation,
        "planned_delivery_candidate_ref": delivery,
        "effect_keys": [item["effect_key"] for item in bindings],
    }
    if value["transaction_id"] != canonical_digest(identity):
        raise FinalTreeTransactionError(
            "projection transaction digest is invalid"
        )
    checkpoints = value.get("checkpoints")
    if not isinstance(checkpoints, dict) or set(checkpoints) != set(CHECKPOINTS):
        raise FinalTreeTransactionError(
            "projection transaction checkpoints are invalid"
        )
    intent = checkpoints["intent-persisted"]
    intent_fields = {
        "manifest_digest",
        "expected_index_tree_oid",
        "source_path",
        "destination_path",
        "checkpoint_key",
    }
    if not isinstance(intent, dict) or set(intent) != intent_fields:
        raise FinalTreeTransactionError(
            "projection transaction intent checkpoint is invalid"
        )
    intent_payload = {
        key: intent[key] for key in intent_fields if key != "checkpoint_key"
    }
    if (
        intent["manifest_digest"] != reference["manifest_digest"]
        or intent["expected_index_tree_oid"] != value["expected_index_tree_oid"]
        or intent["checkpoint_key"]
        != _checkpoint_key(
            value["transaction_id"], "intent-persisted", intent_payload
        )
    ):
        raise FinalTreeTransactionError(
            "projection transaction intent identity is invalid"
        )
    applied = value.get("effects_applied")
    effect_record_fields = {"effect_key", "checkpoint_key", "readback"}
    readback_fields = {
        "path",
        "mode",
        "oid",
        "index_tree_oid",
        "worktree_sha256",
    }
    if not isinstance(applied, list) or len(applied) > len(bindings):
        raise FinalTreeTransactionError(
            "projection transaction applied effects are invalid"
        )
    for index, record in enumerate(applied):
        binding = bindings[index]
        if (
            not isinstance(record, dict)
            or set(record) != effect_record_fields
            or record.get("effect_key") != binding["effect_key"]
            or not isinstance(record.get("readback"), dict)
            or set(record["readback"]) != readback_fields
        ):
            raise FinalTreeTransactionError(
                "projection transaction effect history is invalid"
            )
        readback = record["readback"]
        absent = binding["new_mode"] == "000000"
        if (
            readback["path"] != binding["path"]
            or readback["mode"] != binding["new_mode"]
            or readback["oid"] != binding["new_oid"]
            or not _OID.fullmatch(str(readback["index_tree_oid"]))
            or (
                absent
                and readback["worktree_sha256"] is not None
            )
            or (
                not absent
                and not re.fullmatch(
                    r"[0-9a-f]{64}",
                    str(readback["worktree_sha256"]),
                )
            )
            or record["checkpoint_key"]
            != _checkpoint_key(
                value["transaction_id"],
                f"effect-read-back:{binding['effect_key']}",
                readback,
            )
        ):
            raise FinalTreeTransactionError(
                "projection transaction effect readback is invalid"
            )
    active = value.get("active_effect")
    if active is not None:
        if len(applied) >= len(bindings):
            raise FinalTreeTransactionError(
                "projection transaction active effect is impossible"
            )
        payload = {"effect_key": bindings[len(applied)]["effect_key"]}
        if (
            not isinstance(active, dict)
            or set(active) != {"effect_key", "checkpoint_key"}
            or active["effect_key"] != payload["effect_key"]
            or active["checkpoint_key"]
            != _checkpoint_key(
                value["transaction_id"],
                f"effect-started:{payload['effect_key']}",
                payload,
            )
        ):
            raise FinalTreeTransactionError(
                "projection transaction active effect is invalid"
            )
    effects_checkpoint = checkpoints["effects-read-back"]
    if effects_checkpoint is not None:
        fields = {
            "actual_tree_oid",
            "actual_diff_digest",
            "effect_keys_digest",
            "checkpoint_key",
        }
        if not isinstance(effects_checkpoint, dict) or set(effects_checkpoint) != fields:
            raise FinalTreeTransactionError(
                "projection transaction effects checkpoint is invalid"
            )
        payload = {
            key: effects_checkpoint[key]
            for key in fields
            if key != "checkpoint_key"
        }
        if (
            len(applied) != len(bindings)
            or active is not None
            or effects_checkpoint["actual_tree_oid"]
            != delivery["candidate_tree_oid"]
            or effects_checkpoint["actual_diff_digest"]
            != value["expected_diff_digest"]
            or effects_checkpoint["effect_keys_digest"]
            != canonical_digest([item["effect_key"] for item in bindings])
            or effects_checkpoint["checkpoint_key"]
            != _checkpoint_key(
                value["transaction_id"], "effects-read-back", payload
            )
        ):
            raise FinalTreeTransactionError(
                "projection transaction effects checkpoint identity is invalid"
            )
    final_checkpoint = checkpoints["final-tree-bound"]
    if final_checkpoint is not None:
        fields = {"candidate_ref", "checkpoint_key"}
        if not isinstance(final_checkpoint, dict) or set(final_checkpoint) != fields:
            raise FinalTreeTransactionError(
                "projection transaction final-tree checkpoint is invalid"
            )
        payload = {"candidate_ref": final_checkpoint["candidate_ref"]}
        if (
            effects_checkpoint is None
            or final_checkpoint["candidate_ref"] != delivery
            or final_checkpoint["checkpoint_key"]
            != _checkpoint_key(
                value["transaction_id"], "final-tree-bound", payload
            )
        ):
            raise FinalTreeTransactionError(
                "projection transaction final-tree binding is invalid"
            )
    expected_status = (
        "projected-not-integrated"
        if final_checkpoint is not None
        else "effects-read-back"
        if effects_checkpoint is not None
        else "effects-applying"
        if applied or active is not None
        else "intent-persisted"
    )
    if value.get("status") != expected_status:
        raise FinalTreeTransactionError(
            "projection transaction status is invalid"
        )
    return copy_json(value)


def record_effect_started(
    transaction_value: Mapping[str, Any], effect_key: str
) -> tuple[dict[str, Any], bool]:
    transaction = validate_projection_transaction(dict(transaction_value))
    applied = transaction["effects_applied"]
    bindings = transaction["effect_bindings"]
    if len(applied) >= len(bindings):
        raise FinalTreeTransactionError(
            "projection transaction has no remaining effect"
        )
    expected_key = bindings[len(applied)]["effect_key"]
    if effect_key != expected_key:
        raise FinalTreeTransactionError(
            "projection transaction effect order is contradictory"
        )
    payload = {"effect_key": effect_key}
    record = {
        **payload,
        "checkpoint_key": _checkpoint_key(
            transaction["transaction_id"],
            f"effect-started:{effect_key}",
            payload,
        ),
    }
    if transaction["active_effect"] == record:
        return transaction, False
    if transaction["active_effect"] is not None:
        raise FinalTreeTransactionError(
            "projection transaction active effect is immutable"
        )
    updated = copy_json(transaction)
    updated["active_effect"] = record
    updated["status"] = "effects-applying"
    return validate_projection_transaction(updated), True


def record_effect_readback(
    transaction_value: Mapping[str, Any],
    effect_key: str,
    readback: Mapping[str, Any],
) -> tuple[dict[str, Any], bool]:
    transaction = validate_projection_transaction(dict(transaction_value))
    bindings = transaction["effect_bindings"]
    applied = transaction["effects_applied"]
    existing = next(
        (item for item in applied if item["effect_key"] == effect_key),
        None,
    )
    if existing is not None:
        if existing["readback"] == dict(readback):
            return transaction, False
        raise FinalTreeTransactionError(
            "projection transaction effect history is immutable"
        )
    if len(applied) >= len(bindings):
        raise FinalTreeTransactionError(
            "projection transaction effect history is immutable"
        )
    expected = bindings[len(applied)]
    if (
        expected["effect_key"] != effect_key
        or not isinstance(transaction["active_effect"], dict)
        or transaction["active_effect"].get("effect_key") != effect_key
    ):
        raise FinalTreeTransactionError(
            "projection transaction effect order is contradictory"
        )
    normalized_readback = dict(readback)
    record = {
        "effect_key": effect_key,
        "checkpoint_key": _checkpoint_key(
            transaction["transaction_id"],
            f"effect-read-back:{effect_key}",
            normalized_readback,
        ),
        "readback": normalized_readback,
    }
    updated = copy_json(transaction)
    updated["effects_applied"].append(record)
    updated["active_effect"] = None
    updated["status"] = "effects-applying"
    return validate_projection_transaction(updated), True


def record_effects_checkpoint(
    transaction_value: Mapping[str, Any],
    *,
    actual_tree_oid: str,
    actual_diff_digest: str,
) -> tuple[dict[str, Any], bool]:
    transaction = validate_projection_transaction(dict(transaction_value))
    existing = transaction["checkpoints"]["effects-read-back"]
    payload = {
        "actual_tree_oid": actual_tree_oid,
        "actual_diff_digest": actual_diff_digest,
        "effect_keys_digest": canonical_digest(
            [item["effect_key"] for item in transaction["effect_bindings"]]
        ),
    }
    record = {
        **payload,
        "checkpoint_key": _checkpoint_key(
            transaction["transaction_id"], "effects-read-back", payload
        ),
    }
    if existing == record:
        return transaction, False
    if existing is not None:
        raise FinalTreeTransactionError(
            "projection transaction effects checkpoint is immutable"
        )
    updated = copy_json(transaction)
    updated["checkpoints"]["effects-read-back"] = record
    updated["status"] = "effects-read-back"
    return validate_projection_transaction(updated), True


def record_final_tree_checkpoint(
    transaction_value: Mapping[str, Any], candidate_ref: Mapping[str, Any]
) -> tuple[dict[str, Any], bool]:
    transaction = validate_projection_transaction(dict(transaction_value))
    candidate = copy_json(dict(candidate_ref))
    payload = {"candidate_ref": candidate}
    record = {
        **payload,
        "checkpoint_key": _checkpoint_key(
            transaction["transaction_id"], "final-tree-bound", payload
        ),
    }
    existing = transaction["checkpoints"]["final-tree-bound"]
    if existing == record:
        return transaction, False
    if existing is not None:
        raise FinalTreeTransactionError(
            "projection transaction final-tree checkpoint is immutable"
        )
    updated = copy_json(transaction)
    updated["checkpoints"]["final-tree-bound"] = record
    updated["status"] = "projected-not-integrated"
    return validate_projection_transaction(updated), True


def final_quality_checkpoint(
    transaction_value: Mapping[str, Any],
    candidate_ref: Mapping[str, Any],
    *,
    artifact_generation: int,
) -> dict[str, Any]:
    transaction = validate_projection_transaction(dict(transaction_value))
    candidate = copy_json(dict(candidate_ref))
    if (
        transaction["status"] != "projected-not-integrated"
        or candidate != transaction["planned_delivery_candidate_ref"]
        or not isinstance(artifact_generation, int)
        or isinstance(artifact_generation, bool)
        or artifact_generation <= transaction["artifact_generation"]
    ):
        raise FinalTreeTransactionError(
            "projection final-quality binding is contradictory"
        )
    payload = {
        "contract": QUALITY_CONTRACT,
        "transaction_id": transaction["transaction_id"],
        "candidate_ref": candidate,
        "artifact_generation": artifact_generation,
        "stages": list(FINAL_QUALITY_STAGES),
    }
    return {
        "schema": 1,
        **payload,
        "status": "quality-complete",
        "checkpoint_key": canonical_digest(payload),
        "authority": copy_json(NON_AUTHORITY),
    }


def validate_final_quality_checkpoint(value: object) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {
        "schema",
        "contract",
        "transaction_id",
        "candidate_ref",
        "artifact_generation",
        "stages",
        "status",
        "checkpoint_key",
        "authority",
    }:
        raise FinalTreeTransactionError(
            "projection final-quality checkpoint is invalid"
        )
    payload = {
        "contract": value.get("contract"),
        "transaction_id": value.get("transaction_id"),
        "candidate_ref": value.get("candidate_ref"),
        "artifact_generation": value.get("artifact_generation"),
        "stages": value.get("stages"),
    }
    if (
        value.get("schema") != 1
        or value.get("contract") != QUALITY_CONTRACT
        or not re.fullmatch(
            r"[0-9a-f]{64}", str(value.get("transaction_id"))
        )
        or not isinstance(value.get("candidate_ref"), dict)
        or not isinstance(value.get("artifact_generation"), int)
        or isinstance(value.get("artifact_generation"), bool)
        or value.get("artifact_generation") < 1
        or value.get("stages") != list(FINAL_QUALITY_STAGES)
        or value.get("status") != "quality-complete"
        or value.get("checkpoint_key") != canonical_digest(payload)
        or value.get("authority") != NON_AUTHORITY
    ):
        raise FinalTreeTransactionError(
            "projection final-quality checkpoint identity is invalid"
        )
    return copy_json(value)


def _index_entry(repo: Path, path: str) -> dict[str, str] | None:
    raw = _git(repo, "ls-files", "-s", "-z", "--", path)
    records = [item for item in raw.split(b"\0") if item]
    if not records:
        return None
    if len(records) != 1:
        raise FinalTreeTransactionError(
            f"projection transaction index entry is ambiguous: {path}"
        )
    metadata, separator, observed_path = records[0].partition(b"\t")
    if not separator or observed_path.decode("utf-8") != path:
        raise FinalTreeTransactionError(
            f"projection transaction index entry is malformed: {path}"
        )
    mode, oid, stage = metadata.decode("ascii").split()
    if stage != "0":
        raise FinalTreeTransactionError(
            f"projection transaction index entry is unmerged: {path}"
        )
    return {"mode": mode, "oid": oid}


def _worktree_bytes(repo: Path, path: str) -> bytes | None:
    target = repo / path
    current = repo
    for part in Path(path).parts:
        current = current / part
        if current.is_symlink():
            raise FinalTreeTransactionError(
                f"projection transaction path contains a symlink: {path}"
            )
    if not target.exists():
        return None
    if not target.is_file():
        raise FinalTreeTransactionError(
            f"projection transaction path is not a regular file: {path}"
        )
    return target.read_bytes()


def _worktree_mode(repo: Path, path: str) -> str | None:
    target = repo / path
    if not target.exists():
        return None
    return "100755" if target.stat().st_mode & 0o111 else "100644"


def _hash_blob(repo: Path, content: bytes, *, write: bool = False) -> str:
    arguments = ["hash-object"]
    if write:
        arguments.append("-w")
    arguments.append("--stdin")
    return _git_text(repo, *arguments, input_bytes=content)


def _cat_blob(repo: Path, oid: str) -> bytes:
    return _git(repo, "cat-file", "blob", oid)


def _effect_payload(
    repo: Path, manifest: Mapping[str, Any], effect: Mapping[str, Any]
) -> bytes | None:
    kind = effect["kind"]
    if kind == "ticket-delete":
        return None
    if kind == "ticket-add":
        payload = _cat_blob(repo, manifest["ticket"]["source_oid"])
    elif kind == "completion-receipt-add":
        payload = canonical_bytes(manifest["completion_receipt"]["document"])
    elif kind == "link-repoint":
        before = _cat_blob(repo, effect["old_oid"])
        payload = repoint_bytes(
            effect["path"],
            before,
            effect["source"],
            effect["destination"],
        )
    else:
        raise FinalTreeTransactionError(
            f"unknown projection transaction effect: {kind}"
        )
    if _hash_blob(repo, payload) != effect["new_oid"]:
        raise FinalTreeTransactionError(
            f"projection transaction payload identity changed: {effect['path']}"
        )
    return payload


def _atomic_write(path: Path, content: bytes, mode: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=path.name + ".", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o755 if mode == "100755" else 0o644)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _apply_effect(
    repo: Path, manifest: Mapping[str, Any], effect: Mapping[str, Any]
) -> None:
    path = effect["path"]
    index = _index_entry(repo, path)
    content = _worktree_bytes(repo, path)
    kind = effect["kind"]
    if kind == "ticket-delete":
        if index not in (
            None,
            {"mode": effect["old_mode"], "oid": effect["old_oid"]},
        ):
            raise FinalTreeTransactionError(
                f"projection transaction delete index drifted: {path}"
            )
        if content is not None and (
            _hash_blob(repo, content) != effect["old_oid"]
            or _worktree_mode(repo, path) != effect["old_mode"]
        ):
            raise FinalTreeTransactionError(
                f"projection transaction delete bytes or mode drifted: {path}"
            )
        if index is not None:
            _git(repo, "update-index", "--force-remove", "--", path)
        if content is not None:
            (repo / path).unlink()
        return
    payload = _effect_payload(repo, manifest, effect)
    assert payload is not None
    expected_new = {"mode": effect["new_mode"], "oid": effect["new_oid"]}
    allowed_index = [None, expected_new]
    if kind == "link-repoint":
        allowed_index.append(
            {"mode": effect["old_mode"], "oid": effect["old_oid"]}
        )
    if index not in allowed_index:
        raise FinalTreeTransactionError(
            f"projection transaction index drifted: {path}"
        )
    observed_oid = _hash_blob(repo, content) if content is not None else None
    allowed_content = {None, effect["new_oid"]}
    if kind == "link-repoint":
        allowed_content.add(effect["old_oid"])
    if observed_oid not in allowed_content:
        raise FinalTreeTransactionError(
            f"projection transaction worktree drifted: {path}"
        )
    observed_mode = _worktree_mode(repo, path)
    expected_mode = (
        effect["old_mode"]
        if observed_oid == effect["old_oid"]
        else effect["new_mode"]
        if observed_oid == effect["new_oid"]
        else None
    )
    if observed_mode != expected_mode:
        raise FinalTreeTransactionError(
            f"projection transaction worktree mode drifted: {path}"
        )
    stored_oid = _hash_blob(repo, payload, write=True)
    if stored_oid != effect["new_oid"]:
        raise FinalTreeTransactionError(
            f"projection transaction object write drifted: {path}"
        )
    if observed_oid != effect["new_oid"]:
        _atomic_write(repo / path, payload, effect["new_mode"])
    if index != expected_new:
        _git(
            repo,
            "update-index",
            "--add",
            "--cacheinfo",
            effect["new_mode"],
            effect["new_oid"],
            path,
        )


def _effect_readback(repo: Path, effect: Mapping[str, Any]) -> dict[str, Any]:
    path = effect["path"]
    index = _index_entry(repo, path)
    content = _worktree_bytes(repo, path)
    absent = effect["new_mode"] == "000000"
    if absent:
        if index is not None or content is not None:
            raise FinalTreeTransactionError(
                f"projection transaction delete readback failed: {path}"
            )
        worktree_sha = None
    else:
        expected = {"mode": effect["new_mode"], "oid": effect["new_oid"]}
        if (
            index != expected
            or content is None
            or _hash_blob(repo, content) != effect["new_oid"]
            or _worktree_mode(repo, path) != effect["new_mode"]
        ):
            raise FinalTreeTransactionError(
                f"projection transaction effect readback failed: {path}"
            )
        worktree_sha = hashlib.sha256(content).hexdigest()
    return {
        "path": path,
        "mode": effect["new_mode"],
        "oid": effect["new_oid"],
        "index_tree_oid": _git_text(repo, "write-tree"),
        "worktree_sha256": worktree_sha,
    }


def _assert_ticket_topology(
    repo: Path,
    manifest: Mapping[str, Any],
    transaction: Mapping[str, Any],
) -> None:
    source = manifest["ticket"]["source_path"]
    destination = manifest["ticket"]["destination_path"]
    source_present = _worktree_bytes(repo, source) is not None
    destination_present = _worktree_bytes(repo, destination) is not None
    if source_present and destination_present:
        raise FinalTreeTransactionError(
            "projection transaction found both source and destination"
        )
    by_kind = {
        effect["kind"]: effect["effect_key"]
        for effect in manifest["effects"]
        if effect["kind"] in {"ticket-delete", "ticket-add"}
    }
    applied = {
        item["effect_key"] for item in transaction["effects_applied"]
    }
    active = transaction.get("active_effect") or {}
    delete_started = (
        by_kind["ticket-delete"] in applied
        or active.get("effect_key") == by_kind["ticket-delete"]
    )
    add_started = (
        by_kind["ticket-add"] in applied
        or active.get("effect_key") == by_kind["ticket-add"]
    )
    if source_present and by_kind["ticket-delete"] in applied:
        raise FinalTreeTransactionError(
            "projection transaction source reappeared after delete"
        )
    if not source_present and not destination_present and not delete_started:
        raise FinalTreeTransactionError(
            "projection transaction found both source and destination absent"
        )
    if destination_present and not add_started:
        raise FinalTreeTransactionError(
            "projection transaction destination predates its add checkpoint"
        )


def _prefix_tree(transaction: Mapping[str, Any]) -> str:
    applied = transaction["effects_applied"]
    return (
        applied[-1]["readback"]["index_tree_oid"]
        if applied
        else transaction["expected_index_tree_oid"]
    )


def _assert_index_prefix(repo: Path, transaction: Mapping[str, Any]) -> None:
    expected = _prefix_tree(transaction)
    actual = _git_text(repo, "write-tree")
    active = transaction.get("active_effect")
    if active is None:
        if actual != expected:
            raise FinalTreeTransactionError(
                "projection transaction index differs from its persisted prefix"
            )
        return
    changed = {
        item.decode("utf-8")
        for item in _git(
            repo,
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            "-z",
            expected,
            actual,
        ).split(b"\0")
        if item
    }
    binding = transaction["effect_bindings"][
        len(transaction["effects_applied"])
    ]
    if active["effect_key"] != binding["effect_key"] or not changed.issubset(
        {binding["path"]}
    ):
        raise FinalTreeTransactionError(
            "projection transaction active index effect is contradictory"
        )


def _assert_no_unexpected_boundary(
    repo: Path, transaction: Mapping[str, Any]
) -> None:
    active = transaction.get("active_effect")
    active_binding = (
        transaction["effect_bindings"][len(transaction["effects_applied"])]
        if active is not None
        else None
    )
    effect_paths = {active_binding["path"]} if active_binding else set()
    unstaged = {
        item
        for item in _git(repo, "diff", "--name-only", "-z").split(b"\0")
        if item
    }
    decoded_unstaged = {item.decode("utf-8") for item in unstaged}
    if not decoded_unstaged.issubset(effect_paths):
        raise FinalTreeTransactionError(
            "projection transaction found unexpected unstaged paths"
        )
    untracked = {
        item.decode("utf-8")
        for item in _git(
            repo, "ls-files", "--others", "--exclude-standard", "-z"
        ).split(b"\0")
        if item
    }
    allowed_untracked = (
        {active_binding["path"]}
        if active_binding is not None
        and active_binding["old_mode"] == "000000"
        else set()
    )
    if not untracked.issubset(allowed_untracked):
        raise FinalTreeTransactionError(
            "projection transaction found unexpected untracked paths"
        )


def apply_projection_transaction(
    repo: Path,
    manifest_value: Mapping[str, Any],
    *,
    get_transaction: Callable[[], Mapping[str, Any]],
    persist_effect_started: Callable[[str], None],
    persist_effect: Callable[[str, Mapping[str, Any]], None],
    persist_effects_readback: Callable[[str, str], None],
    after_repository_effect: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    repo = repo.resolve()
    manifest = validate_manifest(dict(manifest_value))
    if manifest["configuration"]["mode"] != "enabled":
        raise FinalTreeTransactionError(
            "projection transaction requires enabled mode"
        )
    transaction = validate_projection_transaction(dict(get_transaction()))
    replaying_final = transaction["status"] == "projected-not-integrated"
    if (
        transaction["manifest"]["manifest_digest"]
        != manifest["manifest_digest"]
        or transaction["effect_bindings"]
        != [_effect_binding(effect) for effect in manifest["effects"]]
    ):
        raise FinalTreeTransactionError(
            "projection transaction state contradicts its manifest"
        )
    _assert_index_prefix(repo, transaction)
    _assert_ticket_topology(repo, manifest, transaction)
    _assert_no_unexpected_boundary(repo, transaction)
    for effect in manifest["effects"]:
        transaction = validate_projection_transaction(dict(get_transaction()))
        recorded = next(
            (
                item
                for item in transaction["effects_applied"]
                if item["effect_key"] == effect["effect_key"]
            ),
            None,
        )
        if recorded is None:
            active = transaction.get("active_effect")
            if active is None:
                _assert_index_prefix(repo, transaction)
                _assert_ticket_topology(repo, manifest, transaction)
                _assert_no_unexpected_boundary(repo, transaction)
                persist_effect_started(effect["effect_key"])
                transaction = validate_projection_transaction(
                    dict(get_transaction())
                )
                active = transaction["active_effect"]
            if active.get("effect_key") != effect["effect_key"]:
                raise FinalTreeTransactionError(
                    "projection transaction active effect order is contradictory"
                )
            _assert_index_prefix(repo, transaction)
            _assert_ticket_topology(repo, manifest, transaction)
            _assert_no_unexpected_boundary(repo, transaction)
            _apply_effect(repo, manifest, effect)
            if after_repository_effect is not None:
                after_repository_effect(effect["effect_key"])
            readback = _effect_readback(repo, effect)
            persist_effect(effect["effect_key"], readback)
        else:
            current = _effect_readback(repo, effect)
            if any(
                current[key] != recorded["readback"][key]
                for key in ("path", "mode", "oid", "worktree_sha256")
            ):
                raise FinalTreeTransactionError(
                    "projection transaction replay readback drifted"
                )
    actual_tree = _git_text(repo, "write-tree")
    if actual_tree != manifest["planned_delivery_candidate_ref"]["candidate_tree_oid"]:
        raise FinalTreeTransactionError(
            "projection transaction final index tree differs from planned D"
        )
    rows = _raw_diff_rows(
        repo,
        manifest["implementation_candidate_ref"]["candidate_tree_oid"],
        actual_tree,
    )
    if rows != manifest["expected_diff"]:
        raise FinalTreeTransactionError(
            "projection transaction final I-to-D proof differs from manifest"
        )
    unstaged = subprocess.run(
        ["git", "diff", "--quiet", "--"], cwd=repo, check=False
    )
    if unstaged.returncode != 0:
        if unstaged.returncode != 1:
            raise FinalTreeTransactionError(
                "projection transaction could not read back the worktree"
            )
        raise FinalTreeTransactionError(
            "projection transaction worktree differs from its final index"
        )
    untracked = _git(repo, "ls-files", "--others", "--exclude-standard", "-z")
    if untracked:
        raise FinalTreeTransactionError(
            "projection transaction left untracked repository paths"
        )
    persist_effects_readback(actual_tree, canonical_digest(rows))
    return {
        "result": "already-applied" if replaying_final else "applied",
        "candidate_ref": copy_json(
            manifest["planned_delivery_candidate_ref"]
        ),
    }
