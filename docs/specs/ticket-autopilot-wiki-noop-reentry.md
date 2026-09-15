# Tracked wiki already-at-target delivery and exact reentry

## Artifact Graph
- Artifact ID: `spec:ticket-autopilot-wiki-noop-reentry`
- Role: spec
- Standalone: true

### Children
- [WNOP-01](../tickets/ticket-autopilot-wiki-noop-reentry/done/01-recognize-already-delivered-wiki.md)

## Problem and evidence

BetShareMarket ticket 02 in run `plfix14` integrated as [PR #297](https://github.com/carlitose/betsharemarket/pull/297). Its exact-source wiki compilation produced valid frozen content identical to wiki [PR #296](https://github.com/carlitose/betsharemarket/pull/296), already on the advanced delivery base. The source commit still contains the preceding wiki snapshot, so compilation correctly reports a candidate, but materializing that candidate on the current delivery base has no Git diff.

`deliver_tracked_candidate` conflates an empty successful diff with Git failure and raises `tracked wiki candidate unexpectedly has no Git diff`. The persisted delivery is terminal even though desired content is present. Existing `retry-wiki-delivery` permits only two historical destination/path failures and rejects this record, including its already-persisted target receipt.

Observed frozen content SHA-256: `d2f17057854029d50d8a0ba086bb43898a840c680acd8731ada28c801f55ce7e`. The #296 and #297 merge commits have the same complete `project-wiki` Git subtree, `05dfb391af8a2261d72924df67779fd29e66105b`. The current failure and fresh compilation checks are preserved in BetShareMarket's local `plfix14/02-quality/wiki-blocker.json`; this diagnosis does not itself resolve runner state.

## Target behavior

1. After ordinary frozen-candidate, target and file validation, a successful exact materialization equal to the freshly observed delivery base is a distinct successful no-op. Persist its base SHA/tree and candidate identity. Do not create a commit, branch, PR, provider call or merge authorization for it.
2. The post-integration driver records completion, distinguishes already-present content from a newly merged wiki, and makes repeated resume idempotent. Do not borrow application verification or claim a merge that did not occur.
3. Extend the existing exact, actor/evidence-bound retry transaction for this one historical pre-provider no-diff failure. Accept only an integrated ticket, exact failure shape, intact frozen candidate and matching persisted target receipt, with no PR/provider/publication/merge authorization evidence. Preserve the complete predecessor and intent/readback/replay semantics. Preparation remains provider-free and returns only delivery-pending; ordinary resume performs fresh destination proof.
4. An actual Git diff failure is not a no-op. Invalid files/modes/content, contradictory target/receipt, stale authority/digest and prior provider activity fail closed. Re-observe the remote base before declaring already-at-target so a base move during materialization cannot become stale success.

## Preserved contracts and limits

The `wiki-sync-v1` candidate, validation, Git clean-byte/mode rules, source identity, protected-worktree boundary, cross-checkout target checks, application lifecycle and normal non-empty PR/merge flow remain unchanged. Reuse current CLI flags and exact retry provenance rather than introducing a reset/force command. Only the explicitly described historical failure gains recovery; other terminal failures remain ineligible.

The no-op proves desired generated content at a named observed Git head. It does not establish runtime behavior, live-provider support, a new merge, application approval, or future remote immutability. Do not edit the consumer ledger or an installed/global runner as an implementation shortcut.

## Implementation slice

One end-to-end WNOP-01 owns no-op recognition, durable driver completion, exact historical reentry, regression tests and the operational reference. Package alignment and BetShareMarket recovery follow integration as separate configuration/operational stages, not source mutations in this ticket.

## Verification strategy

Use focused disposable real-Git repositories and frozen-file fixtures, with provider commands instrumented to fail if invoked in no-op/retry cases. Establish RED for the current empty-diff failure and recovery rejection, then GREEN for exact no-op, repeated resume, exact replay and interrupted retry. Test non-empty normal delivery, corrupt frozen bytes/receipts, extra or missing content, stale failed-record digest, prior provider activity and remote-base movement. Retain relevant byte-fidelity/target/retry regressions. Classify local real-Git tests as local integration with simulated provider boundaries, never live provider evidence.

No broad timeout investigation, production traffic, unrelated compatibility layer, host-policy change or Pi global update/reload is part of this spec.
