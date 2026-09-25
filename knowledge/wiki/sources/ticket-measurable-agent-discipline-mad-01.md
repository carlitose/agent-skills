---
type: source
title: "MAD-01 — Las tres reglas, con su número, donde el instrador ya mira"
identity_key: ticket:measurable-agent-discipline/MAD-01
identity_strength: stable
source_path: docs/tickets/measurable-agent-discipline/01-write-the-three-rules.md
source_digest: sha256:32b739335c811ad1aef57458d4b743a2057ae0ffa1ed4e681c9b39a8e81fb025
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-09-22
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# MAD-01 — Las tres reglas, con su número, donde el instrador ya mira

Compiled from `docs/tickets/measurable-agent-discipline/01-write-the-three-rules.md`. Identity is `ticket:measurable-agent-discipline/MAD-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-22** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/spec-measurable-agent-discipline]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[],"status":"not-identified"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[],"status":"not-identified"}},"parts":[{"index":0,"path":"wiki/sources/ticket-measurable-agent-discipline-mad-01.md","payload_bytes":2022,"payload_sha256":"32b739335c811ad1aef57458d4b743a2057ae0ffa1ed4e681c9b39a8e81fb025"}],"payload_bytes":2022,"payload_sha256":"32b739335c811ad1aef57458d4b743a2057ae0ffa1ed4e681c9b39a8e81fb025","schema":1,"source_digest":"sha256:32b739335c811ad1aef57458d4b743a2057ae0ffa1ed4e681c9b39a8e81fb025","source_identity":"ticket:measurable-agent-discipline/MAD-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | no matching section identified in the source; complete source retained |
| frontier | 5: Frontier |
| exclusions | no matching section identified in the source; complete source retained |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2022,"payload_sha256":"32b739335c811ad1aef57458d4b743a2057ae0ffa1ed4e681c9b39a8e81fb025","schema":1,"source_digest":"sha256:32b739335c811ad1aef57458d4b743a2057ae0ffa1ed4e681c9b39a8e81fb025","source_identity":"ticket:measurable-agent-discipline/MAD-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "MAD-01"
execution_mode: AFK
blocked_by: []
---

# MAD-01 — Las tres reglas, con su número, donde el instrador ya mira

## Artifact Graph
- Artifact ID: `ticket:measurable-agent-discipline:01`
- Role: `ticket`
- Parent: [measurable-agent-discipline.md](../../specs/measurable-agent-discipline.md)

## Parent Spec
[measurable-agent-discipline.md](../../specs/measurable-agent-discipline.md)

## What to Build
Tres filas nuevas en la tabla de `ask-skills/OPERATING-DEFAULTS.md` —una sesión por ticket,
agrupar las llamadas independientes, comprobar la plataforma antes de invocar un shell— cada
una con la medida que la justifica, y una línea que diga que son defaults y no prohibiciones.
La misma sustancia en memoria persistente. La medición antes/después de esta sesión queda
registrada como evidencia con su método.

## Acceptance Criteria
- [ ] Las tres reglas están en `OPERATING-DEFAULTS.md` con su número.
- [ ] Cada regla dice cuándo no aplica.
- [ ] Una línea de tabla por regla: el fichero se lee muchas veces por sesión.
- [ ] La medición antes/después queda registrada con método y fecha.
- [ ] Se dice que no existe todavía una sesión nueva medida.
- [ ] La misma sustancia queda en memoria persistente.
- [ ] El grafo canónico de artefactos sigue válido.

## Frontier
Ready. Skills-only inline. Sin decisiones humanas pendientes.

## Step-by-Step Implementation Plan
1. Emitir y validar ticket, grafo y candidato con las funciones canónicas puras.
2. Medir la sesión partida por el instante de la crítica y guardar el registro.
3. Escribir las tres filas y la línea de excepciones.
4. Guardar la memoria persistente.
5. Entregar con evidencia: admisión, verificación, PR, integración y sincronización.

## Verification
- `sess55-rate-q1.json`: turnos, llamadas, agrupamiento y repeticiones por ventana.
- Auditoría del grafo canónico de artefactos sobre el candidato.
- Registro de verificación canónico con los recibos de cada ejecución.

```
