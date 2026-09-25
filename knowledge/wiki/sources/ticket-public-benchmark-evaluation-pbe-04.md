---
type: source
title: "PBE-04 — Los brazos completos y un informe que diga de qué depende el número"
identity_key: ticket:public-benchmark-evaluation/PBE-04
identity_strength: stable
source_path: docs/tickets/public-benchmark-evaluation/04-run-and-report-the-arms.md
source_digest: sha256:3689472ddb09ad1ac476c31034092051f6b15d1883a750473bd6afd03bb44c9a
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-09-22
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# PBE-04 — Los brazos completos y un informe que diga de qué depende el número

Compiled from `docs/tickets/public-benchmark-evaluation/04-run-and-report-the-arms.md`. Identity is `ticket:public-benchmark-evaluation/PBE-04`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-22** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-public-benchmark-evaluation]]
- Blocked by: [[sources/ticket-public-benchmark-evaluation-pbe-03]] — `ticket:public-benchmark-evaluation/PBE-03`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[],"status":"not-identified"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[],"status":"not-identified"}},"parts":[{"index":0,"path":"wiki/sources/ticket-public-benchmark-evaluation-pbe-04.md","payload_bytes":1780,"payload_sha256":"3689472ddb09ad1ac476c31034092051f6b15d1883a750473bd6afd03bb44c9a"}],"payload_bytes":1780,"payload_sha256":"3689472ddb09ad1ac476c31034092051f6b15d1883a750473bd6afd03bb44c9a","schema":1,"source_digest":"sha256:3689472ddb09ad1ac476c31034092051f6b15d1883a750473bd6afd03bb44c9a","source_identity":"ticket:public-benchmark-evaluation/PBE-04","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | no matching section identified in the source; complete source retained |
| frontier | 5: Frontier |
| exclusions | no matching section identified in the source; complete source retained |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1780,"payload_sha256":"3689472ddb09ad1ac476c31034092051f6b15d1883a750473bd6afd03bb44c9a","schema":1,"source_digest":"sha256:3689472ddb09ad1ac476c31034092051f6b15d1883a750473bd6afd03bb44c9a","source_identity":"ticket:public-benchmark-evaluation/PBE-04"} -->
```markdown
---
ticket_schema: 1
ticket_id: "PBE-04"
execution_mode: AFK
blocked_by:
  - PBE-03
---

# PBE-04 — Los brazos completos y un informe que diga de qué depende el número

## Artifact Graph
- Artifact ID: `ticket:public-benchmark-evaluation:04`
- Role: `ticket`
- Parent: [public-benchmark-evaluation-wayfinder.md](../../specs/public-benchmark-evaluation-wayfinder.md)

## Parent Spec
[public-benchmark-evaluation-wayfinder.md](../../specs/public-benchmark-evaluation-wayfinder.md)

## What to Build
El conjunto autorizado en PBE-01, con los brazos autorizados, y un informe con las mismas
magnitudes que publica el índice público: `pass@1` promediado sobre los intentos acordados,
coste de API por tarea y tiempo de reloj activo por tarea.

El informe debe decir, en su primera afirmación, que la cifra mide **modelo más andamiaje** y
que la comparación entre harnesses no está publicada todavía en el índice de referencia.

## Acceptance Criteria
- [ ] `pass@1` por brazo con el número de intentos declarado.
- [ ] Coste por tarea y tiempo activo por tarea, por brazo.
- [ ] Las tareas no ejecutadas —GPU u otras— se declaran como cobertura perdida, no se sustituyen.
- [ ] El informe dice que el número depende del andamiaje y que la comparación entre harnesses
      del índice sigue sin publicarse.
- [ ] Ningún cambio en Pi, skills o Autopilot para puntuar mejor.

## Frontier
Bloqueado por PBE-03.

## Step-by-Step Implementation Plan
1. Ejecutar el conjunto autorizado por brazo con intentos iguales.
2. Reducir a las tres magnitudes del índice.
3. Escribir el informe con la cobertura perdida y la dependencia del andamiaje.

## Verification
- Registros por intento y la reducción a las tres magnitudes.
- Lista de tareas no ejecutadas con su motivo.

```
