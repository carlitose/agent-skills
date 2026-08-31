from __future__ import annotations

import copy
from typing import Any, Mapping


PREPARATION_REFRESH_STEP = "repository-reconciliation-preparation-refresh"
PREPARATION_REFRESH_HISTORY_STEP = "reconcile-preparation-refresh-history"


class ReconciliationIntentError(ValueError):
    pass


def _intent(value: object, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ReconciliationIntentError(f"{field} must be an object")
    target = value.get("target_base")
    if not isinstance(target, dict) or set(target) != {
        "branch",
        "ref",
        "sha",
        "tree_oid",
    }:
        raise ReconciliationIntentError(
            f"{field} target must contain exact branch, ref, SHA, and tree"
        )
    if not all(isinstance(item, str) and item for item in target.values()):
        raise ReconciliationIntentError(f"{field} target values are invalid")
    return value


def _validate_target_only(
    previous: Mapping[str, Any], replacement: Mapping[str, Any]
) -> None:
    if set(previous) != set(replacement):
        raise ReconciliationIntentError(
            "reconciliation refresh changed non-target fields"
        )
    previous_without_target = {
        key: value for key, value in previous.items() if key != "target_base"
    }
    replacement_without_target = {
        key: value for key, value in replacement.items() if key != "target_base"
    }
    if previous_without_target != replacement_without_target:
        raise ReconciliationIntentError(
            "reconciliation refresh changed non-target fields"
        )
    previous_target = _intent(dict(previous), "previous intent")["target_base"]
    replacement_target = _intent(
        dict(replacement), "replacement intent"
    )["target_base"]
    if (
        previous_target["branch"] != replacement_target["branch"]
        or previous_target["ref"] != replacement_target["ref"]
    ):
        raise ReconciliationIntentError(
            "reconciliation refresh changed target identity"
        )
    if (
        previous_target["sha"],
        previous_target["tree_oid"],
    ) == (
        replacement_target["sha"],
        replacement_target["tree_oid"],
    ):
        raise ReconciliationIntentError(
            "reconciliation refresh did not change the target"
        )


def validate_preparation_refresh(
    refresh: object,
    canonical_intent: Mapping[str, Any],
) -> dict[str, Any]:
    canonical = _intent(dict(canonical_intent), "canonical intent")
    if not isinstance(refresh, dict) or set(refresh) != {
        "schema",
        "original_intent",
        "history",
        "previous_intent",
        "replacement_intent",
    } or refresh.get("schema") != 1:
        raise ReconciliationIntentError(
            "preparation reconciliation refresh is malformed"
        )
    if refresh["original_intent"] != canonical:
        raise ReconciliationIntentError(
            "preparation reconciliation refresh changed its original intent"
        )
    history = refresh["history"]
    if not isinstance(history, list):
        raise ReconciliationIntentError(
            "preparation reconciliation refresh history is malformed"
        )
    effective = canonical
    for item in history:
        if not isinstance(item, dict) or set(item) != {
            "schema",
            "previous_intent",
            "replacement_intent",
        } or item.get("schema") != 1:
            raise ReconciliationIntentError(
                "preparation reconciliation refresh history is malformed"
            )
        if item["previous_intent"] != effective:
            raise ReconciliationIntentError(
                "preparation reconciliation refresh history is not contiguous"
            )
        replacement = _intent(
            item["replacement_intent"], "historical replacement intent"
        )
        _validate_target_only(effective, replacement)
        effective = replacement
    if refresh["previous_intent"] != effective:
        raise ReconciliationIntentError(
            "preparation reconciliation refresh predecessor is stale"
        )
    replacement = _intent(
        refresh["replacement_intent"], "pending replacement intent"
    )
    _validate_target_only(effective, replacement)
    return copy.deepcopy(replacement)


def build_preparation_refresh(
    canonical_intent: Mapping[str, Any],
    current_refresh: object | None,
    replacement_intent: Mapping[str, Any],
) -> dict[str, Any] | None:
    canonical = _intent(dict(canonical_intent), "canonical intent")
    replacement = _intent(dict(replacement_intent), "replacement intent")
    if current_refresh is None:
        if replacement == canonical:
            return None
        _validate_target_only(canonical, replacement)
        return {
            "schema": 1,
            "original_intent": copy.deepcopy(canonical),
            "history": [],
            "previous_intent": copy.deepcopy(canonical),
            "replacement_intent": copy.deepcopy(replacement),
        }
    effective = validate_preparation_refresh(current_refresh, canonical)
    if replacement == effective:
        return copy.deepcopy(current_refresh)
    _validate_target_only(effective, replacement)
    history = copy.deepcopy(current_refresh["history"])
    history.append(
        {
            "schema": 1,
            "previous_intent": copy.deepcopy(
                current_refresh["previous_intent"]
            ),
            "replacement_intent": copy.deepcopy(effective),
        }
    )
    return {
        "schema": 1,
        "original_intent": copy.deepcopy(canonical),
        "history": history,
        "previous_intent": copy.deepcopy(effective),
        "replacement_intent": copy.deepcopy(replacement),
    }
