# Ticket-driver judge identity: one name per actual run invocation

## Artifact Graph
- Artifact ID: `artifact:ticket-driver-judge-identity`
- Role: `spec`
- Standalone: true

### Children
- [JCI-01 — give fallback judges run-scoped IDs](../tickets/ticket-driver-judge-identity/01-give-fallback-judges-run-scoped-ids.md)

## Problem and evidence
In c3b-r4 post-fix (old skill HEAD `0d3df0f...`), a directed blocker triggered builder-2 and another `semantic_gates()` invocation. The first `semantic_gates()` had already used `sessions/judge-1`; a fresh `Cascade` instance reset its counter to zero and reused `judge-1`. The run had passed its candidate tests and several Jev decisions, then failed on `[WinError 183] ... sessions/judge-1` (ledger event 32, `failure=driver`). This was not a model/verification gate; the label consumed one start and remains failed. Direct evidence: `C:/bench38/driver-c3b-r4/project/.git/ticket-driver/runs/tdr-1790214450-ee84a564b4/ledger.jsonl` and `bench38-driver-c3b-r4.json`.

## JCI-01 invariant
Within one run, every fresh fallback judge has a unique receipt ID and session directory across all `Cascade` instances, including when `semantic_gates()` is entered again after a directed builder retry. Failed/partially-created session directories cannot be overwritten. The first judge retains `judge-1`; later judges use the next available monotonically increasing suffix. Do not change Jev confidence thresholds, question content, cascade order, decision parsing, key isolation, prompt or benchmark hidden tests. No guessed `yes` on uncertain results; gate as before when fresh judge is unavailable.

## Scope and verification
Change `ticket-driver/scripts/cascade.py` at the identity allocator, add causal test in `ticket-driver/tests/test_c3.py` and fake leaf support if required. Test RED on baseline by returning Jev uncertainty in both initial and retry semantic gates, causing two fresh judges in one run; GREEN demonstrates unique IDs and no FileExistsError while original c3/c4, c2, c1b and local quick profile remain green. Graph audit, inline review, canonical verification bundle, PR exact-head CI/merge/sync. Post-fix live benchmark labels must bind the *new* installed identity; old c3b-r4 must never be rerun or counted valid.
