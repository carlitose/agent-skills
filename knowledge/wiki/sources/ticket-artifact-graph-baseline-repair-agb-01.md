---
type: source
title: "AGB-01 — Restaurar un grafo verificable conservando la historia"
identity_key: ticket:artifact-graph-baseline-repair/AGB-01
identity_strength: stable
source_path: docs/tickets/artifact-graph-baseline-repair/01-restore-artifact-graph.md
source_digest: sha256:ce15f1ea872031db25740616592b40a78ded41a92873e6f21ffc206d9ea0fba2
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-09-21
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# AGB-01 — Restaurar un grafo verificable conservando la historia

Compiled from `docs/tickets/artifact-graph-baseline-repair/01-restore-artifact-graph.md`. Identity is `ticket:artifact-graph-baseline-repair/AGB-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-21** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/spec-artifact-graph-baseline-repair]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-artifact-graph-baseline-repair-agb-01.md","payload_bytes":3773,"payload_sha256":"ce15f1ea872031db25740616592b40a78ded41a92873e6f21ffc206d9ea0fba2"}],"payload_bytes":3773,"payload_sha256":"ce15f1ea872031db25740616592b40a78ded41a92873e6f21ffc206d9ea0fba2","schema":1,"source_digest":"sha256:ce15f1ea872031db25740616592b40a78ded41a92873e6f21ffc206d9ea0fba2","source_identity":"ticket:artifact-graph-baseline-repair/AGB-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3773,"payload_sha256":"ce15f1ea872031db25740616592b40a78ded41a92873e6f21ffc206d9ea0fba2","schema":1,"source_digest":"sha256:ce15f1ea872031db25740616592b40a78ded41a92873e6f21ffc206d9ea0fba2","source_identity":"ticket:artifact-graph-baseline-repair/AGB-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "AGB-01"
execution_mode: AFK
blocked_by: []
---

# AGB-01 — Restaurar un grafo verificable conservando la historia

## Artifact Graph

- Artifact ID: `ticket:artifact-graph-baseline-repair:AGB-01`
- Role: `ticket`
- Parent: [Reparación del baseline](../../specs/artifact-graph-baseline-repair.md)

## Parent Spec

[Decisiones e invariantes](../../specs/artifact-graph-baseline-repair.md).

## What to Build

Reparar los 45 errores del auditor sobre main d82b9d1, que bloquean el preflight de WGC-04.
Cambiar datos y añadir una regresión del corpus real, sin cambiar contratos/validadores.
Normalizar grafos editables, completar reciprocidad declarada, conservar fuera del grafo las
referencias históricas ausentes y recuperar NDW-01/02/03 desde su snapshot validado.

## Acceptance Criteria

- [ ] AC1: La misma prueba canónica pasa de 45 errores baseline a cero sobre el árbol entregado;
      exige además presencia del artifact de decisión para impedir un PASS por corpus vacío.
- [ ] AC2: Todos los tickets ya versionados conservan bytes, IDs, dependencias y ubicación.
      No se cambian ledgers, snapshots, completion, grants ni datos de otros checkouts.
- [ ] AC3: NDW-01/02/03 recuperados tienen los digests normalizados originales, snapshot validado,
      commits con marcador exacto y ascendencia en base; NDW-04 mantiene sus dependencias.
- [ ] AC4: Se conservan IDs de artifacts existentes; propiedad recíproca única, sin ciclos ni
      raíces/roles inventados por el parser. Recursos externos a las raíces siguen en prosa.
- [ ] AC5: Las 15 referencias a fuentes ausentes retienen título/identificador/ruta visible;
      no se inventan cuerpos, estados o entrega ni se conservan enlaces canónicos falsos.
- [ ] AC6: Warnings legacy no se ocultan ni se migran silenciosamente. Prueba del corpus,
      pruebas del auditor/contrato afectadas y checks de integridad documentan plataformas,
      simulaciones, costes, puertas pendientes y ausencia de cambios de runtime.

## Frontier

AFK, sin blockers de implementación. Prerrequisito de WGC-04 por gate observado, no reparación
mezclada con su código. Checkout aislado C:/artifact34 en main d82b9d1. Suposición explícita:
una fuente que no está en Git se documenta como ausente hasta demostrar su contenido; no se
clasifica automáticamente como cancelada, pendiente o integrada.

## Step-by-Step Implementation Plan

1. Validar spec/ticket, fuente, base/target y allowlist; conservar diagnósticos originales.
2. Añadir una prueba causal del corpus y registrar RED antes de reparar.
3. Validar snapshot/digests/commits NDW antes de cualquier recuperación; corregir los grafos
   y conservar referencias históricas sin alterar tickets existentes ni validadores.
4. Ejecutar GREEN y comparación completa de invariantes; congelar CandidateRef real.
5. Simplificar solo si es necesario, revisar read-only, planificar/ejecutar QA acotada y
   producir el bundle validado. Entrega/sync separados y sujetos a autoridad/CI/readback.

## Testing Plan

Auditor canónico sobre corpus real, snapshot/parser/serializer originales y hashes; tests
existentes de artifact_audit y ticket_contract; diff check y política lint. QA local90s
acumulados; TDD/preparación/CI separados y medidos, sin borrar fallos. Máximo3 quality cycles,
900s/comando. No full-suite automático para datos documentales; CI obligatorio no se omite.

## Out of Scope

- Modificar runtime, parsers, severidades, raíces, lifecycle, grants o tickets existentes.
- Reanudar runner/scheduler/subagentes, planner/inventario/cleanup reales o wiki.
- Copiar ledgers privados al repositorio; fabricar procedencia o cierre de gates.
- Resolver WGC-04 o los demás bugs dentro de este ticket.

```
