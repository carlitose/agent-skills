---
type: source
title: "WCP-01 — Dejar de relanzar procesos para preguntas ya respondidas"
identity_key: ticket:wiki-compile-process-cost/WCP-01
identity_strength: stable
source_path: docs/tickets/wiki-compile-process-cost/01-stop-relaunching-processes.md
source_digest: sha256:ea669f7777370fa07152f7a747d553eccb5d7f897bb48ba546eac27b29565de4
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-09-22
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# WCP-01 — Dejar de relanzar procesos para preguntas ya respondidas

Compiled from `docs/tickets/wiki-compile-process-cost/01-stop-relaunching-processes.md`. Identity is `ticket:wiki-compile-process-cost/WCP-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-22** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/spec-wiki-compile-process-cost]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-wiki-compile-process-cost-wcp-01.md","payload_bytes":2357,"payload_sha256":"ea669f7777370fa07152f7a747d553eccb5d7f897bb48ba546eac27b29565de4"}],"payload_bytes":2357,"payload_sha256":"ea669f7777370fa07152f7a747d553eccb5d7f897bb48ba546eac27b29565de4","schema":1,"source_digest":"sha256:ea669f7777370fa07152f7a747d553eccb5d7f897bb48ba546eac27b29565de4","source_identity":"ticket:wiki-compile-process-cost/WCP-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2357,"payload_sha256":"ea669f7777370fa07152f7a747d553eccb5d7f897bb48ba546eac27b29565de4","schema":1,"source_digest":"sha256:ea669f7777370fa07152f7a747d553eccb5d7f897bb48ba546eac27b29565de4","source_identity":"ticket:wiki-compile-process-cost/WCP-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "WCP-01"
execution_mode: AFK
blocked_by: []
---

# WCP-01 — Dejar de relanzar procesos para preguntas ya respondidas

## Artifact Graph
- Artifact ID: `ticket:wiki-compile-process-cost:01`
- Role: `ticket`
- Parent: [wiki-compile-process-cost.md](../../specs/wiki-compile-process-cost.md)

## Parent Spec
[wiki-compile-process-cost.md](../../specs/wiki-compile-process-cost.md)

## What to Build
En `date_provenance.py`, recordar por estado del repositorio la respuesta de `rev-parse` y el
conjunto de ficheros versionados, leyendo ese estado del sistema de ficheros (`.git` y su
índice). En `ingest_docs.py`, resolver los tickets de un árbol con un solo `ticket-list --json`
del CLI canónico, recordado con una huella barata del árbol, y dejar `ticket-parse` como camino
para lo que el inventario no nombre. Cubre los diez criterios de la spec.

## Acceptance Criteria
- [ ] Cinco artefactos del mismo repositorio cuestan un `rev-parse` y un `ls-files`.
- [ ] Un `commit` entre dos llamadas se ve en la segunda.
- [ ] Un directorio que se convierte en repositorio se ve.
- [ ] Dos repositorios distintos no comparten respuesta.
- [ ] Un árbol de tickets cuesta un solo proceso, y es `ticket-list`.
- [ ] Los bloqueos del ticket sobreviven al inventario.
- [ ] Un ticket editado o añadido nunca se responde con la lectura anterior.
- [ ] Un ticket malformado falla con el mensaje del analizador canónico.
- [ ] Un ticket fuera de la disposición habitual se sigue analizando.
- [ ] La suite completa de `llm-wiki` pasa, incluida la prueba de independencia.

## Frontier
Ready. Skills-only inline sobre `d4d69e07…`.

## Step-by-Step Implementation Plan
1. Medir por fases y atribuir el coste a procesos antes de tocar nada.
2. Escribir las pruebas de coste y de invalidación.
3. Recordar las respuestas del repositorio; inventariar el árbol de tickets en un proceso.
4. Volver a medir sobre la misma copia y ejecutar la suite completa.
5. Handoff con límites; entrega aparte con autoridad y readback frescos.

## Testing Plan
Suite completa de `llm-wiki` más una nueva de coste. La medición usa una copia desechable de una
wiki real; no se publica nada ni se toca el repositorio del proyecto.

## Out of Scope
Sync incremental con caché persistente, agrupar `git log --follow`, y el resto del coste del
lint.

```
