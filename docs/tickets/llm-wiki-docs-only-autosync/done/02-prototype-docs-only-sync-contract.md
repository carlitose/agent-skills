---
ticket_schema: 1
ticket_id: "WS-02"
execution_mode: AFK
blocked_by:
  - "WS-01"
---

# Prototype the docs-only wiki sync contract

## Artifact Graph
- Artifact ID: `artifact:ws-02-prototype-docs-only-sync-contract`
- Role: `ticket`
- Parent: [llm-wiki-docs-only-autosync-wayfinder.md](../../specs/llm-wiki-docs-only-autosync-wayfinder.md)

## Parent Spec
[llm-wiki-docs-only-autosync-wayfinder.md](../../specs/llm-wiki-docs-only-autosync-wayfinder.md)

## What to Build
A disposable prototype that answers whether the docs-only adoption boundary can validate a
generated wiki sync without widening generic documentation scope or reusing an integrated
application CandidateRef.

## Acceptance Criteria
- [ ] Fixtures cover absent, untracked, tracked, partially tracked, multiple-match, broken
      binding, mixed code/wiki, and configuration/wiki candidates.
- [ ] The prototype demonstrates a precise scope profile and normalized result states, or
      records the smallest counterexample showing why that interface fails.
- [ ] Generated wiki Markdown can pass applicable static checks and `llm-wiki lint` while
      code, ticket sources, raw/binary inputs, and ambiguous roots fail closed.
- [ ] At least two identity designs for the post-integration tracked candidate are exercised.
- [ ] The prototype is clearly marked non-production and records limitations.

## Frontier
Blocked by `WS-01`. Its measured result feeds the `WS-03` decision.

## Step-by-Step Implementation Plan
1. Build isolated project/wiki/Git fixtures from the research contract.
2. Exercise a versioned profile design, a separate request-type design, and a caller-owned
   allowlist design against the same matrix.
3. Compare failure modes, candidate binding, validation coverage, and caller complexity.
4. Save the result under `docs/prototypes/llm-wiki-docs-only-autosync/` with an Artifact
   Graph pointing back to this ticket.

## Testing Plan
Automated fixture tests must assert exact paths, result states, CandidateRefs, and unchanged
trees for rejected inputs. No live provider or production wiki is required.

## Out of Scope
- Production implementation or provider delivery.
- Selecting the final policy without the human gate in `WS-03`.
