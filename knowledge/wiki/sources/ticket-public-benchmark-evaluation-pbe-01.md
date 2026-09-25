---
type: source
title: "PBE-01 — Importe autorizado y decisión sobre el demonio de Docker"
identity_key: ticket:public-benchmark-evaluation/PBE-01
identity_strength: stable
source_path: docs/tickets/public-benchmark-evaluation/01-authorize-budget-and-runtime.md
source_digest: sha256:a85e55f1c9c6770c1590a658c6d45b1b4f551367e2030351ca2b3a1ba0162b40
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-09-22
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# PBE-01 — Importe autorizado y decisión sobre el demonio de Docker

Compiled from `docs/tickets/public-benchmark-evaluation/01-authorize-budget-and-runtime.md`. Identity is `ticket:public-benchmark-evaluation/PBE-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-22** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-public-benchmark-evaluation]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[],"status":"not-identified"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[],"status":"not-identified"}},"parts":[{"index":0,"path":"wiki/sources/ticket-public-benchmark-evaluation-pbe-01.md","payload_bytes":1586,"payload_sha256":"a85e55f1c9c6770c1590a658c6d45b1b4f551367e2030351ca2b3a1ba0162b40"}],"payload_bytes":1586,"payload_sha256":"a85e55f1c9c6770c1590a658c6d45b1b4f551367e2030351ca2b3a1ba0162b40","schema":1,"source_digest":"sha256:a85e55f1c9c6770c1590a658c6d45b1b4f551367e2030351ca2b3a1ba0162b40","source_identity":"ticket:public-benchmark-evaluation/PBE-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | no matching section identified in the source; complete source retained |
| frontier | 5: Frontier |
| exclusions | no matching section identified in the source; complete source retained |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1586,"payload_sha256":"a85e55f1c9c6770c1590a658c6d45b1b4f551367e2030351ca2b3a1ba0162b40","schema":1,"source_digest":"sha256:a85e55f1c9c6770c1590a658c6d45b1b4f551367e2030351ca2b3a1ba0162b40","source_identity":"ticket:public-benchmark-evaluation/PBE-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "PBE-01"
execution_mode: HITL
blocked_by: []
---

# PBE-01 — Importe autorizado y decisión sobre el demonio de Docker

## Artifact Graph
- Artifact ID: `ticket:public-benchmark-evaluation:01`
- Role: `ticket`
- Parent: [public-benchmark-evaluation-wayfinder.md](../../specs/public-benchmark-evaluation-wayfinder.md)

## Parent Spec
[public-benchmark-evaluation-wayfinder.md](../../specs/public-benchmark-evaluation-wayfinder.md)

## What to Build
Nada de código. Dos decisiones del usuario, confirmadas explícitamente, antes de que exista
gasto: el **importe máximo** autorizado para la medida, y si se levanta el **demonio de Docker**
en esta máquina o se usa un sandbox remoto de pago.

Requiere [grilling](../../../grilling/SKILL.md) sobre la decisión antes de confirmarla: la
proyección de coste viene de una sola tarea sembrada y puede quedarse corta.

## Acceptance Criteria
- [ ] Hay un importe máximo escrito, no un «adelante».
- [ ] Está decidido si se levanta Docker en local o se paga un sandbox remoto.
- [ ] Está decidido qué brazos se miden: los tres o solo dos.
- [ ] La decisión queda registrada donde el siguiente agente la lea.

## Frontier
Bloqueante. Es una decisión humana; ningún agente la toma por inferencia.

## Step-by-Step Implementation Plan
1. Presentar la proyección de coste con su origen y su incertidumbre.
2. Grilling sobre los supuestos: tareas más largas, reintentos, tareas con GPU.
3. Registrar importe, runtime y brazos elegidos.

## Verification
- La decisión registrada, con fecha y alcance.

```
