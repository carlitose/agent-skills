from __future__ import annotations

from collections.abc import Mapping
from typing import Any

RECONCILIATION_CONDITION_GATE_CATEGORIES = frozenset(
    {
        "provider-merge",
        "stack-reconciliation",
        "stack-reconciliation-recovery",
    }
)


def can_revalidate_provider_gated_candidate(
    ledger: Mapping[str, Any], ticket_id: str, candidate: Mapping[str, Any]
) -> bool:
    """Permit fresh quality, not gate approval, for a changed published candidate.

    This same-base recovery is restricted to ignored sources and pre-merge
    eligibility. Begun/uncertain merges and other gates retain their own paths.
    """
    ticket = ledger["tickets"][ticket_id]
    old = ticket.get("candidate_ref")
    pr = ticket.get("pr")
    delivery = ticket.get("delivery", {})
    progress = delivery.get("merge-progress", {})
    gates = [
        gate for gate in ledger.get("gates", {}).values()
        if gate.get("state") == "open"
        and (gate.get("ticket_id") == ticket_id or gate.get("scope") == "run")
    ]
    if not (
        ledger.get("ticket_source_mode") == "ignored"
        and ledger.get("pause") is None
        and ticket.get("disposition") in {"open", "completed"}
        # Ignored-source delivery completes its source before merging the PR.
        # Preserve that receipt: quality reentry is not administrative reopening.
        and (ticket.get("disposition") != "completed"
             or delivery.get("ignored-finalization-applied", {}).get("state") == "applied")
        and ticket.get("status_barrier") is None
        and ticket.get("completion_projection_grant") is None
        and ticket.get("state") == "gated" and ticket.get("stage") is None
        and isinstance(old, Mapping) and isinstance(pr, Mapping)
        and ticket.get("validated_stages") == [
            "implement", "simplify", "review", "qa-plan", "qa-execute", "verify", "finalize"
        ]
        and candidate.get("candidate_tree_oid") != old.get("candidate_tree_oid")
        and all(candidate.get(key) == old.get(key)
                for key in ("base_tree_oid", "ticket_digest", "contract_version"))
        and ticket.get("delivery_candidate_ref") == old
        and delivery.get("prepared", {}).get("candidate_ref") == old
        and not ticket.get("docs_only")
        and not {"reconcile-prepare", "merge-intent", "merge-attempt", "merge-mutation",
                 "merge-readback", "integration", "terminal-integration"}.intersection(delivery)
        and len(gates) == 1
    ):
        return False
    gate = gates[0]
    return (
        gate.get("category") == "provider-merge" and gate.get("scope") == "ticket"
        and gate.get("kind") == "dynamic" and gate.get("resume_state") == "pr-open"
        and gate.get("resume_stage") is None
        and progress.get("phase") == "eligibility" and progress.get("status") == "gated"
        and progress.get("gate_id") == gate.get("gate_id")
        and bool(pr.get("head_sha"))
        and progress.get("head_sha") == pr["head_sha"]
        and delivery.get("commit", {}).get("head_sha") == pr["head_sha"]
        and delivery.get("push", {}).get("head_sha") == pr["head_sha"]
    )


def reconciliation_condition_gate_ids(
    ledger: Mapping[str, Any], ticket_id: str
) -> list[str]:
    """Return open gates whose condition is resolved by new reconciliation lineage."""
    gates = ledger.get("gates", {})
    if not isinstance(gates, Mapping):
        return []
    return [
        gate_id
        for gate_id, gate in gates.items()
        if isinstance(gate_id, str)
        and isinstance(gate, Mapping)
        and gate.get("ticket_id") == ticket_id
        and gate.get("state") == "open"
        and gate.get("category")
        in RECONCILIATION_CONDITION_GATE_CATEGORIES
    ]
