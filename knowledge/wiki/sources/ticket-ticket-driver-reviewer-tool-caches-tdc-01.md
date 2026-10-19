---
type: source
title: "TDC-01 — Le cache degli strumenti non sono scritture del revisore diretto"
identity_key: ticket:ticket-driver-reviewer-tool-caches/TDC-01
identity_strength: stable
source_path: docs/tickets/ticket-driver-reviewer-tool-caches/done/01-tool-caches-are-not-writes.md
source_digest: sha256:a9fae6b455d4bc99e88af4b4501a34cc2fab39fb0190b2e5e6699ad9a572766c
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-10-01
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# TDC-01 — Le cache degli strumenti non sono scritture del revisore diretto

Compiled from `docs/tickets/ticket-driver-reviewer-tool-caches/done/01-tool-caches-are-not-writes.md`. Identity is `ticket:ticket-driver-reviewer-tool-caches/TDC-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-01** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/spec-ticket-driver-reviewer-tool-caches]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[9],"status":"present"},"frontier":{"headings":[6],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[8],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-ticket-driver-reviewer-tool-caches-tdc-01.md","payload_bytes":2016,"payload_sha256":"a9fae6b455d4bc99e88af4b4501a34cc2fab39fb0190b2e5e6699ad9a572766c"}],"payload_bytes":2016,"payload_sha256":"a9fae6b455d4bc99e88af4b4501a34cc2fab39fb0190b2e5e6699ad9a572766c","schema":1,"source_digest":"sha256:a9fae6b455d4bc99e88af4b4501a34cc2fab39fb0190b2e5e6699ad9a572766c","source_identity":"ticket:ticket-driver-reviewer-tool-caches/TDC-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 8: Testing Plan |
| frontier | 6: Frontier |
| exclusions | 9: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2016,"payload_sha256":"a9fae6b455d4bc99e88af4b4501a34cc2fab39fb0190b2e5e6699ad9a572766c","schema":1,"source_digest":"sha256:a9fae6b455d4bc99e88af4b4501a34cc2fab39fb0190b2e5e6699ad9a572766c","source_identity":"ticket:ticket-driver-reviewer-tool-caches/TDC-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "TDC-01"
execution_mode: AFK
blocked_by: []
---

# TDC-01 — Le cache degli strumenti non sono scritture del revisore diretto

## Artifact Graph
- Artifact ID: `ticket:ticket-driver-reviewer-tool-caches:01`
- Role: `ticket`
- Parent: [ticket-driver-reviewer-tool-caches.md](../../specs/ticket-driver-reviewer-tool-caches.md)

## Parent Spec
[ticket-driver-reviewer-tool-caches.md](../../specs/ticket-driver-reviewer-tool-caches.md)

## What to Build
In `ticket-driver/scripts/risk.py`, `directed_review` esclude dal controllo delle scritture le
cartelle di cache degli strumenti (`TOOL_CACHES`) e il loro contenuto, e le registra
nell'evento `directed-tool-caches`. Ogni altro percorso nella scratch ferma il run come prima.
La foglia finta dei test lascia queste cache, e in un secondo modo anche un file proprio.

## Acceptance Criteria
- [x] Un revisore che lascia `.pytest_cache` e `__pycache__` nella scratch integra, e il ledger
  registra le due cache. Prima della correzione il run si ferma con
  `directed reviewer wrote outside artifact`.
- [x] Un revisore che lascia le cache e un file proprio resta fermo, e l'evento della violazione
  elenca solo il file. Prima della correzione elenca anche le cache.
- [x] Il test esistente sulla scrittura relativa nel prodotto resta verde, con l'intera suite di
  `ticket-driver`.

## Outcome
2026-10-01. I due test nuovi falliscono prima della correzione e passano dopo, con l'intera suite
di `ticket-driver`.

## Frontier
Chiuso. Vale da una nuova `prepare-drivers`; le copie del lotto `dbh-opus` non cambiano.

## Step-by-Step Implementation Plan
1. Test RED in `test_c3.py` e due modi nuovi della foglia finta.
2. `TOOL_CACHES` e `_tool_cache` in `risk.py`, usati dal controllo delle scritture.
3. Suite di `ticket-driver`.

## Testing Plan
`python -B -m unittest discover -s tests` da `ticket-driver`.

## Out of Scope
- La cartella di lavoro del revisore e i comandi che può eseguire.
- Le cache nella worktree del candidato.

```
