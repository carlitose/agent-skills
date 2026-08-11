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
- Parent: [Autopilot Token Economics](../../specs/autopilot-token-economics-wayfinder.md)

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
