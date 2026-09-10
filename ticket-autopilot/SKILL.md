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
For distinct workers, apply the [operating defaults](../ask-skills/OPERATING-DEFAULTS.md); record the requested scope and observed isolation.

## AFK contract

- Continue ready, unrelated AFK work while ticket-scoped gates remain open.
- Create one isolated worktree per folder run for a serialized one-ticket mutation, with one branch/PR each.
- Stack only single-parent chains; a multi-parent join waits until every parent is integrated.
- Treat provider `MERGED` as necessary but insufficient: derive the recursive root delivery base, freshly fetch it, and persist exact-head or explicit-merge-object ancestry before `integrated`.
- Never invent credentials, provider capability, live evidence, approval, or merge authorization.
- Manual merge requires an explicit exact-head decision; autonomous merge requires an actor/evidence-bound run grant. `AFK`, access, and silence grant neither.
- CandidateRef v2 binds semantic trees/digest/version; a separate versioned record binds provider/PR/base/head/branch lineage.
- Semantic drift invalidates all evidence; lineage-only drift preserves it but clears one-shot merge authorization.
- Stop a ticket after the configured quality retry limit; keep other ready tickets moving.

## Public CLI

New runs use ledger schema `4` with quality and interaction/tool/time limits. Interactions default to `10`, reserving one each for `qa-execute` and `verify`; unset limits report `unavailable`. Invalid totals fail before creation.

When importing a directory or bootstrapping private GitHub, load [bootstrap procedures](references/bootstrap.md) before inventory or publication; bootstrap authority grants no run or merge.

When adopting, aborting, cleaning up, or collecting worktrees, load [worktree procedures](references/worktrees.md); eligibility is not deletion authority.

When refreshing installed skills after durable integration, load [local Pi synchronization](references/local-pi-sync.md); require separate actor/evidence configuration and report `/reload` as still required.

When merging PRs, granting/revoking merge authority, migrating repository authority, or reconciling a changed PR base/head, load [merge and reconciliation procedures](references/merge-and-reconciliation.md) before acting.

Affirmative repository-wide “merge all”, “merge everything”, or “mergia tutto”: inspect `repository-autonomous-merge-status`. If absent, grant `--scope current-and-future-runs` with the human actor and durable affirmative message; preserve an exact active grant and fail closed on revoked, legacy, malformed, or contradictory state. Then invoke `merge-all --repo <repository>`; never request a caller-supplied PR head or narrow to one PR. Questions, quotes, negations, and ambiguous identity grant nothing. Merge authority does not unblock other gates or authorize conflict content, publication, cleanup, wiki, or Pi.

When projecting the final tracked tree or recovering an exact source-mode gate, load [final-tree procedures](references/final-tree-projection.md) before effects. New runs default to `--final-tree-mode enabled`; projection is not integration or authority.

`resume --events` accepts `leaf-result` for review, QA plan/execute, and verification. Each schema-3 result binds exact CandidateRef, phases, resources, and normalized `execution`; QA/verification add schema-1 `quality` scope, content-addressed evidence, and limits. Partial handoffs resume only on the same CandidateRef. Semantic drift starts a fresh bounded epoch while append-only history retains lifetime totals; same-candidate retries remain in the current epoch. `leaf-result` is the only channel for leaf context. The [`handoff`](../handoff/SKILL.md) skill bridges human sessions and is not a leaf-context channel. `stage` events with `result: "gated"` and `Kernel.record_stage(..., reason=...)` require a nonblank string `reason` before mutation. Outer whitespace is stripped; the remaining cause is persisted literally, without generated fallback text. Non-gated results need no reason. Never include credentials or private payloads in gate reasons or details.

For environment-stage blockers or uncertainty about a new human decision, load [gate readiness and existing authority](references/technical-gates.md). Reuse valid existing scope only after the cause is resolved; readiness labels alone grant nothing.

When migrating/retiring a legacy run, compacting its ledger, or repairing legacy false budget exhaustion, load [legacy recovery procedures](references/legacy-recovery.md); never hand-edit history or bypass real exhaustion.

Delivery follows the versioned [PR-body handoff](references/delivery-pr-body-v1.md); route `render-required` to `explain-pr`, and require validated provider body/head readback for `pr-open`.

`verification-checkpoint` accepts expected tree, normalized inputs, and absolute `verification-audit` root, then uses its validator/reducer. The checkpoint module owns serialization, hashes, phase indexes, and resume—not evidence classes, gates, authority, or claims. `inspect_verification_checkpoints` reads the trusted prefix without adapters. Cache keys bind CandidateRef, leaf contract, scope, artifacts, command, and environment; exact hits cost no interaction, missing/corrupt entries rerun, and partial chains resume.

`docs-only-adopt` alone bypasses `execute-ticket`. A v1 request binds Ticket Envelope, digest, CandidateRef, paths, and scope. Only staged regular `docs/**/*.md` qualify; ticket/agent/generated/config/code/script/mixed paths, symlinks, submodules, ambiguity, or drift require `standard-path-required`. Content-addressed patch/kind/Markdown/graph/link checks use no leaf interaction, cap at `implementation-complete`, and recheck before guarded delivery/exact-head merge.

When a ticket durably integrates or a wiki delivery needs retry, load [wiki delivery procedures](references/wiki-delivery.md). Run separate `wiki-sync-v1` on the exact head; record failures separately and never inherit ticket verification or merge authority.

When publishing or reconciling a runner-defect issue, load [issue-publication procedures](references/runner-defect-issues.md); require its separate authority, not a run or merge grant.

`TICKET_AUTOPILOT_ROOT` is the absolute skill root, never repository cwd. The command surface is:

```bash
python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" --help
```

Commands are `prepare-zero-to-autopilot`, `zero-to-autopilot`, `zero-to-autopilot-status`, `bootstrap-private-github`, `sync-local-pi`, `grant-repository-autonomous-merge`, `revoke-repository-autonomous-merge`, `repository-autonomous-merge-status`, `grant-repository-autonomous-reconciliation`, `revoke-repository-autonomous-reconciliation`, `repository-autonomous-reconciliation-status`, `migrate-repository-authority`, `merge-all`, `plan`, `run`, `worktree-owner-adopt`, `worktree-gc-plan`, `worktree-gc-apply`, `resume`, `status`, `wiki-delivery-retry-status`, `retry-wiki-delivery`, `pause`, `unpause`, `grant-autonomous-merge`, `grant-completion-projection`, `runner-defect-issue-grant`, `runner-defect-issue-revoke`, `runner-defect-issue-status`, `runner-defect-issue-escalate`, `approve`, `abort`, `cleanup`, `ticket-hold`, `ticket-cancel`, `ticket-reopen-request`, `ticket-reopen`, `migrate-run-lifecycle`, `compact-run-ledger`, `ticket-parse`, `ticket-emit`, `ticket-list`, `artifact-audit`, and `migrate`; use `<command> --help`. `ticket-list` is provider-free/read-only schema 2 and reports disposition, lifecycle, readiness/causes, malformed/duplicate tickets, dependency gaps, and cycles. `artifact-audit` is provider-free/read-only schema 1; it separates errors, legacy warnings, unreferenced candidates, and migration work, and never rewrites artifacts.

`pause` is run-scoped. Hold/cancel require identity, reason, and durable authority. Reopen is request→human `approve`→apply: it consumes only the matching passed gate and invalidates candidate-through-merge state. Approval is durable human authority, not caller authentication. Provider/Git/delivery boundaries recheck pause, disposition, source path, and digest; manual out-of-band TOCTOU remains possible.

## Scheduler flow

1. Accept only base-clean tracked or fully ignored in-repository tickets. Before worktree creation, snapshot canonical content under Git common state and bind mode/digest; resume never reparses caller files. Ignored completion stays outside the PR except for one separately granted, exact-digest, candidate-only canonical `done/` projection; source ownership and finalization remain external.
2. Parse through the canonical CLI; reject unsupported schema, duplicate IDs, dependency gaps, and cycles. Migration is explicit, never fallback.
3. Compute the ready frontier deterministically. Held/canceled tickets are unschedulable and
   block descendants without cascade; a HITL gate does not freeze unrelated AFK tickets.
4. Select one ready ticket and invoke `execute-ticket` with normalized envelope, source artifact reference, body, CandidateRef, retry limit, and scope unless explicit validated `docs-only-adopt` applies. Never infer docs-only eligibility. Finish its serialized mutation and state transition first.
5. Receive implementation and simplification, then either preserve the established full cycle or, for exact enabled tracked eligibility, persist and apply `I → D` before final quality. Run `review → qa-plan → qa-execute → verify → finalize` only for the active final CandidateRef. Reject incomplete, imported, or stale handoffs; do not reinterpret their claim ceiling.
6. After quality passes, freeze, commit, and push only ticket-owned files, then follow the PR-body handoff. Gate failures; record `pr-open` only after provider body/head validation.
7. Record `pr-open` separately from `integrated`. Normal approvals follow the immediate,
   resumable [merge critical path v1](references/merge-critical-path-v1.md). In explicitly
   granted autonomous runs, re-establish fresh eligibility before every mutation attempt
   and reuse that same exact-head path without a per-PR prompt. Every integration entry
   point also binds provider readback and delivery lineage to a fresh terminal SHA/tree,
   proving ancestry of the exact head or explicit provider merge commit; external readback
   retains distinct provenance and cannot authorize a merge mutation. If a provider already
   merged a different single-commit head, `integrate` may adopt it only when the recorded,
   observed, and provider-integration raw transitions are non-empty and byte-identical.
   Accept only a two-parent merge whose second parent is the observed head or its distinct
   same-base, same-tree single-parent integration copy. Persist and read back the versioned
   topology receipt before terminal proof; replay historical schema-1 two-parent receipts
   without rewrite. Patch ID, path-only equality, provider labels, final-tree similarity
   alone, multi-commit, general squash, queue rewrite, or path/blob/mode/parent drift fails.
8. In one idempotent `delivery`, guarded-push, read back to `pr-open`/gated, and complete only after integration.
9. After a parent terminally integrates or a recorded PR base advances, `reconcile` derives Git
   trees/head, preserves evidence only for equal trees, archives superseded attempts, and
   refreshes any advancing target before push. Parentless base advance uses delivery lineage;
   it never invents dependency ancestry.
   Semantic drift revalidates in a fresh bounded epoch; refuse refresh after provider mutation.
10. Only after an `agent-skills` ticket is durably integrated and a separate actor/evidence-bound local configuration exists, run `sync-local-pi` for that exact head. A local sync failure remains visible without rewriting integration; never infer authority or claim the active Pi session reloaded.

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
Repeated reads are pure projections: they do not append heartbeats or consume budget. `open_gates` retains its ordered IDs; `open_gate_records` adds `{"schema": 1, "records": [...]}` in the same order. Deep-copied records include `gate_id`, `ticket_id` (`null` for a run owner), `category`, `scope`, `kind`, `state`, `reason`, and existing `details`. Closed gates are omitted. Historical schema-4 generic reasons remain literal: no backfill, history rewrite, or approval is inferred.

Report each ticket as ready, active, gated, review-exhausted, PR-open, integrated, or
failed. Include PR links and observed head SHAs, evidence ceilings, open human/provider
gates, and the next unblocked frontier. Do not overstate completion.
