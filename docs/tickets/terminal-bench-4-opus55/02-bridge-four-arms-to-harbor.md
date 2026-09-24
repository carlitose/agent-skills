---
ticket_schema: 1
ticket_id: "TBF-02"
execution_mode: AFK
blocked_by:
  - "TBF-01"
---

# TBF-02 — Conectar Pi bare al task Harbor original

## Artifact Graph
- Artifact ID: `ticket:terminal-bench-4-opus55:02`
- Role: `ticket`
- Parent: [terminal-bench-4-opus55.md](../../specs/terminal-bench-4-opus55.md)

## Parent Spec
[terminal-bench-4-opus55.md](../../specs/terminal-bench-4-opus55.md)

## What to Build
Preparar un único brazo Pi bare con `openai-codex/gpt-6-sol`, razonamiento `high`, sobre las tres tareas originales fijadas en TBF-01: mismas imágenes, instrucciones, límites y verificadores separados de Harbor, **sin** overlay Git, skills ni ticket-driver. El adaptador `BaseAgent` externo transmite cada operación de shell/fichero únicamente a `environment.exec` del contenedor; credenciales y trayectoria permanecen en el host. Registrar identidad de task/intento, uso atribuible y una guarda de gasto que detenga solicitudes futuras antes del piloto de tres starts. Mantener las imágenes Git ya preparadas como trabajo diferido del futuro TBF-05, no como evidencia de este método.

## Acceptance Criteria
- [ ] Harbor carga el adaptador por su ruta pública; `setup`/`run` y el tool Pi→`environment.exec` pasan pruebas offline sin solicitud de modelo.
- [ ] Harbor carga las tres tareas originales con imagen de agente, instrucción, timeout y verificador separados fijados; el brazo estándar no inicializa Git ni usa imágenes derivadas.
- [ ] Una prueba en contenedor disposable sin mounts demuestra que operaciones Pi afectan solo al sandbox, no al checkout host; tareas, claves y logs no se pasan como tools del modelo.
- [ ] Catálogo/OAuth confirman `openai-codex/gpt-6-sol` y `high` sin completion; instrucciones y límites de task coinciden con el manifiesto fijado.
- [ ] La clave del proveedor queda en el proceso host; la clave Jev no se carga para este brazo. Una prueba de proceso hijo cubre la herencia de secretos sin mostrar sus valores.
- [ ] El límite de tres starts/$250 se admite con un ledger ligado al método original y a recibos de coste/tokens atribuibles; una duda, presupuesto agotado o fallo de cierre detiene la siguiente solicitud y el siguiente start. No afirmar una factura si solo hay estimación.

## Frontier
TBF-01 fijó el dataset y tres tareas, pero su comprobación Opus es histórica. El usuario eligió ahora un **piloto Harbor estándar primero** y separó la comparación Git/cuatro brazos para TBF-05. Las imágenes originales están en cache y las tres tareas se cargan en Harbor; el puente Pi bare llegó a un container disposable sin modelo. `StandardPiHarborAgent` evita Git y comprueba la imagen original; el binding de las tres tareas coteja instrucciones efectivas de Harbor, imagen y verificador separado. La sesión Pi atravesó una guarda de presupuesto con stream sintético sin llamada al proveedor; un inicio ligado al ledger y la reconciliación de resultado/recibo se ensayaron sin modelo. No equivale a una factura ni a una evaluación real: faltan revisión, QA y readback previo al primer trial; por eso todavía no se inicia ningún intento. Las imágenes derivadas, Jev y el driver conservan su evidencia sin convertirse en requisitos de TBF-03.

## Step-by-Step Implementation Plan
1. Bind de identidad a tres task originales y modelo GPT; conservar datos históricos y overlay diferido sin mezclarlos.
2. Separar el modo estándar Pi bare en el adaptador: `setup` no muta `/app`; Pi solo expone `sandbox_exec` hacia Harbor.
3. Probar frontera de tool, credenciales y carga de las tres tareas sin juicio pagado ni verifier oculto.
4. Implementar y validar ledger de tres celdas, admisión y parada de gasto con recibos atribuibles; pasar a TBF-03 solo si las guardas observadas son suficientes.

## Testing Plan
Tests offline de carga Harbor, tool bridging, aislamiento, admisión/presupuesto y costos desconocidos; una tarea real consumiría uno de los tres starts y pertenece solamente a TBF-03.

## Out of Scope
- Instalar Pi dentro de contenedores, leer tests ocultos, llamar al modelo durante checks offline o alterar imágenes/instrucciones/verificador del método estándar.
- Ejecutar el viejo runner, gastar intentos de los cuatro brazos o afirmar un score de leaderboard.
