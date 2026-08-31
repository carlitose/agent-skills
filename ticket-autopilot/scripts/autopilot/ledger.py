from __future__ import annotations

import copy
import hashlib
import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, IO, Iterator

from .leaf_protocol import (
    LeafProtocolError,
    record_leaf_result as reduce_leaf_result,
    rebuild_leaf_budget_epoch,
    validate_handoff_progression,
    validate_leaf_budget,
    verification_checkpoint_identity,
)
from .candidate_contract import (
    CandidateContractError,
    delivery_lineage,
    semantic_candidate,
)
from .docs_only_contract import DocsOnlyError, normalize_docs_only_receipt
from .equivalent_head import (
    DELIVERY_STEP as EQUIVALENT_HEAD_DELIVERY_STEP,
    EquivalentHeadError,
    validate_equivalent_head_receipt,
)
from .file_lock import acquire_file_lock, release_file_lock
from .history_codec import (
    HistoryCodecError,
    compact_event_history,
    decode_history_event,
    history_event_hash,
    virtual_history_event,
)
from .reconciliation_intent import (
    PREPARATION_REFRESH_HISTORY_STEP,
    PREPARATION_REFRESH_STEP,
    ReconciliationIntentError,
    validate_preparation_refresh,
)
from .terminal_integration import (
    TerminalIntegrationError,
    canonical_digest,
    terminal_branch,
    validate_terminal_integration_proof,
)


LEDGER_VERSION = 4
ENVELOPE_VERSION = 1
AUTONOMOUS_GRANT_VERSION = 1
COMPLETION_PROJECTION_GRANT_VERSION = 1
COMPLETION_PROJECTION_DELIVERY_HEAD_PROOF_VERSION = 1
WIKI_SYNC_GRANT_VERSION = 1
PIPELINE_STAGES = (
    "implement",
    "simplify",
    "review",
    "qa-plan",
    "qa-execute",
    "verify",
    "finalize",
)
HEAD_BOUND_MERGE_DELIVERY_STEPS = (
    "autonomous-eligibility",
    "merge-intent",
    "merge-observation",
    "merge-attempt",
    "merge-mutation",
    "merge-readback",
    "merge-progress",
    "integration",
    "terminal-integration",
    EQUIVALENT_HEAD_DELIVERY_STEP,
)
KNOWN_LEDGER_EVENTS = frozenset(
    {
        "run-initialized",
        "ticket-resumed",
        "ticket-activated",
        "candidate-adopted",
        "candidate-invalidated",
        "docs-only-candidate-adopted",
        "docs-only-candidate-rejected",
        "leaf-result-recorded",
        "revalidation-budget-repaired",
        "evidence-cache-decision",
        "stage-passed",
        "quality-failed",
        "ticket-failed",
        "gate-opened",
        "gate-refreshed",
        "gate-passed",
        "effect-applied",
        "delivery-recorded",
        "delivery-candidate-recorded",
        "delivery-revalidation-required",
        "reconciliation-revalidation-required",
        "reconciliation-delivery-revalidation-required",
        "reconciliation-candidate-sealed",
        "reconciliation-target-refreshed",
        "reconciliation-equivalent",
        "pr-opened",
        "pr-head-updated",
        "external-head-equivalent",
        "merge-authorized",
        "autonomous-merge-granted",
        "completion-projection-granted",
        "completion-projection-gate-resolved",
        "external-merge-integrated",
        "ticket-integrated",
        "ticket-disposition-changed",
        "run-paused",
        "run-unpaused",
        "ledger-v3-lifecycle-migrated",
        "run-aborted",
        "worktree-cleaned",
    }
)
LEGACY_V3_EVENTS = frozenset(
    {
        "run-initialized",
        "ticket-resumed",
        "ticket-activated",
        "candidate-adopted",
        "candidate-invalidated",
        "leaf-result-recorded",
        "evidence-cache-decision",
        "stage-passed",
        "quality-failed",
        "ticket-failed",
        "gate-opened",
        "gate-refreshed",
        "gate-passed",
        "effect-applied",
        "delivery-recorded",
        "delivery-candidate-recorded",
        "delivery-revalidation-required",
        "reconciliation-revalidation-required",
        "reconciliation-equivalent",
        "pr-opened",
        "pr-head-updated",
        "merge-authorized",
        "external-merge-integrated",
        "ticket-integrated",
        "run-aborted",
        "worktree-cleaned",
    }
)

_UNKNOWN_LEAF_EXECUTION = {
    "mode": "unknown",
    "isolation": "unknown",
    "parallel": False,
    "authority_ref": None,
}


def _legacy_leaf_execution_projection(value: dict[str, Any]) -> dict[str, Any]:
    """Project only the execution field absent from pre-OI-09 leaf records."""
    projected = copy.deepcopy(value)
    projected.setdefault("execution", dict(_UNKNOWN_LEAF_EXECUTION))
    return projected


class LedgerError(RuntimeError):
    """A persisted run ledger is absent, locked, corrupt, or incompatible."""


def _legacy_ticket_completed(
    document: dict[str, Any], ticket_id: str, ticket: dict[str, Any]
) -> bool:
    """Infer disposition only from durable v3 completion evidence."""
    mode = document.get("ticket_source_mode")
    completion_compatible_state = ticket.get("state") in {
        "gated",
        "verified",
        "pr-open",
        "integrated",
    }
    applied_effects = [
        effect.get("effect")
        for effect in document.get("effects", {}).values()
        if isinstance(effect, dict)
        and effect.get("ticket_id") == ticket_id
        and effect.get("state") == "applied"
        and effect.get("effect")
        in {"move-done-and-stage", "move-done-and-summarize-external"}
    ]
    ignored_receipt = ticket.get("delivery", {}).get(
        "ignored-finalization-applied"
    )
    ignored_applied = (
        isinstance(ignored_receipt, dict)
        and ignored_receipt.get("state") == "applied"
    )
    if len(applied_effects) > 1:
        raise LedgerError("legacy completion evidence is contradictory")
    if applied_effects == ["move-done-and-stage"] and mode != "tracked":
        raise LedgerError("legacy completion evidence contradicts source mode")
    if (
        applied_effects == ["move-done-and-summarize-external"]
        or ignored_applied
    ) and mode != "ignored":
        raise LedgerError("legacy completion evidence contradicts source mode")
    if ignored_receipt is not None and not ignored_applied:
        raise LedgerError("legacy ignored finalization receipt is ambiguous")
    durable_finalization = bool(applied_effects) or ignored_applied
    if durable_finalization and not completion_compatible_state:
        raise LedgerError("legacy completion evidence contradicts ticket state")
    return bool(ticket.get("preexisting_integrated")) or (
        ticket.get("state") == "integrated"
    ) or durable_finalization


def _migrate_legacy_ticket(
    document: dict[str, Any], ticket_id: str, ticket: dict[str, Any]
) -> None:
    completed = _legacy_ticket_completed(document, ticket_id, ticket)
    ticket["disposition"] = "completed" if completed else "open"
    ticket["attempt_outcome"] = None
    ticket["stop_reason"] = None
    ticket["disposition_receipt"] = None
    source_relative_path = ticket["source_relative_path"]
    ticket["current_source_relative_path"] = (
        f"done/{source_relative_path.rsplit('/', 1)[-1]}"
        if completed
        else source_relative_path
    )


def autonomous_merge_grant_matches_run(document: dict[str, Any]) -> bool:
    grant = document.get("autonomous_merge_grant")
    expected_binding = {
        "schema": 1,
        "policy_version": AUTONOMOUS_GRANT_VERSION,
        "repository_identity": document.get("repo"),
        "run_id": document.get("run_id"),
        "ticket_set_digest": document.get("snapshot_manifest_digest"),
        "provider": document.get("provider"),
        "policy": "autonomous",
    }
    return (
        isinstance(grant, dict)
        and set(grant) == {*expected_binding, "actor", "evidence"}
        and all(
            grant.get(key) == value for key, value in expected_binding.items()
        )
        and all(
            isinstance(grant.get(key), str) and bool(grant[key])
            for key in ("actor", "evidence")
        )
    )


def completion_projection_destination(
    document: dict[str, Any], ticket_id: str
) -> str | None:
    tickets = document.get("tickets")
    ticket = tickets.get(ticket_id) if isinstance(tickets, dict) else None
    repo = document.get("repo")
    folder = document.get("ticket_folder")
    source = ticket.get("source_relative_path") if isinstance(ticket, dict) else None
    if not all(isinstance(value, str) and value for value in (repo, folder, source)):
        return None
    source_path = Path(source)
    if source_path.is_absolute() or ".." in source_path.parts:
        return None
    try:
        folder_relative = Path(folder).resolve().relative_to(Path(repo).resolve())
    except ValueError:
        return None
    return (folder_relative / "done" / source_path.name).as_posix()


def _completion_projection_grant_matches_ticket(
    document: dict[str, Any], ticket_id: str, grant: object
) -> bool:
    tickets = document.get("tickets")
    ticket = tickets.get(ticket_id) if isinstance(tickets, dict) else None
    destination = completion_projection_destination(document, ticket_id)
    if not isinstance(ticket, dict) or destination is None:
        return False
    candidate = grant.get("candidate_ref") if isinstance(grant, dict) else None
    expected = {
        "schema": 1,
        "policy_version": COMPLETION_PROJECTION_GRANT_VERSION,
        "repository_identity": document.get("repo"),
        "run_id": document.get("run_id"),
        "ticket_id": ticket_id,
        "snapshot_manifest_digest": document.get("snapshot_manifest_digest"),
        "ticket_digest": ticket.get("ticket_digest"),
        "destination_relative_path": destination,
    }
    return (
        isinstance(grant, dict)
        and set(grant) == {*expected, "candidate_ref", "actor", "evidence"}
        and all(grant.get(key) == value for key, value in expected.items())
        and isinstance(candidate, dict)
        and set(candidate)
        == {
            "contract_version",
            "base_tree_oid",
            "candidate_tree_oid",
            "ticket_digest",
        }
        and candidate.get("contract_version") == 2
        and candidate.get("ticket_digest") == ticket.get("ticket_digest")
        and all(
            isinstance(candidate.get(key), str) and bool(candidate[key])
            for key in ("base_tree_oid", "candidate_tree_oid", "ticket_digest")
        )
        and all(
            isinstance(grant.get(key), str) and bool(grant[key].strip())
            for key in ("actor", "evidence")
        )
    )


def completion_projection_grant_entry(
    grant: dict[str, Any],
    *,
    sequence: int,
    predecessor_grant_id: str | None,
) -> dict[str, Any]:
    """Wrap one immutable grant with deterministic append-only lineage."""

    return {
        "schema": 1,
        "sequence": sequence,
        "grant_id": canonical_digest(grant),
        "predecessor_grant_id": predecessor_grant_id,
        "grant": copy.deepcopy(grant),
    }


def completion_projection_grant_entries(
    document: dict[str, Any], ticket_id: str
) -> list[dict[str, Any]] | None:
    """Return validated grant lineage, virtualizing a legacy singleton as entry one."""

    tickets = document.get("tickets")
    ticket = tickets.get(ticket_id) if isinstance(tickets, dict) else None
    if not isinstance(ticket, dict):
        return None
    active = ticket.get("completion_projection_grant")
    stored = ticket.get("completion_projection_grants")
    if stored is None:
        if active is None:
            return []
        if not _completion_projection_grant_matches_ticket(
            document, ticket_id, active
        ):
            return None
        return [
            completion_projection_grant_entry(
                active, sequence=1, predecessor_grant_id=None
            )
        ]
    if not isinstance(stored, list):
        return None
    entries: list[dict[str, Any]] = []
    predecessor: str | None = None
    seen: set[str] = set()
    for sequence, entry in enumerate(stored, 1):
        if not isinstance(entry, dict) or set(entry) != {
            "schema",
            "sequence",
            "grant_id",
            "predecessor_grant_id",
            "grant",
        }:
            return None
        grant = entry.get("grant")
        grant_id = canonical_digest(grant) if isinstance(grant, dict) else None
        if (
            entry.get("schema") != 1
            or entry.get("sequence") != sequence
            or entry.get("grant_id") != grant_id
            or entry.get("predecessor_grant_id") != predecessor
            or not isinstance(grant_id, str)
            or grant_id in seen
            or not _completion_projection_grant_matches_ticket(
                document, ticket_id, grant
            )
        ):
            return None
        entries.append(copy.deepcopy(entry))
        seen.add(grant_id)
        predecessor = grant_id
    if (not entries and active is not None) or (
        entries and active != entries[-1]["grant"]
    ):
        return None
    return entries


def completion_projection_grant_matches_ticket(
    document: dict[str, Any], ticket_id: str
) -> bool:
    return completion_projection_grant_entries(document, ticket_id) is not None


def _completion_projection_oid(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) in {40, 64}
        and value == value.lower()
        and all(character in "0123456789abcdef" for character in value)
    )


def completion_projection_terminal_branch(
    document: dict[str, Any], ticket_id: str
) -> str | None:
    """Resolve the terminal target, including legacy integrated-parent runs."""

    tickets = document.get("tickets")
    ticket = tickets.get(ticket_id) if isinstance(tickets, dict) else None
    if not isinstance(ticket, dict):
        return None
    try:
        return terminal_branch(document, ticket_id)
    except TerminalIntegrationError:
        blockers = ticket.get("blocked_by")
        blockers_terminal = isinstance(blockers, list) and all(
            isinstance(tickets.get(blocker), dict)
            and tickets[blocker].get("state") == "integrated"
            for blocker in blockers
        )
        branch_receipt = ticket.get("delivery", {}).get("branch")
        fallback = (
            branch_receipt.get("base")
            if blockers_terminal and isinstance(branch_receipt, dict)
            else None
        )
        return fallback if isinstance(fallback, str) and fallback else None


def completion_projection_delivery_head_proof(
    document: dict[str, Any],
    ticket_id: str,
    *,
    gate_id: str,
    branch: str,
    head_sha: str,
    head_tree_oid: str,
    head_parent_sha: str,
    head_parent_tree_oid: str,
    head_commit_message: str,
    terminal_branch: str,
    terminal_sha: str,
    terminal_tree_oid: str,
) -> dict[str, Any]:
    """Build one proof for an unintegrated runner-prepared delivery head."""

    tickets = document.get("tickets")
    ticket = tickets.get(ticket_id) if isinstance(tickets, dict) else None
    entries = completion_projection_grant_entries(document, ticket_id)
    gate = document.get("gates", {}).get(gate_id)
    delivery = ticket.get("delivery") if isinstance(ticket, dict) else None
    prepared = delivery.get("prepared") if isinstance(delivery, dict) else None
    prepared_candidate = (
        prepared.get("candidate_ref") if isinstance(prepared, dict) else None
    )
    active = entries[-1] if entries else None
    grant = ticket.get("completion_projection_grant") if isinstance(ticket, dict) else None
    if (
        not isinstance(ticket, dict)
        or not isinstance(gate, dict)
        or not isinstance(delivery, dict)
        or not isinstance(prepared_candidate, dict)
        or not isinstance(active, dict)
        or not isinstance(grant, dict)
    ):
        raise ValueError(
            "completion projection delivery-head proof prerequisites are missing"
        )
    payload = {
        "schema": COMPLETION_PROJECTION_DELIVERY_HEAD_PROOF_VERSION,
        "repository_identity": document.get("repo"),
        "run_id": document.get("run_id"),
        "ticket_id": ticket_id,
        "snapshot_manifest_digest": document.get("snapshot_manifest_digest"),
        "ticket_digest": ticket.get("ticket_digest"),
        "grant_id": active["grant_id"],
        "grant_sequence": active["sequence"],
        "candidate_ref": copy.deepcopy(ticket.get("candidate_ref")),
        "destination_relative_path": grant.get("destination_relative_path"),
        "gate_id": gate_id,
        "gate_details_digest": canonical_digest(gate.get("details", {})),
        "branch": branch,
        "head_sha": head_sha,
        "head_tree_oid": head_tree_oid,
        "head_parent_sha": head_parent_sha,
        "head_parent_tree_oid": head_parent_tree_oid,
        "head_commit_message": head_commit_message,
        "prepared_candidate_ref": copy.deepcopy(prepared_candidate),
        "terminal_branch": terminal_branch,
        "terminal_sha": terminal_sha,
        "terminal_tree_oid": terminal_tree_oid,
        "terminal_destination_state": "absent",
        "head_reachable_from_terminal": False,
        "provenance": "runner-prepared-delivery-head",
    }
    proof = {**payload, "proof_id": canonical_digest(payload)}
    if not completion_projection_delivery_head_proof_matches(
        document, ticket_id, gate_id, proof
    ):
        raise ValueError("completion projection delivery-head proof is invalid")
    return proof


def completion_projection_delivery_head_proof_matches(
    document: dict[str, Any],
    ticket_id: str,
    gate_id: str,
    proof: object,
) -> bool:
    """Validate a tracked-base gate proof against its exact pre-resolution state."""

    tickets = document.get("tickets")
    ticket = tickets.get(ticket_id) if isinstance(tickets, dict) else None
    entries = completion_projection_grant_entries(document, ticket_id)
    gates = document.get("gates")
    gate = gates.get(gate_id) if isinstance(gates, dict) else None
    delivery = ticket.get("delivery") if isinstance(ticket, dict) else None
    branch_receipt = delivery.get("branch") if isinstance(delivery, dict) else None
    prepared = delivery.get("prepared") if isinstance(delivery, dict) else None
    prepared_candidate = (
        prepared.get("candidate_ref") if isinstance(prepared, dict) else None
    )
    grant = ticket.get("completion_projection_grant") if isinstance(ticket, dict) else None
    active = entries[-1] if entries else None
    if not all(
        isinstance(value, dict)
        for value in (
            ticket,
            gate,
            delivery,
            branch_receipt,
            prepared_candidate,
            grant,
            active,
            proof,
        )
    ):
        return False
    assert isinstance(proof, dict)
    payload = {
        key: copy.deepcopy(value)
        for key, value in proof.items()
        if key != "proof_id"
    }
    expected_terminal_branch = completion_projection_terminal_branch(
        document, ticket_id
    )
    if expected_terminal_branch is None:
        return False
    details = gate.get("details")
    candidate = ticket.get("candidate_ref")
    expected_fields = {
        "schema",
        "repository_identity",
        "run_id",
        "ticket_id",
        "snapshot_manifest_digest",
        "ticket_digest",
        "grant_id",
        "grant_sequence",
        "candidate_ref",
        "destination_relative_path",
        "gate_id",
        "gate_details_digest",
        "branch",
        "head_sha",
        "head_tree_oid",
        "head_parent_sha",
        "head_parent_tree_oid",
        "head_commit_message",
        "prepared_candidate_ref",
        "terminal_branch",
        "terminal_sha",
        "terminal_tree_oid",
        "terminal_destination_state",
        "head_reachable_from_terminal",
        "provenance",
        "proof_id",
    }
    return (
        set(proof) == expected_fields
        and proof.get("schema")
        == COMPLETION_PROJECTION_DELIVERY_HEAD_PROOF_VERSION
        and proof.get("repository_identity") == document.get("repo")
        and proof.get("run_id") == document.get("run_id")
        and proof.get("ticket_id") == ticket_id
        and proof.get("snapshot_manifest_digest")
        == document.get("snapshot_manifest_digest")
        and proof.get("ticket_digest") == ticket.get("ticket_digest")
        and proof.get("grant_id") == active.get("grant_id")
        and proof.get("grant_sequence") == active.get("sequence")
        and active.get("grant") == grant
        and proof.get("candidate_ref") == candidate == grant.get("candidate_ref")
        and proof.get("destination_relative_path")
        == grant.get("destination_relative_path")
        and proof.get("gate_id") == gate_id
        and gate.get("ticket_id") == ticket_id
        and gate.get("category") == "source-mode-drift"
        and gate.get("state") == "open"
        and isinstance(details, dict)
        and details.get("ticket_id") == ticket_id
        and details.get("snapshot_classification") == "ignored"
        and details.get("observed_classification") == "tracked"
        and details.get("base_classification") == "tracked"
        and details.get("source_path") == grant.get("destination_relative_path")
        and proof.get("gate_details_digest") == canonical_digest(details)
        and proof.get("branch") == branch_receipt.get("branch")
        and proof.get("prepared_candidate_ref") == prepared_candidate
        and prepared_candidate.get("candidate_tree_oid")
        == proof.get("head_tree_oid")
        and prepared_candidate.get("base_tree_oid")
        == proof.get("head_parent_tree_oid")
        == candidate.get("base_tree_oid")
        and proof.get("head_commit_message") == f"ticket {ticket_id}: complete"
        and prepared_candidate.get("ticket_digest")
        == ticket.get("ticket_digest")
        and proof.get("terminal_branch") == expected_terminal_branch
        and proof.get("terminal_destination_state") == "absent"
        and proof.get("head_reachable_from_terminal") is False
        and proof.get("provenance") == "runner-prepared-delivery-head"
        and all(
            _completion_projection_oid(proof.get(field))
            for field in (
                "head_sha",
                "head_tree_oid",
                "head_parent_sha",
                "head_parent_tree_oid",
                "terminal_sha",
                "terminal_tree_oid",
            )
        )
        and proof.get("head_sha") != proof.get("terminal_sha")
        and proof.get("proof_id") == canonical_digest(payload)
    )


def _verified_bundle_request_ref(ticket: object) -> dict[str, str] | None:
    if not isinstance(ticket, dict):
        return None
    evidence = (
        ticket.get("leaf_results", {})
        .get("verify", {})
        .get("quality", {})
        .get("evidence", [])
    )
    if not isinstance(evidence, list):
        return None
    by_id = {
        item.get("id"): item for item in evidence if isinstance(item, dict)
    }
    bundle = by_id.get("verification-checkpoint:bundle-validated")
    handoff = by_id.get("verification-checkpoint:handoff-ready")
    candidate = ticket.get("candidate_ref")
    if not isinstance(bundle, dict) or not isinstance(handoff, dict):
        return None
    if any(
        item.get("result") != "pass"
        or item.get("candidate_ref") != candidate
        or not isinstance(item.get("artifact"), str)
        or not item["artifact"]
        or not isinstance(item.get("sha256"), str)
        or not item["sha256"]
        for item in (bundle, handoff)
    ):
        return None
    return {
        "artifact": str(Path(bundle["artifact"]).resolve()),
        "sha256": bundle["sha256"],
        "handoff_sha256": handoff["sha256"],
    }


def wiki_sync_merge_grant_matches_run(document: dict[str, Any]) -> bool:
    policy = document.get("wiki_sync_policy")
    if policy is None:
        return True
    if (
        not isinstance(policy, dict)
        or set(policy) != {"schema", "merge_policy", "autonomous_grant"}
        or policy.get("schema") != 1
        or policy.get("merge_policy") not in {"manual", "autonomous"}
    ):
        return False
    grant = policy.get("autonomous_grant")
    if policy["merge_policy"] == "manual":
        return grant is None
    expected = {
        "schema": 1,
        "policy_version": WIKI_SYNC_GRANT_VERSION,
        "repository_identity": document.get("repo"),
        "run_id": document.get("run_id"),
        "ticket_set_digest": document.get("snapshot_manifest_digest"),
        "provider": document.get("provider"),
        "policy": "autonomous",
        "scope": "wiki-sync-v1",
    }
    return (
        isinstance(grant, dict)
        and set(grant) == {*expected, "actor", "evidence"}
        and all(grant.get(key) == value for key, value in expected.items())
        and all(
            isinstance(grant.get(key), str) and bool(grant[key])
            for key in ("actor", "evidence")
        )
    )


def _pr_body_rebind_is_closed(
    previous: object,
    current: object,
    reconcile_request: object,
    current_ticket: object,
    *,
    legacy: bool = False,
) -> bool:
    if (
        not isinstance(previous, dict)
        or not isinstance(current, dict)
        or not isinstance(reconcile_request, dict)
    ):
        return False
    if previous.get("schema") not in {1, 2} or current.get("schema") != 2:
        return False
    receipt_fields = {
        "schema",
        "request_hash",
        "expected_head_sha",
        "body_sha256",
        "body_path",
        "bundle_sha256",
        "bundle_path",
        "verification_audit_root",
    }
    if set(previous) != receipt_fields | (
        {"lineage_rebinds"} if previous["schema"] == 2 else set()
    ) or set(current) != receipt_fields | {"lineage_rebinds"}:
        return False
    previous_lineage = previous.get("lineage_rebinds", [])
    current_lineage = current.get("lineage_rebinds")
    if (
        not isinstance(previous_lineage, list)
        or not isinstance(current_lineage, list)
        or len(current_lineage) != len(previous_lineage) + 1
        or current_lineage[:-1] != previous_lineage
    ):
        return False
    latest = current_lineage[-1]
    base_lineage_fields = {
        "schema",
        "old_head",
        "new_head",
        "old_body_sha256",
        "new_body_sha256",
        "render_request_hash",
        "old_receipt",
    }
    if not isinstance(latest, dict):
        return False
    closure = {
        "old_head": previous.get("expected_head_sha"),
        "new_head": reconcile_request.get("expected_head_sha"),
        "old_body_sha256": previous.get("body_sha256"),
        "new_body_sha256": current.get("body_sha256"),
        "render_request_hash": reconcile_request.get("request_hash"),
    }
    common_closed = (
        latest.get("old_receipt") == previous
        and reconcile_request.get("reconciled_from_head")
        == previous.get("expected_head_sha")
        and current.get("request_hash") == reconcile_request.get("request_hash")
        and current.get("expected_head_sha")
        == reconcile_request.get("expected_head_sha")
        and all(
            isinstance(value, str) and bool(value)
            for value in closure.values()
        )
        and all(latest.get(key) == value for key, value in closure.items())
    )
    if not common_closed:
        return False
    extended_fields = base_lineage_fields | {
        "old_bundle_sha256",
        "new_bundle_sha256",
        "old_bundle_path",
        "new_bundle_path",
        "old_verification_audit_root",
        "new_verification_audit_root",
    }
    if latest.get("schema") == 1 and set(latest) == base_lineage_fields:
        return all(
            current.get(field) == previous.get(field)
            for field in (
                "bundle_sha256",
                "bundle_path",
                "verification_audit_root",
            )
        )
    legacy_bundle_fields = extended_fields - {
        "old_verification_audit_root",
        "new_verification_audit_root",
    }
    legacy_bundle_only = (
        legacy
        and latest.get("schema") == 1
        and set(latest) == legacy_bundle_fields
    )
    legacy_extended = legacy_bundle_only or (
        legacy
        and latest.get("schema") == 1
        and set(latest) == extended_fields
    )
    if not legacy_extended and (
        latest.get("schema") != 2 or set(latest) != extended_fields
    ):
        return False
    if not isinstance(current_ticket, dict):
        return False
    request_payload = {
        key: value
        for key, value in reconcile_request.items()
        if key != "request_hash"
    }
    request_hash = hashlib.sha256(_canonical_bytes(request_payload)).hexdigest()
    expected_bundle_ref = _verified_bundle_request_ref(current_ticket)
    enhanced_closure = {
        "old_bundle_sha256": previous.get("bundle_sha256"),
        "new_bundle_sha256": current.get("bundle_sha256"),
        "old_bundle_path": previous.get("bundle_path"),
        "new_bundle_path": current.get("bundle_path"),
        "old_verification_audit_root": previous.get(
            "verification_audit_root"
        ),
        "new_verification_audit_root": current.get(
            "verification_audit_root"
        ),
    }
    lineage_closure = (
        {
            key: value
            for key, value in enhanced_closure.items()
            if key
            not in {
                "old_verification_audit_root",
                "new_verification_audit_root",
            }
        }
        if legacy_bundle_only
        else enhanced_closure
    )
    return (
        reconcile_request.get("request_hash") == request_hash
        and reconcile_request.get("candidate_ref")
        == current_ticket.get("candidate_ref")
        and reconcile_request.get("artifact_generation")
        == current_ticket.get("artifact_generation")
        and expected_bundle_ref is not None
        and reconcile_request.get("verification_bundle")
        == expected_bundle_ref
        and (
            legacy_extended
            or reconcile_request.get("bundle_sha256")
            == current.get("bundle_sha256")
        )
        and reconcile_request.get("required_head_literal")
        == current.get("expected_head_sha")
        and (
            not legacy_bundle_only
            or current.get("verification_audit_root")
            == previous.get("verification_audit_root")
        )
        and all(
            isinstance(value, str) and bool(value)
            for value in lineage_closure.values()
        )
        and all(
            latest.get(key) == value
            for key, value in lineage_closure.items()
        )
    )


def _acquire_file_lock(handle: IO[str]) -> None:
    """Non-blocking: a second runner must fail fast, not queue behind the first."""

    acquire_file_lock(handle, blocking=False)


def _release_file_lock(handle: IO[str]) -> None:
    release_file_lock(handle)


def _canonical_bytes(document: dict[str, Any]) -> bytes:
    return json.dumps(
        document, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


class AtomicLedger:
    def __init__(self, path: Path):
        self.path = path
        self.lock_path = path.with_suffix(path.suffix + ".lock")
        self._loaded_revision: str | None = None
        self._lock_depth = 0

    @contextmanager
    def locked(self) -> Iterator[None]:
        if self._lock_depth:
            self._lock_depth += 1
            try:
                yield
            finally:
                self._lock_depth -= 1
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.lock_path.open("a+", encoding="ascii") as handle:
            try:
                _acquire_file_lock(handle)
            except OSError as error:
                raise LedgerError(f"ledger is locked: {self.lock_path}") from error
            try:
                self._lock_depth = 1
                handle.seek(0)
                handle.truncate()
                handle.write(f"{os.getpid()}\n")
                handle.flush()
                os.fsync(handle.fileno())
                yield
            finally:
                self._lock_depth = 0
                _release_file_lock(handle)

    @contextmanager
    def run_locked(self) -> Iterator[None]:
        """Hold one process-crash-releasing lock across decision and effects."""
        with self.locked():
            yield

    @staticmethod
    def _atomic_write(path: Path, content: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, raw_tmp = tempfile.mkstemp(
            prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
        )
        tmp_path = Path(raw_tmp)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_path, path)
            if os.name != "nt":
                directory = os.open(path.parent, os.O_RDONLY)
                try:
                    os.fsync(directory)
                finally:
                    os.close(directory)
        finally:
            tmp_path.unlink(missing_ok=True)

    def save(self, document: dict[str, Any]) -> None:
        self._validate(document)
        payload_bytes = _canonical_bytes(document)
        envelope = {
            "envelope_schema": ENVELOPE_VERSION,
            "integrity": hashlib.sha256(payload_bytes).hexdigest(),
            "payload": document,
        }
        content = _canonical_bytes(envelope) + b"\n"
        with self.locked():
            if self._loaded_revision is not None and self.path.exists():
                current = hashlib.sha256(self.path.read_bytes()).hexdigest()
                if current != self._loaded_revision:
                    raise LedgerError(
                        "ledger changed since load; refusing to overwrite a newer state"
                    )
            self._atomic_write(self.path, content)
            self._loaded_revision = hashlib.sha256(content).hexdigest()

    def load(self) -> dict[str, Any]:
        with self.locked():
            try:
                content = self.path.read_bytes()
            except FileNotFoundError as error:
                raise LedgerError(f"ledger does not exist: {self.path}") from error
            try:
                envelope = json.loads(content)
            except json.JSONDecodeError as error:
                raise LedgerError(f"ledger is not valid JSON: {self.path}") from error
            envelope_schema = (
                envelope.get("envelope_schema")
                if isinstance(envelope, dict)
                else None
            )
            if (
                not isinstance(envelope, dict)
                or type(envelope_schema) is not int
                or envelope_schema != ENVELOPE_VERSION
                or set(envelope) != {"envelope_schema", "integrity", "payload"}
            ):
                raise LedgerError("ledger integrity envelope is invalid")
            document = envelope["payload"]
            actual = hashlib.sha256(_canonical_bytes(document)).hexdigest()
            if actual != envelope["integrity"]:
                raise LedgerError(f"ledger integrity mismatch: {self.path}")
            self._validate(document)
            self._loaded_revision = hashlib.sha256(content).hexdigest()
            return document

    def compact_history(self) -> dict[str, Any]:
        """Explicitly compact one validated ledger without changing audit hashes."""
        with self.locked():
            document = self.load()
            compacted = copy.deepcopy(document)
            try:
                compacted["history"] = compact_event_history(
                    compacted["history"]
                )
            except HistoryCodecError as error:
                raise LedgerError(str(error)) from error
            if compacted == document:
                return document
            self._validate(compacted)
            self.save(compacted)
            return compacted

    def migrate_lifecycle_v3(
        self,
        *,
        actor: str,
        evidence: str,
        input_ledger_sha256: str,
        recovery_manifest_digest: str,
        action_sequence: int,
    ) -> dict[str, Any]:
        """Upgrade one exact schema-3 ledger under immutable recovery authority."""
        for label, value in (("actor", actor), ("evidence", evidence)):
            if not isinstance(value, str) or not value or value != value.strip():
                raise LedgerError(f"lifecycle migration {label} must be non-empty and trimmed")
        for label, value in (
            ("input ledger digest", input_ledger_sha256),
            ("recovery manifest digest", recovery_manifest_digest),
        ):
            if (
                not isinstance(value, str)
                or len(value) != 64
                or value != value.lower()
                or any(character not in "0123456789abcdef" for character in value)
            ):
                raise LedgerError(f"lifecycle migration {label} must be a SHA-256")
        if type(action_sequence) is not int or action_sequence <= 0:
            raise LedgerError("lifecycle migration action sequence must be positive")
        authority = {
            "input_ledger_sha256": input_ledger_sha256,
            "actor": actor,
            "evidence": evidence,
            "recovery_manifest_digest": recovery_manifest_digest,
            "action_sequence": action_sequence,
        }
        with self.locked():
            try:
                content = self.path.read_bytes()
                envelope = json.loads(content)
            except FileNotFoundError as error:
                raise LedgerError(f"ledger does not exist: {self.path}") from error
            except json.JSONDecodeError as error:
                raise LedgerError(f"ledger is not valid JSON: {self.path}") from error
            if (
                not isinstance(envelope, dict)
                or set(envelope) != {"envelope_schema", "integrity", "payload"}
                or envelope.get("envelope_schema") != ENVELOPE_VERSION
                or not isinstance(envelope.get("payload"), dict)
            ):
                raise LedgerError("ledger integrity envelope is invalid")
            legacy = envelope["payload"]
            legacy_bytes = _canonical_bytes(legacy)
            if hashlib.sha256(legacy_bytes).hexdigest() != envelope["integrity"]:
                raise LedgerError(f"ledger integrity mismatch: {self.path}")
            current_sha256 = hashlib.sha256(content).hexdigest()
            if legacy.get("schema") == LEDGER_VERSION:
                self._validate(legacy)
                migration = legacy.get("legacy_lifecycle_migration")
                if not isinstance(migration, dict) or any(
                    migration.get(key) != value for key, value in authority.items()
                ):
                    raise LedgerError(
                        "schema-4 lifecycle migration receipt contradicts recovery authority"
                    )
                self._loaded_revision = current_sha256
                return legacy
            if current_sha256 != input_ledger_sha256:
                raise LedgerError("lifecycle migration input ledger digest changed")
            self._validate(legacy, allow_legacy_top=True)

            migrated = copy.deepcopy(legacy)
            migrated["schema"] = LEDGER_VERSION
            migrated["pause"] = None
            original_head = (
                legacy["history"][-1]["hash"]
                if legacy["history"]
                else "0" * 64
            )
            migrated["legacy_lifecycle_migration"] = {
                "from_schema": 3,
                "original_integrity": envelope["integrity"],
                "original_history_head": original_head,
                **authority,
            }
            for ticket_id, ticket in migrated.get("tickets", {}).items():
                _migrate_legacy_ticket(migrated, ticket_id, ticket)
            event = {
                "sequence": len(migrated["history"]) + 1,
                "event": "ledger-v3-lifecycle-migrated",
                "ticket_id": None,
                "details": {
                    "from_schema": 3,
                    "to_schema": LEDGER_VERSION,
                    "original_integrity": envelope["integrity"],
                    "original_history_head": original_head,
                    **authority,
                },
                "previous_hash": original_head,
                "snapshot": copy.deepcopy(
                    {key: value for key, value in migrated.items() if key != "history"}
                ),
            }
            event["hash"] = hashlib.sha256(_canonical_bytes(event)).hexdigest()
            migrated["history"].append(event)
            self._validate(migrated)
            payload_bytes = _canonical_bytes(migrated)
            rewritten = _canonical_bytes(
                {
                    "envelope_schema": ENVELOPE_VERSION,
                    "integrity": hashlib.sha256(payload_bytes).hexdigest(),
                    "payload": migrated,
                }
            ) + b"\n"
            self._atomic_write(self.path, rewritten)
            self._loaded_revision = hashlib.sha256(rewritten).hexdigest()
            return migrated

    @staticmethod
    def _validate(
        document: dict[str, Any], *, allow_legacy_top: bool = False
    ) -> None:
        if not isinstance(document, dict):
            raise LedgerError("ledger root must be an object")
        schema = document.get("schema")
        if schema == 3 and not allow_legacy_top:
            raise LedgerError(
                "ledger schema 3 requires explicit recovery: run "
                "migrate-run-lifecycle before resume or status"
            )
        if type(schema) is not int or schema not in (
            {3, LEDGER_VERSION} if allow_legacy_top else {LEDGER_VERSION}
        ):
            raise LedgerError(
                "ledger schema is incompatible with semantic CandidateRef v2: "
                f"{schema!r}; start a new run or use an "
                "explicit validated migration"
            )
        if schema == 3:
            AtomicLedger._validate_legacy_v3(document)
            return
        if not isinstance(document.get("run_id"), str) or not document["run_id"]:
            raise LedgerError("ledger run_id must be a non-empty string")
        history = document.get("history")
        if not isinstance(history, list):
            raise LedgerError("ledger history must be a list")
        for expected, event in enumerate(history, start=1):
            if not isinstance(event, dict) or event.get("sequence") != expected:
                raise LedgerError(
                    f"ledger history sequence must be contiguous at {expected}"
                )
        hashed = ["hash" in event for event in history]
        if any(hashed) and not all(hashed):
            raise LedgerError("ledger history cannot mix hashed and legacy events")
        if all(hashed) and history:
            previous_hash = "0" * 64
            previous_snapshot: dict[str, Any] | None = None
            compact_started = False
            for event_index, event in enumerate(history):
                recorded_hash = event.get("hash")
                if event.get("previous_hash") != previous_hash:
                    raise LedgerError("ledger history hash chain is discontinuous")
                if "snapshot_delta" in event:
                    compact_started = True
                elif compact_started:
                    raise LedgerError(
                        "full history event cannot appear after compact history"
                    )
                try:
                    snapshot = decode_history_event(event, previous_snapshot)
                except HistoryCodecError as error:
                    raise LedgerError(str(error)) from error
                virtual_event = virtual_history_event(event, snapshot)
                actual_hash = history_event_hash(event, snapshot)
                if actual_hash != recorded_hash:
                    raise LedgerError("ledger history event hash mismatch")
                AtomicLedger._validate_ticket_snapshot(snapshot)
                legacy_event = snapshot.get("schema") == 3
                if legacy_event and previous_snapshot is not None and previous_snapshot.get("schema") != 3:
                    raise LedgerError("legacy history appears after schema migration")
                AtomicLedger._validate_event_transition(
                    previous_snapshot,
                    virtual_event,
                    snapshot,
                    legacy=legacy_event,
                )
                if event.get("event") == "revalidation-budget-repaired":
                    details = event["details"]
                    invalidation_sequence = details["invalidation_sequence"]
                    if not 0 < invalidation_sequence < event["sequence"]:
                        raise LedgerError(
                            "revalidation-budget-repaired lineage is invalid"
                        )
                    invalidation = history[invalidation_sequence - 1]
                    if (
                        invalidation.get("event")
                        != details["invalidation_event"]
                        or invalidation.get("ticket_id")
                        != event.get("ticket_id")
                        or invalidation.get("details", {}).get(
                            "candidate_digest"
                        )
                        != details["candidate_digest"]
                        or invalidation.get("details", {}).get(
                            "artifact_generation"
                        )
                        != details["artifact_generation"]
                    ):
                        raise LedgerError(
                            "revalidation-budget-repaired lineage is invalid"
                        )
                    lineage = history[invalidation_sequence:event_index]
                    if any(
                        prior.get("ticket_id") == event.get("ticket_id")
                        and prior.get("event")
                        in {
                            "candidate-invalidated",
                            "delivery-revalidation-required",
                            "reconciliation-revalidation-required",
                        }
                        for prior in lineage
                    ):
                        raise LedgerError(
                            "revalidation-budget-repaired did not bind the latest "
                            "invalidation"
                        )
                    source_sequences = [
                        prior["sequence"]
                        for prior in lineage
                        if prior.get("ticket_id") == event.get("ticket_id")
                        and prior.get("event") == "leaf-result-recorded"
                    ]
                    if source_sequences != details["source_event_sequences"]:
                        raise LedgerError(
                            "revalidation-budget-repaired source lineage differs"
                        )
                previous_snapshot = snapshot
                previous_hash = recorded_hash
            persisted_snapshot = {
                key: value for key, value in document.items() if key != "history"
            }
            if previous_snapshot != persisted_snapshot:
                raise LedgerError(
                    "ledger snapshot cannot be reproduced from history"
                )
        AtomicLedger._validate_ticket_snapshot(document)

    @staticmethod
    def _validate_legacy_v3(document: dict[str, Any]) -> None:
        """Validate the persisted v3 envelope and hash chain before migration."""
        history = document.get("history")
        if not isinstance(document.get("run_id"), str) or not document["run_id"]:
            raise LedgerError("ledger run_id must be a non-empty string")
        if not isinstance(history, list) or not history:
            raise LedgerError("legacy ledger history must be a non-empty array")
        previous_hash = "0" * 64
        previous_snapshot: dict[str, Any] | None = None
        for sequence, event in enumerate(history, start=1):
            if (
                not isinstance(event, dict)
                or set(event)
                != {
                    "sequence",
                    "event",
                    "ticket_id",
                    "details",
                    "previous_hash",
                    "snapshot",
                    "hash",
                }
                or event.get("sequence") != sequence
                or event.get("event") not in LEGACY_V3_EVENTS
                or event.get("previous_hash") != previous_hash
                or not isinstance(event.get("details"), dict)
                or not isinstance(event.get("snapshot"), dict)
                or event["snapshot"].get("schema") != 3
                or "history" in event["snapshot"]
            ):
                raise LedgerError("legacy ledger history is malformed")
            unhashed = dict(event)
            recorded_hash = unhashed.pop("hash")
            actual_hash = hashlib.sha256(_canonical_bytes(unhashed)).hexdigest()
            if recorded_hash != actual_hash:
                raise LedgerError("ledger history event hash mismatch")
            snapshot = event["snapshot"]
            AtomicLedger._validate_ticket_snapshot(snapshot)
            AtomicLedger._validate_event_transition(
                previous_snapshot,
                event,
                snapshot,
                legacy=True,
            )
            previous_snapshot = snapshot
            previous_hash = recorded_hash
        if history[-1]["snapshot"] != {
            key: value for key, value in document.items() if key != "history"
        }:
            raise LedgerError("ledger snapshot cannot be reproduced from history")
        AtomicLedger._validate_ticket_snapshot(document)

    @staticmethod
    def _candidate_digest(candidate: Any) -> str:
        if (
            not isinstance(candidate, dict)
            or set(candidate)
            != {
                "base_tree_oid",
                "candidate_tree_oid",
                "ticket_digest",
                "contract_version",
            }
            or candidate.get("contract_version") != 2
            or any(
                not isinstance(candidate.get(key), str)
                or not candidate[key]
                for key in (
                    "base_tree_oid",
                    "candidate_tree_oid",
                    "ticket_digest",
                )
            )
        ):
            raise LedgerError("event CandidateRef is malformed")
        encoded = json.dumps(
            candidate, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    @staticmethod
    def _derived_run_state(snapshot: dict[str, Any]) -> str:
        tickets = snapshot["tickets"]
        states = [ticket["state"] for ticket in tickets.values()]
        if states and all(state == "integrated" for state in states):
            return "completed"

        def depends_on_failed(ticket_id: str, seen: set[str]) -> bool:
            if ticket_id in seen:
                return False
            seen = {*seen, ticket_id}
            for blocker_id in tickets[ticket_id]["blocked_by"]:
                blocker = tickets[blocker_id]
                if blocker["state"] == "failed" or depends_on_failed(
                    blocker_id, seen
                ):
                    return True
            return False

        if any(state == "failed" for state in states) and all(
            ticket["state"] in {"failed", "integrated"}
            or (
                ticket["state"] == "pending"
                and depends_on_failed(ticket_id, set())
            )
            for ticket_id, ticket in tickets.items()
        ):
            return "failed"
        if snapshot.get("pause") is not None:
            return "waiting"
        active = any(ticket["state"] == "active" for ticket in tickets.values())

        def autonomous_merge_ready(ticket: dict[str, Any]) -> bool:
            blockers = ticket["blocked_by"]
            if not blockers:
                return True
            if any(tickets[item]["state"] != "integrated" for item in blockers):
                return False
            if len(blockers) != 1:
                return True
            lineage = ticket.get("delivery_lineage")
            parent_lineage = tickets[blockers[0]].get("delivery_lineage")
            return (
                isinstance(lineage, dict)
                and isinstance(parent_lineage, dict)
                and lineage.get("base_branch")
                == parent_lineage.get("base_branch")
            )

        pending_runner_merge = any(
            ticket["state"] in {"pr-open", "gated"}
            and isinstance(ticket.get("merge_authorization"), dict)
            and ticket["merge_authorization"].get("mode")
            in {"runner", "autonomous"}
            and (
                ticket["merge_authorization"].get("mode") != "autonomous"
                or autonomous_merge_ready(ticket)
            )
            for ticket in tickets.values()
        )
        run_gate_open = any(
            gate.get("state") == "open" and gate.get("scope") == "run"
            for gate in snapshot["gates"].values()
        )

        def dependency_ready(ticket: dict[str, Any]) -> bool:
            if ticket.get("disposition", "open") != "open":
                return False
            blockers = ticket["blocked_by"]
            if not blockers:
                return True
            if any(
                tickets[item].get("disposition", "open")
                in {"on-hold", "canceled"}
                for item in blockers
            ):
                return False
            blocker_states = [tickets[item]["state"] for item in blockers]
            if len(blockers) == 1:
                blocker_id = blockers[0]
                blocker = tickets[blocker_id]
                provider_merge_gated = any(
                    gate.get("ticket_id") == blocker_id
                    and gate.get("category") == "provider-merge"
                    and gate.get("state") == "open"
                    for gate in snapshot["gates"].values()
                )
                return blocker_states[0] in {"pr-open", "integrated"} or (
                    blocker_states[0] == "gated"
                    and isinstance(blocker.get("pr"), dict)
                    and provider_merge_gated
                )
            return all(state == "integrated" for state in blocker_states)

        ready = (
            not run_gate_open
            and not pending_runner_merge
            and any(
                ticket["state"] == "pending" and dependency_ready(ticket)
                for ticket in tickets.values()
            )
        )
        return "running" if active or pending_runner_merge or ready else "waiting"

    @staticmethod
    def _validate_event_transition(
        previous: dict[str, Any] | None,
        event: dict[str, Any],
        current: dict[str, Any],
        *,
        legacy: bool = False,
    ) -> None:
        name = event.get("event")
        ticket_id = event.get("ticket_id")
        details = event.get("details", {})
        expected_event_fields = {
            "sequence",
            "event",
            "ticket_id",
            "details",
            "previous_hash",
            "snapshot",
            "hash",
        }
        if set(event) != expected_event_fields:
            raise LedgerError("ledger history event fields are invalid")
        if name not in (LEGACY_V3_EVENTS if legacy else KNOWN_LEDGER_EVENTS):
            raise LedgerError(f"unknown ledger history event: {name!r}")
        if not isinstance(details, dict):
            raise LedgerError("ledger history event details must be an object")

        def require(condition: bool, message: str) -> None:
            if not condition:
                raise LedgerError(message)

        def require_details(*fields: str) -> None:
            require(
                set(details) == set(fields),
                f"{name} event payload is invalid",
            )

        if name == "run-initialized":
            require(previous is None, "run-initialized must be the first event")
            require(ticket_id is None, "run-initialized cannot own a ticket")
            require_details()
            require(current.get("cleanup") is None, "run initialized with cleanup")
            require(current.get("gates") == {}, "run initialized with gates")
            require(current.get("effects") == {}, "run initialized with effects")
            require(current.get("pause") is None, "run initialized paused")
            legacy_snapshot = current.get("schema") == 3
            for ticket in current.get("tickets", {}).values():
                preexisting = bool(ticket.get("preexisting_integrated"))
                expected_state = "integrated" if preexisting else "pending"
                require(
                    ticket.get("state") == expected_state
                    and ticket.get("stage") is None
                    and ticket.get("candidate_ref") is None
                    and ticket.get("delivery_candidate_ref") is None
                    and ticket.get("artifact_generation") == 0
                    and ticket.get("validated_stages") == []
                    and ticket.get("delivery") == {}
                    and ticket.get("pr") is None
                    and ticket.get("merge_authorization") is None
                    and ticket.get("quality_failures") == 0
                    and isinstance(ticket.get("leaf_budget"), dict)
                    and ticket["leaf_budget"].get("interactions_consumed") == 0
                    and ticket["leaf_budget"].get("tool_calls_consumed") == 0
                    and ticket["leaf_budget"].get("wall_time_consumed") == 0
                    and ticket.get("leaf_progress_events") == []
                    and ticket.get("leaf_handoff") is None
                    and ticket.get("leaf_results") == {}
                    and ticket.get("failure_kind") is None
                    and (
                        legacy_snapshot
                        or (
                            ticket.get("disposition")
                            in {"open", "on-hold", "canceled", "completed"}
                            and "lifecycle" not in ticket
                            and ticket.get("attempt_outcome") is None
                            and ticket.get("stop_reason") is None
                            and ticket.get("disposition_receipt") is None
                        )
                    )
                    and "resume_pending" not in ticket,
                    "run-initialized ticket snapshot is impossible",
                )
            require(
                current.get("run_state")
                == AtomicLedger._derived_run_state(current),
                "run-initialized run state is impossible",
            )
            return
        if previous is None:
            raise LedgerError("history does not begin with run-initialized")

        if name == "ledger-v3-lifecycle-migrated":
            require(previous.get("schema") == 3, "migration source is not schema 3")
            require(current.get("schema") == LEDGER_VERSION, "migration target is invalid")
            require(ticket_id is None, "migration cannot own a ticket")
            require_details(
                "from_schema",
                "to_schema",
                "original_integrity",
                "original_history_head",
                "input_ledger_sha256",
                "actor",
                "evidence",
                "recovery_manifest_digest",
                "action_sequence",
            )
            migration = current.get("legacy_lifecycle_migration")
            require(
                details.get("from_schema") == 3
                and details.get("to_schema") == LEDGER_VERSION
                and migration
                == {
                    key: value for key, value in details.items() if key != "to_schema"
                }
                and all(
                    isinstance(details.get(key), str) and bool(details[key])
                    for key in ("actor", "evidence")
                )
                and all(
                    isinstance(details.get(key), str)
                    and len(details[key]) == 64
                    and details[key] == details[key].lower()
                    and all(character in "0123456789abcdef" for character in details[key])
                    for key in (
                        "original_integrity",
                        "original_history_head",
                        "input_ledger_sha256",
                        "recovery_manifest_digest",
                    )
                )
                and type(details.get("action_sequence")) is int
                and details["action_sequence"] > 0,
                "migration provenance is invalid",
            )
            expected = copy.deepcopy(previous)
            expected["schema"] = LEDGER_VERSION
            expected["pause"] = None
            expected["legacy_lifecycle_migration"] = migration
            for migrated_ticket_id, migrated_ticket in expected.get(
                "tickets", {}
            ).items():
                _migrate_legacy_ticket(
                    expected, migrated_ticket_id, migrated_ticket
                )
            require(current == expected, "migration changed non-lifecycle state")
            return

        require(
            set(previous) == set(current),
            f"{name} changed the ledger schema",
        )
        mutable_roots = {
            "run_state",
            "pause",
            "tickets",
            "gates",
            "effects",
            "cleanup",
        }
        if name == "autonomous-merge-granted":
            mutable_roots.update({"merge_policy", "autonomous_merge_grant"})
        for key in current:
            if key not in mutable_roots:
                require(
                    previous[key] == current[key],
                    f"{name} changed immutable run field {key}",
                )
        require(
            set(previous["tickets"]) == set(current["tickets"]),
            f"{name} changed the ticket set",
        )

        ticket_events = KNOWN_LEDGER_EVENTS - {
            "run-initialized",
            "run-paused",
            "run-unpaused",
            "autonomous-merge-granted",
            "run-aborted",
            "worktree-cleaned",
            "gate-opened",
            "gate-refreshed",
            "gate-passed",
        }
        if name in ticket_events:
            require(
                isinstance(ticket_id, str)
                and ticket_id in previous["tickets"]
                and ticket_id in current["tickets"],
                f"{name} has an invalid ticket owner",
            )
        elif name in {"gate-opened", "gate-refreshed", "gate-passed"}:
            require(
                ticket_id is None
                or (
                    isinstance(ticket_id, str)
                    and ticket_id in previous["tickets"]
                    and ticket_id in current["tickets"]
                ),
                f"{name} has an invalid gate owner",
            )
        else:
            require(ticket_id is None, f"{name} cannot own a ticket")

        previous_ticket = (
            previous["tickets"].get(ticket_id)
            if isinstance(ticket_id, str)
            else None
        )
        current_ticket = (
            current["tickets"].get(ticket_id)
            if isinstance(ticket_id, str)
            else None
        )

        def require_scope(
            *,
            ticket: bool = False,
            gates: bool = False,
            effects: bool = False,
            cleanup: bool = False,
            pause: bool = False,
        ) -> None:
            if ticket:
                for other_id in current["tickets"]:
                    if other_id != ticket_id:
                        require(
                            previous["tickets"][other_id]
                            == current["tickets"][other_id],
                            f"{name} changed unrelated ticket {other_id}",
                        )
            else:
                require(
                    previous["tickets"] == current["tickets"],
                    f"{name} changed ticket state",
                )
            if not gates:
                require(
                    previous["gates"] == current["gates"],
                    f"{name} changed gate state",
                )
            if not effects:
                require(
                    previous["effects"] == current["effects"],
                    f"{name} changed effect state",
                )
            if not cleanup:
                require(
                    previous["cleanup"] == current["cleanup"],
                    f"{name} changed cleanup state",
                )
            if not pause:
                require(
                    previous.get("pause") == current.get("pause"),
                    f"{name} changed run pause state",
                )

        def changed_ticket_fields() -> set[str]:
            return {
                key
                for key in set(previous_ticket) | set(current_ticket)
                if previous_ticket.get(key) != current_ticket.get(key)
                or (key in previous_ticket) != (key in current_ticket)
            }

        def require_ticket_changes(
            allowed: set[str],
            required: set[str] = frozenset(),
        ) -> None:
            changed = changed_ticket_fields()
            require(
                required <= changed <= allowed,
                f"{name} changed unauthorized ticket fields: {sorted(changed)}",
            )

        def reconciliation_delivery_changes() -> set[str]:
            before_delivery = previous_ticket["delivery"]
            after_delivery = current_ticket["delivery"]
            superseded = {
                step: before_delivery[step]
                for step in HEAD_BOUND_MERGE_DELIVERY_STEPS
                if step in before_delivery
            }
            archive_required = bool(
                superseded or previous_ticket.get("merge_authorization") is not None
            )
            expected = {"reconcile-prepare", *superseded}
            preparation_refresh = before_delivery.get(
                PREPARATION_REFRESH_STEP
            )
            if preparation_refresh is not None:
                prior_intent = before_delivery.get("reconcile-intent")
                try:
                    replacement_intent = validate_preparation_refresh(
                        preparation_refresh, prior_intent
                    )
                except (ReconciliationIntentError, TypeError):
                    replacement_intent = None
                before_refresh_history = before_delivery.get(
                    PREPARATION_REFRESH_HISTORY_STEP, []
                )
                after_refresh_history = after_delivery.get(
                    PREPARATION_REFRESH_HISTORY_STEP
                )
                require(
                    isinstance(replacement_intent, dict)
                    and isinstance(before_refresh_history, list)
                    and isinstance(after_refresh_history, list)
                    and len(after_refresh_history)
                    == len(before_refresh_history) + 1
                    and after_refresh_history[:-1] == before_refresh_history
                    and after_refresh_history[-1]
                    == {
                        "schema": 1,
                        "refresh": preparation_refresh,
                        "result": "consumed",
                    }
                    and after_delivery.get("reconcile-intent")
                    == replacement_intent
                    and PREPARATION_REFRESH_STEP not in after_delivery,
                    "pre-prepare reconciliation target refresh history is invalid",
                )
                expected.update(
                    {
                        "reconcile-intent",
                        PREPARATION_REFRESH_STEP,
                        PREPARATION_REFRESH_HISTORY_STEP,
                    }
                )
            if not archive_required:
                return expected
            expected.add("merge-lineage-history")
            before_history = before_delivery.get("merge-lineage-history", [])
            after_history = after_delivery.get("merge-lineage-history")
            require(
                isinstance(before_history, list)
                and isinstance(after_history, list)
                and after_history[:-1] == before_history,
                f"{name} merge lineage history is not append-only",
            )
            archived = after_history[-1] if after_history else None
            require(
                isinstance(archived, dict)
                and archived.get("schema") == 1
                and archived.get("old_head") == details.get("old_head")
                and archived.get("new_head") == details.get("new_head")
                and archived.get("receipts") == superseded
                and archived.get("merge_authorization")
                == previous_ticket.get("merge_authorization"),
                f"{name} merge lineage archive is invalid",
            )
            return expected

        if name == "ticket-activated":
            require_scope(ticket=True)
            require_details("candidate_digest")
            hitl_start_approved = (
                previous_ticket.get("execution_mode") == "AFK"
                or any(
                    gate.get("ticket_id") == ticket_id
                    and gate.get("kind") == "start"
                    and gate.get("state") == "passed"
                    for gate in previous["gates"].values()
                )
            )
            require(
                previous_ticket["state"] == "pending"
                and "resume_pending" not in previous_ticket
                and current_ticket["state"] == "active"
                and current_ticket["stage"] == PIPELINE_STAGES[0]
                and hitl_start_approved,
                "ticket-activated lifecycle is impossible",
            )
            require_ticket_changes(
                {"state", "stage", "candidate_ref"}
                | (set() if legacy else {"attempt_outcome", "stop_reason"}),
                {"state", "stage", "candidate_ref"},
            )
            require(
                details["candidate_digest"]
                == AtomicLedger._candidate_digest(
                    current_ticket["candidate_ref"]
                ),
                "ticket-activated CandidateRef payload is invalid",
            )
        elif name == "ticket-resumed":
            require_scope(ticket=True)
            require_details("candidate_digest")
            require(
                previous_ticket["state"] == "pending"
                and previous_ticket.get("resume_pending") is True
                and current_ticket["state"] == "active"
                and "resume_pending" not in current_ticket
                and current_ticket["stage"] == previous_ticket["stage"]
                and current_ticket["candidate_ref"]
                == previous_ticket["candidate_ref"],
                "ticket-resumed lifecycle is impossible",
            )
            require_ticket_changes(
                {"state", "resume_pending"}
                | (set() if legacy else {"attempt_outcome", "stop_reason"}),
                {"state", "resume_pending"},
            )
            require(
                details["candidate_digest"]
                == AtomicLedger._candidate_digest(
                    current_ticket["candidate_ref"]
                ),
                "ticket-resumed CandidateRef payload is invalid",
            )
        elif name in {"candidate-adopted", "candidate-invalidated"}:
            require_scope(ticket=True)
            require_details("candidate_digest", "artifact_generation")
            allowed = {
                "candidate_ref",
                "validated_stages",
                "artifact_generation",
                "merge_authorization",
                "leaf_progress_events",
                "leaf_handoff",
                "leaf_results",
                "leaf_budget",
                "docs_only",
            }
            if name == "candidate-invalidated":
                allowed.add("stage")
            require_ticket_changes(
                allowed,
                {"candidate_ref", "artifact_generation"},
            )
            require(
                previous_ticket["state"] == "active"
                and current_ticket["state"] == "active"
                and current_ticket["artifact_generation"]
                == previous_ticket["artifact_generation"] + 1
                and current_ticket["validated_stages"] == []
                and current_ticket["merge_authorization"] is None
                and (
                    name != "candidate-adopted"
                    or (
                        previous_ticket["stage"] == "implement"
                        and current_ticket["stage"] == "implement"
                    )
                )
                and (
                    name != "candidate-invalidated"
                    or current_ticket["stage"] == "implement"
                ),
                f"{name} lifecycle is impossible",
            )
            digest = AtomicLedger._candidate_digest(
                current_ticket["candidate_ref"]
            )
            require(
                details
                == {
                    "candidate_digest": digest,
                    "artifact_generation": current_ticket[
                        "artifact_generation"
                    ],
                },
                f"{name} CandidateRef payload is invalid",
            )
        elif name == "docs-only-candidate-adopted":
            require_scope(ticket=True)
            require_details(
                "candidate_digest",
                "evidence_sha256",
                "leaf_interactions_avoided",
            )
            require_ticket_changes(
                {
                    "candidate_ref",
                    "validated_stages",
                    "artifact_generation",
                    "merge_authorization",
                    "leaf_handoff",
                    "leaf_results",
                    "docs_only",
                    "state",
                    "stage",
                },
                {
                    "validated_stages",
                    "artifact_generation",
                    "leaf_results",
                    "docs_only",
                    "state",
                    "stage",
                },
            )
            receipt = current_ticket.get("docs_only")
            require(
                previous_ticket["state"] == "active"
                and previous_ticket["stage"] == "implement"
                and current_ticket["state"] == "verified"
                and current_ticket["stage"] is None
                and current_ticket["validated_stages"] == ["implement"]
                and current_ticket["artifact_generation"]
                == previous_ticket["artifact_generation"] + 1
                and current_ticket["merge_authorization"] is None
                and current_ticket["leaf_budget"]
                == previous_ticket["leaf_budget"]
                and current_ticket["leaf_progress_events"]
                == previous_ticket["leaf_progress_events"]
                and current_ticket["leaf_handoff"] is None
                and set(current_ticket["leaf_results"]) == {"verify"}
                and isinstance(receipt, dict)
                and current_ticket["leaf_results"]["verify"].get("scope")
                == {
                    "files_expected": receipt.get("changed_paths", []),
                    "files_inspected": receipt.get("changed_paths", []),
                    "files_remaining": [],
                }
                and receipt.get("status") == "eligible",
                "docs-only adoption lifecycle is impossible",
            )
            try:
                normalized_receipt = normalize_docs_only_receipt(
                    receipt,
                    ticket=current_ticket,
                    candidate=current_ticket["candidate_ref"],
                )
            except (DocsOnlyError, ValueError, TypeError, KeyError):
                normalized_receipt = None
            require(
                normalized_receipt == receipt,
                "docs-only adoption receipt is invalid",
            )
            require(
                details
                == {
                    "candidate_digest": AtomicLedger._candidate_digest(
                        current_ticket["candidate_ref"]
                    ),
                    "evidence_sha256": receipt.get("evidence", {}).get(
                        "sha256"
                    ),
                    "leaf_interactions_avoided": receipt.get(
                        "leaf_interactions_avoided"
                    ),
                },
                "docs-only adoption payload is invalid",
            )
        elif name == "docs-only-candidate-rejected":
            require_scope(ticket=True)
            require_details("reason")
            require_ticket_changes({"docs_only"}, {"docs_only"})
            receipt = current_ticket.get("docs_only")
            require(
                previous_ticket["state"] == "active"
                and previous_ticket["stage"] == "implement"
                and current_ticket["state"] == "active"
                and current_ticket["stage"] == "implement"
                and receipt
                == {
                    "contract_version": 1,
                    "status": "rejected",
                    "reason": details["reason"],
                    "leaf_interactions_avoided": 0,
                },
                "docs-only rejection lifecycle is impossible",
            )
        elif name == "revalidation-budget-repaired":
            require_scope(ticket=True)
            require_details(
                "after_budget",
                "artifact_generation",
                "before_budget",
                "candidate_digest",
                "invalidation_event",
                "invalidation_sequence",
                "source_event_sequences",
            )
            require_ticket_changes({"leaf_budget"}, {"leaf_budget"})
            before_budget = previous_ticket.get("leaf_budget")
            after_budget = current_ticket.get("leaf_budget")
            require(
                previous_ticket["state"] == "active"
                and current_ticket["state"] == "active"
                and current_ticket["stage"]
                in {"review", "qa-plan", "qa-execute", "verify"}
                and current_ticket["candidate_ref"]
                == previous_ticket["candidate_ref"]
                and current_ticket["artifact_generation"]
                == previous_ticket["artifact_generation"]
                == details["artifact_generation"]
                and details["candidate_digest"]
                == AtomicLedger._candidate_digest(
                    current_ticket["candidate_ref"]
                )
                and details["invalidation_event"]
                in {
                    "candidate-invalidated",
                    "delivery-revalidation-required",
                    "reconciliation-revalidation-required",
                }
                and isinstance(details["invalidation_sequence"], int)
                and not isinstance(details["invalidation_sequence"], bool)
                and details["invalidation_sequence"] > 0,
                "revalidation-budget-repaired lifecycle is impossible",
            )
            sequences = details["source_event_sequences"]
            require(
                isinstance(sequences, list)
                and len(sequences)
                == len(current_ticket["leaf_progress_events"])
                and all(
                    isinstance(sequence, int)
                    and not isinstance(sequence, bool)
                    and sequence > details["invalidation_sequence"]
                    for sequence in sequences
                )
                and sequences == sorted(set(sequences)),
                "revalidation-budget-repaired source events are invalid",
            )
            try:
                normalized_before = validate_leaf_budget(
                    current, before_budget
                )
                normalized_after = validate_leaf_budget(current, after_budget)
                rebuilt = rebuild_leaf_budget_epoch(
                    current,
                    current_ticket["leaf_progress_events"],
                    expected_candidate_ref=current_ticket["candidate_ref"],
                )
            except LeafProtocolError as error:
                raise LedgerError(
                    f"revalidation-budget-repaired replay is invalid: {error}"
                ) from error
            require(
                details["before_budget"] == normalized_before
                and details["after_budget"] == normalized_after
                and normalized_after == rebuilt
                and normalized_before != normalized_after,
                "revalidation-budget-repaired deterministic replay differs",
            )
            for field in (
                "interactions_consumed",
                "tool_calls_consumed",
                "wall_time_consumed",
            ):
                require(
                    normalized_before[field] >= normalized_after[field],
                    "revalidation-budget-repaired increased consumed resources",
                )
            for stage, reservation in normalized_after["reservations"].items():
                previous_reservation = normalized_before["reservations"][stage]
                require(
                    previous_reservation["consumed"]
                    >= reservation["consumed"]
                    and previous_reservation["complete"]
                    == reservation["complete"],
                    "revalidation-budget-repaired rewrote mandatory progress",
                )
        elif name == "leaf-result-recorded":
            require_scope(ticket=True)
            require_details(
                "candidate_digest",
                "complete",
                "interaction",
                "progress_phase",
                "stage",
                "stop_reason",
                "tool_calls",
                "wall_time",
                "input_drift",
            )
            before_budget = previous_ticket.get("leaf_budget")
            after_budget = current_ticket.get("leaf_budget")
            before_progress = previous_ticket.get("leaf_progress_events")
            after_progress = current_ticket.get("leaf_progress_events")
            handoff = current_ticket.get("leaf_handoff")
            require(
                details["stage"] in {"review", "qa-plan", "qa-execute", "verify"}
                and previous_ticket["state"] == "active"
                and current_ticket["state"] == "active"
                and previous_ticket["stage"] == details["stage"]
                and current_ticket["stage"] == details["stage"]
                and current_ticket["candidate_ref"]
                == previous_ticket["candidate_ref"]
                and isinstance(before_budget, dict)
                and isinstance(after_budget, dict)
                and isinstance(before_progress, list)
                and isinstance(after_progress, list)
                and isinstance(handoff, dict),
                "leaf-result-recorded lifecycle is impossible",
            )
            require_ticket_changes(
                {"leaf_budget", "leaf_progress_events", "leaf_handoff"},
                {"leaf_budget", "leaf_progress_events", "leaf_handoff"},
            )
            require(
                isinstance(details["complete"], bool)
                and isinstance(details["interaction"], int)
                and not isinstance(details["interaction"], bool)
                and isinstance(details["tool_calls"], int)
                and not isinstance(details["tool_calls"], bool)
                and details["tool_calls"] >= 0
                and isinstance(details["wall_time"], int)
                and not isinstance(details["wall_time"], bool)
                and details["wall_time"] >= 0
                and isinstance(details["input_drift"], bool),
                "leaf-result-recorded resource payload is invalid",
            )
            require(
                after_budget["interactions_consumed"]
                == before_budget["interactions_consumed"] + 1
                == details["interaction"]
                and after_budget["tool_calls_consumed"]
                == before_budget["tool_calls_consumed"]
                + details["tool_calls"]
                and after_budget["wall_time_consumed"]
                == before_budget["wall_time_consumed"]
                + details["wall_time"],
                "leaf-result-recorded budget transition is invalid",
            )
            if details["input_drift"]:
                retained_progress = [
                    progress
                    for progress in before_progress
                    if progress.get("stage") != "verify"
                ]
                require(
                    details["stage"] == "verify"
                    and len(after_progress) == len(retained_progress) + 1
                    and after_progress[:-1] == retained_progress,
                    "leaf-result-recorded input drift reset is invalid",
                )
            else:
                require(
                    len(after_progress) == len(before_progress) + 1
                    and after_progress[:-1] == before_progress,
                    "leaf-result-recorded progress append is invalid",
                )
            latest = after_progress[-1]
            require(
                latest.get("candidate_ref") == current_ticket["candidate_ref"]
                and latest.get("stage") == details["stage"]
                and latest.get("phase") == details["progress_phase"]
                and latest.get("complete") == details["complete"]
                and latest.get("stop_reason") == details["stop_reason"]
                and latest.get("resource_delta")
                == {
                    "interactions": 1,
                    "tool_calls": details["tool_calls"],
                    "wall_time": details["wall_time"],
                }
                and handoff.get("candidate_ref")
                == current_ticket["candidate_ref"]
                and handoff.get("stage") == details["stage"]
                and handoff.get("progress_phase")
                == details["progress_phase"]
                and handoff.get("complete") == details["complete"]
                and handoff.get("stop_reason") == details["stop_reason"],
                "leaf-result-recorded handoff payload is invalid",
            )
            require(
                details["candidate_digest"]
                == AtomicLedger._candidate_digest(
                    current_ticket["candidate_ref"]
                ),
                "leaf-result-recorded CandidateRef payload is invalid",
            )
            try:
                previous_handoff = previous_ticket.get("leaf_handoff")
                if previous_handoff is not None:
                    if details["input_drift"]:
                        previous_identity = verification_checkpoint_identity(
                            previous_handoff
                        )
                        current_identity = verification_checkpoint_identity(handoff)
                        if (
                            previous_identity == current_identity
                            or (
                                previous_identity is None
                                and current_identity is None
                            )
                        ):
                            raise LeafProtocolError(
                                "verification input drift lacks a new identity"
                            )
                    else:
                        progression = validate_handoff_progression(
                            previous_handoff,
                            handoff,
                        )
                        if progression != "advance":
                            raise LeafProtocolError(
                                "persisted leaf progress must advance"
                            )
                replay_source_budget = copy.deepcopy(before_budget)
                if details["input_drift"]:
                    replay_source_budget["reservations"]["verify"][
                        "complete"
                    ] = False
                replay_budget, replay_handoff, replay_progress = (
                    reduce_leaf_result(
                        current,
                        replay_source_budget,
                        handoff,
                        expected_candidate_ref=current_ticket["candidate_ref"],
                        expected_stage=details["stage"],
                        tool_calls=details["tool_calls"],
                        wall_time=details["wall_time"],
                    )
                )
            except LeafProtocolError as error:
                raise LedgerError(
                    f"leaf-result-recorded replay is invalid: {error}"
                ) from error
            require(
                replay_budget == after_budget
                and replay_handoff
                == (
                    _legacy_leaf_execution_projection(handoff)
                    if legacy
                    else handoff
                )
                and replay_progress
                == (
                    _legacy_leaf_execution_projection(latest)
                    if legacy
                    else latest
                ),
                "leaf-result-recorded deterministic replay differs",
            )
        elif name == "stage-passed":
            require_scope(ticket=True)
            require_details("stage")
            stage = details.get("stage")
            require(stage in PIPELINE_STAGES, "stage-passed stage is invalid")
            index = PIPELINE_STAGES.index(stage)
            expected_validated = list(PIPELINE_STAGES[: index + 1])
            if stage == PIPELINE_STAGES[-1]:
                expected_state = "verified"
                expected_stage = None
                required_changes = {"state", "stage", "validated_stages"}
            else:
                expected_state = "active"
                expected_stage = PIPELINE_STAGES[index + 1]
                required_changes = {"stage", "validated_stages"}
            leaf_stages = {"review", "qa-plan", "qa-execute", "verify"}
            allowed_changes = {"state", "stage", "validated_stages"}
            if stage in leaf_stages:
                required_changes |= {"leaf_handoff", "leaf_results"}
                allowed_changes |= {"leaf_handoff", "leaf_results"}
                prior_results = previous_ticket.get("leaf_results")
                current_results = current_ticket.get("leaf_results")
                require(
                    isinstance(previous_ticket.get("leaf_handoff"), dict)
                    and current_ticket.get("leaf_handoff") is None
                    and isinstance(prior_results, dict)
                    and isinstance(current_results, dict)
                    and current_results
                    == {
                        **prior_results,
                        stage: previous_ticket["leaf_handoff"],
                    },
                    "stage-passed leaf handoff archival is invalid",
                )
            require(
                previous_ticket["state"] == "active"
                and previous_ticket["stage"] == stage
                and current_ticket["state"] == expected_state
                and current_ticket["stage"] == expected_stage
                and current_ticket["validated_stages"] == expected_validated
                and current_ticket["candidate_ref"]
                == previous_ticket["candidate_ref"],
                "stage-passed lifecycle is impossible",
            )
            require_ticket_changes(
                allowed_changes,
                required_changes,
            )
        elif name == "quality-failed":
            require_scope(ticket=True)
            require_details("stage", "failures")
            stage = details["stage"]
            failures = details["failures"]
            require(
                stage in {"review", "qa-execute", "verify"}
                and previous_ticket["state"] == "active"
                and previous_ticket["stage"] == stage
                and isinstance(failures, int)
                and failures == previous_ticket["quality_failures"] + 1
                and current_ticket["quality_failures"] == failures
                and current_ticket["validated_stages"] == [],
                "quality-failed lifecycle is impossible",
            )
            if stage in {"review", "qa-execute", "verify"}:
                require(
                    current_ticket.get("leaf_progress_events") == []
                    and current_ticket.get("leaf_handoff") is None
                    and current_ticket.get("leaf_results") == {},
                    "quality-failed leaf retained semantic evidence",
                )
            if failures >= current["max_quality_failures"]:
                require(
                    current_ticket["state"] == "failed"
                    and current_ticket["stage"] is None
                    and current_ticket["failure_kind"] == "quality",
                    "quality-failed terminal transition is impossible",
                )
                required_changes = {
                    "state",
                    "stage",
                    "quality_failures",
                    "validated_stages",
                    "failure_kind",
                }
            else:
                require(
                    current_ticket["state"] == "active"
                    and current_ticket["stage"] == "implement"
                    and current_ticket["failure_kind"]
                    == previous_ticket["failure_kind"],
                    "quality-failed retry transition is impossible",
                )
                required_changes = {
                    "stage",
                    "quality_failures",
                    "validated_stages",
                }
            require_ticket_changes(
                {
                    "state",
                    "stage",
                    "quality_failures",
                    "validated_stages",
                    "failure_kind",
                    "leaf_progress_events",
                    "leaf_handoff",
                    "leaf_results",
                    "leaf_budget",
                    "docs_only",
                },
                required_changes,
            )
        elif name == "ticket-failed":
            require_scope(ticket=True)
            require_details("stage", "failure_kind")
            stage = details["stage"]
            failure_kind = details["failure_kind"]
            require(
                stage in PIPELINE_STAGES
                and stage not in {"review", "qa-execute", "verify"}
                and previous_ticket["state"] == "active"
                and previous_ticket["stage"] == stage
                and current_ticket["state"] == "failed"
                and current_ticket["stage"] is None
                and current_ticket["validated_stages"] == []
                and current_ticket["failure_kind"] == failure_kind
                and failure_kind
                == ("finalization" if stage == "finalize" else "implementation"),
                "ticket-failed lifecycle is impossible",
            )
            require_ticket_changes(
                {"state", "stage", "validated_stages", "failure_kind"},
                {"state", "stage", "failure_kind"},
            )
        elif name == "gate-opened":
            require_scope(ticket=ticket_id is not None, gates=True)
            require_details("gate_id", "scope")
            gate_id = details.get("gate_id")
            gate = current.get("gates", {}).get(gate_id)
            new_gate_ids = set(current["gates"]) - set(previous["gates"])
            require(
                new_gate_ids == {gate_id}
                and all(
                    previous["gates"][key] == current["gates"][key]
                    for key in previous["gates"]
                )
                and isinstance(gate, dict)
                and gate.get("state") == "open"
                and gate.get("ticket_id") == ticket_id
                and gate.get("scope") == details["scope"]
                and details["scope"] in {"ticket", "run"}
                and isinstance(gate.get("category"), str)
                and bool(gate["category"])
                and isinstance(gate.get("reason"), str)
                and bool(gate["reason"])
                and isinstance(gate.get("kind"), str)
                and bool(gate["kind"])
                and gate.get("actor") is None
                and gate.get("evidence") is None,
                "gate-opened transition is impossible",
            )
            owner = ticket_id or "run"
            require(
                gate_id
                == f"gate:{owner}:{gate['kind']}:{len(current['gates'])}",
                "gate-opened ID is invalid",
            )
            if gate["kind"] == "start":
                require(
                    ticket_id is not None
                    and previous_ticket.get("execution_mode") == "HITL"
                    and previous_ticket.get("state") == "pending"
                    and previous_ticket.get("stage") is None
                    and gate.get("category") == "human"
                    and gate.get("scope") == "ticket"
                    and gate.get("reason") == "HITL start approval required"
                    and not any(
                        item.get("ticket_id") == ticket_id
                        and item.get("kind") == "start"
                        for item in previous["gates"].values()
                    ),
                    "HITL start gate is invalid",
                )
            if ticket_id is None:
                require(
                    set(gate)
                    == {
                        "gate_id",
                        "ticket_id",
                        "category",
                        "scope",
                        "reason",
                        "kind",
                        "state",
                        "actor",
                        "evidence",
                    },
                    "run gate fields are invalid",
                )
            else:
                expected_fields = {
                    "gate_id",
                    "ticket_id",
                    "category",
                    "scope",
                    "reason",
                    "kind",
                    "state",
                    "actor",
                    "evidence",
                    "resume_state",
                    "resume_stage",
                }
                if gate.get("kind") == "reopen":
                    expected_fields.add("lifecycle_request")
                if gate.get("details") is not None:
                    expected_fields.add("details")
                request = gate.get("lifecycle_request")
                require(
                    set(gate) == expected_fields
                    and gate["resume_state"] == previous_ticket["state"]
                    and gate["resume_stage"] == previous_ticket["stage"]
                    and current_ticket["state"] == "gated"
                    and current_ticket["stage"] == previous_ticket["stage"]
                    and (
                        gate.get("kind") != "reopen"
                        or (
                            gate.get("category") == "human"
                            and isinstance(request, dict)
                            and request.get("ticket_id") == ticket_id
                            and request.get("target_disposition") == "open"
                            and isinstance(request.get("reason"), str)
                            and bool(request["reason"])
                            and isinstance(request.get("requested_by"), str)
                            and bool(request["requested_by"])
                        )
                    ),
                    "ticket gate resume state is invalid",
                )
                require_ticket_changes({"state"})
        elif name == "gate-refreshed":
            require_scope(gates=True)
            require_details("gate_id", "reason")
            gate_id = details["gate_id"]
            before_gate = previous["gates"].get(gate_id)
            after_gate = current["gates"].get(gate_id)
            require(
                set(previous["gates"]) == set(current["gates"])
                and isinstance(before_gate, dict)
                and isinstance(after_gate, dict)
                and before_gate.get("state") == "open"
                and after_gate.get("state") == "open"
                and after_gate.get("ticket_id") == ticket_id
                and isinstance(details["reason"], str)
                and bool(details["reason"])
                and after_gate.get("reason") == details["reason"]
                and before_gate.get("reason") != after_gate.get("reason")
                and {
                    key
                    for key in set(before_gate) | set(after_gate)
                    if before_gate.get(key) != after_gate.get(key)
                }
                == {"reason"}
                and all(
                    previous["gates"][key] == current["gates"][key]
                    for key in previous["gates"]
                    if key != gate_id
                ),
                "gate-refreshed transition is impossible",
            )
        elif name == "gate-passed":
            require_scope(ticket=ticket_id is not None, gates=True)
            require_details("gate_id", "actor")
            gate_id = details.get("gate_id")
            before_gate = previous["gates"].get(gate_id)
            after_gate = current["gates"].get(gate_id)
            require(
                set(previous["gates"]) == set(current["gates"])
                and isinstance(before_gate, dict)
                and isinstance(after_gate, dict)
                and before_gate.get("state") == "open"
                and after_gate.get("state") == "passed"
                and after_gate.get("actor") == details["actor"]
                and isinstance(after_gate.get("evidence"), str)
                and bool(after_gate["evidence"])
                and after_gate.get("ticket_id") == ticket_id
                and {
                    key
                    for key in set(before_gate) | set(after_gate)
                    if before_gate.get(key) != after_gate.get(key)
                }
                == {"state", "actor", "evidence"}
                and all(
                    previous["gates"][key] == current["gates"][key]
                    for key in previous["gates"]
                    if key != gate_id
                ),
                "gate-passed transition is impossible",
            )
            if ticket_id is not None:
                other_open = any(
                    key != gate_id
                    and gate.get("ticket_id") == ticket_id
                    and gate.get("state") == "open"
                    for key, gate in current["gates"].items()
                )
                if other_open:
                    require(
                        previous_ticket == current_ticket,
                        "gate-passed resumed a multiply-gated ticket",
                    )
                else:
                    active_other = any(
                        key != ticket_id and ticket["state"] == "active"
                        for key, ticket in previous["tickets"].items()
                    )
                    expected_state = before_gate["resume_state"]
                    if expected_state == "active" and active_other:
                        require(
                            current_ticket["state"] == "pending"
                            and current_ticket.get("resume_pending") is True,
                            "gate-passed did not defer active resume",
                        )
                    else:
                        require(
                            current_ticket["state"] == expected_state
                            and current_ticket.get("resume_pending")
                            == previous_ticket.get("resume_pending"),
                            "gate-passed restored the wrong ticket state",
                        )
                    require(
                        current_ticket["stage"] == before_gate["resume_stage"],
                        "gate-passed restored the wrong ticket stage",
                    )
                    require_ticket_changes(
                        {"state", "stage", "resume_pending"}
                    )
        elif name == "effect-applied":
            require_scope(ticket=True, effects=True)
            require_details("effect", "idempotency_key")
            effect = details.get("effect")
            new_effects = set(current.get("effects", {})) - set(
                previous.get("effects", {})
            )
            key = details["idempotency_key"]
            expected_key_source = json.dumps(
                [
                    current["run_id"],
                    ticket_id,
                    effect,
                    current_ticket["candidate_ref"],
                ],
                sort_keys=True,
                separators=(",", ":"),
            )
            expected_key = hashlib.sha256(
                expected_key_source.encode("utf-8")
            ).hexdigest()
            require(
                new_effects == {key}
                and key == expected_key
                and all(
                    previous["effects"][item] == current["effects"][item]
                    for item in previous["effects"]
                )
                and current["effects"][key]
                == {
                    "ticket_id": ticket_id,
                    "effect": effect,
                    "state": "applied",
                }
                and current_ticket["state"]
                in {"verified", "pr-open", "integrated"},
                "effect-applied transition is impossible",
            )
            completion_effect = effect in {
                "move-done-and-stage",
                "move-done-and-summarize-external",
            }
            require_ticket_changes(
                set()
                if legacy
                else {
                    "disposition",
                    "attempt_outcome",
                    "stop_reason",
                    "current_source_relative_path",
                    "disposition_receipt",
                },
                (
                    {"disposition", "current_source_relative_path"}
                    if completion_effect and not legacy
                    else set()
                ),
            )
            require(
                legacy
                or not completion_effect
                or (
                    current_ticket["disposition"] == "completed"
                    and current_ticket["attempt_outcome"] is None
                    and current_ticket["stop_reason"] is None
                ),
                "completion effect did not update lifecycle axes",
            )
        elif name == "evidence-cache-decision":
            require_scope(ticket=True)
            require_details(
                "key_hash",
                "hit",
                "commands_avoided",
                "limitations",
                "miss_reason",
            )
            require(
                isinstance(details["key_hash"], str)
                and len(details["key_hash"]) == 64
                and all(
                    character in "0123456789abcdef"
                    for character in details["key_hash"]
                )
                and isinstance(details["hit"], bool)
                and isinstance(details["commands_avoided"], int)
                and not isinstance(details["commands_avoided"], bool)
                and details["commands_avoided"] >= 0
                and isinstance(details["limitations"], list)
                and bool(details["limitations"])
                and all(
                    isinstance(item, str) and bool(item)
                    for item in details["limitations"]
                )
                and (
                    details["miss_reason"] is None
                    if details["hit"]
                    else isinstance(details["miss_reason"], str)
                    and bool(details["miss_reason"])
                ),
                "evidence-cache-decision payload is invalid",
            )
            require_ticket_changes(set())
        elif name == "delivery-recorded":
            require_scope(ticket=True)
            require_details("step")
            step = details["step"]
            gated_delivery = (
                previous_ticket["state"] == "gated"
                and current_ticket["state"] == "gated"
                and any(
                    gate.get("ticket_id") == ticket_id
                    and gate.get("state") == "open"
                    and (
                        (
                            gate.get("category")
                            in {
                                "provider-environment",
                                "provider-pr",
                                "delivery-pr-body",
                                "provider-merge",
                            }
                            and gate.get("resume_state")
                            in {"verified", "pr-open"}
                        )
                        or (
                            isinstance(step, str)
                            and step.startswith("repository-reconciliation-")
                            and gate.get("category")
                            in {
                                "stack-reconciliation",
                                "stack-reconciliation-recovery",
                            }
                        )
                    )
                    for gate in previous["gates"].values()
                )
            )
            require(
                isinstance(step, str)
                and bool(step)
                and (
                    previous_ticket["state"]
                    in {"verified", "pr-open", "integrated"}
                    or gated_delivery
                )
                and current_ticket["state"] == previous_ticket["state"],
                "delivery-recorded lifecycle is impossible",
            )
            before_delivery = previous_ticket["delivery"]
            after_delivery = current_ticket["delivery"]
            require(
                {
                    key
                    for key in set(before_delivery) | set(after_delivery)
                    if before_delivery.get(key) != after_delivery.get(key)
                    or (key in before_delivery) != (key in after_delivery)
                }
                == {step},
                "delivery-recorded changed an unrelated delivery step",
            )
            if step == PREPARATION_REFRESH_STEP:
                prior_intent = before_delivery.get("reconcile-intent")
                current_refresh = after_delivery.get(step)
                previous_refresh = before_delivery.get(step)
                try:
                    validate_preparation_refresh(
                        current_refresh, prior_intent
                    )
                    if previous_refresh is not None:
                        previous_replacement = validate_preparation_refresh(
                            previous_refresh, prior_intent
                        )
                        require(
                            current_refresh["history"]
                            == [
                                *previous_refresh["history"],
                                {
                                    "schema": 1,
                                    "previous_intent": previous_refresh[
                                        "previous_intent"
                                    ],
                                    "replacement_intent": previous_replacement,
                                },
                            ]
                            and current_refresh["previous_intent"]
                            == previous_replacement,
                            "pre-prepare refresh replacement is not append-only",
                        )
                except (ReconciliationIntentError, TypeError) as error:
                    raise LedgerError(
                        "delivery-recorded pre-prepare refresh is invalid"
                    ) from error
            if step == "pr-body":
                previous_body = before_delivery.get(step)
                current_body = after_delivery.get(step)
                require(
                    isinstance(current_body, dict),
                    "delivery-recorded PR-body receipt is invalid",
                )
                if current_body.get("schema") == 2:
                    require(
                        _pr_body_rebind_is_closed(
                            previous_body,
                            current_body,
                            before_delivery.get("reconcile-pr-body-request"),
                            current_ticket,
                            legacy=legacy,
                        ),
                        "delivery-recorded PR-body rebind is not append-only",
                    )
                else:
                    require(
                        not isinstance(previous_body, dict)
                        or previous_body.get("schema") != 2,
                        "delivery-recorded PR-body lineage cannot be downgraded",
                    )
            require_ticket_changes({"delivery"}, {"delivery"})
        elif name == "delivery-candidate-recorded":
            require_scope(ticket=True)
            require_details("candidate_digest")
            require(
                previous_ticket["state"] == "verified"
                and current_ticket["state"] == "verified"
                and current_ticket["delivery_candidate_ref"]
                != previous_ticket["delivery_candidate_ref"]
                and current_ticket["merge_authorization"] is None,
                "delivery-candidate-recorded lifecycle is impossible",
            )
            require_ticket_changes(
                {"delivery_candidate_ref", "merge_authorization"},
                {"delivery_candidate_ref"},
            )
            require(
                details["candidate_digest"]
                == AtomicLedger._candidate_digest(
                    current_ticket["delivery_candidate_ref"]
                ),
                "delivery-candidate-recorded payload is invalid",
            )
        elif name == "reconciliation-candidate-sealed":
            require_scope(ticket=True)
            require_details(
                "old_local_head",
                "new_local_head",
                "candidate_digest",
                "artifact_generation",
            )
            before_delivery = previous_ticket["delivery"]
            after_delivery = current_ticket["delivery"]
            old_prepare = before_delivery.get("reconcile-prepare")
            new_prepare = after_delivery.get("reconcile-prepare")
            before_history = before_delivery.get(
                "reconcile-revalidation-history", []
            )
            after_history = after_delivery.get(
                "reconcile-revalidation-history"
            )
            stale_render = {
                step: before_delivery[step]
                for step in (
                    "reconcile-pr-body-request",
                    "reconcile-pr-body",
                )
                if step in before_delivery
            }
            expected_prepare = copy.deepcopy(old_prepare)
            if isinstance(expected_prepare, dict):
                expected_prepare.update(
                    {
                        "result": "revalidated",
                        "new_semantic_ref": current_ticket["candidate_ref"],
                        "new_delivery_ref": current_ticket["candidate_ref"],
                        "new_head": details["new_local_head"],
                        "candidate_ref": current_ticket["candidate_ref"],
                        "artifact_generation_after": current_ticket[
                            "artifact_generation"
                        ],
                    }
                )
            require(
                previous_ticket["state"] == "verified"
                and current_ticket["state"] == "verified"
                and previous_ticket["stage"] is None
                and current_ticket["stage"] is None
                and current_ticket["candidate_ref"]
                == previous_ticket["candidate_ref"]
                and previous_ticket["delivery_candidate_ref"]
                != previous_ticket["candidate_ref"]
                and current_ticket["delivery_candidate_ref"]
                == current_ticket["candidate_ref"]
                and current_ticket["artifact_generation"]
                == previous_ticket["artifact_generation"]
                and current_ticket["validated_stages"]
                == previous_ticket["validated_stages"]
                and current_ticket["leaf_results"]
                == previous_ticket["leaf_results"]
                and current_ticket["leaf_progress_events"]
                == previous_ticket["leaf_progress_events"]
                and current_ticket["merge_authorization"] is None,
                "reconciliation-candidate-sealed lifecycle is impossible",
            )
            require(
                isinstance(old_prepare, dict)
                and old_prepare.get("new_head") == details["old_local_head"]
                and old_prepare.get("new_delivery_ref")
                == previous_ticket["delivery_candidate_ref"]
                and isinstance(new_prepare, dict)
                and new_prepare == expected_prepare
                and isinstance(before_history, list)
                and isinstance(after_history, list)
                and after_history[:-1] == before_history
                and after_history[-1]
                == {
                    "schema": 1,
                    "prepare": old_prepare,
                    "delivery_candidate_ref": previous_ticket[
                        "delivery_candidate_ref"
                    ],
                    "new_candidate_ref": current_ticket["candidate_ref"],
                    "old_local_head": details["old_local_head"],
                    "new_local_head": details["new_local_head"],
                    "render_receipts": stale_render,
                }
                and all(step not in after_delivery for step in stale_render),
                "reconciliation-candidate-sealed lineage is invalid",
            )
            actual_delivery_changes = {
                key
                for key in set(before_delivery) | set(after_delivery)
                if before_delivery.get(key) != after_delivery.get(key)
                or (key in before_delivery) != (key in after_delivery)
            }
            require(
                actual_delivery_changes
                == {
                    "reconcile-prepare",
                    "reconcile-revalidation-history",
                    *stale_render,
                },
                "reconciliation-candidate-sealed changed unrelated delivery metadata",
            )
            require_ticket_changes(
                {
                    "delivery_candidate_ref",
                    "merge_authorization",
                    "delivery",
                },
                {"delivery_candidate_ref", "delivery"},
            )
            require(
                details["candidate_digest"]
                == AtomicLedger._candidate_digest(current_ticket["candidate_ref"])
                and details["artifact_generation"]
                == current_ticket["artifact_generation"],
                "reconciliation-candidate-sealed payload is invalid",
            )
        elif name == "reconciliation-delivery-revalidation-required":
            require_scope(ticket=True)
            require_details("candidate_digest", "artifact_generation")
            prepared = current_ticket["delivery"].get("reconcile-prepare")
            require(
                previous_ticket["state"] == "verified"
                and current_ticket["state"] == "active"
                and current_ticket["stage"] == "review"
                and current_ticket["validated_stages"]
                == ["implement", "simplify"]
                and current_ticket["candidate_ref"]
                != previous_ticket["candidate_ref"]
                and current_ticket["delivery_candidate_ref"]
                == previous_ticket["delivery_candidate_ref"]
                and current_ticket["candidate_ref"]
                != current_ticket["delivery_candidate_ref"]
                and current_ticket["artifact_generation"]
                == previous_ticket["artifact_generation"] + 1
                and current_ticket["merge_authorization"] is None
                and current_ticket["delivery"] == previous_ticket["delivery"]
                and isinstance(prepared, dict)
                and prepared.get("new_delivery_ref")
                == current_ticket["delivery_candidate_ref"]
                and prepared.get("target_base", {}).get("tree_oid")
                == current_ticket["candidate_ref"].get("base_tree_oid")
                and current_ticket.get("docs_only") is None,
                "reconciliation-delivery-revalidation-required lifecycle is impossible",
            )
            require_ticket_changes(
                {
                    "candidate_ref",
                    "state",
                    "stage",
                    "validated_stages",
                    "artifact_generation",
                    "merge_authorization",
                    "leaf_progress_events",
                    "leaf_handoff",
                    "leaf_results",
                    "leaf_budget",
                    "docs_only",
                },
                {
                    "candidate_ref",
                    "state",
                    "stage",
                    "validated_stages",
                    "artifact_generation",
                },
            )
            require(
                details["candidate_digest"]
                == AtomicLedger._candidate_digest(current_ticket["candidate_ref"])
                and details["artifact_generation"]
                == current_ticket["artifact_generation"],
                "reconciliation-delivery-revalidation-required payload is invalid",
            )
        elif name in {
            "delivery-revalidation-required",
            "reconciliation-revalidation-required",
        }:
            require_scope(ticket=True)
            base_fields = {"candidate_digest", "artifact_generation"}
            if name == "reconciliation-revalidation-required":
                require_details(
                    "old_head",
                    "new_head",
                    "candidate_digest",
                    "artifact_generation",
                )
                delivery_step = "reconcile-prepare"
                expected_before_states = {"pr-open", "gated"}
            else:
                require_details(*sorted(base_fields))
                delivery_step = "prepared"
                expected_before_states = {"verified"}
            require(
                previous_ticket["state"] in expected_before_states
                and current_ticket["state"] == "active"
                and current_ticket["stage"] == "review"
                and current_ticket["validated_stages"]
                == ["implement", "simplify"]
                and current_ticket["artifact_generation"]
                == previous_ticket["artifact_generation"] + 1
                and current_ticket["candidate_ref"]
                == current_ticket["delivery_candidate_ref"]
                and current_ticket["merge_authorization"] is None,
                f"{name} lifecycle is impossible",
            )
            require(
                current_ticket.get("docs_only") is None,
                f"{name} retained stale docs-only evidence",
            )
            require_ticket_changes(
                {
                    "candidate_ref",
                    "delivery_candidate_ref",
                    "state",
                    "stage",
                    "validated_stages",
                    "artifact_generation",
                    "merge_authorization",
                    "delivery",
                    "leaf_progress_events",
                    "leaf_handoff",
                    "leaf_results",
                    "leaf_budget",
                    "docs_only",
                },
                {
                    "candidate_ref",
                    "state",
                    "stage",
                    "validated_stages",
                    "artifact_generation",
                    "delivery",
                },
            )
            before_delivery = previous_ticket["delivery"]
            after_delivery = current_ticket["delivery"]
            expected_delivery_changes = (
                reconciliation_delivery_changes()
                if name == "reconciliation-revalidation-required"
                else {delivery_step}
            )
            if name == "delivery-revalidation-required":
                expected_delivery_changes.update(
                    stale_step
                    for stale_step in (
                        "pr-body-request",
                        "pr-body",
                        "pr",
                        "provider-simulation",
                        "result",
                    )
                    if stale_step in before_delivery
                )
            require(
                {
                    key
                    for key in set(before_delivery) | set(after_delivery)
                    if before_delivery.get(key) != after_delivery.get(key)
                    or (key in before_delivery) != (key in after_delivery)
                }
                == expected_delivery_changes,
                f"{name} changed unrelated delivery metadata",
            )
            candidate_digest = AtomicLedger._candidate_digest(
                current_ticket["candidate_ref"]
            )
            require(
                details["candidate_digest"] == candidate_digest
                and details["artifact_generation"]
                == current_ticket["artifact_generation"],
                f"{name} payload is invalid",
            )
            delivery = after_delivery[delivery_step]
            if name == "reconciliation-revalidation-required":
                require(
                    delivery.get("schema") == 1
                    and delivery.get("result") == "invalidated"
                    and delivery.get("old_semantic_ref")
                    == previous_ticket["candidate_ref"]
                    and delivery.get("new_semantic_ref")
                    == current_ticket["candidate_ref"]
                    and delivery.get("old_delivery_ref")
                    == previous_ticket["delivery_candidate_ref"]
                    and delivery.get("new_delivery_ref")
                    == current_ticket["delivery_candidate_ref"]
                    and delivery.get("candidate_ref")
                    == current_ticket["candidate_ref"]
                    and delivery.get("artifact_generation_before")
                    == previous_ticket["artifact_generation"]
                    and delivery.get("artifact_generation_after")
                    == current_ticket["artifact_generation"]
                    and details["old_head"] == delivery.get("old_head")
                    and details["new_head"] == delivery.get("new_head")
                    and previous_ticket.get("pr", {}).get("head_sha")
                    == details["old_head"],
                    "reconciliation payload contradicts PR state",
                )
            else:
                require(
                    delivery.get("candidate_ref")
                    == current_ticket["candidate_ref"]
                    and delivery.get("artifact_generation")
                    == current_ticket["artifact_generation"],
                    f"{name} delivery CandidateRef is invalid",
                )
        elif name == "reconciliation-target-refreshed":
            require_scope(ticket=True)
            require_details(
                "old_head",
                "new_head",
                "old_target_sha",
                "new_target_sha",
                "candidate_digest",
                "artifact_generation",
                "semantic_change",
            )
            semantic_change = details["semantic_change"]
            require(
                isinstance(semantic_change, bool)
                and previous_ticket["state"] in {"verified", "gated"}
                and previous_ticket.get("pr", {}).get("head_sha")
                == details["old_head"]
                and current_ticket["merge_authorization"] is None,
                "reconciliation-target-refreshed lifecycle is impossible",
            )
            before_delivery = previous_ticket["delivery"]
            after_delivery = current_ticket["delivery"]
            refresh_intent = before_delivery.get("reconcile-refresh-intent")
            old_intent = before_delivery.get("reconcile-intent")
            old_prepare = before_delivery.get("reconcile-prepare")
            new_intent = after_delivery.get("reconcile-intent")
            new_prepare = after_delivery.get("reconcile-prepare")
            before_history = before_delivery.get(
                "reconcile-attempt-history", []
            )
            after_history = after_delivery.get(
                "reconcile-attempt-history"
            )
            stale_render = {
                step: before_delivery[step]
                for step in (
                    "reconcile-pr-body-request",
                    "reconcile-pr-body",
                )
                if step in before_delivery
            }
            require(
                isinstance(refresh_intent, dict)
                and isinstance(old_intent, dict)
                and isinstance(old_prepare, dict)
                and isinstance(new_intent, dict)
                and isinstance(new_prepare, dict)
                and isinstance(before_history, list)
                and isinstance(after_history, list)
                and after_history[:-1] == before_history
                and after_history[-1]
                == {
                    "schema": 1,
                    "intent": old_intent,
                    "prepare": old_prepare,
                    "refresh_intent": refresh_intent,
                    "render_receipts": stale_render,
                }
                and "reconcile-refresh-intent" not in after_delivery
                and all(step not in after_delivery for step in stale_render)
                and "reconcile-push" not in before_delivery
                and "reconcile-retarget" not in before_delivery,
                "reconciliation target refresh history is invalid",
            )
            require(
                refresh_intent.get("schema") == 1
                and refresh_intent.get("old_intent") == old_intent
                and refresh_intent.get("old_prepare") == old_prepare
                and refresh_intent.get("replacement_intent") == new_intent
                and refresh_intent.get("old_local_head")
                == old_prepare.get("new_head")
                and refresh_intent.get("old_target", {}).get("sha")
                == details["old_target_sha"]
                and refresh_intent.get("new_target", {}).get("sha")
                == details["new_target_sha"]
                and new_prepare.get("old_head") == details["old_head"]
                and new_prepare.get("new_head") == details["new_head"]
                and new_prepare.get("target_base", {}).get("sha")
                == details["new_target_sha"],
                "reconciliation target refresh payload is invalid",
            )
            actual_delivery_changes = {
                key
                for key in set(before_delivery) | set(after_delivery)
                if before_delivery.get(key) != after_delivery.get(key)
                or (key in before_delivery) != (key in after_delivery)
            }
            expected_delivery_changes = reconciliation_delivery_changes() | {
                "reconcile-intent",
                "reconcile-refresh-intent",
                "reconcile-attempt-history",
                *stale_render,
            }
            require(
                actual_delivery_changes == expected_delivery_changes,
                "reconciliation-target-refreshed changed unrelated delivery metadata",
            )
            candidate_digest = AtomicLedger._candidate_digest(
                current_ticket["candidate_ref"]
            )
            require(
                details["candidate_digest"] == candidate_digest
                and details["artifact_generation"]
                == current_ticket["artifact_generation"],
                "reconciliation-target-refreshed candidate payload is invalid",
            )
            if semantic_change:
                require(
                    current_ticket["state"] == "active"
                    and current_ticket["stage"] == "review"
                    and current_ticket["validated_stages"]
                    == ["implement", "simplify"]
                    and current_ticket["artifact_generation"]
                    == previous_ticket["artifact_generation"] + 1
                    and current_ticket["candidate_ref"]
                    == current_ticket["delivery_candidate_ref"]
                    and current_ticket.get("docs_only") is None,
                    "semantic reconciliation target refresh is invalid",
                )
                require_ticket_changes(
                    {
                        "candidate_ref",
                        "delivery_candidate_ref",
                        "state",
                        "stage",
                        "validated_stages",
                        "artifact_generation",
                        "merge_authorization",
                        "delivery",
                        "leaf_progress_events",
                        "leaf_handoff",
                        "leaf_results",
                        "leaf_budget",
                        "docs_only",
                    },
                    {
                        "candidate_ref",
                        "state",
                        "stage",
                        "validated_stages",
                        "artifact_generation",
                        "delivery",
                    },
                )
            else:
                require(
                    current_ticket["state"] == "verified"
                    and current_ticket["stage"] is None
                    and current_ticket["candidate_ref"]
                    == previous_ticket["candidate_ref"]
                    and current_ticket["delivery_candidate_ref"]
                    == previous_ticket["delivery_candidate_ref"]
                    and current_ticket["validated_stages"]
                    == previous_ticket["validated_stages"]
                    and current_ticket["leaf_results"]
                    == previous_ticket["leaf_results"]
                    and current_ticket["leaf_progress_events"]
                    == previous_ticket["leaf_progress_events"]
                    and current_ticket["artifact_generation"]
                    == previous_ticket["artifact_generation"],
                    "equivalent reconciliation target refresh is invalid",
                )
                require_ticket_changes(
                    {"state", "merge_authorization", "delivery"},
                    {"delivery"},
                )
        elif name == "reconciliation-equivalent":
            require_scope(ticket=True)
            require_details(
                "old_head",
                "new_head",
                "candidate_digest",
                "artifact_generation",
            )
            receipt = current_ticket.get("delivery", {}).get(
                "reconcile-prepare"
            )
            require(
                previous_ticket["state"] in {"pr-open", "gated"}
                and current_ticket["state"] == "verified"
                and current_ticket["stage"] is None
                and current_ticket["candidate_ref"]
                == previous_ticket["candidate_ref"]
                and current_ticket["delivery_candidate_ref"]
                == previous_ticket["delivery_candidate_ref"]
                and current_ticket["validated_stages"]
                == previous_ticket["validated_stages"]
                and current_ticket["leaf_results"]
                == previous_ticket["leaf_results"]
                and current_ticket["leaf_progress_events"]
                == previous_ticket["leaf_progress_events"]
                and current_ticket["artifact_generation"]
                == previous_ticket["artifact_generation"]
                and current_ticket["merge_authorization"] is None
                and isinstance(receipt, dict)
                and receipt.get("schema") == 1
                and receipt.get("result") == "equivalent"
                and receipt.get("old_semantic_ref")
                == current_ticket["candidate_ref"]
                and receipt.get("new_semantic_ref")
                == current_ticket["candidate_ref"]
                and receipt.get("old_delivery_ref")
                == previous_ticket["delivery_candidate_ref"]
                and receipt.get("new_delivery_ref")
                == current_ticket["delivery_candidate_ref"]
                and receipt.get("old_head") == details["old_head"]
                and receipt.get("new_head") == details["new_head"]
                and receipt.get("artifact_generation_before")
                == current_ticket["artifact_generation"]
                and receipt.get("artifact_generation_after")
                == current_ticket["artifact_generation"]
                and details["candidate_digest"]
                == AtomicLedger._candidate_digest(
                    current_ticket["candidate_ref"]
                )
                and details["artifact_generation"]
                == current_ticket["artifact_generation"],
                "reconciliation-equivalent lifecycle is impossible",
            )
            require_ticket_changes(
                {
                    "state",
                    "merge_authorization",
                    "delivery",
                },
                {"state", "delivery"},
            )
            previous_delivery = previous_ticket["delivery"]
            current_delivery = current_ticket["delivery"]
            require(
                {
                    key
                    for key in set(previous_delivery) | set(current_delivery)
                    if previous_delivery.get(key) != current_delivery.get(key)
                    or (key in previous_delivery) != (key in current_delivery)
                }
                == reconciliation_delivery_changes(),
                "reconciliation-equivalent changed unrelated delivery metadata",
            )
        elif name == "pr-opened":
            require_scope(ticket=True)
            require_details("provider", "pr_id")
            pr = current_ticket.get("pr")
            require(
                previous_ticket["state"] == "verified"
                and previous_ticket.get("pr") is None
                and current_ticket["state"] == "pr-open"
                and isinstance(pr, dict)
                and set(pr) == {"provider", "pr_id", "head_sha", "branch"}
                and pr["provider"] == details["provider"]
                and pr["pr_id"] == details["pr_id"]
                and all(isinstance(pr[key], str) and pr[key] for key in pr),
                "pr-opened transition is impossible",
            )
            lineage = current_ticket.get("delivery_lineage")
            require(
                isinstance(lineage, dict)
                and lineage.get("contract_version") == 1
                and lineage.get("provider") == pr["provider"]
                and lineage.get("pr_id") == pr["pr_id"]
                and lineage.get("branch") == pr["branch"]
                and lineage.get("head_sha") == pr["head_sha"],
                "pr-opened delivery lineage contradicts PR state",
            )
            require_ticket_changes(
                {
                    "state",
                    "pr",
                    "delivery_lineage",
                    "delivery_candidate_ref",
                },
                {"state", "pr", "delivery_lineage"},
            )
        elif name == "external-head-equivalent":
            require_scope(ticket=True)
            require_details("recorded_head", "observed_head", "receipt_digest")
            before_pr = previous_ticket.get("pr")
            after_pr = current_ticket.get("pr")
            before_lineage = previous_ticket.get("delivery_lineage")
            after_lineage = current_ticket.get("delivery_lineage")
            receipt = current_ticket.get("delivery", {}).get(
                EQUIVALENT_HEAD_DELIVERY_STEP
            )
            try:
                normalized_receipt = validate_equivalent_head_receipt(
                    current, ticket_id, receipt
                )
            except (EquivalentHeadError, TypeError) as error:
                raise LedgerError(
                    "external-head-equivalent receipt is invalid"
                ) from error
            require(
                previous_ticket["state"] in {"pr-open", "gated"}
                and current_ticket["state"] == previous_ticket["state"]
                and isinstance(before_pr, dict)
                and isinstance(after_pr, dict)
                and isinstance(before_lineage, dict)
                and isinstance(after_lineage, dict)
                and before_pr.get("head_sha") == details["recorded_head"]
                and after_pr.get("head_sha") == details["observed_head"]
                and before_lineage.get("head_sha") == details["recorded_head"]
                and after_lineage.get("head_sha") == details["observed_head"]
                and normalized_receipt["recorded_head_sha"]
                == details["recorded_head"]
                and normalized_receipt["observed_head_sha"]
                == details["observed_head"]
                and canonical_digest(normalized_receipt)
                == details["receipt_digest"]
                and current_ticket.get("merge_authorization") is None,
                "external-head-equivalent transition is impossible",
            )
            require(
                {
                    key
                    for key in set(before_pr) | set(after_pr)
                    if before_pr.get(key) != after_pr.get(key)
                }
                == {"head_sha"},
                "external-head-equivalent changed unrelated PR fields",
            )
            require(
                {
                    key
                    for key in set(before_lineage) | set(after_lineage)
                    if before_lineage.get(key) != after_lineage.get(key)
                }
                == {"head_sha"},
                "external-head-equivalent changed unrelated lineage fields",
            )
            previous_delivery = previous_ticket.get("delivery", {})
            current_delivery = current_ticket.get("delivery", {})
            require(
                EQUIVALENT_HEAD_DELIVERY_STEP not in previous_delivery
                and {
                    key
                    for key in set(previous_delivery) | set(current_delivery)
                    if previous_delivery.get(key) != current_delivery.get(key)
                    or (key in previous_delivery) != (key in current_delivery)
                }
                == {EQUIVALENT_HEAD_DELIVERY_STEP},
                "external-head-equivalent changed unrelated delivery metadata",
            )
            require_ticket_changes(
                {"pr", "delivery_lineage", "merge_authorization", "delivery"},
                {"pr", "delivery_lineage", "delivery"},
            )
        elif name == "pr-head-updated":
            require_scope(ticket=True)
            require(
                set(details)
                in (
                    {"expected_old", "new"},
                    {"expected_old", "new", "base"},
                ),
                "pr-head-updated event payload is invalid",
            )
            before_pr = previous_ticket.get("pr")
            after_pr = current_ticket.get("pr")
            require(
                isinstance(before_pr, dict)
                and isinstance(after_pr, dict),
                "pr-head-updated requires before and after PR records",
            )
            require(
                before_pr.get("head_sha") == details["expected_old"],
                "pr-head-updated old head payload is invalid",
            )
            require(
                after_pr.get("head_sha") == details["new"],
                "pr-head-updated new head payload is invalid",
            )
            changed_pr_fields = {
                key
                for key in set(before_pr) | set(after_pr)
                if before_pr.get(key) != after_pr.get(key)
            }
            expected_pr_changes = (
                set()
                if details["expected_old"] == details["new"]
                else {"head_sha"}
            )
            require(
                changed_pr_fields == expected_pr_changes,
                "pr-head-updated changed unrelated PR fields: "
                f"{sorted(changed_pr_fields)}",
            )
            require(
                current_ticket["merge_authorization"] is None,
                "pr-head-updated retained merge authorization",
            )
            before_lineage = previous_ticket.get("delivery_lineage")
            after_lineage = current_ticket.get("delivery_lineage")
            require(
                isinstance(before_lineage, dict)
                and isinstance(after_lineage, dict)
                and after_lineage.get("head_sha") == details["new"],
                "pr-head-updated delivery lineage is invalid",
            )
            if "base" in details:
                prepared = previous_ticket["delivery"].get(
                    "reconcile-prepare", {}
                )
                require(
                    previous_ticket["state"] == "verified"
                    and current_ticket["state"] == "pr-open"
                    and prepared.get("old_head") == details["expected_old"]
                    and prepared.get("new_head") == details["new"]
                    and prepared.get("target_base", {}).get("branch")
                    == details["base"],
                    "reconciled pr-head-updated transition is impossible",
                )
                require_ticket_changes(
                    {
                        "state",
                        "pr",
                        "merge_authorization",
                        "delivery_lineage",
                    },
                    {"state", "delivery_lineage"},
                )
            else:
                require(
                    previous_ticket["state"] == "pr-open"
                    and current_ticket["state"] == "pr-open",
                    "pr-head-updated lifecycle is impossible",
                )
                require_ticket_changes(
                    {"pr", "merge_authorization", "delivery_lineage"},
                    {"pr", "delivery_lineage"},
                )
        elif name == "ticket-integrated":
            require_scope(ticket=True)
            proof_event = set(details) == {
                "head_sha",
                "terminal_proof_digest",
            }
            require(
                proof_event or set(details) == {"head_sha"},
                "ticket-integrated event payload is invalid",
            )
            authorization = current_ticket.get("merge_authorization")
            integration = current_ticket.get("delivery", {}).get("integration")
            terminal_proof = current_ticket.get("delivery", {}).get(
                "terminal-integration"
            )
            if proof_event:
                try:
                    validated_proof = validate_terminal_integration_proof(
                        current,
                        ticket_id,
                        terminal_proof,
                        integration,
                        provenance="runner-merge",
                    )
                except (TerminalIntegrationError, TypeError) as error:
                    raise LedgerError(
                        "ticket-integrated terminal proof is invalid"
                    ) from error
                require(
                    canonical_digest(validated_proof)
                    == details["terminal_proof_digest"],
                    "ticket-integrated terminal proof digest is invalid",
                )
            require(
                previous_ticket["state"] == "pr-open"
                and current_ticket["state"] == "integrated"
                and current_ticket["pr"] == previous_ticket["pr"]
                and current_ticket["merge_authorization"]
                == previous_ticket["merge_authorization"]
                and isinstance(authorization, dict)
                and authorization.get("head_sha") == details["head_sha"]
                and current_ticket["pr"].get("head_sha")
                == details["head_sha"],
                "ticket-integrated transition is impossible",
            )
            allowed_changes = {
                "state",
                "disposition",
                "attempt_outcome",
                "stop_reason",
                "disposition_receipt",
            }
            required_changes = {"state"}
            if proof_event:
                allowed_changes.add("delivery")
                required_changes.add("delivery")
            require_ticket_changes(allowed_changes, required_changes)
        elif name == "external-merge-integrated":
            require_scope(ticket=True)
            proof_event = set(details) == {
                "actor",
                "head_sha",
                "provider",
                "pr_id",
                "terminal_proof_digest",
            }
            require(
                proof_event
                or set(details) == {"actor", "head_sha", "provider", "pr_id"},
                "external-merge-integrated event payload is invalid",
            )
            authorization = current_ticket.get("merge_authorization")
            integration = current_ticket.get("delivery", {}).get("integration")
            terminal_proof = current_ticket.get("delivery", {}).get(
                "terminal-integration"
            )
            reconciliation = current_ticket.get("delivery", {}).get(
                "external-reconciliation"
            )
            previous_delivery = previous_ticket.get("delivery", {})
            current_delivery = current_ticket.get("delivery", {})
            changed_delivery_steps = {
                step
                for step in set(previous_delivery) | set(current_delivery)
                if previous_delivery.get(step) != current_delivery.get(step)
                or (step in previous_delivery) != (step in current_delivery)
            }
            if proof_event:
                try:
                    validated_proof = validate_terminal_integration_proof(
                        current,
                        ticket_id,
                        terminal_proof,
                        integration,
                        provenance="external-readback",
                    )
                except (TerminalIntegrationError, TypeError) as error:
                    raise LedgerError(
                        "external integration terminal proof is invalid"
                    ) from error
                require(
                    canonical_digest(validated_proof)
                    == details["terminal_proof_digest"],
                    "external integration terminal proof digest is invalid",
                )
            expected_reconciliation = {
                "schema": 1,
                "mode": "external",
                "provider": details["provider"],
                "pr_id": details["pr_id"],
                "head_sha": details["head_sha"],
                "actor": details["actor"],
                "evidence": authorization.get("evidence")
                if isinstance(authorization, dict)
                else None,
                "observation": integration,
            }
            expected_steps = {"external-reconciliation", "integration"}
            if proof_event:
                expected_reconciliation["terminal_proof"] = terminal_proof
                expected_steps.add("terminal-integration")
            require(
                previous_ticket["state"] == "pr-open"
                and current_ticket["state"] == "integrated"
                and current_ticket["pr"] == previous_ticket["pr"]
                and previous_ticket.get("merge_authorization") is None
                and isinstance(authorization, dict)
                and authorization
                == {
                    "actor": details["actor"],
                    "head_sha": details["head_sha"],
                    "evidence": authorization.get("evidence"),
                    "mode": "external",
                }
                and isinstance(authorization.get("evidence"), str)
                and bool(authorization["evidence"])
                and isinstance(integration, dict)
                and integration.get("schema") == 1
                and integration.get("provider") == details["provider"]
                and integration.get("operation") == "get-pr-state"
                and integration.get("evidence_class") == "live"
                and integration.get("observed") is True
                and integration.get("pr_id") == details["pr_id"]
                and integration.get("head_sha") == details["head_sha"]
                and integration.get("state") == "merged"
                and reconciliation == expected_reconciliation
                and current_ticket["pr"].get("provider")
                == details["provider"]
                and current_ticket["pr"].get("pr_id") == details["pr_id"]
                and current_ticket["pr"].get("head_sha")
                == details["head_sha"]
                and changed_delivery_steps == expected_steps,
                "external-merge-integrated transition is impossible",
            )
            require_ticket_changes(
                {
                    "state",
                    "merge_authorization",
                    "delivery",
                    "disposition",
                    "attempt_outcome",
                    "stop_reason",
                    "disposition_receipt",
                },
                {
                    "state",
                    "merge_authorization",
                    "delivery",
                },
            )
        elif name == "merge-authorized":
            require_scope(ticket=True)
            require_details("actor", "head_sha", "mode")
            authorization = current_ticket.get("merge_authorization")
            require(
                previous_ticket["state"] == "pr-open"
                and current_ticket["state"] == "pr-open"
                and previous_ticket["pr"] == current_ticket["pr"]
                and isinstance(authorization, dict)
                and set(authorization)
                == {"actor", "head_sha", "evidence", "mode"}
                and authorization["actor"] == details["actor"]
                and authorization["head_sha"] == details["head_sha"]
                and authorization["head_sha"]
                == current_ticket["pr"]["head_sha"]
                and authorization["mode"] == details["mode"]
                and authorization["mode"]
                in {"runner", "external", "autonomous"}
                and isinstance(authorization["evidence"], str)
                and bool(authorization["evidence"]),
                "merge-authorized transition is impossible",
            )
            require_ticket_changes(
                {"merge_authorization"}, {"merge_authorization"}
            )
        elif name == "ticket-disposition-changed":
            require_scope(ticket=True, gates=True)
            require_details("receipt")
            receipt = details["receipt"]
            target = receipt.get("to_disposition") if isinstance(receipt, dict) else None
            require(
                isinstance(receipt, dict)
                and receipt.get("schema") == 1
                and receipt.get("state") == "applied"
                and receipt.get("ticket_id") == ticket_id
                and receipt.get("from_disposition")
                == previous_ticket.get("disposition")
                and target == current_ticket.get("disposition")
                and current_ticket.get("disposition_receipt") == receipt,
                "ticket-disposition-changed receipt is impossible",
            )
            allowed = {
                "state",
                "stage",
                "quality_failures",
                "leaf_budget",
                "leaf_progress_events",
                "leaf_handoff",
                "leaf_results",
                "failure_kind",
                "candidate_ref",
                "delivery_candidate_ref",
                "delivery_lineage",
                "artifact_generation",
                "validated_stages",
                "delivery",
                "pr",
                "merge_authorization",
                "preexisting_integrated",
                "resume_pending",
                "disposition",
                "attempt_outcome",
                "stop_reason",
                "disposition_receipt",
                "current_source_relative_path",
            }
            require_ticket_changes(
                allowed,
                {
                    "disposition",
                    "disposition_receipt",
                    "current_source_relative_path",
                },
            )
            require(
                receipt.get("source_relative_path")
                == previous_ticket.get("current_source_relative_path")
                and receipt.get("destination_relative_path")
                == current_ticket.get("current_source_relative_path"),
                "ticket disposition receipt does not track operational path",
            )
            if target == "open":
                gate_id = receipt.get("authority_gate_id")
                before_gate = previous["gates"].get(gate_id)
                after_gate = current["gates"].get(gate_id)
                require(
                    isinstance(before_gate, dict)
                    and isinstance(after_gate, dict)
                    and before_gate.get("state") == "passed"
                    and before_gate.get("actor") == receipt.get("actor")
                    and before_gate.get("evidence") == receipt.get("authority_ref")
                    and before_gate.get("consumed_by_transition_id") is None
                    and after_gate
                    == {
                        **before_gate,
                        "consumed_by_transition_id": receipt.get("transition_id"),
                    }
                    and all(
                        previous["gates"][other_id] == current["gates"][other_id]
                        for other_id in previous["gates"]
                        if other_id != gate_id
                    )
                    and previous_ticket.get("disposition")
                    in {"on-hold", "canceled"}
                    and current_ticket["state"] == "pending"
                    and current_ticket["stage"] is None
                    and current_ticket["candidate_ref"] is None
                    and current_ticket["validated_stages"] == []
                    and current_ticket["delivery"] == {}
                    and current_ticket["pr"] is None
                    and current_ticket["merge_authorization"] is None
                    and current_ticket["attempt_outcome"] is None
                    and current_ticket["stop_reason"] is None,
                    "ticket reopen did not invalidate stale execution state",
                )
            else:
                require(
                    target in {"on-hold", "canceled"}
                    and previous["gates"] == current["gates"]
                    and previous_ticket.get("disposition") == "open"
                    and previous_ticket["state"] in {"pending", "active"}
                    and current_ticket["state"] == "pending"
                    and (
                        previous_ticket["state"] != "active"
                        or (
                            current_ticket["attempt_outcome"] == "stopped"
                            and current_ticket["stop_reason"]
                            == f"administrative-{target}"
                        )
                    ),
                    "ticket hold/cancel safe-boundary transition is impossible",
                )
        elif name == "completion-projection-granted":
            require_scope(ticket=True)
            require_details("grant")
            grant = current_ticket.get("completion_projection_grant")
            if "completion_projection_grants" not in current_ticket:
                # ICP-01 history remains replayable byte-for-byte.
                require_ticket_changes(
                    {"completion_projection_grant"},
                    {"completion_projection_grant"},
                )
                valid_transition = (
                    previous_ticket.get("completion_projection_grant") is None
                )
            else:
                require_ticket_changes(
                    {
                        "completion_projection_grant",
                        "completion_projection_grants",
                    },
                    {
                        "completion_projection_grant",
                        "completion_projection_grants",
                    },
                )
                previous_entries = completion_projection_grant_entries(
                    previous, ticket_id
                )
                current_entries = completion_projection_grant_entries(
                    current, ticket_id
                )
                valid_transition = (
                    previous_entries is not None
                    and current_entries is not None
                    and len(current_entries) == len(previous_entries) + 1
                    and current_entries[:-1] == previous_entries
                    and current_entries[-1]["grant"] == grant
                    and all(
                        entry["grant"] != grant
                        for entry in previous_entries
                    )
                )
            require(
                valid_transition
                and isinstance(grant, dict)
                and details["grant"] == grant
                and grant.get("candidate_ref") == previous_ticket.get("candidate_ref")
                and current_ticket.get("candidate_ref")
                == previous_ticket.get("candidate_ref")
                and completion_projection_grant_matches_ticket(current, ticket_id),
                "completion-projection-granted grant is invalid",
            )
        elif name == "completion-projection-gate-resolved":
            require_scope(ticket=True, gates=True)
            require(
                set(details)
                in (
                    {"grant", "gate_id"},
                    {"grant", "gate_id", "delivery_head_proof"},
                ),
                "completion-projection-gate-resolved event payload is invalid",
            )
            require_ticket_changes({"state", "stage", "resume_pending"})
            grant = current_ticket.get("completion_projection_grant")
            gate_id = details["gate_id"]
            before_gate = previous["gates"].get(gate_id)
            after_gate = current["gates"].get(gate_id)
            proof = details.get("delivery_head_proof")
            base_classification = (
                before_gate.get("details", {}).get("base_classification")
                if isinstance(before_gate, dict)
                else None
            )
            proof_valid = (
                proof is None and base_classification == "ignored"
            ) or (
                isinstance(proof, dict)
                and base_classification == "tracked"
                and completion_projection_delivery_head_proof_matches(
                    previous, ticket_id, gate_id, proof
                )
            )
            expected_gate = (
                {
                    **before_gate,
                    "state": "passed",
                    "actor": grant["actor"],
                    "evidence": grant["evidence"],
                    **(
                        {
                            "completion_projection_delivery_head_proof": copy.deepcopy(
                                proof
                            )
                        }
                        if proof is not None
                        else {}
                    ),
                }
                if isinstance(before_gate, dict) and isinstance(grant, dict)
                else None
            )
            require(
                isinstance(grant, dict)
                and grant == previous_ticket.get("completion_projection_grant")
                and details["grant"] == grant
                and grant.get("candidate_ref") == previous_ticket.get("candidate_ref")
                and current_ticket.get("candidate_ref")
                == previous_ticket.get("candidate_ref")
                and completion_projection_grant_matches_ticket(current, ticket_id)
                and isinstance(before_gate, dict)
                and isinstance(after_gate, dict)
                and before_gate.get("ticket_id") == ticket_id
                and before_gate.get("category") == "source-mode-drift"
                and before_gate.get("state") == "open"
                and proof_valid
                and after_gate == expected_gate
                and all(
                    previous["gates"].get(other_id)
                    == current["gates"].get(other_id)
                    for other_id in set(previous["gates"]) | set(current["gates"])
                    if other_id != gate_id
                ),
                "completion projection consumed a non-matching gate",
            )
            other_open = any(
                other_id != gate_id
                and gate.get("ticket_id") == ticket_id
                and gate.get("state") == "open"
                for other_id, gate in current["gates"].items()
            )
            active_other = any(
                other_id != ticket_id and other.get("state") == "active"
                for other_id, other in previous["tickets"].items()
            )
            resume_deferred = (
                not other_open
                and before_gate["resume_state"] == "active"
                and active_other
            )
            expected_state = (
                "gated"
                if other_open
                else "pending"
                if resume_deferred
                else before_gate["resume_state"]
            )
            expected_stage = (
                previous_ticket["stage"]
                if other_open
                else None
                if resume_deferred
                else before_gate["resume_stage"]
            )
            require(
                current_ticket["state"] == expected_state
                and current_ticket["stage"] == expected_stage
                and (
                    current_ticket.get("resume_pending") is True
                    if resume_deferred
                    else current_ticket.get("resume_pending")
                    == previous_ticket.get("resume_pending")
                ),
                "completion projection gate resume state is invalid",
            )
        elif name == "autonomous-merge-granted":
            require_scope()
            require_details("grant")
            grant = current.get("autonomous_merge_grant")
            unresolved_steps = any(
                ticket.get("state") != "integrated"
                and (
                    ticket.get("merge_authorization") is not None
                    or any(
                        step in ticket.get("delivery", {})
                        for step in HEAD_BOUND_MERGE_DELIVERY_STEPS
                    )
                )
                for ticket in previous["tickets"].values()
            )
            require(
                previous.get("merge_policy", "manual") == "manual"
                and previous.get("autonomous_merge_grant") is None
                and previous["run_state"]
                not in {"completed", "failed", "aborted"}
                and not unresolved_steps
                and current.get("merge_policy") == "autonomous"
                and autonomous_merge_grant_matches_run(current)
                and details["grant"] == grant,
                "autonomous-merge-granted transition is impossible",
            )
        elif name == "run-paused":
            require_scope(pause=True)
            require_details("actor", "reason")
            require(
                previous.get("pause") is None
                and current.get("pause")
                == {"actor": details["actor"], "reason": details["reason"]}
                and all(
                    isinstance(details[field], str) and details[field]
                    for field in ("actor", "reason")
                ),
                "run-paused transition is impossible",
            )
        elif name == "run-unpaused":
            require_scope(pause=True)
            require_details("actor", "reason", "previous")
            require(
                isinstance(previous.get("pause"), dict)
                and details["previous"] == previous["pause"]
                and current.get("pause") is None
                and all(
                    isinstance(details[field], str) and details[field]
                    for field in ("actor", "reason")
                ),
                "run-unpaused transition is impossible",
            )
        elif name == "run-aborted":
            require_scope()
            require_details("actor", "reason")
            require(
                previous["run_state"] not in {"completed", "aborted"}
                and current["run_state"] == "aborted"
                and all(
                    isinstance(details[key], str) and details[key]
                    for key in ("actor", "reason")
                ),
                "run-aborted transition is impossible",
            )
        elif name == "worktree-cleaned":
            require_scope(cleanup=True)
            require_details("worktree", "resume_abandoned")
            cleanup = current.get("cleanup")
            require(
                previous["run_state"] != "running"
                and current["run_state"] == previous["run_state"]
                and previous.get("cleanup") is None
                and isinstance(cleanup, dict)
                and cleanup
                == {
                    "recorded": True,
                    "worktree": details["worktree"],
                    "worktree_removed": cleanup.get("worktree_removed"),
                    "resume_abandoned": details["resume_abandoned"],
                    "remote_state_deleted": False,
                }
                and isinstance(cleanup["worktree_removed"], bool)
                and isinstance(details["worktree"], str)
                and bool(details["worktree"])
                and isinstance(details["resume_abandoned"], bool),
                "worktree-cleaned transition is impossible",
            )

        if name not in {"run-aborted", "worktree-cleaned"}:
            require(
                current["run_state"]
                == AtomicLedger._derived_run_state(current),
                f"{name} produced an impossible run state",
            )

    @staticmethod
    def _validate_ticket_snapshot(document: dict[str, Any]) -> None:
        tickets = document.get("tickets")
        if tickets is not None:
            merge_policy = document.get("merge_policy", "manual")
            grant = document.get("autonomous_merge_grant")
            if merge_policy not in {"manual", "autonomous"}:
                raise LedgerError("ledger contains an invalid merge policy")
            if merge_policy == "manual":
                if grant is not None:
                    raise LedgerError(
                        "manual merge policy cannot carry an autonomous grant"
                    )
            elif not autonomous_merge_grant_matches_run(document):
                raise LedgerError(
                    "autonomous merge grant contradicts its run binding"
                )
            if not wiki_sync_merge_grant_matches_run(document):
                raise LedgerError(
                    "wiki-sync merge grant contradicts its scoped run binding"
                )
            proof_version = document.get("terminal_integration_proof_version")
            if proof_version not in {None, 1}:
                raise LedgerError("ledger terminal integration proof version is invalid")
            source_mode = document.get("ticket_source_mode")
            manifest_digest = document.get("snapshot_manifest_digest")
            manifest_path = document.get("snapshot_manifest_path")
            folder_identity = document.get("ticket_source_folder_identity")
            if source_mode not in {"tracked", "ignored"}:
                raise LedgerError(
                    "ledger ticket source metadata is required; start a new run"
                )
            if (
                not isinstance(manifest_digest, str)
                or len(manifest_digest) != 64
                or any(
                    character not in "0123456789abcdef"
                    for character in manifest_digest
                )
                or not isinstance(manifest_path, str)
                or not manifest_path
            ):
                raise LedgerError("ledger managed ticket snapshot metadata is invalid")
            if (
                not isinstance(folder_identity, dict)
                or set(folder_identity) != {"device", "inode"}
                or any(
                    type(folder_identity[field]) is not int
                    for field in folder_identity
                )
                or any(folder_identity[field] < 0 for field in folder_identity)
            ):
                raise LedgerError("ledger ticket source folder identity is invalid")
            if not isinstance(tickets, dict) or not isinstance(
                document.get("ticket_order"), list
            ):
                raise LedgerError("ledger ticket snapshot is malformed")
            if document["ticket_order"] != list(tickets):
                raise LedgerError("ledger ticket order differs from ticket snapshot")
            active = [
                ticket
                for ticket in tickets.values()
                if isinstance(ticket, dict) and ticket.get("state") == "active"
            ]
            if len(active) > 1:
                raise LedgerError("ledger has more than one active mutating ticket")
            legacy = document.get("schema") == 3
            pause = document.get("pause")
            if pause is not None and (
                not isinstance(pause, dict)
                or set(pause) != {"actor", "reason"}
                or any(
                    not isinstance(value, str) or not value
                    for value in pause.values()
                )
            ):
                raise LedgerError("ledger contains an invalid run pause receipt")
            valid_ticket_states = {
                "pending",
                "active",
                "gated",
                "failed",
                "verified",
                "pr-open",
                "integrated",
            }
            stages = (
                "implement",
                "simplify",
                "review",
                "qa-plan",
                "qa-execute",
                "verify",
                "finalize",
            )
            for ticket_id, ticket in tickets.items():
                if (
                    not isinstance(ticket, dict)
                    or ticket.get("state") not in valid_ticket_states
                ):
                    raise LedgerError("ledger contains an invalid ticket state")
                if ticket.get("execution_mode") not in {"AFK", "HITL"}:
                    raise LedgerError("ledger contains an invalid execution mode")
                if not legacy:
                    disposition = ticket.get("disposition")
                    if disposition not in {
                        "open",
                        "on-hold",
                        "canceled",
                        "completed",
                    }:
                        raise LedgerError("ledger contains an invalid disposition")
                    if "lifecycle" in ticket:
                        raise LedgerError("ledger persists a duplicate lifecycle")
                    if ticket.get("attempt_outcome") not in {None, "stopped"}:
                        raise LedgerError("ledger contains an invalid attempt outcome")
                    stop_reason = ticket.get("stop_reason")
                    if stop_reason is not None and (
                        not isinstance(stop_reason, str) or not stop_reason
                    ):
                        raise LedgerError("ledger contains an invalid stop reason")
                    if (ticket.get("attempt_outcome") == "stopped") != (
                        stop_reason is not None
                    ):
                        raise LedgerError("ledger attempt outcome and reason disagree")
                    disposition_receipt = ticket.get("disposition_receipt")
                    if disposition_receipt is not None and (
                        not isinstance(disposition_receipt, dict)
                        or disposition_receipt.get("ticket_id") != ticket_id
                        or disposition_receipt.get("to_disposition") != disposition
                        or disposition_receipt.get("state") != "applied"
                    ):
                        raise LedgerError(
                            "ledger contains an invalid disposition receipt"
                        )
                if (
                    not isinstance(ticket.get("source_relative_path"), str)
                    or not ticket["source_relative_path"]
                ):
                    raise LedgerError(
                        "ledger contains an invalid ticket source relative path"
                    )
                if not legacy and (
                    not isinstance(ticket.get("current_source_relative_path"), str)
                    or not ticket["current_source_relative_path"]
                ):
                    raise LedgerError(
                        "ledger contains an invalid current ticket source path"
                    )
                if "effective_mode" in ticket:
                    raise LedgerError(
                        "ledger contains non-canonical effective_mode"
                    )
                state = ticket["state"]
                stage = ticket.get("stage")
                candidate = ticket.get("candidate_ref")
                if "delivery_lineage" not in ticket:
                    raise LedgerError(
                        "ledger ticket lacks versioned delivery lineage"
                    )
                try:
                    if candidate is not None:
                        semantic_candidate(candidate)
                    lineage = ticket.get("delivery_lineage")
                    if lineage is not None:
                        delivery_lineage(lineage)
                    equivalence = ticket.get("delivery", {}).get(
                        EQUIVALENT_HEAD_DELIVERY_STEP
                    )
                    if equivalence is not None:
                        validate_equivalent_head_receipt(
                            document, ticket_id, equivalence
                        )
                    integration = ticket.get("delivery", {}).get("integration")
                    terminal_proof = ticket.get("delivery", {}).get(
                        "terminal-integration"
                    )
                    if terminal_proof is not None:
                        validate_terminal_integration_proof(
                            document,
                            ticket_id,
                            terminal_proof,
                            integration,
                        )
                    if (
                        proof_version == 1
                        and ticket.get("state") == "integrated"
                        and not ticket.get("preexisting_integrated")
                        and terminal_proof is None
                    ):
                        raise TerminalIntegrationError(
                            "integrated ticket lacks terminal reachability proof"
                        )
                except (
                    CandidateContractError,
                    EquivalentHeadError,
                    TerminalIntegrationError,
                    TypeError,
                ) as error:
                    raise LedgerError(str(error)) from error
                if not completion_projection_grant_matches_ticket(document, ticket_id):
                    raise LedgerError(
                        "completion projection grant contradicts its run binding"
                    )
                validated = ticket.get("validated_stages", [])
                if not isinstance(validated, list) or validated != list(
                    stages[: len(validated)]
                ):
                    raise LedgerError(
                        "ledger validated stages are not a pipeline prefix"
                    )
                docs_only = ticket.get("docs_only")
                docs_only_eligible = (
                    isinstance(docs_only, dict)
                    and docs_only.get("status") == "eligible"
                )
                if docs_only is not None and (
                    not isinstance(docs_only, dict)
                    or docs_only.get("status") not in {"eligible", "rejected"}
                ):
                    raise LedgerError("ledger docs-only receipt is invalid")
                if docs_only_eligible:
                    try:
                        normalized_docs_only = normalize_docs_only_receipt(
                            docs_only,
                            ticket=ticket,
                            candidate=candidate,
                        )
                    except (DocsOnlyError, ValueError, TypeError, KeyError) as error:
                        raise LedgerError(
                            "ledger docs-only receipt is invalid"
                        ) from error
                    if normalized_docs_only != docs_only:
                        raise LedgerError("ledger docs-only receipt is invalid")
                if docs_only_eligible and (
                    docs_only.get("candidate_ref") != candidate
                    or validated != ["implement"]
                    or ticket.get("leaf_budget", {}).get(
                        "interactions_consumed"
                    )
                    != 0
                    or set(ticket.get("leaf_results", {})) != {"verify"}
                    or docs_only.get("leaf_interactions_avoided") != 4
                ):
                    raise LedgerError(
                        "ledger eligible docs-only receipt contradicts ticket state"
                    )
                if state == "active" and (
                    stage not in stages or not isinstance(candidate, dict)
                ):
                    raise LedgerError("active ticket has no valid stage/CandidateRef")
                if state in {"failed", "verified", "pr-open", "integrated"} and stage is not None:
                    raise LedgerError("terminal ticket retains an active stage")
                preexisting = bool(ticket.get("preexisting_integrated"))
                if (
                    state in {"verified", "pr-open", "integrated"}
                    and not preexisting
                    and validated != list(stages)
                    and not docs_only_eligible
                ):
                    raise LedgerError(
                        "delivered ticket lacks complete stage validation"
                    )
                if (
                    state in {"pr-open", "integrated"}
                    and not preexisting
                    and not isinstance(ticket.get("pr"), dict)
                ):
                    raise LedgerError("delivered ticket has no PR record")
                authorization = ticket.get("merge_authorization")
                if authorization is not None:
                    pr = ticket.get("pr")
                    if (
                        not isinstance(pr, dict)
                        or authorization.get("head_sha") != pr.get("head_sha")
                    ):
                        raise LedgerError(
                            "merge authorization is stale for the PR snapshot"
                        )
            if document.get("run_state") not in {
                "running",
                "waiting",
                "completed",
                "failed",
                "aborted",
            }:
                raise LedgerError("ledger contains an invalid run state")
            run_state = document.get("run_state")
            states = [ticket["state"] for ticket in tickets.values()]
            if run_state == "completed" and not all(
                state == "integrated" for state in states
            ):
                raise LedgerError("completed run contains non-integrated tickets")
            if run_state == "failed" and not any(
                state == "failed" for state in states
            ):
                raise LedgerError("failed run contains no failed ticket")
            gates = document.get("gates", {})
            if not isinstance(gates, dict):
                raise LedgerError("ledger gates must be an object")
            for gate_id, gate in gates.items():
                if not isinstance(gate, dict) or gate.get("gate_id") != gate_id:
                    raise LedgerError("ledger contains a malformed gate")
                if gate.get("state") not in {"open", "passed", "failed", "waived"}:
                    raise LedgerError("ledger contains an invalid gate state")
                owner = gate.get("ticket_id")
                if owner is not None and owner not in tickets:
                    raise LedgerError("ledger gate owns an unknown ticket")
                details = gate.get("details")
                if details is not None and not isinstance(details, dict):
                    raise LedgerError("ledger gate details must be an object")
                if gate.get("category") == "source-mode-drift":
                    required_details = {
                        "schema",
                        "ticket_id",
                        "snapshot_classification",
                        "observed_classification",
                        "base_classification",
                        "boundary",
                        "source_path",
                        "recovery",
                    }
                    if (
                        not isinstance(details, dict)
                        or set(details) != required_details
                        or details.get("schema") != 1
                        or details.get("ticket_id") != owner
                        or details.get("snapshot_classification")
                        not in {"tracked", "ignored"}
                        or details.get("observed_classification")
                        not in {"tracked", "ignored", "untracked"}
                        or details.get("base_classification")
                        not in {"tracked", "ignored", "untracked"}
                        or any(
                            not isinstance(details.get(field), str)
                            or not details[field]
                            for field in ("boundary", "source_path", "recovery")
                        )
                    ):
                        raise LedgerError(
                            "ledger source-mode-drift gate details are invalid"
                        )
                if gate.get("kind") == "start" and (
                    owner is None
                    or tickets[owner].get("execution_mode") != "HITL"
                    or gate.get("category") != "human"
                    or gate.get("scope") != "ticket"
                    or gate.get("resume_state") != "pending"
                    or gate.get("resume_stage") is not None
                ):
                    raise LedgerError("ledger contains an invalid HITL start gate")
                if gate.get("state") == "open" and owner is not None:
                    if tickets[owner]["state"] != "gated":
                        raise LedgerError("open ticket gate does not gate its owner")
