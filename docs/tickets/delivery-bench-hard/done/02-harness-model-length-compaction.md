---
ticket_schema: 1
ticket_id: "DBH-02"
execution_mode: AFK
blocked_by: []
---

# DBH-02 — Harness: modello dal lotto, N richieste, compaction

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:02`
- Role: `ticket`
- Parent: [delivery-bench-hard-wayfinder.md](../../specs/delivery-bench-hard-wayfinder.md)

## Parent Spec
[delivery-bench-hard-wayfinder.md](../../specs/delivery-bench-hard-wayfinder.md)

## What to Build
Rendere `benchmarks/delivery-bench` capace di misurare il regime difficile senza cambiare la
lettura dei lotti esistenti.
- **Modello e tetti dal lotto.** `init-lot --model PROVIDER/ID --thinking LEVEL --request-cap S`
  li scrive nel lotto. Il runner li legge da lì per il comando di Pi dei bracci, per la policy
  del driver (`prepare-drivers`) e per il record di cella. I default restano quelli di oggi.
  I lotti vecchi hanno già provider, modello e thinking nel `lot.json`.
- **Scenari con N richieste.** Il numero si legge da `scenario.json`, e `--through` non può
  superarlo.
- **Risorse del giudice per scenario.** `cpus`, `memory` e `pids` si leggono da
  `scenario.json`, con i default di oggi (`2`, `2g`, `1024`).
- **Compaction registrata.** Per ogni richiesta il runner conta le compaction delle sessioni Pi
  del braccio e le scrive nel record. Il report le somma per catena e per braccio, come dato
  descrittivo.
- **Contratto** (`docs/research/delivery-bench-oracle-contract.md`): aggiornare §1, §4, §5 e §9
  per N richieste, risorse, compaction e tetti presi dal lotto.

## Acceptance Criteria
- [x] Un lotto creato con `--model openai-codex/gpt-6-luna --thinking medium` lancia Pi con quel
  modello e quel thinking, e scrive la policy del driver e il record di cella con gli stessi
  valori. Lo prova un test offline con il Pi finto.
- [x] Uno scenario con 12 richieste si esegue fino a `--through 12`, e `--through 13` viene
  rifiutato.
- [x] Le risorse del giudice di uno scenario arrivano al comando `docker run`.
- [x] Le compaction si contano da una sessione registrata. Prima si verifica su una sessione
  reale di `db07-pilot` in cui la compaction è avvenuta, come il file di Pi rappresenta una
  compaction.
- [x] I report di `db07-pilot` e `c3a-observed` restano identici, compaction a parte.
- [x] I test nuovi falliscono prima del cambiamento. Test di delivery-bench, ruff sui file
  toccati, `npm run lint` e `artifact-audit` passano.

## Outcome
2026-09-27.
- **Modello e tetti dal lotto.** `init-lot` prende `--model`, `--thinking`, `--request-cap` e
  `--chain-cap`. Il runner li legge dal lotto per Pi, per la policy del driver e per il record di
  cella. Se l'autorità nomina un modello, un lotto con un altro viene rifiutato. I default
  restano quelli della prima misura.
- **Lunghezza e giudice dallo scenario.** La lunghezza della catena era già data da
  `requests` e da `max_length`, e un test lo protegge. `pids` del giudice ora viene dallo
  scenario, come già `cpus` e `memory`. Uno scenario può dichiarare `driver_test_command`, e
  `javascript` usa `npm test` e `npm ci` come `typescript`.
- **Compaction.** In 8 sessioni di `db07-pilot` (bracci autopilot e skills-only) la compaction è
  una riga di primo livello `{"type": "compaction", "tokensBefore", "usage": {..., "cost"}}`.
  Ogni richiesta ora registra `compaction`: numero, token prima di ciascuna, costo.
- **Difetto scoperto.** Quel costo non entrava in `usage`, quindi i lotti precedenti
  sottostimano l'USD di Pi per quanto hanno compattato. Il report ora lo somma all'USD di Pi
  delle catene e aggiunge la colonna *Compactions*.
- **Verifiche:**
  - i 7 test nuovi fallivano prima del cambiamento; il test sulla lunghezza della catena
    passava già;
  - 47 test di delivery-bench verdi, con 2 skip Docker dal vivo;
  - ruff pulito, dopo aver sistemato un I001 già presente su `main`;
  - i report di `db07-pilot` e `c3a-observed` a L3 e L8 sono identici riga per riga, a parte la
    colonna nuova (sempre 0) e la frase che la spiega.

## Frontier
Pronto.

## Step-by-Step Implementation Plan
1. Leggere il formato della compaction in una sessione reale e fissarlo in una fixture.
2. Scrivere i test RED: modello dal lotto, N richieste, risorse del giudice, compaction.
3. Implementare in `runner.py`, `judge.py` e `profile_report.py`.
4. Aggiornare contratto e README, poi aprire la PR.

## Testing Plan
Test offline (`test_runner.py`, `test_judge.py`, `test_profile_report.py`) con il Pi, il driver e
il giudice finti. Il giudice Docker vero solo con `DBENCH_LIVE_DOCKER=1`. Il confronto dei report
dei lotti esistenti si fa in locale, senza pubblicare dati privati.

## Out of Scope
- Scenari nuovi e lotti.
- Cambiare assi, regola o lettura della bussola.
