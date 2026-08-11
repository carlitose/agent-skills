---
ticket_schema: 1
ticket_id: "IS-01"
execution_mode: AFK
blocked_by: []
---

# Gate ignored-to-tracked source promotion

## Artifact Graph

- Artifact ID: `artifact:is-01-gate-ignored-to-tracked-source-promotion`
- Role: `ticket`
- Parent: [Ticket Autopilot Ignored Ticket Sources](../../specs/ticket-autopilot-ignored-ticket-sources.md)

## Parent Spec

[Ticket Autopilot Ignored Ticket Sources](../../specs/ticket-autopilot-ignored-ticket-sources.md)

## Type

Bug fix

## What to Build

Close the source-ownership hole exposed by run `7974966ec8d84a35`. The run snapshotted its
ticket folder as `ignored`, then TK-01 published those paths as tracked files. TK-02 and
TK-03 inherited the frozen folder-wide ignored mode, so finalization stayed external while
PRs #59, #60, and #61 left all three tracked tickets at their open paths.

Add a fail-closed source-mode drift boundary that prevents an ignored snapshot from using
external-only finalization after its candidate or an integrated stack ancestor makes the
ticket source tracked. Reconcile the three stranded ticket dispositions from the observed
merged PRs without inventing run, candidate, or completion evidence.

## Acceptance Criteria

- [ ] Delivery re-evaluates each ticket source against the candidate index/tree and current
      base before commit, push, and provider mutation; it does not rely only on the
      folder-wide `ticket_source_mode` frozen at run creation.
- [ ] Stack reconciliation re-evaluates every remaining ticket after a parent integrates,
      before selecting its finalization adapter.
- [ ] An `ignored` snapshot whose source becomes tracked opens a deterministic
      `source-mode-drift` gate before commit, push, PR creation/update, or completion
      mutation.
- [ ] The gate and `status` expose ticket ID, snapshot classification, observed
      classification, boundary, affected source path, and an exact recovery instruction.
- [ ] Recovery requires an explicit source-publication change followed by a new run from a
      tracked base; resume never silently rewrites the immutable snapshot classification.
- [ ] Unchanged tracked and unchanged ignored runs preserve their existing staging,
      external-finalization, idempotency, containment, and crash-recovery behavior.
- [ ] A causal regression starts with fully ignored tickets, promotes them in the first
      candidate or integrated ancestor, and proves no open ticket path or completion claim
      reaches the delivery commit or provider boundary.
- [ ] TK-01, TK-02, and TK-03 under `autopilot-token-economics` are moved to `done/` with
      completion records derived only from run `7974966ec8d84a35`, the existing
      CandidateRefs, and merged PRs #59, #60, and #61; downstream readiness is recalculated.
- [ ] Ticket inventory, source-finalization, stack reconciliation, ledger replay, CLI, and
      focused forward tests pass, with unavailable live-provider behavior reported rather
      than inferred.

## Frontier

Ready. No dependency blocks the fix. It should land before another run consumes a ticket
folder whose Git tracking policy may change inside a stacked delivery.

## Step-by-Step Implementation Plan

1. Add a per-ticket source-classification observation at the last safe Git and provider
   boundaries, preserving the immutable snapshot as the expected side.
2. Compare snapshot, candidate, and reconciled-base classifications and persist a
   deterministic `source-mode-drift` gate before selecting tracked or ignored finalization.
3. Project the drift and recovery instruction through ledger replay, `status`, and final
   reporting without converting it into a quality failure.
4. Add ignored-to-tracked candidate and stacked-ancestor fixtures alongside unchanged-mode
   parity and interruption/replay cases.
5. Reconcile TK-01, TK-02, and TK-03 to `done/` using only existing content-addressed run
   and merge evidence, then verify TK-04 and TK-06 readiness.
6. Run focused source/finalizer/stack tests plus the workflow-family regression surface and
   record all evidence limitations.

## Testing Plan

Use disposable Git repositories with a fully ignored canonical ticket folder. Cover direct
candidate promotion, promotion inherited from a merged parent, restart from a tracked
base, crashes before and after gate persistence, unchanged tracked/ignored parity, symlink
and path containment, and repeated resume. Assert exact staged trees, provider call counts,
ledger events, completion paths, and inventory readiness. No live provider mutation is
required for the implementation claim.

## Out of Scope

- Implicitly migrating an active run from ignored to tracked ownership.
- Accepting arbitrary untracked non-ignored ticket inputs.
- Weakening snapshot immutability, CandidateRef binding, exact-head delivery, or merge
  authorization.
- Reconstructing evidence not present in the existing run artifacts, commits, or provider
  readbacks.
