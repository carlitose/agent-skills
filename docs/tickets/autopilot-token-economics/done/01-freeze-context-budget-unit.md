---
ticket_schema: 1
ticket_id: "TK-01"
execution_mode: HITL
blocked_by: []
---

# Freeze the context budget unit

## Artifact Graph

- Artifact ID: `artifact:tk-01-freeze-context-budget-unit`
- Role: `ticket`
- Parent: [Autopilot Token Economics](../../../specs/autopilot-token-economics-wayfinder.md)

## Type
Grilling

## What to Decide
Fix the unit used to express an autopilot context budget and the surfaces it counts, then
record it as a durable decision. Resolve at least these questions in the canonical
one-question-at-a-time interview:

- Exact tokenizer count or documented deterministic estimator. An exact Anthropic count
  requires credentials and a network call, which would break the provider-free, read-only
  property that lets `ticket-list` and `artifact-audit` close with local evidence.
- Which surfaces the unit covers: the always-on skill listing, the per-workflow static
  closure, the declared leaf intake bounds, or a composition of them.
- How a reported number stays stable enough to compare across commits.

## Acceptance Criteria
- [ ] A decision spec created through `to-spec` records the chosen unit and its rationale.
- [ ] The counted surfaces are enumerated explicitly, with anything excluded named.
- [ ] Rejected options, including the exact-tokenizer path, carry the reason for rejection.
- [ ] The spec states the reporting stability rule that later regression checks rely on.
- [ ] The spec is linked from the parent map and passes `artifact-audit` without new errors.

## Frontier
Ready. It blocks `TK-02` and `TK-03`, which cannot produce comparable numbers until the unit
exists.

## Step-by-Step Plan
1. Run the canonical grilling interview on the three questions above.
2. Record the confirmed decision through `to-spec` with explicit rejected alternatives.
3. Link the spec from the parent map with a reciprocal ownership edge.

## Testing Plan
No runtime behaviour changes. Verify the decision spec satisfies the artifact graph contract
and that `artifact-audit` reports no new errors.

## Out of Scope
- Implementing any measurement command.
- Adding a token axis to ledger budgets or gates.
