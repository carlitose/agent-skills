from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any


DELTA_SCHEMA = 1


class HistoryCodecError(ValueError):
    """A compact history cannot be decoded without ambiguity."""


def diff_snapshots(
    before: Mapping[str, Any], after: Mapping[str, Any]
) -> dict[str, Any]:
    """Return the one canonical structural delta from ``before`` to ``after``."""
    if not isinstance(before, Mapping) or not isinstance(after, Mapping):
        raise HistoryCodecError("history snapshots must be objects")
    operations: list[dict[str, Any]] = []
    _diff_values(dict(before), dict(after), [], operations)
    return {"schema": DELTA_SCHEMA, "operations": operations}


def _diff_values(
    before: Any,
    after: Any,
    path: list[str],
    operations: list[dict[str, Any]],
) -> None:
    if before == after:
        return
    if isinstance(before, dict) and isinstance(after, dict):
        if not all(isinstance(key, str) for key in (*before.keys(), *after.keys())):
            raise HistoryCodecError("history snapshot keys must be strings")
        before_keys = set(before)
        after_keys = set(after)
        for key in sorted(before_keys - after_keys):
            operations.append({"op": "remove", "path": [*path, key]})
        for key in sorted(before_keys & after_keys):
            _diff_values(before[key], after[key], [*path, key], operations)
        for key in sorted(after_keys - before_keys):
            operations.append(
                {
                    "op": "set",
                    "path": [*path, key],
                    "value": copy.deepcopy(after[key]),
                }
            )
        return
    if (
        isinstance(before, list)
        and isinstance(after, list)
        and len(after) > len(before)
        and after[: len(before)] == before
    ):
        operations.append(
            {
                "op": "append",
                "path": list(path),
                "values": copy.deepcopy(after[len(before) :]),
            }
        )
        return
    if not path:
        raise HistoryCodecError("history snapshot root must remain an object")
    operations.append(
        {"op": "set", "path": list(path), "value": copy.deepcopy(after)}
    )


def apply_snapshot_delta(
    before: Mapping[str, Any], delta: Mapping[str, Any]
) -> dict[str, Any]:
    """Apply a delta only when it is well-formed and canonically encoded."""
    if not isinstance(before, Mapping):
        raise HistoryCodecError("history snapshot must be an object")
    if not isinstance(delta, Mapping) or set(delta) != {"schema", "operations"}:
        raise HistoryCodecError("snapshot delta shape is invalid")
    if type(delta.get("schema")) is not int or delta["schema"] != DELTA_SCHEMA:
        raise HistoryCodecError("snapshot delta schema is invalid")
    operations = delta.get("operations")
    if not isinstance(operations, list):
        raise HistoryCodecError("snapshot delta operations must be a list")

    result = copy.deepcopy(dict(before))
    for operation in operations:
        _apply_operation(result, operation)

    canonical = diff_snapshots(before, result)
    if canonical != delta:
        raise HistoryCodecError("snapshot delta is not canonical")
    return result


def _apply_operation(document: dict[str, Any], operation: Any) -> None:
    if not isinstance(operation, Mapping):
        raise HistoryCodecError("snapshot delta operation must be an object")
    kind = operation.get("op")
    expected = {
        "set": {"op", "path", "value"},
        "remove": {"op", "path"},
        "append": {"op", "path", "values"},
    }.get(kind)
    if expected is None or set(operation) != expected:
        raise HistoryCodecError("snapshot delta operation shape is invalid")
    path = operation.get("path")
    if (
        not isinstance(path, list)
        or not path
        or not all(isinstance(component, str) for component in path)
    ):
        raise HistoryCodecError("snapshot delta path is invalid")

    parent: dict[str, Any] = document
    for component in path[:-1]:
        child = parent.get(component)
        if not isinstance(child, dict):
            raise HistoryCodecError("snapshot delta path does not resolve")
        parent = child
    leaf = path[-1]
    if kind == "set":
        parent[leaf] = copy.deepcopy(operation["value"])
        return
    if leaf not in parent:
        raise HistoryCodecError("snapshot delta path does not resolve")
    if kind == "remove":
        del parent[leaf]
        return
    target = parent[leaf]
    values = operation["values"]
    if not isinstance(target, list) or not isinstance(values, list) or not values:
        raise HistoryCodecError("snapshot delta append is invalid")
    target.extend(copy.deepcopy(values))


def decode_history_event(
    event: Mapping[str, Any], previous_snapshot: Mapping[str, Any] | None
) -> dict[str, Any]:
    has_snapshot = "snapshot" in event
    has_delta = "snapshot_delta" in event
    if has_snapshot == has_delta:
        raise HistoryCodecError(
            "history event must contain exactly one snapshot representation"
        )
    if has_snapshot:
        snapshot = event["snapshot"]
        if not isinstance(snapshot, dict) or "history" in snapshot:
            raise HistoryCodecError("history event snapshot is malformed")
        return copy.deepcopy(snapshot)
    if previous_snapshot is None:
        raise HistoryCodecError("compact history must start with a full checkpoint")
    return apply_snapshot_delta(previous_snapshot, event["snapshot_delta"])


def virtual_history_event(
    event: Mapping[str, Any], snapshot: Mapping[str, Any]
) -> dict[str, Any]:
    virtual = copy.deepcopy(dict(event))
    virtual.pop("snapshot_delta", None)
    virtual["snapshot"] = copy.deepcopy(dict(snapshot))
    return virtual


def history_event_hash(
    event: Mapping[str, Any], snapshot: Mapping[str, Any]
) -> str:
    """Hash the original full-snapshot event represented by stored history."""
    unhashed = virtual_history_event(event, snapshot)
    unhashed.pop("hash", None)
    encoded = json.dumps(
        unhashed,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def decode_history(history: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    decoded: list[dict[str, Any]] = []
    previous_snapshot: dict[str, Any] | None = None
    compact_started = False
    for event in history:
        if "snapshot_delta" in event:
            compact_started = True
        elif compact_started:
            raise HistoryCodecError(
                "full history event cannot appear after compact history"
            )
        snapshot = decode_history_event(event, previous_snapshot)
        decoded.append(virtual_history_event(event, snapshot))
        previous_snapshot = snapshot
    return decoded


def compact_event_history(
    history: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Replace every full snapshot after the first with its canonical delta."""
    compact: list[dict[str, Any]] = []
    previous_snapshot: dict[str, Any] | None = None
    compact_started = False
    for index, event in enumerate(history):
        if "snapshot_delta" in event:
            compact_started = True
            snapshot = decode_history_event(event, previous_snapshot)
            compact.append(copy.deepcopy(dict(event)))
        elif compact_started:
            raise HistoryCodecError(
                "full history event cannot appear after compact history"
            )
        else:
            snapshot = decode_history_event(event, previous_snapshot)
            if index == 0:
                compact.append(copy.deepcopy(dict(event)))
            else:
                encoded = copy.deepcopy(dict(event))
                encoded.pop("snapshot", None)
                encoded["snapshot_delta"] = diff_snapshots(
                    previous_snapshot or {}, snapshot
                )
                compact.append(encoded)
        previous_snapshot = snapshot
    return compact
