# Bounded Ticket-Autopilot Leaves Prototype

## Prototype Frame

- **Question:** Can budget accounting, mandatory reservations, progress heartbeats, and
  partial leaf handoffs be deterministic and resumable without reusing stale evidence?
- **Branch:** Logic. The uncertainty is a state-machine and persistence contract, not UI.
- **Assumption:** The scheduler can persist normalized leaf results but host tool-call and
  wall-time telemetry may be unavailable.
- **Useful result:** Replay continues only missing work, mandatory QA/verification capacity
  survives review pressure, and a changed `CandidateRef` fails closed.

This directory is disposable. Keep the learned contract; production tickets should replace
the model rather than import it.

## Run

```bash
python3 -B -m unittest discover \
  -s docs/prototypes/bounded-ticket-autopilot-leaves -p 'test_*.py'

python3 -B docs/prototypes/bounded-ticket-autopilot-leaves/runner.py
```

## Answer

The model supports the bounded protocol without weakening D6:

- quality failures and leaf interactions are independent counters;
- ten total leaf interactions with one reserved QA execution and one reserved verification
  interaction reproduce the pressure in issue #9 while preventing review from consuming the
  last mandatory slots;
- tool-call and wall-time limits can be hard only when configured with real host telemetry;
  otherwise reports say `unavailable`;
- a versioned partial handoff round-trips expected/inspected scope, commands, findings,
  remaining work, phase, stop reason, and exact `CandidateRef`;
- identical progress events are idempotent and phase/count regression fails;
- resumption returns only declared remaining work for the same candidate;
- candidate drift rejects the handoff instead of attempting selective reuse.

## Production Recommendation

- Keep `max_quality_failures=3`.
- Add `max_leaf_interactions=10`, constrained to `3..100`.
- Reserve one interaction for `qa-execute` and one for `verify`; reject configurations that
  leave no non-mandatory interaction.
- Add optional positive `max_leaf_tool_calls` and `max_leaf_wall_time_ms`. Default them to
  `null` and report enforcement as `unavailable` until the host supplies trustworthy
  telemetry.
- Use leaf-result schema `3` and preserve CandidateRef contract version `1`. Schema `3`
  persists the owning leaf stage, its exact canonical phase contract, and the ordered
  suffix still required after the last completed phase.
- Bump the persisted run ledger to schema `2` for the new fields/events.
- Do not migrate implicitly. Schema-1 active runs must fail with an explicit
  migration-or-new-run message. An explicit migrator is separate opt-in compatibility work;
  it is not required by the clean target state.

## Keep

- Orthogonal budget arithmetic and mandatory reservation rule.
- Versioned complete/partial handoff with exact frozen scope.
- Monotonic idempotent progress events.
- Fail-closed ledger and CandidateRef version boundaries.

## Discard

- All code in this directory after production tickets encode the accepted contracts.
- Any idea of treating a heartbeat, cache hit, timeout, or partial scope as a passing gate.

## Review Amendments

The frozen-candidate review exposed four gaps and the prototype now models them
directly:

- the ledger, progress log/events, and leaf handoff all persist and validate the same
  exact `CandidateRef`, owning stage, and canonical phase contract;
- ledger schema `2` round-trips evolved interaction/resource counters, reservation
  accounting, progress events, and nullable candidate-bound continuation state;
- persisted interaction history is replayed through mandatory-capacity admission, raw
  reservation mappings cannot default during restoration, and the handoff phase must
  match the latest progress event;
- the latest budget interaction must match the progress/handoff stage, and complete
  mandatory handoffs require the corresponding completed reservation;
- `scope.files_remaining` is ordered structural data and must equal expected scope minus
  inspected scope; `stage` and `phase_contract` prevent a leaf from claiming another
  leaf's phases, and `phases_remaining` is the ordered contract suffix after
  `progress_phase`; human-readable continuation actions are derived from those fields;
- configuration accepts exactly one reserved interaction for each of `qa-execute` and
  `verify`;
- quality becomes terminal when `failures >= max_quality_failures`, while resource
  exhaustion remains a distinct exception and cause.

The timeout scenario now reaches 500 ms through admitted work, attempts a further 1 ms,
observes the actual `wall-time-budget` rejection, and serializes the resulting partial
handoff. A separate verification-stage scenario interrupts after every file is inspected,
restores the remaining `bundle-reduced` and `handoff-ready` checkpoints, admits a second
budgeted verification interaction with the one remaining tool call, completes the
mandatory reservation, and finishes without repeating inspection. Unconfigured tool-call
or wall-time telemetry is serialized with `enforcement: unavailable`; configured limits
use `enforcement: hard`. The suite contains 36 unit tests plus seven simulated scenarios.

## Remaining Uncertainty

- The production runner does not yet observe leaf tool calls or elapsed time directly.
- Cross-CandidateRef reuse remains a separate HITL decision after same-candidate caching is
  measured.
