---
type: source
title: "TBA-01 — Braccio skills-only sull'adapter originale"
identity_key: ticket:terminal-bench-best-arm/TBA-01
identity_strength: stable
source_path: docs/tickets/terminal-bench-best-arm/done/01-add-skills-only-arm.md
source_digest: sha256:acf026c436d97b4dda38bdd4809f766911a4e2f80e7c48c3eb694a5674357d8f
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-25
created_provenance: git-commit
disposition_changed: 2026-09-25
disposition_changed_provenance: git-rename
---

# TBA-01 — Braccio skills-only sull'adapter originale

Compiled from `docs/tickets/terminal-bench-best-arm/done/01-add-skills-only-arm.md`. Identity is `ticket:terminal-bench-best-arm/TBA-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-25** via `git-commit`
- Disposition changed: **2026-09-25** via `git-rename`

## Graph

- Parent source: [[sources/artifact-terminal-bench-best-arm]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-terminal-bench-best-arm-tba-01.md","payload_bytes":2201,"payload_sha256":"acf026c436d97b4dda38bdd4809f766911a4e2f80e7c48c3eb694a5674357d8f"}],"payload_bytes":2201,"payload_sha256":"acf026c436d97b4dda38bdd4809f766911a4e2f80e7c48c3eb694a5674357d8f","schema":1,"source_digest":"sha256:acf026c436d97b4dda38bdd4809f766911a4e2f80e7c48c3eb694a5674357d8f","source_identity":"ticket:terminal-bench-best-arm/TBA-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2201,"payload_sha256":"acf026c436d97b4dda38bdd4809f766911a4e2f80e7c48c3eb694a5674357d8f","schema":1,"source_digest":"sha256:acf026c436d97b4dda38bdd4809f766911a4e2f80e7c48c3eb694a5674357d8f","source_identity":"ticket:terminal-bench-best-arm/TBA-01"} -->
```markdown
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

```
