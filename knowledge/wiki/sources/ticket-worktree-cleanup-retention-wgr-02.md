---
type: source
title: "WGR-02 — Que cada rechazo de limpieza nombre la salida que sí existe"
identity_key: ticket:worktree-cleanup-retention/WGR-02
identity_strength: stable
source_path: docs/tickets/worktree-cleanup-retention/02-name-the-exit-in-each-refusal.md
source_digest: sha256:2d6119370840f2ec968b5452b900c95b48c7b853597cf695dc8ee87db367dfd7
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-09-22
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# WGR-02 — Que cada rechazo de limpieza nombre la salida que sí existe

Compiled from `docs/tickets/worktree-cleanup-retention/02-name-the-exit-in-each-refusal.md`. Identity is `ticket:worktree-cleanup-retention/WGR-02`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-22** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/spec-worktree-cleanup-retention]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-worktree-cleanup-retention-wgr-02.md","payload_bytes":2389,"payload_sha256":"2d6119370840f2ec968b5452b900c95b48c7b853597cf695dc8ee87db367dfd7"}],"payload_bytes":2389,"payload_sha256":"2d6119370840f2ec968b5452b900c95b48c7b853597cf695dc8ee87db367dfd7","schema":1,"source_digest":"sha256:2d6119370840f2ec968b5452b900c95b48c7b853597cf695dc8ee87db367dfd7","source_identity":"ticket:worktree-cleanup-retention/WGR-02","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2389,"payload_sha256":"2d6119370840f2ec968b5452b900c95b48c7b853597cf695dc8ee87db367dfd7","schema":1,"source_digest":"sha256:2d6119370840f2ec968b5452b900c95b48c7b853597cf695dc8ee87db367dfd7","source_identity":"ticket:worktree-cleanup-retention/WGR-02"} -->
```markdown
---
ticket_schema: 1
ticket_id: "WGR-02"
execution_mode: AFK
blocked_by: []
---

# WGR-02 — Que cada rechazo de limpieza nombre la salida que sí existe

## Artifact Graph
- Artifact ID: `ticket:worktree-cleanup-retention:02`
- Role: `ticket`
- Parent: [worktree-cleanup-retention.md](../../specs/worktree-cleanup-retention.md)

## Parent Spec
[worktree-cleanup-retention.md](../../specs/worktree-cleanup-retention.md)

## What to Build
Cambiar los tres rechazos de limpieza que hoy no dicen cómo se abren para que nombren el acto
exacto y su comando: run en curso (`abort` con actor y motivo, o esperar a que termine), run en
pausa (`unpause`), y ticket en espera administrativa o cancelado (`ticket-reopen-request` para
reabrirlo). El mensaje incluye el identificador de la run o del ticket implicado. Ninguna
condición se relaja: lo que hoy se rechaza se sigue rechazando exactamente igual. Cubre la
sección «Segunda parte: nombrar la salida» de la spec.

## Acceptance Criteria
- [ ] El rechazo de una run en curso nombra `abort`, y que hace falta actor y motivo.
- [ ] El rechazo por pausa nombra `unpause` y el identificador de la run.
- [ ] El rechazo por ticket en espera o cancelado nombra el ticket y cómo se reabre.
- [ ] Las condiciones no cambian: cada caso que hoy se rechaza se sigue rechazando, demostrado
      caso por caso.
- [ ] Los dos rechazos que ya nombraban su salida —`--confirm` y `--force`— siguen igual.
- [ ] Las suites `tests/test_kernel.py` y la suite nueva pasan enteras.

## Frontier
Ready. Skills-only inline. Sin decisiones humanas pendientes. Integración es un gate aparte.

## Step-by-Step Implementation Plan
1. Emitir y validar ticket, grafo y candidato con las funciones canónicas puras.
2. Escribir las pruebas de los cinco mensajes y registrarlas en RED.
3. Cambiar los tres mensajes, sin tocar ninguna condición.
4. Ejecutar lint y las suites afectadas; revisar, QA causal y auditoría.
5. Handoff con límites; entrega aparte, con autoridad y readback frescos, y perfil alojado sobre
   el head exacto.

## Testing Plan
Máximo 900 s por comando, cada intento registrado. Las pruebas construyen ledgers en memoria y
repositorios temporales; ninguna run real se toca.

## Out of Scope
Permitir la limpieza de una run en curso, en pausa o con un ticket en espera; borrar worktrees;
la prueba de retención de WGR-01, ya entregada.

```
