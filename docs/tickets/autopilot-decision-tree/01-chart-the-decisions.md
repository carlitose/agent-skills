---
ticket_schema: 1
ticket_id: "ADT-01"
execution_mode: AFK
blocked_by: []
---

# ADT-01 — Dibujar el árbol decisional de Autopilot

## Artifact Graph
- Artifact ID: `ticket:autopilot-decision-tree:01`
- Role: `ticket`
- Parent: [autopilot-decision-tree.md](../../specs/autopilot-decision-tree.md)

## Parent Spec
[autopilot-decision-tree.md](../../specs/autopilot-decision-tree.md)

## What to Build
El flujo completo de Autopilot en diagramas, con cada elección marcada como programática, LLM,
humana o híbrida, y cada nodo anclado a código en un SHA exacto. Los anclajes se comprueban por
máquina: fichero y línea deben contener el símbolo citado en ese SHA.

## Acceptance Criteria
- [x] Cinco diagramas: lazo del scheduler, ciclo del ticket, entrega y merge, después de
      integrar, controles humanos.
- [x] Los cuatro tipos de decisión con color propio y leyenda.
- [x] Tabla de anclajes `fichero:línea símbolo` al SHA exacto.
- [x] Un comprobador que resuelve cada anclaje contra ese SHA y falla si el símbolo no está.
- [x] Las decisiones sin test que las nombre se declaran como tales, sin inventar cobertura.
- [x] Se declara que no hay trazas vivas porque el runner está suspendido.

## Frontier
Ready. Es documentación derivada de código ya integrado; no requiere ejecutar el runner.

## Step-by-Step Implementation Plan
1. Extraer del SHA los símbolos que deciden el rumbo del flujo.
2. Clasificarlos por quién decide.
3. Dibujar los diagramas y la tabla de anclajes.
4. Comprobar los anclajes por máquina y contar la cobertura real de tests.

## Verification
- `adt40-check-anchors-q1.json`: cada anclaje resuelto contra el SHA.
- `adt40-check-coverage-q1.json`: cobertura de tests por símbolo, incluidas las ausencias.
