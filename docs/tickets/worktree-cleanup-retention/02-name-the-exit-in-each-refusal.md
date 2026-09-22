---
ticket_schema: 1
ticket_id: "WGR-02"
execution_mode: AFK
blocked_by: []
---

# WGR-02 — Que cada rechazo de limpieza nombre la salida que sí existe

## Artifact Graph
- Artifact ID: `ticket:worktree-cleanup-retention:02`
- Role: `ticket`
- Parent: [worktree-cleanup-retention.md](../../specs/worktree-cleanup-retention.md)

## Parent Spec
[worktree-cleanup-retention.md](../../specs/worktree-cleanup-retention.md)

## What to Build
Cambiar los tres rechazos de limpieza que hoy no dicen cómo se abren para que nombren el acto
exacto y su comando: run en curso (`abort` con actor y motivo, o esperar a que termine), run en
pausa (`unpause`), y ticket en espera administrativa o cancelado (`ticket-reopen-request` para
reabrirlo). El mensaje incluye el identificador de la run o del ticket implicado. Ninguna
condición se relaja: lo que hoy se rechaza se sigue rechazando exactamente igual. Cubre la
sección «Segunda parte: nombrar la salida» de la spec.

## Acceptance Criteria
- [ ] El rechazo de una run en curso nombra `abort`, y que hace falta actor y motivo.
- [ ] El rechazo por pausa nombra `unpause` y el identificador de la run.
- [ ] El rechazo por ticket en espera o cancelado nombra el ticket y cómo se reabre.
- [ ] Las condiciones no cambian: cada caso que hoy se rechaza se sigue rechazando, demostrado
      caso por caso.
- [ ] Los dos rechazos que ya nombraban su salida —`--confirm` y `--force`— siguen igual.
- [ ] Las suites `tests/test_kernel.py` y la suite nueva pasan enteras.

## Frontier
Ready. Skills-only inline. Sin decisiones humanas pendientes. Integración es un gate aparte.

## Step-by-Step Implementation Plan
1. Emitir y validar ticket, grafo y candidato con las funciones canónicas puras.
2. Escribir las pruebas de los cinco mensajes y registrarlas en RED.
3. Cambiar los tres mensajes, sin tocar ninguna condición.
4. Ejecutar lint y las suites afectadas; revisar, QA causal y auditoría.
5. Handoff con límites; entrega aparte, con autoridad y readback frescos, y perfil alojado sobre
   el head exacto.

## Testing Plan
Máximo 900 s por comando, cada intento registrado. Las pruebas construyen ledgers en memoria y
repositorios temporales; ninguna run real se toca.

## Out of Scope
Permitir la limpieza de una run en curso, en pausa o con un ticket en espera; borrar worktrees;
la prueba de retención de WGR-01, ya entregada.
