---
type: source
title: "Publish and verify the explain-pr body before pr-open"
identity_key: ticket:ticket-autopilot-delivery-merge/01
identity_strength: stable
source_path: docs/tickets/ticket-autopilot-delivery-merge/done/01-publish-verified-pr-body.md
source_digest: sha256:66488c9b3977fc7eacce1a755d98fb9ccd959b4f3646048dba4b1a255e46155a
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-01
created_provenance: git-commit
disposition_changed: 2026-08-01
disposition_changed_provenance: git-rename
run_id: issue16-17-delivery-merge-20260801
---

# Publish and verify the explain-pr body before pr-open

Compiled from `docs/tickets/ticket-autopilot-delivery-merge/done/01-publish-verified-pr-body.md`. Identity is `ticket:ticket-autopilot-delivery-merge/01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-01** via `git-commit`
- Disposition changed: **2026-08-01** via `git-rename`

## Run

Completed under autopilot run `issue16-17-delivery-merge-20260801`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[2],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-ticket-autopilot-delivery-merge-01.md","payload_bytes":5776,"payload_sha256":"66488c9b3977fc7eacce1a755d98fb9ccd959b4f3646048dba4b1a255e46155a"}],"payload_bytes":5776,"payload_sha256":"66488c9b3977fc7eacce1a755d98fb9ccd959b4f3646048dba4b1a255e46155a","schema":1,"source_digest":"sha256:66488c9b3977fc7eacce1a755d98fb9ccd959b4f3646048dba4b1a255e46155a","source_identity":"ticket:ticket-autopilot-delivery-merge/01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 2: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":5776,"payload_sha256":"66488c9b3977fc7eacce1a755d98fb9ccd959b4f3646048dba4b1a255e46155a","schema":1,"source_digest":"sha256:66488c9b3977fc7eacce1a755d98fb9ccd959b4f3646048dba4b1a255e46155a","source_identity":"ticket:ticket-autopilot-delivery-merge/01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "01"
execution_mode: AFK
blocked_by: []
---

# Publish and verify the explain-pr body before pr-open

## Parent Spec

[ticket-autopilot-delivery-merge-wayfinder.md](../../specs/ticket-autopilot-delivery-merge-wayfinder.md)

## What to Build

Resolve [GitHub issue #16](https://github.com/carlitose/agent-skills/issues/16) as one
end-to-end delivery slice. Carry the exact validated verification bundle and frozen
CandidateRef into an `explain-pr` render request, validate the rendered body locally,
publish it through the selected provider, read back the actual body and HEAD, and validate
the observation again before recording `pr-open`.

The deterministic runner must persist a content-addressed render/publication handoff and
phase receipts. The scheduler skill delegates only semantic rendering to `explain-pr`.
Rendering, validation, provider mutation, or readback failure must leave a durable,
resumable gate. GitHub updates of an existing body must use a REST-only path that does not
depend on the `gh pr edit` GraphQL project-card query.

## Evidence

- `ticket-autopilot/scripts/autopilot/finalizer.py` currently sends
  `ledger://<run-id>/<ticket-id>` as the PR body and records `pr-open` after a provider
  receipt that contains no observed body.
- `ticket-autopilot/scripts/autopilot/providers.py` updates an existing GitHub PR with
  `gh pr edit` and `_github_view` does not request the body.
- `explain-pr/SKILL.md` requires render, local `validate-pr`, publication, provider
  readback, and a second validation against the observed HEAD.
- `verification-audit/scripts/verification_contract.py` already owns the canonical
  `validate-pr` contract and claim-visibility rules.
- The issue reports a real placeholder PR and a real `gh pr edit` failure caused by the
  Projects classic GraphQL query; a body-only REST update succeeded.

## Acceptance Criteria

- [ ] A verified ticket exposes a versioned, content-addressed render request containing
      normalized ticket facts, exact CandidateRef, validated verification-bundle identity,
      diff/code-map facts, and expected PR HEAD.
- [ ] The scheduler delegates that request to `explain-pr`; deterministic code rejects a
      missing, stale, malformed, or differently bound body result.
- [ ] The rendered body passes canonical `validate-pr` before provider publication and
      contains every required section plus exactly one before/after Mermaid diagram.
- [ ] Body wording cannot raise the bundle claim ceiling or conceal simulated/skipped
      evidence, open/failed gates, or residual limitations.
- [ ] Provider publication is followed by live readback of PR identity, body, and HEAD,
      then by canonical revalidation against the same bundle and observed HEAD.
- [ ] The ledger cannot enter `pr-open` while the body is the `ledger://` placeholder or
      while any render, validation, publication, readback, or revalidation phase is absent.
- [ ] Each failure phase opens one durable provider/delivery gate with enough structured
      progress to resume from the first incomplete effect.
- [ ] Resume never creates a second PR, duplicates body content, or replays a completed
      provider mutation; contradictory body or HEAD observations fail closed.
- [ ] Existing GitHub PR body updates avoid `gh pr edit` and its GraphQL Projects classic
      dependency; Azure DevOps retains provider-neutral contract parity or reports an
      explicit capability gate.
- [ ] Automated tests cover render -> validate -> publish -> readback -> revalidate,
      invalid/overclaiming bodies, provider update failure, readback mismatch, crash
      windows, and idempotent replay.

## Frontier

Ready. No preceding ticket is required. Completion unblocks the merge critical path by
ensuring that explanation work is finished before exact-SHA authorization can be requested.

## Step-by-Step Implementation Plan

1. Trace the current verified bundle/checkpoint artifacts into delivery and define one
   versioned render request/result contract bound to ticket ID, CandidateRef, bundle hash,
   expected head, and artifact generation; reject unsafe active-ledger interpretation.
2. Extend deterministic delivery progress and persistence so it can request semantic
   rendering from `explain-pr`, accept only the exact bound body artifact, and resume
   without narrative inference.
3. Invoke the canonical PR-body validator before provider mutation, retaining the original
   validated bundle as the claim ceiling.
4. Add normalized provider publication/readback receipts that include PR identity, body,
   and head. Implement a REST-only body update for existing GitHub PRs and preserve Azure
   DevOps capability negotiation.
5. Revalidate the observed provider body/head, then make that successful receipt the sole
   path to `record_pr` and `pr-open`; map every incomplete phase to a durable gate.
6. Update scheduler/explain-pr boundary instructions and add unit, integration-style,
   provider-fake, ledger replay, and forward regression tests.

## Testing Plan

Run the ticket-autopilot, verification-audit, explain-pr contract/skill-graph, and forward
test suites. Add fake-provider causal tests that observe the exact command and returned
body/head, including REST update failure, changed provider head, invalid readback body,
interruption after mutation, and repeated delivery. No simulated provider result may be
classified as a live `pr-open` proof.

## Out of Scope

- Merge execution or external-merge reconciliation from issue #17.
- A second PR renderer, evidence reducer, or provider-specific core state machine.
- Live provider credentials or production-readiness claims.
- Unrelated leaf-budget, cache, stack-reconciliation, or ticket-contract changes.


```
