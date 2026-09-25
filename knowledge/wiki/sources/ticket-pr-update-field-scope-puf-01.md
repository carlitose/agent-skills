---
type: source
title: "PUF-01 — Mandar solo los campos que cambian al actualizar una pull request"
identity_key: ticket:pr-update-field-scope/PUF-01
identity_strength: stable
source_path: docs/tickets/pr-update-field-scope/01-changed-fields-only.md
source_digest: sha256:98c4fb946a33f6861aba9e0d68414a80c5f818f8b19a2b9eed38a356b21a64f9
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-09-21
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# PUF-01 — Mandar solo los campos que cambian al actualizar una pull request

Compiled from `docs/tickets/pr-update-field-scope/01-changed-fields-only.md`. Identity is `ticket:pr-update-field-scope/PUF-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-21** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/spec-pr-update-field-scope]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-pr-update-field-scope-puf-01.md","payload_bytes":1905,"payload_sha256":"98c4fb946a33f6861aba9e0d68414a80c5f818f8b19a2b9eed38a356b21a64f9"}],"payload_bytes":1905,"payload_sha256":"98c4fb946a33f6861aba9e0d68414a80c5f818f8b19a2b9eed38a356b21a64f9","schema":1,"source_digest":"sha256:98c4fb946a33f6861aba9e0d68414a80c5f818f8b19a2b9eed38a356b21a64f9","source_identity":"ticket:pr-update-field-scope/PUF-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1905,"payload_sha256":"98c4fb946a33f6861aba9e0d68414a80c5f818f8b19a2b9eed38a356b21a64f9","schema":1,"source_digest":"sha256:98c4fb946a33f6861aba9e0d68414a80c5f818f8b19a2b9eed38a356b21a64f9","source_identity":"ticket:pr-update-field-scope/PUF-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "PUF-01"
execution_mode: AFK
blocked_by: []
---

# PUF-01 — Mandar solo los campos que cambian al actualizar una pull request

## Artifact Graph
- Artifact ID: `ticket:pr-update-field-scope:01`
- Role: `ticket`
- Parent: [pr-update-field-scope.md](../../specs/pr-update-field-scope.md)

## Parent Spec
[pr-update-field-scope.md](../../specs/pr-update-field-scope.md)

## What to Build
Lectura previa, PATCH con los campos que difieren, rechazo anticipado de mover la base de
una pull request no abierta y reconciliación de efectos tras un fallo. Cubre Decisión,
Invariantes y Criterios de la spec.

## Acceptance Criteria
- [ ] Sin diferencias, ningún PATCH.
- [ ] Solo el cuerpo distinto, PATCH con solo `body`.
- [ ] Pull request fusionada: la base no viaja en la petición.
- [ ] Mover la base de una fusionada se rechaza nombrando el estado.
- [ ] Un fallo informa de los campos ya aplicados y no se reintenta.
- [ ] Suites de proveedor, kernel y wiki siguen pasando.

## Frontier
Ready. Skills-only inline. Sin decisiones humanas pendientes. Integración es un gate aparte.

## Step-by-Step Implementation Plan
1. Emitir y validar ticket, grafo y candidato con las funciones canónicas puras.
2. Escribir en RED las pruebas del alcance de campos y de la reconciliación.
3. Leer antes de mutar, enviar solo lo que difiere y reconciliar tras un fallo.
4. Ejecutar proveedor, kernel y wiki; revisar, QA causal y auditoría canónica.
5. Handoff con límites; entrega aparte, con autoridad y readback frescos.

## Testing Plan
Máximo 900 s por comando, cada intento registrado. Pruebas nuevas con dobles del CLI,
suites de proveedor, kernel completo y wiki. Sin llamadas reales a GitHub y sin reproducir
el 422 contra el servicio.

## Out of Scope
Azure DevOps, #45, el límite de 4000 caracteres, reintentos, rutas nuevas del proveedor,
#42 y reactivar el runner.

```
