---
type: source
title: "Implement the decided decoding `errors` policy"
identity_key: ticket:windows-text-fidelity/WT-03
identity_strength: stable
source_path: docs/tickets/windows-text-fidelity/done/03-implement-decoding-errors-policy.md
source_digest: sha256:b7223f6f6c5e397ba3f189c019a3f7b31928b29ca0600e79dc8cc9e246df748d
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-12
created_provenance: git-commit
disposition_changed: 2026-08-13
disposition_changed_provenance: git-rename
---

# Implement the decided decoding `errors` policy

Compiled from `docs/tickets/windows-text-fidelity/done/03-implement-decoding-errors-policy.md`. Identity is `ticket:windows-text-fidelity/WT-03`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-12** via `git-commit`
- Disposition changed: **2026-08-13** via `git-rename`

## Graph

- Parent source: [[sources/artifact-windows-text-fidelity-wayfinder]]
- Blocked by: [[sources/ticket-windows-text-fidelity-wt-02]] — `ticket:windows-text-fidelity/WT-02`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-windows-text-fidelity-wt-03.md","payload_bytes":2426,"payload_sha256":"b7223f6f6c5e397ba3f189c019a3f7b31928b29ca0600e79dc8cc9e246df748d"}],"payload_bytes":2426,"payload_sha256":"b7223f6f6c5e397ba3f189c019a3f7b31928b29ca0600e79dc8cc9e246df748d","schema":1,"source_digest":"sha256:b7223f6f6c5e397ba3f189c019a3f7b31928b29ca0600e79dc8cc9e246df748d","source_identity":"ticket:windows-text-fidelity/WT-03","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2426,"payload_sha256":"b7223f6f6c5e397ba3f189c019a3f7b31928b29ca0600e79dc8cc9e246df748d","schema":1,"source_digest":"sha256:b7223f6f6c5e397ba3f189c019a3f7b31928b29ca0600e79dc8cc9e246df748d","source_identity":"ticket:windows-text-fidelity/WT-03"} -->
```markdown
---
ticket_schema: 1
ticket_id: "WT-03"
execution_mode: AFK
blocked_by:
  - "WT-02"
---

# Implement the decided decoding `errors` policy

## Artifact Graph
- Artifact ID: `artifact:wt-03-implement-decoding-errors-policy`
- Role: `ticket`
- Parent: [windows-text-fidelity-wayfinder.md](../../specs/windows-text-fidelity-wayfinder.md)

## Parent Spec
[windows-text-fidelity-wayfinder.md](../../specs/windows-text-fidelity-wayfinder.md)

## What to Build
Apply the policy confirmed in `WT-02` to all five `subprocess.run` call sites in
`git_ops.py`, and reconcile `test_utf8_io.py` with it so the invariant is asserted rather
than merely held.

Current state on CandidateRef `acd881c`: `errors="replace"` at every site, and
`test_command_runner_decodes_stdout_and_stderr_as_utf8` fails with `'strict' != 'replace'`.
On base `d306799` the same test is green. This ticket ends with that test green again,
asserting whatever `WT-02` decided.

## Acceptance Criteria
- [ ] Every `subprocess.run` call site in `git_ops.py` matches the decided policy.
- [ ] `test_utf8_io.py` asserts the decided policy and passes.
- [ ] A non-ASCII payload still survives the runner character-identical, preserving
      `WD-02`'s third acceptance criterion.
- [ ] If the decision separates diagnostic from data paths, a test covers each path
      distinctly.
- [ ] If the decision permits `replace` anywhere a value feeds an equality check, a test
      documents what happens to an undecodable byte there.

## Frontier
Dependency-blocked on `WT-02`. No implementation may begin before that decision is
confirmed; guessing the policy here is what produced the regression in the first place.

## Step-by-Step Implementation Plan
1. Read the decision spec produced by `WT-02`.
2. Apply it to `SubprocessCommandRunner.run`, `run_git`, `origin_url`, and both call sites
   in `assert_cleanup_safe`. Checkpoint: no site left at a default.
3. Update `test_utf8_io.py` to assert the decision. Checkpoint: green.
4. Add the path-distinguishing tests the decision implies.

## Testing Plan
Automated: `test_utf8_io` plus any new per-path tests. Manual: reproduce a provider failure
on a non-English Windows locale and confirm the diagnostic is readable — this is the
observation that motivated the change and it is not covered by any automated test today.

## Out of Scope
- Choosing the policy, which is `WT-02`.
- The body round trip, which is `WT-01`.

```
