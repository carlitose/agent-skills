---
ticket_schema: 1
ticket_id: "DBH-09"
execution_mode: AFK
blocked_by:
  - "DBH-08"
  - "DBH-12"
---

# DBH-09 — Misura completa: catene da 4 e 12

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:09`
- Role: `ticket`
- Parent: [delivery-bench-hard-wayfinder.md](../../specs/delivery-bench-hard-wayfinder.md)

## Parent Spec
[delivery-bench-hard-wayfinder.md](../../specs/delivery-bench-hard-wayfinder.md)

## What to Build
Estendere le celle del pilota, dentro i tetti di DBH-01 e con i tetti di tempo fissati da
DBH-08:
- le ripetizioni 1-3 fino alla richiesta 4;
- la ripetizione 1 fino alla 12;
- altre ripetizioni della catena da 12 solo dove la regola di TBA-03 le chiede.

Il report finale è `docs/research/delivery-bench-hard-results.md`. Contiene:
- la tabella braccio × lunghezza × scenario sui cinque assi, con le compaction;
- la regola di TBA-03;
- la raccomandazione operativa per questo regime;
- il confronto con la prima misura e con la calibrazione di DBH-03;
- i limiti.

## Acceptance Criteria
- [ ] Tutte le celle richieste hanno un profilo. Le ripetizioni extra ci sono solo dove la
  regola, sui tassi, le chiede.
- [ ] Il report ha tabella, regola, raccomandazione e limiti, senza un numero unico. Non nomina
  controlli o trappole nascosti.
- [ ] La mappa passa a Completed e ha il link al report.
- [ ] Spesa e durata stanno sotto i tetti, altrimenti il lotto si ferma e il report lo dice.

## Frontier
Sbloccato il 2026-09-28: il pilota (DBH-08) è chiuso, e i tetti restano quelli
dell'autorità. Durante le catene da 4 una cella si è fermata su un difetto del runner
(DBH-12), corretto fra due `run-lot`.

## Step-by-Step Implementation Plan
1. `run-lot --through 4`, poi `--through 12 --rep 1`.
2. Applicare la regola, eseguire le ripetizioni richieste, poi `judge-gated`.
3. `profile_report.py` alle lunghezze 1, 4 e 12. Scrivere report e aggiornamento della mappa,
   poi aprire la PR.

## Testing Plan
Le prove sono i record del giudice del lotto. Un difetto dell'oracolo si corregge secondo il
contratto §9, fra due `run-lot`, e con un rigiudizio.

## Out of Scope
- Migliorare i bracci.
- Lotti della prima misura.
