# Merge critical path v1

Normal runner merges begin only from a provider-read, validated `pr-open` delivery. The
human approval names the ticket and exact recorded head SHA; the command then holds the run
lock through fresh provider observation, durable authorization, guarded mutation, readback,
and ledger integration.

The ledger stores `merge-intent`, `merge-observation`, `merge-attempt`, `merge-mutation`,
`merge-readback`, and `merge-progress` delivery records. Every effect record carries the
same content-derived `intent_key`, provider, PR identity, and head SHA. `merge-progress`
also stores replay-safe start/update timestamps, phase, status, and any durable gate or
failure. Autonomous `merge-attempt` also binds the eligible direct/queue mode before the
provider call. Manual approval obtains the same exact-head live policy readback before
persisting its mode, so an ambiguous crash cannot switch mutation paths in either policy.
Status derives elapsed time without appending history.

If a queued attempt has neither a durable mutation receipt nor an observable queue entry,
replay gates the ambiguous dispatch instead of issuing another enqueue.

Recovery always observes the provider before deciding whether mutation remains:

- an exact open head with no accepted mutation may execute the expected-head merge;
- an exact merged head with the persisted runner authorization skips mutation and records
  integration;
- a changed head invalidates authorization before any merge command;
- a successful direct mutation whose readback remains open is gated and is never issued
  again;
- a successful queue mutation whose readback remains open stays `queued`; retries read the
  same exact-head queue entry without another mutation, and a missing prior entry or changed
  queue policy gates rather than re-enqueueing or falling back to direct merge;
- an ambiguous provider failure opens `provider-merge`; a later retry reads live state and
  converges without reissuing a merge that already succeeded.

An autonomous run grant replaces only the per-head human prompt. Before an open PR can
enter or re-enter the mutation phase, the runner reads the exact head, required
checks/policies, active base-branch rules, approvals, mergeability, and merge-state status
live. GitHub status rollups are normalized without depending on `gh pr checks --json`, and
the receipt is rejected unless its observed head matches the authorized delivery head. The
runner gates pending, failed, unknown, simulated, provider-incapable, or queue-uncertain
observations and never uses administrator bypass. A proven GitHub merge queue is entered
only through GraphQL `enqueuePullRequest(expectedHeadOid)`; its intent-bound entry is read
back before the call returns, response-loss recovery reads the entry, and replay never
falls back to direct merge. A retry while the PR remains open repeats eligibility checks.
If the exact PR is already merged after a lost response, a persisted autonomous
authorization plus exact-head merge-attempt receipt permits readback/integration recovery
without issuing a second mutation.

Autonomous stack order is dependency-closed: a child cannot enter merge eligibility until
its blockers are integrated and its delivery lineage is reconciled. Reconciliation archives
old-head merge receipts append-only, clears their active intent, and requires a fresh
`render-required` body bound literally to the new head. Retarget publishes base and body
together, reads both back, and revalidates them before fresh eligibility may merge the child.

While a runner authorization is pending and no real gate is open, scheduler readiness is
suppressed and `resume` advances this path before caller events. An explicit provider gate
restores fail-forward scheduling for unrelated tickets.

External reconciliation is a separate non-mutating path. `approve --external-merge`
reads the ledger-recorded PR in live mode and accepts only the exact recorded provider,
PR, merged head, and evidence class. One kernel transaction records the external human
authorization, immutable `external-reconciliation` receipt, provider observation, and
integration. It never invokes the provider merge operation. An exact replay returns the
stored receipt without another provider call or history event; a failed validation or
save leaves no partial authorization or integration.
