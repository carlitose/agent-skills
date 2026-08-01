---
name: "ticket-autopilot"
description: "Drive a ticket folder AFK through deterministic scheduling, isolated implementation, independent quality gates, provider-neutral PRs, and explicit merge authorization."
---

# Ticket Autopilot

Owns: folder scheduling, run state, worktree/branch/PR orchestration, provider
normalization, and guarded finalization. It does not implement tickets, perform review,
write QA plans, or decide verification claims.

The canonical Ticket Envelope is
[version 1](references/ticket-envelope-v1.md). The verification artifact and claim rules
are owned by
[verification-audit](../verification-audit/references/verification-record.md).

## AFK contract

- Continue ready, unrelated AFK work while ticket-scoped gates remain open.
- Create one isolated worktree per folder run. Reuse it for a serialized one-ticket mutation,
  with a distinct branch and PR per ticket.
- Stack only single-parent chains. A multi-parent join waits until every parent is
  integrated.
- Never invent credentials, provider capability, live evidence, approval, or merge
  authorization.
- Never auto-merge. A merge requires an explicit human decision bound to the observed PR
  head SHA.
- A changed candidate invalidates review, QA execution evidence, verification, and merge
  authorization for the prior CandidateRef.
- Stop a ticket after the configured quality retry limit; keep other ready tickets moving.

## Public CLI

New runs use ledger schema `2` and accept orthogonal limits:
`--max-quality-failures`, `--max-leaf-interactions`,
`--max-leaf-tool-calls`, and `--max-leaf-wall-time`. Interaction limits default
to `10` and reserve exactly one turn for `qa-execute` plus one for `verify`.
Optional tool-call and wall-time limits report `unavailable` unless configured.
Invalid totals fail before the ledger is created. Schema-1 active ledgers are
never silently reinterpreted; start a new run or invoke a separately validated,
explicit migration when one exists.

The `resume --events` contract accepts `leaf-result` for review, QA planning,
QA execution, and verification. Every result carries schema-3 handoff data,
the exact CandidateRef, its canonical phase contract, and observed resource
deltas. QA and verification results also carry schema-1 `quality` data with
causal scope, content-addressed evidence references, and explicit limitations.
A partial handoff remains non-passing and resumes only for the same
CandidateRef. Candidate drift clears every semantic leaf artifact and progress
record while preserving consumed resource accounting.

Delivery follows the versioned [PR-body handoff](references/delivery-pr-body-v1.md); route `render-required` to `explain-pr`, and require validated provider body/head readback for `pr-open`.

For verification, the `resume --events` `verification-checkpoint` operation accepts the
expected tree OID, normalized semantic inputs, and an explicit absolute
`verification-audit` skill root. It invokes the content-addressed checkpoint module with
that skill's canonical validator/reducer as injected adapters. The checkpoint module owns
only canonical serialization, content hashes, monotonic phase indexes, and resume. It never
classifies evidence, resolves gates, authorizes a boundary, or raises a claim. Call
`inspect_verification_checkpoints` to project the trusted completed prefix
without executing adapters. Cache keys bind CandidateRef, leaf contract, scope, artifact
hashes, command and environment identity; status reports hits, misses, avoided commands, and
limits. Exact hits cost no interaction; missing/corrupt entries rerun and partial chains resume.

`TICKET_AUTOPILOT_ROOT` means the absolute skill root resolved from the available skill
catalog or from this `SKILL.md` location. Never derive it from repository cwd. The
authoritative command surface is:

```bash
python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" --help
```

It exposes `plan`, `run`, `resume`, `status`, `approve`, `abort`, `cleanup`,
`ticket-parse`, `ticket-emit`, and `migrate`; use `<command> --help` as the authoritative
syntax. Migration is explicit. Never hand-maintain a second parser or serializer. Use
provider commands only through the normalized GitHub or Azure DevOps adapter selected by
capability negotiation.

## Scheduler flow

1. Require a clean enough source tree to preserve unrelated user changes. Record the
   source SHA, create the run ledger under Git common state, and create the run's single
   isolated worktree.
2. Parse every ticket through the canonical CLI. Reject unsupported schema versions,
   duplicate IDs, missing dependencies, and cycles. Migration is a separate explicit
   command, never an implicit fallback.
3. Compute the ready frontier deterministically. A HITL start requirement opens a
   ticket-scoped gate; it does not freeze unrelated AFK tickets.
4. Select one ready ticket, switch the run worktree to its branch, and delegate the
   one-ticket loop to `execute-ticket` exactly once per attempt. Give it the normalized
   envelope, source artifact reference, body, CandidateRef, retry limit, and allowed
   scope. Do not begin another ticket mutation until the current mutation and state
   transition finish.
5. Receive implementation, review findings, QA plan/results, and a validated Verification
   Record. Reject incomplete or stale handoffs; do not reinterpret their claim ceiling.
6. When quality passes, freeze, commit, and push only ticket-owned files, then follow the PR-body handoff.
   Gate every failed phase; record `pr-open` only after canonical validation of provider-read body/head.
7. Record `pr-open` separately from `integrated`. Normal approvals follow the immediate,
   resumable [merge critical path v1](references/merge-critical-path-v1.md).
8. In one idempotent `delivery`, commit, guarded-push, and read back the PR until `pr-open`
   or a gate. Only provider-environment gates auto-resume; complete only after integration.

## Component boundaries

- `execute-ticket`: implementation and ticket-local quality loop; no commit, push, PR, or
  run-state mutation.
- `code-simplification`, `code-review`, `qa-test-plan`, and `verification-audit`: leaf
  workers composed inside `execute-ticket`, not directly by the folder scheduler.
- `explain-pr`: deterministic PR-body rendering used by finalization after a validated
  handoff.

Keep scheduler mutations serialized: at most one active mutation may affect a ticket
CandidateRef, and call the folder finalizer exactly once through its idempotent guard.

For workflow-family releases, run `scripts/forward_test.py --output <artifact.json>`. Use
`--list` to inspect its raw scenario prompts without executing them. Treat the report as local
unit/integration evidence only; its recorded limitations remain claim gates for provider or
environment behavior that was not observed live.

## Final report

`status` and final reports expose configured, consumed, remaining, and reserved
budgets per ticket, plus the last durable progress phase, handoff health,
interaction/tool/time totals, CandidateRef invalidations, and unavailable host
metrics explicitly. Repeated reads are pure projections: they do not append
heartbeats or consume budget.

Report each ticket as ready, active, gated, review-exhausted, PR-open, integrated, or
failed. Include PR links and observed head SHAs, evidence ceilings, open human/provider
gates, and the next unblocked frontier. Do not overstate completion.
