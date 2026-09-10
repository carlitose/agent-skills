---
type: source
title: "Add an opt-in autonomous merge grant"
identity_key: ticket:ticket-autopilot-delivery-merge/06
identity_strength: stable
source_path: docs/tickets/ticket-autopilot-delivery-merge/done/06-add-opt-in-autonomous-merge-grant.md
source_digest: sha256:cfc42b2aab7cc9ef212cb70ba40f7d8741e2d6b09dd06aeda6fb1f1635f8514b
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-05
created_provenance: git-commit
disposition_changed: 2026-08-06
disposition_changed_provenance: git-rename
run_id: issues21-23-autonomous-stack-v6-20260806
---

# Add an opt-in autonomous merge grant

Compiled from `docs/tickets/ticket-autopilot-delivery-merge/done/06-add-opt-in-autonomous-merge-grant.md`. Identity is `ticket:ticket-autopilot-delivery-merge/06`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-05** via `git-commit`
- Disposition changed: **2026-08-06** via `git-rename`

## Graph

- Blocked by: [[sources/ticket-ticket-autopilot-delivery-merge-05]] — `ticket:ticket-autopilot-delivery-merge/05`

## Run

Completed under autopilot run `issues21-23-autonomous-stack-v6-20260806`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[3],"status":"present"},"exclusions":{"headings":[7],"status":"present"},"frontier":{"headings":[4],"status":"present"},"intent":{"headings":[2],"status":"present"},"testing":{"headings":[6],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-ticket-autopilot-delivery-merge-06.md","payload_bytes":4378,"payload_sha256":"cfc42b2aab7cc9ef212cb70ba40f7d8741e2d6b09dd06aeda6fb1f1635f8514b"}],"payload_bytes":4378,"payload_sha256":"cfc42b2aab7cc9ef212cb70ba40f7d8741e2d6b09dd06aeda6fb1f1635f8514b","schema":1,"source_digest":"sha256:cfc42b2aab7cc9ef212cb70ba40f7d8741e2d6b09dd06aeda6fb1f1635f8514b","source_identity":"ticket:ticket-autopilot-delivery-merge/06","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 2: What to Build |
| acceptance | 3: Acceptance Criteria |
| testing | 6: Testing Plan |
| frontier | 4: Frontier |
| exclusions | 7: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":4378,"payload_sha256":"cfc42b2aab7cc9ef212cb70ba40f7d8741e2d6b09dd06aeda6fb1f1635f8514b","schema":1,"source_digest":"sha256:cfc42b2aab7cc9ef212cb70ba40f7d8741e2d6b09dd06aeda6fb1f1635f8514b","source_identity":"ticket:ticket-autopilot-delivery-merge/06"} -->
```markdown
---
ticket_schema: 1
ticket_id: "06"
execution_mode: AFK
blocked_by:
  - "05"
---

# Add an opt-in autonomous merge grant

## Parent Spec

[ticket-autopilot-autonomous-stacked-delivery.md](../../specs/ticket-autopilot-autonomous-stacked-delivery.md)

## What to Build

Resolve [GitHub issue #23](https://github.com/carlitose/agent-skills/issues/23). Add a
manual-by-default run policy that lets a human explicitly grant `ticket-autopilot` authority
to merge every eligible PR in that run without a new per-PR prompt. Apply the grant only
through fresh provider eligibility checks and the existing exact-head, replay-safe merge
critical path.

## Acceptance Criteria

- [ ] Run configuration exposes `manual` and `autonomous` merge policies; `manual` remains
      the default and current per-head approval behavior remains intact.
- [ ] Autonomous mode requires explicit actor and durable evidence and records a versioned
      grant bound to repository identity, run ID, ticket-set digest, provider, and policy.
- [ ] `AFK`, credentials, write access, or an absent response never creates or widens a
      merge grant.
- [ ] Before each merge, the runner performs live PR/head readback, confirms the exact
      semantic candidate is fully validated, observes required checks/policies, and invokes
      only the provider's atomic expected-head operation for that observed head.
- [ ] GitHub uses the normalized `--match-head-commit` capability without `--admin`; pending
      checks wait/gate, failed checks gate, and unproven merge-queue/auto-merge head pinning
      never falls back to an unguarded merge.
- [ ] Providers without an atomic expected-head capability remain explicitly gated rather
      than simulating or weakening autonomous behavior.
- [ ] Provider mutation and readback use keyed intent/applied receipts; crashes before
      mutation, after mutation, and before ledger save converge without a second merge.
- [ ] After a parent integrates, a semantic-equivalent child reconcile keeps the run grant,
      rechecks the new head, and continues the stacked chain without another human prompt;
      semantic drift first forces full revalidation.
- [ ] Status/final reports expose merge policy, grant scope, current eligibility, exact head,
      checks/policy state, merge phase, receipts, and gates without mutating history.
- [ ] Tests cover manual parity, missing/forged grants, stale heads, pending/failed checks,
      unsupported providers, stack progression, semantic drift, queue uncertainty, and
      idempotent crash recovery.

## Frontier

Dependency-blocked by ticket `05`. Autonomous progression must consume the corrected
semantic-versus-lineage identity so downstream stack SHA churn does not trigger redundant
quality loops or inherit stale head authority.

## Step-by-Step Implementation Plan

1. Define and validate merge-policy/grant contracts at plan/run initialization; reject
   partial, contradictory, or changed grant identity on resume.
2. Persist the grant and project it through the kernel, ledger validator, status, and final
   report while keeping manual head authorization as a distinct mode.
3. Refactor merge eligibility into one provider-neutral deterministic reducer over semantic
   validation, live PR/head state, checks/policies, provider capability, and grant scope.
4. Drive eligible autonomous tickets through ticket `02`'s exact-head merge critical path;
   preserve intent/applied/readback receipts and scheduler priority.
5. Connect integrated-parent reconciliation to the next child, rerun provider checks on its
   new head, and continue until a real gate or the folder is integrated.
6. Update the scheduler contract and add adversarial kernel, CLI, provider, ledger replay,
   Git stack, and forward tests.

## Testing Plan

Run ticket-autopilot kernel, CLI, ledger, provider, finalizer, skill-graph, and forward-test
suites. Use stateful fake providers for all crash windows and a three-ticket stack. Retain
live GitHub and provider merge-queue behavior as explicit evidence gates until observed in a
disposable repository.

## Out of Scope

- Administrator bypass, force merge, or disabling branch protection.
- Making autonomous mode the default.
- Treating provider auto-merge as exact-head-safe without a proven capability contract.
- Supporting a provider that cannot atomically reject a stale head.

```
