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
