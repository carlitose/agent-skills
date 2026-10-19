---
type: source
title: "Skills-only as the default lane, plus a direct lane for small changes"
identity_key: artifact:skills-only-default-lane
identity_strength: stable
source_path: docs/specs/skills-only-default-lane.md
source_digest: sha256:da7264ff4e8920740e590d2e416ddeb2402329b1e9b949700d7e1d6aa8484354
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-10-05
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Skills-only as the default lane, plus a direct lane for small changes

Compiled from `docs/specs/skills-only-default-lane.md`. Identity is `artifact:skills-only-default-lane`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-05** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Child source: [[sources/ticket-skills-only-default-lane-sdl-01]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"decisions":{"headings":[],"status":"not-identified"},"exclusions":{"headings":[7],"status":"present"},"goals":{"headings":[],"status":"not-identified"},"invariants":{"headings":[6],"status":"present"},"verification":{"headings":[8],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/artifact-skills-only-default-lane.md","payload_bytes":2737,"payload_sha256":"da7264ff4e8920740e590d2e416ddeb2402329b1e9b949700d7e1d6aa8484354"}],"payload_bytes":2737,"payload_sha256":"da7264ff4e8920740e590d2e416ddeb2402329b1e9b949700d7e1d6aa8484354","schema":1,"source_digest":"sha256:da7264ff4e8920740e590d2e416ddeb2402329b1e9b949700d7e1d6aa8484354","source_identity":"artifact:skills-only-default-lane","source_kind":"spec"} -->

| Topic | Source sections |
|---|---|
| goals | no matching section identified in the source; complete source retained |
| exclusions | 7: Non-goals |
| decisions | no matching section identified in the source; complete source retained |
| invariants | 6: Invariants |
| verification | 8: Verification |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2737,"payload_sha256":"da7264ff4e8920740e590d2e416ddeb2402329b1e9b949700d7e1d6aa8484354","schema":1,"source_digest":"sha256:da7264ff4e8920740e590d2e416ddeb2402329b1e9b949700d7e1d6aa8484354","source_identity":"artifact:skills-only-default-lane"} -->
```markdown
# Skills-only as the default lane, plus a direct lane for small changes

## Artifact Graph
- Artifact ID: `artifact:skills-only-default-lane`
- Role: `spec`
- Standalone: true

### Children
- [SDL-01: default skills-only and direct lane](../tickets/skills-only-default-lane/01-default-and-direct-lane.md)

## Type and Status
Feature/decision spec. Human request, 2026-10-05: make skills-only the default and let small
tasks skip Autopilot and its ceremony entirely.

## Current behavior
- The injected policy (`extensions/mandatory-agent-skills.ts`), `ask-skills`, and `README.md`
  make `to-spec -> to-tickets -> ticket-autopilot` the default. Skills-only needs an explicit
  request and is then a "restriction" kept until lifted.
- Every shippable change, however small, needs a spec, a canonical ticket, `execute-ticket`
  and a Verification Record. "Do not edit a deliverable directly from a loose request."

## Target behavior
Three delivery lanes, chosen and stated at routing:

1. **Skills-only (default).** `to-spec -> to-tickets -> execute-ticket` inline. No runner,
   scheduler or driver. AFK, "continue" and compaction keep this lane.
2. **Direct lane (small changes).** Edit directly, without spec, ticket, CandidateRef or
   Verification Record. Eligible when the user asks for a quick/direct change, or when the
   change is small: one coherent edit, about three files and 100 changed lines at most, no new
   or changed public contract, schema, data migration, dependency, or security/authority/
   delivery policy. Required: run the affected tests/lint, re-read the diff, report in a few
   lines. Escalate to skills-only as soon as the change outgrows these limits or needs a
   design decision. Git/provider delivery keeps its usual authority and CI checks.
3. **Autopilot (on request).** `to-spec -> to-tickets -> ticket-autopilot` only when the user
   explicitly asks for Autopilot or AFK runner orchestration of a ticket folder. The explicit
   "merge all" / "authorize everything" operational routes are unchanged.

## Invariants
- No lane grants merge, publication, installation or reload authority.
- The lifecycle-only `change-status-ticket` lane is unchanged.
- Canonical contracts (ticket parser, CandidateRef, verification validator) are unchanged and
  still required in the skills-only and Autopilot lanes.
- Fail-closed readiness: missing core workflow skills still block mutation.

## Non-goals
- Changing Autopilot itself or the Verification Record contract (the lighter bundle is a
  separate request).
- Updating historical specs, tickets or the wiki.

## Verification
Extension unit tests (`node --test`) for the policy text and `/agent-skills-flow` message;
repository lint (file-size limits); CI.

```
