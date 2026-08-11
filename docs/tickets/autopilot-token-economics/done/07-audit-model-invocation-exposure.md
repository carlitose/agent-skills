---
ticket_schema: 1
ticket_id: "TK-07"
execution_mode: AFK
blocked_by: []
---

# Audit model-invocation exposure

## Artifact Graph

- Artifact ID: `artifact:tk-07-audit-model-invocation-exposure`
- Role: `ticket`
- Parent: [Autopilot Token Economics](../../../specs/autopilot-token-economics-wayfinder.md)

## Type
Task

## What to Build
A stated criterion for when a skill should be hidden from the model-visible listing with
`disable-model-invocation: true`, the flag applied where the criterion says it belongs, and a
check that keeps the listing from drifting.

The flag demonstrably works: `grill-me`, `grill-with-docs`, `handoff`,
`resolving-merge-conflicts`, `to-questionnaire`, and `wizard` carry it and are absent from an
observed model-visible listing, accounting for 267 words already saved. The lever is real but
small, so the criterion matters more than the raw saving.

## Acceptance Criteria
- [ ] The criterion is written down and distinguishes user-invoked-only workflows from skills
      the model must be able to select autonomously.
- [ ] Every skill is classified against the criterion, with the reason recorded.
- [ ] Skills that must stay model-invocable are not hidden merely to reduce the listing.
- [ ] Oversized descriptions are reported rather than silently rewritten.
- [ ] A check fails when a new skill is added without a classification.
- [ ] Uninstalled skills are noted as costing nothing today, without prescribing installation.

## Frontier
Ready. No dependency and no decision remains.

## Step-by-Step Plan
1. Write the hiding criterion.
2. Classify every skill and record each reason.
3. Apply flags only where the criterion requires it.
4. Add the drift check for newly added skills.

## Testing Plan
A static check over skill front matter asserting every skill carries a classification and
that hidden skills match the criterion.

## Out of Scope
- Hiding skills that the model legitimately needs to select.
- Rewriting descriptions for length alone.
- Installing skills that are currently absent from the install root.
