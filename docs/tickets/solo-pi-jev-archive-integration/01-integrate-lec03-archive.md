---
ticket_schema: 1
ticket_id: "LIN-01"
execution_mode: AFK
blocked_by: []
---

# LIN-01 — Integrare l'archivio pi-lec03 a comportamento invariato

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-lin-01`
- Role: `ticket`
- Parent: [solo-pi-jev-archive-integration.md](../../specs/solo-pi-jev-archive-integration.md)

## Parent Spec
[solo-pi-jev-archive-integration.md](../../specs/solo-pi-jev-archive-integration.md): Decision, Invariants, Verification.

## What to Build
Portare in `main` tutto il contenuto di `archive/wt-pi-lec03`, cioè documentazione, arm
di benchmark e catena di `ticket-driver`, adattando `findings.py` e la domanda
`review.scope_complete` in modo che il comportamento distribuito resti identico.

## Acceptance Criteria
- [ ] Tutti gli 81 percorsi dell'archivio sono presenti; le uniche differenze rispetto
      all'archivio sono i due adattamenti della spec e i loro test.
- [ ] `ticket-driver/questions/review.scope_complete.json` è identico a `main` e la cartella
      `ticket-driver/questions/` contiene gli stessi sei file.
- [ ] `parse_findings` senza opzioni riconosce solo percorsi `.py`, come in `main`;
      con `any_extension=True` riconosce qualunque estensione; `chain_controller` usa l'opt-in.
- [ ] La variante adjudicated della domanda è in `benchmarks/delivery-bench/questions/`.
- [ ] `test_staged_behavior` passa: il cambio di sessione confronta il motore delle decisioni
      sottostante e mantiene l'osservazione della copertura.
- [ ] La suite `ticket-driver/tests`, i test nuovi di `benchmarks/delivery-bench` e il lint passano.

## Frontier
Ready.

## Step-by-Step Implementation Plan
1. Applicare il commit d'archivio su un branch da `origin/main`.
2. Ripristinare la domanda distribuita e spostare la variante nei benchmark.
3. Rendere opt-in la regex estesa in `findings.py` e attivarla in `chain_controller.py`.
4. Correggere `_CoverageFeedback.path` e il reincapsulamento in `bind_session` (LEC v3).
5. Aggiungere i test di regressione; eseguire i test causali e il lint.

## Testing Plan
Unitari locali (`unittest`, `node --test` per i `.mjs` nuovi); CI del PR.
Benchmark live non eseguiti: fuori scope.

## Out of Scope
- Rilanciare benchmark, aggiornare il launcher esterno in `C:/dbench`, cambiare il pin installato.
- Spostare in `done/` i ticket importati.
