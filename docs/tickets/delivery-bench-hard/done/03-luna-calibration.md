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

### Produces
- [delivery-bench-luna-calibration.md](../../research/delivery-bench-luna-calibration.md)

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
- [x] Il lotto registra l'autorità di DBH-01, il modello e il thinking, e ha legami di seed e
  suite uguali a `db07-pilot`, che non si tocca.
- [x] Tutte le 18 celle sono giudicate fino alla richiesta 3, con i guasti d'infrastruttura a
  parte.
- [x] La nota dice se luna basta a staccare `bare` e skills-only dal soffitto, e con quali
  numeri. Non nomina controlli nascosti.
- [x] La spesa resta sotto il tetto della calibrazione fissato in DBH-01.

## Outcome
2026-09-27/28. La nota è
[delivery-bench-luna-calibration.md](../../research/delivery-bench-luna-calibration.md).
- **Autorità**: `results/luna-calib-authority.json` (sha256 `352fae74…`), con modello
  `openai-codex/gpt-6-luna` e thinking `medium`. Seed, suite e canarini sono uguali a
  `db07-pilot`, verificati prima di partire.
- **Esito**: 18 celle su 18 giudicate fino alla richiesta 3. L'unico guasto d'infrastruttura è
  un tentativo `infra:host`, dovuto all'interruzione voluta del lotto per riconciliare DBH-01.
  La sua ripresa ha fatto emergere DBH-10.
- **Luna e soffitto**: luna medium stacca i due bracci dal soffitto ma non li separa. Alla
  catena da 3 le accettate sono 22/27 e 20/27, contro 26/27 e 27/27 con sol high; la regola
  resta «indistinguibile» (−2, Holm p 0,6875).
- **Spesa**: 0,234 $ stimati da Pi su 56 tentativi, contro un tetto di 10 $.

## Frontier
Chiuso.

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
