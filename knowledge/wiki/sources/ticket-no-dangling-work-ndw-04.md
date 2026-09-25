---
type: source
title: "Resolver los worktrees con proyección a medias que existen hoy"
identity_key: ticket:no-dangling-work/NDW-04
identity_strength: stable
source_path: docs/tickets/no-dangling-work/done/04-slice.md
source_digest: sha256:328451e2696bbfc01506fdae3a291bf89f53ac88cac5780af54b5ec55884b0c0
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-19
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Resolver los worktrees con proyección a medias que existen hoy

Compiled from `docs/tickets/no-dangling-work/done/04-slice.md`. Identity is `ticket:no-dangling-work/NDW-04`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-19** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/spec-no-dangling-work]]
- Blocked by: [[sources/ticket-no-dangling-work-ndw-01]] — `ticket:no-dangling-work/NDW-01`
- Blocked by: [[sources/ticket-no-dangling-work-ndw-02]] — `ticket:no-dangling-work/NDW-02`
- Blocked by: [[sources/ticket-no-dangling-work-ndw-03]] — `ticket:no-dangling-work/NDW-03`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-no-dangling-work-ndw-04.md","payload_bytes":2151,"payload_sha256":"328451e2696bbfc01506fdae3a291bf89f53ac88cac5780af54b5ec55884b0c0"}],"payload_bytes":2151,"payload_sha256":"328451e2696bbfc01506fdae3a291bf89f53ac88cac5780af54b5ec55884b0c0","schema":1,"source_digest":"sha256:328451e2696bbfc01506fdae3a291bf89f53ac88cac5780af54b5ec55884b0c0","source_identity":"ticket:no-dangling-work/NDW-04","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2151,"payload_sha256":"328451e2696bbfc01506fdae3a291bf89f53ac88cac5780af54b5ec55884b0c0","schema":1,"source_digest":"sha256:328451e2696bbfc01506fdae3a291bf89f53ac88cac5780af54b5ec55884b0c0","source_identity":"ticket:no-dangling-work/NDW-04"} -->
```markdown
---
ticket_schema: 1
ticket_id: "NDW-04"
execution_mode: HITL
blocked_by:
  - "NDW-01"
  - "NDW-02"
  - "NDW-03"
---

# Resolver los worktrees con proyección a medias que existen hoy

## Artifact Graph
- Artifact ID: `artifact:no-dangling-work-04`
- Role: `ticket`
- Parent: [Ningún trabajo colgado al cerrar una fase](../../specs/no-dangling-work.md)

## Parent Spec
[Ningún trabajo colgado al cerrar una fase](../../specs/no-dangling-work.md)

## What to Build
Aplicar la Decisión 3 del spec a los worktrees actuales con proyección de completion staged y
nunca commiteada: `foundation-delivery`, `foundation-delivery-v2`, `suite-cost-deps-04-05-final-v4`,
`linux-fixtures-prerequisite`, `suite-cost-one-percent-final` y `suite-cost-ticket06-execution`,
más los tres temporales `ticket-wiki-*` huérfanos. Para cada uno: guardar patch verificable por
hash, comprobar si su ticket integró por otra vía (ancestro en `main` y comparación de blobs), y
proponer `discard` o `handoff`. La retirada misma requiere autorización humana explícita por
entrada; este ticket produce el inventario, los patches y la propuesta, no el borrado.

## Acceptance Criteria
- [ ] Existe un patch por worktree sucio, con hash registrado, antes de proponer nada.
- [ ] Cada entrada tiene una propuesta motivada: `discard` con la evidencia de integración, o
      `handoff` con lo que contiene y por qué no está en `main`.
- [ ] Ninguna retirada se ejecuta sin autorización humana registrada para esa entrada.
- [ ] El recibo final deja el inventario de checkouts del repositorio sin rutas sin disposición.

## Frontier
Bloqueado por los tres slices anteriores: la regla, la herramienta y la política de cobertura
deben existir antes de la limpieza única, para que no vuelva a acumularse.

## Step-by-Step Implementation Plan
1. Inventariar y guardar patches.
2. Clasificar cada entrada con evidencia.
3. Presentar la propuesta y ejecutar solo lo autorizado, con recibo.

## Testing Plan
Verificación por hash de cada patch y `worktree-gc-plan` después de la operación.

## Out of Scope
- Borrar sin autorización; tocar checkouts de otros repositorios.

```
