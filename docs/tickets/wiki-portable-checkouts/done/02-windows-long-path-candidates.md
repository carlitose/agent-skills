---
ticket_schema: 1
ticket_id: "APM-11"
execution_mode: AFK
blocked_by:
  - "APM-10"
---

# Deliver long-path wiki candidates on Windows and recover the exact pre-provider failure

## Artifact Graph
- Artifact ID: `artifact:autopilot-practical-reliability-apm-11`
- Role: `ticket`
- Parent: [Practical Reliability for Ticket Autopilot](../../specs/autopilot-practical-reliability.md)

## Parent Spec
[Practical Reliability for Ticket Autopilot](../../specs/autopilot-practical-reliability.md) — S11 — Windows Long-Path Wiki Candidate Delivery; consumes S10's portable binding and source/target behavior.

## What to Build
Fix native filesystem handling through the complete frozen-wiki validation and delivery path, not only a string helper or binding value. The observed 262-character absolute candidate path failed ordinary Windows stat but was regular through the extended-length native form. Publication reported `delivery-invalid: tracked wiki candidate contains a non-regular path` after successful compilation of 23 changed files and zero lint errors.

Retain the content-addressed candidate layout and all regular-file, containment, UTF-8, digest, target, and exact-source checks. Keep native filesystem representation separate from repository-relative POSIX Git/manifest paths. Reuse the existing exact-record wiki retry transaction for this narrowly revalidated pre-provider false negative; its present predicate accepts only the older outside-project failure.

## Acceptance Criteria
- [ ] A native Windows regression reproduces the original >=262-character absolute-path failure before the fix and passes enumeration, regular-file validation, strict reads, digest checks, isolated Git materialization, and delivery readback after the fix. Short-path behavior remains correct.
- [ ] The full flow uses APM-10's portable binding and canonical target with an exact source checkout. Deep paths, spaces/non-ASCII names, and platform-appropriate drive/UNC handling are covered; a mocked UNC case is not reported as live network-share evidence.
- [ ] Native long-path spelling does not leak into Markdown links, Git index paths, logical identities, or existing serialized identity fields. Candidate file names, content-addressed directory names, payload bytes, manifests, and receipts are not shortened or rewritten.
- [ ] Genuinely missing, linked, non-regular, executable, escaped, unreadable, invalid UTF-8, or digest-mismatched paths still fail. Filesystem access failures are distinguished from invalid file types where possible; stat failure is never accepted as proof of regularity.
- [ ] The existing retry status/apply boundary can recognize only a fully revalidated eligible terminal pre-provider long-path false negative using the existing exact-record digest and actor/evidence inputs. It retains the complete predecessor, records the owned transition, makes zero provider calls, and replays idempotently. The older outside-project recovery case still works.
- [ ] Wrong record digest, changed bytes/manifest/receipt, wrong target, actual invalid file types, prior provider mutation/uncertain outcomes, and contradictory retry state remain ineligible. A substring match on the old error is not sufficient eligibility.
- [ ] Isolated sync/delivery/recovery tests preserve protected source/canonical worktrees and integrated-ticket state. Injected-provider success is reported as local evidence, not live publication.
- [ ] After implementation integration, report whether the recorded APM-PREP-01 candidate is recoverable through the owned command. Actual historical recovery requires its real inputs; missing authority is a visible post-integration gate, never grounds to hand-edit the terminal ledger or recreate a possibly published candidate.

## Frontier
Dependency-blocked by [APM-10](01-portable-project-binding.md). This end-to-end slice consumes its portable configuration and canonical-target semantics, and serializes changes in the shared wiki owners.

Execute inline. AFK does not authorize subagents, provider mutation, recovery inputs, or merge. No new security/approval framework is needed; use the existing transactions and evidence boundaries.

## Step-by-Step Implementation Plan
1. Build a bounded disposable reproduction of the native long-path access failure and inspect `wiki_sync._frozen_files`, candidate production, target validation, materialization, and retry predicates. Completion: the failing production path and the separate current retry rejection are both observed without changing the historical record.
2. Adapt only the owning native-I/O boundary and its consumers. Completion: the production flow reads and materializes the unchanged long candidate while Git paths and serialized identity remain unchanged.
3. Extend the existing retry eligibility/replay validation for the exact fully revalidated long-path false negative. Completion: positive/replay fixtures preserve the predecessor and make no provider calls; the full negative matrix remains rejected.
4. Exercise portable-binding sync through isolated delivery with an injected provider and independent byte/tree assertions. Completion: long and short cases pass with protected trees unchanged and no duplicate publication behavior.
5. Run relevant wiki/sync regression suites and document supported native behavior plus the recovery command's precise eligibility. Completion: record actual tests, skips/unavailable environments, and historical recovery status without claiming live publication.

## Testing Plan
- Native Windows reproduction: the observed relative filename `wiki/sources/artifact-artifact-graph-disposition-drift-diagnostic.md` under the digest-addressed store, producing an absolute path of at least 262 characters; compare short and deep/Unicode cases.
- Integration: `llm-wiki/tests/test_sync_project.py`, `ticket-autopilot/tests/test_wiki_sync.py`, and `test_wiki_sync_forward_matrix.py`; actual filesystem/Git effects plus a provider seam, not a pre-decoded or always-regular fake filesystem.
- Recovery: eligible pre-provider historical-shaped record, complete predecessor/readback, exact replay, every stale/unsafe/ambiguous negative, and regression for the existing outside-project failure.
- Observe Windows and POSIX independently; report unavailable symlink/network/platform capabilities rather than suppressing or overstating them. Never change registry, global Git settings, or user directory layout to make the fixture pass.

These are planned checks. The observed production failure is not proof that the proposed implementation works.

## Out of Scope
- APM-02's final-tree Git receipt separator fix, APM-09's Azure JSON decoding, general process limits, or a generic path/retry framework.
- Weakening validation, shortening identity-bearing digests, deleting/moving uncertain worktrees, modifying frozen evidence, direct terminal-ledger edits, or broad automatic terminal retries.
- Folding generated wiki files into the implementation candidate, transferring application merge grants to wiki publication, or updating installed/global Pi copies.
