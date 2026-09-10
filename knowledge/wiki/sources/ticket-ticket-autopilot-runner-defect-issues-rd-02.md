---
type: source
title: "Prototype fingerprinted issue escalation"
identity_key: ticket:ticket-autopilot-runner-defect-issues/RD-02
identity_strength: stable
source_path: docs/tickets/ticket-autopilot-runner-defect-issues/done/02-prototype-fingerprinted-issue-escalation.md
source_digest: sha256:092920a0958145724a6d945d06a08bfb157074a44912e8b899829d0d8000b3bc
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-28
created_provenance: git-commit
disposition_changed: 2026-08-29
disposition_changed_provenance: git-rename
run_id: runner-defect-issues-20260829
---

# Prototype fingerprinted issue escalation

Compiled from `docs/tickets/ticket-autopilot-runner-defect-issues/done/02-prototype-fingerprinted-issue-escalation.md`. Identity is `ticket:ticket-autopilot-runner-defect-issues/RD-02`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-28** via `git-commit`
- Disposition changed: **2026-08-29** via `git-rename`

## Graph

- Parent source: [[sources/artifact-ticket-autopilot-runner-defect-issue-wayfinder]]
- Blocked by: [[sources/ticket-ticket-autopilot-runner-defect-issues-rd-01]] — `ticket:ticket-autopilot-runner-defect-issues/RD-01`

## Run

Completed under autopilot run `runner-defect-issues-20260829`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-ticket-autopilot-runner-defect-issues-rd-02.md","payload_bytes":2547,"payload_sha256":"092920a0958145724a6d945d06a08bfb157074a44912e8b899829d0d8000b3bc"}],"payload_bytes":2547,"payload_sha256":"092920a0958145724a6d945d06a08bfb157074a44912e8b899829d0d8000b3bc","schema":1,"source_digest":"sha256:092920a0958145724a6d945d06a08bfb157074a44912e8b899829d0d8000b3bc","source_identity":"ticket:ticket-autopilot-runner-defect-issues/RD-02","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2547,"payload_sha256":"092920a0958145724a6d945d06a08bfb157074a44912e8b899829d0d8000b3bc","schema":1,"source_digest":"sha256:092920a0958145724a6d945d06a08bfb157074a44912e8b899829d0d8000b3bc","source_identity":"ticket:ticket-autopilot-runner-defect-issues/RD-02"} -->
```markdown
---
ticket_schema: 1
ticket_id: "RD-02"
execution_mode: AFK
blocked_by:
  - "RD-01"
---

# Prototype fingerprinted issue escalation

## Artifact Graph

- Artifact ID: `artifact:rd-02-prototype-fingerprinted-issue-escalation`
- Role: `ticket`
- Parent: [Ticket Autopilot Runner-Defect Issue Escalation](../../specs/ticket-autopilot-runner-defect-issue-wayfinder.md)

## Parent Spec

[Ticket Autopilot Runner-Defect Issue Escalation](../../specs/ticket-autopilot-runner-defect-issue-wayfinder.md)

## What to Build

Build a disposable, no-network model for normalized runner-defect eligibility, secret-safe
issue rendering, canonical fingerprints, local outbox receipts, GitHub-search deduplication,
and crash replay. Use the RD-01 report as the ownership and evidence boundary.

## Acceptance Criteria

- [ ] Equivalent failures with different paths, run IDs, timestamps, branches, or stack-line
      numbers produce one fingerprint; materially different owners or failure shapes do not.
- [ ] Project failures, expected gates, provider outages, low-confidence suspicions, and
      unredacted evidence are rejected before any provider operation is proposed.
- [ ] The model represents absent, open-match, closed-match, create-success, ambiguous-match,
      permission-failure, offline, crash-before-create, and lost-response states.
- [ ] Replay after every crash point creates at most one issue and never comments, reopens,
      labels, or closes an existing issue.
- [ ] The prototype exposes a deterministic dry-run transcript and tests proving that ticket,
      gate, verification, and merge state remain unchanged.
- [ ] Keep/discard guidance names the narrow production seam and unresolved RD-03 choices.

## Frontier

Blocked by RD-01. It becomes ready when the research report fixes stable inputs and owners.

## Step-by-Step Implementation Plan

1. Encode the normalized defect record and rejection reasons from RD-01.
2. Compare fingerprint designs and select one with explicit volatility stripping.
3. Model local reservation, provider search, create, readback, and durable receipt phases.
4. Add causal tests and document counterexamples, limits, and production keep/discard advice.

## Testing Plan

Run deterministic unit and state-machine tests with synthetic secret-bearing fixtures that
must be rejected or redacted. Use a fake GitHub adapter only; no network or live issue write.

## Out of Scope

- Production runner integration.
- Deciding or persisting real publication authority.
- General-purpose issue tracker support.

```
