---
ticket_schema: 1
ticket_id: "APF-01"
execution_mode: AFK
blocked_by: []
---

# APF-01 — Un comando que emite el `leaf-result` que el runner espera

## Artifact Graph
- Artifact ID: `ticket:autopilot-protocol-friction:01`
- Role: `ticket`
- Parent: [autopilot-protocol-friction-wayfinder.md](../../specs/autopilot-protocol-friction-wayfinder.md)

## Parent Spec
[autopilot-protocol-friction-wayfinder.md](../../specs/autopilot-protocol-friction-wayfinder.md)

## What to Build
Prototipo: `leaf-result-template <run_id> [--ticket ID] [--stage STAGE]` en el CLI del runner. Lee el
ledger y emite el JSON de esquema 3 con todo lo que el runner ya sabe rellenado —CandidateRef exacto,
ticket, etapa activa, fases, campos de `quality` que la etapa exige— y con marcadores explícitos en
lo que solo el modelo puede aportar: hallazgos, evidencia direccionada, recursos. Se mide sobre el
ticket sembrado del benchmark: cuántas lecturas de código del runner hace el modelo con la plantilla
disponible, frente a 41 sin ella (turnos 61–175 de q2).

## Acceptance Criteria
- [ ] El comando existe y emite JSON válido para `validate_leaf_result` una vez rellenados los marcadores.
- [ ] Para `review`, `qa-plan`, `qa-execute` y `verify` incluye el bloque `quality` con la forma que la etapa exige.
- [ ] Un run del benchmark con la plantilla disponible: lecturas de código del runner contadas y comparadas con 41.
- [ ] Coste y tiempo del run medidos y comparados con 6,42 $ y 1 935 s.
- [ ] Si el prototipo no baja las lecturas, se dice y el mapa vuelve al diagnóstico.

## Frontier
Ready. Es un prototipo: código desechable hasta que APF-06 decida la forma definitiva.

## Step-by-Step Implementation Plan
1. Localizar en `leaf_protocol.py` y `cli.py` qué campos puede derivar el runner del ledger.
2. Emitir la plantilla con marcadores `<<FILL: …>>` en lo que no puede derivar.
3. Añadir una línea a `ticket-autopilot/SKILL.md` que nombre el comando junto a `resume --events`.
4. Lanzar el brazo autopilot del benchmark en detached y medir.

## Testing Plan
- Test: la plantilla rellenada con valores de ejemplo pasa `validate_leaf_result` para cada etapa.
- Registro del run: lecturas de código del runner, coste, tiempo, defectos, frente a q2.

## Out of Scope
- Cambiar `validate_leaf_result` o el esquema 3: la plantilla se adapta al contrato, no al revés.
- Convertir el prototipo en contrato definitivo: eso lo decide APF-06.
- Tocar `execute-ticket` o el prompt del benchmark.
