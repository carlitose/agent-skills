---
type: source
title: "Bounded Ticket-Autopilot Leaves"
identity_key: artifact:bounded-ticket-autopilot-leaves-wayfinder
identity_strength: stable
source_path: docs/specs/bounded-ticket-autopilot-leaves-wayfinder.md
source_digest: sha256:018fed2ac580305b47575819a728feaf778999dee4e187869fe4b46d449a5015
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-07-28
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Bounded Ticket-Autopilot Leaves

Compiled from `docs/specs/bounded-ticket-autopilot-leaves-wayfinder.md`. Identity is `artifact:bounded-ticket-autopilot-leaves-wayfinder`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-07-28** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Child source: [[sources/ticket-bounded-ticket-autopilot-leaves-07]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"decisions":{"headings":[6],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"goals":{"headings":[5],"status":"present"},"invariants":{"headings":[],"status":"not-identified"},"verification":{"headings":[],"status":"not-identified"}},"parts":[{"index":0,"path":"wiki/sources/artifact-bounded-ticket-autopilot-leaves-wayfinder.md","payload_bytes":7106,"payload_sha256":"018fed2ac580305b47575819a728feaf778999dee4e187869fe4b46d449a5015"}],"payload_bytes":7106,"payload_sha256":"018fed2ac580305b47575819a728feaf778999dee4e187869fe4b46d449a5015","schema":1,"source_digest":"sha256:018fed2ac580305b47575819a728feaf778999dee4e187869fe4b46d449a5015","source_identity":"artifact:bounded-ticket-autopilot-leaves-wayfinder","source_kind":"spec"} -->

| Topic | Source sections |
|---|---|
| goals | 5: Destination |
| exclusions | 8: Out of Scope |
| decisions | 6: Decisions So Far |
| invariants | no matching section identified in the source; complete source retained |
| verification | no matching section identified in the source; complete source retained |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":7106,"payload_sha256":"018fed2ac580305b47575819a728feaf778999dee4e187869fe4b46d449a5015","schema":1,"source_digest":"sha256:018fed2ac580305b47575819a728feaf778999dee4e187869fe4b46d449a5015","source_identity":"artifact:bounded-ticket-autopilot-leaves-wayfinder"} -->
```markdown
# Bounded Ticket-Autopilot Leaves

## Artifact Graph

- Artifact ID: `artifact:bounded-ticket-autopilot-leaves-wayfinder`
- Role: `wayfinder`
- Standalone: true

### Children

- [BT-07 Add a docs-only fast path](../tickets/bounded-ticket-autopilot-leaves/done/07-add-docs-only-fast-path.md)

## Type

Wayfinding spec

## Status

Active

## Destination

Make ticket-autopilot leaf execution bounded, observable, resumable, and materially less
verbose while preserving independent review, causal QA, verification claims, exact-SHA
delivery, and explicit human authorization.

The source is [GitHub issue #9](https://github.com/carlitose/agent-skills/issues/9). The
target protocol is framed in
[bounded-ticket-autopilot-leaf-protocol.md](./bounded-ticket-autopilot-leaf-protocol.md).

## Decisions So Far

- Quality gates are not weakened. A bounded or timed-out leaf returns partial progress, not a
  pass.
- Quality failures and leaf resource consumption are orthogonal budgets.
- Mandatory QA execution and verification retain reserved execution capacity.
- The scheduler supplies one immutable ticket/`CandidateRef` context package instead of
  requiring every leaf to rediscover shared facts.
- Deterministic scripts own bundle construction, validation, reduction, hashing, counters,
  and resumable checkpoints; agents retain semantic judgment.
- Same-`CandidateRef` evidence may be cached only when scope and artifact hashes match.
- The accepted invalidation rule in
  [ticket-autopilot](../../ticket-autopilot/SKILL.md) remains in force: candidate or
  ticket-contract changes invalidate review, QA execution, verification, and merge
  authorization.
- Cross-`CandidateRef` evidence reuse is a later explicit HITL decision.
- Delivery remains provider-neutral, idempotent, readback-based, and exact-SHA gated; only
  the caller-facing continuation becomes less chatty.
- Backward compatibility is opt-in. Existing ledgers require an explicit validated migration
  or a clear fail-closed version error.

## Not Yet Specified

- Concrete default/max values and reservation arithmetic for interactions, tool calls, and
  wall time.
- Which host telemetry can be enforced versus only observed.
- The versioned schemas for `LeafContext`, partial handoff, progress events, and evidence
  manifests.
- Ledger versioning and active-run migration policy.
- Heartbeat cadence and the deterministic boundary between healthy, stuck, and timed out.
- Whether any evidence category may safely survive a changed `CandidateRef`.
- The exact final forward-test corpus and success budget derived from issue #9.

## Out of Scope

- Auto-merge or inferred human authorization.
- Weaker review completeness, causal coverage, claim reduction, or provider checks.
- Reusing stale semantic evidence merely because files appear unrelated.
- Provider-specific orchestration or a generic hosted workflow engine.
- Fabricated live database, browser, payment, provider, credential, or human evidence.
- Exact token accounting when the host does not expose it.

## Frontier / Blocking Edges

- **Budget semantics and ledger compatibility:** implementation cannot start reliably until
  reservations, timeout outcomes, and schema/version behavior are proven. Ticket `01` owns
  the prototype.
- **Bounded leaf result:** review and QA cannot resume safely from narrative-only output.
  Ticket `02` owns the first production vertical slice.
- **Opaque verification:** audit phases need deterministic artifacts and checkpoints before
  evidence caching can be trusted. Ticket `03` owns this edge.
- **Chatty delivery:** existing effects are safe but caller continuation is not terminal in
  one request. Ticket `04` owns the independent delivery slice.
- **Repeated unchanged work:** caching needs scope/artifact identity and must remain within
  one `CandidateRef`. Ticket `05` owns this safe boundary.
- **Selective invalidation — resolved:** the explicit ticket-06 decision preserves D6.
  Same-CandidateRef caching is the safe optimization ceiling; cross-CandidateRef semantic
  reuse remains unauthorized.
- **Docs-only overhead:** a prebuilt candidate restricted to project documentation should
  not pay for the full `execute-ticket` quality loop. Ticket `07` owns a fail-closed,
  deterministic fast path that preserves CandidateRef, documentation validation, delivery,
  and merge gates.
- **Integrated release evidence:** the final two-ticket forward-test ticket will be emitted
  only after ticket `06` resolves the policy; Wayfinder will then update the DAG rather than
  guessing its contract now.

## Ticket Plan

- [`01`](../tickets/bounded-ticket-autopilot-leaves/done/01-prototype-bounded-leaf-accounting.md)
  — prototype, AFK, ready — **Prototype bounded leaf accounting and resumable
  handoffs.** Expected output: deterministic budget/reservation model, phase events, partial
  handoff replay, and ledger version recommendation.
- [`02`](../tickets/bounded-ticket-autopilot-leaves/done/02-implement-budgets-bounded-review.md)
  — task, AFK, blocked by `01` — **Implement budgets and a bounded review handoff.**
  Expected output: CLI/config/status/final-report budgets plus one end-to-end review leaf
  that returns complete or resumable partial state.
- [`03`](../tickets/bounded-ticket-autopilot-leaves/done/03-checkpoint-qa-verification.md)
  — task, AFK, blocked by `02` — **Checkpoint QA and deterministic verification.**
  Expected output: QA/audit progress, script-built resumable bundle phases, and preserved
  claim gates.
- [`04`](../tickets/bounded-ticket-autopilot-leaves/done/04-single-request-delivery.md)
  — task, AFK, blocked by `01` — **Drive delivery to a terminal result in one
  request.** Expected output: one caller-level continuation across existing idempotent
  delivery effects, stopping only at a terminal result or real gate.
- [`05`](../tickets/bounded-ticket-autopilot-leaves/done/05-cache-unchanged-candidate.md)
  — task, AFK, blocked by `03` — **Cache immutable context and evidence for an unchanged
  CandidateRef.** Expected output: hash/scope-bound cache hits with zero stale semantic
  reuse.
- [`06`](../tickets/bounded-ticket-autopilot-leaves/06-decide-selective-invalidation.md)
  — decision, HITL, blocked by `05` — **Preserve D6.** Accepted output:
  [candidate invalidation decision](candidate-invalidation-decision.md); no selective-reuse
  implementation tickets are authorized.
- [`07`](../tickets/bounded-ticket-autopilot-leaves/done/07-add-docs-only-fast-path.md)
  — task, AFK, ready — **Add a docs-only fast path.** Expected output: explicit candidate
  adoption, deterministic documentation checks, and delivery without invoking
  `execute-ticket` when the frozen diff remains inside the approved documentation scope.

## Next Review

Review and integrate the stacked ticket chain in dependency order. Keep every merge
human-authorized for the exact observed head SHA. Do not open selective-invalidation
implementation work unless a future explicit decision replaces D6 with a fail-closed causal
contract and independent evidence.

```
