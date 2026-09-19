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
