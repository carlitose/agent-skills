---
ticket_schema: 1
ticket_id: "PUF-01"
execution_mode: AFK
blocked_by: []
---

# PUF-01 — Mandar solo los campos que cambian al actualizar una pull request

## Artifact Graph
- Artifact ID: `ticket:pr-update-field-scope:01`
- Role: `ticket`
- Parent: [pr-update-field-scope.md](../../specs/pr-update-field-scope.md)

## Parent Spec
[pr-update-field-scope.md](../../specs/pr-update-field-scope.md)

## What to Build
Lectura previa, PATCH con los campos que difieren, rechazo anticipado de mover la base de
una pull request no abierta y reconciliación de efectos tras un fallo. Cubre Decisión,
Invariantes y Criterios de la spec.

## Acceptance Criteria
- [ ] Sin diferencias, ningún PATCH.
- [ ] Solo el cuerpo distinto, PATCH con solo `body`.
- [ ] Pull request fusionada: la base no viaja en la petición.
- [ ] Mover la base de una fusionada se rechaza nombrando el estado.
- [ ] Un fallo informa de los campos ya aplicados y no se reintenta.
- [ ] Suites de proveedor, kernel y wiki siguen pasando.

## Frontier
Ready. Skills-only inline. Sin decisiones humanas pendientes. Integración es un gate aparte.

## Step-by-Step Implementation Plan
1. Emitir y validar ticket, grafo y candidato con las funciones canónicas puras.
2. Escribir en RED las pruebas del alcance de campos y de la reconciliación.
3. Leer antes de mutar, enviar solo lo que difiere y reconciliar tras un fallo.
4. Ejecutar proveedor, kernel y wiki; revisar, QA causal y auditoría canónica.
5. Handoff con límites; entrega aparte, con autoridad y readback frescos.

## Testing Plan
Máximo 900 s por comando, cada intento registrado. Pruebas nuevas con dobles del CLI,
suites de proveedor, kernel completo y wiki. Sin llamadas reales a GitHub y sin reproducir
el 422 contra el servicio.

## Out of Scope
Azure DevOps, #45, el límite de 4000 caracteres, reintentos, rutas nuevas del proveedor,
#42 y reactivar el runner.
