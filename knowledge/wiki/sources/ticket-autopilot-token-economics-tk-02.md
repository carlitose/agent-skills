---
type: source
title: "Measure the static prompt prefix"
identity_key: ticket:autopilot-token-economics/TK-02
identity_strength: stable
source_path: docs/tickets/autopilot-token-economics/done/02-measure-static-prompt-prefix.md
source_digest: sha256:194027341c2d45a2150a3fa075ba18abc6c63ba439f8fc7cd5eafc4dbb35a7f2
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-11
created_provenance: git-commit
disposition_changed: 2026-08-11
disposition_changed_provenance: git-rename
run_id: 7974966ec8d84a35
---

# Measure the static prompt prefix

Compiled from `docs/tickets/autopilot-token-economics/done/02-measure-static-prompt-prefix.md`. Identity is `ticket:autopilot-token-economics/TK-02`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-11** via `git-commit`
- Disposition changed: **2026-08-11** via `git-rename`

## Graph

- Parent source: [[sources/artifact-autopilot-token-economics-wayfinder]]
- Blocked by: [[sources/ticket-autopilot-token-economics-tk-01]] — `ticket:autopilot-token-economics/TK-01`

## Run

Completed under autopilot run `7974966ec8d84a35`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-autopilot-token-economics-tk-02.md","payload_bytes":2462,"payload_sha256":"194027341c2d45a2150a3fa075ba18abc6c63ba439f8fc7cd5eafc4dbb35a7f2"}],"payload_bytes":2462,"payload_sha256":"194027341c2d45a2150a3fa075ba18abc6c63ba439f8fc7cd5eafc4dbb35a7f2","schema":1,"source_digest":"sha256:194027341c2d45a2150a3fa075ba18abc6c63ba439f8fc7cd5eafc4dbb35a7f2","source_identity":"ticket:autopilot-token-economics/TK-02","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2462,"payload_sha256":"194027341c2d45a2150a3fa075ba18abc6c63ba439f8fc7cd5eafc4dbb35a7f2","schema":1,"source_digest":"sha256:194027341c2d45a2150a3fa075ba18abc6c63ba439f8fc7cd5eafc4dbb35a7f2","source_identity":"ticket:autopilot-token-economics/TK-02"} -->
```markdown
---
ticket_schema: 1
ticket_id: "TK-02"
execution_mode: AFK
blocked_by:
  - "TK-01"
---

# Measure the static prompt prefix

## Artifact Graph

- Artifact ID: `artifact:tk-02-measure-static-prompt-prefix`
- Role: `ticket`
- Parent: [Autopilot Token Economics](../../../specs/autopilot-token-economics-wayfinder.md)

## Type
Task

## What to Build
A provider-free, read-only command that reports the static context cost of the skill
catalogue in the unit frozen by `TK-01`, following the surface shape already accepted for
`ticket-list` and `artifact-audit`: text output for humans and versioned JSON as the
contract other work consumes.

It must report the always-on skill listing, the per-workflow static closure with a per-file
breakdown, and which skills are hidden from the model-visible listing. The observed baseline
to reproduce is a full autopilot closure of 6,289 words across eleven files, an always-on
listing of roughly 714 words over 22 installed model-visible skills, and 267 words already
hidden by `disable-model-invocation: true`.

## Acceptance Criteria
- [ ] The command runs with no credentials, no network access, and mutates nothing.
- [ ] JSON output is explicitly versioned and documents every field.
- [ ] Output separates the always-on listing from the per-workflow closure.
- [ ] Hidden skills are reported as hidden rather than silently omitted.
- [ ] Skills present in the repository but absent from the install root are distinguished
      from installed ones, because uninstalled skills cost nothing in a session.
- [ ] Malformed or missing front matter is a diagnostic, not a silent skip.
- [ ] A repository-level check reproduces the recorded baseline figures.

## Frontier
Blocked by `TK-01`. Unblocked once the unit and counted surfaces are frozen.

## Step-by-Step Plan
1. Add the measurement module against the frozen unit, reusing existing catalogue discovery.
2. Expose the read-only CLI surface with text and versioned JSON output.
3. Add fixtures for hidden skills, uninstalled skills, malformed front matter, and an empty
   catalogue.
4. Add one repository-level check that reproduces the baseline.

## Testing Plan
Deterministic unit fixtures for each case above, plus the repository-level reproduction.
Assert no writes, no network, and no ledger or run-state mutation.

## Out of Scope
- Measuring live consumption or cache behaviour.
- Editing any `SKILL.md` prose.
- Enforcing a ceiling, which belongs to `TK-04`.

```
