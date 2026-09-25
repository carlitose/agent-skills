---
type: source
title: "GP-01 — Observe all GitHub required-check policies"
identity_key: ticket:github-required-check-readback/GP-01
identity_strength: stable
source_path: docs/tickets/github-required-check-readback/01-observe-required-checks.md
source_digest: sha256:065b89ae8ea7fa036c7c24a8a21c5ecafb6117b0e1da20482011e0f819d85d56
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-09-20
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# GP-01 — Observe all GitHub required-check policies

Compiled from `docs/tickets/github-required-check-readback/01-observe-required-checks.md`. Identity is `ticket:github-required-check-readback/GP-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-20** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-github-required-check-readback]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-github-required-check-readback-gp-01.md","payload_bytes":3082,"payload_sha256":"065b89ae8ea7fa036c7c24a8a21c5ecafb6117b0e1da20482011e0f819d85d56"}],"payload_bytes":3082,"payload_sha256":"065b89ae8ea7fa036c7c24a8a21c5ecafb6117b0e1da20482011e0f819d85d56","schema":1,"source_digest":"sha256:065b89ae8ea7fa036c7c24a8a21c5ecafb6117b0e1da20482011e0f819d85d56","source_identity":"ticket:github-required-check-readback/GP-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3082,"payload_sha256":"065b89ae8ea7fa036c7c24a8a21c5ecafb6117b0e1da20482011e0f819d85d56","schema":1,"source_digest":"sha256:065b89ae8ea7fa036c7c24a8a21c5ecafb6117b0e1da20482011e0f819d85d56","source_identity":"ticket:github-required-check-readback/GP-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "GP-01"
execution_mode: AFK
blocked_by: []
---

# GP-01 — Observe all GitHub required-check policies

## Artifact Graph
- Artifact ID: `artifact:github-required-check-readback-gp01`
- Role: `ticket`
- Parent: [Spec](../../specs/github-required-check-readback.md)

## Parent Spec
[GitHub required-check policy readback](../../specs/github-required-check-readback.md)

## What to Build
Repair todos #58 and #62 in the existing provider boundary: classic branch-protection
readback and app-bound required status checks, composing with rulesets and exact-head CI.

## Acceptance Criteria
- [ ] A classic required context missing from the rollup remains pending.
- [ ] Classic and ruleset requirements are combined without duplicate identical gates.
- [ ] A same-name check from the wrong app cannot satisfy a declared app constraint;
      current-head app-bound pass, pending and failure observations remain distinguishable.
- [ ] Exact unprotected-branch absence, private-plan unavailability, malformed data and
      ordinary permission/network/not-found failures remain distinct and fail closed as
      specified; malformed or incomplete app/head observations cannot become PASS.
- [ ] Existing queue, approval, non-passing-check and head guards remain intact; Azure
      behavior, remote policies, authorization and runtime settings are unchanged.
- [ ] Focused RED/GREEN, shared-context review, causal QA and a validated verification
      bundle retain failures, cost and explicit limits; delivery requires real current-head CI.

## Frontier
Ready. No implementation-start human decision is missing. Required hosted CI and exact-head
provider checks remain delivery gates. Runner suspended; no subagents; wiki sync deferred.

## Step-by-Step Implementation Plan
1. Preserve diagnosis and canonical ticket/candidate identity from current remote main.
2. Add failing public-adapter regressions for classic policy and app identity.
3. Implement bounded readback/normalization, then update explicit fake API responses.
4. Run focused checks, simplify only if useful, freeze and review the candidate inline.
5. Plan/execute causal QA and validate the verification handoff; caller delivery is separate.

## Testing Plan
Exercise `ProviderExecutor.execute` with controlled command results, including pagination
and adversarial malformed/mismatched responses. Run affected semantic-normalization and
merge-gate integration tests. Use existing read-only live policy/check data for an adapter
smoke check and require hosted CI on the final PR head. No fabricated external service,
independent review, runtime reload, or duration evidence. Retry limit: three quality cycles;
retain consumption and failed evidence, and never exceed 900 seconds for a check/job.

## Out of Scope
- Scheduler execution, ledger reconciliation, source-independent approval/merge authority.
- Remote branch-protection changes, new bot/runtime tooling, wiki synchronization and reload.
- General provider refactoring, cleanup of inherited graph errors, or raising any ceiling.

```
