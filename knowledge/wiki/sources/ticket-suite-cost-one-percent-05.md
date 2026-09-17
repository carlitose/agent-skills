---
type: source
title: "Quitar del runner los comandos git repetidos dentro de una misma operación"
identity_key: ticket:suite-cost-one-percent/05
identity_strength: stable
source_path: docs/tickets/suite-cost-one-percent/done/05-runner-git-dedup.md
source_digest: sha256:b8576738abcd96547201bd328137deaaaefc621c424e97e78dc8e5b6c074cb38
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-17
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
run_id: suite-cost-deps-04-05-final-v4
---

# Quitar del runner los comandos git repetidos dentro de una misma operación

Compiled from `docs/tickets/suite-cost-one-percent/done/05-runner-git-dedup.md`. Identity is `ticket:suite-cost-one-percent/05`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-17** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-suite-cost-one-percent-wayfinder]]
- Blocked by: [[sources/ticket-suite-cost-one-percent-02]] — `ticket:suite-cost-one-percent/02`

## Run

Completed under autopilot run `suite-cost-deps-04-05-final-v4`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[9],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[8],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-suite-cost-one-percent-05.md","payload_bytes":5660,"payload_sha256":"b8576738abcd96547201bd328137deaaaefc621c424e97e78dc8e5b6c074cb38"}],"payload_bytes":5660,"payload_sha256":"b8576738abcd96547201bd328137deaaaefc621c424e97e78dc8e5b6c074cb38","schema":1,"source_digest":"sha256:b8576738abcd96547201bd328137deaaaefc621c424e97e78dc8e5b6c074cb38","source_identity":"ticket:suite-cost-one-percent/05","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 8: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 9: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":5660,"payload_sha256":"b8576738abcd96547201bd328137deaaaefc621c424e97e78dc8e5b6c074cb38","schema":1,"source_digest":"sha256:b8576738abcd96547201bd328137deaaaefc621c424e97e78dc8e5b6c074cb38","source_identity":"ticket:suite-cost-one-percent/05"} -->
```markdown
---
ticket_schema: 1
ticket_id: "05"
execution_mode: AFK
blocked_by:
  - "02"
---

# Quitar del runner los comandos git repetidos dentro de una misma operación

## Artifact Graph
- Artifact ID: `artifact:suite-one-percent-runner-git-dedup`
- Role: `ticket`
- Parent: [suite-cost-one-percent-wayfinder.md](../../specs/suite-cost-one-percent-wayfinder.md)

## Parent Spec
[suite-cost-one-percent-wayfinder.md](../../specs/suite-cost-one-percent-wayfinder.md)

## What to Build
Con la tabla del ticket 02, eliminar las repeticiones **idénticas dentro de la misma
operación** del runner: el mismo argv sobre el mismo estado del árbol, emitido varias veces
porque distintas funciones lo piden por separado. El resultado se obtiene una vez por
operación y se reutiliza mientras el estado no cambia.

Esto acelera las ejecuciones reales del runner, no solo los tests. Cubre la palanca «cuántos
comandos emite el runner por operación» del mapa.

## Acceptance Criteria
- [x] Solo se reutilizan resultados de comandos que el ticket 02 clasificó como repetición
      idéntica dentro de operación. Una repetición entre operaciones no se cachea: el estado
      puede haber cambiado.
- [x] Cualquier mutación del árbol o del índice invalida lo reutilizado dentro de la
      operación. Un test lo demuestra: mutar entre dos lecturas produce la lectura nueva.
- [x] El número de comandos `git` por operación, medido con el arnés del ticket 02 sobre los
      mismos tres casos, baja y se reporta antes/después en segundos y en conteo.
- [x] `test_command_bounds`, `test_command_capture_failures`, `test_provider_command_bounds`
      y `test_posix_command_bounds` pasan sin modificarse.
- [x] `test_kernel`, `test_cli` y `test_worktree_gc` pasan sin modificar ningún aserto.
- [x] Ningún cambio en `capture_command` ni en su contención.

## Frontier
Done.

## Resultado medido

**Qué se implementó.** `git_ops.repository_scope()`, un ámbito que se entra una vez por
invocación de la CLI (`cli.main`, alrededor de `args.handler(args)`, el punto único por el que
pasan tanto los subprocesos como las llamadas en proceso). Dentro de él, `repository_root` y
`common_git_dir` responden una vez por directorio. Fuera de él no hay caché ninguna: una
respuesta no puede sobrevivir al comando que la pidió, y nada que haga un test o un proceso
vecino entre invocaciones puede servirse de una entrada válida.

**Invalidación.** `init`, `clone`, `worktree` y `submodule` vacían el ámbito: son los únicos
comandos que pueden mover una ruta de un repositorio a otro. Un fallo nunca se recuerda.

**Antes / después por caso** (baseline obtenido desactivando el ámbito desde el arnés, sin
tocar código de producto):

| caso | antes | después | comandos |
|---|---|---|---|
| `test_candidate_invalidation_...` | 40,4 s | **33,5 s** (−17 %) | 395 → 329 |
| `test_enabled_preflight_exclusion_...` | 32,0 s | **24,4 s** (−24 %) | 302 → 239 |
| `test_approve_resolves_hitl_start_gate` | 9,9 s | **7,2 s** (−27 %) | 83 → 59 |

`git rev-parse --show-toplevel` en el caso mediano: **116 llamadas y 8,8 s → 54 llamadas y
2,8 s**.

**Verificación completa** (`full --jobs 8`, 20:48:03 → 21:06:11): 174 ok, **0 fallos, 0
errores**, check-time **7 803 s** (−19 % sobre los 9 646 s del ticket 01), reloj 18 min, check
más largo 300,5 s. Las cuatro suites de límites de comando pasaron sin modificarse.
Acumulado desde la referencia: 14 322 s → 7 803 s, **−46 %**; reloj 78 → 18 min.

**Qué no se tocó, y por qué.** Dos grupos de repeticiones quedan vivos a propósito:

- `status_barrier._lexical_root` (+25 y +25 por caso) revalida identidad y alias del
  repositorio en cada uso. Repetir *es* su trabajo; cachear una barrera la desarma.
- `git_ops.semantic_candidate_ref` (`add -A` + `write-tree` + `rev-parse <oid>^{tree}`, 116
  comandos y 11,4 s en un caso) son instantáneas de estado. Reutilizarlas exigiría demostrar que
  nada escribió en el árbol entre dos llamadas, incluidas escrituras de Python que ningún
  comando `git` delata. La pregunta real es de producto: por qué una invocación necesita 40
  instantáneas semánticas. Queda en el mapa, sin tocar.

**Tests añadidos**: `ticket-autopilot/tests/test_git_repository_scope.py`, 7 casos, incluidos
el repositorio anidado creado dentro del ámbito, el worktree añadido dentro del ámbito, el
fallo que no se recuerda y la lectura de contenido que nunca se sirve desde el ámbito.

**Límite declarado**: medido solo en Windows 11. La lógica es independiente del sistema, pero
la cifra de ahorro no se puede dar por hecha en POSIX sin medirla allí.

## Step-by-Step Implementation Plan
1. Elegir la costura: el punto donde el runner conoce «operación en curso» y puede alojar
   un ámbito de reutilización con invalidación. Checkpoint: un test de invalidación por
   mutación en verde antes de reutilizar nada.
2. Reutilizar la familia más frecuente de la tabla primero (probablemente
   `rev-parse --show-toplevel`). Checkpoint: conteo antes/después en un caso.
3. Seguir por frecuencia × coste hasta agotar la lista «idéntica dentro de operación».
   Checkpoint: las suites completas en verde.

## Testing Plan
- Automático: test de invalidación por mutación; las suites de límites sin cambios;
  `test_kernel` y `test_cli` completos.
- Medición: arnés del ticket 02 sobre los tres casos, solos.
- No disponible aquí: medida en POSIX; la lógica es común y se declara sin cifra.

## Out of Scope
- Cachear entre operaciones o entre eventos.
- Reducir el coste de captura por comando; eso es otro spec si la tabla lo justifica.

```
