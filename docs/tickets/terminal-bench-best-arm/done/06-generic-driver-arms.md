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
- [x] Il lot dichiara braccio c1a/c3a con lo snapshot delle skill vincolato per SHA-256; c3a richiede una chiave Jev host-only fuori da Git e fallisce prima di qualsiasi start se manca.
- [x] Il bridge accetta per il metodo originale solo builder (istruzione invariata), checker, reviewer (solo c3a) e un corrector, in quest'ordine, con prompt che contengono l'istruzione originale e system prompt costanti; qualsiasi altra sequenza è rifiutata prima della richiesta al modello.
- [x] c1a: verdetto `PASS` → nessuna correzione; altrimenti una correzione con il report del checker. c3a: correzione se un giudizio Jev non approva o il checker non passa; fallimento/incertezza Jev → fallback deterministico registrato.
- [x] Il costo della cella somma modello e Jev dai journal; la chiave Jev non entra nell'ambiente di Pi; i campi di stato Jev restano entro 24 KiB.
- [x] Pi bare e skills-only restano byte-identici; test offline RED→GREEN in Python e Node; CI esatta verde; merge.

## Frontier
**Completato** in esecuzione skills-only. RED: 3 test Node e l'import Python mancante; GREEN: 131 test Python e 32 Node della suite benchmark, lint. Install-only Harbor reale su `html-js-filter` per c1a e c3a (header `arms` corretto, snapshot `cfda5721…`, 0 start, nessuna eccezione). Una sola richiesta Jev reale tramite `ComparisonJev` e `jev_key_scope`: esito `yes`, costo noto $0,000014868, chiave mai stampata né passata a Pi. Corretto durante GREEN un bug di `fit_jev_state` (eccedenza maggiore del campo più lungo). Il test TBA-01 che rifiutava c1a è stato aggiornato al nuovo contratto. Il lotto skills-only (TBA-02) non è stato toccato. CI esatta e merge registrati nella PR; spostato in `done/` senza ricevuta del runner.

## Step-by-Step Implementation Plan
1. Test RED per grammatica delle fasi (Node) e flusso/decisioni/costi (Python) con processi e Jev finti.
2. Implementare bridge, agente e generalizzazione di ComparisonJev all'identità del metodo originale.
3. Suite benchmark, lint, quick profile; install-only Harbor reale per c1a e c3a; PR, CI, merge.

## Testing Plan
Unit/integrazione offline con stream e transport Jev finti; install-only Harbor senza modello; nessun lotto live qui.

## Out of Scope
- Eseguire i lotti (TBA-07).
- Riprodurre fedelmente il ticket-driver originale, smoke per task o Git.
