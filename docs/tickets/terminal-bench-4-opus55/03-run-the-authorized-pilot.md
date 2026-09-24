---
ticket_schema: 1
ticket_id: "TBF-03"
execution_mode: AFK
blocked_by:
  - "TBF-01"
  - "TBF-02"
---

# TBF-03 — Ejecutar tres intentos Harbor estándar

## Artifact Graph
- Artifact ID: `ticket:terminal-bench-4-opus55:03`
- Role: `ticket`
- Parent: [terminal-bench-4-opus55.md](../../specs/terminal-bench-4-opus55.md)

## Parent Spec
[terminal-bench-4-opus55.md](../../specs/terminal-bench-4-opus55.md)

## What to Build
Tras validar TBF-02, ejecutar una vez cada uno de los tres tasks originales congelados con **Pi bare, `openai-codex/gpt-6-sol`, `high`**, sin overlay Git, habilidades ni ticket-driver. Harbor conserva imagen, instrucción y verificador separados originales. Máximo **tres starts** y **$250 acumulados** incluidos fallos, sin retry ni smoke pagado adicional. Este nuevo lote estándar sustituye el plan de doce celdas sin transferir starts no usados al posterior experimento de cuatro brazos. Registrar y analizar resultados para decidir si proponer un lote full distinto; no iniciarlo aquí ni publicar un score oficial.

## Acceptance Criteria
- [ ] Cada start liga dataset/ref/task original/imagen/verificador, Pi bare, `openai-codex/gpt-6-sol`, `high`, límites y evidencia de TBF-02; el chequeo Opus y las imágenes Git no suplen este binding.
- [ ] Como máximo tres starts únicos, uno por task; un gate/fallo consume su start y no se reintenta ni sustituye.
- [ ] El coste acumulado observado y reservado queda bajo $250, con presupuesto restante conocido antes de cada start y corte efectivo de solicitudes posteriores; un coste incierto detiene el lote. El techo del proyecto permanece $1.000, sin autorizar un full run.
- [ ] Cada intento conserva verifier original, estado de ejecución, tiempo, tokens, costo del modelo, recibos atribuibles y evidencia de aislamiento, incluidos fallos.
- [ ] El informe declara resultado por task, exclusiones GPU y cobertura de 3/66, gasto y decisión de proponer o detener un lote estándar posterior; no afirma comparación entre cuatro brazos ni score de leaderboard.

## Frontier
Bloqueado por evidencia integrada de TBF-01 y un TBF-02 validado **para el método estándar**. La decisión posterior del usuario eligió tres tareas Pi bare antes de estudiar los cuatro brazos con un harness modificado. El lote anterior de doce celdas no se suma a estos tres starts: cero consumidos hasta la fecha, método y autoridad nuevos que deben leerse de vuelta antes del primer start. Falta demostrar control y reconciliación de gasto modelo bajo $250; catálogo/OAuth no son facturas. Jev, Git y suites locales del driver no participan. No iniciar un trial ni asumir `done` si falta cualquiera de estos gates.

## Step-by-Step Implementation Plan
1. Revalidar manifest, imagen original/verifier, credenciales host, TBF-02, límites y saldo antes de cada start.
2. Reservar y arrancar una tarea Pi bare a la vez, con límite de solicitud y una identidad inmutable.
3. Reconciliar recibos y gastos, incluyendo fallo o incertidumbre, antes de admitir la siguiente tarea.
4. Reducir resultados originales y costes; no iniciar el set completo ni el experimento modificado.

## Testing Plan
Comparar ledger y recibos con identidad/modelo/verifier originales; validar cuentas 0–3, techo, abstención ante coste incierto y que `valid` no equivale a tarea aprobada.

## Out of Scope
- El lote full, Jev, overlay Git, otros brazos, reutilizar outputs corregidos o publicar resultados en un leaderboard.
