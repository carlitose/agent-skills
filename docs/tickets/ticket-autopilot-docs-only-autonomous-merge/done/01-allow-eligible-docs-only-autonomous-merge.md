---
ticket_schema: 1
ticket_id: "DA-01"
execution_mode: AFK
blocked_by: []
---

# Allow eligible docs-only candidates through autonomous merge

## Artifact Graph

- Artifact ID: `artifact:da-01-allow-eligible-docs-only-autonomous-merge`
- Role: `ticket`
- Parent: [Docs-only autonomous merge diagnostic](../../specs/ticket-autopilot-docs-only-autonomous-merge-diagnostic.md)

## Parent Spec

[Docs-only autonomous merge diagnostic](../../specs/ticket-autopilot-docs-only-autonomous-merge-diagnostic.md)

## What to Build

Make autonomous merge eligibility recognize the runner's canonical eligible docs-only state
as an alternative to the complete standard leaf pipeline. Keep every exact-identity,
delivery-lineage, grant, live-provider, checks, approval, mergeability, and expected-head
guard unchanged.

## Acceptance Criteria

- [ ] A canonical eligible docs-only receipt bound to the current CandidateRef can pass
      autonomous eligibility without fabricated `simplify`, `review`, or QA stages.
- [ ] Standard-path candidates still require every stage in `STAGES`.
- [ ] Rejected, missing, stale, malformed, or CandidateRef-drifted docs-only receipts fail
      closed before provider merge mutation.
- [ ] Docs-only evidence keeps the `implementation-complete` claim ceiling and does not become
      behavior, live-host, independent-review, or production evidence.
- [ ] An end-to-end autonomous docs-only regression opens the PR, performs live fake-provider
      eligibility readback, merges by expected head, and records durable integration.
- [ ] Existing docs-only delivery/revalidation, autonomous merge, stacked delivery, and full
      runner suites remain green.

## Step-by-Step Implementation Plan

1. Add a failing autonomous docs-only delivery regression at the eligibility boundary.
2. Extract or add the smallest canonical predicate for standard versus eligible docs-only
   validation state.
3. Exercise negative receipt and CandidateRef cases without calling the provider merge
   mutation.
4. Run the focused regression, CLI suite, and full ticket-autopilot suite.

## Testing Plan

Use real temporary Git repositories and the existing fake live GitHub runner. Assert the
provider operation sequence, expected-head merge binding, ledger integration record, unchanged
claim ceiling, and zero fabricated leaf stages. Retain a negative test that proves invalid
docs-only state never reaches merge mutation.

## Out of Scope

- Changing single-parent stacked scheduling or dependency readiness.
- Raising docs-only evidence or claims above `implementation-complete`.
- Weakening provider, policy, approval, lineage, or exact-head merge checks.
- Editing or bypassing the CR-05 ledger gate manually.
