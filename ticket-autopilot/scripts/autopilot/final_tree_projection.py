from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from .candidate_contract import CANDIDATE_CONTRACT_VERSION
from .link_repoint import plan_repoints
from .ticket_contract import ticket_source_digest


PROJECTION_CONTRACT = "tracked-final-tree-observation-v1"
PROJECTION_CONTRACT_VERSION = 1
PROJECTION_CONFIG_SCHEMA = 1
PROJECTION_MODES = ("off", "observe", "enabled")
DEFAULT_PROJECTION_MODE = "enabled"
PROJECTION_ROLLBACK_STATUS = {
    "schema": 1,
    "new_projections": "select-off-for-established-full-process",
    "persisted_intents": "exact-version-bound-replay-or-block",
    "history_rewritten": False,
}
NON_AUTHORITY = {
    "completion": False,
    "provider": False,
    "merge": False,
    "terminal": False,
    "quality": False,
    "publication": False,
    "recovery": False,
    "wiki": False,
    "pi": False,
    "status_change": False,
    "cleanup": False,
}
_OID = re.compile(r"^[0-9a-f]{40,64}$")


class FinalTreeProjectionError(RuntimeError):
    pass


class ProjectionExcluded(FinalTreeProjectionError):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


@dataclass(frozen=True)
class PlannedProjection:
    manifest: dict[str, Any]
    bytes: bytes


@dataclass(frozen=True)
class ProjectionObservation:
    document: dict[str, Any]
    bytes: bytes


def canonical_bytes(document: Any) -> bytes:
    return (
        json.dumps(
            document,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        + "\n"
    ).encode("utf-8")


def canonical_digest(document: Any) -> str:
    return hashlib.sha256(canonical_bytes(document)).hexdigest()


def projection_config(mode: str = DEFAULT_PROJECTION_MODE) -> dict[str, Any]:
    if mode not in PROJECTION_MODES:
        raise FinalTreeProjectionError(
            "final-tree projection mode must be one of: "
            + ", ".join(PROJECTION_MODES)
        )
    return {
        "schema": PROJECTION_CONFIG_SCHEMA,
        "contract_version": PROJECTION_CONTRACT_VERSION,
        "mode": mode,
    }


def validate_projection_config(value: object) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {
        "schema",
        "contract_version",
        "mode",
    }:
        raise FinalTreeProjectionError(
            "final-tree projection configuration is malformed"
        )
    expected = projection_config(str(value.get("mode")))
    if value != expected:
        raise FinalTreeProjectionError(
            "final-tree projection configuration is malformed"
        )
    return expected


def _git(
    repo: Path,
    *args: str,
    env: Mapping[str, str] | None = None,
    input_bytes: bytes | None = None,
    check: bool = True,
) -> bytes:
    command_env = os.environ.copy()
    if env is not None:
        command_env.update(env)
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        env=command_env,
        input=input_bytes,
        capture_output=True,
        check=False,
    )
    if check and result.returncode:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise FinalTreeProjectionError(
            f"git {' '.join(args)} failed: {message or result.returncode}"
        )
    return result.stdout


def _git_text(
    repo: Path,
    *args: str,
    env: Mapping[str, str] | None = None,
    input_bytes: bytes | None = None,
) -> str:
    return _git(repo, *args, env=env, input_bytes=input_bytes).decode(
        "utf-8"
    ).strip()


def _path(value: str) -> str:
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts or not candidate.parts:
        raise ProjectionExcluded(
            "invalid-path", f"projection path is not repository-relative: {value}"
        )
    normalized = candidate.as_posix()
    if normalized in {"", "."}:
        raise ProjectionExcluded("invalid-path", "projection path is empty")
    return normalized


def _candidate(value: object) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {
        "contract_version",
        "base_tree_oid",
        "candidate_tree_oid",
        "ticket_digest",
    }:
        raise ProjectionExcluded(
            "candidate-ref", "projection requires an exact CandidateRef"
        )
    if value.get("contract_version") != CANDIDATE_CONTRACT_VERSION or any(
        not isinstance(value.get(field), str)
        or not _OID.fullmatch(str(value[field]))
        for field in ("base_tree_oid", "candidate_tree_oid")
    ) or not isinstance(value.get("ticket_digest"), str) or not re.fullmatch(
        r"[0-9a-f]{64}", str(value["ticket_digest"])
    ):
        raise ProjectionExcluded(
            "candidate-ref", "projection CandidateRef is malformed"
        )
    return dict(value)


def _index_entries(repo: Path) -> dict[str, dict[str, str]]:
    fields = _git(repo, "ls-files", "-s", "-z").split(b"\0")
    entries: dict[str, dict[str, str]] = {}
    for raw in fields:
        if not raw:
            continue
        metadata, separator, path_bytes = raw.partition(b"\t")
        if not separator:
            raise FinalTreeProjectionError("git index output is malformed")
        mode, oid, stage = metadata.decode("ascii").split()
        path = path_bytes.decode("utf-8")
        if stage != "0":
            raise ProjectionExcluded(
                "unmerged-index", "projection cannot inspect an unmerged index"
            )
        entries[path] = {"mode": mode, "oid": oid}
    return entries


def _assert_clean_index_boundary(repo: Path, candidate_tree_oid: str) -> None:
    if _git_text(repo, "write-tree") != candidate_tree_oid:
        raise ProjectionExcluded(
            "candidate-drift",
            "projection CandidateRef differs from the current index tree",
        )
    if subprocess.run(
        ["git", "diff", "--quiet", "--"], cwd=repo, check=False
    ).returncode:
        raise ProjectionExcluded(
            "unstaged-change", "projection requires an exact index/worktree boundary"
        )
    untracked = _git(repo, "ls-files", "--others", "--exclude-standard", "-z")
    if untracked:
        raise ProjectionExcluded(
            "untracked-change", "projection excludes untracked repository paths"
        )


def _blob_oid(repo: Path, data: bytes) -> str:
    return _git_text(repo, "hash-object", "--stdin", input_bytes=data)


def _entry_effect(
    kind: str,
    *,
    path: str,
    old_mode: str,
    new_mode: str,
    old_oid: str,
    new_oid: str,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "kind": kind,
        "path": path,
        "old_mode": old_mode,
        "new_mode": new_mode,
        "old_oid": old_oid,
        "new_oid": new_oid,
    }
    if extra:
        payload.update(extra)
    return {"effect_key": canonical_digest(payload), **payload}


def _raw_diff_rows(
    repo: Path,
    before_tree: str,
    after_tree: str,
    *,
    env: Mapping[str, str] | None = None,
) -> list[dict[str, str]]:
    raw = _git(
        repo,
        "diff",
        "--raw",
        "--full-index",
        "--abbrev=64",
        "--no-renames",
        "-z",
        before_tree,
        after_tree,
        env=env,
    ).split(b"\0")
    rows: list[dict[str, str]] = []
    if raw and raw[-1] == b"":
        raw.pop()
    if len(raw) % 2:
        raise FinalTreeProjectionError("raw Git tree diff is malformed")
    for position in range(0, len(raw), 2):
        metadata = raw[position].decode("ascii")
        path = raw[position + 1].decode("utf-8")
        fields = metadata.removeprefix(":").split()
        if len(fields) != 5:
            raise FinalTreeProjectionError("raw Git tree diff is malformed")
        old_mode, new_mode, old_oid, new_oid, status = fields
        if status not in {"A", "D", "M", "T"}:
            raise FinalTreeProjectionError(
                f"unexpected raw projection status: {status}"
            )
        rows.append(
            {
                "path": path,
                "status": status,
                "old_mode": old_mode,
                "new_mode": new_mode,
                "old_oid": old_oid,
                "new_oid": new_oid,
            }
        )
    return sorted(rows, key=lambda row: (row["path"], row["status"]))


def _temporary_tree(
    repo: Path,
    before_tree: str,
    effects: Sequence[dict[str, Any]],
    blob_contents: Mapping[str, bytes],
) -> tuple[str, list[dict[str, str]]]:
    objects_text = _git_text(repo, "rev-parse", "--git-path", "objects")
    objects = Path(objects_text)
    if not objects.is_absolute():
        objects = (repo / objects).resolve()
    with tempfile.TemporaryDirectory(prefix="ticket-final-tree-") as directory:
        root = Path(directory)
        temporary_objects = root / "objects"
        temporary_objects.mkdir()
        index = root / "index"
        env = {
            "GIT_INDEX_FILE": str(index),
            "GIT_OBJECT_DIRECTORY": str(temporary_objects),
            "GIT_ALTERNATE_OBJECT_DIRECTORIES": str(objects),
        }
        _git(repo, "read-tree", before_tree, env=env)
        materialized_oids: dict[str, str] = {}
        for path, content in sorted(blob_contents.items()):
            materialized_oids[path] = _git_text(
                repo,
                "hash-object",
                "-w",
                "--stdin",
                env=env,
                input_bytes=content,
            )
        for effect in effects:
            kind = effect["kind"]
            path = effect["path"]
            if kind == "ticket-delete":
                _git(repo, "update-index", "--force-remove", "--", path, env=env)
                continue
            oid = materialized_oids[path]
            if oid != effect["new_oid"]:
                raise FinalTreeProjectionError(
                    f"planned blob identity changed for {path}"
                )
            _git(
                repo,
                "update-index",
                "--add",
                "--cacheinfo",
                f"{effect['new_mode']},{oid},{path}",
                env=env,
            )
        tree_oid = _git_text(repo, "write-tree", env=env)
        rows = _raw_diff_rows(repo, before_tree, tree_oid, env=env)
        return tree_oid, rows


def _manifest_payload(manifest: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in manifest.items() if key != "manifest_digest"}


def validate_projection_reference(
    value: object, *, kind: str
) -> dict[str, Any]:
    if kind not in {"plan", "observation"} or not isinstance(value, dict):
        raise FinalTreeProjectionError(
            "final-tree projection reference is malformed"
        )
    common = {
        "schema", "artifact", "sha256", "status", "authority", "mode",
        "contract_version",
    }
    status = value.get("status")
    if kind == "plan" and status == "eligible":
        expected = common | {
            "manifest_digest",
            "implementation_candidate_ref",
            "planned_delivery_candidate_ref",
        }
    elif kind == "plan" and status == "excluded":
        expected = common | {"reason"}
        if value.get("mode") == "enabled":
            expected.add("artifact_generation")
    elif kind == "observation" and status in {"parity", "discrepancy"}:
        expected = common | {
            "manifest_digest",
            "observation_digest",
            "actual_delivery_candidate_ref",
            "discrepancies",
        }
    else:
        raise FinalTreeProjectionError(
            "final-tree projection reference status is invalid"
        )
    if (
        set(value) != expected
        or value.get("schema") != 1
        or not isinstance(value.get("artifact"), str)
        or not value["artifact"]
        or not re.fullmatch(r"[0-9a-f]{64}", str(value.get("sha256")))
        or value.get("authority") != NON_AUTHORITY
        or value.get("mode")
        not in (
            {"observe", "enabled"}
            if kind == "plan" and status == "excluded"
            else {"observe"}
        )
        or value.get("contract_version") != PROJECTION_CONTRACT_VERSION
    ):
        raise FinalTreeProjectionError(
            "final-tree projection reference identity is invalid"
        )
    if status == "eligible":
        _candidate(value.get("implementation_candidate_ref"))
        _candidate(value.get("planned_delivery_candidate_ref"))
        if not re.fullmatch(
            r"[0-9a-f]{64}", str(value.get("manifest_digest"))
        ):
            raise FinalTreeProjectionError(
                "final-tree projection manifest reference is invalid"
            )
    elif status == "excluded":
        reason = value.get("reason")
        generation = value.get("artifact_generation")
        if (
            not isinstance(reason, dict)
            or set(reason) != {"code", "detail"}
            or any(not isinstance(item, str) or not item for item in reason.values())
            or (
                value.get("mode") == "enabled"
                and (
                    not isinstance(generation, int)
                    or isinstance(generation, bool)
                    or generation < 0
                )
            )
        ):
            raise FinalTreeProjectionError(
                "final-tree projection exclusion is invalid"
            )
    else:
        _candidate(value.get("actual_delivery_candidate_ref"))
        if any(
            not re.fullmatch(r"[0-9a-f]{64}", str(value.get(field)))
            for field in ("manifest_digest", "observation_digest")
        ) or not isinstance(value.get("discrepancies"), list) or any(
            not isinstance(item, str) or not item
            for item in value["discrepancies"]
        ) or (status == "parity" and value["discrepancies"]):
            raise FinalTreeProjectionError(
                "final-tree projection observation reference is invalid"
            )
    return copy_json(value)


def copy_json(value: Any) -> Any:
    return json.loads(canonical_bytes(value))


def validate_manifest(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise FinalTreeProjectionError("projection manifest must be an object")
    expected_fields = {
        "schema",
        "contract",
        "contract_version",
        "run_id",
        "ticket_id",
        "artifact_generation",
        "configuration",
        "implementation_candidate_ref",
        "planned_delivery_candidate_ref",
        "ticket",
        "completion_receipt",
        "link_closure",
        "effects",
        "expected_diff",
        "negative_proof",
        "authority",
        "manifest_digest",
    }
    if set(value) != expected_fields:
        raise FinalTreeProjectionError("projection manifest shape is invalid")
    if (
        value.get("schema") != 1
        or value.get("contract") != PROJECTION_CONTRACT
        or value.get("contract_version") != PROJECTION_CONTRACT_VERSION
        or value.get("authority") != NON_AUTHORITY
        or not isinstance(value.get("run_id"), str)
        or not value["run_id"]
        or not isinstance(value.get("ticket_id"), str)
        or not value["ticket_id"]
        or not isinstance(value.get("artifact_generation"), int)
        or value["artifact_generation"] < 0
    ):
        raise FinalTreeProjectionError("projection manifest identity is invalid")
    config = validate_projection_config(value.get("configuration"))
    if config["mode"] not in {"observe", "enabled"}:
        raise FinalTreeProjectionError(
            "projection manifests require observe or enabled mode"
        )
    implementation = _candidate(value.get("implementation_candidate_ref"))
    delivery = _candidate(value.get("planned_delivery_candidate_ref"))
    if (
        implementation["base_tree_oid"] != delivery["base_tree_oid"]
        or implementation["ticket_digest"] != delivery["ticket_digest"]
    ):
        raise FinalTreeProjectionError(
            "projection manifest CandidateRef lineage is invalid"
        )
    ticket = value.get("ticket")
    receipt = value.get("completion_receipt")
    closure = value.get("link_closure")
    effects = value.get("effects")
    rows = value.get("expected_diff")
    proof = value.get("negative_proof")
    if not isinstance(ticket, dict) or set(ticket) != {
        "source_path",
        "destination_path",
        "source_mode",
        "source_oid",
        "source_sha256",
        "ticket_digest",
    }:
        raise FinalTreeProjectionError("projection ticket binding is invalid")
    if not isinstance(receipt, dict) or set(receipt) != {
        "path",
        "mode",
        "oid",
        "sha256",
        "document",
    }:
        raise FinalTreeProjectionError("projection completion receipt is invalid")
    if (
        ticket["ticket_digest"] != implementation["ticket_digest"]
        or ticket["source_mode"] != "100644"
        or not _OID.fullmatch(str(ticket["source_oid"]))
        or not re.fullmatch(r"[0-9a-f]{64}", str(ticket["source_sha256"]))
        or receipt["path"]
        != str(Path(ticket["destination_path"]).with_suffix(".completion.json"))
        or receipt["mode"] != "100644"
        or not _OID.fullmatch(str(receipt["oid"]))
        or receipt["sha256"]
        != hashlib.sha256(canonical_bytes(receipt["document"])).hexdigest()
        or not isinstance(receipt["document"], dict)
        or set(receipt["document"])
        != {
            "schema",
            "run_id",
            "ticket_id",
            "implementation_status",
            "candidate_ref",
            "ticket_source_mode",
            "snapshot_manifest_digest",
        }
        or receipt["document"].get("schema") != 1
        or receipt["document"].get("run_id") != value["run_id"]
        or receipt["document"].get("ticket_id") != value["ticket_id"]
        or receipt["document"].get("implementation_status") != "complete"
        or receipt["document"].get("candidate_ref") != implementation
        or receipt["document"].get("ticket_source_mode") != "tracked"
        or not re.fullmatch(
            r"[0-9a-f]{64}",
            str(receipt["document"].get("snapshot_manifest_digest")),
        )
    ):
        raise FinalTreeProjectionError("projection completion binding is invalid")
    if not isinstance(closure, list) or not isinstance(effects, list) or not isinstance(
        rows, list
    ) or not isinstance(proof, dict):
        raise FinalTreeProjectionError("projection manifest collections are invalid")
    if closure != sorted(closure, key=lambda item: item.get("path", "")):
        raise FinalTreeProjectionError("projection link closure is not canonical")
    closure_fields = {
        "path",
        "mode",
        "before_oid",
        "after_oid",
        "before_sha256",
        "after_sha256",
    }
    if any(
        not isinstance(item, dict)
        or set(item) != closure_fields
        or item["mode"] != "100644"
        or not _OID.fullmatch(str(item["before_oid"]))
        or not _OID.fullmatch(str(item["after_oid"]))
        or not re.fullmatch(r"[0-9a-f]{64}", str(item["before_sha256"]))
        or not re.fullmatch(r"[0-9a-f]{64}", str(item["after_sha256"]))
        for item in closure
    ) or len({item["path"] for item in closure}) != len(closure):
        raise FinalTreeProjectionError("projection link closure is invalid")
    effect_keys = [effect.get("effect_key") for effect in effects if isinstance(effect, dict)]
    if len(effect_keys) != len(effects) or len(set(effect_keys)) != len(effect_keys):
        raise FinalTreeProjectionError("projection effects are not unique")
    expected_effect_fields = {
        "ticket-delete": {
            "effect_key", "kind", "path", "old_mode", "new_mode",
            "old_oid", "new_oid", "destination",
        },
        "ticket-add": {
            "effect_key", "kind", "path", "old_mode", "new_mode",
            "old_oid", "new_oid", "source",
        },
        "completion-receipt-add": {
            "effect_key", "kind", "path", "old_mode", "new_mode",
            "old_oid", "new_oid",
        },
        "link-repoint": {
            "effect_key", "kind", "path", "old_mode", "new_mode",
            "old_oid", "new_oid", "source", "destination",
        },
    }
    derived_rows: list[dict[str, str]] = []
    for effect in effects:
        kind = effect.get("kind") if isinstance(effect, dict) else None
        if kind not in expected_effect_fields or set(effect) != expected_effect_fields[kind]:
            raise FinalTreeProjectionError("projection effect shape is invalid")
        payload = {key: item for key, item in effect.items() if key != "effect_key"}
        if effect["effect_key"] != canonical_digest(payload):
            raise FinalTreeProjectionError("projection effect identity is invalid")
        if effect["old_mode"] == "000000":
            status = "A"
        elif effect["new_mode"] == "000000":
            status = "D"
        elif effect["old_mode"] != effect["new_mode"]:
            status = "T"
        else:
            status = "M"
        derived_rows.append(
            {
                "path": effect["path"],
                "status": status,
                "old_mode": effect["old_mode"],
                "new_mode": effect["new_mode"],
                "old_oid": effect["old_oid"],
                "new_oid": effect["new_oid"],
            }
        )
    derived_rows.sort(key=lambda row: (row["path"], row["status"]))
    if len({row["path"] for row in rows}) != len(rows):
        raise FinalTreeProjectionError("projection diff paths are not unique")
    if rows != derived_rows:
        raise FinalTreeProjectionError(
            "projection diff rows do not close over effects: "
            f"expected={canonical_digest(derived_rows)} "
            f"observed={canonical_digest(rows)}"
        )
    if rows != sorted(rows, key=lambda row: (row["path"], row["status"])):
        raise FinalTreeProjectionError("projection diff rows are not canonical")
    if effects != sorted(effects, key=lambda effect: (effect["path"], effect["kind"])):
        raise FinalTreeProjectionError("projection effects are not canonical")
    by_kind = {effect["kind"]: effect for effect in effects if effect["kind"] != "link-repoint"}
    links = [effect for effect in effects if effect["kind"] == "link-repoint"]
    link_effects_match = all(
        effect["source"] == ticket["source_path"]
        and effect["destination"] == ticket["destination_path"]
        and effect["old_oid"] == item["before_oid"]
        and effect["new_oid"] == item["after_oid"]
        and effect["old_mode"] == item["mode"] == effect["new_mode"]
        for effect, item in zip(links, closure)
    )
    if (
        set(by_kind) != {"ticket-delete", "ticket-add", "completion-receipt-add"}
        or by_kind["ticket-delete"]["path"] != ticket["source_path"]
        or by_kind["ticket-delete"]["destination"] != ticket["destination_path"]
        or by_kind["ticket-delete"]["old_oid"] != ticket["source_oid"]
        or by_kind["ticket-add"]["path"] != ticket["destination_path"]
        or by_kind["ticket-add"]["source"] != ticket["source_path"]
        or by_kind["ticket-add"]["new_oid"] != ticket["source_oid"]
        or by_kind["completion-receipt-add"]["path"] != receipt["path"]
        or by_kind["completion-receipt-add"]["new_oid"] != receipt["oid"]
        or [effect["path"] for effect in links]
        != [item["path"] for item in closure]
        or not link_effects_match
    ):
        raise FinalTreeProjectionError("projection completion effects are contradictory")
    if proof != {
        "complete": True,
        "extra_diff_rows": 0,
        "expected_diff_digest": canonical_digest(rows),
        "link_closure_digest": canonical_digest(closure),
    }:
        raise FinalTreeProjectionError("projection negative proof is invalid")
    if value.get("manifest_digest") != canonical_digest(_manifest_payload(value)):
        raise FinalTreeProjectionError("projection manifest digest is invalid")
    return copy_json(value)


def plan_tracked_completion(
    repo: Path,
    *,
    run_id: str,
    ticket_id: str,
    artifact_generation: int,
    configuration: Mapping[str, Any],
    candidate_ref: Mapping[str, Any],
    source_relative_path: str,
    destination_relative_path: str,
    receipt_document: Mapping[str, Any],
    source_mode: str,
    delivery_metadata: Mapping[str, Any] | None = None,
    pr: object = None,
    excluded_reasons: Sequence[str] = (),
) -> PlannedProjection:
    repo = repo.resolve()
    config = validate_projection_config(dict(configuration))
    if config["mode"] not in {"observe", "enabled"}:
        raise ProjectionExcluded(
            "mode",
            f"tracked final-tree projection is not active in {config['mode']} mode",
        )
    if source_mode != "tracked":
        raise ProjectionExcluded(
            "source-mode", "projection observer accepts only tracked ticket sources"
        )
    if excluded_reasons:
        raise ProjectionExcluded(
            "lifecycle",
            "projection observer excludes this lifecycle: "
            + ", ".join(sorted(set(excluded_reasons))),
        )
    if pr is not None:
        raise ProjectionExcluded(
            "provider-state", "projection observer excludes existing provider state"
        )
    delivery = dict(delivery_metadata or {})
    forbidden = sorted(key for key in delivery if key != "branch")
    if forbidden:
        raise ProjectionExcluded(
            "delivery-state",
            "projection observer excludes prior delivery/recovery state: "
            + ", ".join(forbidden),
        )
    implementation = _candidate(dict(candidate_ref))
    _assert_clean_index_boundary(repo, implementation["candidate_tree_oid"])
    source = _path(source_relative_path)
    destination = _path(destination_relative_path)
    receipt_path = str(Path(destination).with_suffix(".completion.json"))
    entries = _index_entries(repo)
    source_entry = entries.get(source)
    if source_entry is None:
        raise ProjectionExcluded(
            "source-missing", "tracked completion source is absent from the index"
        )
    if source_entry["mode"] != "100644":
        raise ProjectionExcluded(
            "source-mode-drift", "tracked completion source mode is not 100644"
        )
    if destination in entries or receipt_path in entries:
        raise ProjectionExcluded(
            "destination-present",
            "tracked completion destination or receipt already exists",
        )
    source_bytes = (repo / source).read_bytes()
    if _blob_oid(repo, source_bytes) != source_entry["oid"]:
        raise ProjectionExcluded(
            "source-content-drift", "tracked ticket bytes differ from the index"
        )
    observed_digest = ticket_source_digest(repo / source)
    if observed_digest != implementation["ticket_digest"]:
        raise ProjectionExcluded(
            "ticket-digest-drift",
            "tracked ticket digest differs from the CandidateRef",
        )
    receipt_bytes = canonical_bytes(dict(receipt_document))
    receipt_oid = _blob_oid(repo, receipt_bytes)
    repoints = plan_repoints(repo, source, destination)
    effects: list[dict[str, Any]] = [
        _entry_effect(
            "ticket-delete",
            path=source,
            old_mode=source_entry["mode"],
            new_mode="000000",
            old_oid=source_entry["oid"],
            new_oid="0" * len(source_entry["oid"]),
            extra={"destination": destination},
        ),
        _entry_effect(
            "ticket-add",
            path=destination,
            old_mode="000000",
            new_mode=source_entry["mode"],
            old_oid="0" * len(source_entry["oid"]),
            new_oid=source_entry["oid"],
            extra={"source": source},
        ),
        _entry_effect(
            "completion-receipt-add",
            path=receipt_path,
            old_mode="000000",
            new_mode="100644",
            old_oid="0" * len(source_entry["oid"]),
            new_oid=receipt_oid,
        ),
    ]
    blob_contents: dict[str, bytes] = {
        destination: source_bytes,
        receipt_path: receipt_bytes,
    }
    closure: list[dict[str, Any]] = []
    for path, after_bytes in sorted(repoints.items()):
        path = _path(path)
        before_entry = entries.get(path)
        if before_entry is None or before_entry["mode"] != "100644":
            raise ProjectionExcluded(
                "link-closure",
                f"link closure path is not an ordinary tracked file: {path}",
            )
        before_bytes = (repo / path).read_bytes()
        before_oid = _blob_oid(repo, before_bytes)
        if before_oid != before_entry["oid"]:
            raise ProjectionExcluded(
                "link-content-drift", f"link closure path drifted: {path}"
            )
        after_oid = _blob_oid(repo, after_bytes)
        closure.append(
            {
                "path": path,
                "mode": before_entry["mode"],
                "before_oid": before_oid,
                "after_oid": after_oid,
                "before_sha256": hashlib.sha256(before_bytes).hexdigest(),
                "after_sha256": hashlib.sha256(after_bytes).hexdigest(),
            }
        )
        effects.append(
            _entry_effect(
                "link-repoint",
                path=path,
                old_mode=before_entry["mode"],
                new_mode=before_entry["mode"],
                old_oid=before_oid,
                new_oid=after_oid,
                extra={"source": source, "destination": destination},
            )
        )
        blob_contents[path] = after_bytes
    effects = sorted(effects, key=lambda effect: (effect["path"], effect["kind"]))
    planned_tree, rows = _temporary_tree(
        repo,
        implementation["candidate_tree_oid"],
        effects,
        blob_contents,
    )
    expected_paths = sorted(effect["path"] for effect in effects)
    row_paths = sorted(row["path"] for row in rows)
    if row_paths != expected_paths or len(rows) != len(effects):
        raise FinalTreeProjectionError(
            "projection negative proof found an unexpected tree effect"
        )
    delivery_candidate = {
        **implementation,
        "candidate_tree_oid": planned_tree,
    }
    payload = {
        "schema": 1,
        "contract": PROJECTION_CONTRACT,
        "contract_version": PROJECTION_CONTRACT_VERSION,
        "run_id": run_id,
        "ticket_id": ticket_id,
        "artifact_generation": artifact_generation,
        "configuration": config,
        "implementation_candidate_ref": implementation,
        "planned_delivery_candidate_ref": delivery_candidate,
        "ticket": {
            "source_path": source,
            "destination_path": destination,
            "source_mode": source_entry["mode"],
            "source_oid": source_entry["oid"],
            "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
            "ticket_digest": observed_digest,
        },
        "completion_receipt": {
            "path": receipt_path,
            "mode": "100644",
            "oid": receipt_oid,
            "sha256": hashlib.sha256(receipt_bytes).hexdigest(),
            "document": dict(receipt_document),
        },
        "link_closure": closure,
        "effects": effects,
        "expected_diff": rows,
        "negative_proof": {
            "complete": True,
            "extra_diff_rows": 0,
            "expected_diff_digest": canonical_digest(rows),
            "link_closure_digest": canonical_digest(closure),
        },
        "authority": dict(NON_AUTHORITY),
    }
    manifest = {**payload, "manifest_digest": canonical_digest(payload)}
    normalized = validate_manifest(manifest)
    return PlannedProjection(normalized, canonical_bytes(normalized))


def compare_projection(
    repo: Path,
    manifest_value: Mapping[str, Any],
    actual_candidate_ref: Mapping[str, Any],
) -> ProjectionObservation:
    manifest = validate_manifest(dict(manifest_value))
    actual = _candidate(dict(actual_candidate_ref))
    implementation = manifest["implementation_candidate_ref"]
    planned = manifest["planned_delivery_candidate_ref"]
    discrepancies: list[str] = []
    if actual != planned:
        discrepancies.append("actual CandidateRef differs from planned delivery CandidateRef")
    actual_rows = _raw_diff_rows(
        repo.resolve(),
        implementation["candidate_tree_oid"],
        actual["candidate_tree_oid"],
    )
    expected_rows = manifest["expected_diff"]
    if actual_rows != expected_rows:
        discrepancies.append("actual I-to-D tree diff differs from expected diff")
    if len({effect["effect_key"] for effect in manifest["effects"]}) != len(
        manifest["effects"]
    ):
        discrepancies.append("planned effects are not unique")
    payload = {
        "schema": 1,
        "contract": PROJECTION_CONTRACT,
        "contract_version": PROJECTION_CONTRACT_VERSION,
        "run_id": manifest["run_id"],
        "ticket_id": manifest["ticket_id"],
        "artifact_generation": manifest["artifact_generation"],
        "manifest_digest": manifest["manifest_digest"],
        "status": "parity" if not discrepancies else "discrepancy",
        "implementation_candidate_ref": implementation,
        "planned_delivery_candidate_ref": planned,
        "actual_delivery_candidate_ref": actual,
        "expected_diff_digest": canonical_digest(expected_rows),
        "actual_diff_digest": canonical_digest(actual_rows),
        "actual_diff": actual_rows,
        "discrepancies": discrepancies,
        "authority": dict(NON_AUTHORITY),
    }
    document = {**payload, "observation_digest": canonical_digest(payload)}
    return ProjectionObservation(document, canonical_bytes(document))


def comparison_failure(
    manifest_value: Mapping[str, Any],
    actual_candidate_ref: Mapping[str, Any],
    detail: str,
) -> ProjectionObservation:
    manifest = validate_manifest(dict(manifest_value))
    actual = _candidate(dict(actual_candidate_ref))
    payload = {
        "schema": 1,
        "contract": PROJECTION_CONTRACT,
        "contract_version": PROJECTION_CONTRACT_VERSION,
        "run_id": manifest["run_id"],
        "ticket_id": manifest["ticket_id"],
        "artifact_generation": manifest["artifact_generation"],
        "manifest_digest": manifest["manifest_digest"],
        "status": "discrepancy",
        "implementation_candidate_ref": manifest[
            "implementation_candidate_ref"
        ],
        "planned_delivery_candidate_ref": manifest[
            "planned_delivery_candidate_ref"
        ],
        "actual_delivery_candidate_ref": actual,
        "expected_diff_digest": manifest["negative_proof"][
            "expected_diff_digest"
        ],
        "actual_diff_digest": None,
        "actual_diff": None,
        "discrepancies": [f"observer comparison failed: {detail}"],
        "authority": dict(NON_AUTHORITY),
    }
    document = {**payload, "observation_digest": canonical_digest(payload)}
    return ProjectionObservation(document, canonical_bytes(document))


def validate_excluded_observation(value: object) -> dict[str, Any]:
    expected = {
        "schema",
        "contract",
        "contract_version",
        "run_id",
        "ticket_id",
        "artifact_generation",
        "configuration",
        "status",
        "reason",
        "authority",
        "observation_digest",
    }
    if not isinstance(value, dict) or set(value) != expected:
        raise FinalTreeProjectionError(
            "final-tree projection exclusion artifact is malformed"
        )
    payload = {
        key: value[key] for key in expected if key != "observation_digest"
    }
    reason = value.get("reason")
    if (
        value.get("schema") != 1
        or value.get("contract") != PROJECTION_CONTRACT
        or value.get("contract_version") != PROJECTION_CONTRACT_VERSION
        or not isinstance(value.get("run_id"), str)
        or not value["run_id"]
        or not isinstance(value.get("ticket_id"), str)
        or not value["ticket_id"]
        or not isinstance(value.get("artifact_generation"), int)
        or isinstance(value.get("artifact_generation"), bool)
        or value["artifact_generation"] < 0
        or value.get("status") != "excluded"
        or not isinstance(reason, dict)
        or set(reason) != {"code", "detail"}
        or any(not isinstance(item, str) or not item for item in reason.values())
        or value.get("authority") != NON_AUTHORITY
        or value.get("observation_digest") != canonical_digest(payload)
    ):
        raise FinalTreeProjectionError(
            "final-tree projection exclusion artifact identity is invalid"
        )
    validate_projection_config(value.get("configuration"))
    return json.loads(json.dumps(value))


def excluded_observation(
    *,
    run_id: str,
    ticket_id: str,
    artifact_generation: int,
    configuration: Mapping[str, Any],
    code: str,
    detail: str,
) -> ProjectionObservation:
    payload = {
        "schema": 1,
        "contract": PROJECTION_CONTRACT,
        "contract_version": PROJECTION_CONTRACT_VERSION,
        "run_id": run_id,
        "ticket_id": ticket_id,
        "artifact_generation": artifact_generation,
        "configuration": validate_projection_config(dict(configuration)),
        "status": "excluded",
        "reason": {"code": code, "detail": detail},
        "authority": dict(NON_AUTHORITY),
    }
    document = {**payload, "observation_digest": canonical_digest(payload)}
    return ProjectionObservation(document, canonical_bytes(document))
