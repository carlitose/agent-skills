---
type: source
title: "ROA-01 — Una concesión operativa duradera, revocable y visible"
identity_key: ticket:repository-operational-authority/ROA-01
identity_strength: stable
source_path: docs/tickets/repository-operational-authority/01-one-durable-operational-grant.md
source_digest: sha256:a0119534ccdeafc2d059ad0020ddcb460ea294346b85091cf38a35bec5648a42
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-09-22
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# ROA-01 — Una concesión operativa duradera, revocable y visible

Compiled from `docs/tickets/repository-operational-authority/01-one-durable-operational-grant.md`. Identity is `ticket:repository-operational-authority/ROA-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-22** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/spec-repository-operational-authority]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-repository-operational-authority-roa-01.md","payload_bytes":3053,"payload_sha256":"a0119534ccdeafc2d059ad0020ddcb460ea294346b85091cf38a35bec5648a42"}],"payload_bytes":3053,"payload_sha256":"a0119534ccdeafc2d059ad0020ddcb460ea294346b85091cf38a35bec5648a42","schema":1,"source_digest":"sha256:a0119534ccdeafc2d059ad0020ddcb460ea294346b85091cf38a35bec5648a42","source_identity":"ticket:repository-operational-authority/ROA-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3053,"payload_sha256":"a0119534ccdeafc2d059ad0020ddcb460ea294346b85091cf38a35bec5648a42","schema":1,"source_digest":"sha256:a0119534ccdeafc2d059ad0020ddcb460ea294346b85091cf38a35bec5648a42","source_identity":"ticket:repository-operational-authority/ROA-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "ROA-01"
execution_mode: AFK
blocked_by: []
---

# ROA-01 — Una concesión operativa duradera, revocable y visible

## Artifact Graph
- Artifact ID: `ticket:repository-operational-authority:01`
- Role: `ticket`
- Parent: [repository-operational-authority.md](../../specs/repository-operational-authority.md)

## Parent Spec
[repository-operational-authority.md](../../specs/repository-operational-authority.md)

## What to Build
Añadir la clase de autoridad `operations` (`roa-…`) sobre la maquinaria de autoridad por
repositorio que ya existe, con una lista cerrada y versionada de capacidades
(`publish-pr`, `sync-local-install`, `request-runtime-reload`), comprobación de capacidad que
falla en cerrado, comandos de CLI para conceder, revocar y consultar, una lectura combinada de
las tres clases, y el enrutado natural de la frase afirmativa en `ask-skills`. Cubre Decisión,
Invariantes y Criterios de la spec.

## Acceptance Criteria
- [ ] Conceder es idempotente para el mismo actor y evidencia, y falla como contradictorio
      para otros; revocar impide volver a conceder.
- [ ] La comprobación de una capacidad de la lista pasa con la concesión activa y falla con la
      autoridad ausente o revocada.
- [ ] Una capacidad fuera de la lista se rechaza nombrándola, aunque la concesión esté activa.
- [ ] El estado es el mismo desde otro worktree del mismo repositorio.
- [ ] `repository-authority-status` devuelve fusión, reconciliación y operaciones en una
      lectura, sin conceder nada.
- [ ] El texto de `ask-skills` documenta la frase afirmativa, el alcance cerrado, que fusión y
      reconciliación mantienen su propia concesión, y que citas y negaciones no crean
      autoridad; con prueba de regresión sobre el texto.
- [ ] Las suites existentes de autoridad y CLI siguen pasando.

## Frontier
Ready. Skills-only inline. Sin decisiones humanas pendientes dentro del ticket: conceder la
autoridad en un repositorio real es un acto del usuario, no parte de la entrega.

## Step-by-Step Implementation Plan
1. Emitir y validar ticket, grafo y candidato con las funciones canónicas puras.
2. Escribir en RED las pruebas de ciclo de vida, capacidad cubierta y no cubierta, fallo en
   cerrado, estabilidad entre worktrees, lectura combinada y contrato de enrutado.
3. Implementar el módulo de autoridad de operaciones reutilizando `RepositoryAuthorityStore`.
4. Añadir los comandos de CLI y la lectura combinada.
5. Ampliar el texto de `ask-skills` y su prueba de regresión.
6. Ejecutar las suites de autoridad, CLI y grafo de skills; revisar, QA causal y auditoría.
7. Handoff con límites; entrega aparte con autoridad y readback frescos.

## Testing Plan
Máximo 900 s por comando, cada intento registrado. Repositorios Git temporales reales para el
estado y los worktrees; sin mutación de proveedor.

## Out of Scope
Migración de estado heredado de esta clase, autoridad entre repositorios o por cuenta, cambios
en la semántica de fusión y reconciliación, #36 y Telegram.

```
