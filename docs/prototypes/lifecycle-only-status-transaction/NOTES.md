# Lifecycle-only status transaction prototype

## Prototype frame

- **Question:** Can one lifecycle-only transaction resolve an exact ticket, isolate its administrative source move from unrelated active-candidate state, and recover the Git/provider path without manufacturing an implementation quality loop?
- **Branch:** Logic. The uncertainty is transaction ownership, state ordering, isolation, and replay rather than UI.
- **Assumption:** A tracked status change is repository delivery even though it is not implementation; an ignored-source change remains external and unpublished.
- **Useful result:** One runnable fixture proves or disproves a concrete transaction owner and clean-candidate seam, while identifying any state that the current runner still cannot project safely.
- **Production successor:** [Change Status Ticket](../../specs/change-status-ticket.md) adopts the proved seam and preserves the unresolved barriers.

Run from the repository root:

```bash
python3 -B -m unittest discover \
  -s docs/prototypes/lifecycle-only-status-transaction \
  -p 'test_*.py' -v
```

The prototype is disposable. `model.py` is not a production runner path.

## Result

**Adopt a repository-owned lifecycle transaction and a dedicated clean administrative
worktree as the v1 seam. Do not make an arbitrary target run or its worktree own delivery.**

The answer is positive for candidate isolation and deterministic replay, with one explicit
production gap: the current run kernel accepts hold/cancel preflight only for `pending` and
`active`. It rejects `gated` and `waiting`, even though the accepted lifecycle decision
allows inactive administrative changes at a proved safe boundary. Production work must
add a repository-intent mutation barrier and an exact post-terminal run projection before
claiming those states; the first tracer must fail closed there until that behavior is
implemented and causally tested.

## What the fixtures proved

Eleven causal tests exercise only temporary repositories, in-memory fake providers, and
fixture ledgers.

### Exact target and transaction owner

- A unique usable schema-4 run is an optional **projection target**, not the transaction
  owner.
- Missing ownership and retired historical ownership use the same repository transaction;
  they do not require resurrecting or guessing a run.
- More than one usable matching owner fails closed.
- Public inputs accept only `open`, `on-hold`, or `canceled`. Hold/cancel require actor,
  reason, and durable authority; reopen additionally requires the exact passed human gate.

The durable identity should live under repository-common Ticket Autopilot state and bind
repository identity, ticket Artifact ID/path/digest, prior and target dispositions, actor,
reason, authority, source mode, target branch, and optional run projection.

### Existing state matrix

A fixture calls the production `Kernel.preflight_disposition_transition` directly:

| Execution state | Current kernel hold/cancel | Safe-boundary model |
| --- | --- | --- |
| `pending` | accepts | apply inactive |
| `active` | accepts | wait for the atomic effect, record stopped attempt, then apply |
| `gated` | rejects | preserve gate/evidence and apply only after a new tested projection seam exists |
| `waiting` | rejects | preserve attempt/evidence and apply only after a new tested projection seam exists |

An in-flight atomic effect always gates. No fixture interrupts or erases it. The model does
not silently normalize `gated`/`waiting` to `pending` and does not treat a gate as authority.

### Dirty-state isolation

The tracked fixture creates a target checkout with both staged and unstaged unrelated
changes, then creates a clean detached administrative worktree at the exact target SHA. It
runs the existing `transition_ticket_source` primitive there, repoints the inbound map, and
freezes exactly:

1. the old ticket path,
2. the new disposition path, and
3. deterministic inbound-link repoints.

Neither dirty target path enters the candidate. Adding one rogue path to the admin index
fails the exact-set allowlist. This proves that scanning or committing the target run
worktree is unnecessary and unsafe.

The ignored fixture runs the same receipted source primitive against an ignored folder.
Git sees no candidate; there is no commit, push, PR, merge, terminal-branch claim, tracked
completion projection, wiki operation, or publication. Its terminal outcome is explicitly
`external-unpublished`.

### Crash and replay boundaries

The existing source primitive is exercised with crashes both before the move and after the
move but before the applied receipt. Exact replay completes once and returns the same
receipt.

The tracked model persists and replays this order:

1. request validated;
2. repository lifecycle intent;
3. source receipt applied in the admin worktree;
4. exact allowlisted candidate frozen;
5. commit intent;
6. commit readback;
7. provider-delivery intent;
8. provider dispatch started;
9. exact PR readback;
10. independent merge decision (exact authority before mutation, or read-only external provenance);
11. provider `MERGED` readback;
12. fresh terminal-branch reachability;
13. repository receipt and optional usable-run projection;
14. complete.

A crash after a known non-mutation retries. A crash after a provider-dispatch marker never
redispatches; it allows only read-only reconciliation. Provider `MERGED` without terminal
reachability remains gated. Source, commit, provider, merge, and projection effects remain
single-shot across exact replay.

## Production shape to keep

TSC-02 should freeze these properties:

- **Owner:** one repository lifecycle transaction, independent of all implementation runs.
- **Isolation:** one clean admin worktree and an exact old-path/new-path/repoint allowlist;
  target-run index and worktree state are never candidate inputs.
- **Mutation barrier:** after authorized intent reaches a safe boundary, every owning run
  must consult the repository transaction before any new work, provider, or delivery effect.
- **Projection:** tracked source truth becomes final only after commit/provider readback,
  separate merge authorization, and terminal proof. A usable run receives an append-only
  disposition projection afterward; missing/retired ownership retains repository truth.
- **Ignored mode:** applied external receipt is terminal but unpublished; no tracked delivery
  or completion effect is inferred.
- **Replay:** intent precedes every ambiguous effect; exact readback, not redispatch, follows
  an armed provider/merge boundary.
- **Authority:** disposition, reopen, merge, publication, wiki, Pi, cleanup, and target-ticket
  implementation authorities remain separate.

## Production gaps to make explicit

1. The current lifecycle CLI requires an existing run and moves/stages in that run's
   worktree. It cannot be the public end-to-end lane.
2. Current mutation boundaries do not consume a repository-owned lifecycle intent. Active
   isolation therefore requires a new checked barrier, not merely a clean worktree.
3. Current ledger preflight rejects `gated` and `waiting`. Initial production behavior must
   gate those states until an append-only safe-boundary projection preserves their attempt
   and gate evidence.
4. A run worktree may remain on an old branch after terminal integration. Projection must
   validate the terminal source and repository receipt rather than pretending the old
   worktree already contains the merged path.
5. Ambiguous duplicate ticket identity or usable ownership, source drift, unexpected admin
   paths, missing merge authority, provider ambiguity, and missing terminal reachability all
   stop without strengthening the outcome.

## Keep, discard, and next work

- **Keep:** this recommendation, the state/order tables, and causal scenarios as inputs to
  TSC-02's production spec and tracer tickets.
- **Discard:** `model.py` and its fake provider after the production state machine has
  equivalent tests.
- **Do not promote directly:** none of the prototype code belongs in a skill or runner.
- **Next:** TSC-02 may specify the production capability and emit tracer tickets. It must
  preserve the gated/waiting gap rather than claiming the prototype changed current kernel
  support.

No real ticket source, provider object, authority record, installed skill, wiki, Pi checkout,
or live run ledger is mutated by this prototype.
