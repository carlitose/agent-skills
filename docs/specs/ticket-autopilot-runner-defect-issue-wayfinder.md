# Ticket Autopilot Runner-Defect Issue Escalation

## Artifact Graph

- Artifact ID: `artifact:ticket-autopilot-runner-defect-issue-wayfinder`
- Role: `wayfinder`
- Standalone: true

### Children

- [RD-01 Map runner-defect evidence and escalation seams](../tickets/ticket-autopilot-runner-defect-issues/01-map-runner-defect-escalation-seams.md)
- [RD-02 Prototype fingerprinted issue escalation](../tickets/ticket-autopilot-runner-defect-issues/02-prototype-fingerprinted-issue-escalation.md)
- [RD-03 Freeze issue-publication authority](../tickets/ticket-autopilot-runner-defect-issues/03-freeze-issue-publication-authority.md)
- [RD-04 Implement audited runner-defect issue escalation](../tickets/ticket-autopilot-runner-defect-issues/04-implement-audited-runner-defect-issue-escalation.md)
- [RD-05 Forward-test live GitHub issue idempotency](../tickets/ticket-autopilot-runner-defect-issues/05-forward-test-live-github-issue-idempotency.md)

## Type

Wayfinding spec

## Status

Active

## Destination

When `ticket-autopilot` or one of its owned scripts proves a defect in the runner itself,
an explicitly authorized AFK run can create at most one secret-safe, evidence-backed issue
in `carlitose/agent-skills`. Replays and equivalent failures reuse the same fingerprint and
never create duplicates. The issue receipt is durable and auditable, and issue escalation
never substitutes for a gate, repairs a ledger, authorizes a merge, or upgrades uncertain
diagnosis into fact.

## Decisions So Far

- The target repository is fixed to `carlitose/agent-skills`; this is not a generic
  issue-tracker abstraction in the first slice.
- Only defects attributed to runner-owned code or contracts are eligible. Project test
  failures, candidate regressions, provider outages, permission failures, and ordinary
  human gates remain local run outcomes unless diagnosis proves a runner defect.
- A runner error is not automatically a bug report. Eligibility needs a normalized,
  secret-redacted diagnosis with a reproducible symptom, owning component, confidence,
  and regression-test or feedback-loop evidence.
- The canonical fingerprint must exclude volatile paths, timestamps, run IDs, tokens,
  branch names, and raw stack traces. It must include stable ownership and failure-shape
  facts sufficient for deduplication.
- Before creation, the GitHub adapter must search for the exact fingerprint marker. An
  existing open or closed issue is a deduplication receipt, not permission to create or
  comment again.
- Raw ledgers, transcripts, environment dumps, credentials, private repository content,
  and provider headers never enter an issue body. Evidence crosses the external boundary
  only after the diagnostic secret-redaction contract accepts it.
- Existing merge grants, gate approvals, and AFK execution mode do not imply issue-write
  authority. Publication requires its own explicit, bounded grant; RD-03 freezes its
  lifetime and revocation semantics.
- Failure to publish leaves the original run state unchanged and records a resumable or
  terminal escalation receipt separately. It cannot hide, pass, or replace the underlying
  runner gate.

## Not Yet Specified

- Whether issue-write authority is granted per run, per repository, or as a separately
  revocable reusable grant.
- The minimum diagnosis confidence and evidence classes required before automatic
  publication.
- Whether a matched closed issue should remain a no-op, reopen through a separate human
  action, or create a linked follow-up only after explicit authorization.
- The durable outbox location and crash boundary when GitHub is unavailable after the
  fingerprint has been reserved but before a provider receipt exists.
- Which labels and template fields are stable enough to become contract rather than
  presentation details.

## Out of Scope

- Creating issues for bugs in the project being processed by the runner.
- Automatically fixing, merging, closing, reopening, labeling, assigning, or commenting
  on an issue after its initial authorized creation.
- Uploading raw logs or relying on GitHub search text as the only local idempotency record.
- Treating issue creation as recovery from a corrupt ledger or as evidence that a gate
  passed.
- Supporting non-GitHub trackers or arbitrary destination repositories in the first
  implementation.

## Frontier / Blocking Edges

- **Current ownership and evidence seams** — ready, AFK. The runner has gates, provider
  receipts, and diagnostic workflows but no proven defect-escalation boundary. RD-01 maps
  exact owners into this Wayfinder and fixes the evidence contract consumed by the prototype.
- **Fingerprint and side-effect model** — blocked by RD-01, AFK. RD-02 proves stable
  classification, redaction, deduplication, crash replay, and a no-network dry-run before
  product code is selected.
- **Publication authority** — blocked by RD-01 and RD-02, HITL. RD-03 uses `grilling` to
  freeze grant scope, expiry, revocation, closed-issue behavior, and the minimum claim
  ceiling; no durable provider mutation is allowed before confirmation.
- **Runner integration** — blocked by RD-03, AFK. RD-04 connects the accepted contract to
  the runner and GitHub provider while keeping escalation state orthogonal to ticket and
  merge state.
- **Live provider proof** — blocked by RD-04, HITL. RD-05 creates or deduplicates one
  controlled issue and proves replay safety with a user-authorized GitHub boundary.

## Ticket Plan

| ID | Type | Mode | Blockers | Title | Expected output |
| --- | --- | --- | --- | --- | --- |
| `RD-01` | task | AFK | none | Map runner-defect evidence and escalation seams | Source-backed Wayfinder update defining eligibility, redaction boundary, state owners, provider seams, and unknowns |
| `RD-02` | prototype | AFK | `RD-01` | Prototype fingerprinted issue escalation | Disposable classifier, canonical fingerprint, dedupe/outbox model, crash replay, and counterexamples |
| `RD-03` | grilling | HITL | `RD-01`, `RD-02` | Freeze issue-publication authority | Confirmed decision for grant scope, expiry, revocation, claim threshold, and closed-issue policy |
| `RD-04` | task | AFK | `RD-03` | Implement audited runner-defect issue escalation | Runner/provider integration, durable receipts, redaction and dedupe guards, tests and docs |
| `RD-05` | forward test | HITL | `RD-04` | Forward-test live GitHub issue idempotency | One controlled live creation or dedupe observation, replay evidence, cleanup recommendation, and limitations |

## Next Review

Execute RD-01. The next review checks that the report separates observed runner ownership
from proposed policy and that RD-02 can run without GitHub mutation. Do not begin RD-03's
publication-policy interview until the research and prototype have reduced the decision to
concrete grant and lifecycle choices.
