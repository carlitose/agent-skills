---
type: source
title: "Allow eligible docs-only candidates through autonomous merge"
identity_key: ticket:ticket-autopilot-docs-only-autonomous-merge/DA-01
identity_strength: stable
source_path: docs/tickets/ticket-autopilot-docs-only-autonomous-merge/done/01-allow-eligible-docs-only-autonomous-merge.md
source_digest: sha256:b814c0e496a55f20bdbcbc55dac42f277ad44ff418ad7083fd0d5270e07c107c
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-29
created_provenance: git-commit
disposition_changed: 2026-08-29
disposition_changed_provenance: git-rename
run_id: da01-docs-only-automerge-20260829
---

# Allow eligible docs-only candidates through autonomous merge

Compiled from `docs/tickets/ticket-autopilot-docs-only-autonomous-merge/done/01-allow-eligible-docs-only-autonomous-merge.md`. Identity is `ticket:ticket-autopilot-docs-only-autonomous-merge/DA-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-29** via `git-commit`
- Disposition changed: **2026-08-29** via `git-rename`

## Graph

- Parent source: [[sources/artifact-ticket-autopilot-docs-only-autonomous-merge-diagnostic]]

## Run

Completed under autopilot run `da01-docs-only-automerge-20260829`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[7],"status":"present"},"frontier":{"headings":[],"status":"not-identified"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[6],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-ticket-autopilot-docs-only-autonomous-merge-da-01.md","payload_bytes":2723,"payload_sha256":"b814c0e496a55f20bdbcbc55dac42f277ad44ff418ad7083fd0d5270e07c107c"}],"payload_bytes":2723,"payload_sha256":"b814c0e496a55f20bdbcbc55dac42f277ad44ff418ad7083fd0d5270e07c107c","schema":1,"source_digest":"sha256:b814c0e496a55f20bdbcbc55dac42f277ad44ff418ad7083fd0d5270e07c107c","source_identity":"ticket:ticket-autopilot-docs-only-autonomous-merge/DA-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 6: Testing Plan |
| frontier | no matching section identified in the source; complete source retained |
| exclusions | 7: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2723,"payload_sha256":"b814c0e496a55f20bdbcbc55dac42f277ad44ff418ad7083fd0d5270e07c107c","schema":1,"source_digest":"sha256:b814c0e496a55f20bdbcbc55dac42f277ad44ff418ad7083fd0d5270e07c107c","source_identity":"ticket:ticket-autopilot-docs-only-autonomous-merge/DA-01"} -->
```markdown
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

```
