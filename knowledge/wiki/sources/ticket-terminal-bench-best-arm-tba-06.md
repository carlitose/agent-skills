---
type: source
title: "TBA-06 — Bracci ticket-driver c1a/c3a generici sull'adapter originale"
identity_key: ticket:terminal-bench-best-arm/TBA-06
identity_strength: stable
source_path: docs/tickets/terminal-bench-best-arm/done/06-generic-driver-arms.md
source_digest: sha256:c056f7f7ec403a5324cd2186ad2a8a671fc2bb49af969c75caf9b6743f7805e8
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-26
created_provenance: git-commit
disposition_changed: 2026-09-26
disposition_changed_provenance: git-rename
---

# TBA-06 — Bracci ticket-driver c1a/c3a generici sull'adapter originale

Compiled from `docs/tickets/terminal-bench-best-arm/done/06-generic-driver-arms.md`. Identity is `ticket:terminal-bench-best-arm/TBA-06`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-26** via `git-commit`
- Disposition changed: **2026-09-26** via `git-rename`

## Graph

- Parent source: [[sources/artifact-terminal-bench-best-arm]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-terminal-bench-best-arm-tba-06.md","payload_bytes":3111,"payload_sha256":"c056f7f7ec403a5324cd2186ad2a8a671fc2bb49af969c75caf9b6743f7805e8"}],"payload_bytes":3111,"payload_sha256":"c056f7f7ec403a5324cd2186ad2a8a671fc2bb49af969c75caf9b6743f7805e8","schema":1,"source_digest":"sha256:c056f7f7ec403a5324cd2186ad2a8a671fc2bb49af969c75caf9b6743f7805e8","source_identity":"ticket:terminal-bench-best-arm/TBA-06","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3111,"payload_sha256":"c056f7f7ec403a5324cd2186ad2a8a671fc2bb49af969c75caf9b6743f7805e8","schema":1,"source_digest":"sha256:c056f7f7ec403a5324cd2186ad2a8a671fc2bb49af969c75caf9b6743f7805e8","source_identity":"ticket:terminal-bench-best-arm/TBA-06"} -->
```markdown
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

```
