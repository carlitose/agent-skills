---
type: source
title: "ADT-01 — Dibujar el árbol decisional de Autopilot"
identity_key: ticket:autopilot-decision-tree/ADT-01
identity_strength: stable
source_path: docs/tickets/autopilot-decision-tree/01-chart-the-decisions.md
source_digest: sha256:b8c87ccc60e77db13ba3e4f5c1ccbf23ffdd130f317670bfb48879ad687b087c
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-09-22
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# ADT-01 — Dibujar el árbol decisional de Autopilot

Compiled from `docs/tickets/autopilot-decision-tree/01-chart-the-decisions.md`. Identity is `ticket:autopilot-decision-tree/ADT-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-22** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-autopilot-decision-tree]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[],"status":"not-identified"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[],"status":"not-identified"}},"parts":[{"index":0,"path":"wiki/sources/ticket-autopilot-decision-tree-adt-01.md","payload_bytes":1761,"payload_sha256":"b8c87ccc60e77db13ba3e4f5c1ccbf23ffdd130f317670bfb48879ad687b087c"}],"payload_bytes":1761,"payload_sha256":"b8c87ccc60e77db13ba3e4f5c1ccbf23ffdd130f317670bfb48879ad687b087c","schema":1,"source_digest":"sha256:b8c87ccc60e77db13ba3e4f5c1ccbf23ffdd130f317670bfb48879ad687b087c","source_identity":"ticket:autopilot-decision-tree/ADT-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | no matching section identified in the source; complete source retained |
| frontier | 5: Frontier |
| exclusions | no matching section identified in the source; complete source retained |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1761,"payload_sha256":"b8c87ccc60e77db13ba3e4f5c1ccbf23ffdd130f317670bfb48879ad687b087c","schema":1,"source_digest":"sha256:b8c87ccc60e77db13ba3e4f5c1ccbf23ffdd130f317670bfb48879ad687b087c","source_identity":"ticket:autopilot-decision-tree/ADT-01"} -->
```markdown
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

```
