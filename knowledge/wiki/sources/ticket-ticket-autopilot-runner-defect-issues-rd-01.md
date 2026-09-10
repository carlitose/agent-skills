---
type: source
title: "Map runner-defect evidence and escalation seams"
identity_key: ticket:ticket-autopilot-runner-defect-issues/RD-01
identity_strength: stable
source_path: docs/tickets/ticket-autopilot-runner-defect-issues/done/01-map-runner-defect-escalation-seams.md
source_digest: sha256:3ad4509e63aea8b1f4f28df415c83c776e8b8ac17c93e6a9a3cb553ecb0a6b0f
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-28
created_provenance: git-commit
disposition_changed: 2026-08-29
disposition_changed_provenance: git-rename
run_id: runner-defect-issues-20260829
---

# Map runner-defect evidence and escalation seams

Compiled from `docs/tickets/ticket-autopilot-runner-defect-issues/done/01-map-runner-defect-escalation-seams.md`. Identity is `ticket:ticket-autopilot-runner-defect-issues/RD-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-28** via `git-commit`
- Disposition changed: **2026-08-29** via `git-rename`

## Graph

- Parent source: [[sources/artifact-ticket-autopilot-runner-defect-issue-wayfinder]]

## Run

Completed under autopilot run `runner-defect-issues-20260829`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-ticket-autopilot-runner-defect-issues-rd-01.md","payload_bytes":2817,"payload_sha256":"3ad4509e63aea8b1f4f28df415c83c776e8b8ac17c93e6a9a3cb553ecb0a6b0f"}],"payload_bytes":2817,"payload_sha256":"3ad4509e63aea8b1f4f28df415c83c776e8b8ac17c93e6a9a3cb553ecb0a6b0f","schema":1,"source_digest":"sha256:3ad4509e63aea8b1f4f28df415c83c776e8b8ac17c93e6a9a3cb553ecb0a6b0f","source_identity":"ticket:ticket-autopilot-runner-defect-issues/RD-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2817,"payload_sha256":"3ad4509e63aea8b1f4f28df415c83c776e8b8ac17c93e6a9a3cb553ecb0a6b0f","schema":1,"source_digest":"sha256:3ad4509e63aea8b1f4f28df415c83c776e8b8ac17c93e6a9a3cb553ecb0a6b0f","source_identity":"ticket:ticket-autopilot-runner-defect-issues/RD-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "RD-01"
execution_mode: AFK
blocked_by: []
---

# Map runner-defect evidence and escalation seams

## Artifact Graph

- Artifact ID: `artifact:rd-01-map-runner-defect-escalation-seams`
- Role: `ticket`
- Parent: [Ticket Autopilot Runner-Defect Issue Escalation](../../specs/ticket-autopilot-runner-defect-issue-wayfinder.md)

## Parent Spec

[Ticket Autopilot Runner-Defect Issue Escalation](../../specs/ticket-autopilot-runner-defect-issue-wayfinder.md)

## What to Build

Produce a source-backed update to the owning Wayfinder that traces how runner-owned defects
are currently detected, diagnosed, gated, persisted, and exposed through provider adapters.
Separate observed code and contracts from proposed issue-escalation policy. Define the
smallest secret-safe evidence shape that RD-02 can model without calling GitHub.

## Acceptance Criteria

- [ ] The report identifies exact owners for exception classification, gate creation,
      diagnostic output, ledger history, provider capabilities, and external mutation guards.
- [ ] It distinguishes runner defects from project failures, provider/environment failures,
      expected gates, unsupported configurations, and user errors with counterexamples.
- [ ] The report defines a proposed normalized defect record and lists every field excluded
      by the diagnostic secret-redaction boundary.
- [ ] It maps deduplication, crash, replay, permission, offline, and pre-ledger failure cases
      without claiming an implementation exists.
- [ ] It identifies the safest integration seam and the tests needed to prove that issue
      escalation cannot alter ticket, gate, verification, or merge state.
- [ ] The Wayfinder records the resulting evidence, decisions, remaining unknowns, and exact
      RD-02 input contract. Any separate managed output is created only with reciprocal graph
      links in the same candidate.

## Frontier

Ready. Repository scope and destination are fixed; current runner ownership is the missing
input for RD-02.

## Step-by-Step Implementation Plan

1. Trace runner exceptions, gates, ledger transitions, provider negotiation, and diagnostics.
2. Classify observed failure families and identify stable versus volatile evidence.
3. Model lifecycle and crash boundaries for create, dedupe, retry, and unavailable provider.
4. Fold the source-backed findings and resulting RD-02 contract into the Wayfinder.

## Testing Plan

Use read-only source inspection and focused existing tests. Validate the updated Wayfinder and
Artifact Graph. No GitHub issue mutation, credential probe, or raw ledger capture is allowed.

## Out of Scope

- Implementing issue creation or a provider command.
- Choosing publication authority or closed-issue behavior.
- Diagnosing project bugs unrelated to the runner.

```
