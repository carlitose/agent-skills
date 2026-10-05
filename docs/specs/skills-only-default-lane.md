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
