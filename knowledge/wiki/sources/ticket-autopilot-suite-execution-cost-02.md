---
type: source
title: "Construir el repositorio de fixture una vez por clase y copiarlo por caso"
identity_key: ticket:autopilot-suite-execution-cost/02
identity_strength: stable
source_path: docs/tickets/autopilot-suite-execution-cost/02-shared-git-fixture.md
source_digest: sha256:7d1d4bb71389bc903028dd490edb8375ff61f429ec5e47561d4f0311d4a65f97
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-09-17
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Construir el repositorio de fixture una vez por clase y copiarlo por caso

Compiled from `docs/tickets/autopilot-suite-execution-cost/02-shared-git-fixture.md`. Identity is `ticket:autopilot-suite-execution-cost/02`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-17** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-autopilot-suite-execution-cost]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-autopilot-suite-execution-cost-02.md","payload_bytes":3031,"payload_sha256":"7d1d4bb71389bc903028dd490edb8375ff61f429ec5e47561d4f0311d4a65f97"}],"payload_bytes":3031,"payload_sha256":"7d1d4bb71389bc903028dd490edb8375ff61f429ec5e47561d4f0311d4a65f97","schema":1,"source_digest":"sha256:7d1d4bb71389bc903028dd490edb8375ff61f429ec5e47561d4f0311d4a65f97","source_identity":"ticket:autopilot-suite-execution-cost/02","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3031,"payload_sha256":"7d1d4bb71389bc903028dd490edb8375ff61f429ec5e47561d4f0311d4a65f97","schema":1,"source_digest":"sha256:7d1d4bb71389bc903028dd490edb8375ff61f429ec5e47561d4f0311d4a65f97","source_identity":"ticket:autopilot-suite-execution-cost/02"} -->
```markdown
---
ticket_schema: 1
ticket_id: "02"
execution_mode: AFK
blocked_by: []
---

# Construir el repositorio de fixture una vez por clase y copiarlo por caso

## Artifact Graph
- Artifact ID: `artifact:suite-cost-shared-git-fixture`
- Role: `ticket`
- Parent: [autopilot-suite-execution-cost.md](../../specs/autopilot-suite-execution-cost.md)

## Parent Spec
[autopilot-suite-execution-cost.md](../../specs/autopilot-suite-execution-cost.md)

## What to Build
Un soporte de fixture en `git_test_support` que construya una plantilla de repositorio una sola
vez por clase y entregue a cada caso una copia de directorio, en lugar de repetir
`git init` + `git config` + `git add` + `git commit` por caso (260-330 ms por llamada medidos).

Cubre la sección «Slice 2» del spec.

## Acceptance Criteria
- [x] Un caso que hoy inicializa su repositorio obtiene una copia y no invoca `git init`.
      `CliTests.setUp` ahora copia una plantilla construida una vez por clase.
- [x] La copia es idéntica byte a byte a lo que producía la inicialización: contenido,
      finales de línea, e índice. Verificado comparando `HEAD`, `write-tree`,
      `status --porcelain` y los bytes de un fichero LF y uno CRLF.
- [x] Cada caso sigue recibiendo un repositorio propio: mutarlo no afecta a ningún otro caso,
      verificado por un test que muta y otro que observa.
- [x] El aislamiento de configuración de `isolated_git_environment` no cambia.
- [x] Una plantilla corrupta o una copia parcial falla de forma visible, no ejecuta contra un
      repositorio a medias.
- [x] Se reporta la duración antes/después de al menos una suite convertida. Medido en la
      misma máquina y bajo la misma carga: inicializar cuesta **1292 ms** por caso, copiar
      **271 ms**; 1021 ms menos por caso, ~103 s sobre los 101 casos de `CliTests`.

## Frontier
Done.

## Step-by-Step Implementation Plan
1. Añadir a `git_test_support` la construcción de plantilla por clase y la entrega de copias,
   sin convertir todavía ninguna suite. Checkpoint: el soporte tiene su propio test y
   `test_git_test_support` sigue verde.
2. Verificar equivalencia byte a byte entre repositorio inicializado y copiado, incluido el
   índice, con un test que compare ambos. Checkpoint: ese test pasa antes de convertir nada.
3. Convertir una suite representativa que hoy pague inicialización por caso. Checkpoint: la
   suite pasa y su duración baja de forma medible.
4. Convertir el resto de suites que compartan ese patrón, una a una. Checkpoint tras cada una.

## Testing Plan
- Automático: `test_git_test_support` ampliado; equivalencia byte a byte; aislamiento entre
  casos; las suites convertidas.
- Automático: las suites de fidelidad de texto en Windows, que son las que detectarían una
  copia que altere finales de línea.
- Manual: ninguno.

## Out of Scope
- Compartir un repositorio **mutable** entre casos.
- Cambiar el aislamiento de configuración de Git.
- Convertir suites cuyo objeto de prueba sea la propia inicialización del repositorio.

```
