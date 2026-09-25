---
type: source
title: "TBF-02 — Conectar Pi bare al task Harbor original"
identity_key: ticket:terminal-bench-4-opus55/TBF-02
identity_strength: stable
source_path: docs/tickets/terminal-bench-4-opus55/done/02-bridge-four-arms-to-harbor.md
source_digest: sha256:89788ed7c3d487589808ba2d096748b670d708b8497f89e2f310ac5bfcee727c
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-24
created_provenance: git-commit
disposition_changed: 2026-09-25
disposition_changed_provenance: git-rename
---

# TBF-02 — Conectar Pi bare al task Harbor original

Compiled from `docs/tickets/terminal-bench-4-opus55/done/02-bridge-four-arms-to-harbor.md`. Identity is `ticket:terminal-bench-4-opus55/TBF-02`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-24** via `git-commit`
- Disposition changed: **2026-09-25** via `git-rename`

## Graph

- Parent source: [[sources/artifact-terminal-bench-4-opus55]]
- Blocked by: [[sources/ticket-terminal-bench-4-opus55-tbf-01]] — `ticket:terminal-bench-4-opus55/TBF-01`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-terminal-bench-4-opus55-tbf-02.md","payload_bytes":4435,"payload_sha256":"89788ed7c3d487589808ba2d096748b670d708b8497f89e2f310ac5bfcee727c"}],"payload_bytes":4435,"payload_sha256":"89788ed7c3d487589808ba2d096748b670d708b8497f89e2f310ac5bfcee727c","schema":1,"source_digest":"sha256:89788ed7c3d487589808ba2d096748b670d708b8497f89e2f310ac5bfcee727c","source_identity":"ticket:terminal-bench-4-opus55/TBF-02","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":4435,"payload_sha256":"89788ed7c3d487589808ba2d096748b670d708b8497f89e2f310ac5bfcee727c","schema":1,"source_digest":"sha256:89788ed7c3d487589808ba2d096748b670d708b8497f89e2f310ac5bfcee727c","source_identity":"ticket:terminal-bench-4-opus55/TBF-02"} -->
```markdown
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
- [x] Harbor carga el adaptador por su ruta pública; `setup`/`run` y el tool Pi→`environment.exec` pasan pruebas offline sin solicitud de modelo.
- [x] Harbor carga las tres tareas originales con imagen de agente, instrucción, timeout y verificador separados fijados; el brazo estándar no inicializa Git ni usa imágenes derivadas.
- [x] Una prueba en contenedor disposable sin mounts demuestra que operaciones Pi afectan solo al sandbox, no al checkout host; tareas, claves y logs no se pasan como tools del modelo.
- [x] Catálogo/OAuth confirman `openai-codex/gpt-6-sol` y `high` sin completion; instrucciones y límites de task coinciden con el manifiesto fijado.
- [x] La clave del proveedor queda en el proceso host; la clave Jev no se carga para este brazo. Una prueba de proceso hijo cubre la herencia de secretos sin mostrar sus valores.
- [x] El límite de tres starts/$250 se admite con un ledger ligado al método original y a recibos de coste/tokens atribuibles; una duda, presupuesto agotado o fallo de cierre detiene la siguiente solicitud y el siguiente start. No afirmar una factura si solo hay estimación. *(Admisión y stop cumplidos en el piloto; recibos en fallos **no**: dos starts sin recibo, historia abierta en TBF-03; corregido para futuras ejecuciones por TBF-06.)*

## Frontier
**Completado** e integrado por PR #347 (merge `513c860e0775cea4c302150d662b98497d9034b1`; CI exacto verde en `454bb101…` y `6457b228…`). Evidencia por criterio: carga Harbor, tool `sandbox_exec` y tareas originales en `test_standard_pi_agent.py`/`test_harbor_pi_agent.py`/`standard-pilot.json`; frontera de sandbox y herencia de secretos en tests de proceso hijo sin modelo; catálogo/OAuth sin completion en la spec. Último criterio: la admisión y el stop funcionaron en el piloto (el ledger bloqueó el tercer start hasta la excepción humana explícita), pero **dos starts fallidos del piloto quedaron sin recibo** porque este puente guardaba la sesión Pi solo en memoria; ese defecto queda como historia abierta en TBF-03 y se corrigió para ejecuciones futuras con el journal durable del adapter de [TBF-06](06-adapt-original-harbor-to-pi.md) (PR #348), que usa el lote TBF-04. Movido a `done/` en ejecución skills-only, sin recibo de runner.

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

```
