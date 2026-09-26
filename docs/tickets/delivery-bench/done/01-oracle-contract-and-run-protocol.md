---
ticket_schema: 1
ticket_id: "DB-01"
execution_mode: AFK
blocked_by: []
---

# DB-01 — Contratto dell'oracolo e protocollo di esecuzione

## Artifact Graph
- Artifact ID: `ticket:delivery-bench:01`
- Role: `ticket`
- Parent: [delivery-bench-wayfinder.md](../../specs/delivery-bench-wayfinder.md)

### Produces
- [delivery-bench-oracle-contract.md](../../research/delivery-bench-oracle-contract.md)

## Parent Spec
[delivery-bench-wayfinder.md](../../specs/delivery-bench-wayfinder.md)

## What to Build
Definire in `docs/research/delivery-bench-oracle-contract.md` il contratto del benchmark: formato di una richiesta grezza, di uno scenario (stato iniziale pubblico, richieste 1..8, suite nascosta per richiesta, latenti, trappole con distanza), come la suite gira in un container contro un repo consegnato senza toccarlo, come ogni braccio riceve la richiesta N solo dopo la consegna della N-1, e il record del profilo a cinque assi. Chiarire come Autopilot riceve la richiesta grezza (spec e ticket li scrive il braccio; merge nel repo del benchmark, provider locale o repo effimero) e un tetto di tempo per catena. Riusare `bench38_harness.py` e `arm_comparison.py` dove possibile. Sezioni della mappa: Decisions 2-4, 6-7, 9-11, Not Yet Specified.

## Acceptance Criteria
- [x] Il documento risponde a ogni voce di *Not Yet Specified* della mappa o dichiara la domanda ancora aperta con il prossimo passo.
- [x] Un runner minimo esegue una suite nascosta d'esempio su un repo consegnato in un container e scrive un profilo JSON; il repo consegnato risulta byte-identico dopo l'esecuzione.
- [x] Le regole di isolamento sono verificabili: elenco esplicito di cosa il braccio vede a ogni richiesta e prova che la suite nascosta non è nel suo checkout.
- [x] Il protocollo di Autopilot è descritto passo per passo e provato una volta su un repo effimero senza chiamate al modello.

## Frontier
**Completato** in esecuzione skills-only (2026-09-26): contratto in `docs/research/delivery-bench-oracle-contract.md`; `benchmarks/delivery-bench/judge.py` con scenario d'esempio: 12 test offline, prova live in `python:3.12-slim` (riferimento 5/5, stub fallisce esattamente i 5 controlli attesi, albero consegnato identico); sonda Autopilot senza modello su repo effimero fino a `verified` e push del ramo di consegna (limiti nel contratto, §7). Merge registrato nella PR di consegna; spostato in `done/` senza ricevuta del runner.

## Step-by-Step Implementation Plan
1. Leggere bench38 (`/c/bench38`, `bench38_harness.py`, `acceptance.py`) e il runner Harbor usato per Terminal-Bench; decidere cosa si riusa.
2. Scrivere il contratto; provare il runner minimo su un repo giocattolo.
3. Provare il giro Autopilot senza modello su un repo effimero; registrare limiti.

## Testing Plan
Prova del runner minimo (repo consegnato immutato, profilo scritto); prova Autopilot senza modello. Nessun lotto live.

## Out of Scope
- Scrivere gli scenari (DB-03/04/05).
- Scegliere il vincitore o modificare i bracci.
