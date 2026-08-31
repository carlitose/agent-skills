---
ticket_schema: 1
ticket_id: "TCR-01"
execution_mode: AFK
blocked_by: []
---

# Bind conflict proposals to the completion-projected delivery candidate

## Artifact Graph

- Artifact ID: `artifact:tcr-01-bind-conflict-proposals-to-delivery-candidate`
- Role: `ticket`
- Parent: [Ticket Autopilot Tracked Completion Reconciliation Candidate Binding](../../specs/ticket-autopilot-tracked-completion-reconciliation-candidate-binding.md)

## Parent Spec

[Ticket Autopilot Tracked Completion Reconciliation Candidate Binding](../../specs/ticket-autopilot-tracked-completion-reconciliation-candidate-binding.md)

## What to Build

Correct repository autonomous reconciliation so an exact tracked-source conflict proposal
binds the completion-projected `delivery_candidate_ref` that identifies the branch tree
being rebased, while preserving semantic `candidate_ref` fallback when no delivery
candidate exists. Keep all proposal, authority, gate, revalidation, provider, and merge
invariants from the parent spec.

## Acceptance Criteria

- [ ] Proposal context selects `delivery_candidate_ref` when present and otherwise preserves
      existing semantic CandidateRef behavior.
- [ ] A tracked completion-projected conflict proposal can bind the actual old local tree and
      pass exact grant/context validation.
- [ ] Semantic-candidate substitution, wrong delivery tree, malformed or stale candidate,
      wrong grant, target/head drift, extra conflict paths, and changed resolution blobs fail
      before proposal application.
- [ ] Proposal application records exact adoption/application receipts, consumes only covered
      reconciliation gates, and requires fresh CandidateRef quality evidence before push or
      merge.
- [ ] The provider-free two-sided contradiction fixture is causal: it fails on the baseline
      and passes only through the delivery-candidate correction.
- [ ] Full runner, extension, forward, static, context, and Artifact Graph delta checks pass
      without transferring completion, merge, publication, wiki, Pi, source, or cleanup
      authority.

## Frontier

Ready. The existing repository autonomous reconciliation grant supplies exact bounded
proposal authority, but no manual conflict resolution or gate bypass is permitted.

## Step-by-Step Implementation Plan

1. Add a narrow CandidateRef selector at proposal-context construction, preferring the
   recorded delivery candidate and retaining semantic fallback.
2. Add provider-free unit coverage for both sides of the current unsatisfiable predicate and
   every stale/malformed candidate boundary.
3. Add a disposable tracked-source finalization/rebase-conflict scenario that creates a real
   completion projection and applies an exact delivery-bound proposal.
4. Prove post-application candidate invalidation and fresh revalidation precede any simulated
   provider publication.
5. Run focused and full regressions, forward scenarios, static/context checks, and Artifact
   Graph baseline/candidate comparison.

## Testing Plan

Use direct proposal validation for the minimal red/green loop and real disposable Git
worktrees for tracked completion projection, target advancement, conflict observation,
proposal application, replay, revocation, and drift. Provider mutation remains simulated;
no live provider operation is needed.

## Out of Scope

- Manual resolution outside the exact proposal transaction.
- Changes to completion projection content or authority.
- Live provider mutation or RD-04 merge itself.
- Runner-defect issue publication or RD-05 authorization.
