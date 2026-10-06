---
ticket_schema: 1
ticket_id: "DBH-31"
execution_mode: AFK
blocked_by:
  - "DBH-28"
---

# DBH-31 — Revisione Opus 5.5 alla cieca

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:31`
- Role: `ticket`
- Parent: [delivery-bench-hard-quality-judge.md](../../specs/delivery-bench-hard-quality-judge.md)

## Parent Spec
[delivery-bench-hard-quality-judge.md](../../specs/delivery-bench-hard-quality-judge.md)

## What to Build
`quality.py review` avvia per ogni unità un processo `pi -p` nuovo, nella cartella neutra dell'albero, con `--model anthropic/claude-opus-5-5`, `--no-extensions --no-skills --no-context-files` e solo gli strumenti di lettura.

Il revisore riceve la richiesta (`TASK.md`) e la diff dei soli file di codice e di test. Sono esclusi `docs/specs`, `docs/tickets` e `.pi/`.

Risponde in JSON con una griglia fissa:
- bug probabili, ciascuno con gravità, file:riga e motivo;
- voti da 1 a 5 per rischio di correttezza, qualità dei test, design e leggibilità.

Spec: Target behavior 5.

## Acceptance Criteria
- [x] Il prompt e la diff filtrata non contengono nomi di braccio, lotto o cella.
- [x] La risposta è validata contro lo schema. Se non è valida si riprova una volta, poi si registra come errore.
- [x] Il costo e i token di ogni revisione vengono registrati dall'output JSON di Pi.

## Evidence
- Merged in #437. Opus needs the Claude Pro/Max OAuth extension `@wierdbytes/pi-anthropic`,
  loaded with `-e` from the user's Pi packages; plain Pi is refused as a third-party app.
- Cost and tokens come from the review's own session files, as the runner reads an arm's,
  not from Pi's JSON output.
- Real smoke, dbh-luna3d pi-tools r1 request 2: scores 2.5 / 3.0 / 3.25, $0.22-0.53 each.

## Frontier
Bloccato da DBH-28.

## Gates
Come la spec:
- un tentativo è un giudizio completo di `dbh-luna3d` più `dbh-luna3e`;
- nessun tetto di budget né di tempo, con la spesa riportata;
- al massimo 2 tentativi, il pilota e il giudizio completo;
- nessuna versione esatta;
- merge con CI 8/8 e `--match-head-commit`.

Blocco: niente esecuzioni Docker o Opus sui lotti veri finché `dbh-luna3e` gira.

## Step-by-Step Implementation Plan
1. Filtrare la diff e scrivere il prompt.
2. Eseguire Pi e leggere la risposta.
3. Scrivere un record per unità.

## Testing Plan
- Test unitari del filtro di cecità, del parsing e dello schema.
- Una revisione reale su un'unità giocattolo.

## Out of Scope
- Più revisioni per unità: le decide il pilota (DBH-32).
