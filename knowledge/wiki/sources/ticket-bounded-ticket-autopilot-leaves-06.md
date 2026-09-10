---
type: source
title: "Decide whether evidence may survive CandidateRef changes"
identity_key: ticket:bounded-ticket-autopilot-leaves/06
identity_strength: stable
source_path: docs/tickets/bounded-ticket-autopilot-leaves/06-decide-selective-invalidation.md
source_digest: sha256:81760bbd91ea766da6cdaedb7505d4c1e1b8aca02329b4381662a3bcdb9ebafb
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-07-28
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Decide whether evidence may survive CandidateRef changes

Compiled from `docs/tickets/bounded-ticket-autopilot-leaves/06-decide-selective-invalidation.md`. Identity is `ticket:bounded-ticket-autopilot-leaves/06`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-07-28** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Blocked by: [[sources/ticket-bounded-ticket-autopilot-leaves-05]] — `ticket:bounded-ticket-autopilot-leaves/05`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[3],"status":"present"},"exclusions":{"headings":[7],"status":"present"},"frontier":{"headings":[4],"status":"present"},"intent":{"headings":[2],"status":"present"},"testing":{"headings":[6],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-bounded-ticket-autopilot-leaves-06.md","payload_bytes":2946,"payload_sha256":"81760bbd91ea766da6cdaedb7505d4c1e1b8aca02329b4381662a3bcdb9ebafb"}],"payload_bytes":2946,"payload_sha256":"81760bbd91ea766da6cdaedb7505d4c1e1b8aca02329b4381662a3bcdb9ebafb","schema":1,"source_digest":"sha256:81760bbd91ea766da6cdaedb7505d4c1e1b8aca02329b4381662a3bcdb9ebafb","source_identity":"ticket:bounded-ticket-autopilot-leaves/06","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 2: What to Build |
| acceptance | 3: Acceptance Criteria |
| testing | 6: Testing Plan |
| frontier | 4: Frontier |
| exclusions | 7: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2946,"payload_sha256":"81760bbd91ea766da6cdaedb7505d4c1e1b8aca02329b4381662a3bcdb9ebafb","schema":1,"source_digest":"sha256:81760bbd91ea766da6cdaedb7505d4c1e1b8aca02329b4381662a3bcdb9ebafb","source_identity":"ticket:bounded-ticket-autopilot-leaves/06"} -->
```markdown
---
ticket_schema: 1
ticket_id: "06"
execution_mode: HITL
blocked_by:
  - "05"
---

# Decide whether evidence may survive CandidateRef changes

## Parent Spec

[bounded-ticket-autopilot-leaf-protocol.md](../../specs/bounded-ticket-autopilot-leaf-protocol.md)

## What to Build

Run a focused grilling decision on issue #9's proposed selective invalidation. Decide
whether to preserve accepted decision D6 unchanged or replace it with a precise,
fail-closed causal reuse contract.

## Acceptance Criteria

- [ ] The decision compares global invalidation with concrete selective-reuse alternatives
      for review, QA plan, QA execution, verification, static environment facts, live
      evidence, and merge authorization.
- [ ] Each alternative names authorization, causal scope proof, cache identity, stale-result
      attack cases, failure behavior, and implementation cost.
- [ ] The analysis demonstrates whether the same real blocker and should-fix from issue #9
      would still be discovered after a candidate mutation.
- [ ] Human authority explicitly chooses to preserve D6 or accepts exact replacement rules;
      silence or a broad performance goal is not authorization.
- [ ] If D6 is preserved, the decision records why same-CandidateRef caching is the safe
      optimization ceiling.
- [ ] If D6 changes, a decision spec records the new invariant and Wayfinder emits separate
      implementation and integrated forward-test tickets.
- [ ] Merge authorization remains bound to the current PR head SHA in every alternative.
- [ ] No missing live evidence or partial inspection can survive as a stronger claim.

## Frontier

Exact human decision required. Dependency-blocked by `05` so the decision uses measured
same-CandidateRef savings before considering a weaker invalidation boundary.

## Step-by-Step Implementation Plan

1. Present current D6, observed repeated-work costs, and measured safe cache gains.
2. Enumerate artifact categories and candidate-change examples.
3. Stress-test causal independence, hidden callers, generated artifacts, environment drift,
   and claim propagation.
4. Compare preserve-D6, limited non-semantic carry-forward, and semantic selective-reuse
   contracts.
5. Obtain an explicit human decision and record rationale, rejected alternatives, and
   consequences.
6. Update the Wayfinder frontier and emit only the tickets authorized by that decision.

## Testing Plan

- Tabletop adversarial scenarios for stale findings, partial diffs, shared callers, changed
  tests, changed ticket acceptance, provider receipts, and PR-head drift.
- Prototype or fixture evidence where reasoning alone cannot establish causal independence.
- No code implementation or claim elevation occurs in this ticket.

## Out of Scope

- Implementing selective invalidation before the decision.
- Treating file-path non-overlap as sufficient causal proof.
- Weakening exact-SHA authorization or live-evidence gates.

```
