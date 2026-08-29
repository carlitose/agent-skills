# Ticket-Autopilot Reconciliation Seal Recovery

## Artifact Graph

- Artifact ID: `artifact:ticket-autopilot-reconciliation-seal-recovery-diagnostic`
- Role: `spec`
- Standalone: true

### Children

- [SR-01 gate an out-of-protocol reconciliation head](../tickets/ticket-autopilot-reconciliation-seal-recovery/01-gate-out-of-protocol-reconciliation-head.md)

## Type

Diagnostic spec

## Status

Diagnosed; ready for SR-01.

## Diagnosis Report - lens: replay-safe sealing boundary

### Root cause

After semantic reconciliation is revalidated, `_seal_revalidated_reconciliation_head()`
accepts only two local states: the prepared head with the verified tree staged, or the exact
runner-created sealing commit whose parent and trailer match the recorded run and ticket. If
`HEAD` advances through any other commit, the helper correctly refuses to treat it as the
runner's replay-safe seal.

The refusal is not integrated with the reconciliation recovery protocol. The seal call and
the following ledger transition sit outside the reconciliation `GitError`/`ProviderError`
handler, so the helper raises a bare `GitError` with only
`reconciliation head changed outside the replay-safe sealing step`. No gate is recorded, the
unexpected and expected heads are omitted, the worktree is not identified, and no safe repair
sequence is provided. The verified ledger state remains unchanged, so every resume repeats the
same opaque exception.

### Evidence

- The semantic reconciliation handler catches Git and provider failures while deriving and
  refreshing candidates, but calls `_seal_revalidated_reconciliation_head()` outside either
  catch boundary.
- The helper reads `old_local_head`, current `HEAD`, its parent, and the runner marker, then
  discards all of those values when it raises the generic error.
- A deterministic reproduction starts from a verified reconciled candidate, commits the same
  verified staged tree with an operator message and a non-recorded parent, then resumes. It
  raises the bare `GitError` directly; the ledger records no recovery gate.
- Because the ticket remains `verified`, replay re-enters the same head/marker check and fails
  identically. The runner has no supported acknowledgement-and-resume path for this state.

### User-visible failure

An operator or interrupted automation that changes the reconciliation branch after fresh
verification strands the run. The runner detects the audit violation, but does not turn it
into an auditable decision point and does not explain how to preserve the unexpected head,
restore the prepared lineage while retaining the verified staged tree, validate that tree,
and resume.

### Feedback loop built

Extend the semantic reconciliation integration test at the post-verification sealing
boundary. Advance the worktree with a commit that lacks the runner marker and prove that resume
returns a durable `stack-reconciliation-recovery` gate rather than raising. The gate must record
the expected head, observed head, verified candidate tree, branch, worktree, reason, and explicit
human-repair steps, while issuing no provider mutation.

The regression must then perform the documented repair: preserve the unexpected head under a
backup ref, soft-reset to the expected prepared head so the verified tree remains staged, prove
`git write-tree` equals the recorded candidate tree, approve the exact gate with evidence, and
resume through the ordinary canonical seal. This proves the recovery guidance is executable and
that approval alone cannot bypass the Git invariant.

### Fix location and approach

Represent unexpected reconciliation lineage as a structured `GitError` carrying recovery
details. Include the exact observed state and non-destructive instructions; never reset or
adopt the unexpected commit automatically.

Wrap the sealing step in the existing durable reconciliation error-gate path and use the
category `stack-reconciliation-recovery`. Teach `_reconciliation_error_gate()` to preserve the
structured details. Gate approval returns the ticket to its prior verified state; a subsequent
resume succeeds only after the operator has restored the expected lineage and verified staged
tree, so the canonical marker commit and ledger transition remain authoritative.

### Alternatives ruled out

- **Automatically soft-reset the branch.** Rejected because the unexpected commit may contain
  operator work and must first be preserved deliberately.
- **Accept any commit with the verified tree.** Rejected because parent lineage and the
  run/ticket marker are part of the replay-safe sealing proof.
- **Retry without a gate.** Rejected because unchanged local state deterministically produces
  the same failure and loses auditability.
- **Require a new run for every occurrence.** Rejected because the recorded prepared head and
  verified tree provide a safe, explicit repair-and-resume contract.
- **Catch all transition and lifecycle errors.** Rejected because pause, cancellation, source
  drift, and invalid ledger transitions retain their existing contracts; this fix is scoped to
  Git failures at the sealing boundary.

### Confidence: high

The reproduction follows the exact live branch, the missing catch boundary is visible in the
handler, and all values needed for a deterministic recovery record are already read by the
sealing helper.
