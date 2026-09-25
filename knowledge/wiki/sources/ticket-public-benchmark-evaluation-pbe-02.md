---
type: source
title: "PBE-02 — Un `BaseAgent` de Harbor que arranque Pi"
identity_key: ticket:public-benchmark-evaluation/PBE-02
identity_strength: stable
source_path: docs/tickets/public-benchmark-evaluation/02-write-the-harbor-adapter.md
source_digest: sha256:b6c30afcf96c3a537c501f927c0b8d779ed08963d385b88c9c44b1b646ef21e3
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-09-22
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# PBE-02 — Un `BaseAgent` de Harbor que arranque Pi

Compiled from `docs/tickets/public-benchmark-evaluation/02-write-the-harbor-adapter.md`. Identity is `ticket:public-benchmark-evaluation/PBE-02`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-22** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-public-benchmark-evaluation]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[],"status":"not-identified"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[],"status":"not-identified"}},"parts":[{"index":0,"path":"wiki/sources/ticket-public-benchmark-evaluation-pbe-02.md","payload_bytes":1967,"payload_sha256":"b6c30afcf96c3a537c501f927c0b8d779ed08963d385b88c9c44b1b646ef21e3"}],"payload_bytes":1967,"payload_sha256":"b6c30afcf96c3a537c501f927c0b8d779ed08963d385b88c9c44b1b646ef21e3","schema":1,"source_digest":"sha256:b6c30afcf96c3a537c501f927c0b8d779ed08963d385b88c9c44b1b646ef21e3","source_identity":"ticket:public-benchmark-evaluation/PBE-02","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | no matching section identified in the source; complete source retained |
| frontier | 5: Frontier |
| exclusions | no matching section identified in the source; complete source retained |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1967,"payload_sha256":"b6c30afcf96c3a537c501f927c0b8d779ed08963d385b88c9c44b1b646ef21e3","schema":1,"source_digest":"sha256:b6c30afcf96c3a537c501f927c0b8d779ed08963d385b88c9c44b1b646ef21e3","source_identity":"ticket:public-benchmark-evaluation/PBE-02"} -->
```markdown
---
ticket_schema: 1
ticket_id: "PBE-02"
execution_mode: AFK
blocked_by: []
---

# PBE-02 — Un `BaseAgent` de Harbor que arranque Pi

## Artifact Graph
- Artifact ID: `ticket:public-benchmark-evaluation:02`
- Role: `ticket`
- Parent: [public-benchmark-evaluation-wayfinder.md](../../specs/public-benchmark-evaluation-wayfinder.md)

## Parent Spec
[public-benchmark-evaluation-wayfinder.md](../../specs/public-benchmark-evaluation-wayfinder.md)

## What to Build
Un módulo Python con una clase que herede de `harbor.agents.base.BaseAgent` e implemente
`name()`, `version()`, `setup(environment)` y `run(instruction, environment, context)`. El bucle
de Pi vive en Harbor y actúa sobre la tarea a través de `environment.exec(...)`; no se instala
Pi dentro del contenedor. Se invoca como `-a modulo.ruta:Clase`.

Tres variantes del mismo adaptador, una por brazo: Pi desnudo, Pi con skills, Pi con Autopilot.
La diferencia entre brazos es el andamiaje, no el modelo ni el prompt de la tarea.

## Acceptance Criteria
- [ ] El adaptador carga por `módulo:Clase` sin registrarse en Harbor.
- [ ] Arranca contra la tarea `hello-world` y deja trayectoria legible.
- [ ] Los tres brazos comparten modelo, nivel de razonamiento y texto de la tarea.
- [ ] El coste y los tokens de cada intento salen del fichero de sesión del propio brazo.
- [ ] Si Pi no puede ejercer alguna herramienta dentro del sandbox, queda escrito cuál.

## Frontier
Ready: escribir el adaptador no cuesta dinero de API. Validarlo contra tareas reales depende de
PBE-01.

## Step-by-Step Implementation Plan
1. Leer la referencia de `BaseAgent` y el ejemplo `marker_agent.py`.
2. Escribir el adaptador y las tres variantes de brazo.
3. Probar contra `hello-world` con un sandbox local.
4. Registrar qué herramientas de Pi quedan degradadas dentro del sandbox, si alguna.

## Verification
- Trayectoria de `hello-world` por cada brazo.
- Lista explícita de capacidades degradadas, o su ausencia.

```
