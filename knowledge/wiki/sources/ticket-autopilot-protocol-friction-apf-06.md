---
type: source
title: "APF-06 — ¿Construye el runner el `leaf-result` y el modelo solo rellena?"
identity_key: ticket:autopilot-protocol-friction/APF-06
identity_strength: stable
source_path: docs/tickets/autopilot-protocol-friction/06-decide-whether-the-runner-drives-the-leaf.md
source_digest: sha256:1bd7a3d2f89b38441d9d28c870b5093181c9a8d38160912b3617c3599ddfc07b
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-09-22
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# APF-06 — ¿Construye el runner el `leaf-result` y el modelo solo rellena?

Compiled from `docs/tickets/autopilot-protocol-friction/06-decide-whether-the-runner-drives-the-leaf.md`. Identity is `ticket:autopilot-protocol-friction/APF-06`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-22** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-autopilot-protocol-friction]]
- Blocked by: [[sources/ticket-autopilot-protocol-friction-apf-01]] — `ticket:autopilot-protocol-friction/APF-01`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-autopilot-protocol-friction-apf-06.md","payload_bytes":1930,"payload_sha256":"1bd7a3d2f89b38441d9d28c870b5093181c9a8d38160912b3617c3599ddfc07b"}],"payload_bytes":1930,"payload_sha256":"1bd7a3d2f89b38441d9d28c870b5093181c9a8d38160912b3617c3599ddfc07b","schema":1,"source_digest":"sha256:1bd7a3d2f89b38441d9d28c870b5093181c9a8d38160912b3617c3599ddfc07b","source_identity":"ticket:autopilot-protocol-friction/APF-06","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1930,"payload_sha256":"1bd7a3d2f89b38441d9d28c870b5093181c9a8d38160912b3617c3599ddfc07b","schema":1,"source_digest":"sha256:1bd7a3d2f89b38441d9d28c870b5093181c9a8d38160912b3617c3599ddfc07b","source_identity":"ticket:autopilot-protocol-friction/APF-06"} -->
```markdown
---
ticket_schema: 1
ticket_id: "APF-06"
execution_mode: HITL
blocked_by:
  - "APF-01"
---

# APF-06 — ¿Construye el runner el `leaf-result` y el modelo solo rellena?

## Artifact Graph
- Artifact ID: `ticket:autopilot-protocol-friction:06`
- Role: `ticket`
- Parent: [autopilot-protocol-friction-wayfinder.md](../../specs/autopilot-protocol-friction-wayfinder.md)

## Parent Spec
[autopilot-protocol-friction-wayfinder.md](../../specs/autopilot-protocol-friction-wayfinder.md)

## What to Build
Decisión de arquitectura. Hoy el modelo construye el evento entero y el runner lo valida; el
prototipo APF-01 prueba el punto medio, una plantilla. La alternativa fuerte es invertir la dirección:
el runner abre la etapa, genera el esqueleto exacto con CandidateRef y fases, y el modelo solo
devuelve hallazgos y evidencia. Cambia el contrato `leaf-result`, la skill y quién posee la forma del
evento. Requiere [grilling](../../../grilling/SKILL.md) y confirmación explícita con los datos del
prototipo delante.

## Acceptance Criteria
- [ ] La decisión está tomada con los números de APF-01 a la vista: lecturas, coste, tiempo.
- [ ] Están escritos los trade-offs: qué pierde el modelo en flexibilidad, qué gana el runner en control.
- [ ] Si se invierte la dirección, el cambio de contrato queda especificado en `to-spec` antes de ningún ticket de implementación.

## Frontier
Bloqueado por APF-01. Decisión humana; ningún agente la toma por inferencia.

## Step-by-Step Implementation Plan
1. Presentar los resultados del prototipo.
2. Grilling sobre la inversión del contrato.
3. Registrar la decisión y, si procede, la spec del nuevo contrato.

## Testing Plan
- La decisión registrada con fecha, alcance y los números que la sostienen.

## Out of Scope
- Implementar nada: es una decisión.
- Tomarla por inferencia o sin los números de APF-01.
- Extenderla a otros contratos (`stage`, gates, autoridad).

```
