---
type: source
title: "Revalidate a changed provider-gated candidate"
identity_key: ticket:provider-gated-candidate-revalidation/PGR-01
identity_strength: stable
source_path: docs/tickets/provider-gated-candidate-revalidation/done/01-revalidate-provider-gated-candidate.md
source_digest: sha256:399e6d474b30e064f415d0aa0611e11f210f2ddba1d1cc7b7f0cae3e5bf69251
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-16
created_provenance: git-commit
disposition_changed: 2026-09-16
disposition_changed_provenance: git-rename
run_id: pgr03
---

# Revalidate a changed provider-gated candidate

Compiled from `docs/tickets/provider-gated-candidate-revalidation/done/01-revalidate-provider-gated-candidate.md`. Identity is `ticket:provider-gated-candidate-revalidation/PGR-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-16** via `git-commit`
- Disposition changed: **2026-09-16** via `git-rename`

## Graph

- Parent source: [[sources/artifact-provider-gated-candidate-revalidation]]

## Run

Completed under autopilot run `pgr03`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-provider-gated-candidate-revalidation-pgr-01.md","payload_bytes":4148,"payload_sha256":"399e6d474b30e064f415d0aa0611e11f210f2ddba1d1cc7b7f0cae3e5bf69251"}],"payload_bytes":4148,"payload_sha256":"399e6d474b30e064f415d0aa0611e11f210f2ddba1d1cc7b7f0cae3e5bf69251","schema":1,"source_digest":"sha256:399e6d474b30e064f415d0aa0611e11f210f2ddba1d1cc7b7f0cae3e5bf69251","source_identity":"ticket:provider-gated-candidate-revalidation/PGR-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":4148,"payload_sha256":"399e6d474b30e064f415d0aa0611e11f210f2ddba1d1cc7b7f0cae3e5bf69251","schema":1,"source_digest":"sha256:399e6d474b30e064f415d0aa0611e11f210f2ddba1d1cc7b7f0cae3e5bf69251","source_identity":"ticket:provider-gated-candidate-revalidation/PGR-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "PGR-01"
execution_mode: AFK
blocked_by: []
---

# Revalidate a changed provider-gated candidate

## Artifact Graph

- Artifact ID: `artifact:pgr-01-provider-gated-revalidation`
- Role: `ticket`
- Parent: [Provider-gated candidate revalidation](../../specs/provider-gated-candidate-revalidation.md)

## Parent Spec

[Provider-gated candidate revalidation](../../specs/provider-gated-candidate-revalidation.md)

## What to Build

Implement the one bounded same-base, ignored-source recovery specified by the parent.
A single explicit `delivery-revalidate` request must re-enter final quality for an eligible
changed candidate before resume dispatches the old pending PR head. Share the eligibility
predicate between CLI/workflow, kernel and ledger replay. Preserve all existing provider,
source, lifecycle and merge-authority boundaries. The installed cache patch is a proposal,
not an implementation to accept without tests.

Allowed implementation scope: `ticket-autopilot/scripts/autopilot/{cli.py,
final_tree_workflow.py,kernel.py,ledger.py,reconciliation_gates.py}` and focused
`ticket-autopilot/tests/` regressions. Normal ticket completion artifacts belong to the runner.
Do not edit unrelated files, installed Pi packages, existing uncommitted source files,
credentials, settings, provider state or other runs.

## Acceptance Criteria

- [ ] A baseline regression demonstrates rejection of a changed, published, eligibility-gated
  ignored-source candidate through the real workflow/CLI and ledger boundary.
- [ ] Valid recovery supersedes only its stale provider gate and restarts review with fresh
  candidate-bound QA/verification requirements, a new artifact generation and no one-shot
  merge authorization; existing ignored-source completion remains intact.
- [ ] A single explicit valid recovery is processed before old-head merge work, without any
  provider mutation. Replaying it is idempotent and persisted history reloads correctly.
- [ ] Ineligible cases in the parent eligibility matrix remain fail-closed, including local
  HEAD/branch drift and already-begun merge; unrelated gates and observations are preserved.
- [ ] Focused regressions and the workflow forward matrix have observed results; any
  environment or pre-existing failure is reported rather than hidden.

## Frontier

Ready. One AFK slice; no dependencies. Merge remains manual and external delivery requires
its own applicable authority. Preserve both the installed cache patch and source checkout's
unrelated untracked files.

## Step-by-Step Implementation Plan

1. Build a focused published ignored-source fixture from canonical existing test helpers;
   demonstrate the failing explicit revalidation boundary on the source baseline.
2. Implement the shared restricted eligibility predicate and its exhaustive negative matrix.
3. Connect workflow Git/source guards, explicit resume priority, kernel state transition and
   exact ledger replay validation without broadening other resume events.
4. Run success, rejection, replay, source-disposition and zero-provider-mutation regressions;
   simplify only after GREEN and rerun affected checks.
5. Perform shared-context review, causal QA and canonical verification through the runner;
   stop at an explicit human/environment/delivery gate without inventing evidence.

## Testing Plan

Use unittest with temporary Git repositories and the existing fake GitHub provider; no live
PR mutation is needed for correctness evidence. Cover the full eligibility matrix with pure
predicate tests and successful/rejected replay through AtomicLedger. Run focused workflow,
CLI, kernel and ledger suites, the local quick test entry point and forward scenarios as
feasible, recording commands, counts and limitations at the final CandidateRef.

## Out of Scope

- Generic gate approval, administrative reopening, schema changes or compatibility shims.
- Tracked-source, docs-only, semantic base reconciliation or post-merge recovery.
- Automatic merge, publication of a PR without applicable authority, local Pi update/reload.
- Reusing cache test claims or modifying the cache in place.

```
