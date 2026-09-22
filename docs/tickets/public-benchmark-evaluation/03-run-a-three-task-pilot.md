---
ticket_schema: 1
ticket_id: "PBE-03"
execution_mode: AFK
blocked_by:
  - PBE-01
  - PBE-02
---

# PBE-03 — Piloto de tres tareas antes de gastar el resto

## Artifact Graph
- Artifact ID: `ticket:public-benchmark-evaluation:03`
- Role: `ticket`
- Parent: [public-benchmark-evaluation-wayfinder.md](../../specs/public-benchmark-evaluation-wayfinder.md)

## Parent Spec
[public-benchmark-evaluation-wayfinder.md](../../specs/public-benchmark-evaluation-wayfinder.md)

## What to Build
Tres tareas de Terminal-Bench 4.0, un intento por brazo, con el sandbox decidido en PBE-01. El
piloto existe para contrastar la proyección de coste contra la realidad **antes** de comprometer
el presupuesto entero, y para contar cuántas tareas del conjunto exigen GPU.

## Acceptance Criteria
- [ ] Coste y tiempo reales por tarea y por brazo, medidos, no estimados.
- [ ] Comparación explícita contra la proyección: 0,112 / 0,436 / 3,977 $ por tarea.
- [ ] Número de tareas del conjunto completo que exigen GPU, contado.
- [ ] Si el coste real supera la proyección, se para y se vuelve a PBE-01.

## Frontier
Bloqueado por PBE-01 (importe y runtime) y PBE-02 (adaptador).

## Step-by-Step Implementation Plan
1. Elegir tres tareas sin GPU y fijarlas por nombre.
2. Ejecutar un intento por brazo con el mismo modelo y nivel de razonamiento.
3. Medir coste, tiempo y resultado; contar las tareas con GPU del conjunto.
4. Comparar con la proyección y decidir si se sigue.

## Verification
- Registro por intento con coste, tokens, tiempo y resultado.
- Recuento de tareas con GPU, con el método de conteo.
