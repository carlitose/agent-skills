---
type: source
title: "PBE-03 — Piloto de tres tareas antes de gastar el resto"
identity_key: ticket:public-benchmark-evaluation/PBE-03
identity_strength: stable
source_path: docs/tickets/public-benchmark-evaluation/03-run-a-three-task-pilot.md
source_digest: sha256:d19d7967295f72219cdd7e15cfc394b57bce2cf02a2c1fd7cd4264efc6e3d7e7
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-09-22
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# PBE-03 — Piloto de tres tareas antes de gastar el resto

Compiled from `docs/tickets/public-benchmark-evaluation/03-run-a-three-task-pilot.md`. Identity is `ticket:public-benchmark-evaluation/PBE-03`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-22** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-public-benchmark-evaluation]]
- Blocked by: [[sources/ticket-public-benchmark-evaluation-pbe-01]] — `ticket:public-benchmark-evaluation/PBE-01`
- Blocked by: [[sources/ticket-public-benchmark-evaluation-pbe-02]] — `ticket:public-benchmark-evaluation/PBE-02`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[],"status":"not-identified"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[],"status":"not-identified"}},"parts":[{"index":0,"path":"wiki/sources/ticket-public-benchmark-evaluation-pbe-03.md","payload_bytes":1602,"payload_sha256":"d19d7967295f72219cdd7e15cfc394b57bce2cf02a2c1fd7cd4264efc6e3d7e7"}],"payload_bytes":1602,"payload_sha256":"d19d7967295f72219cdd7e15cfc394b57bce2cf02a2c1fd7cd4264efc6e3d7e7","schema":1,"source_digest":"sha256:d19d7967295f72219cdd7e15cfc394b57bce2cf02a2c1fd7cd4264efc6e3d7e7","source_identity":"ticket:public-benchmark-evaluation/PBE-03","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | no matching section identified in the source; complete source retained |
| frontier | 5: Frontier |
| exclusions | no matching section identified in the source; complete source retained |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1602,"payload_sha256":"d19d7967295f72219cdd7e15cfc394b57bce2cf02a2c1fd7cd4264efc6e3d7e7","schema":1,"source_digest":"sha256:d19d7967295f72219cdd7e15cfc394b57bce2cf02a2c1fd7cd4264efc6e3d7e7","source_identity":"ticket:public-benchmark-evaluation/PBE-03"} -->
```markdown
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

```
