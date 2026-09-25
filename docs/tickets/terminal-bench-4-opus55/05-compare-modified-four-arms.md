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
El piloto previo consumió 3/3 starts con solo un resultado del verifier (reward 0) y dos errores sin recibos Pi. TBF-03 mantiene criterios de coste/recibos sin satisfacer: **no** se declara su completion. TBF-05 utilizó autorización independiente y dos reservas de $60 solo para admisión, sin reescribir aquellos eventos. El método quedó congelado en `add93366cbab9811f8ae2fce1f497505730cc8f1` con CI verde antes del primer start. **12/12 starts, cero retries:** diez decisiones Harbor (una reward 1, nueve reward 0), dos c3a sin decisión por JevFailure antes de petición Jev. Los doce costes modificados son estimaciones atribuibles, $3.406283852 en total incluyendo $0.000176652 Jev; dos costes del piloto estándar siguen desconocidos. El ledger fuera de Git tiene SHA-256 `6ae0764ffc7978f6427e5b23d315bfa3d9085036370e4fc75269008ad7ea13a8`. El [informe](../../../benchmarks/terminal-bench-4-opus55/comparison-results.md) conserva la tabla y las diferencias metodológicas. Ningún score ausente equivale a cero; no hay autorización de nuevo start o merge.

## Step-by-Step Implementation Plan
1. Implementar test-first el timeout dentro del sandbox y journaling de uso/fallos; preservar toda evidencia anterior.
2. Implementar el contrato de fases/smoke público y ledger de lote con límites comunes, snapshots congelados y Jev aislado en host. Reconstruir y revalidar las imágenes Git y el verifier original.
3. Revisar, pasar QA/CI del head exacto, leer de vuelta el mandato y compromiso de proyecto, reservar y ejecutar solo las 12 celdas en serie; incertidumbre nueva detiene el lote.
4. Reducir y etiquetar los resultados como harness local modificado.

## Testing Plan
Pruebas offline del sandbox y política de coste; pruebas live solo dentro del nuevo lote autorizado, sin asumir equivalencia con el piloto estándar.

## Out of Scope
- Reetiquetar el piloto estándar, leer tests/soluciones ocultas o publicar en leaderboard.
