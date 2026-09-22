---
ticket_schema: 1
ticket_id: "APF-04"
execution_mode: AFK
blocked_by: []
---

# APF-04 — Los ejemplos de la skill se ejecutan en un test

## Artifact Graph
- Artifact ID: `ticket:autopilot-protocol-friction:04`
- Role: `ticket`
- Parent: [autopilot-protocol-friction-wayfinder.md](../../specs/autopilot-protocol-friction-wayfinder.md)

## Parent Spec
[autopilot-protocol-friction-wayfinder.md](../../specs/autopilot-protocol-friction-wayfinder.md)

## What to Build
Dos fallos del run q2 vienen de la propia documentación: `resume --events leaf-result` leído como
fichero produjo `[Errno 2] No such file or directory: 'leaf-result'` (T63), y `python3` en Windows
resolvió al alias de la Microsoft Store: «Python was not found» (T137). Cada ejemplo de comando en
`ticket-autopilot/SKILL.md` y sus referencias debe extraerse y ejecutarse en un test; el intérprete
se nombra de forma que resuelva en Windows, macOS y Linux.

## Acceptance Criteria
- [ ] Un test extrae cada bloque de comando de la skill y lo ejecuta contra un repo de prueba.
- [ ] El ejemplo de `resume --events` muestra la forma real del argumento.
- [ ] El intérprete de los ejemplos resuelve en Windows sin el alias de la Store.
- [ ] T63 y T137 no se reproducen.

## Frontier
Ready.

## Step-by-Step Implementation Plan
1. Inventariar los bloques de comando de la skill y sus referencias.
2. Corregir el ejemplo de `--events` y el intérprete.
3. Test que los ejecuta.

## Testing Plan
- El test de ejemplos en verde en los tres sistemas del CI.

## Out of Scope
- Reescribir la skill o cambiar el comportamiento del CLI: solo los ejemplos y el intérprete que nombran.
- Skills distintas de `ticket-autopilot` y sus referencias.
