---
type: source
title: "Freeze the context budget unit"
identity_key: ticket:autopilot-token-economics/TK-01
identity_strength: stable
source_path: docs/tickets/autopilot-token-economics/done/01-freeze-context-budget-unit.md
source_digest: sha256:d56f0f0278e07967a383866dc911c40217a7f579af761560111a2c29d5c24b70
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-11
created_provenance: git-commit
disposition_changed: 2026-08-11
disposition_changed_provenance: git-rename
run_id: 7974966ec8d84a35
---

# Freeze the context budget unit

Compiled from `docs/tickets/autopilot-token-economics/done/01-freeze-context-budget-unit.md`. Identity is `ticket:autopilot-token-economics/TK-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-11** via `git-commit`
- Disposition changed: **2026-08-11** via `git-rename`

## Graph

- Parent source: [[sources/artifact-autopilot-token-economics-wayfinder]]

## Run

Completed under autopilot run `7974966ec8d84a35`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[],"status":"not-identified"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-autopilot-token-economics-tk-01.md","payload_bytes":2141,"payload_sha256":"d56f0f0278e07967a383866dc911c40217a7f579af761560111a2c29d5c24b70"}],"payload_bytes":2141,"payload_sha256":"d56f0f0278e07967a383866dc911c40217a7f579af761560111a2c29d5c24b70","schema":1,"source_digest":"sha256:d56f0f0278e07967a383866dc911c40217a7f579af761560111a2c29d5c24b70","source_identity":"ticket:autopilot-token-economics/TK-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | no matching section identified in the source; complete source retained |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2141,"payload_sha256":"d56f0f0278e07967a383866dc911c40217a7f579af761560111a2c29d5c24b70","schema":1,"source_digest":"sha256:d56f0f0278e07967a383866dc911c40217a7f579af761560111a2c29d5c24b70","source_identity":"ticket:autopilot-token-economics/TK-01"} -->
```markdown
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

```
