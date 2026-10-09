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
- Parent: [delivery-bench-hard-vague-requests.md](../../../specs/delivery-bench-hard-vague-requests.md)

## Parent Spec
[delivery-bench-hard-vague-requests.md](../../../specs/delivery-bench-hard-vague-requests.md), Target behavior 6–7 e Gates.

## What to Build
Il lotto `dbh-vague` con `pi-tools`, `pi-full` e `bare-goal`, catene da 4, 3 ripetizioni × 3
scenari, `gpt-6-luna` medium, lanciato in modo visibile come i lotti precedenti. Poi il report a
confronto con `dbh-luna3d` e `dbh-luna3e` e il giudizio di qualità sulle sue unità.

## Acceptance Criteria
- [x] Il lotto finisce entro 24 ore, oppure si ferma con il motivo registrato.
- [x] Il report confronta l'accettazione per braccio e posizione con le catene precise e riporta
      le domande per richiesta (media, massimo, quante dalla cache) e il costo del simulato.
- [x] Il giudizio di qualità delle unità è riportato a parte e non cambia il verdetto ufficiale.

## Evidence
- Lotto `dbh-vague` (pin delle skill come `dbh-luna3d`/`3e`): 2026-10-08T17:05Z → 23:54Z
  (6 h 49 min), 27/27 celle, 108 richieste giudicate, nessuna cella invalidata, nessun tetto.
  116 tentativi, 14,66 USD a listino; simulato `gpt-6-sol` 0,23 USD a parte.
- Accettazione vaghe (precise) per richiesta 1 / 2 / 3 / 4:
  - pi-tools 2/9 (7) · 3/9 (6) · 2/9 (8) · 0/9 (9): 7/36 contro 30/36.
  - pi-full 2/9 (5) · 0/9 (7) · 3/9 (8) · 0/9 (9): 5/36 contro 29/36.
  - bare-goal 3/9 (6) · 2/9 (5) · 2/9 (6) · 0/9 (8): 7/36 contro 25/36.
- Domande per richiesta (media / massimo / dalla cache): pi-tools 0,2 / 6 / 0; pi-full
  1,0 / 3 / 0; bare-goal 0,1 / 3 / 0. Nessuna rifiutata o oltre il limite. pi-full chiede a
  ogni richiesta e riceve i nomi giusti (es. `lua_setfrozen`), ma non passa lo stesso.
- Qualità, a parte (non cambia il verdetto): copertura 94-95% e mutazione 73-75% come con le
  richieste precise; review 2,8-3,2 (precise 3,2-3,5); latenti trovati 117-123/267 (precise
  205-218); invarianti rotte 113-129 (precise 21-33). File del lotto identici prima e dopo.
- Report nel repo privato: `results/dbh-vague/report.md`, `results/quality-vague/report.md`.

## Frontier
Fatto.

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
