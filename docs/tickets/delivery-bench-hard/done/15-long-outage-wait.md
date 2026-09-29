---
ticket_schema: 1
ticket_id: "DBH-15"
execution_mode: AFK
blocked_by:
  - "DBH-14"
---

# DBH-15 — Aspettare un buco di rete lungo prima di esaurire le ripetizioni

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:15`
- Role: `ticket`
- Parent: [delivery-bench-hard-wayfinder.md](../../specs/delivery-bench-hard-wayfinder.md)

## Parent Spec
[delivery-bench-hard-wayfinder.md](../../specs/delivery-bench-hard-wayfinder.md)

## What to Build
Un difetto del runner osservato nella rimisura dei driver (lotto `dbh-drivers`).
- **Osservato**: il 29/09 fra le 16:02 e le 16:45 UTC le foglie del driver sono uscite con
  `fetch failed`, in circa 25 s ciascuna e senza spesa. Le attese di DBH-14 (1 e 10 minuti)
  coprono circa 11 minuti. Il buco è durato 42 minuti, e 10 richieste su 72 della catena da 4
  hanno esaurito le ripetizioni: contano come non accettate (contratto §9).
- **Causa**: 2 ripetizioni con 11 minuti di attesa bastano per il buco di 9 minuti del lotto
  `dbh`, non per uno di tre quarti d'ora.

Il comportamento atteso:
- fino a 5 ripetizioni, con attese crescenti di 1, 5, 15, 30 e 60 minuti, quasi due ore in
  tutto;
- un buco di 9 minuti e uno di 42 minuti non esauriscono le ripetizioni;
- l'attesa resta fuori dai tetti ed è registrata come in DBH-14.

## Acceptance Criteria
- [x] Un test modella i due buchi osservati, 9 e 42 minuti con tentativi di 25 s. Prima della
  correzione quello da 42 minuti esaurisce le ripetizioni; dopo, nessuno dei due.
- [x] Dopo 6 tentativi falliti la richiesta è esaurita, con 5 attese crescenti registrate nel
  ledger e nella richiesta.
- [x] Dopo un tentativo dell'agente il runner non aspetta. Il contratto §9 descrive le attese.

## Outcome
2026-09-29. Il test `test_infrastructure_retries_wait_out_the_observed_outages` fallisce prima
della correzione nel caso da 42 minuti, e passa dopo. Anche `..._stop_after_five` fallisce prima
(3 tentativi invece di 6). Dopo la correzione passano tutti i test di `benchmarks/delivery-bench`.
- `MAX_INFRA_RETRIES` passa da 2 a 5, e le attese diventano 1, 5, 15, 30 e 60 minuti.
- Un tentativo fallito in un buco di rete costa circa 25 s e nessun token.
- I record già scritti non cambiano. Le 10 richieste perse della catena da 4 di `dbh-drivers`
  restano non accettate, come vuole il contratto.

## Frontier
Chiuso. Vale dal prossimo `run-lot`: la catena da 12 di `dbh-drivers` gira con la correzione.

## Step-by-Step Implementation Plan
1. Test RED in `test_runner.py`: tentativi che falliscono finché dura il buco, dato il tempo
   delle attese del runner.
2. Più ripetizioni e attese più lunghe.
3. Contratto §9 aggiornato.

## Testing Plan
Test offline di `benchmarks/delivery-bench`, con le attese registrate senza dormire.

## Out of Scope
- Rigiocare le 10 richieste perse: il contratto §9 le conta come non accettate.
- Sondare la rete prima di ripetere.
