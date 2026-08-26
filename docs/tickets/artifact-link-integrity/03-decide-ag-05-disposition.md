---
ticket_schema: 1
ticket_id: "LI-03"
execution_mode: HITL
blocked_by: []
---

# Decide AG-05's disposition

## Artifact Graph
- Artifact ID: `artifact:li-03-decide-ag-05-disposition`
- Role: `ticket`
- Parent: [artifact-link-integrity-wayfinder.md](../../specs/artifact-link-integrity-wayfinder.md)

## Parent Spec
[artifact-link-integrity-wayfinder.md](../../specs/artifact-link-integrity-wayfinder.md)

## What to Build
A human decision, then its paperwork. This ticket requires `grilling`: walk the user through
the finding below, one question at a time, and confirm the disposition before touching
anything.

**The finding.** `AG-05` (`docs/tickets/artifact-graph-disposition-drift/05-align-docs-only-with-the-audit.md`)
was emitted on a diagnosis this map has since measured to be wrong on both halves:

- Its Defect 4 said the docs-only gate refuses the six graph-less specs because it blocks on
  the `legacy-artifact` **warning**. Measured with the gate narrowed to errors only: the edit
  is still refused, by `missing-artifact-graph`, an **error**. The audit grandfathers an
  untouched file and demands the section the moment the file is edited — deliberately.
  Narrowing the gate is a no-op.
- Its other half — giving `docs_only` the disposition-tolerant resolver — would forgive
  repairable drift in writable documents. The refusal is what got the llm-wiki map's seven
  stale links repaired. With `LI-02` in place, the literal check on writable documents is
  simply *correct*, because the mover keeps the links true.

An implementation exists in the abandoned worktree of run `42cf7d6d50a84f97`: a shared
`artifact_links` module, both readers wired to it, the gate narrowed, 23 + 38 tests green. It
implements the wrong thing correctly and was never delivered. One salvageable piece: `LI-01`
may adopt the module's resolution semantics for its scanner.

**The recommendation to put to the user**: cancel `AG-05` as superseded by `LI-01` and
`LI-02`, correct the diagnostic, and abort the run.

## Acceptance Criteria
- [ ] The user has confirmed a disposition for `AG-05` through `grilling` — cancel, rewrite,
      or keep — and the confirmation is quoted in this ticket's record.
- [ ] If cancelled: `ticket-cancel` executed with the user's identity, the quoted reason, and
      this ticket as the durable authority reference; `AG-05` reports `canceled` in
      `ticket-list`.
- [ ] Run `42cf7d6d50a84f97` is aborted, and its worktree removed if unchanged salvage is not
      wanted.
- [ ] `docs/specs/artifact-graph-disposition-drift-diagnostic.md` records the Defect 4
      correction with the measurement — the `missing-artifact-graph` error, not the
      `legacy-artifact` warning, is what refuses an edited graph-less file — and points its
      fix direction at `LI-01`/`LI-02` instead of at a gate change.
- [ ] `artifact-audit` totals are unchanged by the paperwork.

## Frontier
Blocked on the user: cancelling a ticket requires explicit human authority, and the
recommendation reverses a ticket the user approved earlier today. Nothing else blocks it, and
nothing blocks on it.

## Step-by-Step Implementation Plan
1. Run `grilling` on the single question: given the measurement, what is `AG-05`'s
   disposition? Present cancel-as-superseded as the recommendation, with rewrite and keep as
   alternatives. Checkpoint: an explicit answer.
2. Execute the chosen disposition through the canonical CLI. Checkpoint: `ticket-list` agrees.
3. Abort the stale run; record what, if anything, was salvaged from its worktree.
   Checkpoint: the run no longer appears active.
4. Correct the diagnostic. Checkpoint: no sentence in it still claims the warning blocks the
   gate.

## Testing Plan
Automated: `ticket-list --json` asserting the final disposition; `artifact-audit --json`
before and after the paperwork, totals equal.

Manual: the `grilling` transcript is the evidence for the decision itself.

Unavailable boundary: none. Administrative and documentary only.

## Out of Scope
- Implementing any reader or gate change. That possibility ends with this decision.
- The repair and the mover (`LI-01`, `LI-02`).
- Deleting `AG-05`'s file. A cancelled ticket moves to `canceled/`; history stays.
