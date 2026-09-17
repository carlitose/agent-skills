---
type: source
title: "Decidir el contrato de perfiles y qué cobertura e2e con Git real es irrenunciable"
identity_key: ticket:suite-cost-one-percent/04
identity_strength: stable
source_path: docs/tickets/suite-cost-one-percent/done/04-profile-contract-decision.md
source_digest: sha256:935cc94f3be289e766a30631eff18d8f2532a5e4af5e9fdb56197463c2851f3f
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-17
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
run_id: suite-cost-deps-04-05-final-v4
---

# Decidir el contrato de perfiles y qué cobertura e2e con Git real es irrenunciable

Compiled from `docs/tickets/suite-cost-one-percent/done/04-profile-contract-decision.md`. Identity is `ticket:suite-cost-one-percent/04`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-17** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-suite-cost-one-percent-wayfinder]]
- Blocked by: [[sources/ticket-suite-cost-one-percent-02]] — `ticket:suite-cost-one-percent/02`
- Blocked by: [[sources/ticket-suite-cost-one-percent-03]] — `ticket:suite-cost-one-percent/03`

## Run

Completed under autopilot run `suite-cost-deps-04-05-final-v4`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[9],"status":"present"},"frontier":{"headings":[6],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[8],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-suite-cost-one-percent-04.md","payload_bytes":3389,"payload_sha256":"935cc94f3be289e766a30631eff18d8f2532a5e4af5e9fdb56197463c2851f3f"}],"payload_bytes":3389,"payload_sha256":"935cc94f3be289e766a30631eff18d8f2532a5e4af5e9fdb56197463c2851f3f","schema":1,"source_digest":"sha256:935cc94f3be289e766a30631eff18d8f2532a5e4af5e9fdb56197463c2851f3f","source_identity":"ticket:suite-cost-one-percent/04","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 8: Testing Plan |
| frontier | 6: Frontier |
| exclusions | 9: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3389,"payload_sha256":"935cc94f3be289e766a30631eff18d8f2532a5e4af5e9fdb56197463c2851f3f","schema":1,"source_digest":"sha256:935cc94f3be289e766a30631eff18d8f2532a5e4af5e9fdb56197463c2851f3f","source_identity":"ticket:suite-cost-one-percent/04"} -->
```markdown
---
ticket_schema: 1
ticket_id: "04"
execution_mode: HITL
blocked_by:
  - "02"
  - "03"
---

# Decidir el contrato de perfiles y qué cobertura e2e con Git real es irrenunciable

## Artifact Graph
- Artifact ID: `artifact:suite-one-percent-profile-contract-decision`
- Role: `ticket`
- Parent: [suite-cost-one-percent-wayfinder.md](../../specs/suite-cost-one-percent-wayfinder.md)
- Produces: [local-verification-profile-contract.md](../../specs/local-verification-profile-contract.md)

## Parent Spec
[suite-cost-one-percent-wayfinder.md](../../specs/suite-cost-one-percent-wayfinder.md)

## What to Build
Decisión humana, no implementación. Entrevista `grilling`, una pregunta a la vez, con las
medidas de 02 y 03; confirmación final antes de registrar el contrato mediante `to-spec`.

Decidir composición y presupuesto del gate, obligatoriedad de `full`, riesgo de detección
diferida y tratamiento de los candidatos a consolidación. No inferir equivalencia de
comportamiento a partir de líneas ni usar check-time como si fuera reloj paralelo.

## Acceptance Criteria
- [x] Entrevista realizada una pregunta a la vez, con las respuestas confirmadas.
- [x] Decisiones registradas en `docs/specs/local-verification-profile-contract.md`, con
      evidencia de 02/03, correcciones de interpretación y confirmación final atribuible.
- [x] El spec nombra los diez e2e por identificador, conservados con Git real.
- [x] El mapa enlaza el contrato y retira la incógnita de producto.
- [x] No se cambia ningún test en este ticket.

## Decision Record
El usuario confirmó el resumen final con **«Si conferma»** el 16/09/2026, mensaje `9886d004`
de la sesión `2026-09-16T10-53-30-845Z_01a0a9d9-af5c-70dc-9d3b-d5aee3d1124d.jsonl`.

- Objetivo: ≤150 s de **reloj** con `--jobs 8`, todavía no medido.
- Gate: `quick` actual + todo `test_kernel` + los diez e2e enumerados en el spec.
- `full`: todos los tests actuales; obligatorio antes de PRs de runner/harness y release.
  PRs solo de documentación: gate rápido.
- Se acepta detección diferida en `full` de variantes fuera de la muestra del gate.
- No borrar, fusionar ni migrar masivamente los tests por la matriz de líneas.

El 10,6 % de candidatos del 03 no prueba redundancia de comportamiento. Sus 73 casos
restantes no tienen cobertura exclusiva demostrada. El spec documenta también que son
97 archivos por caso más un resumen, y que el ahorro de 416 s era hipotético.

## Frontier
Decisión y artefacto completados localmente; **cierre canónico no acreditado**. `ticket-list`
sigue mostrando dependencias 02/03 abiertas y `lifecycle: unknown`. Este registro aporta la
evidencia humana para el runner, pero no concede integración, merge ni exención de gates.

## Step-by-Step Implementation Plan
1. Consultar las medidas y sus límites de 02/03.
2. Entrevistar y confirmar el resumen final antes de escribir.
3. Registrar el contrato, actualizar el mapa y pasar la reformulación del 06 a `to-tickets`.

## Testing Plan
- Manual: comprobar correspondencia entre decisiones confirmadas y spec/mapa.
- Estático: verificar los diez identificadores y enlaces recíprocos mediante el contrato
  canónico. No se afirma haber ejecutado el nuevo gate.

## Out of Scope
- Implementar perfiles o modificar tests: responsabilidad del ticket 06 reformulado.
- Autorizar merge o simular estados de finalización del runner.

```
