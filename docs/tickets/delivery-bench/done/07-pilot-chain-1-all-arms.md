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

### Produces
- [delivery-bench-pilot.md](../../research/delivery-bench-pilot.md)

## Parent Spec
[delivery-bench-wayfinder.md](../../specs/delivery-bench-wayfinder.md)

## What to Build
Eseguire la catena da 1 in ciascuno dei tre scenari con i cinque bracci (3 ripetizioni), con `openai-codex/gpt-6-sol`, e leggere i profili: i bracci sono confrontabili? Quali guasti dell'harness emergono? L'utente autorizza il lotto e rivede i risultati prima della misura completa.

## Acceptance Criteria
- [x] Autorità, lotto e ledger fuori da Git; ogni cella con receipt, journal, tempo e profilo.
- [x] 15 celle per scenario (5 bracci × 3 ripetizioni), guasti d'infrastruttura ripetuti al massimo due volte.
- [x] Report a profilo e confronto appaiato; elenco dei guasti dell'harness con correzione o ticket.

## Frontier
**Completato** (2026-09-26, skills-only): lotto `db07-pilot`, 45 celle (3 scenari × 5 bracci × 3 ripetizioni) con `openai-codex/gpt-6-sol`, autorità dall'obiettivo di sessione vincolata per hash, lotto, ledger e record di cella nel repo privato fuori da Git. 45/45 richieste giudicate; nessun guasto d'infrastruttura, errore del giudice, timeout o riscontro dell'audit. Report e letture: [delivery-bench-pilot.md](../../../research/delivery-bench-pilot.md). In sintesi: accettazione al soffitto per bare, skills-only, Autopilot e c1a (9/9), indistinguibili per la regola di TBA-03; c3a 2/9 perché 7 run si fermano sul cancello semantico in attesa di un umano (candidati bloccati 7/7 accettabili a parte); costo da 0,74 $ (bare) a 8,26 $ (Autopilot) per 9 celle. Correzioni dell'harness nella stessa PR: esiti del driver e giudizio controfattuale (`judge-gated`), `run-lot --rep`, `profile_report.py --through/--rep` con la regola del vincitore. Revisione dell'utente: l'obiettivo di sessione autorizza DB-07 e DB-08 senza fermarsi; il report è il punto di revisione.

## Step-by-Step Implementation Plan
1. Autorizzazione e lotto.
2. Esecuzione seriale per scenario.
3. Report e revisione con l'utente.

## Testing Plan
Live; nessuna modifica ai bracci durante il pilota.

## Out of Scope
- Catene da 3 e 8 (DB-08).
