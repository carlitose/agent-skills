---
ticket_schema: 1
ticket_id: "WGC-03"
execution_mode: AFK
blocked_by: []
---

# Accept Windows Git path separators without weakening worktree GC

## Artifact Graph
- Artifact ID: `artifact:worktree-gc-windows-git-paths`
- Role: `ticket`
- Parent: [Ticket Autopilot orphan-worktree garbage collection](../../specs/ticket-autopilot-orphan-worktree-garbage-collection.md)

## Parent Spec
[Ticket Autopilot orphan-worktree garbage collection](../../specs/ticket-autopilot-orphan-worktree-garbage-collection.md) — Windows Git inventory path correction — WGC-03.

## What to Build
Adapt Windows filesystem separators at the `git worktree list --porcelain -z` input boundary before the existing canonical validator. The observed absolute `C:/...` Git path fails literal comparison with native `os.path.normpath`, so planning cannot reach classification. Convert separators only, leaving aliases and invalid lexical forms visible for rejection. Preserve POSIX literal backslashes and the existing native inventory representation.

## Acceptance Criteria
- [ ] Actual Windows Git inventory reaches public `worktree-gc-plan`, produces a valid deterministic plan, and agrees with native-spelled owner paths instead of failing at `_canonical_absolute`.
- [ ] Equivalent Windows slash and backslash input spellings work at the Git boundary. POSIX backslashes remain filename characters, not separators.
- [ ] Dot/parent components, repeated separators, drive-relative/root-relative paths, symlinks, wrong managed parents, ownership mismatches, and stale plans remain rejected or protected under the existing contracts.
- [ ] Persisted manifest, ledger, plan, intent, and receipt validation stays strict; no record rewriting, broad string normalization, case folding, or digest weakening is introduced.
- [ ] Existing running/dirty/unretained/locked/open-wiki/incomplete-Pi/unmanaged protections and provider-free planning remain covered. Existing isolated apply/replay tests retain their safety assertions.
- [ ] A focused production-path test is RED on the baseline and GREEN after the fix. Run GC and relevant CLI/owner regressions, distinguishing native Windows, unavailable POSIX/symlink capabilities, and unrelated fixture failures.
- [ ] No real worktree is removed, adopted, or manually cleaned. This ticket authorizes the fix and disposable test fixtures only; actual GC application still requires its separate exact-plan authority.

## Frontier
Ready. AFK, inline only; no subagents. WGC-01/WGC-02 are completed predecessors, not tickets to reopen. This correction has no implementation dependency on Azure decoding or wiki publication.

## Step-by-Step Implementation Plan
1. Reproduce the actual Git inventory failure and add focused boundary/planning regression coverage. Completion: the failure is the native separator comparison, not missing Git or a synthetic unrelated exception.
2. Apply the smallest separator-only adaptation at the Git input boundary. Completion: planning reaches protected/eligible classification with persisted validation unchanged.
3. Add lexical-negative and platform-specific backslash checks and run the existing GC safety/replay tests. Completion: the green positive path has not relaxed any deletion prerequisite.
4. Complete simplification, shared-context review, QA, and canonical verification through the runner. Completion: evidence is bound to the actual candidate and no production cleanup is claimed or performed.

## Testing Plan
- Real local Git/CLI planning and deterministic replay in disposable repositories, plus the existing GC module tests.
- Windows slash/native spelling, malformed lexical paths and identities; POSIX literal-backslash test only on a native applicable host.
- Existing guarded apply, stale input, active/open-effect protection, and interruption/replay tests, with removals restricted to their temporary fixtures.
- Strict byte identity of protected real ledgers/manifests and unchanged runtime authority. No provider call is needed to prove this feature.

These are planned checks, not verification results.

## Out of Scope
- Actual repository cleanup, `--force`, pruning, branch deletion, manual ledger edits, or silent legacy ownership adoption.
- Provider decoding, verification-checkpoint repair, long-path wiki publication, a generic path framework, global settings, or installed skill updates.
