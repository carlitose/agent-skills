# Ticket Autopilot Docs-only Autonomous Merge Diagnostic

## Artifact Graph

- Artifact ID: `artifact:ticket-autopilot-docs-only-autonomous-merge-diagnostic`
- Role: `spec`
- Standalone: true

### Children

- [DA-01 allow eligible docs-only candidates through autonomous merge](../tickets/ticket-autopilot-docs-only-autonomous-merge/done/01-allow-eligible-docs-only-autonomous-merge.md)

## Status

Diagnosed — reproduced in live run `cr-autocompact-removal-20260829` on 2026-08-29.

## Symptom

CR-05 was adopted through the canonical docs-only path. The runner validated two Markdown
paths, produced a canonical Verification Bundle with final disposition and maximum claim
`implementation-complete`, committed and pushed head
`57438e692978ad37e657a4b11f46069e7550a195`, and opened GitHub PR #143. Autonomous delivery
then opened `gate:CR-05:dynamic:2` with:

> autonomous merge requires the exact semantic candidate to be fully validated

The run has a valid autonomous merge grant. The provider observation is live. The failure is
before checks, rules, approvals, or merge mutation.

## Expected behavior

An eligible docs-only receipt is the explicit runner-owned substitute for the standard leaf
pipeline. If its exact CandidateRef, content-addressed receipt, verification handoff, delivery
lineage, and live provider state remain valid, autonomous eligibility must accept that
candidate without inventing review, QA, or runtime evidence.

## Reproduction

1. Start an autonomous run with a valid run-scoped merge grant.
2. Activate an AFK ticket and stage only regular `docs/**/*.md` project documentation.
3. Submit `docs-only-adopt`; observe `status: eligible`, `validated_stages: [implement]`, a
   canonical verify handoff, and `max_claim: implementation-complete`.
4. Deliver the candidate, validate the PR body, and open a live provider PR.
5. Observe `_autonomous_eligibility()` reject the candidate before provider eligibility
   checks.

The production reproduction is PR #143 in run `cr-autocompact-removal-20260829`. Existing
tests cover docs-only adoption and delivery up to `render-required`, but no test exercises the
autonomous merge path for an eligible docs-only candidate.

## Root cause

`Kernel.complete_docs_only_candidate()` and ledger validation intentionally encode an eligible
docs-only candidate as:

- `validated_stages == ["implement"]`;
- an eligible normalized `docs_only` receipt bound to the exact CandidateRef;
- zero leaf interactions;
- one canonical verification result and handoff.

`_autonomous_eligibility()` instead contains a single standard-path predicate requiring
`ticket["validated_stages"] == list(STAGES)`. It does not recognize the runner's eligible
docs-only state. Therefore a state accepted by the docs-only contract and ledger can never
pass autonomous merge eligibility.

This is a runner bug, not a CR-05 or GitHub failure. Confidence is high because the live run
reached the exact predicate and source inspection exposes the contradictory invariants.

## Classified non-cause

CR-06 becoming ready while CR-05 is `pr-open` or gated on provider merge is intentional
single-parent stack scheduling. `_dependency_ready()` permits that state; the stricter
`autonomous_merge_dependencies_ready()` still requires every blocker to be integrated before
the child can merge. No change is required there.

## Fix contract

Introduce one canonical eligibility predicate that accepts either:

1. the unchanged standard path with the complete `STAGES` prefix; or
2. an exact eligible docs-only receipt that passes the existing normalized receipt and
   CandidateRef invariants.

The change must not synthesize missing leaf stages, raise the docs-only claim ceiling, skip
live provider checks, weaken delivery-lineage checks, or admit rejected/stale/drifted
docs-only receipts. Add an autonomous end-to-end regression that reaches durable integration
through the fake live provider and a negative regression for an ineligible receipt.

## Evidence and limits

- Live GitHub PR creation and readback were observed for PR #143; no merge mutation occurred.
- Candidate and delivery identities are recorded in the append-only ledger.
- The diagnosis does not authorize editing the ledger, manually closing the gate, or merging
  around the runner.
- Provider policy behavior remains outside the root cause because eligibility failed before
  those calls.
