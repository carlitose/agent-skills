---
ticket_schema: 1
ticket_id: "TBA-02"
execution_mode: AFK
blocked_by:
  - "TBA-01"
---

# TBA-02 — Lotto skills-only sui 63 task originali

## Artifact Graph
- Artifact ID: `ticket:terminal-bench-best-arm:02`
- Role: `ticket`
- Parent: [terminal-bench-best-arm.md](../../specs/terminal-bench-best-arm.md)

## Parent Spec
[terminal-bench-best-arm.md](../../specs/terminal-bench-best-arm.md)

## What to Build
Eseguire il braccio skills-only una volta per task sulla stessa lista di 63 task del lotto B (GPU esclusi), con la stessa policy flat-rate (1.000 richieste per start), `-n 3` e lot/authority/ledger propri. Sezione spec: Decisions 1–3.

## Acceptance Criteria
- [ ] Lot file, authority e ledger nuovi, fuori da Git, vincolati alla head integrata di TBA-01.
- [ ] 63 celle avviate al massimo una volta, senza retry; ogni cella ha result.json Harbor, ricevuta e journal.
- [ ] Nessun container si sovrappone al lotto B; il report grezzo elenca reward, eccezioni, richieste, tempo e costo stimato per task.

## Frontier
Bloccato da TBA-01 e dalla fine del lotto B (Pi bare, TBF-04).

## Step-by-Step Implementation Plan
1. Verificare che il lotto B sia chiuso e nessun container sia attivo.
2. Creare lot/authority con policy flat-rate e braccio skills-only; install-only di controllo.
3. Lanciare Harbor, monitorare, raccogliere i risultati.

## Testing Plan
Controlli live sul ledger e sui result.json; nessun gate di budget (token flat-rate).

## Out of Scope
- Seconda ripetizione (decisa in TBA-03).
- Modifiche all'agente.
