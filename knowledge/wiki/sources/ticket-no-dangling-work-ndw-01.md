---
type: source
title: "Añadir el estado del árbol como sexta comprobación del checkpoint"
identity_key: ticket:no-dangling-work/NDW-01
identity_strength: stable
source_path: docs/tickets/no-dangling-work/done/01-slice.md
source_digest: sha256:3810f8334b66e7dcb62e1dce585b637cad6aca0abf58074a11e0f3d29427bd41
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-21
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Añadir el estado del árbol como sexta comprobación del checkpoint

Compiled from `docs/tickets/no-dangling-work/done/01-slice.md`. Identity is `ticket:no-dangling-work/NDW-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-21** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/spec-no-dangling-work]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-no-dangling-work-ndw-01.md","payload_bytes":2289,"payload_sha256":"3810f8334b66e7dcb62e1dce585b637cad6aca0abf58074a11e0f3d29427bd41"}],"payload_bytes":2289,"payload_sha256":"3810f8334b66e7dcb62e1dce585b637cad6aca0abf58074a11e0f3d29427bd41","schema":1,"source_digest":"sha256:3810f8334b66e7dcb62e1dce585b637cad6aca0abf58074a11e0f3d29427bd41","source_identity":"ticket:no-dangling-work/NDW-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2289,"payload_sha256":"3810f8334b66e7dcb62e1dce585b637cad6aca0abf58074a11e0f3d29427bd41","schema":1,"source_digest":"sha256:3810f8334b66e7dcb62e1dce585b637cad6aca0abf58074a11e0f3d29427bd41","source_identity":"ticket:no-dangling-work/NDW-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "NDW-01"
execution_mode: AFK
blocked_by: []
---

# Añadir el estado del árbol como sexta comprobación del checkpoint

## Artifact Graph
- Artifact ID: `artifact:no-dangling-work-01`
- Role: `ticket`
- Parent: [Ningún trabajo colgado al cerrar una fase](../../specs/no-dangling-work.md)

## Parent Spec
[Ningún trabajo colgado al cerrar una fase](../../specs/no-dangling-work.md)

## What to Build
Ampliar `ask-skills/PLAN-REVIEW-CHECKPOINT.md` con una sexta comprobación, **estado del árbol**: al
cerrar una fase se inventarían todos los checkouts del repositorio (`git worktree list` y
`worktree-gc-plan`) y cada ruta no limpia recibe exactamente una disposición —`commit` con su
ticket, `discard` con su razón, o `handoff` con destinatario y patch guardado—. La regla dice
explícitamente que «lo miro luego» no es una disposición, y que un worktree con proyección
aplicada y ticket no integrado nunca se descarta sin patch.

Añadir el spec del padre al repositorio y ampliar `test_plan_review_checkpoint.py` para que la
sexta comprobación y las tres disposiciones sean verificables estructuralmente.

## Acceptance Criteria
- [ ] La referencia del checkpoint enumera seis comprobaciones y la sexta es el estado del árbol.
- [ ] Nombra las tres disposiciones exactas y declara que no existe una cuarta.
- [ ] Dice que el inventario cubre todos los checkouts del repositorio, no solo el activo.
- [ ] Protege la única copia: proyección aplicada y ticket no integrado implica patch antes de
      cualquier descarte.
- [ ] La prueba estructural falla si desaparece cualquiera de esos puntos y la referencia sigue
      por debajo de su límite de palabras.
- [ ] El spec del padre queda añadido en la misma entrega.

## Frontier
Independiente. Es documentación de disciplina y su prueba estructural.

## Step-by-Step Implementation Plan
1. Ampliar primero la prueba para que falle.
2. Redactar la sexta comprobación en la referencia, respetando el límite de palabras.
3. Ejecutar la prueba y las suites de skills.

## Testing Plan
Prueba estructural ampliada, suites de skills y grafo, perfil quick en ambas plataformas.

## Out of Scope
- El barrido del runner y la resolución de los worktrees actuales, que son slices propios.

```
