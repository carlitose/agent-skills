---
ticket_schema: 1
ticket_id: "U-04"
execution_mode: HITL
blocked_by:
  - "U-02"
---

# Scope architecture improvement with shared design vocabulary

## Parent Spec
[Open GitHub Issues Remediation](../../specs/open-github-issues-wayfinder.md)

## Adoption Source
[OI-07 approved parity selection](../../research/mattpocock-skills-parity.md#oi-07-approved-adoption-selection)

## What to Build
Update `improve-codebase-architecture` to consume U-02 `codebase-design` terminology and start from recent-change hot spots before widening by evidence. Preserve `improve-codebase-architecture` as the bounded survey owner and `codebase-improver` as the separate human-gated full-repository workflow. Ask one human question before deciding whether the temporary visual report is a stable output or an optional ephemeral aid.

## Acceptance Criteria
- [ ] Shared design terms link to U-02 rather than being redefined locally.
- [ ] Default discovery considers recent changes and documents when evidence justifies a wider scan.
- [ ] The visual-report stability decision is explicitly confirmed and reflected in docs/tests before its output contract changes.
- [ ] No routing behavior from OI-08 or execution/AgentTool/isolation behavior from OI-09 is duplicated.
- [ ] `codebase-improver` ownership and human gate remain unchanged.

## Frontier
Dependency-blocked by U-02; then HITL on whether the visual report is stable or ephemeral.

## Step-by-Step Implementation Plan
1. Replace duplicated design language with links to U-02.
2. Add recent-change-first scoping with an evidence-based widening rule.
3. Present the visual-report tradeoff as one canonical human decision and wait for confirmation.
4. Implement and test only the confirmed output contract while preserving both local owners.

## Testing Plan
Run static ownership/link/scoping tests. If a stable report is approved, add a bounded render smoke test; otherwise verify the ephemeral path is not claimed as a durable contract.

## Out of Scope
- Wayfinder-to-Grilling routing owned by OI-08.
- AgentTool-optional composition, execution isolation, or authority vocabulary owned by OI-09.
- Folding `codebase-improver` into this skill.
