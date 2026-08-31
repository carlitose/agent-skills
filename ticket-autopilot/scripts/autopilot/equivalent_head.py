from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path
from typing import Any, Callable, Mapping

from .terminal_integration import canonical_digest


RECEIPT_SCHEMA = 2
LEGACY_RECEIPT_SCHEMA = 1
DELIVERY_STEP = "external-head-equivalence"
TWO_PARENT_HEAD_MERGE = "two-parent-head-merge"
SINGLE_PARENT_INTEGRATION_COPY = "single-parent-integration-copy"
_GIT = ("git", "--no-replace-objects")
_OID = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")
_RAW_METADATA = re.compile(
    rb"^:[0-7]{6} [0-7]{6} [0-9a-f]{40}(?:[0-9a-f]{24})? "
    rb"[0-9a-f]{40}(?:[0-9a-f]{24})? [ADMT]$"
)
_RECEIPT_FIELDS_V1 = {
    "schema",
    "repository_identity",
    "provider",
    "pr_id",
    "branch",
    "base_branch",
    "recorded_base_sha",
    "recorded_base_tree_oid",
    "recorded_head_sha",
    "recorded_head_tree_oid",
    "observed_base_sha",
    "observed_base_tree_oid",
    "observed_head_sha",
    "observed_head_tree_oid",
    "merge_commit_sha",
    "merge_commit_tree_oid",
    "raw_delta_sha256",
    "raw_delta_entries",
    "provider_observation_digest",
    "actor",
    "evidence",
}
_RECEIPT_FIELDS_V2 = _RECEIPT_FIELDS_V1 | {
    "topology",
    "integration_parent_shas",
}
_TOPOLOGIES = {TWO_PARENT_HEAD_MERGE, SINGLE_PARENT_INTEGRATION_COPY}


class EquivalentHeadError(RuntimeError):
    """A provider-observed replacement head is not exactly equivalent."""


def _checked_text(worktree: Path, *arguments: str, failure: str) -> str:
    result = subprocess.run(
        [*_GIT, *arguments],
        cwd=worktree,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        detail = result.stderr or result.stdout or failure
        raise EquivalentHeadError(f"{failure}: {detail.strip()}")
    return result.stdout.strip()


def _checked_bytes(worktree: Path, *arguments: str, failure: str) -> bytes:
    result = subprocess.run(
        [*_GIT, *arguments],
        cwd=worktree,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        detail = (result.stderr or result.stdout).decode("utf-8", errors="replace")
        raise EquivalentHeadError(f"{failure}: {detail.strip()}")
    return result.stdout


def _require_oid(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _OID.fullmatch(value):
        raise EquivalentHeadError(f"equivalent-head {label} is malformed")
    return value


def _ensure_commit(
    worktree: Path,
    oid: str,
    *,
    boundary_guard: Callable[[str], None],
) -> None:
    probe = subprocess.run(
        [*_GIT, "cat-file", "-e", f"{oid}^{{commit}}"],
        cwd=worktree,
        capture_output=True,
        check=False,
    )
    if probe.returncode == 0:
        return
    boundary_guard("git:equivalent-head-object-fetch")
    fetched = subprocess.run(
        [
            *_GIT,
            "fetch",
            "--no-tags",
            "--no-write-fetch-head",
            "origin",
            oid,
        ],
        cwd=worktree,
        text=True,
        capture_output=True,
        check=False,
    )
    if fetched.returncode:
        detail = fetched.stderr or fetched.stdout or "exact object fetch failed"
        raise EquivalentHeadError(
            f"equivalent-head exact object fetch failed: {detail.strip()}"
        )
    readback = subprocess.run(
        [*_GIT, "cat-file", "-e", f"{oid}^{{commit}}"],
        cwd=worktree,
        capture_output=True,
        check=False,
    )
    if readback.returncode:
        raise EquivalentHeadError("equivalent-head fetched object is not a commit")


def _commit(worktree: Path, oid: str) -> tuple[list[str], str]:
    fields = _checked_text(
        worktree,
        "show",
        "-s",
        "--format=%P%x00%T",
        oid,
        failure="equivalent-head commit readback failed",
    ).split("\0")
    if len(fields) != 2:
        raise EquivalentHeadError("equivalent-head commit readback is malformed")
    parents = fields[0].split() if fields[0] else []
    tree = _require_oid(fields[1], "tree OID")
    if any(not _OID.fullmatch(parent) for parent in parents):
        raise EquivalentHeadError("equivalent-head commit parent is malformed")
    return parents, tree


def _raw_delta(worktree: Path, base: str, head: str) -> tuple[bytes, int]:
    raw = _checked_bytes(
        worktree,
        "diff-tree",
        "-r",
        "--no-commit-id",
        "--raw",
        "--full-index",
        "--no-renames",
        "-z",
        base,
        head,
        failure="equivalent-head raw tree transition failed",
    )
    parts = raw.split(b"\0")
    if not raw or parts[-1] != b"" or (len(parts) - 1) % 2:
        raise EquivalentHeadError("equivalent-head raw tree transition is malformed")
    entries = (len(parts) - 1) // 2
    if entries == 0:
        raise EquivalentHeadError("equivalent-head raw tree transition is empty")
    for index in range(0, len(parts) - 1, 2):
        metadata, path = parts[index : index + 2]
        if not _RAW_METADATA.fullmatch(metadata) or not path:
            raise EquivalentHeadError("equivalent-head raw tree entry is malformed")
    return raw, entries


def _validate_shape(receipt: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(receipt, Mapping):
        raise EquivalentHeadError("equivalent-head receipt shape is invalid")
    schema = receipt.get("schema")
    if not isinstance(schema, int) or isinstance(schema, bool):
        raise EquivalentHeadError("equivalent-head receipt schema is invalid")
    expected_fields = {
        LEGACY_RECEIPT_SCHEMA: _RECEIPT_FIELDS_V1,
        RECEIPT_SCHEMA: _RECEIPT_FIELDS_V2,
    }.get(schema)
    if expected_fields is None:
        raise EquivalentHeadError("equivalent-head receipt schema is invalid")
    if set(receipt) != expected_fields:
        raise EquivalentHeadError("equivalent-head receipt shape is invalid")
    if schema == RECEIPT_SCHEMA and receipt.get("topology") not in _TOPOLOGIES:
        raise EquivalentHeadError("equivalent-head receipt topology is invalid")
    string_fields = expected_fields - {
        "schema",
        "raw_delta_entries",
        "integration_parent_shas",
    }
    if any(
        not isinstance(receipt.get(field), str) or not receipt[field]
        for field in string_fields
    ):
        raise EquivalentHeadError("equivalent-head receipt contains an empty binding")
    oid_fields = {
        "recorded_base_sha",
        "recorded_base_tree_oid",
        "recorded_head_sha",
        "recorded_head_tree_oid",
        "observed_base_sha",
        "observed_base_tree_oid",
        "observed_head_sha",
        "observed_head_tree_oid",
        "merge_commit_sha",
        "merge_commit_tree_oid",
    }
    if any(not _OID.fullmatch(str(receipt[field])) for field in oid_fields):
        raise EquivalentHeadError("equivalent-head receipt contains a malformed OID")
    digest_fields = {"raw_delta_sha256", "provider_observation_digest"}
    if any(
        not re.fullmatch(r"[0-9a-f]{64}", str(receipt[field]))
        for field in digest_fields
    ):
        raise EquivalentHeadError("equivalent-head receipt contains a malformed digest")
    if (
        not isinstance(receipt.get("raw_delta_entries"), int)
        or isinstance(receipt.get("raw_delta_entries"), bool)
        or receipt["raw_delta_entries"] <= 0
    ):
        raise EquivalentHeadError("equivalent-head receipt entry count is invalid")
    if receipt["recorded_head_sha"] == receipt["observed_head_sha"]:
        raise EquivalentHeadError("equivalent-head receipt did not replace the head")
    if receipt["recorded_base_sha"] == receipt["observed_base_sha"]:
        raise EquivalentHeadError("equivalent-head receipt did not advance the base")
    if schema == RECEIPT_SCHEMA:
        expected_parents = [receipt["observed_base_sha"]]
        if receipt["topology"] == TWO_PARENT_HEAD_MERGE:
            expected_parents.append(receipt["observed_head_sha"])
        elif receipt["merge_commit_sha"] == receipt["observed_head_sha"]:
            raise EquivalentHeadError(
                "equivalent-head integration copy must differ from the observed head"
            )
        if receipt.get("integration_parent_shas") != expected_parents:
            raise EquivalentHeadError(
                "equivalent-head receipt integration parents contradict its topology"
            )
        if receipt["merge_commit_tree_oid"] != receipt["observed_head_tree_oid"]:
            raise EquivalentHeadError(
                "equivalent-head receipt integration tree is contradictory"
            )
    return dict(receipt)


def validate_equivalent_head_receipt(
    ledger: Mapping[str, Any],
    ticket_id: str,
    receipt: Mapping[str, Any],
) -> dict[str, Any]:
    normalized = _validate_shape(receipt)
    tickets = ledger.get("tickets")
    ticket = tickets.get(ticket_id) if isinstance(tickets, Mapping) else None
    pr = ticket.get("pr") if isinstance(ticket, Mapping) else None
    lineage = ticket.get("delivery_lineage") if isinstance(ticket, Mapping) else None
    if not isinstance(pr, Mapping) or not isinstance(lineage, Mapping):
        raise EquivalentHeadError("equivalent-head receipt lost its PR lineage")
    expected = {
        "repository_identity": ledger.get("repo"),
        "provider": ledger.get("provider"),
        "pr_id": pr.get("pr_id"),
        "branch": pr.get("branch"),
        "base_branch": lineage.get("base_branch"),
        "recorded_base_sha": lineage.get("base_sha"),
        "observed_head_sha": pr.get("head_sha"),
    }
    if any(normalized.get(key) != value for key, value in expected.items()):
        raise EquivalentHeadError("equivalent-head receipt binding is stale")
    if lineage.get("head_sha") != normalized["observed_head_sha"]:
        raise EquivalentHeadError("equivalent-head delivery lineage is stale")
    return normalized


def build_equivalent_head_receipt(
    worktree: Path,
    ledger: Mapping[str, Any],
    ticket_id: str,
    provider_observation: Mapping[str, Any],
    *,
    actor: str,
    evidence: str,
    boundary_guard: Callable[[str], None],
) -> dict[str, Any]:
    tickets = ledger.get("tickets")
    ticket = tickets.get(ticket_id) if isinstance(tickets, Mapping) else None
    pr = ticket.get("pr") if isinstance(ticket, Mapping) else None
    lineage = ticket.get("delivery_lineage") if isinstance(ticket, Mapping) else None
    if not isinstance(pr, Mapping) or not isinstance(lineage, Mapping):
        raise EquivalentHeadError("equivalent-head proof requires PR delivery lineage")
    if not actor or not evidence:
        raise EquivalentHeadError("equivalent-head proof requires actor and evidence")
    expected_observation = {
        "schema": 1,
        "provider": ledger.get("provider"),
        "operation": "get-pr-state",
        "evidence_class": "live",
        "observed": True,
        "pr_id": pr.get("pr_id"),
        "branch": pr.get("branch"),
        "base": lineage.get("base_branch"),
        "state": "merged",
    }
    if any(
        provider_observation.get(key) != value
        for key, value in expected_observation.items()
    ):
        raise EquivalentHeadError(
            "equivalent-head provider observation contradicts the recorded PR"
        )
    recorded_base = _require_oid(lineage.get("base_sha"), "recorded base")
    recorded_head = _require_oid(pr.get("head_sha"), "recorded head")
    observed_head = _require_oid(
        provider_observation.get("head_sha"), "observed head"
    )
    merge_commit = _require_oid(
        provider_observation.get("merge_commit_sha"), "merge commit"
    )
    if observed_head == recorded_head:
        raise EquivalentHeadError("equivalent-head proof requires a different head")

    for oid in (recorded_base, recorded_head, observed_head, merge_commit):
        _ensure_commit(worktree, oid, boundary_guard=boundary_guard)
    recorded_parents, recorded_head_tree = _commit(worktree, recorded_head)
    _, recorded_base_tree = _commit(worktree, recorded_base)
    observed_parents, observed_head_tree = _commit(worktree, observed_head)
    integration_parents, integration_tree = _commit(worktree, merge_commit)
    if recorded_parents != [recorded_base]:
        raise EquivalentHeadError(
            "equivalent-head recorded delivery is not one commit on its recorded base"
        )
    if len(integration_parents) == 2 and integration_parents[1] == observed_head:
        topology = TWO_PARENT_HEAD_MERGE
        observed_base = integration_parents[0]
    elif len(integration_parents) == 1:
        topology = SINGLE_PARENT_INTEGRATION_COPY
        observed_base = integration_parents[0]
        if merge_commit == observed_head:
            raise EquivalentHeadError(
                "equivalent-head integration copy must differ from the observed head"
            )
    else:
        raise EquivalentHeadError(
            "equivalent-head provider integration topology is unsupported"
        )
    _ensure_commit(worktree, observed_base, boundary_guard=boundary_guard)
    _, observed_base_tree = _commit(worktree, observed_base)
    if observed_parents != [observed_base]:
        raise EquivalentHeadError(
            "equivalent-head observed delivery is not one commit on the integration base"
        )
    if observed_base == recorded_base:
        raise EquivalentHeadError("equivalent-head provider base did not advance")
    if integration_tree != observed_head_tree:
        raise EquivalentHeadError(
            "equivalent-head integration commit tree differs from the observed head tree"
        )

    recorded_delta, recorded_entries = _raw_delta(
        worktree, recorded_base, recorded_head
    )
    observed_delta, observed_entries = _raw_delta(
        worktree, observed_base, observed_head
    )
    integration_delta, integration_entries = _raw_delta(
        worktree, observed_base, merge_commit
    )
    if (
        recorded_entries != observed_entries
        or recorded_entries != integration_entries
        or recorded_delta != observed_delta
        or recorded_delta != integration_delta
    ):
        raise EquivalentHeadError(
            "equivalent-head raw tree transitions are not byte-identical"
        )
    digest = hashlib.sha256(recorded_delta).hexdigest()
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "topology": topology,
        "integration_parent_shas": integration_parents,
        "repository_identity": ledger.get("repo"),
        "provider": ledger.get("provider"),
        "pr_id": pr.get("pr_id"),
        "branch": pr.get("branch"),
        "base_branch": lineage.get("base_branch"),
        "recorded_base_sha": recorded_base,
        "recorded_base_tree_oid": recorded_base_tree,
        "recorded_head_sha": recorded_head,
        "recorded_head_tree_oid": recorded_head_tree,
        "observed_base_sha": observed_base,
        "observed_base_tree_oid": observed_base_tree,
        "observed_head_sha": observed_head,
        "observed_head_tree_oid": observed_head_tree,
        "merge_commit_sha": merge_commit,
        "merge_commit_tree_oid": integration_tree,
        "raw_delta_sha256": digest,
        "raw_delta_entries": recorded_entries,
        "provider_observation_digest": canonical_digest(provider_observation),
        "actor": actor,
        "evidence": evidence,
    }
    return _validate_shape(receipt)
