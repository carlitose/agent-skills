---
ticket_schema: 1
ticket_id: "TBF-06"
execution_mode: AFK
blocked_by: []
---

# TBF-06 — Adaptar Harbor original a nuestro Pi

## Artifact Graph
- Artifact ID: `ticket:terminal-bench-4-opus55:06`
- Role: `ticket`
- Parent: [terminal-bench-4-opus55.md](../../specs/terminal-bench-4-opus55.md)

## Parent Spec
[terminal-bench-4-opus55.md](../../specs/terminal-bench-4-opus55.md)

## What to Build
Implementar un adapter nativo Harbor/Pi bare para cualquiera de los 66 tasks congelados sin overlay Git, smoke añadido, Jev ni driver. Reutilizar el transporte con timeout dentro del sandbox y journaling durable que ya funcionó; no repetir el puente roto del piloto. La selección humana del set completo autoriza esta preparación, no nuevos starts pagados. Contrato de uso: [adapter original](../../../benchmarks/terminal-bench-4-opus55/standard-full.md).

## Acceptance Criteria
- [x] Identidad de task/configuración original, instrucción Harbor y modelo verificadas antes de iniciar Pi; task fuera del piloto aceptado si pertenece al manifest (fixture no piloto; solo `html-js-filter` original observado en setup real).
- [x] Un lote externo nuevo liga mandato, manifest, presupuesto, repeticiones y evidencia previa; ledger pasivo sin scheduler, una celda por task/repetición, sin retry ni reutilización de los lotes consumidos. El hash del archivo no constituye consentimiento humano: su validez se comprueba externamente antes de cualquier start.
- [x] Pi recibe solo instrucción original y tool sandbox; no bootstrap Git, helper público, suite local ni llamada al verifier/Jev dentro del agente. No asumir `/app` ni borrar Git que ya estuviera presente.
- [x] Timeout retorna código de tool; pérdida de transporte detiene el proceso. Uso conocido se conserva en error y solicitud pendiente conserva coste desconocido, bloqueando nuevos starts.
- [x] Pruebas offline ejercitan un task no piloto, binding alterado, error/timeout y recibos, usando streams falsos; no trial/modelo pagado.
- [x] Documentar uso del adapter y limitaciones: set 66 con GPU, ejemplo oficial k=5 sin convertirlo en permiso, política de 48 requests/$57 como límite del agente, no resultado full ni aprobación leaderboard.

## Frontier
Preparación inline autorizada por «prendi sto harness sto coso cambialo per che possa funzionare con il nostro». Base de implementación `6457b228e22ff7426d49bb836f63224632374c41`. Revisión shared-context, no delegación, máximo dos correcciones de calidad; preservar evidencia de cada intento. TBF-03/05 aportan observaciones históricas, no bloquean reparar el adapter ni transfieren starts. El lanzamiento TBF-04 sigue separado y bloqueado por entorno GPU, presupuesto/mandato nuevo, binding del set completo y CI. Evidencia local: 23 Python y 25 Node PASS sobre el candidato, Harbor install-only original con cero starts/requests y auditoría local en `.tbf-env/standard-full-preparation/`; no equivalencia a 66 ejecuciones ni verifiers. Continuación skills-only en el host Windows del operador sobre main `513c860` (árbol idéntico a la base): se añadió `excluded_tasks` test-first para vincular el mandato TBF-04 de 63 tasks (RED 2 fallos, GREEN 103 Python + 25 Node), y los 66 `task.toml`/`instruction.md` descargados coinciden con el manifest. **Completado** e integrado por PR #348: head `62ea9f54748588df23c5a736b68f582f38d9d971` con CI exacto verde (run 36129549485, `local-profile` y seis shards), merge `5c79d13c36385b621f5849ab7daed5533d12727c` con árbol idéntico al candidato verificado `b20b958c`. Verification bundle `implementation-complete`, release `eligible`; gates GPU/compatibilidad abiertos y no críticos para el adapter, propiedad de TBF-04. Movido a `done/` en ejecución skills-only, sin recibo de runner.

## Step-by-Step Implementation Plan
1. Escribir pruebas RED del adapter original y admisión genérica, conservando contratos históricos.
2. Reutilizar transporte/accounting; añadir binding original y un único agente Pi bare para una celda.
3. Ejecutar tests causales, simplificación, revisión, QA y auditoría inline; conservar gates externos.

## Testing Plan
Tests Python/Node sin proveedor y prueba de conexión real al endpoint sin request modelo; fixture de entorno y ledger; setup Harbor original install-only si viable. No descarga de imágenes masiva, sandbox cloud, GPU pagada, ni inferencia. Verificar en el árbol entregado links y ticket canónico. CI de head exacto sigue requerida antes de futuros starts.

## Out of Scope
- Lanzar, reintentar o autorizar modelos; instalar cloud/GPU; cambiar dataset, recursos o verifier; leer soluciones/tests ocultos.
- Runner, scheduler, cuatro brazos, Jev, leaderboard, merge o nueva instalación Pi.
