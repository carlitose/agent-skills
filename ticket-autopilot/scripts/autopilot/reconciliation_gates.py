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
