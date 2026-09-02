from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def autonomous_merge_dependencies_ready(
    ticket: Mapping[str, Any],
    tickets: Mapping[str, Mapping[str, Any]],
) -> bool:
    """Return whether a ticket's dependency topology permits autonomous merge."""

    blockers = ticket.get("blocked_by")
    if not isinstance(blockers, list) or any(
        not isinstance(blocker_id, str) or not blocker_id
        for blocker_id in blockers
    ):
        return False
    if not blockers:
        return True

    parents: list[Mapping[str, Any]] = []
    for blocker_id in blockers:
        parent = tickets.get(blocker_id)
        if not isinstance(parent, Mapping) or parent.get("state") != "integrated":
            return False
        parents.append(parent)
    if len(parents) != 1:
        return True

    parent = parents[0]
    parent_lineage = parent.get("delivery_lineage")
    if parent_lineage is None:
        return (
            parent.get("disposition") == "completed"
            and "candidate_ref" in parent
            and parent["candidate_ref"] is None
        )

    child_lineage = ticket.get("delivery_lineage")
    if not isinstance(child_lineage, Mapping) or not isinstance(
        parent_lineage, Mapping
    ):
        return False
    child_base = child_lineage.get("base_branch")
    parent_base = parent_lineage.get("base_branch")
    return (
        isinstance(child_base, str)
        and bool(child_base)
        and isinstance(parent_base, str)
        and bool(parent_base)
        and child_base == parent_base
    )
