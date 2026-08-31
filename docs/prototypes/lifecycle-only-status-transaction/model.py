"""Disposable logic model for a lifecycle-only status transaction.

Question: can one repository-owned transaction isolate an administrative ticket move from
an active run's candidate and still recover every Git/provider boundary exactly?

This is prototype code.  It deliberately does not implement a production command.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Iterable


DISPOSITIONS = {"open", "on-hold", "canceled"}
EXECUTION_STATES = {"pending", "active", "gated", "waiting"}


class PrototypeError(RuntimeError):
    """The model cannot prove that the next lifecycle-only step is safe."""


class SimulatedCrash(RuntimeError):
    """A durable boundary was written and the process then stopped."""


@dataclass(frozen=True)
class OwnerRecord:
    run_id: str
    status: str  # usable or retired
    ticket_digest: str


@dataclass(frozen=True)
class OwnerResolution:
    transaction_owner: str
    projection_run_id: str | None
    historical_run_ids: tuple[str, ...]


def resolve_owner(ticket_digest: str, records: Iterable[OwnerRecord]) -> OwnerResolution:
    """Resolve an optional run projection without making a run own the transaction."""

    matching = [record for record in records if record.ticket_digest == ticket_digest]
    usable = [record for record in matching if record.status == "usable"]
    retired = sorted(record.run_id for record in matching if record.status == "retired")
    if len(usable) > 1:
        raise PrototypeError("ambiguous usable run ownership")
    if any(record.status not in {"usable", "retired"} for record in matching):
        raise PrototypeError("unknown run ownership status")
    return OwnerResolution(
        transaction_owner="repository-lifecycle",
        projection_run_id=usable[0].run_id if usable else None,
        historical_run_ids=tuple(retired),
    )


@dataclass(frozen=True)
class BoundaryDecision:
    action: str
    preserves_attempt: bool


def status_boundary(execution_state: str, *, atomic_effect_in_flight: bool) -> BoundaryDecision:
    """Model the accepted decision's safe boundary, separate from current kernel support."""

    if execution_state not in EXECUTION_STATES:
        raise PrototypeError("unsupported execution state")
    if atomic_effect_in_flight:
        raise PrototypeError("atomic effect must settle before disposition mutation")
    if execution_state == "active":
        return BoundaryDecision("stop-active-at-safe-boundary", True)
    if execution_state in {"gated", "waiting"}:
        return BoundaryDecision("preserve-settled-attempt-and-apply", True)
    return BoundaryDecision("apply-inactive", False)


def validate_request(
    *,
    ticket_id: str,
    target_disposition: str,
    actor: str,
    reason: str,
    authority_ref: str,
    reopen_gate_id: str | None,
) -> None:
    values = (ticket_id, actor, reason, authority_ref)
    if target_disposition not in DISPOSITIONS:
        raise PrototypeError("administrative disposition is invalid")
    if any(not isinstance(value, str) or not value.strip() for value in values):
        raise PrototypeError("ticket identity, actor, reason, and authority are required")
    if target_disposition == "open" and not reopen_gate_id:
        raise PrototypeError("reopen requires an exact passed human gate")
    if target_disposition != "open" and reopen_gate_id is not None:
        raise PrototypeError("hold and cancel cannot consume a reopen gate")


def expected_tracked_paths(
    *,
    ticket_root: str,
    source_relative_path: str,
    destination_relative_path: str,
    inbound_repoints: Iterable[str],
) -> frozenset[str]:
    prefix = ticket_root.rstrip("/")
    paths = {
        f"{prefix}/{source_relative_path}",
        f"{prefix}/{destination_relative_path}",
        *inbound_repoints,
    }
    return frozenset(paths)


def freeze_candidate(
    *,
    source_mode: str,
    observed_paths: Iterable[str],
    allowed_paths: Iterable[str],
) -> str | None:
    """Freeze only an admin-worktree diff; target-run dirt is not an input."""

    observed = frozenset(observed_paths)
    allowed = frozenset(allowed_paths)
    if source_mode == "ignored":
        if observed:
            raise PrototypeError("ignored source cannot create a tracked candidate")
        return None
    if source_mode != "tracked":
        raise PrototypeError("source mode is invalid")
    if observed != allowed:
        raise PrototypeError("administrative candidate differs from exact allowlist")
    raw = json.dumps(sorted(observed), separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


TRACKED_ORDER = (
    "request-validated",
    "lifecycle-intent",
    "source-applied",
    "candidate-frozen",
    "commit-intent",
    "committed",
    "provider-intent",
    "provider-dispatch-started",
    "pr-read-back",
    "merge-decision-recorded",
    "provider-merged",
    "terminal-proved",
    "projection-recorded",
    "complete",
)
IGNORED_ORDER = (
    "request-validated",
    "lifecycle-intent",
    "source-applied",
    "projection-recorded",
    "complete",
)


@dataclass
class FakeProvider:
    pr_state: str = "absent"  # absent, open, merged
    dispatch_calls: int = 0
    merge_calls: int = 0


@dataclass
class Transaction:
    source_mode: str
    owner: OwnerResolution
    durable_steps: list[str] = field(default_factory=list)
    source_effects: int = 0
    commit_effects: int = 0
    projection_effects: int = 0
    run_projection_effects: int = 0
    stop_reason: str | None = None

    def has(self, step: str) -> bool:
        return step in self.durable_steps

    def record(self, step: str, *, crash_after: str | None) -> bool:
        """Append one ordered durable fact and report whether it was new."""

        if self.has(step):
            return False
        order = IGNORED_ORDER if self.source_mode == "ignored" else TRACKED_ORDER
        expected = order[len(self.durable_steps)]
        if step != expected:
            raise PrototypeError(f"out-of-order step: expected {expected}, got {step}")
        self.durable_steps.append(step)
        if crash_after == step:
            raise SimulatedCrash(step)
        return True


def _project(
    transaction: Transaction,
    *,
    crash_after: str | None,
    outcome: str = "complete",
) -> str:
    if transaction.record("projection-recorded", crash_after=crash_after):
        transaction.projection_effects += 1
        if transaction.owner.projection_run_id is not None:
            transaction.run_projection_effects += 1
    transaction.record("complete", crash_after=crash_after)
    transaction.stop_reason = None
    return outcome


def advance(
    transaction: Transaction,
    provider: FakeProvider,
    *,
    candidate_paths_exact: bool = True,
    merge_authorized: bool = False,
    terminal_reachable: bool = False,
    crash_after: str | None = None,
) -> str:
    """Advance or replay one transaction without redispatching ambiguous effects."""

    transaction.record("request-validated", crash_after=crash_after)
    transaction.record("lifecycle-intent", crash_after=crash_after)
    if not transaction.has("source-applied"):
        transaction.source_effects += 1
        transaction.record("source-applied", crash_after=crash_after)

    if transaction.source_mode == "ignored":
        # No Git, provider, merge, tracked projection, wiki, or publication follows.
        return _project(
            transaction,
            crash_after=crash_after,
            outcome="external-unpublished",
        )

    if transaction.source_mode != "tracked":
        raise PrototypeError("source mode is invalid")
    if not candidate_paths_exact:
        raise PrototypeError("administrative candidate differs from exact allowlist")
    transaction.record("candidate-frozen", crash_after=crash_after)
    transaction.record("commit-intent", crash_after=crash_after)
    if not transaction.has("committed"):
        transaction.commit_effects += 1
        transaction.record("committed", crash_after=crash_after)
    transaction.record("provider-intent", crash_after=crash_after)

    if not transaction.has("provider-dispatch-started"):
        transaction.record("provider-dispatch-started", crash_after=None)
        provider.dispatch_calls += 1
        if provider.pr_state == "absent":
            transaction.stop_reason = "provider-outcome-ambiguous"
            if crash_after == "provider-dispatch-started":
                raise SimulatedCrash("provider-dispatch-started")
            return transaction.stop_reason
    if crash_after == "provider-dispatch-started" and provider.dispatch_calls:
        raise SimulatedCrash("provider-dispatch-started")
    if provider.pr_state == "absent":
        transaction.stop_reason = "provider-outcome-ambiguous"
        return transaction.stop_reason
    transaction.record("pr-read-back", crash_after=crash_after)

    if provider.pr_state == "open":
        if not merge_authorized:
            transaction.stop_reason = "merge-authority-required"
            return transaction.stop_reason
        if not transaction.has("merge-decision-recorded"):
            transaction.record("merge-decision-recorded", crash_after=None)
            provider.merge_calls += 1
            provider.pr_state = "merged"
            if crash_after == "merge-decision-recorded":
                raise SimulatedCrash("merge-decision-recorded")
    else:
        # An externally merged PR grants no mutation authority, but no mutation remains.
        transaction.record("merge-decision-recorded", crash_after=crash_after)
    if provider.pr_state != "merged":
        transaction.stop_reason = "provider-merge-outcome-ambiguous"
        return transaction.stop_reason
    transaction.record("provider-merged", crash_after=crash_after)
    if not terminal_reachable:
        transaction.stop_reason = "terminal-proof-required"
        return transaction.stop_reason
    transaction.record("terminal-proved", crash_after=crash_after)
    return _project(transaction, crash_after=crash_after)
