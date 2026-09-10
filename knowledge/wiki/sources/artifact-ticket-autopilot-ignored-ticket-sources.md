---
type: source
title: "Ticket Autopilot Ignored Ticket Sources"
identity_key: artifact:ticket-autopilot-ignored-ticket-sources
identity_strength: stable
source_path: docs/specs/ticket-autopilot-ignored-ticket-sources.md
source_digest: sha256:451fb9f91d184d226e115c882c955c2a81626be1f6225fdb4991ed19d33ac508
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-08-05
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Ticket Autopilot Ignored Ticket Sources

Compiled from `docs/specs/ticket-autopilot-ignored-ticket-sources.md`. Identity is `artifact:ticket-autopilot-ignored-ticket-sources`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-05** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Child source: [[sources/ticket-ticket-autopilot-ignored-ticket-sources-is-01]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"decisions":{"headings":[],"status":"not-identified"},"exclusions":{"headings":[],"status":"not-identified"},"goals":{"headings":[6],"status":"present"},"invariants":{"headings":[13],"status":"present"},"verification":{"headings":[19],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/artifact-ticket-autopilot-ignored-ticket-sources.md","payload_bytes":7687,"payload_sha256":"451fb9f91d184d226e115c882c955c2a81626be1f6225fdb4991ed19d33ac508"}],"payload_bytes":7687,"payload_sha256":"451fb9f91d184d226e115c882c955c2a81626be1f6225fdb4991ed19d33ac508","schema":1,"source_digest":"sha256:451fb9f91d184d226e115c882c955c2a81626be1f6225fdb4991ed19d33ac508","source_identity":"artifact:ticket-autopilot-ignored-ticket-sources","source_kind":"spec"} -->

| Topic | Source sections |
|---|---|
| goals | 6: Goal |
| exclusions | no matching section identified in the source; complete source retained |
| decisions | no matching section identified in the source; complete source retained |
| invariants | 13: Semantic Invariants |
| verification | 19: Verification Strategy |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":7687,"payload_sha256":"451fb9f91d184d226e115c882c955c2a81626be1f6225fdb4991ed19d33ac508","schema":1,"source_digest":"sha256:451fb9f91d184d226e115c882c955c2a81626be1f6225fdb4991ed19d33ac508","source_identity":"artifact:ticket-autopilot-ignored-ticket-sources"} -->
```markdown
# Ticket Autopilot Ignored Ticket Sources

## Type

Architecture spec

## Status

Implemented baseline; ignored-to-tracked promotion defect open.

## Artifact Graph

- Artifact ID: `artifact:ticket-autopilot-ignored-ticket-sources`
- Role: `spec`
- Standalone: true

### Children

- [IS-01 Gate ignored-to-tracked source promotion](../tickets/ticket-autopilot-ignored-ticket-sources/done/01-gate-ignored-to-tracked-source-promotion.md)

## Source

- [GitHub issue #21 — Autopilot ticket should be used also with docs gitignored](https://github.com/carlitose/agent-skills/issues/21)

## Goal

Allow `ticket-autopilot` to plan and execute a canonical ticket folder under a Git-ignored
repository path without requiring those ticket files to exist in the isolated worktree or
silently adding them to the implementation pull request.

## Current Behavior

- `run` calls `assert_ticket_folder_at_ref`, which requires the folder to be inside the
  repository, clean, tracked, and present at the selected base ref. An ignored folder is
  therefore rejected before the run worktree is created.
- `finalize_done` reconstructs the ticket path inside the isolated worktree, moves it to
  `done/`, stages the move, and writes a staged completion summary. Ignored source tickets
  do not exist in that worktree.
- The canonical parser already turns each ticket into a normalized envelope, body, path,
  and digest; the missing boundary is durable source ownership, not ticket parsing.

## Target Behavior

### Source classification

Before creating a run, classify the ticket folder as exactly one of:

- `tracked`: the existing clean-at-base contract;
- `ignored`: inside the repository and positively matched by `git check-ignore` for every
  consumed ticket artifact;
- rejected: outside the repository, partly ignored, or untracked but not ignored.

The runner must not infer that arbitrary untracked files are intentional ticket input.

### Managed snapshot

For either accepted source mode, parse every ticket through the canonical Ticket Envelope
parser and atomically snapshot the normalized envelope, body, relative source path, and
content digest under the run's managed Git-common directory before worktree creation. The
ledger binds to the snapshot manifest and source mode; resume consumes the snapshot rather
than reparsing mutable caller files.

The managed snapshot is scheduler input, not implementation evidence and not a substitute
for the ticket digest inside `CandidateRef`.

### Finalization

- `tracked` mode preserves the existing isolated-worktree move, completion summary, and
  staging behavior.
- `ignored` mode never stages or commits the ignored ticket source. At the same terminal
  boundary, it atomically moves the exact digest-matched caller source into its ignored
  `done/` directory and writes the completion summary beside it.
- The external move has a durable intent/applied receipt. Resume after a crash converges on
  either the original exact source or the exact destination; contradictory or modified
  content opens a gate instead of overwriting either path.

### Source-mode promotion

The snapshot source mode remains immutable run input, but it cannot by itself select the
finalization adapter after the candidate or an integrated stack ancestor changes Git
tracking policy.

Before commit, push, PR mutation, and descendant reconciliation, the runner compares the
snapshot classification with the candidate and current base classification of every
ticket source. An `ignored` source that becomes tracked is `source-mode-drift`. The runner
must fail closed before publication, report the exact old and new classifications, and
require an explicit source-publication change followed by a new run from a tracked base.
It must not silently reinterpret the existing snapshot or leave a tracked ticket at its
open path while recording external-only completion.

This specification does not introduce an implicit `ignored` to `tracked` migration. Such a
migration would need a separate versioned contract for ownership, stacked descendants,
completion records, and crash recovery.

## Semantic Invariants

- The executed envelope and body equal the immutable managed snapshot.
- Ignored ticket content never appears in a PR unless the implementation independently
  changes Git tracking policy.
- A candidate or integrated ancestor that changes an ignored ticket to tracked cannot use
  ignored external-only finalization or publish the ticket at its open path.
- A source change after snapshot cannot silently change acceptance criteria or be
  overwritten during finalization.
- Ticket completion remains idempotent and observable in the ledger and source folder.
- Caller files outside the accepted ticket folder remain untouched.

## External Contract Changes

- `plan`, `run`, `status`, and final reports expose `ticket_source_mode` and the snapshot
  manifest digest.
- `run <folder>` accepts a fully ignored in-repository ticket folder without an additional
  unsafe override.
- Existing tracked folders keep their current behavior.

If ledger persistence changes, incompatible active ledgers fail with a clear version error;
there is no silent reinterpretation.

## Failure Modes

- Mixed tracked/ignored ticket inputs.
- An ignore rule changes between planning and run creation.
- A candidate or integrated stack ancestor promotes an ignored ticket source to tracked
  after the run snapshot is frozen.
- A source ticket changes or disappears after snapshot but before its finalization effect.
- A crash occurs between the ignored-source move and receipt persistence.
- The destination already exists with contradictory content.

Every case fails closed or resumes from the exact recorded effect identity.

## Security and Data Concerns

- Keep snapshots under the run-managed Git-common directory with path containment checks.
- Reject symlink escapes and source/destination paths outside the accepted folder.
- Do not persist credentials or unrelated ignored files in the snapshot.
- Snapshot only parser-consumed ticket files, not the entire ignored `docs/` tree.

## Alternatives

- Force users to track tickets: rejected because it does not resolve issue #21.
- Copy the ignored folder into every worktree: rejected because it risks committing ignored
  planning data and creates two mutable sources.
- Accept every untracked folder: rejected because Git ignore is the explicit repository
  intent that distinguishes managed external input from accidental local files.

## Implementation Slice

Ticket `04` in
[`docs/tickets/ticket-autopilot-delivery-merge`](../tickets/ticket-autopilot-delivery-merge/)
owns source classification, snapshots, dual-mode finalization, reporting, and causal tests.

Follow-up ticket
[IS-01](../tickets/ticket-autopilot-ignored-ticket-sources/done/01-gate-ignored-to-tracked-source-promotion.md)
owns source-mode drift detection, stacked-run revalidation, the regression found in run
`7974966ec8d84a35`, and evidence-bound repair of its stranded TK-01, TK-02, and TK-03
ticket dispositions.

## Verification Strategy

- Unit tests for classification, containment, manifest hashing, and source drift.
- Integration tests for tracked parity, fully ignored sources, mixed/untracked rejection,
  crash-resume around the external move, and contradictory destinations.
- A regression fixture starts with a fully ignored folder, promotes its ticket paths in a
  candidate or integrated ancestor, and proves publication stops at `source-mode-drift`
  before commit, push, or PR mutation.
- Git assertions proving ignored tickets and summaries never enter the implementation
  commit while intended code changes still do.

```
