---
ticket_schema: 1
ticket_id: "CR-05"
execution_mode: AFK
blocked_by:
  - "CR-03"
---

# Map supported Claude Code compaction controls

## Artifact Graph

- Artifact ID: `artifact:cr-05-map-supported-compaction-controls`
- Role: `ticket`
- Parent: [Cross-host Context Rollover](../../specs/cross-host-context-rollover-wayfinder.md)

### Produces

- [Claude Code compaction control baseline](../../research/cross-host-context-compaction-controls.md)

## Parent Spec

[Cross-host Context Rollover](../../specs/cross-host-context-rollover-wayfinder.md)

## What to Build

Turn the baseline report into version-bound evidence for supported Claude Code compaction
controls. Separate official documentation, local CLI help, and observed runtime effects. Do
not treat `--autocompact` as an eligible solution.

## Acceptance Criteria

- [ ] The report binds exact local versions, sanitized help surfaces, and official-source
      revisions without storing credentials or transcript content.
- [ ] Isolated temporary-configuration probes classify `DISABLE_COMPACT`, blocking
      `PreCompact`, `PostCompact`, and `/compact` as `supported`, `unsupported`, or
      `unobserved`.
- [ ] A help entry alone never becomes runtime evidence, and `--autocompact` remains rejected
      even where a local binary parses it.
- [ ] No probe changes global hooks, shell configuration, Claude settings, or unrelated
      sessions.
- [ ] The report fixes the capability contract that CR-06 consumes: supported prevention,
      observation-only, or visible `no-go` before 150,000 tokens.
- [ ] Unavailable live boundaries stay explicit and do not become passing simulated claims.

## Frontier

Ready. The destination is fixed; only current host capability evidence is missing.

## Step-by-Step Implementation Plan

1. Capture versioned official and local command surfaces with secret-safe evidence.
2. Build isolated fixtures for environment and hook control candidates.
3. Run the smallest authorized probes and classify each observed boundary.
4. Update the baseline report with evidence, limits, and the exact CR-06 contract.

## Testing Plan

Use temporary directories and sanitized fixture inputs. Unit checks validate classification
and prevent help-only promotion. Any real host process probe remains local and must record its
version, configuration isolation, exit behavior, and limitations.

## Out of Scope

- Restoring `--autocompact` under another version gate.
- Editing the rollover prototype; CR-06 owns that change.
- Installing global hooks or changing global Claude configuration.
- Running the HITL live rollover owned by CR-04.
