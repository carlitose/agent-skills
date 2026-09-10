---
type: source
title: "Bind delivery branch creation to the verified base"
identity_key: ticket:ticket-autopilot-delivery-stale-local-base/FS-01
identity_strength: stable
source_path: docs/tickets/ticket-autopilot-delivery-stale-local-base/done/01-bind-delivery-branch-to-verified-base.md
source_digest: sha256:ddf00e5e0b16f970465599d74021a14a14da6a176fe66b472d562029ac385e6b
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-29
created_provenance: git-commit
disposition_changed: 2026-08-29
disposition_changed_provenance: git-rename
run_id: 369ba446eb4948e9
---

# Bind delivery branch creation to the verified base

Compiled from `docs/tickets/ticket-autopilot-delivery-stale-local-base/done/01-bind-delivery-branch-to-verified-base.md`. Identity is `ticket:ticket-autopilot-delivery-stale-local-base/FS-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-29** via `git-commit`
- Disposition changed: **2026-08-29** via `git-rename`

## Graph

- Parent source: [[sources/artifact-ticket-autopilot-delivery-stale-local-base-diagnostic]]

## Run

Completed under autopilot run `369ba446eb4948e9`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-ticket-autopilot-delivery-stale-local-base-fs-01.md","payload_bytes":3152,"payload_sha256":"ddf00e5e0b16f970465599d74021a14a14da6a176fe66b472d562029ac385e6b"}],"payload_bytes":3152,"payload_sha256":"ddf00e5e0b16f970465599d74021a14a14da6a176fe66b472d562029ac385e6b","schema":1,"source_digest":"sha256:ddf00e5e0b16f970465599d74021a14a14da6a176fe66b472d562029ac385e6b","source_identity":"ticket:ticket-autopilot-delivery-stale-local-base/FS-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3152,"payload_sha256":"ddf00e5e0b16f970465599d74021a14a14da6a176fe66b472d562029ac385e6b","schema":1,"source_digest":"sha256:ddf00e5e0b16f970465599d74021a14a14da6a176fe66b472d562029ac385e6b","source_identity":"ticket:ticket-autopilot-delivery-stale-local-base/FS-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "FS-01"
execution_mode: AFK
blocked_by: []
---

# Bind delivery branch creation to the verified base

## Artifact Graph

- Artifact ID: `artifact:fs-01-bind-delivery-branch-to-verified-base`
- Role: `ticket`
- Parent: [delivery stale-local-base diagnostic](../../specs/ticket-autopilot-delivery-stale-local-base-diagnostic.md)

## Parent Spec

[Delivery stale-local-base diagnostic](../../specs/ticket-autopilot-delivery-stale-local-base-diagnostic.md)

## What to Build

Make tracked-ticket delivery create a new branch from a commit proven to match the verified
CandidateRef base tree, instead of trusting a possibly stale local `main` ref. Preserve the
staged candidate exactly, avoid mutating user-owned base branches, and record the actual base
SHA used for delivery lineage.

## Acceptance Criteria

- [ ] A two-ticket regression advances remote `main` through the first provider merge while
      local `main` remains stale, then delivers a second candidate that edits the same file
      without opening a finalization-environment gate.
- [ ] Branch creation proves that its selected start commit has the CandidateRef base tree
      before Git mutation and preserves the exact staged and committed candidate trees.
- [ ] Delivery does not force-update, checkout, or otherwise mutate the user's local base
      branch.
- [ ] The recorded delivery lineage names the actual base commit used by branch creation and
      remains compatible with provider base-branch readback.
- [ ] Replay after branch creation and after delivery commit is idempotent.
- [ ] A missing matching base commit or genuine base-tree drift fails closed with a precise
      reconciliation requirement before push or provider mutation.
- [ ] Existing initial delivery, stacked delivery, reconciliation, ignored-source, and
      exact-head merge tests remain green.

## Frontier

Ready. The live reproduction, tree identities, source owner, and safe recovery are all pinned
in the diagnostic spec; no product or authority decision remains.

## Step-by-Step Implementation Plan

1. Add a failing long-lived stacked-delivery regression with stale local `main` and a
   same-file second candidate.
2. Move delivery branch start-point selection behind a helper that proves CandidateRef
   base-tree identity without changing the local base branch.
3. Bind delivery lineage to the selected start commit and reject unmatched or drifted bases
   before branch mutation.
4. Add replay and true-drift cases, then run focused finalizer/CLI and full runner suites.

## Testing Plan

Use deterministic temporary repositories and provider fakes. Cover stale local refs, exact
tree preservation, no local-base mutation, crash/replay boundaries, genuine drift, initial
delivery, stacked delivery, and provider readback. Run static checks and the full runner suite;
classify any exact-base failures separately.

## Out of Scope

- Reconciliation rebase policy or conflict resolution.
- Provider merge-rule discovery.
- Weakening CandidateRef, exact-head, force-with-lease, or PR-body readback guards.
- Automatically updating any user-owned local branch.

```
