---
name: "ticket-autopilot"
description: "Drive a ticket folder AFK through deterministic scheduling, isolated implementation, evidence-backed quality gates, provider-neutral PRs, and explicit merge authorization."
---

# Ticket Autopilot

Owns: folder scheduling, run state, worktree/branch/PR orchestration, provider normalization, and guarded finalization. It does not implement tickets, review, QA plans, or claims.

The canonical Ticket Envelope is [version 1](references/ticket-envelope-v1.md). Verification artifact and claim rules belong to [verification-audit](../verification-audit/references/verification-record.md).

## Portable composition

invoke = execute one skill inline; compose = run skills in serial sequence while preserving ownership.
delegate = use a distinct host worker; independent = observed separate context; parallel = concurrent delegations.
Default ticket execution composes serially inline and requires zero AgentTool calls.
Delegate only with explicit user or applicable host authority; AFK, capability, and silence are not authority.

## AFK contract

- Continue ready, unrelated AFK work while ticket-scoped gates remain open.
- Create one isolated worktree per folder run for a serialized one-ticket mutation, with one branch/PR each.
- Stack only single-parent chains; a multi-parent join waits until every parent is integrated.
- Never invent credentials, provider capability, live evidence, approval, or merge authorization.
- Manual merge requires an explicit exact-head decision; autonomous merge requires an actor/evidence-bound run grant. `AFK`, access, and silence grant neither.
- CandidateRef v2 binds semantic trees/digest/version; a separate versioned record binds provider/PR/base/head/branch lineage.
- Semantic drift invalidates all evidence; lineage-only drift preserves it but clears one-shot merge authorization.
- Stop a ticket after the configured quality retry limit; keep other ready tickets moving.

## Public CLI

New runs use ledger schema `4` with quality and interaction/tool/time limits. Interactions default to `10`, reserving one each for `qa-execute` and `verify`; unset limits report `unavailable`. Invalid totals fail before creation. Explicit `migrate-run-lifecycle` validates schema-3 history, preserves its chain, and appends one audited v4 event.

`run --merge-policy autonomous --merge-actor <identity> --merge-evidence <durable-ref>` creates the sole standing grant; manual mode rejects it. It binds repository, run, ticket-set digest, provider, and policy. Before mutation, reread live exact head, checks/rules, approval, and mergeability, then merge atomically by expected head. Non-passing, simulated, queue-uncertain, or unsupported results gate. Only a proven GitHub queue may use `enqueuePullRequest(expectedHeadOid)` with intent-bound readback and no direct fallback.

`resume --events` accepts `leaf-result` for review, QA plan/execute, and verification. Each schema-3 result binds exact CandidateRef, phases, resources, and normalized `execution`; QA/verification add schema-1 `quality` scope, content-addressed evidence, and limits. Partial handoffs resume only on the same CandidateRef. Semantic drift starts a fresh bounded epoch while append-only history retains lifetime totals; same-candidate retries remain in the current epoch. `leaf-result` is the only channel for leaf context. The [`handoff`](../handoff/SKILL.md) skill bridges human sessions and is not a leaf-context channel.

For pre-epoch schema-4 runs, `revalidation-budget-repair` binds the exact tree, rebuilds matching progress, preserves retries, and appends one idempotent audit event. Use it for legacy false exhaustion; real exhaustion opens a durable `resource-budget` gate.

Delivery follows the versioned [PR-body handoff](references/delivery-pr-body-v1.md); route `render-required` to `explain-pr`, and require validated provider body/head readback for `pr-open`.

`verification-checkpoint` accepts expected tree, normalized inputs, and absolute `verification-audit` root, then uses its validator/reducer. The checkpoint module owns serialization, hashes, phase indexes, and resume—not evidence classes, gates, authority, or claims. `inspect_verification_checkpoints` reads the trusted prefix without adapters. Cache keys bind CandidateRef, leaf contract, scope, artifacts, command, and environment; exact hits cost no interaction, missing/corrupt entries rerun, and partial chains resume.

`docs-only-adopt` alone bypasses `execute-ticket`. A v1 request binds Ticket Envelope, digest, CandidateRef, paths, and scope. Only staged regular `docs/**/*.md` qualify; ticket/agent/generated/config/code/script/mixed paths, symlinks, submodules, ambiguity, or drift require `standard-path-required`. Content-addressed patch/kind/Markdown/graph/link checks use no leaf interaction, cap at `implementation-complete`, and recheck before guarded delivery/exact-head merge.

After durable integration, run separate `wiki-sync-v1` against a detached exact-head source; the ticket is provenance only and docs-only v1 never widens. External or internal-untracked output may apply directly. Internal-tracked output is a fresh `WikiSyncRef`/CandidateRef with no inherited verification, PR, or authority. `llm-wiki` never commits or delivers; persist its result separately and keep failure prominent/retryable without rewriting the ticket. Tracked PRs require exact-head `approve <run> --wiki-sync --ticket <id> --head-sha <head> --actor <id> --evidence <ref>` or a separate autonomous wiki grant; application grants never transfer.

`TICKET_AUTOPILOT_ROOT` is the absolute skill root, never repository cwd. The command surface is:

```bash
python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" --help
```

Commands are `plan`, `run`, `resume`, `status`, `pause`, `unpause`, `approve`, `abort`, `cleanup`, `ticket-hold`, `ticket-cancel`, `ticket-reopen-request`, `ticket-reopen`, `migrate-run-lifecycle`, `ticket-parse`, `ticket-emit`, `ticket-list`, `artifact-audit`, and `migrate`; use `<command> --help`. `ticket-list` is provider-free/read-only schema 2 and reports disposition, lifecycle, readiness/causes, malformed/duplicate tickets, dependency gaps, and cycles. `artifact-audit` is provider-free/read-only schema 1; it separates errors, legacy warnings, unreferenced candidates, and migration work, and never rewrites artifacts.

`pause` is run-scoped. Hold/cancel require identity, reason, and durable authority. Reopen is request→human `approve`→apply: it consumes only the matching passed gate and invalidates candidate-through-merge state. Approval is durable human authority, not caller authentication. Provider/Git/delivery boundaries recheck pause, disposition, source path, and digest; manual out-of-band TOCTOU remains possible.

## Scheduler flow

1. Accept only base-clean tracked or fully ignored in-repository tickets. Before worktree creation, snapshot canonical content under Git common state and bind mode/digest; resume never reparses caller files, and ignored completion stays outside the PR.
2. Parse through the canonical CLI; reject unsupported schema, duplicate IDs, dependency gaps, and cycles. Migration is explicit, never fallback.
3. Compute the ready frontier deterministically. Held/canceled tickets are unschedulable and
   block descendants without cascade; a HITL gate does not freeze unrelated AFK tickets.
4. Select one ready ticket and invoke `execute-ticket` with normalized envelope, source artifact reference, body, CandidateRef, retry limit, and scope unless explicit validated `docs-only-adopt` applies. Never infer docs-only eligibility. Finish its serialized mutation and state transition first.
5. Receive implementation, review findings, QA plan/results, and a validated Verification
   Record. Reject incomplete or stale handoffs; do not reinterpret their claim ceiling.
6. After quality passes, freeze, commit, and push only ticket-owned files, then follow the PR-body handoff. Gate failures; record `pr-open` only after provider body/head validation.
7. Record `pr-open` separately from `integrated`. Normal approvals follow the immediate,
   resumable [merge critical path v1](references/merge-critical-path-v1.md). In explicitly
   granted autonomous runs, re-establish fresh eligibility before every mutation attempt
   and reuse that same exact-head path without a per-PR prompt.
8. In one idempotent `delivery`, guarded-push, read back to `pr-open`/gated, and complete only after integration.
9. After a parent integrates, `reconcile` derives Git trees/head, preserves evidence only for
   equal trees, archives superseded attempts, and refreshes any advancing target before push.
   Semantic drift revalidates in a fresh bounded epoch; refuse refresh after provider mutation.

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

`status` schema 2 exposes authoritative lifecycle, outcomes, readiness, gates, progress,
budgets/totals, CandidateRef invalidations, source/delivery state, grants, and exact heads.
Repeated reads are pure projections: they do not append heartbeats or consume budget.

Report each ticket as ready, active, gated, review-exhausted, PR-open, integrated, or
failed. Include PR links and observed head SHAs, evidence ceilings, open human/provider
gates, and the next unblocked frontier. Do not overstate completion.
