---
ticket_schema: 1
ticket_id: "TBF-04"
execution_mode: HITL
blocked_by:
  - "TBF-06"
---

# TBF-04 — Medir el set completo solo tras una nueva autorización

## Artifact Graph
- Artifact ID: `ticket:terminal-bench-4-opus55:04`
- Role: `ticket`
- Parent: [terminal-bench-4-opus55.md](../../specs/terminal-bench-4-opus55.md)

## Parent Spec
[terminal-bench-4-opus55.md](../../specs/terminal-bench-4-opus55.md)

## What to Build
Si el piloto **Harbor estándar/Pi bare** demuestra viabilidad y coste, solicitar autorización humana explícita para **cada nuevo lote** del set completo original, con imagen y verificador originales, dentro del techo acumulado $1.000 incluido el piloto. El tamaño y número de intentos full son decisiones futuras, no se infieren del antiguo diseño de cuatro brazos. Publicar solo un informe local que declare cobertura, tasa de éxito, coste y tiempo sin simular tareas ausentes ni convertir resultados piloto en full a posteriori.

## Acceptance Criteria
- [x] Antes del primer start full existe un nuevo mandato explícito, con tareas, agente Pi bare, número de intentos, exclusiones, binding original y saldo del techo $1.000; el permiso del piloto no se reutiliza.
- [x] El dataset completo tiene un manifiesto cerrado y las tareas GPU/no ejecutables constan como cobertura perdida, no se reemplazan.
- [x] Cada intento autorizado conserva identidad, verifier result, tokens, coste del modelo, tiempo y errores; un gate consume start y dinero sin retry tácito.
- [x] Si el techo no cubre todas las celdas previstas, el trabajo se detiene y el informe dice `partial`, o se consulta al humano por nueva autorización. Nunca se afirma un resultado full a partir de cobertura parcial.
- [x] El informe estándar no atribuye resultados al harness Git de TBF-05 ni publica en un leaderboard.

## Frontier
**Completado** en ejecución skills-only. Resultado: **15/63 tasks puntuados superados** (Pi bare, `openai-codex/gpt-6-sol` `high`, una repetición, 63 de 66 tasks, GPU excluidos como cobertura perdida) — [informe](../../../benchmarks/terminal-bench-4-opus55/standard-full-results.md). Criterios: (1) mandato explícito «Sì, 63 task $150» y después «supera tutti i budget tanto ho token falt» (tokens flat-rate): el techo $1.000 queda sustituido por decisión del usuario y los USD son estimaciones; (2) manifest cerrado y 3 tasks GPU declarados en `excluded_tasks`; (3) cada intento conserva result.json de Harbor, recibo, journal, tokens, coste y errores; los 4 reintentos no son tácitos sino la regla explícita del usuario para fallos de infraestructura, con lote, autoridad y ledger propios y el intento original intacto; (4) el informe dice `partial` (63/66); (5) no mezcla TBF-05 ni publica en leaderboard. 67 intentos, $42,0070 estimados conocidos y 2 intentos de coste desconocido (desconexión del proveedor). Lote A (2 starts con límite de 48 peticiones) se informa aparte, sin puntuar. Movido a `done/` sin recibo del runner.

Historia previa del ticket:

**Mandato nuevo (2026-09-25, elección explícita del usuario «Sì, 63 task $150»):** 63 tasks CPU (los 66 del manifest menos `fp8-rmsnorm-gemm`, `jax-speedrun-gpu`, `math-eval-grader`, declarados en `excluded_tasks` como cobertura perdida), Pi bare, `openai-codex/gpt-6-sol` `high`, imágenes/instrucciones/verifiers originales, **una repetición**, sin retry, techo de lote **$150 estimados**, reserva por celda en curso, stop ante cualquier coste desconocido nuevo, Docker local en el host Windows del operador. El resultado máximo es **parcial 63/66**, nunca full. Requisito previo: TBF-06 con CI verde en el head exacto. TBF-03 queda abierto por decisión del usuario: sus dos costes no son recuperables (sesión Pi en memoria), y el mandato se dio conociendo ese estado.

**Actualización flat-rate (2026-09-25, usuario: «supera tutti i budget tanto ho token flat»):** los tokens son de tarifa plana, así que los USD son estimaciones y ningún presupuesto limita el lote. El lote A (con límite de 48 peticiones) se detuvo tras dos celdas: en la primera el agente agotó las 48 peticiones y Harbor no ejecutó el verifier. El lote B repite los mismos 63 tasks con política declarada (1.000 peticiones y $9.000 estimados por start como techo de seguridad, coste desconocido registrado sin bloquear, hasta tres celdas en paralelo) y verifier de Harbor también tras fallos del agente. No se añaden tasks GPU ni repeticiones; ambos lotes se informan por separado.

**Fallos de infraestructura se repiten (usuario, 2026-09-25):** un error del agente cuenta; un fallo del harness, del proveedor del modelo o de otro factor ajeno al trabajo del agente se repite en un lote de reintento separado, como máximo dos veces por celda, conservando el intento original. Clasificación con `retry_classification.py`; verifiers sin red con `no_network_docker:NoNetworkDockerEnvironment`. El informe da por celda el primer intento no infraestructural.

Antes del mandato: bloqueado por TBF-06, entorno capaz de los 66 tasks (incluidos GPU) y un **nuevo lote autorizado** con repeticiones explícitas tras el informe piloto. TBF-03 aporta evidencia histórica incompleta, no una completion inventada. El techo de $1.000 no es por sí solo permiso para ejecutar el set completo. Compromiso de admisión previo $123.58286105200000007, saldo máximo teórico $876.41713894799999993; 66 starts × $57 de reserva individual suman $3.762 en el peor caso, **no una predicción de factura**. La admisión secuencial libera reservas no usadas, pero no garantiza terminar el set bajo ese techo. El host Docker actual no demuestra GPU para las tres tareas GPU. Antes del launch se necesitan un mandato nuevo, repetición explícita, entorno GPU, proyección de modelo + infraestructura y política de stop/partial; no aumentar el techo ni bajar límites en silencio.

## Step-by-Step Implementation Plan
1. Analizar costes piloto, seleccionar un lote acotado sin superar saldo y obtener autorización específica antes de gastos.
2. Ejecutar solo intentos estándar autorizados y reconciliar consumo tras cada uno; si el dataset o configuración deriva, detener y revalidar.
3. Reducir por tarea, intentos y cobertura; separar métricas comparables de exclusiones y gates.
4. Entregar el informe local con evidencia de cada afirmación y necesidad de otro lote, sin mutación en proveedor externo.

## Testing Plan
Comprobar aritmética del saldo y el nuevo número de intentos autorizado sobre recibos originales; probar explícitamente parcialidad, exclusiones y costo desconocido. Verificar que el benchmark no se lanzó en ausencia del nuevo mandato.

## Out of Scope
- Usar el mandato del piloto para continuar, aumentar automáticamente el techo o integrar un resultado parcial como puntuación del índice público.
