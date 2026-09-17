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
