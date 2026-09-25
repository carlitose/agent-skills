---
type: source
title: "TBA-05 — Benchmark privato stile Terminal-Bench (condizionale)"
identity_key: ticket:terminal-bench-best-arm/TBA-05
identity_strength: stable
source_path: docs/tickets/terminal-bench-best-arm/05-private-benchmark.md
source_digest: sha256:00a45de33261bbd34ee2e549273a99cd2a1b4c309ed626fc99beb3412ee08b04
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-09-25
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# TBA-05 — Benchmark privato stile Terminal-Bench (condizionale)

Compiled from `docs/tickets/terminal-bench-best-arm/05-private-benchmark.md`. Identity is `ticket:terminal-bench-best-arm/TBA-05`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-25** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-terminal-bench-best-arm]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-terminal-bench-best-arm-tba-05.md","payload_bytes":1519,"payload_sha256":"00a45de33261bbd34ee2e549273a99cd2a1b4c309ed626fc99beb3412ee08b04"}],"payload_bytes":1519,"payload_sha256":"00a45de33261bbd34ee2e549273a99cd2a1b4c309ed626fc99beb3412ee08b04","schema":1,"source_digest":"sha256:00a45de33261bbd34ee2e549273a99cd2a1b4c309ed626fc99beb3412ee08b04","source_identity":"ticket:terminal-bench-best-arm/TBA-05","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1519,"payload_sha256":"00a45de33261bbd34ee2e549273a99cd2a1b4c309ed626fc99beb3412ee08b04","schema":1,"source_digest":"sha256:00a45de33261bbd34ee2e549273a99cd2a1b4c309ed626fc99beb3412ee08b04","source_identity":"ticket:terminal-bench-best-arm/TBA-05"} -->
```markdown
---
ticket_schema: 1
ticket_id: "TBA-05"
execution_mode: HITL
blocked_by: []
---

# TBA-05 — Benchmark privato stile Terminal-Bench (condizionale)

## Artifact Graph
- Artifact ID: `ticket:terminal-bench-best-arm:05`
- Role: `ticket`
- Parent: [terminal-bench-best-arm.md](../../specs/terminal-bench-best-arm.md)

## Parent Spec
[terminal-bench-best-arm.md](../../specs/terminal-bench-best-arm.md)

## What to Build
Creare un piccolo set privato di task Harbor nel nostro dominio, con istruzione, immagine, test nascosti e verifier separato, da usare come held-out non contaminato o come fallback se l'harness originale diventa inutilizzabile. Sezione spec: Decision 5.

## Acceptance Criteria
- [ ] Esiste un via libera esplicito dell'utente con numero di task e domini.
- [ ] Ogni task è un pacchetto Harbor valido con verifier separato e soluzione di riferimento che passa; `harbor run` con l'adapter lo carica.
- [ ] I task non riusano testo o soluzioni di Terminal-Bench.

## Frontier
Richiede una decisione umana: attivare o no, con che dimensione. Oggi l'harness originale funziona, quindi resta condizionato.

## Step-by-Step Implementation Plan
1. Raccogliere dall'utente scope e domini.
2. Scrivere i task con `harbor init` e validarli con la soluzione di riferimento.
3. Integrare nel protocollo di TBA-04 come held-out aggiuntivo.

## Testing Plan
Validazione dei task con la soluzione di riferimento e con uno stub che deve fallire.

## Out of Scope
- Sostituire Terminal-Bench nel report di selezione.

```
