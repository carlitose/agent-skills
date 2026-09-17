---
type: source
title: "Corregir los fixtures Linux y verificar ambos hosts"
identity_key: ticket:linux-suite-fixture-portability/01
identity_strength: stable
source_path: docs/tickets/linux-suite-fixture-portability/done/01-portable-fixtures.md
source_digest: sha256:5c1346666558a9e7f0b2e243ae43736a6be7cd67ce00c5496d39b5a927e37a63
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-17
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
run_id: linux-fixtures-prerequisite
---

# Corregir los fixtures Linux y verificar ambos hosts

Compiled from `docs/tickets/linux-suite-fixture-portability/done/01-portable-fixtures.md`. Identity is `ticket:linux-suite-fixture-portability/01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-17** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-linux-suite-fixture-portability]]

## Run

Completed under autopilot run `linux-fixtures-prerequisite`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-linux-suite-fixture-portability-01.md","payload_bytes":3340,"payload_sha256":"5c1346666558a9e7f0b2e243ae43736a6be7cd67ce00c5496d39b5a927e37a63"}],"payload_bytes":3340,"payload_sha256":"5c1346666558a9e7f0b2e243ae43736a6be7cd67ce00c5496d39b5a927e37a63","schema":1,"source_digest":"sha256:5c1346666558a9e7f0b2e243ae43736a6be7cd67ce00c5496d39b5a927e37a63","source_identity":"ticket:linux-suite-fixture-portability/01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3340,"payload_sha256":"5c1346666558a9e7f0b2e243ae43736a6be7cd67ce00c5496d39b5a927e37a63","schema":1,"source_digest":"sha256:5c1346666558a9e7f0b2e243ae43736a6be7cd67ce00c5496d39b5a927e37a63","source_identity":"ticket:linux-suite-fixture-portability/01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "01"
execution_mode: AFK
blocked_by: []
---

# Corregir los fixtures Linux y verificar ambos hosts

## Artifact Graph
- Artifact ID: `artifact:linux-suite-fixture-portability:01`
- Role: `ticket`
- Parent: [linux-suite-fixture-portability.md](../../specs/linux-suite-fixture-portability.md)

## Parent Spec
[linux-suite-fixture-portability.md](../../specs/linux-suite-fixture-portability.md)

## What to Build
Corregir las cinco causas de fixtures demostradas en el spec, que explican los diez checks
Linux preexistentes. Hacer explícitos los bytes de goldens, el intérprete de filtros Git,
los modos del filesystem anfitrión y la observación exacta de reaping mediante pidfd.

## Acceptance Criteria
- [ ] Los diez checks originales pasan sin editar el wrapper forward ni los hashes golden.
- [ ] LF y CRLF son deterministas; los filtros usan el intérprete actual con quoting seguro.
- [ ] El spy POSIX aplica el modo real y la rama Windows sigue sin llamar a fchmod.
- [ ] El índice y el archivo ejecutable coinciden sin desactivar filemode.
- [ ] El predicado pidfd rechaza vivo/zombie y acepta ESRCH tras wait; no consume wait status.
- [ ] Timeout, cancelación, límite de salida, control vivo, plazos y cleanup se conservan.
- [ ] Los módulos afectados y full --jobs 8 pasan en Linux y Windows sobre el candidato final.
- [ ] Review, QA y verificación registran límites, incluidos macOS no observado y ausencia
  de aislamiento independiente. No se modifica runtime ni se inventa autoridad de entrega.

## Frontier
Ready: alcance y predicado ESRCH confirmados por el usuario. AFK, sin dependencias internas.
La implementación local está autorizada; publicación/merge de este prerrequisito no se
infieren de la autorización del lote principal. Máximo 20 ciclos de calidad.

## Step-by-Step Implementation Plan
1. Preservar el RED registrado y vincular el candidato a la base corregida de revisión.
2. Cambiar exclusivamente los cinco archivos de tests listados en el spec; añadir controles
   negativos y de bytes/modos sin retirar escenarios. Checkpoint: checks focales GREEN.
3. Ejecutar módulos afectados y full en ambos hosts sin bloquear el foreground. Checkpoint:
   recibos completos de cada ejecución y mismo contenido candidato.
4. Congelar, simplificar, revisar, planificar/ejecutar QA y auditar con los contratos canónicos.
   Checkpoint: handoff validado o gates exactos pendientes, nunca un done manual.

## Testing Plan
- Linux nativo WSL: repetir los diez checks de linux-failure-signature-comparison.json;
  ejecutar los cinco módulos afectados y el wrapper forward sin patches diagnósticos.
- Windows nativo: ejecutar esos módulos con sus guardas de plataforma existentes.
- Control pidfd: hijo vivo, salida sin wait, ESRCH después de wait; preservar status propio.
- Ambos hosts: node scripts/test-local.mjs full --jobs 8 con logs y exit code.
- Mantener el límite explícito de macOS no ejecutado. Simulación de ramas no es host nativo.

## Out of Scope
- Runtime, goldens nuevos, eliminación de casos, skips nuevos, retries encubridores o deadlines mayores.
- Instalaciones globales, cambios de configuración global Git y ajustes del contrato de perfiles.
- Publicación, integración, resolución de dependencias o done del lote principal sin sus gates.

```
