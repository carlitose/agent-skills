---
ticket_schema: 1
ticket_id: "ICR-01"
execution_mode: AFK
blocked_by: []
---

# Reconcile an exact single-parent integration copy

## Artifact Graph

- Artifact ID: `ticket:ticket-autopilot-post-merge-integration-copy-reconciliation:ICR-01`
- Role: `ticket`
- Parent: [Post-merge integration-copy reconciliation](../../specs/ticket-autopilot-post-merge-integration-copy-reconciliation.md)

## Parent Spec

[Post-merge integration-copy reconciliation](../../specs/ticket-autopilot-post-merge-integration-copy-reconciliation.md)

## What to Build

Extend EHR-01's exact equivalent-head proof with the accepted `single-parent-integration-copy` topology. New schema-2 receipts must distinguish it from `two-parent-head-merge`, while historical schema-1 two-parent receipts remain loadable and exactly replayable. Preserve receipt-first crash ordering, read-only provider behavior, and separate ordinary terminal integration proof.

The implementation must reproduce the historical Betsharemarket PR #248 object shape in disposable real Git: recorded and observed one-commit deliveries on different bases, a distinct integration commit that is a sibling of the observed head on the observed base, identical observed/integration trees, three byte-identical non-empty raw transitions, and terminal reachability of only the integration commit.

## Acceptance Criteria

- [ ] New proof emits schema-2 receipts with exact topology `two-parent-head-merge` or `single-parent-integration-copy` and rejects unknown or contradictory schema/topology shapes.
- [ ] The sibling topology requires distinct observed/integration SHAs, the same exact one parent for both, identical trees, and byte-identical non-empty recorded, observed, and integration raw transitions.
- [ ] Existing two-parent proof remains green and new proof continues to disable Git replacement objects and use only exact-SHA safe object fetches.
- [ ] Historical schema-1 two-parent receipts load and replay byte-for-byte without migration or rewrite.
- [ ] Wrong integration parent/base, equal observed/integration SHA, tree or raw drift, extra commits, replacement-ref spoofing, provider-readback drift, and forged ledger history fail closed.
- [ ] Adoption persists and reads back before repeated provider observation; only PR/lineage head, stale merge authorization, and the new receipt may change.
- [ ] Ordinary terminal proof records reachability of the integration commit for the sibling shape; provider `MERGED` and receipt adoption alone never integrate.
- [ ] Existing exact-head integration and EHR-01 two-parent behavior do not regress.
- [ ] Full Ticket Autopilot, verification-audit, llm-wiki, npm extension, forward, static, context-budget, and Artifact Graph delta checks pass.
- [ ] After integration and exact local Pi sync, the normal Betsharemarket ticket 06 consumer replay succeeds with fresh readback while `gate:08:start:4` remains open; that replay is not candidate verification evidence.

## Frontier

Ready. EHR-01 is integrated and locally synchronized. The first post-integration consumer replay failed closed before Betsharemarket mutation and supplies the corrected one-parent diagnosis. No additional human decision or provider mutation is required for implementation.

## Step-by-Step Implementation Plan

1. Version the strict receipt contract so schema 1 remains historical two-parent-only and schema 2 requires a topology discriminator.
2. Refactor exact Git proof into explicit two-parent and single-parent-integration-copy branches without weakening shared object, raw-transition, replacement-object, provider identity, or safe-fetch checks.
3. For the sibling branch, bind the observed base from both one-parent commits, require distinct SHAs and identical trees, and compare all three raw byte streams.
4. Preserve kernel adoption, protected ledger history, receipt readback, provider reread, merge-authorization clearing, and idempotent crash replay across both schemas.
5. Extend real-Git, kernel, ledger, CLI, and forward tests with the historical sibling topology and malicious near misses, including terminal reachability of the integration commit rather than the observed head.
6. Update the runner contract, documentation, context baseline, and Artifact Graph relationships without representing historical evidence as a fresh live run.
7. Complete the normal bounded review, QA, verification, delivery, terminal-proof, and post-integration local-sync path before attempting the existing-run consumer replay.

## Testing Plan

- Real disposable Git tests for both accepted topologies and exact three-way raw transition equality.
- Negative tests for every parent/tree/raw/schema/topology/binding difference and replacement-ref spoofing.
- Kernel/ledger tests for schema-1 compatibility, schema-2 strictness, history replay, stale authorization clearing, and crash idempotence.
- CLI tests with simulated provider readback before/after receipt persistence and terminal proof that reaches only the integration commit.
- Historical raw fixture digest check as diagnostic-only evidence.
- Full repository suites, forward matrix, static compilation/tree checks, controlled context ceiling, and baseline/candidate Artifact Graph comparison.
- Post-integration only: fresh read-only GitHub and Git terminal proof through the Betsharemarket run; no caller-supplied receipt or ledger edits.

## Out of Scope

- General squash, multi-commit rebase, queue rewrite, conflict resolution, octopus merge, or arbitrary same-tree commit adoption.
- Commit-message, provider-label, patch-ID-only, final-tree-only, path-only, or user-asserted equivalence.
- Provider mutation during proof, manual Betsharemarket ledger/gate/source/branch/PR/lineage edits, or waiver of terminal proof.
- Satisfying or bypassing `gate:08:start:4`, publishing runner-defect issues, resuming status work before recovery, or reloading the active Pi session.
