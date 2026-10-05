---
ticket_schema: 1
ticket_id: "SPB-09"
execution_mode: AFK
blocked_by:
  - "SPB-08"
---

# SPB-09 — Una sola misura Yjs L4 sul braccio corretto

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-spb-09`
- Role: `ticket`
- Parent: [Luna adjudicated L4](../../specs/solo-pi-jev-luna-adjudicated-l4.md)

### Produces
- [Risultato osservato](../../research/solo-pi-jev-luna-adjudicated-l4-results.md)

## Parent Spec
[Luna adjudicated L4](../../specs/solo-pi-jev-luna-adjudicated-l4.md).

## What to Build
Una nuova cella persistente Yjs L4 Luna medium sul runtime congelato SPB-08, con source e
scope grant distinti da SPB-07; readback e report score/causa senza replay o source storico mutato.

## Acceptance Criteria
- [ ] SPB-08/target/tree/graph, runtime/SDK/skills/request/seed/suite/question/policy/immagini e grant «1» verificati prima della spesa.
- [ ] Costi cumulativi originali ammessi senza perdere i 10/47/7/367, uso operatore aggiornato e separato dalle stime sperimentali/invoice/FX.
- [ ] Esattamente un processo/cella nuovi; candidato e delivered con prove osservate, blocchi distinti dai tentativi; nessun secondo launch o replay dopo errore.
- [ ] Decisioni reali/port/input/causa e score riportati, oracle caller-only immutabile; nessun hidden feedback, confronto storico solo descrittivo e invariato.
- [ ] Frozen report/review/QA/audit inline con limiti, costi e tentativi preservati; nessuna suite runtime invariata ripetuta né delivery/installazione/delega/runner.

## Frontier
Ready: SPB-08 implementation-complete/release-blocked con handoff canonico validabile;
nuova authority di scope selezionata esplicitamente «1» nella conversazione corrente.

## Step-by-Step Implementation Plan
1. Canonical admission and cumulative ledger/source snapshot, reuse observed one-cell caller.
2. One prepare and one run on new paths; never replace failed setup/launch.
3. Bounded score/cause readback, preserved history/costs, frozen aggregate report and handoff.

## Testing Plan
Graph/serializer/Git/source/input/package/images and cost preflight; one authorized real
cell; readback/hash/accounting/decision/candidate/delivered after. No runtime suite replay.

## Out of Scope
Other model/scenario/cell, historical mutation, new ports/thresholds/budgets, paired bare,
hidden prompts, independent reviewer, runner, publication/commit/push/merge/install/reload/wiki sync.
