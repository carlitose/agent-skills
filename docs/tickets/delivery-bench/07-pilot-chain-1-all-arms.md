---
ticket_schema: 1
ticket_id: "DB-07"
execution_mode: HITL
blocked_by:
  - "DB-03"
  - "DB-04"
  - "DB-05"
  - "DB-06"
---

# DB-07 — Pilota: catena da 1, cinque bracci, tre scenari

## Artifact Graph
- Artifact ID: `ticket:delivery-bench:07`
- Role: `ticket`
- Parent: [delivery-bench-wayfinder.md](../../specs/delivery-bench-wayfinder.md)

## Parent Spec
[delivery-bench-wayfinder.md](../../specs/delivery-bench-wayfinder.md)

## What to Build
Eseguire la catena da 1 in ciascuno dei tre scenari con i cinque bracci (3 ripetizioni), con `openai-codex/gpt-6-sol`, e leggere i profili: i bracci sono confrontabili? Quali guasti dell'harness emergono? L'utente autorizza il lotto e rivede i risultati prima della misura completa.

## Acceptance Criteria
- [ ] Autorità, lotto e ledger fuori da Git; ogni cella con receipt, journal, tempo e profilo.
- [ ] 15 celle per scenario (5 bracci × 3 ripetizioni), guasti d'infrastruttura ripetuti al massimo due volte.
- [ ] Report a profilo e confronto appaiato; elenco dei guasti dell'harness con correzione o ticket.

## Frontier
Bloccato da DB-03/04/05/06 e da un'autorizzazione esplicita dell'utente per il lotto.

## Step-by-Step Implementation Plan
1. Autorizzazione e lotto.
2. Esecuzione seriale per scenario.
3. Report e revisione con l'utente.

## Testing Plan
Live; nessuna modifica ai bracci durante il pilota.

## Out of Scope
- Catene da 3 e 8 (DB-08).
