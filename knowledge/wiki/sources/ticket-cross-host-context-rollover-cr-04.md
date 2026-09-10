---
type: source
title: "Prove cross-host rollover live"
identity_key: ticket:cross-host-context-rollover/CR-04
identity_strength: stable
source_path: docs/tickets/cross-host-context-rollover/done/04-prove-cross-host-rollover-live.md
source_digest: sha256:20585d01c7704981348c3bfde12e84dff51d3db039a83d0e00a89aa911ccc13e
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-11
created_provenance: git-commit
disposition_changed: 2026-08-29
disposition_changed_provenance: git-rename
run_id: cr-autocompact-removal-20260829
---

# Prove cross-host rollover live

Compiled from `docs/tickets/cross-host-context-rollover/done/04-prove-cross-host-rollover-live.md`. Identity is `ticket:cross-host-context-rollover/CR-04`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-11** via `git-commit`
- Disposition changed: **2026-08-29** via `git-rename`

## Graph

- Parent source: [[sources/artifact-cross-host-context-rollover-wayfinder]]
- Blocked by: [[sources/ticket-cross-host-context-rollover-cr-02]] — `ticket:cross-host-context-rollover/CR-02`
- Blocked by: [[sources/ticket-cross-host-context-rollover-cr-03]] — `ticket:cross-host-context-rollover/CR-03`
- Blocked by: [[sources/ticket-cross-host-context-rollover-cr-06]] — `ticket:cross-host-context-rollover/CR-06`

## Run

Completed under autopilot run `cr-autocompact-removal-20260829`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[5],"status":"present"},"exclusions":{"headings":[9],"status":"present"},"frontier":{"headings":[6],"status":"present"},"intent":{"headings":[],"status":"not-identified"},"testing":{"headings":[8],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-cross-host-context-rollover-cr-04.md","payload_bytes":3808,"payload_sha256":"20585d01c7704981348c3bfde12e84dff51d3db039a83d0e00a89aa911ccc13e"}],"payload_bytes":3808,"payload_sha256":"20585d01c7704981348c3bfde12e84dff51d3db039a83d0e00a89aa911ccc13e","schema":1,"source_digest":"sha256:20585d01c7704981348c3bfde12e84dff51d3db039a83d0e00a89aa911ccc13e","source_identity":"ticket:cross-host-context-rollover/CR-04","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | no matching section identified in the source; complete source retained |
| acceptance | 5: Acceptance Criteria |
| testing | 8: Testing Plan |
| frontier | 6: Frontier |
| exclusions | 9: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3808,"payload_sha256":"20585d01c7704981348c3bfde12e84dff51d3db039a83d0e00a89aa911ccc13e","schema":1,"source_digest":"sha256:20585d01c7704981348c3bfde12e84dff51d3db039a83d0e00a89aa911ccc13e","source_identity":"ticket:cross-host-context-rollover/CR-04"} -->
```markdown
---
ticket_schema: 1
ticket_id: "CR-04"
execution_mode: HITL
blocked_by:
  - "CR-02"
  - "CR-03"
  - "CR-06"
---

# Prove cross-host rollover live

## Artifact Graph

- Artifact ID: `artifact:cr-04-prove-cross-host-rollover-live`
- Role: `ticket`
- Parent: [Cross-host Context Rollover](../../specs/cross-host-context-rollover-wayfinder.md)

## Parent Spec

[Cross-host Context Rollover](../../specs/cross-host-context-rollover-wayfinder.md)

## Type

Live proof

## What to Prove

Run one user-controlled Codex rollover and one user-controlled Claude Code rollover using the
two disposable tracer bullets after the CR-06 Claude retrofit. Observe the real session
boundary, hook events, handoff
validation, new-session creation, bootstrap submission, and durable frontier reconstruction.

This ticket owns the human authority and live host boundary. It does not turn a passing
prototype into a production release by implication.

## Acceptance Criteria

- [ ] The user confirms the two source sessions, working directory, threshold fixture, and
      permission to create replacement sessions before the runs begin.
- [ ] Each run records the source session identity, observed count, trigger, handoff path and
      digest, replacement session identity, hook events, and reconstruction result without
      retaining transcript content.
- [ ] Each host records the current-context value immediately below and at/above 150,000,
      proves that crossing only arms `rollover_pending`, and proves no active task is
      interrupted.
- [ ] No replacement session starts until the handoff validates and the source turn has
      stopped.
- [ ] Each replacement reads the Wayfinder map, canonical ticket inventory, current run
      status, and correct next frontier from durable pointers.
- [ ] Expiry, cleanup, one-shot consumption, retry, and multi-chat collision behavior are
      exercised or explicitly left unobserved.
- [ ] Codex and Claude Code limitations are compared without treating one host's evidence as
      proof for the other.
- [ ] The Claude run requires no `--autocompact`; it records the supported CR-05 capability
      or reports a visible `no-go` if early compaction prevents the fixed threshold.
- [ ] The result recommends operator-visible, controller-managed, compaction-only, or no-go
      production direction for each host.
- [ ] Any production follow-up is recorded through `to-spec` and new tracer-bullet tickets;
      this live proof does not silently install hooks or controllers.

## Frontier

Blocked by `CR-02`, `CR-03`, and `CR-06`, then by human availability and permission to
create the two
replacement sessions.

## Step-by-Step Implementation Plan

1. Review the reduced evidence and limitations from both prototypes plus CR-05/CR-06 with
   the user.
2. Bind the live run inputs and authority to the exact prototype versions.
3. Execute the Codex rollover and capture sanitized causal evidence.
4. Execute the Claude Code rollover and capture sanitized causal evidence.
5. Compare the two observations and record the production-design recommendation.
6. Delete or retain each private handoff according to the confirmed expiry policy.

## Testing Plan

The evidence is the two live, user-controlled observations. Local fixtures remain supporting
evidence only. Failure to observe a host boundary is recorded as unavailable or blocked, not
converted into a passing simulated claim.

## Out of Scope

- Installing a production controller, global hook, scheduled task, or service.
- Clearing unrelated chats or selecting sessions by recency alone.
- Copying provider transcripts into repository artifacts.
- Claiming production readiness from one successful rollover per host.
- Restoring `--autocompact` as a prerequisite or treating its help entry as live evidence.

```
