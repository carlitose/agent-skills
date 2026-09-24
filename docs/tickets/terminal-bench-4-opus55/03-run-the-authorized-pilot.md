---
ticket_schema: 1
ticket_id: "TBF-03"
execution_mode: AFK
blocked_by:
  - "TBF-01"
  - "TBF-02"
---

# TBF-03 — Ejecutar solo el piloto autorizado de doce intentos

## Artifact Graph
- Artifact ID: `ticket:terminal-bench-4-opus55:03`
- Role: `ticket`
- Parent: [terminal-bench-4-opus55.md](../../specs/terminal-bench-4-opus55.md)

## Parent Spec
[terminal-bench-4-opus55.md](../../specs/terminal-bench-4-opus55.md)

## What to Build
Con las pruebas TBF-01/02 completadas, ejecutar los tres nombres de tarea congelados una vez en cada uno de los cuatro brazos, como máximo doce starts. La autoridad humana de este lote es explícita: máximo acumulativo $250 incluidos intentos fallidos, sin reintentos automáticos, excepción para ticket-driver c1a/c3a **solo en este piloto**. El runner antiguo sigue suspendido. Reducir resultados para decidir si continuar hacia el set completo, sin iniciarlo.

## Acceptance Criteria
- [ ] El preflight liga cada start a dataset/ref/task/arm/modelo, presupuesto restante y evidencia de TBF-01/02 antes de gastar.
- [ ] Como máximo 12 start únicos: tres tareas × cuatro brazos, una tentativa por celda; gate/fracaso consumen su start, jamás se reetiquetan o sustituyen automáticamente.
- [ ] El coste acumulado observado y reservado del lote no supera $250; el coste de full+piloto queda por debajo del techo $1.000; una duda sobre coste o disponibilidad detiene el siguiente start.
- [ ] Quedan resultado del verificador, estado de ejecución, tiempo, tokens, coste del modelo y exposición de credenciales por intento, incluidos fallos.
- [ ] Informe piloto contrasta el coste real frente al saldo del techo total, declara paridad/perdida de tareas GPU y propone continuar o detener; no corre ninguna tarea del lote completo.

## Frontier
Bloqueado por TBF-01 y TBF-02; autorización humana para este único lote ya consta. Cualquier cambio de scope, gastos >$250 o sustitución de un intento fallido requiere autorización nueva. La disponibilidad efectiva de credenciales y un puente fiel son gates técnicos.

## Step-by-Step Implementation Plan
1. Revalidar versión/manifest, sandbox, acceso al modelo, aislamiento de claves, derechos del lote y presupuesto restante.
2. Reservar y arrancar secuencialmente un intento identificable por tarea/brazo; observar cada salida antes del siguiente.
3. Registrar de forma inmutable cada fallo/gate y todo gasto; nunca reintentar sin nueva autorización.
4. Analizar resultados y costes reales; detenerse antes del set completo.

## Testing Plan
Comparar el ledger y los recibos de cada intento con la fuente original del modelo y verificador. Validar cuentas 0–12 y budget; un fallo técnico permanece visible. No equivaler `valid` con tarea aprobada.

## Out of Scope
- Los intentos completos tres-por-tarea, reutilizar outputs corregidos o publicar resultados en un leaderboard.
