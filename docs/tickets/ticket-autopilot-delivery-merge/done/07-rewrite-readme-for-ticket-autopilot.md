---
ticket_schema: 1
ticket_id: "07"
execution_mode: AFK
blocked_by:
  - "03"
  - "04"
  - "06"
---

# Rewrite the README for ticket-autopilot

## Parent Spec

[ticket-autopilot-delivery-merge-wayfinder.md](../../specs/ticket-autopilot-delivery-merge-wayfinder.md)

## What to Build

Resolve [GitHub issue #22](https://github.com/carlitose/agent-skills/issues/22) by replacing
the repository's attribution-only README with a concise, accurate guide to the implemented
ticket-autopilot workflow and its composing skills. Document only public behavior proven by
tickets `01–06`, with copy-pasteable commands and explicit safety/recovery boundaries.

## Acceptance Criteria

- [ ] README explains the problem ticket-autopilot solves, Ticket Envelope v1, the
      `to-spec -> to-tickets -> ticket-autopilot` flow, and the roles of execute/review/QA/
      verification/explain leaves.
- [ ] A minimal tracked-ticket example covers plan, run, status/resume, manual exact-head
      approval, integration, abort, and cleanup with current authoritative CLI syntax.
- [ ] A Git-ignored ticket-source example explains snapshots, ignored finalization, drift
      gates, and why ignored planning files do not enter the PR.
- [ ] Merge documentation clearly distinguishes manual and explicitly granted autonomous
      modes; `AFK` is not described as merge consent.
- [ ] Stacked PR documentation explains single-parent stacking, merge/rebase/retarget flow,
      semantic tree identity, when evidence is preserved, and which drift forces review.
- [ ] Recovery/troubleshooting covers provider capability gates, failed/pending checks,
      stale heads, external merge reconciliation, remote divergence, conflicts, active
      ledger version errors, and crash-safe resume.
- [ ] Safety language forbids invented credentials/evidence, `--admin` policy bypass,
      unguarded provider merge, and claims above observed live evidence.
- [ ] Links point to canonical skill/spec/reference files instead of duplicating schemas;
      attribution remains intact.
- [ ] Every command is checked against `ticket-autopilot.py --help`, links resolve, examples
      use canonical Ticket Envelope serialization, and repository tests/Markdown checks pass.

## Frontier

Dependency-blocked by tickets `03`, `04`, and `06`. The README is the documentation join and
must describe shipped external-merge recovery, ignored-source support, autonomous merge, and
stack identity rather than planned behavior.

## Step-by-Step Implementation Plan

1. Inventory the final public command surface and stable contracts from the completed
   tickets and canonical skill references.
2. Design a short README path from concept to minimal manual run, then add focused sections
   for ignored sources, autonomous mode, stacks, and recovery.
3. Generate example tickets only through the canonical envelope shape and validate every
   command against CLI help in an isolated fixture where practical.
4. Link detailed specs/references for advanced contracts and retain attribution without
   making it the README's primary content.
5. Run link, Markdown, CLI-help, skill-graph, and relevant workflow tests; correct any
   documentation/code mismatch rather than documenting aspirational behavior.

## Testing Plan

Validate commands through the authoritative CLI help and isolated smoke runs, check internal
links and Markdown formatting, and run skill-graph plus ticket-autopilot tests that assert
public contract language. No live merge is required solely for documentation.

## Out of Scope

- Implementing missing workflow behavior from tickets `01–06` in the README ticket.
- Duplicating full ledger, provider, Ticket Envelope, or Verification Record schemas.
- Closing GitHub issues or publishing a release without separate authorization.
