---
ticket_schema: 1
ticket_id: "WBF-01"
execution_mode: AFK
blocked_by: []
---

# WBF-01 — Freeze and deliver exact Git-representation wiki bytes

## Artifact Graph
- Artifact ID: `ticket:wiki-git-byte-fidelity:WBF-01`
- Role: `ticket`
- Parent: [Tracked wiki Git-byte fidelity](../../specs/wiki-git-byte-fidelity.md)

## Parent Spec
[Tracked wiki Git-byte fidelity](../../specs/wiki-git-byte-fidelity.md), especially evidence, target invariants, and verification strategy.

## What to Build

Correct the internal-tracked producer-to-delivery byte boundary. Before final validation, project generated pages into the source repository's Git blob representation and compare against a consistent Git-representation baseline. Freeze and validate those exact bytes. Materialize them through a disposable raw index without running clean/EOL filters again. Keep the strict final byte, path, parent, and complete-scope assertions.

## Acceptance Criteria
- [ ] CRLF checkout plus `core.autocrlf=true` yields a newly validated candidate whose exact bytes equal the delivered commit blobs; full Git diff equals declared changed paths, including unchanged pages and deletions.
- [ ] `text eol=lf`, explicit `-text` CRLF, and a non-idempotent clean filter are covered. Filtering happens before final lint/hash/receipt, never after freeze; invalid filtered content cannot obtain a passing receipt.
- [ ] Protected worktree, HEAD, index, repository/global configuration, tracked attributes, source CAS, and forbidden-scope checks remain intact. New owned candidate artifacts and content-addressed blobs are allowed.
- [ ] External/internal-untracked behavior is unchanged; raw drift, corrupt manifests, wrong parent/base, extra/missing files, and failed required filtering still fail closed.
- [ ] Historical APM-08 candidate, branch, records, and evidence remain unchanged. No implicit historical retry, semantic-equality acceptance, receipt rewrite, or compatibility path is introduced.
- [ ] Windows-focused producer/delivery/long-path regression results and feasible Linux/quick/forward results are recorded with honest limits. No provider or wiki-merge claim is inferred from fixtures.
- [ ] Contract documentation explains prevalidation Git representation and raw delivery; application integration and a later fresh wiki synchronization remain separately reported and authorized.

## Frontier

Ready; AFK. No dependencies or unresolved product decision. Existing application merge authority, if valid, does not authorize wiki merge. A historical wiki failure remains terminal; this ticket does not grant its retry.

## Step-by-Step Implementation Plan
1. Build a deterministic producer-to-delivery RED case reproducing EOL conversion using a local bare remote and simulated provider transport. Preserve raw byte and exact changed-path assertions.
2. Introduce the smallest tracked-only Git-representation projection before final scope/lint/digest/receipt. Separate Git baseline identity from literal protected-state guards and reject mixed projection inputs.
3. Insert frozen blobs directly into the disposable delivery index, preserving modes/deletions/full-tree proof and avoiding a second clean-filter application.
4. Add negative, non-idempotent-filter, explicit `-text`, unchanged-page, deletion, stale, isolation, and cross-platform coverage. Update the owning contract documentation.
5. Run focused checks, simplify only after GREEN, and submit a fresh frozen CandidateRef through review, QA, verification, and normal delivery. After integration, report the normal new wiki attempt separately; do not modify the APM-08 failed attempt.

## Testing Plan

Focus on `llm-wiki/tests/test_sync_project.py`, `ticket-autopilot/tests/test_wiki_sync.py`, and `ticket-autopilot/tests/test_wiki_long_paths.py`. Use real Git fixture operations and explicitly simulated provider readback. Check exact blob bytes, full changed-path equality, and protected state. Run project quick and relevant forward regression checks. Run Linux where available; full-suite timeout or unavailable boundaries remain inconclusive.

## Out of Scope

- SW semantic policy; APM-12/APM-13 execution or disposition.
- Private local recovery runtime patch or historical ledger/gate repair.
- Global Git configuration changes, cleanup, Pi sync, arbitrary retry API, provider policy changes, or inherited wiki merge authorization.
- Rewriting old frozen artifacts, weakening raw-byte checks, or shipping unrelated dirty files.
