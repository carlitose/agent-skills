---
ticket_schema: 1
ticket_id: "DBH-03"
execution_mode: AFK
blocked_by:
  - "DBH-01"
  - "DBH-02"
---

# DBH-03 — Calibrazione di luna sugli scenari vecchi

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:03`
- Role: `ticket`
- Parent: [delivery-bench-hard-wayfinder.md](../../specs/delivery-bench-hard-wayfinder.md)

## Parent Spec
[delivery-bench-hard-wayfinder.md](../../specs/delivery-bench-hard-wayfinder.md)

## What to Build
Un lotto piccolo, `luna-calib`, separa l'effetto del modello da quello del problema. Fa girare
`bare` e skills-only con `openai-codex/gpt-6-luna` e thinking `medium` sui tre scenari della prima
misura, fino alla richiesta 3 con 3 ripetizioni. Seed, suite e canarini sono quelli di
`db07-pilot`.

Una nota, `docs/research/delivery-bench-luna-calibration.md`, confronta i due regimi a parità
di scenario e di braccio: accettazione, regressioni, latenti, costo e tempo. Il confronto va
etichettato come confronto fra modelli, non fra bracci.

## Acceptance Criteria
- [ ] Il lotto registra l'autorità di DBH-01, il modello e il thinking, e ha legami di seed e
  suite uguali a `db07-pilot`, che non si tocca.
- [ ] Tutte le 18 celle sono giudicate fino alla richiesta 3, con i guasti d'infrastruttura a
  parte.
- [ ] La nota dice se luna basta a staccare `bare` e skills-only dal soffitto, e con quali
  numeri. Non nomina controlli nascosti.
- [ ] La spesa resta sotto il tetto della calibrazione fissato in DBH-01.

## Frontier
Bloccato da DBH-01 (autorità e tetti) e da DBH-02 (modello dal lotto).

## Step-by-Step Implementation Plan
1. `init-lot` con modello, thinking e i tre scenari vecchi, solo per `bare` e skills-only.
2. `run-lot --through 3 --jobs 4`.
3. `profile_report.py` sul lotto, poi confronto con `db07-pilot` per gli stessi bracci. Scrivere
   la nota e aprire la PR.

## Testing Plan
Le prove sono i record del giudice del lotto. Prima del lotto, un controllo dei digest contro
`db07-pilot`.

## Out of Scope
- Gli altri tre bracci.
- Gli scenari nuovi.
- Modificare `db07-pilot`.
