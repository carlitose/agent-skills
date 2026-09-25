---
type: source
title: "APF-03 — `run` comprueba remoto y proveedor antes de tocar Git"
identity_key: ticket:autopilot-protocol-friction/APF-03
identity_strength: stable
source_path: docs/tickets/autopilot-protocol-friction/03-preflight-run-before-touching-git.md
source_digest: sha256:d02b93444b4b52868fb360c67088e9cb78f5c74504c3cf86e4535581b859eec3
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-09-22
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# APF-03 — `run` comprueba remoto y proveedor antes de tocar Git

Compiled from `docs/tickets/autopilot-protocol-friction/03-preflight-run-before-touching-git.md`. Identity is `ticket:autopilot-protocol-friction/APF-03`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-22** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-autopilot-protocol-friction]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-autopilot-protocol-friction-apf-03.md","payload_bytes":2057,"payload_sha256":"d02b93444b4b52868fb360c67088e9cb78f5c74504c3cf86e4535581b859eec3"}],"payload_bytes":2057,"payload_sha256":"d02b93444b4b52868fb360c67088e9cb78f5c74504c3cf86e4535581b859eec3","schema":1,"source_digest":"sha256:d02b93444b4b52868fb360c67088e9cb78f5c74504c3cf86e4535581b859eec3","source_identity":"ticket:autopilot-protocol-friction/APF-03","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2057,"payload_sha256":"d02b93444b4b52868fb360c67088e9cb78f5c74504c3cf86e4535581b859eec3","schema":1,"source_digest":"sha256:d02b93444b4b52868fb360c67088e9cb78f5c74504c3cf86e4535581b859eec3","source_identity":"ticket:autopilot-protocol-friction/APF-03"} -->
```markdown
---
ticket_schema: 1
ticket_id: "APF-03"
execution_mode: AFK
blocked_by: []
---

# APF-03 — `run` comprueba remoto y proveedor antes de tocar Git

## Artifact Graph
- Artifact ID: `ticket:autopilot-protocol-friction:03`
- Role: `ticket`
- Parent: [autopilot-protocol-friction-wayfinder.md](../../specs/autopilot-protocol-friction-wayfinder.md)

## Parent Spec
[autopilot-protocol-friction-wayfinder.md](../../specs/autopilot-protocol-friction-wayfinder.md)

## What to Build
El run q2 falló tres veces al arrancar: `target-fetch-failed: cannot refresh configured target` (T45,
T49) y «remote provider cannot be detected; pass an explicit supported override» (T51), sobre un
repositorio sembrado sin remoto. El runner descubre tras crear estado lo que podía saber antes. Un
preflight en `run` que, antes de crear worktree o ledger, compruebe remoto, proveedor y target, y
falle con un mensaje que nombre qué falta y qué opción lo resuelve, o que declare explícitamente el
modo local si el repositorio no tiene remoto.

## Acceptance Criteria
- [ ] Sobre un repo sin remoto, `run` falla antes de crear worktree o ledger, o entra en modo local declarado; se decide y se documenta cuál.
- [ ] El mensaje nombra la comprobación fallida y la opción (`--provider`, `--provider-mode simulated`, remoto) que la resuelve.
- [ ] T45, T49 y T51 reproducidos como tests.
- [ ] Ningún estado queda en disco tras un preflight fallido.

## Frontier
Ready.

## Step-by-Step Implementation Plan
1. Reproducir los tres fallos con un repo sembrado sin remoto.
2. Mover las comprobaciones de remoto/proveedor/target antes de cualquier mutación.
3. Un test por fallo; un test que afirme que no queda estado.

## Testing Plan
- Tests de los tres fallos y del no-estado.
- El run sembrado del benchmark arranca al primer intento o falla en un solo mensaje claro.

## Out of Scope
- Implementar un modo local completo si se decide rechazar los repos sin remoto.
- Cambiar la detección de proveedor en repos con remoto válido.
- Los errores de `resume`: son APF-02.

```
