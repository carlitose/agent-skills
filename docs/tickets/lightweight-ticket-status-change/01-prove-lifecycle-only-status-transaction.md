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
