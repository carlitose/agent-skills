"""Coordinate candidate quality and tracked completion without owning delivery.

The CLI retains event parsing, administrative preflight and ordinary event persistence.
This boundary owns projection recovery, stage advancement and delivery revalidation;
Kernel and the existing finalizer/transaction owners still enforce their contracts.
"""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable, Mapping

from .docs_only import DocsOnlyError, revalidate_docs_only_receipt
from .final_tree_transaction import TRANSACTION_STEP
from .finalizer import CompletionProjectionError, DeliveryFinalizer
from .git_ops import CommandRunner, candidate_ref
from .kernel import CandidateRef, Kernel, TransitionError
from .ledger import AtomicLedger
from .providers import ProviderExecutor, detect_provider


def current_candidate(worktree: Path, ticket: Mapping[str, Any]) -> CandidateRef:
    stored = ticket.get("candidate_ref")
    base_ref = (
        stored["base_tree_oid"]
        if isinstance(stored, Mapping)
        and isinstance(stored.get("base_tree_oid"), str)
        else "HEAD"
    )
    return candidate_ref(worktree, str(ticket["ticket_digest"]), base_ref=base_ref)


def reset_stale_preparation(
    kernel: Kernel, ticket_id: str, candidate: CandidateRef
) -> bool:
    if kernel.ledger["tickets"][ticket_id].get("pr") is not None:
        return False
    return kernel.reset_stale_delivery_preparation(ticket_id, candidate)


class FinalTreeWorkflow:
    def __init__(
        self,
        store: AtomicLedger,
        kernel: Kernel,
        worktree: Path,
        *,
        runner: CommandRunner | None,
        boundary_guard: Callable[[str, str], None],
    ) -> None:
        self.store = store
        self.kernel = kernel
        self.worktree = worktree
        self.runner = runner
        self.boundary_guard = boundary_guard

    def _project(self, ticket_id: str) -> dict[str, Any] | None:
        provider = detect_provider("", override=self.kernel.ledger["provider"])
        executor = ProviderExecutor(
            provider,
            cwd=self.worktree,
            mode=self.kernel.ledger.get("provider_mode", "live"),
            runner=self.runner,
        )
        return DeliveryFinalizer(
            self.store,
            self.kernel,
            executor,
            boundary_guard=self.boundary_guard,
        ).project_before_final_quality(ticket_id)

    def recover(
        self, ticket_id: str, operation: str
    ) -> tuple[dict[str, object] | None, bool]:
        """Resume a persisted projection before quality; return outcome and stop flag."""
        ticket = self.kernel.ledger["tickets"][ticket_id]
        transaction = ticket.get("delivery", {}).get(TRANSACTION_STEP)
        recovery_required = isinstance(transaction, dict) and (
            transaction.get("status") != "projected-not-integrated"
            or ticket.get("candidate_ref")
            != transaction.get("planned_delivery_candidate_ref")
            or ticket.get("completion_effect", {}).get("state") != "applied"
        )
        if not (
            operation != "activate"
            and ticket["state"] == "active"
            and ticket["stage"] == "review"
            and ticket["validated_stages"] == ["implement", "simplify"]
            and recovery_required
        ):
            return None, False
        try:
            projected = self._project(ticket_id)
        except CompletionProjectionError as error:
            self.store.save(self.kernel.ledger)
            return {
                "operation": "final-tree-projection-recovery",
                "ticket_id": ticket_id,
                "result": "blocked",
                "reason": str(error),
            }, True
        if projected is None:
            return None, False
        return {
            "operation": "final-tree-projection-recovery",
            "ticket_id": ticket_id,
            "result": "resumed",
            "tree_oid": projected["candidate_tree_oid"],
        }, False

    def record_stage(
        self, event: Mapping[str, Any]
    ) -> tuple[dict[str, object], bool]:
        """Advance one stage; projection failure stops the caller's remaining batch."""
        ticket_id = event["ticket_id"]
        ticket = self.kernel.ledger["tickets"][ticket_id]
        stage = event.get("stage")
        result = event.get("result")
        expected_tree = event.get("expected_tree_oid")
        if not all(isinstance(value, str) for value in (stage, result, expected_tree)):
            raise TransitionError(
                "stage event requires stage, result, and expected_tree_oid"
            )
        fixed = current_candidate(self.worktree, ticket)
        if fixed.candidate_tree_oid != expected_tree:
            raise TransitionError(
                "stage event expected_tree_oid differs from current Git tree"
            )
        if ticket["candidate_ref"] != asdict(fixed):
            reset_stale_preparation(self.kernel, ticket_id, fixed)
            if ticket["stage"] == "implement" and stage == "implement":
                self.kernel.adopt_implementation_candidate(ticket_id, fixed)
            else:
                self.kernel.invalidate_for_candidate_drift(ticket_id, fixed)
                self.store.save(self.kernel.ledger)
                return {
                    "operation": event["operation"],
                    "ticket_id": ticket_id,
                    "result": "invalidated",
                    "tree_oid": fixed.candidate_tree_oid,
                }, True
        self.kernel.record_stage(
            ticket_id, stage, result, fixed, reason=event.get("reason")
        )
        outcome: dict[str, object] = {
            "operation": event["operation"],
            "ticket_id": ticket_id,
            "stage": stage,
            "result": result,
            "tree_oid": fixed.candidate_tree_oid,
        }
        if stage == "simplify" and result == "pass":
            try:
                projected = self._project(ticket_id)
            except CompletionProjectionError as error:
                outcome["projection"] = "recovery-required"
                outcome["reason"] = str(error)
                self.store.save(self.kernel.ledger)
                return outcome, True
            if projected is not None:
                outcome["projection"] = "projected-not-integrated"
                outcome["projected_tree_oid"] = projected["candidate_tree_oid"]
        if stage == "finalize" and result == "pass":
            if self.kernel.record_final_tree_projection_quality_complete(ticket_id):
                self.store.save(self.kernel.ledger)
                outcome["projection_quality"] = "quality-complete"
        return outcome, False

    def revalidate_delivery(self, ticket_id: str) -> dict[str, object]:
        """Re-enter quality on semantic drift without republishing or rolling back D.

        Unlike ordinary stage events this operation owns its persistence: an already
        active ticket and an unchanged docs-only receipt retain the old no-save path.
        """
        ticket = self.kernel.ledger["tickets"][ticket_id]
        outcome: dict[str, object] = {
            "operation": "delivery-revalidate",
            "ticket_id": ticket_id,
        }
        if ticket["state"] == "active":
            return {
                **outcome,
                "result": "revalidation-required",
                "tree_oid": ticket["candidate_ref"]["candidate_tree_oid"],
            }
        if ticket["state"] != "verified":
            raise TransitionError("delivery revalidation requires verified ticket state")
        docs_only = ticket.get("docs_only")
        if isinstance(docs_only, dict) and docs_only.get("status") == "eligible":
            try:
                validation = revalidate_docs_only_receipt(
                    self.worktree,
                    ticket,
                    docs_only,
                    evidence_dir=self.store.path.parent / "evidence",
                )
            except DocsOnlyError as error:
                raise TransitionError(str(error)) from error
            return {
                **outcome,
                "result": "unchanged",
                "tree_oid": validation.candidate.candidate_tree_oid,
            }
        fixed = current_candidate(self.worktree, ticket)
        if ticket["candidate_ref"] == asdict(fixed):
            outcome["result"] = "unchanged"
        else:
            reset_stale_preparation(self.kernel, ticket_id, fixed)
            self.kernel.prepare_delivery_revalidation(ticket_id, fixed)
            outcome["result"] = "revalidation-required"
        outcome["tree_oid"] = fixed.candidate_tree_oid
        self.store.save(self.kernel.ledger)
        return outcome
