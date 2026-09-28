---
ticket_schema: 1
ticket_id: "DBH-11"
execution_mode: AFK
blocked_by:
  - "DBH-02"
---

# DBH-11 — Un tetto per richiesta oltre l'ora

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:11`
- Role: `ticket`
- Parent: [delivery-bench-hard-wayfinder.md](../../specs/delivery-bench-hard-wayfinder.md)

## Parent Spec
[delivery-bench-hard-wayfinder.md](../../specs/delivery-bench-hard-wayfinder.md)

## What to Build
Un difetto del runner trovato al lancio del pilota (DBH-08). L'autorità del lotto `dbh` fissa un
tetto di 5400 s per richiesta, confermato dall'utente in DBH-01. `init-lot` lo accetta e lo
registra, ma la cattura dei processi rifiuta ogni timeout oltre 3600 s.
- **Osservato**: le prime 4 celle del pilota hanno fatto 3 tentativi ciascuna, tutti
  `infra:harness` con guasto `configuration`, in 0 s e senza spesa. Poi sono state giudicate
  sul seme come richieste con i retry d'infrastruttura esauriti. Il lotto è stato fermato a mano
  prima delle altre celle.
- **Causa**: `capture_command` accetta timeout da 0,1 a 3600 s. È un limite generico della
  primitiva, non una politica: i comandi di Autopilot hanno già il loro tetto di un'ora in
  `git_ops`. DBH-02 ha portato i tetti nel lotto, ma nessun test faceva girare un tentativo con
  un tetto oltre l'ora.
- **Secondo difetto sullo stesso percorso**: `init-lot` non controlla i tetti. Un tetto che la
  cattura non può rispettare diventa un guasto d'infrastruttura in ogni cella, invece di un
  errore prima che il lotto esista.

Il comportamento atteso: un tetto di 5400 s arriva al braccio, e `init-lot` rifiuta un tetto per
richiesta fuori dal limite della cattura e un tetto di catena sotto 1 s.

## Acceptance Criteria
- [x] Un test fa girare un tentativo con tetto 5400 s, e fallisce prima della correzione con 3
  tentativi `infra:harness`.
- [x] Dopo la correzione il tentativo è `agent`, con timeout 5400 s, e la richiesta è accettata.
- [x] `init-lot` rifiuta un tetto per richiesta di 0 s o oltre 24 h e un tetto di catena di 0 s,
  senza creare il lotto.
- [x] Il tetto di un'ora dei comandi di Autopilot non cambia.

## Outcome
2026-09-28. I due test nuovi di `test_runner.py` falliscono prima della correzione: il primo con
3 tentativi `infra:harness`, come nel pilota, il secondo perché `init-lot` accetta i tre tetti.
Dopo la correzione passano, insieme agli altri 24 test di `test_runner.py`.
- La cattura accetta timeout fino a 24 h. È un limite finito, e il tetto dei comandi di
  Autopilot resta di un'ora in `git_ops`. I test della cattura e dei limiti dei comandi passano
  (33).
- `init-lot` rifiuta i tetti fuori limite prima di creare il lotto.
- I record salvati non cambiano.

Le 4 celle del pilota senza nessun tentativo del braccio non contano. DBH-08 archivia il lotto
fermato e ne apre uno nuovo.

## Frontier
Chiuso. Sblocca il pilota (DBH-08).

## Step-by-Step Implementation Plan
1. Test RED in `test_runner.py`: un tentativo con tetto 5400 s e i tetti fuori limite.
2. Alzare a 24 h il limite generico di `capture_command`.
3. Controllare i tetti in `init-lot`.
4. Aggiornare il README del runner.

## Testing Plan
Test offline di `test_runner.py` con il braccio finto, e i test della cattura e dei limiti dei
comandi di Autopilot. Poi il lancio vero del pilota in DBH-08.

## Out of Scope
- Cambiare la classificazione dei guasti o il numero di retry.
- Cambiare i tetti dei comandi di Autopilot.
- Riscrivere i record già salvati.
