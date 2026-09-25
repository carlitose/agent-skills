---
type: source
title: "APF-05 — El harness cuenta las lecturas de código del runner como métrica"
identity_key: ticket:autopilot-protocol-friction/APF-05
identity_strength: stable
source_path: docs/tickets/autopilot-protocol-friction/05-measure-runner-source-reads-as-regression.md
source_digest: sha256:017e1e5432d2bf19eae1ad159f2d28779720e9736e519949ab81ff4674aadf82
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-09-22
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# APF-05 — El harness cuenta las lecturas de código del runner como métrica

Compiled from `docs/tickets/autopilot-protocol-friction/05-measure-runner-source-reads-as-regression.md`. Identity is `ticket:autopilot-protocol-friction/APF-05`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-22** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-autopilot-protocol-friction]]
- Blocked by: [[sources/ticket-autopilot-protocol-friction-apf-01]] — `ticket:autopilot-protocol-friction/APF-01`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-autopilot-protocol-friction-apf-05.md","payload_bytes":1725,"payload_sha256":"017e1e5432d2bf19eae1ad159f2d28779720e9736e519949ab81ff4674aadf82"}],"payload_bytes":1725,"payload_sha256":"017e1e5432d2bf19eae1ad159f2d28779720e9736e519949ab81ff4674aadf82","schema":1,"source_digest":"sha256:017e1e5432d2bf19eae1ad159f2d28779720e9736e519949ab81ff4674aadf82","source_identity":"ticket:autopilot-protocol-friction/APF-05","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1725,"payload_sha256":"017e1e5432d2bf19eae1ad159f2d28779720e9736e519949ab81ff4674aadf82","schema":1,"source_digest":"sha256:017e1e5432d2bf19eae1ad159f2d28779720e9736e519949ab81ff4674aadf82","source_identity":"ticket:autopilot-protocol-friction/APF-05"} -->
```markdown
---
ticket_schema: 1
ticket_id: "APF-05"
execution_mode: AFK
blocked_by:
  - "APF-01"
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

```
