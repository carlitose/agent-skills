---
ticket_schema: 1
ticket_id: "TBF-04"
execution_mode: HITL
blocked_by:
  - "TBF-03"
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
Bloqueado por TBF-03 y por un **nuevo lote autorizado** tras el informe piloto. El techo de $1.000 no es por sí solo permiso para ejecutar el set completo.

## Step-by-Step Implementation Plan
1. Analizar costes piloto, seleccionar un lote acotado sin superar saldo y obtener autorización específica antes de gastos.
2. Ejecutar solo intentos estándar autorizados y reconciliar consumo tras cada uno; si el dataset o configuración deriva, detener y revalidar.
3. Reducir por tarea, intentos y cobertura; separar métricas comparables de exclusiones y gates.
4. Entregar el informe local con evidencia de cada afirmación y necesidad de otro lote, sin mutación en proveedor externo.

## Testing Plan
Comprobar aritmética del saldo y el nuevo número de intentos autorizado sobre recibos originales; probar explícitamente parcialidad, exclusiones y costo desconocido. Verificar que el benchmark no se lanzó en ausencia del nuevo mandato.

## Out of Scope
- Usar el mandato del piloto para continuar, aumentar automáticamente el techo o integrar un resultado parcial como puntuación del índice público.
