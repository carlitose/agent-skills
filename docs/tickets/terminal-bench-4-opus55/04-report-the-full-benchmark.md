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
- [ ] Antes del primer start full existe un nuevo mandato explícito, con tareas, agente Pi bare, número de intentos, exclusiones, binding original y saldo del techo $1.000; el permiso del piloto no se reutiliza.
- [ ] El dataset completo tiene un manifiesto cerrado y las tareas GPU/no ejecutables constan como cobertura perdida, no se reemplazan.
- [ ] Cada intento autorizado conserva identidad, verifier result, tokens, coste del modelo, tiempo y errores; un gate consume start y dinero sin retry tácito.
- [ ] Si el techo no cubre todas las celdas previstas, el trabajo se detiene y el informe dice `partial`, o se consulta al humano por nueva autorización. Nunca se afirma un resultado full a partir de cobertura parcial.
- [ ] El informe estándar no atribuye resultados al harness Git de TBF-05 ni publica en un leaderboard.

## Frontier
**Mandato nuevo (2026-09-25, elección explícita del usuario «Sì, 63 task $150»):** 63 tasks CPU (los 66 del manifest menos `fp8-rmsnorm-gemm`, `jax-speedrun-gpu`, `math-eval-grader`, declarados en `excluded_tasks` como cobertura perdida), Pi bare, `openai-codex/gpt-6-sol` `high`, imágenes/instrucciones/verifiers originales, **una repetición**, sin retry, techo de lote **$150 estimados**, reserva por celda en curso, stop ante cualquier coste desconocido nuevo, Docker local en el host Windows del operador. El resultado máximo es **parcial 63/66**, nunca full. Requisito previo: TBF-06 con CI verde en el head exacto. TBF-03 queda abierto por decisión del usuario: sus dos costes no son recuperables (sesión Pi en memoria), y el mandato se dio conociendo ese estado.

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
