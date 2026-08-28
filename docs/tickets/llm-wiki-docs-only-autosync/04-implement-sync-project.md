---
ticket_schema: 1
ticket_id: "WS-04"
execution_mode: AFK
blocked_by:
  - "WS-03"
---

# Implement the idempotent sync-project boundary

## Artifact Graph
- Artifact ID: `artifact:ws-04-implement-sync-project`
- Role: `ticket`
- Parent: [llm-wiki-docs-only-autosync-wayfinder.md](../../specs/llm-wiki-docs-only-autosync-wayfinder.md)

## Parent Spec
[llm-wiki-docs-only-autosync-wayfinder.md](../../specs/llm-wiki-docs-only-autosync-wayfinder.md)

## What to Build
One versioned `llm-wiki sync-project` capability that hides discovery, project-history
ingest, timeline rebuild, wiki validation, tracking classification, and normalized outcomes.
Implement the confirmed docs-only wiki profile at the same public boundary.

## Acceptance Criteria
- [ ] A single invocation returns the decision-spec result for every normal and error state.
- [ ] Repeating sync on unchanged inputs writes nothing and returns an unchanged result.
- [ ] Untracked output is validated directly; tracked output is returned as a frozen
      docs-only candidate and is not committed or delivered by `llm-wiki`.
- [ ] Mixed, partial, ambiguous, broken, stale, and concurrently changed inputs fail exactly
      as decided.
- [ ] Unit and integration tests prove command ordering, allowed paths, lint evidence,
      CandidateRef binding, and claim ceiling.

## Frontier
Blocked by confirmed decision `WS-03`. It unblocks both caller integrations.

## Step-by-Step Implementation Plan
1. Add the versioned result/request contracts and pure normalization tests.
2. Compose existing ingest, timeline, and lint owners behind one idempotent operation.
3. Add the docs-only profile adapter and tracked/untracked delivery seam.
4. Expose the CLI and update `llm-wiki` plus `ticket-autopilot` instructions.

## Testing Plan
Run focused unit tests for both packages and isolated Git integration fixtures for all
matrix states. Run the existing llm-wiki lint and docs-only suites unchanged.

## Out of Scope
- Caller triggers, provider PR creation, or automatic merge.
- Scaffolding a missing wiki.
