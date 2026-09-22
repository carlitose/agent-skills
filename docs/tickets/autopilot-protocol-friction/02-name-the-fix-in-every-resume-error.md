---
ticket_schema: 1
ticket_id: "APF-02"
execution_mode: AFK
blocked_by: []
---

# APF-02 — Cada error de `resume` nombra el campo, lo recibido y lo esperado

## Artifact Graph
- Artifact ID: `ticket:autopilot-protocol-friction:02`
- Role: `ticket`
- Parent: [autopilot-protocol-friction-wayfinder.md](../../specs/autopilot-protocol-friction-wayfinder.md)

## Parent Spec
[autopilot-protocol-friction-wayfinder.md](../../specs/autopilot-protocol-friction-wayfinder.md)

## What to Build
Los tres rechazos del run q2 —«bounded leaf results require an active leaf stage» (T120), «another
ticket is already active» (T128), «quality leaf result requires structured quality evidence» (T131)—
nombran el invariante y callan la salida. Cada `TransitionError` y `LeafProtocolError` que `resume`
devuelve debe incluir: qué campo o estado falló, qué se recibió, qué se esperaba, y qué comando o
evento lo corrige. Sin relajar ningún invariante.

## Acceptance Criteria
- [ ] Los tres errores de T120, T128 y T131 se reproducen en tests con el ledger y el evento que los causaron.
- [ ] Cada uno devuelve campo, recibido, esperado y siguiente paso en el JSON de respuesta.
- [ ] Ningún invariante del kernel cambia; los tests existentes siguen verdes.
- [ ] La respuesta no incluye credenciales ni payloads privados.

## Frontier
Ready.

## Step-by-Step Implementation Plan
1. Reproducir cada error con un ledger mínimo.
2. Extender el mensaje en el punto que lo lanza, no en el CLI.
3. Un test por error que afirme los cuatro elementos.

## Testing Plan
- `ticket-autopilot/tests`: tres tests nuevos, uno por error.
- La suite completa del runner sigue verde.

## Out of Scope
- Relajar o reordenar invariantes del kernel.
- Cambiar códigos de salida o quitar campos del JSON de respuesta; solo se añaden.
- Los mensajes de `run`: son APF-03.
