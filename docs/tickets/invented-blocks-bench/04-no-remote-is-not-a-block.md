---
ticket_schema: 1
ticket_id: "IB-04"
execution_mode: AFK
blocked_by:
  - "IB-01"
---

# IB-04 — Senza remote il target è il ramo locale

## Artifact Graph
- Artifact ID: `ticket:invented-blocks-bench:04`
- Role: `ticket`
- Parent: [invented-blocks-bench.md](../../specs/invented-blocks-bench.md)

## Parent Spec
[invented-blocks-bench.md](../../specs/invented-blocks-bench.md), Findings of the first measure.

## What to Build
In `execute-ticket/references/skills-only.md`, admission step 2: a repository with no remote has
no remote target; the local target branch is the target, and that is not a block.

## Acceptance Criteria
- [ ] The sentence is in the contract; a test in `test_skill_graph.py` checks it.
- [ ] Pin in `pi-personal-config` and `update:personal` verified.

## Frontier
Pronto.

## Gates
Come la spec: merge con CI verde, pin, `update:personal` e reload da parte dell'agente.

## Step-by-Step Implementation Plan
1. Frase e test. 2. PR, merge, pin, installazione. 3. Rimisura con `block-bench`.

## Testing Plan
- `test_skill_graph.py`; rimisura di `goal-prerequisite`.

## Out of Scope
- Il resto dell'ammissione skills-only.
