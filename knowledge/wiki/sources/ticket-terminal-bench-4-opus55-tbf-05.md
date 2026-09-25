---
type: source
title: "TBF-05 — Comparar cuatro brazos en un harness local modificado"
identity_key: ticket:terminal-bench-4-opus55/TBF-05
identity_strength: stable
source_path: docs/tickets/terminal-bench-4-opus55/done/05-compare-modified-four-arms.md
source_digest: sha256:2f36e7b1bd3c9c28f55a11ba9c09890a5a7605ec73f038d504fa503059325d60
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-24
created_provenance: git-commit
disposition_changed: 2026-09-25
disposition_changed_provenance: git-rename
---

# TBF-05 — Comparar cuatro brazos en un harness local modificado

Compiled from `docs/tickets/terminal-bench-4-opus55/done/05-compare-modified-four-arms.md`. Identity is `ticket:terminal-bench-4-opus55/TBF-05`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-24** via `git-commit`
- Disposition changed: **2026-09-25** via `git-rename`

## Graph

- Parent source: [[sources/artifact-terminal-bench-4-opus55]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-terminal-bench-4-opus55-tbf-05.md","payload_bytes":4666,"payload_sha256":"2f36e7b1bd3c9c28f55a11ba9c09890a5a7605ec73f038d504fa503059325d60"}],"payload_bytes":4666,"payload_sha256":"2f36e7b1bd3c9c28f55a11ba9c09890a5a7605ec73f038d504fa503059325d60","schema":1,"source_digest":"sha256:2f36e7b1bd3c9c28f55a11ba9c09890a5a7605ec73f038d504fa503059325d60","source_identity":"ticket:terminal-bench-4-opus55/TBF-05","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":4666,"payload_sha256":"2f36e7b1bd3c9c28f55a11ba9c09890a5a7605ec73f038d504fa503059325d60","schema":1,"source_digest":"sha256:2f36e7b1bd3c9c28f55a11ba9c09890a5a7605ec73f038d504fa503059325d60","source_identity":"ticket:terminal-bench-4-opus55/TBF-05"} -->
```markdown
---
ticket_schema: 1
ticket_id: "TBF-05"
execution_mode: HITL
blocked_by: []
---

# TBF-05 — Comparar cuatro brazos en un harness local modificado

## Artifact Graph
- Artifact ID: `ticket:terminal-bench-4-opus55:05`
- Role: `ticket`
- Parent: [terminal-bench-4-opus55.md](../../specs/terminal-bench-4-opus55.md)

## Parent Spec
[terminal-bench-4-opus55.md](../../specs/terminal-bench-4-opus55.md)

## What to Build
Tras agotar los tres starts del piloto estándar y conservar sus errores/costes desconocidos, ejecutar el nuevo lote expresamente autorizado: 12 starts (tres tasks × Pi bare, skills-only, c1a adaptado y c3a adaptado), $720 estimados incluidos juicios Jev, en serie y sin retry. Seguir el contrato del apartado «Authorized modified comparison contract» de la spec: corregir primero timeout y recibos, y comparar todos los brazos sobre el mismo overlay Git reconstruido. `openai-codex/gpt-6-sol` y el verificador separado de Harbor permanecen fijados. Esta comparación es un experimento **local modificado**, no un score Terminal-Bench estándar ni una reproducción del ticket-driver original si las fases o tests cambian.

## Acceptance Criteria
- [x] El mandato nuevo cubre 12 starts/$720 estimados y acepta ese riesgo; la admisión del proyecto mantiene $120.17657720000000002 del piloto ($60 asumidos por cada error), sin declarar costes reales conocidos ni reciclar starts.
- [x] El overlay, tool boundary, credenciales y límites son iguales cuando se afirma paridad; los cambios inevitables quedaron nombrados antes de ejecutar.
- [x] Las fases adaptadas siguen la spec: builder con skills, smoke público no exhaustivo, fingerprint Git y, para c3a, juicios tipados/riesgo/revisión dirigida. Los smoke checks derivan solo del contrato público y sample de desarrollo; no equivalen a la suite original ni al verifier. Dos c3a fallaron antes de un juicio Jev y carecen de score, sin aprobar falsamente el gate.
- [x] El timeout del comando se aplica dentro del sandbox y vuelve al modelo como error de tool; el timeout externo no confirmado no se encubre. Cada solicitud y uso atribuible se persiste incrementalmente fuera de Git, incluso en salidas fallidas; solicitudes pendientes mantienen coste desconocido.
- [x] Cada start y gasto se reconcilió con recibos propios; no hubo coste nuevo desconocido ni retry automático.
- [x] El [informe terminal](../../../benchmarks/terminal-bench-4-opus55/comparison-results.md) separa estos resultados del método Harbor original y no publica puntuaciones en un leaderboard.

## Frontier
El piloto previo consumió 3/3 starts con solo un resultado del verifier (reward 0) y dos errores sin recibos Pi. TBF-03 mantiene criterios de coste/recibos sin satisfacer: **no** se declara su completion. TBF-05 utilizó autorización independiente y dos reservas de $60 solo para admisión, sin reescribir aquellos eventos. El método quedó congelado en `add93366cbab9811f8ae2fce1f497505730cc8f1` con CI verde antes del primer start. **12/12 starts, cero retries:** diez decisiones Harbor (una reward 1, nueve reward 0), dos c3a sin decisión por JevFailure antes de petición Jev. Los doce costes modificados son estimaciones atribuibles, $3.406283852 en total incluyendo $0.000176652 Jev; dos costes del piloto estándar siguen desconocidos. El ledger fuera de Git tiene SHA-256 `6ae0764ffc7978f6427e5b23d315bfa3d9085036370e4fc75269008ad7ea13a8`. El [informe](../../../benchmarks/terminal-bench-4-opus55/comparison-results.md) conserva la tabla y las diferencias metodológicas. Ningún score ausente equivale a cero; no hay autorización de nuevo start. **Completado** e integrado después por PR #347 (merge `513c860e0775cea4c302150d662b98497d9034b1`); movido a `done/` en ejecución skills-only, sin recibo de runner.

## Step-by-Step Implementation Plan
1. Implementar test-first el timeout dentro del sandbox y journaling de uso/fallos; preservar toda evidencia anterior.
2. Implementar el contrato de fases/smoke público y ledger de lote con límites comunes, snapshots congelados y Jev aislado en host. Reconstruir y revalidar las imágenes Git y el verifier original.
3. Revisar, pasar QA/CI del head exacto, leer de vuelta el mandato y compromiso de proyecto, reservar y ejecutar solo las 12 celdas en serie; incertidumbre nueva detiene el lote.
4. Reducir y etiquetar los resultados como harness local modificado.

## Testing Plan
Pruebas offline del sandbox y política de coste; pruebas live solo dentro del nuevo lote autorizado, sin asumir equivalencia con el piloto estándar.

## Out of Scope
- Reetiquetar el piloto estándar, leer tests/soluciones ocultas o publicar en leaderboard.

```
