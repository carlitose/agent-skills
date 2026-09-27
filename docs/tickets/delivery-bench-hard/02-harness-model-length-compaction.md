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
- [ ] Un lotto creato con `--model openai-codex/gpt-6-luna --thinking medium` lancia Pi con quel
  modello e quel thinking, e scrive la policy del driver e il record di cella con gli stessi
  valori. Lo prova un test offline con il Pi finto.
- [ ] Uno scenario con 12 richieste si esegue fino a `--through 12`, e `--through 13` viene
  rifiutato.
- [ ] Le risorse del giudice di uno scenario arrivano al comando `docker run`.
- [ ] Le compaction si contano da una sessione registrata. Prima si verifica su una sessione
  reale di `db07-pilot` in cui la compaction è avvenuta, come il file di Pi rappresenta una
  compaction.
- [ ] I report di `db07-pilot` e `c3a-observed` restano identici, compaction a parte.
- [ ] I test nuovi falliscono prima del cambiamento. Test di delivery-bench, ruff sui file
  toccati, `npm run lint` e `artifact-audit` passano.

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
