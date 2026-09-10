---
type: source
title: "Bound leaf context intake"
identity_key: ticket:autopilot-token-economics/TK-03
identity_strength: stable
source_path: docs/tickets/autopilot-token-economics/done/03-bound-leaf-context-intake.md
source_digest: sha256:e99c372e9283415b74c764e5c818b0fbb8d3c5fc8db58ab1d547c03c1f67125b
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-11
created_provenance: git-commit
disposition_changed: 2026-08-11
disposition_changed_provenance: git-rename
run_id: 7974966ec8d84a35
---

# Bound leaf context intake

Compiled from `docs/tickets/autopilot-token-economics/done/03-bound-leaf-context-intake.md`. Identity is `ticket:autopilot-token-economics/TK-03`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-11** via `git-commit`
- Disposition changed: **2026-08-11** via `git-rename`

## Graph

- Parent source: [[sources/artifact-autopilot-token-economics-wayfinder]]
- Blocked by: [[sources/ticket-autopilot-token-economics-tk-01]] — `ticket:autopilot-token-economics/TK-01`

## Run

Completed under autopilot run `7974966ec8d84a35`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-autopilot-token-economics-tk-03.md","payload_bytes":2462,"payload_sha256":"e99c372e9283415b74c764e5c818b0fbb8d3c5fc8db58ab1d547c03c1f67125b"}],"payload_bytes":2462,"payload_sha256":"e99c372e9283415b74c764e5c818b0fbb8d3c5fc8db58ab1d547c03c1f67125b","schema":1,"source_digest":"sha256:e99c372e9283415b74c764e5c818b0fbb8d3c5fc8db58ab1d547c03c1f67125b","source_identity":"ticket:autopilot-token-economics/TK-03","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2462,"payload_sha256":"e99c372e9283415b74c764e5c818b0fbb8d3c5fc8db58ab1d547c03c1f67125b","schema":1,"source_digest":"sha256:e99c372e9283415b74c764e5c818b0fbb8d3c5fc8db58ab1d547c03c1f67125b","source_identity":"ticket:autopilot-token-economics/TK-03"} -->
```markdown
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

```
