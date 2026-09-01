"""Read-only repository lifecycle barrier lookup for runner mutation seams.

The status transaction owns the journal.  This module deliberately knows only enough of
that append-only contract to reject malformed state and expose one exact active barrier;
it grants no disposition, provider, merge, completion, wiki, or Pi authority.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Mapping


ZERO_HASH = "0" * 64
TERMINAL_EVENTS = frozenset({"external-unpublished", "tracked-complete"})
HEX_DIGEST = re.compile(r"[0-9a-f]{64}")
KNOWN_EVENTS = frozenset(
    {
        "transaction-intent",
        "transaction-gated",
        "tracked-handoff-ready",
        "safe-boundary-armed",
        "target-refreshed",
        "source-applied",
        "candidate-frozen",
        "commit-intent",
        "committed",
        "push-intent",
        "push-armed",
        "pushed",
        "provider-intent",
        "provider-armed",
        "pr-read-back",
        "merge-gated",
        "merge-intent",
        "merge-armed",
        "provider-merged",
        "terminal-proved",
        "projected",
        "tracked-complete",
        "external-unpublished",
    }
)


class StatusBarrierError(RuntimeError):
    """Repository lifecycle barrier state is malformed or forbids a mutation."""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _event_hash(event: Mapping[str, Any]) -> str:
    return _digest({key: value for key, value in event.items() if key != "event_hash"})


def _lexical_root(repository: Path) -> tuple[Path, Path]:
    lexical = Path(os.path.abspath(repository))
    current = Path(lexical.anchor)
    for part in lexical.parts[1:]:
        current = current / part
        if current.exists() and current.is_symlink():
            raise StatusBarrierError("repository lifecycle barrier rejects repository aliases")
    supplied = lexical.resolve()
    root_result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=supplied,
        text=True,
        capture_output=True,
        check=False,
    )
    common_result = subprocess.run(
        ["git", "rev-parse", "--git-common-dir"],
        cwd=supplied,
        text=True,
        capture_output=True,
        check=False,
    )
    if root_result.returncode or common_result.returncode:
        raise StatusBarrierError("repository lifecycle barrier binding is unavailable")
    root = Path(root_result.stdout.strip()).resolve()
    common_value = Path(common_result.stdout.strip())
    common = (
        common_value.resolve()
        if common_value.is_absolute()
        else (supplied / common_value).resolve()
    )
    if root != supplied:
        raise StatusBarrierError("repository lifecycle barrier requires the canonical root")
    return root, common


def _load_journal(path: Path, *, root: Path, common: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise StatusBarrierError("repository lifecycle journal is unsafe")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise StatusBarrierError("repository lifecycle journal is unreadable") from error
    if (
        not isinstance(value, dict)
        or set(value) != {"schema", "transaction_id", "request", "history"}
        or value.get("schema") != 1
        or not isinstance(value.get("request"), dict)
        or not isinstance(value.get("history"), list)
        or not value["history"]
        or value.get("transaction_id") != _digest(value["request"])
        or path.name != f"{value.get('transaction_id')}.json"
    ):
        raise StatusBarrierError("repository lifecycle journal identity is invalid")
    request = value["request"]
    if (
        request.get("repository_identity") != str(root)
        or request.get("git_common_dir") != str(common)
        or request.get("schema") != 1
    ):
        raise StatusBarrierError("repository lifecycle journal repository binding drifted")
    previous = ZERO_HASH
    safe_events: list[dict[str, Any]] = []
    for sequence, raw in enumerate(value["history"], 1):
        if (
            not isinstance(raw, dict)
            or set(raw)
            != {
                "schema",
                "sequence",
                "event",
                "details",
                "previous_event_hash",
                "event_hash",
            }
            or raw.get("schema") != 1
            or raw.get("sequence") != sequence
            or raw.get("event") not in KNOWN_EVENTS
            or not isinstance(raw.get("details"), dict)
            or raw.get("previous_event_hash") != previous
            or raw.get("event_hash") != _event_hash(raw)
        ):
            raise StatusBarrierError("repository lifecycle journal hash lineage is invalid")
        previous = raw["event_hash"]
        if raw["event"] == "safe-boundary-armed":
            safe_events.append(raw)
    if len(safe_events) > 1:
        raise StatusBarrierError("repository lifecycle journal has multiple safe boundaries")
    return value


def _reject_symlink_chain(base: Path, target: Path) -> None:
    try:
        relative = target.relative_to(base)
    except ValueError as error:
        raise StatusBarrierError(
            "repository lifecycle transaction store escapes Git state"
        ) from error
    current = base
    for part in relative.parts:
        current = current / part
        if current.exists() and current.is_symlink():
            raise StatusBarrierError(
                "repository lifecycle transaction store contains a symlink"
            )


def active_status_barrier(
    repository: Path,
    *,
    run_id: str,
    ticket_id: str,
) -> dict[str, Any] | None:
    """Return one exact active barrier for a run ticket, or fail closed on drift."""

    if (
        not isinstance(run_id, str)
        or not run_id
        or not isinstance(ticket_id, str)
        or not ticket_id
    ):
        raise StatusBarrierError("repository lifecycle barrier identity is incomplete")
    root, common = _lexical_root(repository)
    transaction_root = common / "ticket-autopilot" / "status-transactions"
    _reject_symlink_chain(common, transaction_root)
    if not transaction_root.exists():
        return None
    if transaction_root.is_symlink() or not transaction_root.is_dir():
        raise StatusBarrierError("repository lifecycle transaction store is unsafe")
    matches: list[dict[str, Any]] = []
    for path in sorted(transaction_root.glob("*.json"), key=lambda item: item.name):
        document = _load_journal(path, root=root, common=common)
        request = document["request"]
        if request.get("projection_run_id") != run_id or request.get("ticket_id") != ticket_id:
            continue
        safe = next(
            (
                event
                for event in document["history"]
                if event["event"] == "safe-boundary-armed"
            ),
            None,
        )
        if safe is None or document["history"][-1]["event"] in TERMINAL_EVENTS:
            continue
        details = safe["details"]
        if (
            set(details)
            != {
                "projection_run_id",
                "ticket_state",
                "execution_lifecycle",
                "readiness",
                "stop_reason",
                "atomic_effect_settled",
                "run_barrier_receipt_digest",
            }
            or details.get("projection_run_id") != run_id
            or details.get("atomic_effect_settled") is not True
            or not isinstance(details.get("ticket_state"), str)
            or not isinstance(details.get("execution_lifecycle"), str)
            or not isinstance(details.get("readiness"), str)
            or (
                details.get("stop_reason") is not None
                and not isinstance(details.get("stop_reason"), str)
            )
            or not isinstance(details.get("run_barrier_receipt_digest"), str)
            or HEX_DIGEST.fullmatch(details["run_barrier_receipt_digest"])
            is None
        ):
            raise StatusBarrierError("repository lifecycle safe-boundary receipt is invalid")
        matches.append(
            {
                "schema": 1,
                "transaction_id": document["transaction_id"],
                "ticket_id": ticket_id,
                "run_id": run_id,
                "to_disposition": request.get("to_disposition"),
                "actor": request.get("actor"),
                "reason": request.get("reason"),
                "authority_ref": request.get("authority_ref"),
                "phase": document["history"][-1]["event"],
                "safe_boundary": details,
            }
        )
    if len(matches) > 1:
        raise StatusBarrierError("multiple repository lifecycle barriers target one run ticket")
    return matches[0] if matches else None
