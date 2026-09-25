---
type: source
title: "APF-02 — Cada error de `resume` nombra el campo, lo recibido y lo esperado"
identity_key: ticket:autopilot-protocol-friction/APF-02
identity_strength: stable
source_path: docs/tickets/autopilot-protocol-friction/02-name-the-fix-in-every-resume-error.md
source_digest: sha256:d22c9993a5f8aa284c75361e97eb674c1167b023313144683e78a934af6a69a4
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-09-22
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# APF-02 — Cada error de `resume` nombra el campo, lo recibido y lo esperado

Compiled from `docs/tickets/autopilot-protocol-friction/02-name-the-fix-in-every-resume-error.md`. Identity is `ticket:autopilot-protocol-friction/APF-02`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-22** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-autopilot-protocol-friction]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-autopilot-protocol-friction-apf-02.md","payload_bytes":1856,"payload_sha256":"d22c9993a5f8aa284c75361e97eb674c1167b023313144683e78a934af6a69a4"}],"payload_bytes":1856,"payload_sha256":"d22c9993a5f8aa284c75361e97eb674c1167b023313144683e78a934af6a69a4","schema":1,"source_digest":"sha256:d22c9993a5f8aa284c75361e97eb674c1167b023313144683e78a934af6a69a4","source_identity":"ticket:autopilot-protocol-friction/APF-02","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1856,"payload_sha256":"d22c9993a5f8aa284c75361e97eb674c1167b023313144683e78a934af6a69a4","schema":1,"source_digest":"sha256:d22c9993a5f8aa284c75361e97eb674c1167b023313144683e78a934af6a69a4","source_identity":"ticket:autopilot-protocol-friction/APF-02"} -->
```markdown
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

```
