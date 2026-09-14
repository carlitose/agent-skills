---
type: source
title: "Preserve completion provenance during candidate correction"
identity_key: ticket:ticket-autopilot-completion-provenance/CPR-01
identity_strength: stable
source_path: docs/tickets/ticket-autopilot-completion-provenance/done/01-preserve-completion-provenance.md
source_digest: sha256:07f59caab9067b937e73b31affe1fb6d1d063978544e90ae821a23e76c5e681c
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-10
created_provenance: git-commit
disposition_changed: 2026-09-10
disposition_changed_provenance: git-rename
run_id: cpr01
---

# Preserve completion provenance during candidate correction

Compiled from `docs/tickets/ticket-autopilot-completion-provenance/done/01-preserve-completion-provenance.md`. Identity is `ticket:ticket-autopilot-completion-provenance/CPR-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-10** via `git-commit`
- Disposition changed: **2026-09-10** via `git-rename`

## Graph

- Parent source: [[sources/artifact-ticket-autopilot-completion-provenance]]

## Run

Completed under autopilot run `cpr01`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-ticket-autopilot-completion-provenance-cpr-01.md","payload_bytes":3910,"payload_sha256":"07f59caab9067b937e73b31affe1fb6d1d063978544e90ae821a23e76c5e681c"}],"payload_bytes":3910,"payload_sha256":"07f59caab9067b937e73b31affe1fb6d1d063978544e90ae821a23e76c5e681c","schema":1,"source_digest":"sha256:07f59caab9067b937e73b31affe1fb6d1d063978544e90ae821a23e76c5e681c","source_identity":"ticket:ticket-autopilot-completion-provenance/CPR-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3910,"payload_sha256":"07f59caab9067b937e73b31affe1fb6d1d063978544e90ae821a23e76c5e681c","schema":1,"source_digest":"sha256:07f59caab9067b937e73b31affe1fb6d1d063978544e90ae821a23e76c5e681c","source_identity":"ticket:ticket-autopilot-completion-provenance/CPR-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "CPR-01"
execution_mode: AFK
blocked_by: []
---

# Preserve completion provenance during candidate correction

## Artifact Graph
- Artifact ID: `artifact:ticket-autopilot-completion-provenance-cpr-01`
- Role: `ticket`
- Parent: [Completion provenance](../../specs/ticket-autopilot-completion-provenance.md)

## Parent Spec
[Preserve completion provenance across final-candidate corrections](../../specs/ticket-autopilot-completion-provenance.md)

## What to Build
Implement the spec's corrected-candidate finalization boundary: consume receipt-derived completion state rather than a report-only field, and validate an ordinary tracked completion summary against its first immutable candidate-bound effect receipt. Reuse existing history, preserve no-clobber behavior, and leave authorization and fresh-quality rules unchanged.

## Acceptance Criteria
- [ ] A fully completed enabled projection does not replay before a staged correction; D2 enters implementation with all previous quality invalidated and history retained.
- [ ] Genuine interrupted or contradictory projection retains exact recovery and fail-closed behavior.
- [ ] Ordinary tracked I completion → D review failure → correction → fresh D2 quality → guarded delivery preserves the original summary byte-for-byte.
- [ ] Replay uses the first completion identity, not the newest candidate or a later replay receipt. Missing, corrupt, mismatched, or symlinked summary/provenance fails without replacement or provider mutation.
- [ ] Existing projection provenance, source ownership, post-provider restrictions, ledger schema/history, quality and merge gates remain intact.
- [ ] Focused real-Git CLI tests, unit negatives, relevant broader/forward checks and final-candidate review/QA/verification pass with explicit local-evidence ceilings; failures and timeouts are preserved.
- [ ] SW-04 and WBF-01 evidence remains untouched; no recovery or deployment is claimed by this ticket.

## Frontier
Ready AFK; no ticket dependencies or human decision needed for this deterministic repair. Existing affected-run gates remain separate and unchanged. The user's ongoing request authorizes implementation inline, not delegation or invented gate approval.

## Step-by-Step Implementation Plan
1. Reproduce completed-projection correction and ordinary summary replay in disposable fixtures; record RED evidence.
2. Share the persisted-receipt completion-state query between report and recovery; retain interrupted-transaction handling.
3. Reuse original summary-effect provenance in ordinary tracked replay, requiring exact document identity and first-effect binding; preserve no-clobber and all delivery guards.
4. Add replay, tamper/missing/symlink and post-provider negatives; simplify the shared boundary without unrelated refactoring.
5. Run focused and broader checks, then fresh review, QA, verification and standard delivery for the final CandidateRef.

## Testing Plan
Real-Git CLI tests for I→D projection, interrupted recovery and D2 adoption; ordinary finalization through D2 with original summary preserved; no provider calls before qualified delivery. Unit checks for first-event selection and exact effect-key binding, run/ticket/digest/snapshot contradictions, missing/corrupt files/receipts and repeated replay. Include final-tree, finalizer, kernel, ledger and relevant forward scenarios. Read-only checks preserve the two affected live ledgers and WBF summary. Shared-context review is not independent; local fake-provider tests do not prove live provider behavior.

## Out of Scope
- Implementing or resuming SW-04, WBF-01, SW-06 or wiki delivery within this ticket.
- Manual ledger/index/receipt repair, historical backfill, new authority, gate relaxation or a parallel provenance store.
- General ignored-source redesign, arbitrary reconciliation, delegation, local Pi installation or reload.

```
