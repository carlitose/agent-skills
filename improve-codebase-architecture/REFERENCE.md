# Reference

This file owns only the refactor RFC template used by this workflow.

Dependency categories, seam placement, and boundary-testing guidance are owned by
[codebase-design](../codebase-design/SKILL.md). Use its
[deepening reference](../codebase-design/DEEPENING.md) rather than copying that vocabulary
into this workflow.

## Refactor RFC Template

<refactor-rfc-template>

## Problem

Describe the architectural friction:

- Which modules are shallow and tightly coupled
- What integration risk exists in the seams between them
- Why this makes the codebase harder to navigate and maintain

## Proposed Interface

The chosen interface design:

- Interface signature (types, methods, params)
- Usage example showing how callers use it
- What complexity it hides internally

## Dependency Strategy

Name the canonical dependency category from
[DEEPENING.md](../codebase-design/DEEPENING.md), then explain the chosen seam, adapter or
substitute, and how the decision applies to this candidate.

## Testing Strategy

- **New boundary tests to write**: describe the behaviors to verify at the interface
- **Old tests to delete**: list the shallow module tests that become redundant
- **Test environment needs**: any local stand-ins or adapters required

## Implementation Recommendations

Durable architectural guidance that is NOT coupled to current file paths:

- What the module should own (responsibilities)
- What it should hide (implementation details)
- What it should expose (the interface contract)
- How callers should migrate to the new interface

</refactor-rfc-template>
