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
