---
type: source
title: "Make repository authority worktree-stable"
identity_key: ticket:ticket-autopilot-worktree-stable-repository-authority/MRA-01
identity_strength: stable
source_path: docs/tickets/ticket-autopilot-worktree-stable-repository-authority/done/01-make-repository-authority-worktree-stable.md
source_digest: sha256:c02f233471445c892dbc2f1e9622e97927852c53c2d6f12fbd0269967f317a43
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-04
created_provenance: git-commit
disposition_changed: 2026-09-04
disposition_changed_provenance: git-rename
run_id: repository-authority-worktree-stable-mra01-20260903
---

# Make repository authority worktree-stable

Compiled from `docs/tickets/ticket-autopilot-worktree-stable-repository-authority/done/01-make-repository-authority-worktree-stable.md`. Identity is `ticket:ticket-autopilot-worktree-stable-repository-authority/MRA-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-04** via `git-commit`
- Disposition changed: **2026-09-04** via `git-rename`

## Graph

- Parent source: [[sources/spec-ticket-autopilot-worktree-stable-repository-authority]]

## Run

Completed under autopilot run `repository-authority-worktree-stable-mra01-20260903`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-ticket-autopilot-worktree-stable-repository-authority-mra-01.md","payload_bytes":4617,"payload_sha256":"c02f233471445c892dbc2f1e9622e97927852c53c2d6f12fbd0269967f317a43"}],"payload_bytes":4617,"payload_sha256":"c02f233471445c892dbc2f1e9622e97927852c53c2d6f12fbd0269967f317a43","schema":1,"source_digest":"sha256:c02f233471445c892dbc2f1e9622e97927852c53c2d6f12fbd0269967f317a43","source_identity":"ticket:ticket-autopilot-worktree-stable-repository-authority/MRA-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":4617,"payload_sha256":"c02f233471445c892dbc2f1e9622e97927852c53c2d6f12fbd0269967f317a43","schema":1,"source_digest":"sha256:c02f233471445c892dbc2f1e9622e97927852c53c2d6f12fbd0269967f317a43","source_identity":"ticket:ticket-autopilot-worktree-stable-repository-authority/MRA-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "MRA-01"
execution_mode: AFK
blocked_by: []
---

# Make repository authority worktree-stable

## Artifact Graph

- Artifact ID: `ticket:ticket-autopilot-worktree-stable-repository-authority:MRA-01`
- Role: `ticket`
- Parent: [Worktree-stable repository authority](../../specs/ticket-autopilot-worktree-stable-repository-authority.md)

## Parent Spec

[Worktree-stable repository authority](../../specs/ticket-autopilot-worktree-stable-repository-authority.md)

## What to Build

Implement the complete repository-authority schema-2 boundary from the parent specification: a Git-common-directory, provider, and normalized-remote identity shared by linked worktrees but not independent clones; an explicit, content-addressed schema-1 migration transaction; and lazy, need-based authority consumption that does not block unrelated manual implementation.

The slice owns both merge and reconciliation authority stores, their CLI/status surfaces, migration receipts and provenance, operator documentation, and the cross-worktree regression suite. It must not apply any live authority migration or grant authority.

## Acceptance Criteria

- [ ] Newly granted merge and reconciliation authority uses schema 2 and binds the exact Git common directory, provider, and normalized remote while retaining the observing worktree only as non-authoritative context.
- [ ] Two linked worktrees inspect the same schema-2 state, while an independent clone with the same remote receives no authority.
- [ ] Complete schema-1 active and revoked envelopes remain inspectable from their original checkout; sibling worktrees report `legacy-binding-migration-required` instead of generic corruption.
- [ ] One explicit CLI transaction migrates exactly one authority kind using the expected old-state SHA-256 plus actor and durable evidence, writes intent before replacement, preserves predecessor grant/revocation provenance, validates exact readback, and replays idempotently.
- [ ] Migration rejects absent, malformed, symlinked, drifted, wrong-common-directory, wrong-remote, wrong-provider, wrong-kind, contradictory, and ambiguous state without mutating the old bytes.
- [ ] An unrelated manual run can proceed when no run-local merge adoption, open reconciliation gate, or matching proposal needs legacy authority; `merge-all` and reconciliation consumption remain blocked with exact migration guidance.
- [ ] CLI help, skill/operator documentation, status output, and deterministic receipts describe the new identity and authority boundaries without implying consent.
- [ ] Focused unit/integration tests plus the existing Ticket Autopilot, verification, extension, and Artifact Graph regression suites pass on the final projected tree.

## Frontier

Ready. WCA-01 and tracked wiki PR #224 are integrated. No product decision or live migration authority is required to implement this slice.

## Step-by-Step Implementation Plan

1. Introduce a shared schema-2 repository identity helper and versioned validation/serialization used by merge and reconciliation authority stores.
2. Update grant, revoke, inspect, and consume paths to distinguish active schema 2, original-root legacy state, sibling migration-required state, and independent-clone absence.
3. Add the explicit migration command with content-addressed intent, predecessor provenance, atomic replacement/readback, and idempotent receipt semantics.
4. Make scheduler authority lookup lazy so irrelevant legacy state cannot block manual work, while mutation/adoption paths remain fail-closed.
5. Add cross-worktree, independent-clone, fixture, tamper, replay, and CLI tests; update public documentation.
6. Run final-tree projection and re-run all required quality gates against the exact delivery CandidateRef.

## Testing Plan

- Unit tests for identity normalization, schema validation, migration digest and receipt construction, atomic replacement, and failure classifications.
- Integration tests using one repository, two linked worktrees, and one independent clone with the same remote.
- Scheduler/CLI tests proving irrelevant legacy state is non-blocking and consumption remains gated.
- Full Ticket Autopilot, verification-audit, extension, and Artifact Graph regressions on the exact final tree.

## Out of Scope

- Applying a migration to any live repository authority file.
- Granting, revoking, renewing, broadening, or consuming repository authority.
- Resolving PR conflicts or bypassing provider checks and expected-head guards.
- Changing tracked-wiki, Pi synchronization, bootstrap, cleanup, or unrelated source authority.

```
