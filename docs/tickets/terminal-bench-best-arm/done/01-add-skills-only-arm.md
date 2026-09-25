---
ticket_schema: 1
ticket_id: "TBA-01"
execution_mode: AFK
blocked_by: []
---

# TBA-01 — Braccio skills-only sull'adapter originale

## Artifact Graph
- Artifact ID: `ticket:terminal-bench-best-arm:01`
- Role: `ticket`
- Parent: [terminal-bench-best-arm.md](../../specs/terminal-bench-best-arm.md)

## Parent Spec
[terminal-bench-best-arm.md](../../specs/terminal-bench-best-arm.md)

## What to Build
Estendere `standard_full:FullStandardPiHarborAgent` con un'opzione di braccio `skills-only` che aggiunge al system prompt lo snapshot congelato di TBF-05 (`comparison-skills.md`, sha256 `cfda5721…`), vincolato per hash nel lot file. Pi espone ancora solo `sandbox_exec`; Pi bare resta byte-identico. Sezioni spec: Decisions 1–2, Invariants.

## Acceptance Criteria
- [x] Il lot file dichiara braccio e snapshot (percorso + SHA-256); un hash diverso o uno snapshot mancante fallisce prima di qualsiasi start.
- [x] Il bridge accetta `skills-only` con il metodo originale solo con snapshot non vuoto e lo registra nell'identità del journal; Pi bare resta invariato.
- [x] Una cella non può cambiare braccio tra setup e run; ledger e ricevute riportano il braccio.
- [x] Test offline RED→GREEN in Python e Node; CI esatta verde; merge.

## Frontier
**Completato** in esecuzione skills-only: RED (2 Python, 2 Node) → GREEN 110 Python e 29 Node; install-only Harbor reale su `html-js-filter` con lotto skills-only (header `arms: [skills-only]`, `skills_sha256` `cfda5721…`, 0 start, nessuna eccezione). Pi bare resta byte-identico (system prompt verificato nei test). CI esatta e merge registrati nella PR di consegna; spostato in `done/` senza ricevuta del runner.

## Step-by-Step Implementation Plan
1. Scrivere i test RED per binding del braccio e drift dello snapshot.
2. Implementare opzione di braccio, binding nel lot e prompt di sistema nel bridge.
3. Eseguire la suite benchmark, lint e quick profile; PR, CI, merge.

## Testing Plan
Unit/integrazione offline con stream finto; install-only Harbor su un task originale con il braccio skills-only; nessuna chiamata al modello.

## Out of Scope
- Braccio c1a/c3a, modifiche ai task o al verifier.
- Esecuzione del lotto (TBA-02).
