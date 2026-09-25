---
type: source
title: "Declarar el seguimiento de los JSON por test del prototipo de cobertura"
identity_key: ticket:no-dangling-work/NDW-03
identity_strength: stable
source_path: docs/tickets/no-dangling-work/done/03-slice.md
source_digest: sha256:a766da805b80b74d81722c1529b9f10bc2be35c20339d8b94851c33d7592ecaa
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-21
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Declarar el seguimiento de los JSON por test del prototipo de cobertura

Compiled from `docs/tickets/no-dangling-work/done/03-slice.md`. Identity is `ticket:no-dangling-work/NDW-03`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-21** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/spec-no-dangling-work]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-no-dangling-work-ndw-03.md","payload_bytes":1530,"payload_sha256":"a766da805b80b74d81722c1529b9f10bc2be35c20339d8b94851c33d7592ecaa"}],"payload_bytes":1530,"payload_sha256":"a766da805b80b74d81722c1529b9f10bc2be35c20339d8b94851c33d7592ecaa","schema":1,"source_digest":"sha256:a766da805b80b74d81722c1529b9f10bc2be35c20339d8b94851c33d7592ecaa","source_identity":"ticket:no-dangling-work/NDW-03","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1530,"payload_sha256":"a766da805b80b74d81722c1529b9f10bc2be35c20339d8b94851c33d7592ecaa","schema":1,"source_digest":"sha256:a766da805b80b74d81722c1529b9f10bc2be35c20339d8b94851c33d7592ecaa","source_identity":"ticket:no-dangling-work/NDW-03"} -->
```markdown
---
ticket_schema: 1
ticket_id: "NDW-03"
execution_mode: AFK
blocked_by: []
---

# Declarar el seguimiento de los JSON por test del prototipo de cobertura

## Artifact Graph
- Artifact ID: `artifact:no-dangling-work-03`
- Role: `ticket`
- Parent: [Ningún trabajo colgado al cerrar una fase](../../specs/no-dangling-work.md)

## Parent Spec
[Ningún trabajo colgado al cerrar una fase](../../specs/no-dangling-work.md)

## What to Build
Añadir a `.gitignore` los JSON por test que `docs/prototypes/suite-cost-one-percent/coverage_matrix.py`
escribe en `docs/prototypes/suite-cost-one-percent/coverage/`, conservando versionado el
`report.json` agregado, y declarar esa decisión en el docstring del script: el agregado es la
evidencia, los ficheros por test son materia prima regenerable.

## Acceptance Criteria
- [ ] Tras regenerar la cobertura, `git status` no muestra los JSON por test como sin seguimiento.
- [ ] `report.json` sigue versionado y sin cambios de política.
- [ ] El docstring del script dice qué se versiona y qué se ignora.
- [ ] Ninguna otra ruta cambia de estado de seguimiento.

## Frontier
Independiente y pequeño.

## Step-by-Step Implementation Plan
1. Comprobar qué escribe el script y que `report.json` es el agregado.
2. Añadir la regla de `.gitignore` y el docstring.
3. Verificar con el propio script que el estado queda limpio.

## Testing Plan
Ejecución del prototipo y `git status`; perfil quick en ambas plataformas.

## Out of Scope
- Cambiar el contenido o el formato de la cobertura.

```
