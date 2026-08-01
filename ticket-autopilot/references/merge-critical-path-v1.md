# Merge critical path v1

Normal runner merges begin only from a provider-read, validated `pr-open` delivery. The
human approval names the ticket and exact recorded head SHA; the command then holds the run
lock through fresh provider observation, durable authorization, guarded mutation, readback,
and ledger integration.

The ledger stores `merge-intent`, `merge-observation`, `merge-attempt`, `merge-mutation`,
`merge-readback`, and `merge-progress` delivery records. Every effect record carries the
same content-derived `intent_key`, provider, PR identity, and head SHA. `merge-progress`
also stores replay-safe start/update timestamps, phase, status, and any durable gate or
failure. Status derives elapsed time without appending history.

Recovery always observes the provider before deciding whether mutation remains:

- an exact open head with no accepted mutation may execute the expected-head merge;
- an exact merged head with the persisted runner authorization skips mutation and records
  integration;
- a changed head invalidates authorization before any merge command;
- a successful mutation whose readback remains open is gated and is never issued again;
- an ambiguous provider failure opens `provider-merge`; a later retry reads live state and
  converges without reissuing a merge that already succeeded.

While a runner authorization is pending and no real gate is open, scheduler readiness is
suppressed and `resume` advances this path before caller events. An explicit provider gate
restores fail-forward scheduling for unrelated tickets.
