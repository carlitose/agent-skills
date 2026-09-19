---
type: source
title: "Provider-gated candidate revalidation"
identity_key: artifact:provider-gated-candidate-revalidation
identity_strength: stable
source_path: docs/specs/provider-gated-candidate-revalidation.md
source_digest: sha256:060278c40d994b9d025bbab543cec22894ef79e010886a49e0da2a0b9bc39a43
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-09-16
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Provider-gated candidate revalidation

Compiled from `docs/specs/provider-gated-candidate-revalidation.md`. Identity is `artifact:provider-gated-candidate-revalidation`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-16** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Child source: [[sources/ticket-provider-gated-candidate-revalidation-pgr-01]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"decisions":{"headings":[],"status":"not-identified"},"exclusions":{"headings":[],"status":"not-identified"},"goals":{"headings":[],"status":"not-identified"},"invariants":{"headings":[],"status":"not-identified"},"verification":{"headings":[],"status":"not-identified"}},"parts":[{"index":0,"path":"wiki/sources/artifact-provider-gated-candidate-revalidation.md","payload_bytes":5502,"payload_sha256":"060278c40d994b9d025bbab543cec22894ef79e010886a49e0da2a0b9bc39a43"}],"payload_bytes":5502,"payload_sha256":"060278c40d994b9d025bbab543cec22894ef79e010886a49e0da2a0b9bc39a43","schema":1,"source_digest":"sha256:060278c40d994b9d025bbab543cec22894ef79e010886a49e0da2a0b9bc39a43","source_identity":"artifact:provider-gated-candidate-revalidation","source_kind":"spec"} -->

| Topic | Source sections |
|---|---|
| goals | no matching section identified in the source; complete source retained |
| exclusions | no matching section identified in the source; complete source retained |
| decisions | no matching section identified in the source; complete source retained |
| invariants | no matching section identified in the source; complete source retained |
| verification | no matching section identified in the source; complete source retained |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":5502,"payload_sha256":"060278c40d994b9d025bbab543cec22894ef79e010886a49e0da2a0b9bc39a43","schema":1,"source_digest":"sha256:060278c40d994b9d025bbab543cec22894ef79e010886a49e0da2a0b9bc39a43","source_identity":"artifact:provider-gated-candidate-revalidation"} -->
```markdown
# Provider-gated candidate revalidation

## Artifact Graph

- Artifact ID: `artifact:provider-gated-candidate-revalidation`
- Role: `spec`
- Standalone: true

### Children

- [PGR-01 Revalidate a changed provider-gated candidate](../tickets/provider-gated-candidate-revalidation/done/01-revalidate-provider-gated-candidate.md)

## Type and status

Bug analysis and bounded correction specification. Ready for implementation.

## Evidence and current behavior

At source baseline `d7a7541`, `FinalTreeWorkflow.revalidate_delivery()` and
`Kernel.prepare_delivery_revalidation()` require `verified` state. A fully verified,
published ignored-source ticket stopped at the provider's pre-merge eligibility gate is
instead `gated`. An explicitly staged correction therefore cannot re-enter quality with
`delivery-revalidate`; resume may poll or attempt the old pending head first.

Five uncommitted files in the installed Pi agent-skills cache contain an unverified local
proposal for this behavior. They are diagnostic input, not accepted implementation or test
evidence. The cache and other existing local changes must remain untouched. Existing RDR-02
covers explicit base reconciliation priority, not this same-base delivery revalidation.

## Goals and target behavior

Accept an explicit, single `delivery-revalidate` event for a changed staged candidate only
when its published ticket is blocked at the narrow provider-merge eligibility boundary.
Process that valid recovery before old-head merge dispatch. Re-enter the existing final
quality cycle, invalidate old evidence and one-shot merge authorization, and persist the
superseded stale provider gate atomically with the new candidate. This is not gate approval
or a new merge grant.

## Eligibility and semantic invariants

- The run is not paused and uses ignored ticket sources; no status barrier or completion
  projection grant exists. A completed disposition is eligible only with the existing
  applied ignored-finalization receipt; hold and cancellation are never bypassed.
- The ticket is gated, has no active stage, and has passed the complete existing quality
  sequence. Docs-only and tracked final-tree paths remain unchanged.
- Exactly one relevant open gate exists (ticket or run scope). It is the ticket's dynamic
  `provider-merge` gate, resumes `pr-open`, and matches `merge-progress` in gated eligibility.
- A real candidate-tree change is required. Base tree, ticket digest and contract version
  stay unchanged. Existing prepared and delivery candidate references match the old one.
- Recorded PR, commit, push and merge-progress heads agree. Local HEAD and branch still
  match that PR. No reconciliation preparation, merge intent/mutation/readback or integration
  receipt exists. Existing lifecycle/source guards run before recovery mutation.
- Only that stale provider gate is superseded. Prior history and provider observations
  remain available; no unrelated gate or source completion receipt is changed.
- Review, QA and verification must run again on the new candidate. No remote mutation is
  caused by the recovery itself. Replay of the accepted event is idempotent.
- Kernel transitions and ledger replay enforce the same eligibility predicate and reject
  an unrelated gate change. Malformed or ineligible state cannot grant recovery.

## Non-goals and authority

No general reopen command, generic gate clearing, schema migration, compatibility alias,
tracked-source extension, docs-only shortcut, new provider API, publication, merge, local Pi
synchronization or active-session reload is authorized by this spec. Keep delivery manual.
Do not copy the installed cache wholesale or its generated package lock.

## Implementation slice

PGR-01 is one end-to-end slice across the shared eligibility predicate, workflow Git guards,
resume ordering, kernel transition, ledger replay and regression tests. These files share a
single invariant and must not be delivered independently.

## Verification strategy and acceptance

1. Reproduce rejection on the unmodified source using a real temporary Git repository and
   the existing fake-provider/ledger harness, not an edited production ledger.
2. Prove accepted recovery reaches active review, advances artifact generation, discards
   stale leaf evidence, clears one-shot authorization, supersedes only the old gate, preserves
   published observations, and survives canonical ledger save/load and replay.
3. Assert zero old-head merge/provider mutation before or during recovery; check repeat
   event idempotency and eventual normal revalidation flow.
4. Exercise negative controls: unchanged tree, changed base or ticket identity, pause,
   hold/cancel, other/run gates, wrong gate/head/branch, tracked/docs-only sources,
   reconciliation and begun/uncertain merge. Verify fail-closed state is preserved.
5. Run focused workflow, CLI, kernel and ledger regression tests plus the forward matrix.
   Record actual commands and failures. Local fake-provider tests are not live-provider
   evidence. Review is serial and shared-context unless separately authorized.

## Alternatives and unresolved questions

A full base reconciliation is unnecessary for a same-base staged repair; an administrative
reopen would change source disposition and is not the requested operation. Broad gate
approval would wrongly preserve old quality evidence. The narrow existing operation is
preferred. No product decision remains open; test evidence and external delivery are pending.

```
