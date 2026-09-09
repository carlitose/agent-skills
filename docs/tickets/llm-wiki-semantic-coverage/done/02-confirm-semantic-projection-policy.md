---
ticket_schema: 1
ticket_id: "SW-02"
execution_mode: HITL
blocked_by:
  - "SW-01"
---

# Confirm semantic projection and lint policy

## Artifact Graph
- Artifact ID: `artifact:sw-02-confirm-semantic-projection-policy`
- Role: `ticket`
- Parent: [LLM Wiki semantic coverage recovery](../../specs/llm-wiki-semantic-coverage-wayfinder.md)

## Parent Spec
[LLM Wiki semantic coverage recovery](../../specs/llm-wiki-semantic-coverage-wayfinder.md)

## Produces
- `docs/specs/llm-wiki-semantic-projection-decision.md`, which must point back to this ticket.

## What to Build
Use the `SW-01` prototype evidence to obtain and record the human decision that fixes the semantic projection and lint contract. Invoke the canonical `grilling` skill, ask one question at a time, and wait for confirmation rather than converting an AFK recommendation into product authority.

The decision must define per-kind required semantic content; whether content is preserved, deterministically extracted, agent-authored, or layered; freshness and audit rules; page-size bounds; failure behavior for absent or malformed sections; and the machine-readable markers that semantic lint may trust. It must explicitly reconcile the new contract with the current provenance-first design.

## Acceptance Criteria
- [ ] The decision cites the `SW-01` measurements and distinguishes measured facts from product choices.
- [ ] Canonical `grilling` is used and the human explicitly confirms the selected option.
- [ ] Required semantic coverage is defined separately for tickets, specs, research, prototypes, and guides.
- [ ] The contract states whether any prose may be agent-authored and, if so, how source grounding, freshness, audit, and deterministic re-ingest are represented.
- [ ] The contract fixes page-size/splitting behavior and the exact markers consumed by lint.
- [ ] Existing identity, digest, graph, timeline, tombstone, move, and canonical ticket-parser invariants are preserved or explicitly changed.
- [ ] A decision spec is created through `to-spec` with a reciprocal Artifact Graph, alternatives, consequences, and observable acceptance outcomes.

## Frontier
HITL and dependency-blocked on `SW-01`. After the prototype lands, this ticket still requires explicit human confirmation. AFK mode, merge authority, and silence do not satisfy this gate.

## Step-by-Step Implementation Plan
1. Read the complete `SW-01` report and validate its evidence paths and limitations.
2. Invoke `grilling` around the remaining product choices, one question at a time.
3. Record the confirmed decision through `to-spec`, including rejected alternatives and compatibility consequences.
4. Update the map and reciprocal graph links. Checkpoint: `SW-03` and `SW-04` can implement and test the contract without inventing policy.

## Testing Plan
Statically verify that every unresolved decision from the map and diagnostic has one explicit disposition. Run the canonical artifact audit and Markdown-link checks over the decision, map, prototype output, and ticket graph.

No production compiler behavior, live wiki mutation, or external model call is claimed by this decision ticket.

## Out of Scope
- Implementing compiler or lint behavior.
- Treating the prototype recommendation as human confirmation.
- Deciding historical gate-repair evidence, which belongs to `SW-06`.
