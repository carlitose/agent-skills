---
type: source
title: "Make final-tree receipt paths portable at the real Git boundary"
identity_key: ticket:autopilot-practical-reliability/APM-02
identity_strength: stable
source_path: docs/tickets/autopilot-practical-reliability/done/02-portable-git-paths.md
source_digest: sha256:b6fd22f797eed1556d872e22e9c989a327756a35266672c71a6479a3f9034f68
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-07
created_provenance: git-commit
disposition_changed: 2026-09-07
disposition_changed_provenance: git-rename
run_id: apm-practical-reliability
---

# Make final-tree receipt paths portable at the real Git boundary

Compiled from `docs/tickets/autopilot-practical-reliability/done/02-portable-git-paths.md`. Identity is `ticket:autopilot-practical-reliability/APM-02`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-07** via `git-commit`
- Disposition changed: **2026-09-07** via `git-rename`

## Graph

- Parent source: [[sources/artifact-autopilot-practical-reliability]]

## Run

Completed under autopilot run `apm-practical-reliability`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-autopilot-practical-reliability-apm-02.md","payload_bytes":3093,"payload_sha256":"b6fd22f797eed1556d872e22e9c989a327756a35266672c71a6479a3f9034f68"}],"payload_bytes":3093,"payload_sha256":"b6fd22f797eed1556d872e22e9c989a327756a35266672c71a6479a3f9034f68","schema":1,"source_digest":"sha256:b6fd22f797eed1556d872e22e9c989a327756a35266672c71a6479a3f9034f68","source_identity":"ticket:autopilot-practical-reliability/APM-02","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3093,"payload_sha256":"b6fd22f797eed1556d872e22e9c989a327756a35266672c71a6479a3f9034f68","schema":1,"source_digest":"sha256:b6fd22f797eed1556d872e22e9c989a327756a35266672c71a6479a3f9034f68","source_identity":"ticket:autopilot-practical-reliability/APM-02"} -->
```markdown
---
ticket_schema: 1
ticket_id: "APM-02"
execution_mode: AFK
blocked_by: []
---

# Make final-tree receipt paths portable at the real Git boundary

## Artifact Graph
- Artifact ID: `artifact:autopilot-practical-reliability-apm-02`
- Role: `ticket`
- Parent: [Practical Reliability for Ticket Autopilot](../../specs/autopilot-practical-reliability.md)

## Parent Spec
[Practical Reliability for Ticket Autopilot](../../specs/autopilot-practical-reliability.md) — S2 — Portable Final-Tree Git Paths.

## What to Build
Fix the receipt-path defect where str(Path(destination).with_suffix('.completion.json')) produces backslashes on Windows and git update-index --cacheinfo rejects the path. Make receipt derivation, manifest validation, temporary-index planning, and transaction application share repository-relative POSIX Git paths while filesystem operations retain native Path semantics.

## Acceptance Criteria
- [ ] Nested ticket and receipt paths use forward slashes at every Git index/tree boundary on Windows and POSIX; deriving a receipt cannot reintroduce native separators.
- [ ] A temporary-repository test exercises the production projection and application path through real git update-index/write-tree, not only a string helper or fake Git response.
- [ ] Completion bytes, modes, manifests, candidate binding, expected changed paths, and replay behavior remain correct; projection is not reported as integration.
- [ ] Invalid/outside-repository paths remain rejected and unrelated final-tree eligibility behavior is unchanged.
- [ ] The preceding exit-128 backslash reproduction is covered. Any remaining EOL fixture failure is reported separately for APM-03, not claimed fixed.

## Frontier
Ready. No unresolved product decision; missing execution environments must be reported.

Execute inline. AFK does not authorize subagents; explicit user request is required. This ticket does not authorize provider publication or merge.

## Step-by-Step Implementation Plan
1. Reproduce the nested receipt failure in an explicitly configured disposable Git repository and inspect receipt construction/validation in final_tree_projection.py and final_tree_transaction.py.
2. Use the existing path owner consistently at the Git boundary; avoid a new general path framework.
3. Add production-path planning, application, and replay checks for nested paths and paths containing spaces/non-ASCII characters.
4. Run focused final-tree and relevant kernel tests, separating path success from any known line-ending fixture failures.

## Testing Plan
- Real local Git integration: nested receipt, expected final tree, unchanged payload bytes, replay, and invalid path rejection.
- Run on Windows and POSIX where available; explicitly report an unavailable platform instead of calling a mocked branch a native-platform pass.

These are planned checks, not evidence that implementation or verification has occurred.

## Out of Scope
- Relaxing digest/path validation or disabling final-tree projection.
- Global Git configuration changes, provider mutation, or unrelated Windows provider fixes.

```
