---
type: source
title: "Rewrite the README for ticket-autopilot"
identity_key: ticket:ticket-autopilot-delivery-merge/07
identity_strength: stable
source_path: docs/tickets/ticket-autopilot-delivery-merge/done/07-rewrite-readme-for-ticket-autopilot.md
source_digest: sha256:3952f08ba6fc5ecc3aa4974eaf48b39fc01f3fc76526ac4b225eee0159a86b3f
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-05
created_provenance: git-commit
disposition_changed: 2026-08-06
disposition_changed_provenance: git-rename
run_id: issues21-23-autonomous-stack-v7-20260806
---

# Rewrite the README for ticket-autopilot

Compiled from `docs/tickets/ticket-autopilot-delivery-merge/done/07-rewrite-readme-for-ticket-autopilot.md`. Identity is `ticket:ticket-autopilot-delivery-merge/07`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-05** via `git-commit`
- Disposition changed: **2026-08-06** via `git-rename`

## Graph

- Blocked by: [[sources/ticket-ticket-autopilot-delivery-merge-03]] — `ticket:ticket-autopilot-delivery-merge/03`
- Blocked by: [[sources/ticket-ticket-autopilot-delivery-merge-04]] — `ticket:ticket-autopilot-delivery-merge/04`
- Blocked by: [[sources/ticket-ticket-autopilot-delivery-merge-06]] — `ticket:ticket-autopilot-delivery-merge/06`

## Run

Completed under autopilot run `issues21-23-autonomous-stack-v7-20260806`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[3],"status":"present"},"exclusions":{"headings":[7],"status":"present"},"frontier":{"headings":[4],"status":"present"},"intent":{"headings":[2],"status":"present"},"testing":{"headings":[6],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-ticket-autopilot-delivery-merge-07.md","payload_bytes":3807,"payload_sha256":"3952f08ba6fc5ecc3aa4974eaf48b39fc01f3fc76526ac4b225eee0159a86b3f"}],"payload_bytes":3807,"payload_sha256":"3952f08ba6fc5ecc3aa4974eaf48b39fc01f3fc76526ac4b225eee0159a86b3f","schema":1,"source_digest":"sha256:3952f08ba6fc5ecc3aa4974eaf48b39fc01f3fc76526ac4b225eee0159a86b3f","source_identity":"ticket:ticket-autopilot-delivery-merge/07","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 2: What to Build |
| acceptance | 3: Acceptance Criteria |
| testing | 6: Testing Plan |
| frontier | 4: Frontier |
| exclusions | 7: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3807,"payload_sha256":"3952f08ba6fc5ecc3aa4974eaf48b39fc01f3fc76526ac4b225eee0159a86b3f","schema":1,"source_digest":"sha256:3952f08ba6fc5ecc3aa4974eaf48b39fc01f3fc76526ac4b225eee0159a86b3f","source_identity":"ticket:ticket-autopilot-delivery-merge/07"} -->
```markdown
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

```
