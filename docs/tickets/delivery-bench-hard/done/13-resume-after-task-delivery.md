---
ticket_schema: 1
ticket_id: "DBH-13"
execution_mode: AFK
blocked_by:
  - "DBH-12"
---

# DBH-13 — Riprendere una richiesta il cui task è già consegnato

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:13`
- Role: `ticket`
- Parent: [delivery-bench-hard-wayfinder.md](../../specs/delivery-bench-hard-wayfinder.md)

## Parent Spec
[delivery-bench-hard-wayfinder.md](../../specs/delivery-bench-hard-wayfinder.md)

## What to Build
Un difetto del runner trovato riprendendo le celle ferme per DBH-12, durante la misura completa
(DBH-09). Per ogni richiesta il runner fa tre cose, in quest'ordine:
1. consegna il task: scrive `TASK.md` e lo registra con un commit;
2. prende l'istantanea della cartella del braccio;
3. aggiunge la richiesta al record della cella.
- **Osservato**: nel lotto `dbh` due celle si erano fermate all'istantanea della richiesta 3
  (DBH-12). Con il runner corretto, al `run-lot` successivo, si fermano di nuovo e subito: il
  commit di `TASK 3` fallisce.
- **Causa**: la consegna del task sta prima dell'istantanea, quindi il commit di `TASK 3` c'era
  già. Il record non aveva ancora la richiesta, e il runner l'ha ripresa da capo. Con niente da
  registrare, `git commit` esce con 1. DBH-12 dichiarava che la cella avrebbe ripreso, ma nessun
  test faceva fallire un passo fra la consegna e l'istantanea.

Il comportamento atteso: se il task della richiesta è già nella storia, la consegna non fa un
secondo commit e la richiesta riprende.

## Acceptance Criteria
- [x] Un test fa fallire l'istantanea della richiesta 2 e poi riprende la cella. Prima della
  correzione la ripresa fallisce sul commit di `TASK 2`, come nel lotto.
- [x] Dopo la correzione la richiesta 2 va al braccio una volta sola ed è accettata, e la storia
  di `TASK.md` ha un commit per richiesta.
- [x] Una consegna nuova fa ancora il suo commit.

## Outcome
2026-09-28. Il test nuovo di `test_runner.py` fallisce prima della correzione con lo stesso errore
del lotto. Dopo la correzione passa, insieme agli altri test di `test_runner.py`,
`test_judge.py` e `test_profile_report.py` (52, 2 saltati).
- La consegna fa il commit solo se `TASK.md` differisce da quello della storia.
- Su copie dei progetti delle due celle ferme, la consegna della richiesta 3 con il runner
  corretto non fa un commit nuovo.
- I record salvati non cambiano.

## Frontier
Chiuso. Le due celle ferme riprendono al `run-lot` successivo della misura completa (DBH-09).

## Step-by-Step Implementation Plan
1. Test RED in `test_runner.py`: l'istantanea fallisce dopo la consegna, poi la cella riprende.
2. Commit del task solo se c'è qualcosa da registrare.

## Testing Plan
Test offline di `test_runner.py`, una prova su copie delle due celle ferme, poi la ripresa vera
nel lotto `dbh`.

## Out of Scope
- Cambiare l'ordine fra consegna e istantanea: l'istantanea deve contenere il task, perché un
  ripristino lo conservi.
- Riscrivere i record già salvati.
