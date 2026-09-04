---
ticket_schema: 1
ticket_id: "WDT-01"
execution_mode: AFK
blocked_by: []
---

# Deliver tracked wiki candidates through the canonical target

## Artifact Graph

- Artifact ID: `ticket:ticket-autopilot-cross-checkout-wiki-delivery:WDT-01`
- Role: `ticket`
- Parent: [Cross-checkout wiki delivery](../../specs/ticket-autopilot-cross-checkout-wiki-delivery.md)

## Parent Spec

[Cross-checkout wiki delivery](../../specs/ticket-autopilot-cross-checkout-wiki-delivery.md)

## What to Build

Implement the complete canonical-target delivery boundary from the parent specification. A post-integration run may remain in an isolated clone while an exact source worktree, tracked candidate store, logical wiki identity, and delivery branch belong to the path-bound canonical project repository. Resolve and persist that destination before provider mutation, require exact provider/normalized-remote agreement, and invoke tracked delivery in the destination repository without mutating any protected checkout.

Add a provider-free exact-record retry transaction for terminal pre-provider wiki delivery failures. It must bind the current record digest, actor, evidence, integrated ticket, immutable candidate, validated destination, and complete prior record. It may prepare a later ordinary resume but must not itself observe or mutate a provider.

The slice includes public CLI/status/operator documentation and the end-to-end security regression. It must preserve same-repository behavior and the existing strict path-specific LLM Wiki binding.

## Acceptance Criteria

- [ ] Candidate delivery persists a content-addressed target receipt binding canonical project root, Git common directory, safe wiki-relative path, provider, normalized remote, WikiSyncRef, candidate tree, manifest, and validation receipt before provider mutation.
- [ ] An independent run clone can deliver an exact candidate through the distinct canonical destination only when provider and normalized remote match exactly and the validated result names that destination.
- [ ] The branch/PR worktree is created from the canonical destination repository while run, source, and canonical protected checkout bytes remain unchanged.
- [ ] Existing same-repository tracked wiki delivery remains unchanged.
- [ ] Different provider/remote, absent or unsafe target, symlink/path escape, another candidate store, stale candidate/manifest/receipt, malformed result, and contradictory target receipt all fail before provider observation.
- [ ] A public exact-record retry command accepts only an integrated ticket with the expected current-record SHA-256, one eligible terminal pre-provider delivery failure, the unchanged candidate, actor, and durable evidence; it persists intent and complete predecessor provenance, replaces atomically, reads back, and replays idempotently.
- [ ] Retry rejects stale digest, absent candidate, partial/ambiguous provider state, branch/PR/authorization/merge evidence, non-integrated tickets, other failure reasons, and target drift without changing the ledger.
- [ ] Retry performs no provider operation and grants no publication, merge, reconciliation, cleanup, Pi-sync, or reload authority; later resume still consumes only the existing manual/autonomous wiki policy.
- [ ] Skill/README/CLI help and status explain run repository versus canonical wiki destination without weakening exact binding.
- [ ] Focused unit/integration tests and the full Ticket Autopilot, LLM Wiki, verification, extension, exact-tree, and Artifact Graph regression suites pass on the final projected tree.

## Frontier

Ready. MRA-01 code is integrated and its exact wiki candidate is frozen. The production record failed before provider observation, providing a concrete recovery fixture. No product decision or new remote authority is needed to implement this slice.

## Step-by-Step Implementation Plan

1. Introduce canonical wiki delivery-target parsing, Git/provider/remote/path validation, and a versioned content-addressed receipt.
2. Separate the run repository from the destination repository in post-integration sync and tracked delivery, preserving the exact-source and same-repository paths.
3. Persist/read back the target receipt before provider boundaries and keep every identity mismatch fail-closed.
4. Add the exact-record local retry transaction and CLI/status surfaces with intent-first atomic replacement, predecessor provenance, and idempotent replay.
5. Add an independent-clone/canonical-target integration fixture plus identity, tamper, stale-state, prior-provider-state, and protected-checkout negatives.
6. Update operator documentation and run final-tree quality against the exact delivery CandidateRef.

## Testing Plan

- Unit tests for target receipt construction, safe relative paths, Git common directory ownership, provider/remote equality, candidate and record digests, and retry classification.
- Integration tests with an independent run clone and a distinct canonical checkout sharing only the same normalized remote; injected provider proves the destination repository selected before any mutation.
- Negative tests for cross-remote/provider, symlink/path escape, candidate-store escape, stale manifest/receipt, dirty protected checkouts, and every forbidden retry state.
- Replay tests proving both target receipt and retry are byte-idempotent.
- Full Ticket Autopilot and LLM Wiki suites, verification-audit, extension tests, compileall, exact-tree readback, and Artifact Graph comparison.

## Out of Scope

- Weakening or rebinding `knowledge/llm-wiki-project.json`.
- Treating arbitrary paths or equal Git history as destination authority.
- Publishing or merging the MRA wiki candidate during implementation or verification.
- Transferring code merge, repository reconciliation, completion, cleanup, Pi-sync, or reload authority.
- Changing generated wiki content, catalog ownership, Omicron, MAR semantics, or unrelated terminal runs.
