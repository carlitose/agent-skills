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
- [ ] Il lot file dichiara braccio e snapshot (percorso + SHA-256); un hash diverso o uno snapshot mancante fallisce prima di qualsiasi start.
- [ ] Il bridge accetta `skills-only` con il metodo originale solo con snapshot non vuoto e lo registra nell'identità del journal; Pi bare resta invariato.
- [ ] Una cella non può cambiare braccio tra setup e run; ledger e ricevute riportano il braccio.
- [ ] Test offline RED→GREEN in Python e Node; CI esatta verde; merge.

## Frontier
Ready. Nessuna dipendenza aperta; il codice di riferimento è su main (#348, #349).

## Step-by-Step Implementation Plan
1. Scrivere i test RED per binding del braccio e drift dello snapshot.
2. Implementare opzione di braccio, binding nel lot e prompt di sistema nel bridge.
3. Eseguire la suite benchmark, lint e quick profile; PR, CI, merge.

## Testing Plan
Unit/integrazione offline con stream finto; install-only Harbor su un task originale con il braccio skills-only; nessuna chiamata al modello.

## Out of Scope
- Braccio c1a/c3a, modifiche ai task o al verifier.
- Esecuzione del lotto (TBA-02).
