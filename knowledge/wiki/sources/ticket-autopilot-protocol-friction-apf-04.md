---
type: source
title: "APF-04 — Los ejemplos de la skill se ejecutan en un test"
identity_key: ticket:autopilot-protocol-friction/APF-04
identity_strength: stable
source_path: docs/tickets/autopilot-protocol-friction/04-make-the-skill-examples-runnable.md
source_digest: sha256:a5676db306c4ccc4b9c1b3fe3f288f5469e31643bfcbf1aac152e16d58e7aff0
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-09-22
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# APF-04 — Los ejemplos de la skill se ejecutan en un test

Compiled from `docs/tickets/autopilot-protocol-friction/04-make-the-skill-examples-runnable.md`. Identity is `ticket:autopilot-protocol-friction/APF-04`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-22** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-autopilot-protocol-friction]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-autopilot-protocol-friction-apf-04.md","payload_bytes":1711,"payload_sha256":"a5676db306c4ccc4b9c1b3fe3f288f5469e31643bfcbf1aac152e16d58e7aff0"}],"payload_bytes":1711,"payload_sha256":"a5676db306c4ccc4b9c1b3fe3f288f5469e31643bfcbf1aac152e16d58e7aff0","schema":1,"source_digest":"sha256:a5676db306c4ccc4b9c1b3fe3f288f5469e31643bfcbf1aac152e16d58e7aff0","source_identity":"ticket:autopilot-protocol-friction/APF-04","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1711,"payload_sha256":"a5676db306c4ccc4b9c1b3fe3f288f5469e31643bfcbf1aac152e16d58e7aff0","schema":1,"source_digest":"sha256:a5676db306c4ccc4b9c1b3fe3f288f5469e31643bfcbf1aac152e16d58e7aff0","source_identity":"ticket:autopilot-protocol-friction/APF-04"} -->
```markdown
---
ticket_schema: 1
ticket_id: "APF-04"
execution_mode: AFK
blocked_by: []
---

# APF-04 — Los ejemplos de la skill se ejecutan en un test

## Artifact Graph
- Artifact ID: `ticket:autopilot-protocol-friction:04`
- Role: `ticket`
- Parent: [autopilot-protocol-friction-wayfinder.md](../../specs/autopilot-protocol-friction-wayfinder.md)

## Parent Spec
[autopilot-protocol-friction-wayfinder.md](../../specs/autopilot-protocol-friction-wayfinder.md)

## What to Build
Dos fallos del run q2 vienen de la propia documentación: `resume --events leaf-result` leído como
fichero produjo `[Errno 2] No such file or directory: 'leaf-result'` (T63), y `python3` en Windows
resolvió al alias de la Microsoft Store: «Python was not found» (T137). Cada ejemplo de comando en
`ticket-autopilot/SKILL.md` y sus referencias debe extraerse y ejecutarse en un test; el intérprete
se nombra de forma que resuelva en Windows, macOS y Linux.

## Acceptance Criteria
- [ ] Un test extrae cada bloque de comando de la skill y lo ejecuta contra un repo de prueba.
- [ ] El ejemplo de `resume --events` muestra la forma real del argumento.
- [ ] El intérprete de los ejemplos resuelve en Windows sin el alias de la Store.
- [ ] T63 y T137 no se reproducen.

## Frontier
Ready.

## Step-by-Step Implementation Plan
1. Inventariar los bloques de comando de la skill y sus referencias.
2. Corregir el ejemplo de `--events` y el intérprete.
3. Test que los ejecuta.

## Testing Plan
- El test de ejemplos en verde en los tres sistemas del CI.

## Out of Scope
- Reescribir la skill o cambiar el comportamiento del CLI: solo los ejemplos y el intérprete que nombran.
- Skills distintas de `ticket-autopilot` y sus referencias.

```
