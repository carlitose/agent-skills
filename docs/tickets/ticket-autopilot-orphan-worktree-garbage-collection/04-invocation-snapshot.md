---
ticket_schema: 1
ticket_id: "WGC-04"
execution_mode: AFK
blocked_by: []
---

# WGC-04 — Bound redundant GC planning work with an invocation snapshot

## Artifact Graph

- Artifact ID: `artifact:ticket-autopilot-worktree-gc-invocation-snapshot`
- Role: `ticket`
- Parent: [Orphan-worktree GC](../../specs/ticket-autopilot-orphan-worktree-garbage-collection.md)

## Parent Spec

[Orphan-worktree GC — invocation-scoped planning snapshot](../../specs/ticket-autopilot-orphan-worktree-garbage-collection.md#invocation-scoped-planning-snapshot--wgc-04).

## What to Build

Remove repeated primary repository-binding discovery and whole-corpus ledger decoding from the per-owner loop in `plan_worktree_gc`. One private invocation snapshot owns cross-reference extraction, source fingerprints and freshness rejection before plan persistence. Keep the public API, persisted schemas, stable-input classification and all apply-time checks unchanged.

Historical #57 evidence distinguishes redundant work and oversized buffered output from the unobserved final frame of the original90s timeout. Source continuity is confirmed at reviewed based82b9d17257f44ab4358a428ff3d2fb4c38d52c2. No real inventory checkpoint or cleanup rerun is authorized. Bounded/progressive output belongs to the separate #42 protocol work.

## Acceptance Criteria

- [ ] AC1: A multi-owner disposable fixture proves at most one cross-reference integrity/decode pass per source per planning invocation, plus raw-content freshness checks; primary binding discovery is invocation-bounded rather than repeated for every owner.
- [ ] AC2: Stable input produces the existing eligible/protected classifications, reason ordering, exact `referenced_by` behavior and deterministic plan digest; cover own-run exclusion, multiple active references and nested history-only paths.
- [ ] AC3: New invocations observe changed ledger content; no process/global/persistent cache or retained decoded historical corpus is introduced. No-target planning avoids unnecessary corpus decoding.
- [ ] AC4: Source path addition/removal, byte change, unverifiable freshness or primary binding drift during planning fails before plan persistence; initial integrity validation is never replaced by hash comparison alone.
- [ ] AC5: Owner identity, exact managed paths, locks, invalid-owner protection, dirty/ignored/untracked states, retained heads, per-owner drift, operational protection and exact all-entry apply/replay checks remain effective. Preserve current unchanged malformed foreign-payload handling rather than silently introducing a second validation policy.
- [ ] AC6: Focused regression/causal tests and disposable guarded-apply/stale-plan tests pass on observed platforms; source/candidate/evidence are bound canonically. Report unavailable native platforms, broad-suite gaps and synthetic boundaries explicitly.
- [ ] AC7: No live planner/inventory replay, cleanup, adoption, live runner/scheduler, provider mutation, timeout increase or ledger/session rewrite occurs during implementation/QA. A disposable test's fixture kernel/ledger is not workflow scheduling or a fabricated delivery receipt.

## Frontier

Ready, AFK, no active blockers. Existing ownership/planning/application APIs and WGC-03 are already integrated in the admitted base; archived predecessor tickets remain untouched. Work serially inline in an isolated checkout. The primary developer checkout has unrelated untracked artifacts and must not be reset, cleaned or fast-forwarded.

## Step-by-Step Implementation Plan

1. Preserve the prior diagnosis and establish source/candidate identities; use the existing owning spec and canonical ticket contract without runner admission.
2. Add one public-planner causal regression in disposable fixtures: multiple owners must not multiply complete-ledger decoding and primary-binding discovery. Capture RED with a small bounded command.
3. Implement the private invocation snapshot/index and primary-binding reuse; retain each owner's binding/common-directory validation. Confirm GREEN before the next test.
4. Add one freshness/cross-reference scenario at a time, including independent calls, history exclusion, changed bytes and source-set drift. Reject unsafe persistence, not silently refresh mid-plan.
5. Run focused safety regressions; freeze the candidate, simplify, review, plan/execute scoped QA and validate the standalone verification bundle. Max3 quality cycles; failed attempts consume their recorded budget.
6. Return the validated handoff. Separately authorized delivery must freshly check provider/CI/merge authority and retain exact readback. Any required personal-bundle pin update is separately reviewed; never silently sync an unreviewed pin or claim runtime activation from files on disk.

## Testing Plan

- Causal unit/integration tests: real temporary files/Git, instrumentation at source-read and repository-binding boundaries; no timing threshold as the correctness oracle.
- Behavioral fixtures: protected and eligible owners, multiple active references, own-run/history exclusions, deterministic repeat and changes between calls.
- Adversarial drift: add/remove/edit ledger sources and change binding during an invocation; assert zero plan persistence and no cleanup/provider calls.
- Regression: focused worktree-GC module and relevant ownership/CLI boundary tests, compilation, diff check and artifact-graph audit. Full-suite/native-platform results are separate evidence gates, not implied by targeted tests.
- Every command <=900s; start with short targeted runs and report elapsed/failed/unknown costs. Do not rerun the original buffered45-worktree command or the instrumented production planner merely to collect fresh timings.

## Out of Scope

- Real cleanup/adoption, tree disposition, locks/ledgers migration or loss of unrelated WIP.
- Persistent caches, new public options, timeout/heap raises, skipping validation, repository-wide scheduler activation or subagents.
- New foreign-ledger validation semantics, provider422 repair, Pi sandbox defects, Telegram and the later benchmark.
- Claiming the complete original workload is now under90s, native macOS success, independent review, or active-runtime reload without observation.
