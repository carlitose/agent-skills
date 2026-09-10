# Distinguish technical gates from human decisions

## Artifact Graph
- Artifact ID: `artifact:autopilot-gate-readiness`
- Role: `spec`
- Standalone: true

### Children
- [RGC-01](../tickets/autopilot-gate-readiness/done/01-distinguish-gate-readiness.md)

## Type and status
Bug analysis and bounded implementation decision. The projection repair and focused regressions are implemented; final quality, delivery and installed-runtime activation remain separate.

## Observed behavior
At integrated source `c5be6904ce20cdb8f9224651c4a44335d98bc148`, `Kernel.record_stage(..., result="gated")` opens an `environment` gate. `Kernel.report()` labels every gated ticket `human-gated`, and `human_gated_ids()` returns every open gate regardless of category. This encourages callers to confuse a technical obstacle with a new human decision.

A disposable fixture reproduced an environment gate and a true HITL gate with identical `human-gated` readiness. An unrelated AFK ticket remained ready. The existing resolution operation restored `active / implement` using a synthetic prior implementation reference without passing any stage, changing CandidateRef, or closing the other ticket's human gate. Status itself did not mutate the ledger.

Local evidence is retained under `.git/ticket-autopilot/diagnostics/environment-gates/` in the observing repository. This proves current mechanics, not the validity of any historical BetShareMarket authorization. A nonempty reference accepted by an API is not semantic proof of its scope.

## Decision
Deliver the narrow projection and operator-guidance repair now. Do not introduce a new authority store, automatic gate resolver, stop-evidence schema, host continuation loop or Pi-core patch in this change. The broader evidence-backed continuation design remains a separate planning outcome.

### Gate projection
- Add an accurately named ordered accessor for **all open gate IDs**. The public `open_gates` and `open_gate_records` projections must continue exposing all categories in the same order.
- Make `human_gated_ids()` return only open gates whose persisted category is `human`. Do not preserve its misleading all-gates behavior through an alias.
- For an otherwise eligible gated ticket, inspect its applicable open ticket/run gates. An explicit human gate yields `human-gated`; an environment-only set yields `environment-gated`; mixed, other or unavailable classification yields conservative `gated`.
- Human gates dominate mixed categories. A category is a persisted classification, not proof that a prerequisite is restored or that a gate is automatically recoverable. Do not infer category, authority or recovery eligibility from reason prose.
- Preserve administrative barriers, dependency behavior, ready-ticket selection, run waiting state and every actual open gate. Classification must not activate a ticket, mark a gate passed, grant approval or change quality evidence.

### Operator continuation and existing authority
Owning Ticket Autopilot guidance must distinguish incomplete work, a demonstrably unavailable prerequisite and a missing decision. A technical gate may prevent finalization while leaving authorized diagnosis or unrelated AFK work actionable.

Before resuming a technically blocked stage, inspect the exact current run/ticket/candidate/gate, the original durable implementation or recovery authority, and the concrete prerequisite evidence. Reuse that authority only if it actually covers the same action and scope and has not been stopped or superseded. A valid prior instruction does not require a new conversational approval merely because the existing API takes an actor and evidence reference.

Use the existing public resolution path only after the cause is genuinely resolved and the scope check succeeds. This is an operator-attested action, not automatic authorization inferred from `environment` or from a merge grant. Ambiguous historical causes, unresolved human decisions, missing credentials, changed scope, required independent evidence and unproved recovery remain blocked. Never invent a human message or retrofit a decision into history.

Resuming returns control to the recorded stage; it is not a review, QA, verification, provider or merge pass. Candidate drift still forces normal fresh evidence. Implementation, recovery, quality, provider/merge, wiki and Pi authority remain distinct. The API's nonempty actor/reference check is not advertised as a semantic authorization verifier.

## Invariants
1. Reporting is pure, including repeated reads and legacy schema-4 replay; persisted gate reasons and history remain literal.
2. Every open gate remains visible and effective. Human/HITL gates, unknown categories and mixed gates are not automatically resolved.
3. Unrelated ready AFK work remains schedulable while another ticket is gated.
4. An exact resumed stage retains its uncompleted state and quality budget; no new quality pass or authority follows from recovery.
5. Historical evidence, grants, receipts, branch lineage and CandidateRefs are not rewritten by classification.

## External behavior and compatibility
Public status remains schema 2. Its readiness vocabulary gains `environment-gated` and conservative `gated`; consumers must not treat every gated result as a fresh human-consent request. Existing `open_gates` and `open_gate_records` remain complete, ordered projections. The intentionally corrected `human_gated_ids()` behavior is a Python API semantic change. No persisted-ledger schema, migration, alias or approval semantics change is required.

## Acceptance and validation
- Reproduce the old environment-as-human defect before implementation.
- Test actual human, environment-only, mixed human/environment, other-category, run-scoped and closed gates. Preserve barriers and dependencies.
- Assert full open-gate projection equality, ordering and deep-copy/read-only behavior; replay historical generic reasons without editing them.
- Through normal kernel/CLI fixtures, show that scoped resolution returns to the current phase without adding validated stages or closing unrelated human gates. Fixtures use synthetic authority and prove mechanics only.
- Preserve explicit negative guidance for merge-only authority, unattempted alternatives, missing actual decisions, stale candidates and unresolved historical causes. Review these operator semantics; string presence alone is not a live authorization test.
- Run focused kernel/CLI/status tests, existing reason/replay regressions, owning documentation tests and selected forward scenarios. Record baseline failures and timeouts honestly; no full-suite or live-provider claim follows from focused passes.

## Implementation slice
RGC-01 owns one complete outcome: truthful runtime gate classification plus the matching operator procedure and regressions. Keep the change local to gate reporting, existing consumers, owning guidance and tests. No new scheduler or recovery mutation is needed.

## Non-goals and follow-up
- Do not modify real BetShareMarket runs, SW-06, historical technical failures, approval records or the original dirty checkout.
- Do not certify that all technical alternatives were attempted. Requiring structured stop evidence and a runner-owned continuation assessment belongs to the separate premature-stop work.
- Do not implement the Pi settled/compaction adapter, install or reload Pi, update the Pi binary, resolve Windows launcher support, or merge a wiki PR in this ticket.
- Installation/readback is separate from successful source delivery. Source guidance cannot retroactively replace an active model's prior context.
