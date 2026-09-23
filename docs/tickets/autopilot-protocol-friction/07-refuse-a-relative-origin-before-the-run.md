---
ticket_schema: 1
ticket_id: "APF-07"
execution_mode: AFK
blocked_by:
  - "APF-03"
---

# APF-07 — Un origin con path relativo se rechaza en `run`, no en el gate de entrega

## Artifact Graph
- Artifact ID: `ticket:autopilot-protocol-friction:07`
- Role: `ticket`
- Parent: [autopilot-protocol-friction-wayfinder.md](../../specs/autopilot-protocol-friction-wayfinder.md)

## Parent Spec
[autopilot-protocol-friction-wayfinder.md](../../specs/autopilot-protocol-friction-wayfinder.md)

## What to Build
En q3 el modelo siguió el consejo de APF-03 —`git remote add origin <url>`— con `../project-origin.git`.
`run` hizo `ls-remote` desde la raíz del repo y pasó (turno 38); el gate `finalization-environment` lo
rehizo desde el worktree aislado, donde `../project-origin.git` no existe, y falló (turno 157): Git
resuelve un path relativo desde la raíz del worktree actual. Veintidós turnos hasta el `set-url`
correcto (158). El preflight de `run` debe rechazar un origin relativo con el `set-url` absoluto ya
escrito, y el consejo del caso "sin origin" debe pedir path absoluto o URL.

## Acceptance Criteria
- [ ] `run` con `remote.origin.url` relativo se rechaza antes de tocar Git; `detail.next_step` es el `git remote set-url origin <path absoluto>` exacto.
- [ ] Aplicado ese `next_step` literalmente, el mismo `run` arranca.
- [ ] El consejo de "repository has no origin" pide un path absoluto o una URL.
- [ ] Un test reproduce la causa: `ls-remote` desde un worktree enlazado falla con el origin relativo y pasa con el absoluto.

## Frontier
Cierra QB-apf03-2. Bloqueado por APF-03, ya entregado (#330).

## Step-by-Step Implementation Plan
1. `git_ops.relative_origin_path(repo)`: `None` para URL, path absoluto o `host:path`; el path resuelto para un relativo.
2. En `_run`, tras `observe_target`: rechazar con `GitError` + `rejection_detail` sobre `remote.origin.url`.
3. Test en `test_run_preflight.py`: rechazo, remedio aplicado, causa reproducida.

## Testing Plan
- Test que crea el repo con origin relativo, invoca `run`, aplica el `next_step` devuelto y vuelve a invocar `run`.
- Test del worktree enlazado: `ls-remote` falla con el relativo y pasa tras `set-url`.

## Out of Scope
- Corregir el remote del usuario por él: el runner no muta la configuración del repo.
- Rutas con `~`: Git no las expande en `remote.<name>.url`; no se clasifican aquí.
