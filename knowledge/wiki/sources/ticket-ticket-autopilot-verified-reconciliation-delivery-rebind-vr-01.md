---
type: source
title: "Rebind a verified reconciliation candidate"
identity_key: ticket:ticket-autopilot-verified-reconciliation-delivery-rebind/VR-01
identity_strength: stable
source_path: docs/tickets/ticket-autopilot-verified-reconciliation-delivery-rebind/done/01-rebind-verified-reconciliation-candidate.md
source_digest: sha256:5e5792a7420090f063c908bc0f6393a78084bd6d9c2e5761d38808dcb774b0dc
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-29
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Rebind a verified reconciliation candidate

Compiled from `docs/tickets/ticket-autopilot-verified-reconciliation-delivery-rebind/done/01-rebind-verified-reconciliation-candidate.md`. Identity is `ticket:ticket-autopilot-verified-reconciliation-delivery-rebind/VR-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-29** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-ticket-autopilot-verified-reconciliation-delivery-rebind-diagnostic]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[3],"status":"present"},"exclusions":{"headings":[5],"status":"present"},"frontier":{"headings":[],"status":"not-identified"},"intent":{"headings":[],"status":"not-identified"},"testing":{"headings":[4],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-ticket-autopilot-verified-reconciliation-delivery-rebind-vr-01.md","payload_bytes":2663,"payload_sha256":"5e5792a7420090f063c908bc0f6393a78084bd6d9c2e5761d38808dcb774b0dc"}],"payload_bytes":2663,"payload_sha256":"5e5792a7420090f063c908bc0f6393a78084bd6d9c2e5761d38808dcb774b0dc","schema":1,"source_digest":"sha256:5e5792a7420090f063c908bc0f6393a78084bd6d9c2e5761d38808dcb774b0dc","source_identity":"ticket:ticket-autopilot-verified-reconciliation-delivery-rebind/VR-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | no matching section identified in the source; complete source retained |
| acceptance | 3: Acceptance Criteria |
| testing | 4: Testing |
| frontier | no matching section identified in the source; complete source retained |
| exclusions | 5: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2663,"payload_sha256":"5e5792a7420090f063c908bc0f6393a78084bd6d9c2e5761d38808dcb774b0dc","schema":1,"source_digest":"sha256:5e5792a7420090f063c908bc0f6393a78084bd6d9c2e5761d38808dcb774b0dc","source_identity":"ticket:ticket-autopilot-verified-reconciliation-delivery-rebind/VR-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "VR-01"
execution_mode: AFK
blocked_by: []
---

# Rebind a verified reconciliation candidate

## Artifact Graph

- Artifact ID: `artifact:vr-01-rebind-verified-reconciliation-candidate`
- Role: `ticket`
- Parent: [verified reconciliation delivery-rebind diagnostic](../../../specs/ticket-autopilot-verified-reconciliation-delivery-rebind-diagnostic.md)

## What Was Built

Reconciliation resume now seals a corrected, fully verified candidate into a replay-safe commit
and updates its delivery candidate, prepared head, semantic lineage, and stale render history in
one audited transition. Genuine post-verification drift keeps the last delivery binding, runs one
fresh bounded quality epoch, and then uses the same seal before publication.

## Acceptance Criteria

- [x] The semantic stack regression reproduces a verified candidate that differs from stale
      delivery and prepared lineage.
- [x] Sealing preserves CandidateRef, artifact generation, leaf results, verification checkpoints,
      and validated stages while clearing one-shot merge authority.
- [x] The replacement commit and ledger transition replay after crashes on either side of durable
      ledger persistence.
- [x] Reconciled PR-body rendering binds the current verification bundle and head while retaining
      append-only body and reconciliation history.
- [x] Genuine Git drift from both semantic and delivery candidates invalidates evidence exactly
      once, preserves the previous delivery binding, and seals only after fresh verification.
- [x] Same-tree reconciliation, repeated target refresh, provider-race, and existing PR-body
      rebind behavior remain covered.
- [x] Ledger replay rejects forged seal head lineage and unrelated mutations.
- [x] Focused CLI, kernel, replay, compilation, and patch-integrity checks pass; full-suite
      baseline differences are reported explicitly.

## Testing

- Semantic reconciliation/rebind regression: pass, including two seal crash points, genuine
  post-verification drift, two target refreshes, and fresh-bundle PR-body publication.
- Existing equivalent reconciliation and crash-resumable delivery regressions: pass.
- Kernel and semantic replay suites: pass.
- Full runner suite: 445 of 448 passed; the three `wait-what` inventory-policy failures
  reproduced unchanged on `main`.
- Python compilation and `git diff --check`: pass.

## Out of Scope

- Automatic rebase-conflict resolution.
- Weakening force-with-lease, provider readback, exact-head merge, or append-only audit guards.
- Manual production-ledger repair.
- Unrelated baseline failures outside Ticket Autopilot reconciliation.

```
