"""Content-addressed, resumable checkpoints for deterministic verification work."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path
from typing import Any, Callable, Mapping


PHASES = (
    "context-loaded",
    "bundle-built",
    "bundle-validated",
    "bundle-reduced",
    "handoff-ready",
)


class VerificationCheckpointError(RuntimeError):
    """A verification checkpoint cannot be trusted or produced."""


class CheckpointCorruption(VerificationCheckpointError):
    """Persisted content does not match its recorded content address."""


class CheckpointPhaseFailure(VerificationCheckpointError):
    """A deterministic phase failed after its trusted prefix was persisted."""

    def __init__(self, phase: str, error: Exception) -> None:
        self.phase = phase
        super().__init__(f"{phase} checkpoint failed: {error}")


@dataclass(frozen=True)
class Artifact:
    phase: str
    digest: str
    path: Path


@dataclass(frozen=True)
class CheckpointRun:
    candidate_hash: str
    input_hash: str
    artifacts: Mapping[str, Artifact]
    phases_executed: tuple[str, ...]
    handoff: Mapping[str, Any]
    cache_hit: bool
    leaf_interactions_consumed: int = 0


@dataclass(frozen=True)
class CheckpointStatus:
    candidate_hash: str
    input_hash: str
    phases_complete: tuple[str, ...]
    artifact_hashes: Mapping[str, str]
    complete: bool


def _canonical_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise VerificationCheckpointError(
            "checkpoint inputs and adapter outputs must be canonical JSON"
        ) from error


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _candidate_document(candidate_ref: Any) -> dict[str, Any]:
    if is_dataclass(candidate_ref):
        candidate_ref = asdict(candidate_ref)
    if not isinstance(candidate_ref, Mapping):
        raise VerificationCheckpointError("CandidateRef must be a mapping or dataclass")
    document = dict(candidate_ref)
    expected = {"contract_version", "base_sha", "tree_oid", "ticket_digest"}
    if set(document) != expected:
        raise VerificationCheckpointError("CandidateRef has an invalid shape")
    if type(document["contract_version"]) is not int or document["contract_version"] != 1:
        raise VerificationCheckpointError("unsupported CandidateRef contract_version")
    if any(
        not isinstance(document[name], str) or not document[name]
        for name in ("base_sha", "tree_oid", "ticket_digest")
    ):
        raise VerificationCheckpointError("CandidateRef fields must be non-empty strings")
    return document


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise CheckpointCorruption(f"unreadable checkpoint: {path.name}") from error


def _write_json_atomic(path: Path, value: Any) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    try:
        temporary.write_bytes(_canonical_bytes(value) + b"\n")
        temporary.replace(path)
    except OSError as error:
        raise VerificationCheckpointError(
            f"could not persist checkpoint: {path.name}"
        ) from error


def _load_artifact(
    path: Path,
    *,
    phase: str,
    candidate: Mapping[str, Any],
    input_hash: str,
    upstream_hash: str | None,
    expected_digest: str,
) -> dict[str, Any]:
    document = _read_json(path)
    if not isinstance(document, dict):
        raise CheckpointCorruption(f"checkpoint is not an object: {path.name}")
    recorded_digest = document.get("artifact_hash")
    payload = {key: value for key, value in document.items() if key != "artifact_hash"}
    actual_digest = _digest(payload)
    if (
        recorded_digest != actual_digest
        or recorded_digest != expected_digest
        or path.stem != actual_digest
    ):
        raise CheckpointCorruption(f"checkpoint hash mismatch: {path.name}")
    if (
        document.get("schema") != 1
        or document.get("phase") != phase
        or document.get("candidate_ref") != candidate
        or document.get("input_hash") != input_hash
        or document.get("upstream_hash") != upstream_hash
    ):
        raise CheckpointCorruption(f"checkpoint binding mismatch: {path.name}")
    return document


def _write_artifact(
    artifact_dir: Path,
    *,
    phase: str,
    candidate: Mapping[str, Any],
    input_hash: str,
    upstream_hash: str | None,
    value: Any,
) -> Artifact:
    payload = {
        "schema": 1,
        "phase": phase,
        "candidate_ref": dict(candidate),
        "input_hash": input_hash,
        "upstream_hash": upstream_hash,
        "value": value,
    }
    digest = _digest(payload)
    path = artifact_dir / f"{digest}.json"
    if path.exists():
        _load_artifact(
            path,
            phase=phase,
            candidate=candidate,
            input_hash=input_hash,
            upstream_hash=upstream_hash,
            expected_digest=digest,
        )
    else:
        document = {**payload, "artifact_hash": digest}
        _write_json_atomic(path, document)
    return Artifact(phase=phase, digest=digest, path=path)


def _load_chain(
    checkpoint_dir: Path,
    candidate_ref: Any,
    validated_inputs: Any,
    *,
    create: bool,
) -> tuple[
    dict[str, Any],
    str,
    str,
    Path,
    Path,
    dict[str, Artifact],
    dict[str, Any],
]:
    candidate = _candidate_document(candidate_ref)
    input_hash = _digest(validated_inputs)
    candidate_hash = _digest(candidate)
    chain_key = _digest(
        {"candidate_hash": candidate_hash, "input_hash": input_hash, "schema": 1}
    )
    artifact_dir = checkpoint_dir / "artifacts"
    index_dir = checkpoint_dir / "indexes"
    if create:
        artifact_dir.mkdir(parents=True, exist_ok=True)
        index_dir.mkdir(parents=True, exist_ok=True)
    index_path = index_dir / f"{chain_key}.json"

    indexed: dict[str, str] = {}
    if index_path.exists():
        index = _read_json(index_path)
        if (
            not isinstance(index, dict)
            or index.get("schema") != 1
            or index.get("candidate_hash") != candidate_hash
            or index.get("input_hash") != input_hash
            or not isinstance(index.get("artifacts"), dict)
        ):
            raise CheckpointCorruption("checkpoint index binding mismatch")
        indexed = dict(index["artifacts"])
        if any(
            phase not in PHASES or not isinstance(digest, str)
            for phase, digest in indexed.items()
        ):
            raise CheckpointCorruption("checkpoint index artifact map is malformed")
        missing_predecessor = False
        for phase in PHASES:
            if phase not in indexed:
                missing_predecessor = True
            elif missing_predecessor:
                raise CheckpointCorruption("checkpoint index is not a phase prefix")

    artifacts: dict[str, Artifact] = {}
    values: dict[str, Any] = {}
    upstream_hash: str | None = None
    for phase in PHASES:
        digest = indexed.get(phase)
        if digest is None:
            break
        path = artifact_dir / f"{digest}.json"
        if not path.exists():
            raise CheckpointCorruption(
                f"indexed checkpoint is missing: {path.name}"
            )
        document = _load_artifact(
            path,
            phase=phase,
            candidate=candidate,
            input_hash=input_hash,
            upstream_hash=upstream_hash,
            expected_digest=digest,
        )
        artifacts[phase] = Artifact(phase, digest, path)
        values[phase] = document["value"]
        upstream_hash = digest
    return (
        candidate,
        candidate_hash,
        input_hash,
        artifact_dir,
        index_path,
        artifacts,
        values,
    )


def _write_index(
    index_path: Path,
    *,
    candidate_hash: str,
    input_hash: str,
    artifacts: Mapping[str, Artifact],
) -> None:
    _write_json_atomic(
        index_path,
        {
            "schema": 1,
            "candidate_hash": candidate_hash,
            "input_hash": input_hash,
            "artifacts": {
                phase: artifacts[phase].digest
                for phase in PHASES
                if phase in artifacts
            },
        },
    )


def inspect_verification_checkpoints(
    checkpoint_dir: Path,
    candidate_ref: Any,
    validated_inputs: Any,
) -> CheckpointStatus:
    """Return the trusted completed prefix for one exact checkpoint chain."""

    (
        _candidate,
        candidate_hash,
        input_hash,
        _artifact_dir,
        _index_path,
        artifacts,
        _values,
    ) = _load_chain(
        checkpoint_dir,
        candidate_ref,
        validated_inputs,
        create=False,
    )
    phases_complete = tuple(phase for phase in PHASES if phase in artifacts)
    return CheckpointStatus(
        candidate_hash=candidate_hash,
        input_hash=input_hash,
        phases_complete=phases_complete,
        artifact_hashes={
            phase: artifacts[phase].digest for phase in phases_complete
        },
        complete=phases_complete == PHASES,
    )


def load_verification_adapters(
    verification_audit_root: Path,
    *,
    current_candidate: Any,
) -> tuple[Callable[[Any], Any], Callable[[Any], Any]]:
    """Load the canonical validator/reducer from an explicit skill root."""

    candidate = _candidate_document(current_candidate)
    if not verification_audit_root.is_absolute():
        raise VerificationCheckpointError(
            "verification-audit root must be an absolute path"
        )
    contract_path = (
        verification_audit_root / "scripts" / "verification_contract.py"
    )
    spec = importlib.util.spec_from_file_location(
        "_ticket_autopilot_verification_contract",
        contract_path,
    )
    if spec is None or spec.loader is None:
        raise VerificationCheckpointError(
            "verification-audit contract module is unavailable"
        )
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as error:
        raise VerificationCheckpointError(
            "verification-audit contract module could not be loaded"
        ) from error
    validator = getattr(module, "validate_bundle", None)
    reducer = getattr(module, "reduce_claims", None)
    if not callable(validator) or not callable(reducer):
        raise VerificationCheckpointError(
            "verification-audit contract adapters are unavailable"
        )

    def validate_current(value: Any) -> Any:
        return validator(value, current_candidate=candidate)

    return validate_current, reducer


def run_verification_checkpoints(
    checkpoint_dir: Path,
    candidate_ref: Any,
    validated_inputs: Any,
    *,
    builder: Callable[[Any], Any],
    validator: Callable[[Any], Any],
    reducer: Callable[[Any], Any],
) -> CheckpointRun:
    """Build or resume one exact CandidateRef/input verification chain.

    ``validator`` and ``reducer`` are the canonical policy adapters. This module
    only serializes their results; it never upgrades structural validity into a
    semantic claim.
    """

    (
        candidate,
        candidate_hash,
        input_hash,
        artifact_dir,
        index_path,
        artifacts,
        values,
    ) = _load_chain(
        checkpoint_dir,
        candidate_ref,
        validated_inputs,
        create=True,
    )
    first_missing = len(artifacts)
    upstream_hash = (
        artifacts[PHASES[first_missing - 1]].digest
        if first_missing
        else None
    )

    executed: list[str] = []
    for phase in PHASES[first_missing:]:
        try:
            if phase == "context-loaded":
                value = validated_inputs
            elif phase == "bundle-built":
                value = builder(values["context-loaded"])
            elif phase == "bundle-validated":
                value = validator(values["bundle-built"])
            elif phase == "bundle-reduced":
                value = reducer(values["bundle-validated"])
            else:
                validated = values["bundle-validated"]
                reduced = values["bundle-reduced"]
                if not isinstance(validated, Mapping) or not isinstance(
                    reduced, Mapping
                ):
                    raise VerificationCheckpointError(
                        "validator and reducer must return JSON objects"
                    )
                value = {**dict(validated), **dict(reduced)}
        except Exception as error:
            raise CheckpointPhaseFailure(phase, error) from error
        artifact = _write_artifact(
            artifact_dir,
            phase=phase,
            candidate=candidate,
            input_hash=input_hash,
            upstream_hash=upstream_hash,
            value=value,
        )
        artifacts[phase] = artifact
        values[phase] = value
        upstream_hash = artifact.digest
        executed.append(phase)
        _write_index(
            index_path,
            candidate_hash=candidate_hash,
            input_hash=input_hash,
            artifacts=artifacts,
        )

    return CheckpointRun(
        candidate_hash=candidate_hash,
        input_hash=input_hash,
        artifacts=artifacts,
        phases_executed=tuple(executed),
        handoff=values["handoff-ready"],
        cache_hit=not executed,
    )
