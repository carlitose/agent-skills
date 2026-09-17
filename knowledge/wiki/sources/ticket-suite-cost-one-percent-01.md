---
type: source
title: "Sacar la forward matrix del perfil `full` y dejarla como comando explícito de release"
identity_key: ticket:suite-cost-one-percent/01
identity_strength: stable
source_path: docs/tickets/suite-cost-one-percent/done/01-forward-matrix-out-of-full.md
source_digest: sha256:f94834345cdecf616d616e711899672a6314a43075cc4cfab0682564deebc054
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-17
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
run_id: suite-cost-one-percent-final
---

# Sacar la forward matrix del perfil `full` y dejarla como comando explícito de release

Compiled from `docs/tickets/suite-cost-one-percent/done/01-forward-matrix-out-of-full.md`. Identity is `ticket:suite-cost-one-percent/01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-17** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-suite-cost-one-percent-wayfinder]]

## Run

Completed under autopilot run `suite-cost-one-percent-final`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[9],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[8],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-suite-cost-one-percent-01.md","payload_bytes":4200,"payload_sha256":"f94834345cdecf616d616e711899672a6314a43075cc4cfab0682564deebc054"}],"payload_bytes":4200,"payload_sha256":"f94834345cdecf616d616e711899672a6314a43075cc4cfab0682564deebc054","schema":1,"source_digest":"sha256:f94834345cdecf616d616e711899672a6314a43075cc4cfab0682564deebc054","source_identity":"ticket:suite-cost-one-percent/01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 8: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 9: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":4200,"payload_sha256":"f94834345cdecf616d616e711899672a6314a43075cc4cfab0682564deebc054","schema":1,"source_digest":"sha256:f94834345cdecf616d616e711899672a6314a43075cc4cfab0682564deebc054","source_identity":"ticket:suite-cost-one-percent/01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "01"
execution_mode: AFK
blocked_by: []
---

# Sacar la forward matrix del perfil `full` y dejarla como comando explícito de release

## Artifact Graph
- Artifact ID: `artifact:suite-one-percent-forward-matrix-out-of-full`
- Role: `ticket`
- Parent: [suite-cost-one-percent-wayfinder.md](../../specs/suite-cost-one-percent-wayfinder.md)

## Parent Spec
[suite-cost-one-percent-wayfinder.md](../../specs/suite-cost-one-percent-wayfinder.md)

## What to Build
`scripts/test-local.mjs full` deja de incluir `autopilot-forward-matrix`. El script
`ticket-autopilot/scripts/forward_test.py` no cambia: sigue siendo el comando que
`ticket-autopilot/SKILL.md` prescribe para releases de la familia de workflows, y se invoca
explícitamente cuando se prepara una.

Motivo medido: la forward matrix no tiene tests propios. Lanza `unittest -k <caso>` sobre 85
casos de otras suites (32 de `test_cli`, 17 de `test_kernel`, 9 de `test_skill_graph`, …) que
la misma corrida `full` ya ejecutó. Cuesta 3 857 s de 14 322 (27 %) y contiene la unidad
indivisible que fija el reloj: `autonomous-merge-grant`, 2 304 s. Cubre la arista 1 del mapa.

## Acceptance Criteria
- [x] `node scripts/test-local.mjs full --list` no contiene `autopilot-forward-matrix`.
- [x] `node scripts/test-local.mjs full` termina con los mismos casos de suite en verde que
      antes y sin ningún check cuya duración supere los 600 s.
- [x] `python ticket-autopilot/scripts/forward_test.py --list` y `--output` siguen
      funcionando sin cambios; `test_forward_test.py` y `test_final_tree_forward_test.py`
      pasan sin modificarse.
- [x] El README describe `full` sin la matriz y nombra el comando de release explícito, con
      una frase que diga por qué: los casos ya corren en sus suites.
- [x] `scripts/test-local.test.mjs` deja de esperar la matriz en `full` y sigue cubriendo la
      clasificación de informes forward para el camino explícito.
- [x] Se registra en el mapa el check-time y el reloj de la primera corrida `full` sin la
      matriz.

## Frontier
Done.

## Resultado medido

Corrida `full --jobs 8` del 16/09/2026, 20:04:48 → 20:27:15.

| | referencia (con matriz) | esta corrida | |
|---|---|---|---|
| check-time | 14 322 s | **9 646 s** | −33 % |
| reloj | 78 min | **22 min** | −72 % |
| checks | 190 | 176 ejecutados | |
| resultado | 188 ok / 1 fallo | **175 ok / 0 fallos / 0 errores** | |
| check más largo | 2 304 s (`autonomous-merge-grant`) | **399,9 s** (`test_cli [57/62]`) | |

El reloj baja más que el check-time porque la unidad indivisible de 38 min desaparece: el
check más largo pasa a ser un trozo de `test_cli` de 6,7 min, que el planificador sí reparte.
Un `not-run` esperado (`autopilot-forward-matrix`, con su motivo de release) y un `skipped`
esperado (`test_posix_command_bounds.py`, no es POSIX esta máquina).

La suite forward propia siguió en verde sin tocarla: `test_forward_test.py` 2 tests OK en
55,9 s y `test_final_tree_forward_test.py` 2 tests OK en 53,9 s. `forward_test.py --list`
sigue devolviendo sus 32 escenarios.

Nota lateral, no reclamada como arreglo: el flake abierto
(`autonomous-stack-reconcile-load-flake.md`) no se reprodujo en esta corrida. Una corrida sin
fallo no cierra un flake.

## Step-by-Step Implementation Plan
1. Quitar la inclusión de `autopilot-forward-matrix` en `buildPlan` y su rama de chunking en
   `refinePlan`; conservar `classify(result, 'forward')` para quien ejecute el script a mano
   con `--report`. Checkpoint: `--list` limpio.
2. Ajustar `scripts/test-local.test.mjs`. Checkpoint: 21 tests en verde.
3. README: sección de perfiles. Checkpoint: `git diff --check` limpio.
4. Corrida `full` completa y anotar cifras en el mapa. Checkpoint: cero checks > 600 s.

## Testing Plan
- Automático: `node --test scripts/test-local.test.mjs`; `test_forward_test.py`;
  `test_final_tree_forward_test.py`.
- Integración: una corrida `full` con `--jobs 8`, comparada con la referencia del mapa.
- Manual: ninguno.

## Out of Scope
- Cambiar qué escenarios contiene la forward matrix o cómo produce su informe.
- Partir el escenario `autonomous-merge-grant`: sale de `full`, no se optimiza.

```
