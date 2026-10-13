---
ticket_schema: 1
ticket_id: "BGT-01"
execution_mode: AFK
blocked_by: []
---

# BGT-01 — Recovery tools on Pi 1.2.0 and pi-agent-ide

## Artifact Graph
- Artifact ID: `ticket:break-glass-pi-1-2-tools:01`
- Role: `ticket`
- Parent: [break-glass-pi-1-2-tools.md](../../../specs/break-glass-pi-1-2-tools.md)

## Parent Spec
[break-glass-pi-1-2-tools.md](../../../specs/break-glass-pi-1-2-tools.md), Goal 1–4 and Verification.

## What to Build
In `extensions/break-glass.ts`: accept both built-in path forms, trust same-name tools from
`npm:pi-agent-ide`, skip hidden tools, and name the exposed tools in the policy text. In
`extensions/mandatory-agent-skills.ts`: the block reason and the omission notice. README and
the amended spec section.

## Acceptance Criteria
- [x] Built-ins with path `builtin:<name>` and `<builtin:<name>>` are both selected.
- [x] pi-agent-ide `read` and `write` are selected; its hidden `edit` is neither selected nor ambiguous.
- [x] Another extension's `read` still gives no recovery tools.
- [x] The policy names the exposed tools; block reason and notice no longer say "canonical built-in".
- [x] Extension tests pass; CI is green.

## Evidence
- agent-skills #478 (`c7948f0`): `selectRecoveryTools` accepts `builtin:<name>` and
  `<builtin:<name>>`, trusts same-name `npm:pi-agent-ide` tools, skips hidden ones; policy,
  block reason and notice name the exposed tools.
- `node --test extensions/break-glass.test.ts extensions/mandatory-agent-skills.test.ts`: 41/41;
  CI 8/8 green on the merged head.
- Installation of the skills follows after lot `dbh-vague5` (spec Gates).

## Frontier
Done.

## Gates
As the spec: one PR with green CI, merged by the agent; no spend; 4 hours per attempt, at most
2 attempts; installation only after lot `dbh-vague5`.

## Step-by-Step Implementation Plan
1. Failing cases in `extensions/break-glass.test.ts`.
2. `selectRecoveryTools` and the texts.
3. README and spec wording; tests.

## Testing Plan
- `node --test` on `extensions/break-glass.test.ts` and `extensions/mandatory-agent-skills.test.ts`.

## Out of Scope
- Other trusted packages, more IDE tools, the arming lifecycle.
