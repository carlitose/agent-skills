---
ticket_schema: 1
ticket_id: "DRB-01"
execution_mode: AFK
blocked_by: []
---

# DRB-01 — Isolate and interpret directed review

## Artifact Graph
- Artifact ID: `artifact:ticket-driver-directed-review-boundary-01`
- Role: `ticket`
- Parent: [ticket-driver-directed-review-boundary.md](../../specs/ticket-driver-directed-review-boundary.md)

## Parent Spec
[ticket-driver-directed-review-boundary.md](../../specs/ticket-driver-directed-review-boundary.md)

## What to Build
Correct directed-review's function-scoped clean handling and mutable product working directory in `ticket-driver/scripts/risk.py` and its prompt, preserving global parser fail-closed semantics and the candidate fingerprint guard. Pass a pathless blocker to the bounded retry without inventing `:None`. No live benchmark in this ticket.

## Acceptance Criteria
- [ ] A directed artifact with section-local clean under a file/function heading and explicit nits elsewhere parses the nits; a global contradictory clean or a pathless nit still gates. Canonical findings and fences keep existing behavior.
- [ ] The directed reviewer runs in an owned scratch cwd separate from the candidate, can write only its review artifact without a gate, and a fake relative product edit never reaches the candidate; unexpected scratch outputs and absolute candidate edits gate. Receipts state the actual cwd.
- [ ] A blocker with no line is included in retry prose without a fabricated line, and the existing one-retry limit remains.
- [ ] Prompt asks for path-bearing severity lines or a single global clean marker, but not JSON; Jev isolation, Windows process-tree ownership, c4 completed-local and c1b/c2 behavior remain unchanged.
- [ ] RED/GREEN tests, graph audit, focused c1b/c2/c3 suites and mandatory quick profile are observed; no previously gated c3 run is counted valid.

## Frontier
Ready. User explicitly requested fixing bugs before finishing the already-authorized c3/c4 benchmark; no unresolved implementation-start decision.

## Step-by-Step Implementation Plan
1. Add synthetic causal RED cases for section-local clean and a fake directed reviewer writing an extra product file; add a pathless blocker retry check.
2. Place the directed reviewer in a disposable scratch cwd, parse only section-local clean with a narrow adapter, clarify the prompt and preserve fail-closed global behavior.
3. Run focused suites, admitted local profile, review frozen diff, QA, canonical verification bundle and separately authorized delivery/sync before new live benchmark binding.

## Testing Plan
Python unittest fake Pi/Jev with real subprocesses and scratch files, plus read-only parse of historical c3a artifacts. No hosted model/Jev calls for the fix ticket.

## Out of Scope
- Rerunning or retroactively validating the first c3 batches, bypassing semantic verify uncertainty, changing hidden acceptance tests or prior run receipts, or altering ticket-autopilot.
