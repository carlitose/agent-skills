---
type: source
title: "Prove a lifecycle-only status transaction"
identity_key: ticket:lightweight-ticket-status-change/TSC-01
identity_strength: stable
source_path: docs/tickets/lightweight-ticket-status-change/done/01-prove-lifecycle-only-status-transaction.md
source_digest: sha256:54050e2b687fb7bbe8ecaf674456d57cbdf2b5033643e3f06f34e6969a924aca
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-31
created_provenance: git-commit
disposition_changed: 2026-09-01
disposition_changed_provenance: git-rename
run_id: lightweight-ticket-status-change-v2-20260831
---

# Prove a lifecycle-only status transaction

Compiled from `docs/tickets/lightweight-ticket-status-change/done/01-prove-lifecycle-only-status-transaction.md`. Identity is `ticket:lightweight-ticket-status-change/TSC-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-31** via `git-commit`
- Disposition changed: **2026-09-01** via `git-rename`

## Graph

- Parent source: [[sources/artifact-lightweight-ticket-status-change-wayfinder]]

## Run

Completed under autopilot run `lightweight-ticket-status-change-v2-20260831`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-lightweight-ticket-status-change-tsc-01.md","payload_bytes":3173,"payload_sha256":"54050e2b687fb7bbe8ecaf674456d57cbdf2b5033643e3f06f34e6969a924aca"}],"payload_bytes":3173,"payload_sha256":"54050e2b687fb7bbe8ecaf674456d57cbdf2b5033643e3f06f34e6969a924aca","schema":1,"source_digest":"sha256:54050e2b687fb7bbe8ecaf674456d57cbdf2b5033643e3f06f34e6969a924aca","source_identity":"ticket:lightweight-ticket-status-change/TSC-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3173,"payload_sha256":"54050e2b687fb7bbe8ecaf674456d57cbdf2b5033643e3f06f34e6969a924aca","schema":1,"source_digest":"sha256:54050e2b687fb7bbe8ecaf674456d57cbdf2b5033643e3f06f34e6969a924aca","source_identity":"ticket:lightweight-ticket-status-change/TSC-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "TSC-01"
execution_mode: AFK
blocked_by: []
---

# Prove a lifecycle-only status transaction

## Artifact Graph

- Artifact ID: `artifact:tsc-01-lifecycle-only-status-transaction-prototype`
- Role: `ticket`
- Parent: [Lightweight Ticket Status Changes](../../specs/lightweight-ticket-status-change-wayfinder.md)

## Parent Spec

[Lightweight Ticket Status Changes](../../specs/lightweight-ticket-status-change-wayfinder.md)

## What to Build

Build a throwaway, repository-local prototype that answers whether one lifecycle-only transaction can safely resolve an exact ticket, apply the existing administrative disposition primitive, isolate only the allowed source move and inbound-link repoints from unrelated active-candidate state, and recover across Git/ledger crash boundaries. Compare tracked and ignored sources, usable/missing/retired runs, and pending/active/gated/waiting execution states without changing any real project ticket.

## Acceptance Criteria

- [ ] Disposable fixtures cover tracked and ignored tickets with usable, missing, retired, and ambiguous run ownership.
- [ ] Pending, active, gated, and waiting execution states are observed against the existing transition matrix without changing its product semantics.
- [ ] A dirty target worktree and index cannot leak unrelated paths into the administrative candidate.
- [ ] The prototype records the minimum ordered lifecycle-intent, source-transition, candidate, commit, provider-delivery, merge, terminal-proof, and projection boundaries needed for exact replay.
- [ ] Crash/replay cases distinguish known non-mutation, ambiguous dispatch, provider `MERGED`, and fresh terminal-branch reachability.
- [ ] Tracked-source and ignored-source outcomes preserve their existing publication boundary.
- [ ] The result recommends one v1 transaction owner and seam, or explicitly keeps the capability at the map boundary if isolation cannot be proven.
- [ ] No production runner path, real project ticket, live provider object, authority record, or installed skill is mutated by the prototype.

## Frontier

Ready for AFK throwaway exploration. No human disposition, merge, issue-publication, or live-provider authority is required.

## Step-by-Step Implementation Plan

1. Model the existing source, ledger, Git, provider, and terminal-proof boundaries with disposable fixtures.
2. Exercise the lifecycle/run/state matrix and exact target resolution failures.
3. Inject unrelated dirty worktree/index state and prove candidate allowlist isolation.
4. Inject crashes at each durable boundary and record replay requirements.
5. Write the recommendation and causal test evidence under `docs/prototypes/`.

## Testing Plan

Use only temporary repositories, fake providers, and fixture ledgers. Run the prototype's focused causal tests plus repository documentation/static checks. Do not call a live provider.

## Out of Scope

- Production implementation of `change-status-ticket`.
- Any real ticket hold, cancellation, reopen request, or reopen.
- Changing lifecycle vocabulary or transition semantics.
- Live GitHub issue, PR, merge, wiki, Pi-sync, or publication operations.

```
