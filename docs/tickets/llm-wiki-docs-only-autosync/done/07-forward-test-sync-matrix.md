---
ticket_schema: 1
ticket_id: "WS-07"
execution_mode: AFK
blocked_by:
  - "WS-05"
  - "WS-06"
---

# Forward-test the wiki auto-sync matrix

## Artifact Graph
- Artifact ID: `artifact:ws-07-forward-test-sync-matrix`
- Role: `ticket`
- Parent: [llm-wiki-docs-only-autosync-wayfinder.md](../../specs/llm-wiki-docs-only-autosync-wayfinder.md)

## Parent Spec
[llm-wiki-docs-only-autosync-wayfinder.md](../../specs/llm-wiki-docs-only-autosync-wayfinder.md)

## What to Build
A deterministic forward-test suite and report proving the complete behavior of both triggers
across absent, untracked, tracked, and exceptional wiki states.

## Acceptance Criteria
- [ ] Ticket creation invokes sync once per batch; integration invokes sync once per durable
      integrated ticket effect.
- [ ] Absent is a no-op, untracked is directly validated, and tracked is a separate
      docs-only candidate with the expected claim ceiling.
- [ ] Partial tracking, multiple roots, broken binding, mixed paths, failed lint, concurrent
      change, resume, and retry all reach the decided result without silent fallback.
- [ ] No scenario scaffolds a wiki, mutates an application CandidateRef, bypasses merge
      authorization, or presents wiki content as primary evidence.
- [ ] The report records local simulation limitations and makes no live-provider claim.

## Frontier
Blocked by both caller integrations `WS-05` and `WS-06`.

## Step-by-Step Implementation Plan
1. Add raw scenario prompts/fixtures for every matrix row and trigger boundary.
2. Execute them through the public CLIs and capture normalized results.
3. Validate idempotency, Git isolation, evidence ceilings, and retry state.
4. Emit a machine-readable report and fold outcomes into the parent wayfinder.

## Testing Plan
Run the complete unit/integration suites plus the new forward-test scenarios. Provider and
production-wiki boundaries remain explicitly unobserved unless separately authorized.

## Out of Scope
- Live provider mutation or automatic merging during the forward test.
- New behavior beyond the confirmed `WS-03` decision.
