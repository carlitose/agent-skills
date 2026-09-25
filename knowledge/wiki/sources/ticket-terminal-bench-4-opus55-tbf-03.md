---
type: source
title: "TBF-03 — Ejecutar tres intentos Harbor estándar"
identity_key: ticket:terminal-bench-4-opus55/TBF-03
identity_strength: stable
source_path: docs/tickets/terminal-bench-4-opus55/canceled/03-run-the-authorized-pilot.md
source_digest: sha256:acc26f4aa0beedbb4b0afa8cbd1d1e39d0678d80ecf67fa7ea4ef4bf03b4c4a6
source_status: present
artefact_kind: ticket
disposition: canceled
created: 2026-05-18
created_provenance: git-commit
disposition_changed: 2026-05-18
disposition_changed_provenance: git-rename
---

# TBF-03 — Ejecutar tres intentos Harbor estándar

Compiled from `docs/tickets/terminal-bench-4-opus55/canceled/03-run-the-authorized-pilot.md`. Identity is `ticket:terminal-bench-4-opus55/TBF-03`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-05-18** via `git-commit`
- Disposition changed: **2026-05-18** via `git-rename`

## Graph

- Parent source: [[sources/artifact-terminal-bench-4-opus55]]
- Blocked by: [[sources/ticket-terminal-bench-4-opus55-tbf-01]] — `ticket:terminal-bench-4-opus55/TBF-01`
- Blocked by: [[sources/ticket-terminal-bench-4-opus55-tbf-02]] — `ticket:terminal-bench-4-opus55/TBF-02`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-terminal-bench-4-opus55-tbf-03.md","payload_bytes":4793,"payload_sha256":"acc26f4aa0beedbb4b0afa8cbd1d1e39d0678d80ecf67fa7ea4ef4bf03b4c4a6"}],"payload_bytes":4793,"payload_sha256":"acc26f4aa0beedbb4b0afa8cbd1d1e39d0678d80ecf67fa7ea4ef4bf03b4c4a6","schema":1,"source_digest":"sha256:acc26f4aa0beedbb4b0afa8cbd1d1e39d0678d80ecf67fa7ea4ef4bf03b4c4a6","source_identity":"ticket:terminal-bench-4-opus55/TBF-03","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":4793,"payload_sha256":"acc26f4aa0beedbb4b0afa8cbd1d1e39d0678d80ecf67fa7ea4ef4bf03b4c4a6","schema":1,"source_digest":"sha256:acc26f4aa0beedbb4b0afa8cbd1d1e39d0678d80ecf67fa7ea4ef4bf03b4c4a6","source_identity":"ticket:terminal-bench-4-opus55/TBF-03"} -->
```markdown
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
- [ ] El coste acumulado observado y reservado queda bajo $250, con presupuesto restante conocido antes de cada start y corte efectivo de solicitudes posteriores; un coste incierto detiene el lote salvo la excepción humana puntual del segundo start descrita abajo; esa excepción nunca convierte coste desconocido en observado. El techo del proyecto permanece $1.000, sin autorizar un full run.
- [ ] Cada intento conserva verifier original, estado de ejecución, tiempo, tokens, costo del modelo, recibos atribuibles y evidencia de aislamiento, incluidos fallos.
- [ ] El informe declara resultado por task, exclusiones GPU y cobertura de 3/66, gasto y decisión de proponer o detener un lote estándar posterior; no afirma comparación entre cuatro brazos ni score de leaderboard.

## Frontier
TBF-01 y TBF-02 están integrados (PR #346, PR #347). **Queda abierto por decisión explícita del usuario (2026-09-25, «Lascia aperto»)** tras un intento de recuperación de recibos por SSH en el host del piloto: el puente usaba `SessionManager.inMemory`, stderr descartado y exportación solo al final, y no se escribió ningún archivo del puente en las ventanas 18:28–18:32Z y 20:03–20:07Z del 2026-09-24; los dos costes no son recuperables y no se deroga el criterio. El mandato TBF-04 se dio conociendo este estado. Se consumieron **3/3 starts originales**, sin retry: `html-js-filter` dio reward 0 con $0.17657720000000002 estimados; `interleaved-vigenere` terminó sin recibo Pi ni verifier; `wal-recovery-ordering` sufrió timeout del bridge sin recibo Pi ni verifier. Ambos costes fallidos siguen desconocidos. La deroga append-only de $60 para admitir el tercer start conservó la incertidumbre; el segundo error no tiene recibo recuperado. El informe terminal y los hashes están fuera de Git en `C:/Users/rdpuser/projects/.tbf-env/standard-pilot-live/pilot-results.md`. Este ticket **no** se marca completado porque no satisface todos los criterios de coste/recibos: el piloto agotado se cierra por límite de starts, no por éxito. El usuario autorizó por separado un experimento local modificado (TBF-05) con dos supuestos de $60 solo para admisión; no se reinterpreta este piloto como resultado de cuatro brazos.

## Step-by-Step Implementation Plan
1. Revalidar manifest, imagen original/verifier, credenciales host, TBF-02, límites y saldo antes de cada start.
2. Reservar y arrancar una tarea Pi bare a la vez, con límite de solicitud y una identidad inmutable.
3. Reconciliar recibos y gastos antes de admitir otra tarea. Para la única excepción autorizada, probar RED/GREEN, conservar el ledger anterior intacto y registrar $60 asumidos aparte del gasto conocido; solo admitir `wal-recovery-ordering` una vez después de CI del nuevo head.
4. Reducir resultados originales y costes; no iniciar el set completo ni el experimento modificado.

## Testing Plan
Comparar ledger y recibos con identidad/modelo/verifier originales; validar cuentas 0–3, techo y que `valid` no equivale a tarea aprobada. La excepción debe rechazar autoridad ausente, hash previo obsoleto, método modificado, duplicados, reservas menores y un nuevo coste incierto; reconstruir estado desde bytes append-only sin presentar $60 asumidos como coste observado.

## Out of Scope
- El lote full, Jev, overlay Git, otros brazos, reutilizar outputs corregidos o publicar resultados en un leaderboard.

```
