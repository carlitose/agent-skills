---
ticket_schema: 1
ticket_id: "DBH-29"
execution_mode: AFK
blocked_by:
  - "DBH-28"
---

# DBH-29 — Copertura dei test limitata alla diff

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:29`
- Role: `ticket`
- Parent: [delivery-bench-hard-quality-judge.md](../../specs/delivery-bench-hard-quality-judge.md)

## Parent Spec
[delivery-bench-hard-quality-judge.md](../../specs/delivery-bench-hard-quality-judge.md)

## What to Build
`quality.py coverage` esegue il `test_command` dell'albero di ogni unità nell'immagine dello scenario, offline. Misura quante righe eseguibili aggiunte nei sorgenti, esclusi i test, vengono eseguite.

Per linguaggio:
- Python: `coverage.py`, in un'immagine derivata con versione fissata;
- C: build con `--coverage` e `gcov`;
- JavaScript: `NODE_V8_COVERAGE`. La mappatura da `dist/` a `src/` va verificata; se non è possibile, si usa un fallback esplicito e lo si riporta.

Spec: Target behavior 3.

## Acceptance Criteria
- [ ] Per ogni unità c'è una quota con righe aggiunte, eseguibili e coperte, oppure "n/a" con il motivo.
- [ ] Le immagini derivate si costruiscono da file in `dbench-private/scenarios/*/images`, con versioni fissate.
- [ ] Smoke su un'unità reale per scenario.

## Frontier
Bloccato da DBH-28. L'esecuzione sui lotti veri aspetta la fine di `dbh-luna3e`.

## Gates
Come la spec:
- un tentativo è un giudizio completo di `dbh-luna3d` più `dbh-luna3e`;
- nessun tetto di budget né di tempo, con la spesa riportata;
- al massimo 2 tentativi, il pilota e il giudizio completo;
- nessuna versione esatta;
- merge con CI 8/8 e `--match-head-commit`.

Blocco: niente esecuzioni Docker o Opus sui lotti veri finché `dbh-luna3e` gira.

## Step-by-Step Implementation Plan
1. Calcolare le righe aggiunte dalla diff, nei file sorgente e non nei test.
2. Scrivere un adattatore per ogni linguaggio.
3. Eseguire in Docker con il timeout dello scenario.

## Testing Plan
- Test unitari delle righe aggiunte e del calcolo della quota, su output di coverage finti.
- Smoke Docker su un'unità per scenario.

## Out of Scope
- Mutation (DBH-30).
