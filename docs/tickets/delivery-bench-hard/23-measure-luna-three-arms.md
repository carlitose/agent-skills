---
ticket_schema: 1
ticket_id: "DBH-23"
execution_mode: AFK
blocked_by:
  - "DBH-21"
  - "DBH-22"
---

# DBH-23 — Misurare Luna su tre bracci e scrivere il report

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:23`
- Role: `ticket`
- Parent: [delivery-bench-hard-luna-three-arms.md](../../specs/delivery-bench-hard-luna-three-arms.md)

## Parent Spec
[delivery-bench-hard-luna-three-arms.md](../../specs/delivery-bench-hard-luna-three-arms.md),
sezioni *Comportamento atteso* 5–6, *Spesa e autorità*, *Decisioni dell'utente*.

## What to Build
Il lotto `dbh-luna3` (`bare`, `pi-tools`, `pi-full`; `openai-codex/gpt-6-luna` medium) sui tre
scenari di DBH-09, visibile sul terminale, e il report
`docs/research/delivery-bench-hard-luna3.md`.

## Acceptance Criteria
- [ ] File d'autorità `dbh-luna3-authority.json` fuori da Git, con le frasi dell'utente, bracci,
      scenari, 3 ripetizioni, catena massima 12, modello, tetto 50 $ di listino.
- [ ] Preflight reale passato sui tre bracci prima di `init-lot`.
- [ ] Lotto legato a skill installate `07c1f0a` (pi-personal-config `0dd13f5`) e ai profili di
      DBH-21; nessun `update:personal` durante il lotto.
- [ ] `run-lot` in primo piano in una finestra visibile, 9 celle per volta; viewer aperto.
- [ ] Catene da 4 alle ripetizioni 1–3, poi catena da 12 alla ripetizione 1; ogni richiesta
      giudicata; nessuna nuova cella se la spesa proiettata supera il tetto.
- [ ] Report con i tre confronti appaiati (regola di TBA-03), spesa, guasti e differenze rispetto
      a DBH-09.

## Frontier
Dependency-blocked da DBH-21 e DBH-22.

## Step-by-Step Implementation Plan
1. Autorità e preflight.
2. `init-lot`, apertura del viewer, `run-lot --through 4` per ripetizione.
3. Proiezione della spesa, poi `run-lot --through 12 --rep 1`.
4. Giudizio, tabelle, report e chiusura del ticket.

## Testing Plan
- È la misura live: nessuna affermazione sui risultati prima del giudizio. Le verifiche di
  legame (skill, estensioni, suite) le fa il runner a ogni tentativo.

## Out of Scope
- Ripetizioni oltre quanto indicato, altri modelli, rilanci dei lotti storici.
