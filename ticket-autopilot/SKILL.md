---
name: "ticket-autopilot"
description: "Drive a ticket folder AFK through deterministic scheduling, isolated implementation, independent quality gates, provider-neutral PRs, and explicit merge authorization."
---

# Ticket Autopilot

Owns: folder scheduling, run state, worktree/branch/PR orchestration, provider normalization, and guarded finalization. It does not implement tickets, review, QA plans, or claims.

The canonical Ticket Envelope is [version 1](references/ticket-envelope-v1.md). Verification artifact and claim rules belong to [verification-audit](../verification-audit/references/verification-record.md).

## AFK contract

- Continue ready, unrelated AFK work while ticket-scoped gates remain open.
- Create one isolated worktree per folder run. Reuse it for a serialized one-ticket mutation,
  with a distinct branch and PR per ticket.
- Stack only single-parent chains. A multi-parent join waits until every parent is
  integrated.
- Never invent credentials, provider capability, live evidence, approval, or merge
  authorization.
- Manual merge is the default and requires an explicit human decision bound to the
  observed PR head SHA. Autonomous merge exists only for a run created with an explicit,
  actor/evidence-bound grant; `AFK`, credentials, write access, and silence never grant it.
- CandidateRef v2 binds base/candidate trees, ticket digest, and version; provider/PR/
  base/head/branch use a separate versioned delivery-lineage record.
- Semantic drift invalidates all evidence; lineage-only drift preserves it but clears
  one-shot merge authorization.
- Stop a ticket after the configured quality retry limit; keep other ready tickets moving.

## Public CLI

New runs use ledger schema `3` and accept quality, interaction, tool-call, and wall-time limits.
Interactions default to `10`, reserving one each for `qa-execute` and `verify`; optional
tool/time limits report `unavailable` unless configured.
Invalid totals fail before the ledger is created. Older active ledgers and CandidateRef
v1 records are never silently reinterpreted; start a new run or invoke a separately
validated, explicit migration when one exists.

`run --merge-policy autonomous --merge-actor <identity> --merge-evidence <durable-ref>`
creates the only standing merge grant. The default `--merge-policy manual` rejects grant
arguments. The grant is immutable and bound to repository, run, ticket snapshot digest,
provider, and policy version. Every autonomous attempt still performs live current-head,
checks/policies, approval, and mergeability readback before the atomic expected-head merge;
GitHub check rollups and active branch rules are normalized into an exact-head receipt.
Pending, failed, unknown, simulated, queue-uncertain, or unsupported results gate. A proven
GitHub merge queue uses `enqueuePullRequest(expectedHeadOid)` with intent-bound readback;
it never falls back to a direct or unpinned merge.

The `resume --events` contract accepts `leaf-result` for review, QA planning, QA execution,
and verification. Every result carries schema-3 handoff data, the exact CandidateRef, its
canonical phase contract, and observed resource deltas. QA and verification results also
carry schema-1 `quality` data with causal scope, content-addressed evidence references, and limitations. A partial handoff remains non-passing and resumes only for the same
CandidateRef. Candidate drift clears every semantic leaf artifact and progress
record while preserving consumed resource accounting.

Delivery follows the versioned [PR-body handoff](references/delivery-pr-body-v1.md); route `render-required` to `explain-pr`, and require validated provider body/head readback for `pr-open`.

For verification, `resume --events` `verification-checkpoint` accepts the expected tree OID,
normalized inputs, and an absolute `verification-audit` skill root. It invokes the checkpoint
module with that skill's validator/reducer. The module owns serialization, content hashes,
phase indexes, and resume—not evidence classification, gates, boundary authority, or claims.
`inspect_verification_checkpoints` projects the trusted prefix without executing adapters.
Cache keys bind CandidateRef, leaf contract, scope, artifact hashes, command and environment;
exact hits cost no interaction, while missing/corrupt entries rerun and partial chains resume.

`TICKET_AUTOPILOT_ROOT` is the absolute skill root resolved from the catalog or this
`SKILL.md`, never repository cwd. The authoritative command surface is:

```bash
python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" --help
```

It exposes `plan`, `run`, `resume`, `status`, `approve`, `abort`, `cleanup`, `ticket-parse`,
`ticket-emit`, `ticket-list`, and `migrate`; use `<command> --help` for syntax. Migration is explicit. Never
hand-maintain a parser or use provider commands outside the capability-negotiated adapters.

`ticket-list [root] [--state <state>] [--json]` is the provider-free, read-only repository
inventory. It discovers canonical ticket folders below the explicit root, accepts folders
containing only `done/` tickets, derives disposition and readiness, and reports malformed
files, folder-local duplicate IDs, missing dependencies, and cycles as diagnostics. Its
JSON data uses inventory schema `1`; the default view is deterministic human-readable text.

## Scheduler flow

1. Accept only base-clean tracked or fully Git-ignored in-repository tickets, snapshot their
   canonical content under Git common state, and bind source mode/digest before worktree
   creation; resume never reparses caller files and ignored completion stays outside the PR.
2. Parse every ticket through the canonical CLI. Reject unsupported schema versions,
   duplicate IDs, missing dependencies, and cycles. Migration is a separate explicit
   command, never an implicit fallback.
3. Compute the ready frontier deterministically. A HITL start requirement opens a
   ticket-scoped gate; it does not freeze unrelated AFK tickets.
4. Select one ready ticket, switch the run worktree to its branch, and delegate one attempt
   to `execute-ticket` with its envelope, source artifact reference, body, CandidateRef, retry limit, and scope.
   Do not begin another ticket mutation until its mutation and state transition finish.
5. Receive implementation, review findings, QA plan/results, and a validated Verification
   Record. Reject incomplete or stale handoffs; do not reinterpret their claim ceiling.
6. When quality passes, freeze, commit, and push only ticket-owned files, then follow the PR-body handoff.
   Gate every failed phase; record `pr-open` only after canonical validation of provider-read body/head.
7. Record `pr-open` separately from `integrated`. Normal approvals follow the immediate,
   resumable [merge critical path v1](references/merge-critical-path-v1.md). In explicitly
   granted autonomous runs, re-establish fresh eligibility before every mutation attempt
   and reuse that same exact-head path without a per-PR prompt.
8. In one idempotent `delivery`, guarded-push, read back until `pr-open`/gated, and complete only after integration.
9. After a parent integrates, `reconcile` derives trees/head from Git: equality preserves
   leaf evidence, supersedes old-head merge receipts, and rerenders/readbacks the body; drift revalidates.

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

`status` exposes configured, consumed, remaining, and reserved budgets, progress phase, handoff health,
interaction/tool/time totals, CandidateRef invalidations, and unavailable host
metrics explicitly, plus source mode, manifest digest, completion effect, and drift gates.
It also exposes merge policy, immutable grant scope, current eligibility receipts, exact
head, checks/policies, merge phase, and gates.
Repeated reads are pure projections: they do not append heartbeats or consume budget.

Report each ticket as ready, active, gated, review-exhausted, PR-open, integrated, or
failed. Include PR links and observed head SHAs, evidence ceilings, open human/provider
gates, and the next unblocked frontier. Do not overstate completion.
