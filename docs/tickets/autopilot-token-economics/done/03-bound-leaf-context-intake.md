---
ticket_schema: 1
ticket_id: "TK-03"
execution_mode: AFK
blocked_by:
  - "TK-01"
---

# Bound leaf context intake

## Artifact Graph

- Artifact ID: `artifact:tk-03-bound-leaf-context-intake`
- Role: `ticket`
- Parent: [Autopilot Token Economics](../../../specs/autopilot-token-economics-wayfinder.md)

## Type
Task

## What to Build
Declared, tested upper bounds on how much volatile content each leaf skill may read into
context. This is the substantive lever: the static prefix is paid once and is cache-friendly,
while diffs, logs, and file reads accumulate and are re-sent every turn.

Apply bounds to the leaf contracts composed inside `execute-ticket` — `code-review`,
`qa-test-plan`, `verification-audit`, and `code-simplification` — covering read budgets,
output truncation, and preferring references over pasted content. The serialized handoff is
already pointer-based, since `leaf_protocol.py:460-478` validates quality evidence as
64-character `sha256` digests, so this work targets prompt-level intake and not the JSON
contract.

## Acceptance Criteria
- [ ] Each named leaf declares an explicit volume bound for what it reads.
- [ ] Bounds are derived from observed leaf behaviour, not asserted round numbers.
- [ ] No verification duty, evidence classification, causal-scope rule, or claim ceiling is
      weakened, removed, or reworded to permit reading less.
- [ ] Prompt-level tests assert each bound exists and is honoured.
- [ ] `test_skill_graph.py` and `forward_test.py` continue to pass unchanged in intent.
- [ ] The ticket states plainly that local evidence proves a declared bound, not a measured
      token saving.

## Frontier
Blocked by `TK-01`. It is the riskiest edit in this map because it touches the same contracts
that own verification duties.

## Step-by-Step Plan
1. Observe what each leaf actually reads today and where volume concentrates.
2. Derive a defensible bound per leaf from those observations.
3. Add the bound to each leaf contract without touching verification clauses.
4. Add prompt-level tests for presence and enforcement of every bound.

## Testing Plan
Prompt-level regression tests per leaf, plus a diff review confirming no verification clause
changed. Existing skill-graph and forward tests must still pass.

## Out of Scope
- Quantifying the resulting token saving, which requires the `TK-09` live observation.
- Compressing `SKILL.md` prose.
- Changing what any leaf must verify or may claim.
