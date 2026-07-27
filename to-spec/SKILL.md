---
name: "to-spec"
description: "Create or update a focused feature, decision, diagnostic, architecture, or bug-analysis spec; backward compatibility is opt-in."
---

# To Spec

Owns: specification framing, decisions, constraints, and implementation intent. It does
not serialize tickets, schedule work, implement code, or decide verification claims.

## Defaults

Unless the user or destination explicitly requires compatibility, specify the clean target
state. Do not add legacy aliases, parallel formats, shims, or migration work by inference.
Still identify destructive data changes, breaking external contracts, and irreversible
operations.

Save under `docs/specs/<slug>.md` unless the user provides a path. Update an existing
matching spec rather than creating a duplicate.

## Process

1. Choose the smallest fitting type:
   - feature: desired behavior and product boundaries;
   - decision: options, decision, trade-offs, and consequences;
   - diagnostic: evidence, hypotheses, root cause, and fix direction;
   - architecture: components, contracts, state, and rollout;
   - bug analysis: observed/expected behavior, reproduction, cause, and acceptance.
2. Reconstruct known context from user decisions, code, current docs, prior specs, tickets,
   and evidence. Fetch current primary documentation when an external library/API/CLI/cloud
   contract matters.
3. Separate fact, decision, assumption, and unresolved question. Ask only for a missing
   decision that materially changes the target.
4. Write concise sections appropriate to the type. Include goals, non-goals, current and
   target behavior, semantic invariants, external contracts, failure modes, security/data
   concerns, alternatives, implementation slices, and verification strategy when relevant.
5. Use project domain language consistently and link evidence rather than copying large
   source blocks.

## Quality checks

- Acceptance outcomes are observable.
- Every material external behavior is preserved or explicitly changed.
- Unknowns and human decisions are visible.
- The implementation plan is ordered but not tied to brittle line numbers.
- Tests distinguish unit, integration, system, live, and manual needs without claiming
  they ran.
- Compatibility and migration obligations are explicit rather than assumed.

## Handoff

If executable tickets are requested, pass the spec path and slice defaults to
`to-tickets`. Do not emit YAML/front matter yourself.

Report the spec path, type, key decisions, unresolved questions, and recommended next
step.
