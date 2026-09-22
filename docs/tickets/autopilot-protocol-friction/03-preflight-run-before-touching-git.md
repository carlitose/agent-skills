---
ticket_schema: 1
ticket_id: "APF-03"
execution_mode: AFK
blocked_by: []
---

# APF-03 — `run` comprueba remoto y proveedor antes de tocar Git

## Artifact Graph
- Artifact ID: `ticket:autopilot-protocol-friction:03`
- Role: `ticket`
- Parent: [autopilot-protocol-friction-wayfinder.md](../../specs/autopilot-protocol-friction-wayfinder.md)

## Parent Spec
[autopilot-protocol-friction-wayfinder.md](../../specs/autopilot-protocol-friction-wayfinder.md)

## What to Build
El run q2 falló tres veces al arrancar: `target-fetch-failed: cannot refresh configured target` (T45,
T49) y «remote provider cannot be detected; pass an explicit supported override» (T51), sobre un
repositorio sembrado sin remoto. El runner descubre tras crear estado lo que podía saber antes. Un
preflight en `run` que, antes de crear worktree o ledger, compruebe remoto, proveedor y target, y
falle con un mensaje que nombre qué falta y qué opción lo resuelve, o que declare explícitamente el
modo local si el repositorio no tiene remoto.

## Acceptance Criteria
- [ ] Sobre un repo sin remoto, `run` falla antes de crear worktree o ledger, o entra en modo local declarado; se decide y se documenta cuál.
- [ ] El mensaje nombra la comprobación fallida y la opción (`--provider`, `--provider-mode simulated`, remoto) que la resuelve.
- [ ] T45, T49 y T51 reproducidos como tests.
- [ ] Ningún estado queda en disco tras un preflight fallido.

## Frontier
Ready.

## Step-by-Step Implementation Plan
1. Reproducir los tres fallos con un repo sembrado sin remoto.
2. Mover las comprobaciones de remoto/proveedor/target antes de cualquier mutación.
3. Un test por fallo; un test que afirme que no queda estado.

## Testing Plan
- Tests de los tres fallos y del no-estado.
- El run sembrado del benchmark arranca al primer intento o falla en un solo mensaje claro.

## Out of Scope
- Implementar un modo local completo si se decide rechazar los repos sin remoto.
- Cambiar la detección de proveedor en repos con remoto válido.
- Los errores de `resume`: son APF-02.
