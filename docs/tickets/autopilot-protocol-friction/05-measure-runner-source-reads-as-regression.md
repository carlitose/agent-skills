---
ticket_schema: 1
ticket_id: "APF-05"
execution_mode: AFK
blocked_by: 
  - APF-01
---

# APF-05 — El harness cuenta las lecturas de código del runner como métrica

## Artifact Graph
- Artifact ID: `ticket:autopilot-protocol-friction:05`
- Role: `ticket`
- Parent: [autopilot-protocol-friction-wayfinder.md](../../specs/autopilot-protocol-friction-wayfinder.md)

## Parent Spec
[autopilot-protocol-friction-wayfinder.md](../../specs/autopilot-protocol-friction-wayfinder.md)

## What to Build
El diagnóstico se apoya en una medida —lecturas de código fuente del runner por run, 22 en q1 y 41
en q2— que hoy se calcula a mano. El harness `bench38_harness.py` debe calcularla al recolectar cada
brazo, junto a `grep` sobre el runner, `resume` fallidos y turnos con más de una llamada, y
publicarla en el registro del brazo. Es la métrica que dice si el destino del mapa se alcanzó.

## Acceptance Criteria
- [ ] `collect` publica: lecturas de código del runner, KB leídos de él, `grep` sobre él, `resume` fallidos, turnos multi-llamada.
- [ ] Recalculado sobre q1 y q2 da 22/41 lecturas y 0 turnos multi-llamada en q2.
- [ ] `compare` muestra la métrica por brazo.

## Frontier
Bloqueado por APF-01: la métrica se estrena midiendo su prototipo.

## Step-by-Step Implementation Plan
1. Extraer el perfilado de `adt58-q2-timeline` a una función del harness.
2. Publicarlo en el registro de cada brazo.
3. Recalcular q1 y q2.

## Testing Plan
- Los números de q1 y q2 coinciden con los del mapa.

## Out of Scope
- Relanzar q1 o q2: se recalculan de las sesiones guardadas.
- Cambiar el brazo, el modelo o el prompt del benchmark.
- Juzgar el resultado: la métrica se publica, la lectura la hace el mapa.
