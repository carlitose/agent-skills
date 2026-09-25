---
type: source
title: "TDR-04 — Riesgo por función y review dirigida (`c3`, `c4`)"
identity_key: ticket:ticket-driver/TDR-04
identity_strength: stable
source_path: docs/tickets/ticket-driver/04-risk-directed-review.md
source_digest: sha256:f86bc086d445a3e40595a2c2672d36b2c20beb3590e879bc3ae52bca4f4e4ba7
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-09-23
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# TDR-04 — Riesgo por función y review dirigida (`c3`, `c4`)

Compiled from `docs/tickets/ticket-driver/04-risk-directed-review.md`. Identity is `ticket:ticket-driver/TDR-04`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-23** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-ticket-driver]]
- Blocked by: [[sources/ticket-ticket-driver-tdr-03]] — `ticket:ticket-driver/TDR-03`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-ticket-driver-tdr-04.md","payload_bytes":3217,"payload_sha256":"f86bc086d445a3e40595a2c2672d36b2c20beb3590e879bc3ae52bca4f4e4ba7"}],"payload_bytes":3217,"payload_sha256":"f86bc086d445a3e40595a2c2672d36b2c20beb3590e879bc3ae52bca4f4e4ba7","schema":1,"source_digest":"sha256:f86bc086d445a3e40595a2c2672d36b2c20beb3590e879bc3ae52bca4f4e4ba7","source_identity":"ticket:ticket-driver/TDR-04","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3217,"payload_sha256":"f86bc086d445a3e40595a2c2672d36b2c20beb3590e879bc3ae52bca4f4e4ba7","schema":1,"source_digest":"sha256:f86bc086d445a3e40595a2c2672d36b2c20beb3590e879bc3ae52bca4f4e4ba7","source_identity":"ticket:ticket-driver/TDR-04"} -->
```markdown
---
ticket_schema: 1
ticket_id: "TDR-04"
execution_mode: AFK
blocked_by:
  - "TDR-03"
---

# TDR-04 — Riesgo por función y review dirigida (`c3`, `c4`)

## Artifact Graph
- Artifact ID: `ticket:ticket-driver:04`
- Role: `ticket`
- Parent: [ticket-driver.md](../../specs/ticket-driver.md)

## Parent Spec
[ticket-driver.md](../../specs/ticket-driver.md)

## What to Build
El driver calcula el diff **por función** del candidato (AST de Python en esta versión: funciones
añadidas o modificadas con su hunk), pregunta `risk.semantic_change` (score) por cada una en una sola
petición, y las funciones por encima del umbral de política reciben una hoja `reviewer` nueva dirigida
solo a ellas (`prompts/reviewer-directed.md`: hunk, criterios del ticket, pregunta explícita por
redondeo, límites y aritmética de dinero). `--candidate c3a|c3b` = `c2x` + esto. `--candidate c4` =
una sola hoja como el brazo skills-only + riesgo + review dirigida, **sin** worktree propio,
integración ni árbitro de gates: mide el valor de Jev aislado. Todo juicio y su función van a
`judgments.jsonl`. Secciones de la spec: Regla observable/semántico (riesgo latente), Preguntas
iniciales (`risk.semantic_change`), Candidatos (`c3`, `c4`), S4.

## Acceptance Criteria
- [ ] Sobre el diff del repositorio sembrado con la hoja de sustitución, el driver enumera exactamente las funciones Python añadidas o modificadas con su hunk; ficheros no Python se registran como `unsupported`, no se omiten en silencio.
- [ ] Con el servidor falso devolviendo scores altos para dos funciones y bajos para el resto, la hoja dirigida recibe solo esas dos y sus hallazgos entran en el bucle de calidad como los de la review general.
- [ ] `c4` termina en el mismo directorio de trabajo (sin worktree) con `summary.json`, juicios y hoja dirigida, y sin ninguna llamada al integrador ni a los gates del árbitro.
- [ ] `c2` y `c1` no cambian de comportamiento (suites verdes).

## Frontier
Bloqueado por TDR-03: usa el árbitro, la cascada y los recibos.

## Step-by-Step Implementation Plan
1. `function_diff.py`: `ast` sobre base y candidato por fichero `.py` tocado; emparejar por nombre calificado; hunk por función con `difflib`.
2. `questions/risk.semantic_change.json` con niveles concretos (de «formato o renombre» a «cambia redondeo, límites o aritmética de dinero»); umbral en `policy.json`.
3. `prompts/reviewer-directed.md`; hoja dirigida integrada en el bucle tras la review general.
4. Configuración `c4`: bandera que desactiva worktree, integrador y árbitro de gates, conserva riesgo y review dirigida.
5. `tests/`: fixtures con funciones añadidas, modificadas, renombradas y un fichero no Python; guiones del servidor falso; los cuatro criterios.

## Testing Plan
- Unitarias: diff por función (añadida, modificada, renombrada, borrada, decoradores, métodos anidados); agrupación en una petición; umbral.
- Integración con hojas y servidor falsos: `c3a` con dos funciones dirigidas; `c4` sin worktree.
- En vivo: ninguna; el comportamiento real de Jev sobre hunks se mide en TDR-05.

## Out of Scope
- Otros lenguajes que Python.
- Cambiar la review general o `code-review`.
- Calibración del umbral de riesgo.

```
