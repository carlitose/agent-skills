---
ticket_schema: 1
ticket_id: "DBH-39"
execution_mode: AFK
blocked_by:
  - "DBH-37"
  - "DBH-38"
---

# DBH-39 — Lotto con richieste vaghe e report

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:39`
- Role: `ticket`
- Parent: [delivery-bench-hard-vague-requests.md](../../specs/delivery-bench-hard-vague-requests.md)

## Parent Spec
[delivery-bench-hard-vague-requests.md](../../specs/delivery-bench-hard-vague-requests.md), Target behavior 6–7 e Gates.

## What to Build
Il lotto `dbh-vague` con `pi-tools`, `pi-full` e `bare-goal`, catene da 4, 3 ripetizioni × 3
scenari, `gpt-6-luna` medium, lanciato in modo visibile come i lotti precedenti. Poi il report a
confronto con `dbh-luna3d` e `dbh-luna3e` e il giudizio di qualità sulle sue unità.

## Acceptance Criteria
- [ ] Il lotto finisce entro 24 ore, oppure si ferma con il motivo registrato.
- [ ] Il report confronta l'accettazione per braccio e posizione con le catene precise e riporta
      le domande per richiesta (media, massimo, quante dalla cache) e il costo del simulato.
- [ ] Il giudizio di qualità delle unità è riportato a parte e non cambia il verdetto ufficiale.

## Frontier
Bloccato da DBH-37, DBH-38 e dalla fine di `dbh-chain12`.

## Gates
Come la spec: un lotto completo per tentativo, nessun tetto di spesa, 24 ore, al massimo 2
tentativi; un solo lotto alla volta; il checkout principale di `agent-skills` non si aggiorna
durante il lotto.

## Step-by-Step Implementation Plan
1. Preflight, autorità del lotto con i gate, `init-lot` con la variante vaga.
2. Avvio visibile e watcher.
3. Report e giudizio di qualità.

## Testing Plan
- Esecuzione reale; ledger e celle controllati a fine lotto.

## Out of Scope
- Catene da 12 e bracci Crew su richieste vaghe.
