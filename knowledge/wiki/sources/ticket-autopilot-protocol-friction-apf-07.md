---
type: source
title: "APF-07 — Un origin con path relativo se rechaza en `run`, no en el gate de entrega"
identity_key: ticket:autopilot-protocol-friction/APF-07
identity_strength: stable
source_path: docs/tickets/autopilot-protocol-friction/07-refuse-a-relative-origin-before-the-run.md
source_digest: sha256:b9e5e23bf313a7b0ab000c6a946e55e342d8baddfe33a4a12eb4443272577d25
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-09-23
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# APF-07 — Un origin con path relativo se rechaza en `run`, no en el gate de entrega

Compiled from `docs/tickets/autopilot-protocol-friction/07-refuse-a-relative-origin-before-the-run.md`. Identity is `ticket:autopilot-protocol-friction/APF-07`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-23** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-autopilot-protocol-friction]]
- Blocked by: [[sources/ticket-autopilot-protocol-friction-apf-03]] — `ticket:autopilot-protocol-friction/APF-03`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-autopilot-protocol-friction-apf-07.md","payload_bytes":2384,"payload_sha256":"b9e5e23bf313a7b0ab000c6a946e55e342d8baddfe33a4a12eb4443272577d25"}],"payload_bytes":2384,"payload_sha256":"b9e5e23bf313a7b0ab000c6a946e55e342d8baddfe33a4a12eb4443272577d25","schema":1,"source_digest":"sha256:b9e5e23bf313a7b0ab000c6a946e55e342d8baddfe33a4a12eb4443272577d25","source_identity":"ticket:autopilot-protocol-friction/APF-07","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2384,"payload_sha256":"b9e5e23bf313a7b0ab000c6a946e55e342d8baddfe33a4a12eb4443272577d25","schema":1,"source_digest":"sha256:b9e5e23bf313a7b0ab000c6a946e55e342d8baddfe33a4a12eb4443272577d25","source_identity":"ticket:autopilot-protocol-friction/APF-07"} -->
```markdown
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

```
