# Ticket Autopilot Parentless Base Reconciliation

## Type

Bug-analysis and delivery-hardening spec

## Status

Implemented by PBR-01 candidate; durable integration pending.

## Artifact Graph

- Artifact ID: `artifact:ticket-autopilot-parentless-base-reconciliation`
- Role: `spec`
- Parent: [Ticket Autopilot Multi-parent Base Reconciliation Diagnostic](ticket-autopilot-multi-parent-base-reconciliation-diagnostic.md)

### Children

- [PBR-01 support parentless PR base reconciliation](../tickets/ticket-autopilot-parentless-base-reconciliation/01-support-parentless-pr-base-reconciliation.md)

## Problem

Ticket Autopilot has an audited reconciliation path for a single-parent stacked child and,
after MPR-01, a multi-parent join whose blockers are integrated. It still rejects an ordinary
PR with `blocked_by: []` before fetching its recorded base:

```text
TransitionError: reconciliation requires recorded dependency lineage
```

PR #163 is the preserved reproduction. ICP-01 opened against `main` at base
`ed0857a03f83a323a2f53688880172b6f51cef8f`. After PRs #160, #161, and #162 were merged,
`main` advanced to `9351aae67643ee5010c173faf0936ba497d6a5c6`; GitHub then reported PR #163 as
`CONFLICTING` / `DIRTY`. The run retains exact delivery lineage and an open manual PR, but
`reconcile` refuses before Git or provider mutation because the ticket has no blockers.

## Root Cause

The CLI checks `if not blockers: raise` before selecting reconciliation mode. The later
base-advance branch already derives the old anchor from `delivery_lineage.base_sha` and the
new target from `delivery_lineage.base_branch`, but the empty-blocker guard makes that branch
unreachable for the ordinary parentless case. Dependency lineage is therefore treated as a
precondition even though immutable delivery lineage contains the required base identity.

## Goal

Allow a PR-open parentless ticket to enter the existing audited base-advance reconciliation
pipeline when its recorded base branch advances, without manufacturing dependency ancestry,
resolving semantic conflicts automatically, weakening CandidateRef evidence, or bypassing
provider and exact-head controls.

## Non-Goals

- Guessing content during a rebase conflict.
- Treating a parentless PR as a stack or inventing a blocker.
- Caller-supplied old/new SHAs, CandidateRefs, equivalence claims, or retarget receipts.
- Manual force-push outside the ledger.
- Preserving review/QA evidence after semantic tree drift.
- Authorizing merge, autonomous policy, wiki sync, issue publication, or use of ICP-01 as
  implementation evidence for this runner fix.

## Target Contract

### Mode selection

Reconciliation selects exactly one mode from ledger state:

- one blocker: existing single-parent stack behavior;
- two or more blockers, all integrated: existing multi-parent base-advance behavior;
- zero blockers: parentless base-advance behavior using delivery lineage only.

For parentless mode, the old anchor is `delivery_lineage.base_sha`, the target branch is
`delivery_lineage.base_branch`, and the expected remote head is
`delivery_lineage.head_sha`. Caller values may only be absent or exactly equal to those
ledger-derived identities.

### Reconciliation behavior

The runner fetches the recorded base branch, records durable intent before mutation, and
uses the existing guarded rebase, abort cleanup, CandidateRef derivation, evidence
preservation/invalidation, PR-body rebind, force-with-lease publication, provider readback,
and exact-head merge path.

A clean lineage-only rebase preserves validated evidence but clears one-shot merge authority.
A changed semantic tree enters bounded revalidation and requires a fresh Verification Bundle
and PR body. A content conflict aborts back to the exact old branch/head and remains explicit;
no conflict marker or guessed resolution may be committed.

### Replay and failure

Replay is idempotent and derives all identities from the ledger and live Git/provider
readbacks. Remote-head drift, target drift after provider mutation, a local replay head not
based on the exact fetched target, failed abort cleanup, source drift, or unsupported provider
state fails closed without force-pushing an unproven head.

## Semantic Invariants

- Empty dependency lineage is not missing delivery lineage.
- The old base, target branch, remote head, CandidateRef, PR body, and provider receipt remain
  exact and ledger-bound.
- Parentless, single-parent stack, and multi-parent join modes stay distinguishable.
- Semantic equality is Git-derived; semantic change invalidates inherited quality evidence.
- Force-with-lease and provider body/head readback remain mandatory.
- Manual merge remains manual and requires a fresh exact-head decision.

## Observable Acceptance Outcomes

- A PR-open ticket with `blocked_by: []` can prepare base-advance reconciliation after its
  recorded base branch advances.
- Preparation records parentless/base-advance mode and uses only delivery-lineage base/head
  identities.
- Clean rebase, semantic drift/revalidation, conflict-abort/replay, remote drift, and target
  refresh follow the same audited contracts as existing reconciliation.
- Existing stack and multi-parent behavior remains unchanged.
- PR #163 is not mutated as implementation evidence; after the fix is durably integrated,
  its run may separately invoke reconciliation.

## Implementation Slice

[PBR-01](../tickets/ticket-autopilot-parentless-base-reconciliation/01-support-parentless-pr-base-reconciliation.md)
owns the mode-selection change, history/status semantics if required, disposable integration
coverage, regression/forward checks, and operator documentation.

## Verification Strategy

- Disposable bare-remote integration fixture for a parentless PR whose `main` advances.
- Clean equivalent rebase with exact remote replacement and PR-body readback.
- Semantic-drift path requiring fresh bounded verification.
- Automatic conflict with proven abort back to old branch/head and resumable durable intent.
- Negative cases for caller ancestry claims, stale remote head, advancing target, and replay
  head not descended from the exact target.
- Existing single-parent, multi-parent, refresh, source-mode, full-suite, forward-scenario,
  artifact-audit-delta, static, and controlled-context checks.
- No live provider mutation, merge, or modification of PR #163 as implementation evidence.

## Security and Data Concerns

Reconciliation replaces a remote branch head. The implementation must preserve
force-with-lease, exact expected remote SHA, target ancestry checks, source-mode guards,
append-only ledger intent, and provider readback. A caller cannot convert the new mode into a
generic force-push primitive.

## Alternatives

- **Resolve PR #163 manually.** Rejected because the ledger, CandidateRef, Verification Bundle,
  PR body, and exact-head authority would remain bound to the old head.
- **Invent a synthetic blocker.** Rejected because dependency metadata is not Git ancestry.
- **Close and recreate every conflicted parentless PR.** Rejected as avoidable delivery churn
  that still leaves the runner gap.
- **Automatically choose conflict content.** Rejected; semantic resolution remains explicit
  implementation work followed by revalidation.
