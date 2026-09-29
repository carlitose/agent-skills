---
ticket_schema: 1
ticket_id: "DBH-17"
execution_mode: AFK
blocked_by:
  - "DBH-16"
---

# DBH-17 — Legare al lotto le skill installate

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:17`
- Role: `ticket`
- Parent: [delivery-bench-hard-wayfinder.md](../../specs/delivery-bench-hard-wayfinder.md)

## Parent Spec
[delivery-bench-hard-wayfinder.md](../../specs/delivery-bench-hard-wayfinder.md)

## What to Build
Un difetto di provenienza del runner, trovato dopo la rimisura dei driver (DBH-16).
- **Osservato**: il 29/09 alle 11:22 UTC un aggiornamento di pi-personal-config ha installato
  le skill di `a4190bc`, e sono cambiate `ask-skills`, `llm-wiki` e `ticket-autopilot`. Il lotto
  `dbh` era ancora in corso. Dopo l'aggiornamento sono partite 2 richieste di Autopilot, e altre
  2 erano in corso. Il lotto `dbh-drivers2` è girato tutto dopo. I report di DBH-09 e DBH-16
  dicevano che i bracci avevano le skill del 24/09.
- **Causa**: il lotto lega seed, suite, modello e copie del driver, ma non le skill installate,
  che i bracci vedono. Il runner non registra quali skill vede un tentativo, e un aggiornamento a
  metà lotto passa senza traccia.

Il comportamento atteso:
- il lotto registra il manifest delle skill installate, con digest, head e albero;
- ogni tentativo registra il digest del manifest con cui parte;
- se il manifest è cambiato, il runner si ferma prima del tentativo e `run-lot` non parte;
- i lotti legati prima di questo ticket non hanno il legame e non vengono controllati.

## Acceptance Criteria
- [x] Un test lega un manifest al lotto, esegue una richiesta, cambia il manifest e chiede la
  seconda. Prima della correzione il lotto non ha il legame. Dopo, la cella e `run-lot` si
  fermano con un errore, e nessun tentativo parte con le skill nuove.
- [x] Il contratto §8 descrive il legame. I report di DBH-09 e DBH-16 hanno una correzione
  esplicita.

## Outcome
2026-09-29. Il test `test_a_lot_binds_the_installed_skills_and_stops_when_they_change`
fallisce prima della correzione (`KeyError: 'installed_skills'`) e passa dopo, con tutti i test
di `benchmarks/delivery-bench`.
- Nel lotto `dbh`: delle 4 richieste di Autopilot toccate, 1 è accettata. Togliendo le 4 coppie,
  alla catena da 12 Autopilot resta indistinguibile da `bare` (Holm 0,083) e la regola non
  cambia.
- In `dbh-drivers2` i driver hanno copie proprie di `ticket-driver` e `ticket-autopilot` da
  `36aebf7`. I loro builder vedono le altre skill installate, cioè quelle di `a4190bc`.
- I record già scritti non cambiano.

## Frontier
Chiuso. Vale dal prossimo `init-lot`.

## Step-by-Step Implementation Plan
1. Test RED in `test_runner.py`, con il manifest in una cartella del test.
2. Legame in `init-lot`, controllo prima di ogni tentativo e all'avvio di `run-lot`.
3. Contratto §8 e correzioni nei due report.

## Testing Plan
Test offline di `benchmarks/delivery-bench`.

## Out of Scope
- Bloccare gli aggiornamenti di pi-personal-config durante un lotto.
- Rigiocare le richieste toccate: la regola non cambia senza di loro.
- Il digest dei singoli file delle skill: il legame è il manifest scritto dall'installatore.
