---
type: source
title: "Repartir los checks por duración medida y dar timeout proporcional al chunk"
identity_key: ticket:autopilot-suite-execution-cost/03
identity_strength: stable
source_path: docs/tickets/autopilot-suite-execution-cost/03-duration-aware-scheduling.md
source_digest: sha256:5c4a9c04e837e60f8b875f819e6d1d009960d67447263871cf6c1d9ad73bf696
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-09-17
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Repartir los checks por duración medida y dar timeout proporcional al chunk

Compiled from `docs/tickets/autopilot-suite-execution-cost/03-duration-aware-scheduling.md`. Identity is `ticket:autopilot-suite-execution-cost/03`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-17** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-autopilot-suite-execution-cost]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[9],"status":"present"},"frontier":{"headings":[6],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[8],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-autopilot-suite-execution-cost-03.md","payload_bytes":4466,"payload_sha256":"5c4a9c04e837e60f8b875f819e6d1d009960d67447263871cf6c1d9ad73bf696"}],"payload_bytes":4466,"payload_sha256":"5c4a9c04e837e60f8b875f819e6d1d009960d67447263871cf6c1d9ad73bf696","schema":1,"source_digest":"sha256:5c4a9c04e837e60f8b875f819e6d1d009960d67447263871cf6c1d9ad73bf696","source_identity":"ticket:autopilot-suite-execution-cost/03","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 8: Testing Plan |
| frontier | 6: Frontier |
| exclusions | 9: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":4466,"payload_sha256":"5c4a9c04e837e60f8b875f819e6d1d009960d67447263871cf6c1d9ad73bf696","schema":1,"source_digest":"sha256:5c4a9c04e837e60f8b875f819e6d1d009960d67447263871cf6c1d9ad73bf696","source_identity":"ticket:autopilot-suite-execution-cost/03"} -->
```markdown
---
ticket_schema: 1
ticket_id: "03"
execution_mode: AFK
blocked_by: []
---

# Repartir los checks por duración medida y dar timeout proporcional al chunk

## Artifact Graph
- Artifact ID: `artifact:suite-cost-duration-aware-scheduling`
- Role: `ticket`
- Parent: [autopilot-suite-execution-cost.md](../../specs/autopilot-suite-execution-cost.md)

## Parent Spec
[autopilot-suite-execution-cost.md](../../specs/autopilot-suite-execution-cost.md)

## What to Build
`scripts/test-local.mjs` deja de repartir por posición (`position % total`) y de chunkear por
número de casos con un timeout fijo. Pasa a usar duraciones observadas para chunkear por coste
estimado, repartir longest-first y asignar timeout proporcional al coste del chunk, con mínimo.

Motivado por `autopilot-forward-matrix [2/16]`, muerto por SIGKILL a 1800,1 s mientras otros
shards terminaban ociosos. Cubre la sección «Slice 3» del spec.

## Acceptance Criteria
- [x] Las duraciones observadas se persisten y se reutilizan entre ejecuciones.
- [x] Con histórico disponible, los chunks se forman por coste estimado, no por conteo.
- [x] Los chunks se reparten longest-first entre shards.
- [x] El timeout de cada invocación es proporcional a su coste estimado, con un mínimo, y nunca
      inferior al coste observado previo del mismo chunk. Verificado en la corrida final: el
      escenario que había muerto a 365 s y luego a 1 463 s recibió 3 600 s y completó en
      2 304 s. Corregido además el borde en que una suite de **una sola unidad** muere en su
      primera ejecución: su cota inferior ya no se descarta por no existir todavía un promedio
      de suite, que habría repetido el mismo timeout indefinidamente.
- [x] Sin histórico, o con histórico corrupto, ausente u obsoleto respecto a los ids actuales,
      el comportamiento degrada al reparto actual y lo dice en el informe. Nunca falla por eso.
- [x] El histórico vive fuera del control de versiones y es reconstruible.
- [x] Las suites de `SERIAL` siguen ejecutándose sin vecinos y sin chunkear.
- [x] `--jobs 1` sigue dando una ejecución completamente serie.
- [x] El default de `--jobs` conserva un techo portable y documenta la evidencia que lo
      justifica. Medido en la implementación: con 21 shards en Windows 11, checks triviales
      murieron con `0xC0000142` (`STATUS_DLL_INIT_FAILED`) y `0x40010004`
      (`DBG_TERMINATE_PROCESS`) antes de que Python arrancara. El límite no es la CPU sino
      el presupuesto de procesos del sistema; el techo de 8 es lo que hace que el resultado
      **no** dependa de la máquina. El reloj de pared lo gobierna el trabajo total medido.
- [x] `scripts/test-local.test.mjs` cubre: reparto longest-first, timeout proporcional, y las
      tres degradaciones de histórico. 21 tests, todos en verde.

## Resultado medido
Corrida final (`--jobs 8`): **190 checks, 188 ok, 1 fallo, 1 skip, 0 errored y ningún check
terminado por señal**, frente a 1 SIGKILL y 4 escenarios abortados en la referencia.
Check-time 29 882 s → **14 317 s**. El reloj de pared pasa a estar gobernado por una sola
unidad indivisible de 2 304 s; partir ese escenario forward en sus casos es la palanca
siguiente y no forma parte de este ticket.

## Frontier
Done.

## Step-by-Step Implementation Plan
1. Persistir duraciones por id de check tras cada ejecución, en un fichero reconstruible fuera
   del repo. Checkpoint: una segunda ejecución lee lo que escribió la primera.
2. Chunkear por coste estimado usando ese histórico, cayendo al conteo actual cuando falte.
   Checkpoint: los tests de `refinePlan` cubren ambos caminos.
3. Sustituir el reparto por posición por reparto longest-first sobre coste estimado.
   Checkpoint: un plan sintético desbalanceado produce shards equilibrados.
4. Hacer el timeout proporcional al coste del chunk, con mínimo y con suelo en el coste
   observado previo. Checkpoint: el escenario que hoy mata a la forward matrix ya no la mata.
5. Registrar en el informe qué modo de planificación se usó y por qué, especialmente al
   degradar.

## Testing Plan
- Automático: `scripts/test-local.test.mjs` para reparto, chunking, timeout y degradaciones.
- Integración: una ejecución completa que termine sin ningún check terminado por señal.
- Manual: ninguno.

## Out of Scope
- Cambiar qué suites existen o qué casos ejercen.
- Ejecución distribuida entre máquinas.
- Cualquier cambio en `command_capture` o en los fixtures.

```
