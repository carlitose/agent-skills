---
ticket_schema: 1
ticket_id: "DBH-08"
execution_mode: AFK
blocked_by:
  - "DBH-05"
  - "DBH-06"
  - "DBH-07"
---

# DBH-08 — Pilota: catena da 1

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:08`
- Role: `ticket`
- Parent: [delivery-bench-hard-wayfinder.md](../../specs/delivery-bench-hard-wayfinder.md)

## Parent Spec
[delivery-bench-hard-wayfinder.md](../../specs/delivery-bench-hard-wayfinder.md)

## What to Build
Il lotto `dbh-pilot` con i cinque bracci, i tre scenari nuovi e 3 ripetizioni, fino alla
richiesta 1. Usa `openai-codex/gpt-6-luna` con thinking `medium` e i tetti di DBH-01. Dopo il
lotto:
- si esegue `judge-gated`;
- si scrive il report `docs/research/delivery-bench-hard-pilot.md` con profilo, esiti del
  driver, compaction e distribuzione della durata delle richieste;
- si fissano i tetti di tempo della misura completa.

## Acceptance Criteria
- [ ] Il lotto registra autorità, modello e thinking, e le copie del driver prese da un
  checkout pulito di `main` con `prepare-drivers --source`.
- [ ] Tutte le 45 celle sono giudicate, con i guasti d'infrastruttura a parte. Un guasto
  dell'harness si corregge solo fra due `run-lot` e va nel report.
- [ ] Il report confronta i bracci sui cinque assi e riporta le compaction. Propone il tetto
  per richiesta della misura completa, basato sulla durata osservata, con la ragione.
- [ ] Se spesa o durata superano i tetti di DBH-01, il lotto si ferma e il report lo dice.

## Frontier
Bloccato da DBH-05, DBH-06 e DBH-07.

## Step-by-Step Implementation Plan
1. `init-lot` con i tre scenari nuovi, i cinque bracci, `--model` e `--thinking`.
2. `prepare-drivers --source`, poi `run-lot --through 1 --jobs 4`.
3. `judge-gated`, `profile_report.py`, report e PR.

## Testing Plan
Le prove sono i record del giudice del lotto. Un rigiudizio di controllo su un campione di celle
deve dare esito identico.

## Out of Scope
- Catene più lunghe di 1 (DBH-09).
- Correggere un braccio dentro il lotto.
