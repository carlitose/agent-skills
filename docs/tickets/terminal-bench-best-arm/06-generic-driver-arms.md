---
ticket_schema: 1
ticket_id: "TBA-06"
execution_mode: AFK
blocked_by: []
---

# TBA-06 — Bracci ticket-driver c1a/c3a generici sull'adapter originale

## Artifact Graph
- Artifact ID: `ticket:terminal-bench-best-arm:06`
- Role: `ticket`
- Parent: [terminal-bench-best-arm.md](../../specs/terminal-bench-best-arm.md)

## Parent Spec
[terminal-bench-best-arm.md](../../specs/terminal-bench-best-arm.md)

## What to Build
Aggiungere all'adapter originale i bracci `ticket-driver-c1a` e `ticket-driver-c3a` secondo la sezione *Generic ticket-driver arms* della spec: builder con skill, checker fresco con verdetto, per c3a revisore fresco e giudizi Jev host-only, al massimo una correzione, nessun rollback. Il bridge impone la grammatica delle fasi.

## Acceptance Criteria
- [ ] Il lot dichiara braccio c1a/c3a con lo snapshot delle skill vincolato per SHA-256; c3a richiede una chiave Jev host-only fuori da Git e fallisce prima di qualsiasi start se manca.
- [ ] Il bridge accetta per il metodo originale solo builder (istruzione invariata), checker, reviewer (solo c3a) e un corrector, in quest'ordine, con prompt che contengono l'istruzione originale e system prompt costanti; qualsiasi altra sequenza è rifiutata prima della richiesta al modello.
- [ ] c1a: verdetto `PASS` → nessuna correzione; altrimenti una correzione con il report del checker. c3a: correzione se un giudizio Jev non approva o il checker non passa; fallimento/incertezza Jev → fallback deterministico registrato.
- [ ] Il costo della cella somma modello e Jev dai journal; la chiave Jev non entra nell'ambiente di Pi; i campi di stato Jev restano entro 24 KiB.
- [ ] Pi bare e skills-only restano byte-identici; test offline RED→GREEN in Python e Node; CI esatta verde; merge.

## Frontier
Ready. TBA-01 è integrato; il lotto skills-only (TBA-02) gira in parallelo e non viene toccato.

## Step-by-Step Implementation Plan
1. Test RED per grammatica delle fasi (Node) e flusso/decisioni/costi (Python) con processi e Jev finti.
2. Implementare bridge, agente e generalizzazione di ComparisonJev all'identità del metodo originale.
3. Suite benchmark, lint, quick profile; install-only Harbor reale per c1a e c3a; PR, CI, merge.

## Testing Plan
Unit/integrazione offline con stream e transport Jev finti; install-only Harbor senza modello; nessun lotto live qui.

## Out of Scope
- Eseguire i lotti (TBA-07).
- Riprodurre fedelmente il ticket-driver originale, smoke per task o Git.
