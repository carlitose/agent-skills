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
- Treat provider `MERGED` as necessary but insufficient: derive the recursive root delivery base, freshly fetch it, and persist exact-head or explicit-merge-object ancestry before `integrated`.
- Never invent credentials, provider capability, live evidence, approval, or merge authorization.
- Manual merge requires an explicit exact-head decision; autonomous merge requires an actor/evidence-bound run grant. `AFK`, access, and silence grant neither.
- CandidateRef v2 binds semantic trees/digest/version; a separate versioned record binds provider/PR/base/head/branch lineage.
- Semantic drift invalidates all evidence; lineage-only drift preserves it but clears one-shot merge authorization.
- Stop a ticket after the configured quality retry limit; keep other ready tickets moving.

## Public CLI

New runs use ledger schema `4` with quality and interaction/tool/time limits. Interactions default to `10`, reserving one each for `qa-execute` and `verify`; unset limits report `unavailable`. Invalid totals fail before creation. Explicit `migrate-run-lifecycle` validates schema-3 history, preserves its chain, and appends one audited v4 event. `compact-run-ledger` alone compacts history; event hashes stay fixed.

`prepare-zero-to-autopilot --repo <absolute-directory> --target <owner/repository> --visibility private --base <branch> --output <absolute-external-path>` performs a provider-free bounded scan and writes a canonical exact inventory outside the source tree. Entries bind regular-file path, digest, size, mode, risk findings, and publish/exclude disposition; links, special files, nested Git metadata, unsafe/colliding paths, unreadable content, or inventory drift fail closed. `zero-to-autopilot` requires that manifest's exact SHA-256 plus separate actor/evidence authority. It persists immutable intent before `git init`, explicit staging, commit, origin, push, or provider mutation; new Git receives one exact root tree, while existing Git additionally requires `--base-sha` and preserves history/index. The command composes only the audited private GitHub bootstrap, rechecks tree/base/origin/default branch, and records an integrity-wrapped append-only receipt. Replay re-observes without duplicate init/commit/create/push. `zero-to-autopilot-status` is provider-free. This authority grants no run, implementation, PR, merge, conflict resolution, source, wiki, Pi, cleanup, visibility change, or future bootstrap.

`bootstrap-private-github --repo <absolute-root> --target <owner/repository> --visibility private --base <branch> --base-sha <sha> --actor <identity> --evidence <durable-ref>` persists one immutable Git-common intent before creating/adopting the exact private repository, configuring only an absent/equivalent `origin`, non-force publishing an absent exact base, and verifying live default-branch readback. Replay re-observes and emits no duplicate mutation; contradictions fail closed. Bootstrap grants no run, PR, merge, wiki-sync, cleanup, or future authority.

`sync-local-pi <run> --repo <repository> --ticket <id> --checkout <absolute-persistent-path> --agents-root <absolute-skill-root> --pi-settings <absolute-settings> --actor <identity> --evidence <durable-ref>` accepts only a durably integrated ticket, binds its exact head/tree, and persists one local transaction intent. It materializes a clean persistent checkout, replaces only package- or prior-manifest-owned skills, invokes `pi install` and `pi list` through the normal zsh wrapper, and retains `skills: []` on exactly one local package. Pi may store the local source relative to its settings root: preserve that spelling but require its resolved identity and the package row—not the indented installed path—to equal the approved checkout. First adoption and package-source replacement require their explicit flags. An owned-manifest source change additionally requires `--migrate-owned-source-from <exact-old-root>`; it uses a distinct deterministic successor state and preserves ordinary failed history literally. Owned digest drift remains blocked unless repeated `--replace-drifted-owned <name>=<observed-sha256>` inputs exactly equal the complete observed drift set; this destructive authority is valid only during that source migration. Replay re-observes without a second install; wrong trees, dirty or unsafe paths, command/readback failure, and package contradictions fail closed and recover owned local state. It never updates the Pi binary or an active session; report that `/reload` is required. Sync authority grants no merge, provider, wiki, bootstrap, cleanup, or unrelated future sync.

`run --merge-policy autonomous --merge-actor <identity> --merge-evidence <durable-ref>` creates a standing grant with the run. For an existing non-terminal manual run, `grant-autonomous-merge <run> --repo <repository> --actor <identity> --evidence <durable-ref>` appends the same immutable run-bound authority exactly once; identical replay is idempotent, while conflicting authority or unresolved merge mutation fails closed. The grant binds repository, run, ticket-set digest, provider, and policy. Before mutation, reread live exact head, checks/rules, approval, and mergeability, then merge atomically by expected head. Non-passing, simulated, queue-uncertain, or unsupported results gate. Only a proven GitHub queue may use `enqueuePullRequest(expectedHeadOid)` with intent-bound readback and no direct fallback.

`grant-repository-autonomous-merge --repo <absolute-repository> --scope current-and-future-runs --actor <identity> --evidence <durable-ref>` persists one append-only Git-common authority across that exact repository's current and future runs. `merge-all --repo <repository>` discovers canonical run ledgers, adopts the grant only for merge-ready manual runs, and drives each independently eligible PR through the unchanged live expected-head path; future runs adopt at the same boundary. An already-provider-merged PR may instead be reconciled as `external-readback` only when a fresh terminal proof succeeds; this records history and grants no provider mutation authority. `revoke-repository-autonomous-merge` serializes revocation before any later provider mutation. Run-local grants are never overwritten, and non-merge gates, conflict content, bootstrap, source/finalization, wiki, Pi, visibility, and cleanup authority remain separate.

`grant-repository-autonomous-reconciliation --repo <absolute-repository> --scope current-and-future-runs --actor <identity> --evidence <durable-ref>` persists a second, independently revocable Git-common authority; it is never inferred from chat or merge authority. `resume` and `merge-all` may apply only the run-local `artifacts/autonomous-reconciliation/<ticket-id>.json` proposal bound to the active grant, exact repository/remote, ticket digest/CandidateRef, old remote/local head and tree, old/new target SHA/tree, sorted Git-observed conflict paths, canonical resolution digest, and exact result tree. Recreate the real rebase, modify only unresolved index paths, reject markers/extra paths/drift, persist adoption before mutation, persist application readback, and force normal fresh CandidateRef review, QA, verification, finalization, PR-body, provider, and merge eligibility afterward. `revoke-repository-autonomous-reconciliation` blocks unapplied proposals and later dependent mutation; it grants no semantic choice, implementation, source, bootstrap, wiki, Pi, provider-policy, or merge authority.

New `plan`/`run` persist `--final-tree-mode off|observe|enabled`, default `observe`; historical absence stays literal and malformed values fail closed. For tracked completion, observe builds a content-addressed manifest from implementation CandidateRef `I`, binding ticket identity, receipt, link closure, unique effects, complete raw no-renames `I → D` rows, and no-extra-row proof; finalizer records parity/discrepancy. Enabled persists intent before effects, applies/reads each move, receipt, and link once, proves the complete tree, then binds `D` at `final-tree-bound` as `projected-not-integrated`. Prefixes resume; final replay is `already-applied`; contradictions block rollback, publication, provider mutation, integration, and pending restoration. After simplification, enabled scheduling adopts `D` as a fresh generation, clears leaf evidence, runs `review → qa-plan → qa-execute → verify → finalize` once on `D`, and binds `quality-complete` before delivery. Final stage failure retries the same local `D`; semantic implementation drift archives lineage and restarts `implement` without path rollback; projection only contradiction stays in exact recovery. Neither mode transfers evidence, satisfies gates, or grants completion, publication, recovery, provider, or merge authority. Ignored/recovery/reconciliation/provider/drift/ambiguity/untracked/extra-effect cases retain the full process; `status` exposes checkpoints, quality, and all-false authority. For an ignored-source ticket containing a same-digest regular non-executable canonical `done/` receipt, `grant-completion-projection <run> --repo <repository> --ticket <id> --expected-tree <tree> --actor <identity> --evidence <durable-ref>` records an exact repository/run/ticket/snapshot/CandidateRef/destination grant and may resolve only its `source-mode-drift` gate after index/tree and caller-source bytes/mode validation. Replay is idempotent; drift, contradiction, tracked source, extra paths, or unrelated gates fail closed. Drift never retargets authority: a new actor/evidence call appends a successor; only the newest exact match is active. Legacy singleton grants remain entry one; mutated, deleted, reordered, branching, or same-candidate contradictory lineage fails closed. A tracked-base gate requires: lock-held proof of the same run branch, runner-shaped prepared commit and parent/tree, ignored CandidateRef lineage, newest grant, and a fresh terminal branch lacking destination and head ancestry. Preserve its observation; integrated, fetched, reconciled, arbitrary, stale, changed-branch, or multiple-gate cases remain blocked. Grants and delivery-head proofs never migrate source ownership or grant merge, provider, wiki, finalization, or implementation-evidence authority; descendants never inherit them.

`resume --events` accepts `leaf-result` for review, QA plan/execute, and verification. Each schema-3 result binds exact CandidateRef, phases, resources, and normalized `execution`; QA/verification add schema-1 `quality` scope, content-addressed evidence, and limits. Partial handoffs resume only on the same CandidateRef. Semantic drift starts a fresh bounded epoch while append-only history retains lifetime totals; same-candidate retries remain in the current epoch. `leaf-result` is the only channel for leaf context. The [`handoff`](../handoff/SKILL.md) skill bridges human sessions and is not a leaf-context channel.

For pre-epoch schema-4 runs, `revalidation-budget-repair` binds the exact tree, rebuilds matching progress, preserves retries, and appends one idempotent audit event. Use it for legacy false exhaustion; real exhaustion opens a durable `resource-budget` gate.

Delivery follows the versioned [PR-body handoff](references/delivery-pr-body-v1.md); route `render-required` to `explain-pr`, and require validated provider body/head readback for `pr-open`.

`verification-checkpoint` accepts expected tree, normalized inputs, and absolute `verification-audit` root, then uses its validator/reducer. The checkpoint module owns serialization, hashes, phase indexes, and resume—not evidence classes, gates, authority, or claims. `inspect_verification_checkpoints` reads the trusted prefix without adapters. Cache keys bind CandidateRef, leaf contract, scope, artifacts, command, and environment; exact hits cost no interaction, missing/corrupt entries rerun, and partial chains resume.

`docs-only-adopt` alone bypasses `execute-ticket`. A v1 request binds Ticket Envelope, digest, CandidateRef, paths, and scope. Only staged regular `docs/**/*.md` qualify; ticket/agent/generated/config/code/script/mixed paths, symlinks, submodules, ambiguity, or drift require `standard-path-required`. Content-addressed patch/kind/Markdown/graph/link checks use no leaf interaction, cap at `implementation-complete`, and recheck before guarded delivery/exact-head merge.

After durable integration, run separate `wiki-sync-v1` against a detached exact-head source; the ticket is provenance only and docs-only v1 never widens. External or internal-untracked output may apply directly. Internal-tracked output is a fresh `WikiSyncRef`/CandidateRef with no inherited verification, PR, or authority. `llm-wiki` never commits or delivers; persist its result separately and keep failure prominent/retryable without rewriting the ticket. Tracked PRs require exact-head `approve <run> --wiki-sync --ticket <id> --head-sha <head> --actor <id> --evidence <ref>` or a separate autonomous wiki grant; application grants never transfer.

Runner-defect issue publication is also orthogonal. `runner-defect-issue-grant` registers one repository-scoped, revocable authority for exactly `carlitose/agent-skills`; no run, gate, provider access, AFK mode, or merge grant implies it. `runner-defect-issue-escalate <run> <record> --dry-run` validates strict high-confidence diagnosis, redaction, stable fingerprint, exact run-ledger binding, and fixed rendering without a provider call or sidecar write. Live escalation negotiates GitHub issue capabilities, searches open and closed issues by the exact marker, creates only with the `bug` label, and persists an integrity-wrapped Git-common outbox receipt. Exact matches never comment, reopen, relabel, or edit. Revocation blocks new mutations; ambiguous sends permit read-only exact-search reconciliation but never automatic recreation. Escalation holds the canonical run lock and proves `ledger.json` byte identity before returning. See the root README operator procedure and the publication decision.

`TICKET_AUTOPILOT_ROOT` is the absolute skill root, never repository cwd. The command surface is:

```bash
python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" --help
```

Commands are `prepare-zero-to-autopilot`, `zero-to-autopilot`, `zero-to-autopilot-status`, `bootstrap-private-github`, `sync-local-pi`, `grant-repository-autonomous-merge`, `revoke-repository-autonomous-merge`, `grant-repository-autonomous-reconciliation`, `revoke-repository-autonomous-reconciliation`, `repository-autonomous-reconciliation-status`, `merge-all`, `plan`, `run`, `resume`, `status`, `pause`, `unpause`, `grant-autonomous-merge`, `grant-completion-projection`, `runner-defect-issue-grant`, `runner-defect-issue-revoke`, `runner-defect-issue-status`, `runner-defect-issue-escalate`, `approve`, `abort`, `cleanup`, `ticket-hold`, `ticket-cancel`, `ticket-reopen-request`, `ticket-reopen`, `migrate-run-lifecycle`, `compact-run-ledger`, `ticket-parse`, `ticket-emit`, `ticket-list`, `artifact-audit`, and `migrate`; use `<command> --help`. `ticket-list` is provider-free/read-only schema 2 and reports disposition, lifecycle, readiness/causes, malformed/duplicate tickets, dependency gaps, and cycles. `artifact-audit` is provider-free/read-only schema 1; it separates errors, legacy warnings, unreferenced candidates, and migration work, and never rewrites artifacts.

`pause` is run-scoped. Hold/cancel require identity, reason, and durable authority. Reopen is request→human `approve`→apply: it consumes only the matching passed gate and invalidates candidate-through-merge state. Approval is durable human authority, not caller authentication. Provider/Git/delivery boundaries recheck pause, disposition, source path, and digest; manual out-of-band TOCTOU remains possible.

## Scheduler flow

1. Accept only base-clean tracked or fully ignored in-repository tickets. Before worktree creation, snapshot canonical content under Git common state and bind mode/digest; resume never reparses caller files. Ignored completion stays outside the PR except for one separately granted, exact-digest, candidate-only canonical `done/` projection; source ownership and finalization remain external.
2. Parse through the canonical CLI; reject unsupported schema, duplicate IDs, dependency gaps, and cycles. Migration is explicit, never fallback.
3. Compute the ready frontier deterministically. Held/canceled tickets are unschedulable and
   block descendants without cascade; a HITL gate does not freeze unrelated AFK tickets.
4. Select one ready ticket and invoke `execute-ticket` with normalized envelope, source artifact reference, body, CandidateRef, retry limit, and scope unless explicit validated `docs-only-adopt` applies. Never infer docs-only eligibility. Finish its serialized mutation and state transition first.
5. Receive implementation and simplification, then either preserve the established full cycle or, for exact enabled tracked eligibility, persist and apply `I → D` before final quality. Accept review, QA plan/results, verification, and finalization only for the active final CandidateRef. Reject incomplete, imported, or stale handoffs; do not reinterpret their claim ceiling.
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
Repeated reads are pure projections: they do not append heartbeats or consume budget.

Report each ticket as ready, active, gated, review-exhausted, PR-open, integrated, or
failed. Include PR links and observed head SHAs, evidence ceilings, open human/provider
gates, and the next unblocked frontier. Do not overstate completion.
