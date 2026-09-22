---
ticket_schema: 1
ticket_id: "AWD-01"
execution_mode: AFK
blocked_by: []
---

# AWD-01 — Pasar el cuerpo por fichero cuando `az` es un envoltorio por lotes

## Artifact Graph
- Artifact ID: `ticket:azure-windows-delivery:01`
- Role: `ticket`
- Parent: [azure-windows-delivery.md](../../specs/azure-windows-delivery.md)

## Parent Spec
[azure-windows-delivery.md](../../specs/azure-windows-delivery.md)

## What to Build
Detectar que el ejecutable resuelto es un envoltorio por lotes de Windows y, en ese caso,
escribir el cuerpo en un fichero temporal fuera del worktree y pasarlo como un único valor
`@fichero`. Conservar intacto el argv por línea en el resto de casos. Rechazar antes de llamar
un cuerpo de más de 4000 caracteres, nombrando longitud y límite. Acotar el mensaje de error de
un mandato fallido para que no arrastre el cuerpo. Cubre Decisión, Invariantes y Criterios de
la spec.

## Acceptance Criteria
- [ ] Con envoltorio por lotes: `--description` seguido de un único `@fichero` cuyo contenido
      es el cuerpo tal cual.
- [ ] Ningún elemento del argv con salto de línea ni metacaracteres de `cmd.exe` en ese caso.
- [ ] El fichero temporal no está dentro del worktree y desaparece al terminar.
- [ ] Sin envoltorio por lotes, el argv por línea no cambia.
- [ ] Un cuerpo de más de 4000 caracteres se rechaza antes de ejecutar nada.
- [ ] El mensaje de error queda acotado y conserva `stderr` completo.
- [ ] Las suites existentes de proveedores y entrega siguen pasando.

## Frontier
Ready. Skills-only inline. Sin decisiones humanas pendientes. Integración es un gate aparte.

## Step-by-Step Implementation Plan
1. Emitir y validar ticket, grafo y candidato con las funciones canónicas puras.
2. Conservar los dos recibos de reproducción en este equipo como evidencia causal.
3. Escribir en RED las pruebas de argv por fichero, ausencia de metacaracteres, ubicación y
   borrado del temporal, camino no-Windows intacto, límite de longitud y error acotado.
4. Implementar la detección del envoltorio, el paso por fichero, el límite y el renderizado.
5. Ejecutar las suites de proveedores y entrega y el packlist; revisar, QA causal y auditoría.
6. Handoff con límites; entrega aparte, con autoridad y readback frescos, y perfil alojado
   sobre el head exacto.

## Testing Plan
Máximo 900 s por comando, cada intento registrado. Dobles y un envoltorio `.cmd` real en este
equipo; sin instancia de Azure DevOps, así que no se afirma nada sobre el servicio real.

## Out of Scope
GitHub, política de contenido del cuerpo, #35 y #36.
