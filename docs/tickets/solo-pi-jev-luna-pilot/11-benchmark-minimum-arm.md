---
ticket_schema: 1
ticket_id: "SPB-11"
execution_mode: AFK
blocked_by:
  - "SPB-10"
---

# SPB-11 — Benchmark minimo reale del braccio Yjs L4

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-spb-11`
- Role: `ticket`
- Parent: [Repair loop](../../specs/solo-pi-jev-luna-repair-loop.md)

### Produces
- [Risultato](../../research/solo-pi-jev-luna-repair-loop-results.md)

## Parent Spec
[Repair loop](../../specs/solo-pi-jev-luna-repair-loop.md).

## What to Build
Nuova catena Luna medium Yjs L4 sul runtime congelato SPB-10, port e valutazione reali;
diagnosi causale e repair/retest di eventuali bug del braccio nel mandato/budget originale.

## Acceptance Criteria
- [ ] Snapshot SPB-10/target/graph/envelope/input/SDK/model/skills/images e mandato attuale verificati; API owner renewal + nonstarting preflight prima di ready.
- [ ] Budget storico 10/47/7/367 conservato, operatore aggiornato, €1000 e FX originali invariati; ogni nuova prova conserva il consumo completo.
- [ ] Processo/sessione reali unici per cella, quattro richieste cumulative e dipendenze originarie; candidati/consegnati e oracle caller-only immutabili.
- [ ] Score, port esercitati, difetti del braccio e errori del codice distinti; gate/unattempted non trasformati in 0/4 o fallimenti del modello.
- [ ] Se bug del braccio: causal fix congelato e nuovo trial distinto, non reset/replay/forzatura 4/4; limiti/costi/verifica/handoff inline riportati.

## Frontier
Ready: SPB-10 implementation-complete/release-blocked e mandato umano repair-loop valido.

## Step-by-Step Implementation Plan
1. Admission completa e nuovo source/cell; owner rinnova soltanto prossimo slot.
2. Trial reale; bounded readback di stato/port/errore senza hidden feedback al partecipante.
3. Repair soltanto di difetti dimostrati del braccio, retest distinto; factual report e audit.

## Testing Plan
Admission/hash/immutabilità/contabilità; benchmark reale, analisi causale degli output/port;
nessuna suite runtime invariata ripetuta. No fake PASS o release/CI/delivery claim.

## Out of Scope
New model/scenario/arm, hidden feedback, original grant/ledger resets, product intervention,
runner/scheduler/subagent, publication/commit/push/merge/install/reload/wiki sync.
