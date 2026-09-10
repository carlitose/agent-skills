# Preserve completion provenance across final-candidate corrections

## Artifact Graph
- Artifact ID: `artifact:ticket-autopilot-completion-provenance`
- Role: `spec`
- Standalone: true

### Children
- [CPR-01 Preserve completion provenance during candidate correction](../tickets/ticket-autopilot-completion-provenance/01-preserve-completion-provenance.md)

## Type and status
Bug-analysis spec. Diagnosis reproduced; implementation and verification pending.

## Goal
Let a corrected final candidate enter fresh quality and normal guarded delivery without replaying completed projection effects or rebinding an immutable completion summary to a later candidate. Preserve all historical evidence and existing authority boundaries.

## Diagnosis Report - lens: single-pass

### Root cause
Two consumers confuse current delivery state with the provenance of completed effects. `FinalTreeWorkflow.recover` consults `ticket.completion_effect` in the raw ledger, but that field exists only in `Kernel.report()`; the persisted receipts already prove the projection completed. The mistaken recovery replays the old fixed-index transaction before a staged correction can enter ordinary candidate-drift handling. Separately, `DeliveryFinalizer._ensure_summary` recovers the implementation candidate from enabled projection history, but the ordinary/excluded lane instead constructs its expected summary from the current candidate. A legitimate D-to-D2 correction therefore contradicts the already-written I-bound summary.

### Evidence
- SW-04: completed transaction and ledger candidate `1039ffeb6df1cc705b0955fb729c2264697d8348`; staged correction `2f056ec7a1f82236ad3e85e171c7f6f1cd27d83e`. Raw `completion_effect` is absent while the report says `applied`. The real resume reports `projection transaction index differs from its persisted prefix` before processing D2 stages.
- WBF-01: summary candidate `73d8ff3f58ee7e02c06d307126b00dbf0af314c8`, current candidate `5a9a33fc0065b3a56f140229abb38afa127c2c75`. The first immutable `completion-summary` effect event, sequence 26, has an idempotency key that exactly matches the stored summary candidate under the existing run/ticket/effect/CandidateRef hash contract. This is existing provenance, not new authority.
- Local evidence: `.git/ticket-autopilot/diagnostics/completion-provenance/observations-2.json`, `runs/sw-semantic-coverage/artifacts/SW-04/implementation-D2-response.json`, and `runs/wbf-01/artifacts/summary-gate-diagnosis.md` under Git-common state.

### Feedback loop built
`diagnostics/completion-provenance/diagnose-boundary.py` loads both ledgers through `AtomicLedger`, confirms the production recovery predicate enters projection with effects replaced by a call counter, and validates WBF's original effect key. Ledger and summary byte hashes remain unchanged; no provider calls or projection effects execute. The first diagnostic attempt used an `inspect.py` filename that shadowed the Python standard library and failed before loading run state; the renamed second attempt passed. This is diagnosis, not implementation verification.

### Fix location and approach
- Use one receipt-derived completion-state query shared by the kernel report and recovery. A fully bound completed projection must reach ordinary event processing, including semantic-drift invalidation. Incomplete or contradictory transactions still require exact recovery or fail closed.
- In ordinary tracked finalization, validate the original summary candidate against the first immutable completion-summary effect event and its applied receipt. Reuse the existing candidate-bound effect-key contract; do not trust disk content alone, select a later replay receipt, or invent a parallel provenance ledger. Continue using enabled projection provenance where applicable.
- Keep the no-clobber writer and normal delivery/source/provider guards intact. An already-receipted missing, symlinked, malformed, or contradictory summary fails before replacement or provider mutation.

### Alternatives ruled out
- Restoring SW-04's index to the old projection would conceal the correction rather than fix its entry boundary.
- Replacing WBF's summary with a D2-bound document would rewrite historical meaning.
- Accepting any candidate found on disk or any later summary-effect receipt would allow replay to redefine the original completion identity.
- New human approval cannot repair these deterministic data-flow defects.

### Confidence: high
Both observed failures are reproduced against preserved live state; focused production regressions and delivery proof remain pending.

## Acceptance and invariants
1. Completed enabled projection followed by staged semantic correction reaches implementation; all old quality is invalidated and archived, no completion effect is rerun, and no provider call occurs during adoption.
2. Interrupted projection still resumes exactly once; wrong index, missing receipt, or contradictory transaction does not acquire recovery clearance.
3. Ordinary tracked I completion, D review failure, implementation correction, fresh D2 quality, and normal delivery reuse the original summary byte-for-byte.
4. Repeated replay retains the first completion identity even after later summary effects are recorded. Unknown/mismatched candidate, run, ticket, digest, snapshot, missing or corrupt provenance, missing summary, and symlink cases fail closed.
5. Existing projection provenance, source ownership, post-provider mutation restrictions, lineage checks, and required quality stages remain unchanged. A summary proves historical completion, not current quality or integration.
6. Preserve SW-04/WBF-01 ledgers, summaries, candidates, gates and histories during this repair. Apply the integrated runtime through normal later resumes; do not manually clear their gates.

## Slice and verification strategy
CPR-01 owns the shared kernel/finalizer/workflow boundary, focused real-Git CLI regression, unit negatives, documentation and standard quality/delivery. Work inline and serially. No external library API changes or new credentials are required.

Run focused final-tree workflow, finalizer, kernel and ledger tests, then relevant broader Ticket Autopilot and forward scenarios plus static/diff/document checks. Distinguish local fixtures from live provider evidence. A failed or timed-out suite is not a pass. Observe target ledgers and summary hashes before/after implementation. Verify the final CandidateRef afresh after any correction.

## Non-goals and explicit compatibility
No gate relaxation, new approval ceremony, authority grant, receipt/history migration, direct recovery of the affected runs, reconciliation/content decisions, ignored-source redesign, wiki delivery repair, SW-04 lint edits, SW-06 human evidence, Pi installation or reload. Existing schema-4 run evidence must remain readable and literal; compatibility here is explicitly required to recover the preserved runs, not an inferred general migration obligation.
