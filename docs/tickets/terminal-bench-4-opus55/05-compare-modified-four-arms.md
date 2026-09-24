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
- [ ] El mandato nuevo cubre 12 starts/$720 estimados y acepta ese riesgo; la admisión del proyecto mantiene $120.17657720000000002 del piloto ($60 asumidos por cada error), sin declarar costes reales conocidos ni reciclar starts.
- [ ] El overlay, tool boundary, credenciales y límites son iguales cuando se afirma paridad; los cambios inevitables quedan nombrados antes de ejecutar.
- [ ] Las fases adaptadas siguen la spec: builder con skills, smoke público no exhaustivo, fingerprint Git y, para c3a, juicios tipados/riesgo/revisión dirigida. Los smoke checks derivan solo del contrato público y sample de desarrollo; no equivalen a la suite original ni al verifier. Una fase imposible o semántica no resuelta sigue como gate.
- [ ] El timeout del comando se aplica dentro del sandbox y vuelve al modelo como error de tool; el timeout externo no confirmado no se encubre. Cada solicitud y uso atribuible se persiste incrementalmente fuera de Git, incluso en salidas fallidas; solicitudes pendientes mantienen coste desconocido.
- [ ] Cada start y gasto se reconcilia con recibos propios; incertidumbre detiene el lote sin retry automático.
- [ ] El informe separa estos resultados del método Harbor original y no publica puntuaciones en un leaderboard.

## Frontier
El piloto previo consumió 3/3 starts con solo un resultado del verifier (reward 0) y dos errores sin recibos Pi. TBF-03 queda con criterios de coste/recibos sin satisfacer: **no** se declara su completion. El usuario autorizó explícitamente este lote separado después del informe terminal, con ambas reservas perdidas como compromiso de admisión; por ello TBF-05 ya no bloquea su ejecución en una falsa completion de TBF-03. No se reescriben sus eventos. La dependencia TBF-03 aporta ese informe terminal, no una aprobación ficticia de las tareas. El contrato modificado está fijado en la spec; antes de gastar faltan corregir el puente, completar/controlar fases y tarifas, reconstruir imágenes, pasar QA y CI del head exacto. El reset Docker autorizado conservó repositorios y recibos host.

## Step-by-Step Implementation Plan
1. Implementar test-first el timeout dentro del sandbox y journaling de uso/fallos; preservar toda evidencia anterior.
2. Implementar el contrato de fases/smoke público y ledger de lote con límites comunes, snapshots congelados y Jev aislado en host. Reconstruir y revalidar las imágenes Git y el verifier original.
3. Revisar, pasar QA/CI del head exacto, leer de vuelta el mandato y compromiso de proyecto, reservar y ejecutar solo las 12 celdas en serie; incertidumbre nueva detiene el lote.
4. Reducir y etiquetar los resultados como harness local modificado.

## Testing Plan
Pruebas offline del sandbox y política de coste; pruebas live solo dentro del nuevo lote autorizado, sin asumir equivalencia con el piloto estándar.

## Out of Scope
- Reetiquetar el piloto estándar, leer tests/soluciones ocultas o publicar en leaderboard.
