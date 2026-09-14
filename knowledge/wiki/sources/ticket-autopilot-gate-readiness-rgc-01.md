---
type: source
title: "Distinguish technical gates and reuse exact existing authority"
identity_key: ticket:autopilot-gate-readiness/RGC-01
identity_strength: stable
source_path: docs/tickets/autopilot-gate-readiness/done/01-distinguish-gate-readiness.md
source_digest: sha256:f17329c88bbf56e2106ee16cb2a605a593fbaf1e3bbd904f81213ad27bb9a79a
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-10
created_provenance: git-commit
disposition_changed: 2026-09-10
disposition_changed_provenance: git-rename
run_id: rgc01
---

# Distinguish technical gates and reuse exact existing authority

Compiled from `docs/tickets/autopilot-gate-readiness/done/01-distinguish-gate-readiness.md`. Identity is `ticket:autopilot-gate-readiness/RGC-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-10** via `git-commit`
- Disposition changed: **2026-09-10** via `git-rename`

## Graph

- Parent source: [[sources/artifact-autopilot-gate-readiness]]

## Run

Completed under autopilot run `rgc01`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-autopilot-gate-readiness-rgc-01.md","payload_bytes":4184,"payload_sha256":"f17329c88bbf56e2106ee16cb2a605a593fbaf1e3bbd904f81213ad27bb9a79a"}],"payload_bytes":4184,"payload_sha256":"f17329c88bbf56e2106ee16cb2a605a593fbaf1e3bbd904f81213ad27bb9a79a","schema":1,"source_digest":"sha256:f17329c88bbf56e2106ee16cb2a605a593fbaf1e3bbd904f81213ad27bb9a79a","source_identity":"ticket:autopilot-gate-readiness/RGC-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":4184,"payload_sha256":"f17329c88bbf56e2106ee16cb2a605a593fbaf1e3bbd904f81213ad27bb9a79a","schema":1,"source_digest":"sha256:f17329c88bbf56e2106ee16cb2a605a593fbaf1e3bbd904f81213ad27bb9a79a","source_identity":"ticket:autopilot-gate-readiness/RGC-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "RGC-01"
execution_mode: AFK
blocked_by: []
---

# Distinguish technical gates and reuse exact existing authority

## Artifact Graph
- Artifact ID: `artifact:autopilot-gate-readiness-rgc-01`
- Role: `ticket`
- Parent: [Gate readiness spec](../../specs/autopilot-gate-readiness.md)

## Parent Spec
[Gate readiness spec](../../specs/autopilot-gate-readiness.md), especially Decision, Invariants and External behavior.

## What to Build
Correct the runtime status projection that labels every gate as human, and provide the matching scoped operator procedure. Preserve the existing resolution mechanism and every historical gate. This is not an automatic recovery or authorization feature.

## Acceptance Criteria
- [ ] All open gate IDs have an accurately named accessor; the human accessor filters only persisted human-category gates.
- [ ] Applicable human gates yield `human-gated`, environment-only gates yield `environment-gated`, and other/mixed/unavailable classifications yield conservative `gated`; human takes precedence in mixed sets.
- [ ] Status retains all open gates/records in order and remains pure; barriers, dependencies and unrelated AFK readiness are unchanged.
- [ ] Owning guidance requires exact current cause, prerequisite evidence and original implementation/recovery scope before using the existing resolution path. It reuses a valid existing decision rather than demanding a duplicate prompt, without treating merge authority or category labels as recovery permission.
- [ ] Resolution regression proves recorded-stage reentry, unchanged uncompleted quality state and unrelated human gates. No fixture is called live authorization evidence.
- [ ] Historical generic reasons, ledger bytes and quality/provenance remain unchanged by reporting; no approval, migration or ledger-repair side effect is added.
- [ ] Documentation explains the new readiness values and intentionally corrected Python accessor semantics, with all stated non-goals intact.

## Frontier
Ready AFK. The user requested the runner correction and normal delivery. No subagents; compose review and QA inline and report shared context honestly. No new user decision is needed to correct this demonstrated projection bug. Any genuine runtime gate remains separate.

## Step-by-Step Implementation Plan
1. Reproduce the environment/human conflation on the clean base using disposable kernel fixtures; retain the observed result.
2. Correct accessors and readiness classification together; inspect every caller so public open-gate visibility never shrinks.
3. Add/update the owning operator procedure and status contract without adding a second authority or recovery system.
4. Add causal category, scope, ordering, replay, no-write and stage-reentry regressions; keep unrelated ready work and human decisions protected.
5. Simplify the candidate, then perform fresh review, causal QA, canonical verification and normal provider-gated delivery on the final CandidateRef.

## Testing Plan
- Kernel and CLI/status fixtures for environment versus human, mixed/run-scoped/closed/other gates, all-gate enumeration and unchanged scheduler behavior.
- Existing missing-reason, generic-reason replay, source/projection recovery and human-start/reopen regressions.
- Operator-guidance review for valid prior scope, merge-only scope, restored versus unattempted prerequisites, stale candidates and real human decisions.
- Focused documentation/static graph checks and selected forward scenarios; broader local tests only with explicit outcomes and finite bounds.
- No live BetShareMarket mutation, independent-review, full-suite, provider readiness, wiki merge, package installation or active Pi reload claim.

## Out of Scope
- New gate states, ledger migrations, technical-recovery commands, automatic approvals or grant stores.
- Structured stop-evidence validation and the Pi continuation/compaction adapter; these remain separate planned work.
- SW-06 historical decisions; completion provenance repairs already integrated; Windows Pi launcher implementation.
- Any edits to the original dirty checkout, installed package, real historical ledger or unrelated source.

```
