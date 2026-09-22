---
ticket_schema: 1
ticket_id: "APF-06"
execution_mode: HITL
blocked_by: 
  - APF-01
---

# APF-06 — ¿Construye el runner el `leaf-result` y el modelo solo rellena?

## Artifact Graph
- Artifact ID: `ticket:autopilot-protocol-friction:06`
- Role: `ticket`
- Parent: [autopilot-protocol-friction-wayfinder.md](../../specs/autopilot-protocol-friction-wayfinder.md)

## Parent Spec
[autopilot-protocol-friction-wayfinder.md](../../specs/autopilot-protocol-friction-wayfinder.md)

## What to Build
Decisión de arquitectura. Hoy el modelo construye el evento entero y el runner lo valida; el
prototipo APF-01 prueba el punto medio, una plantilla. La alternativa fuerte es invertir la dirección:
el runner abre la etapa, genera el esqueleto exacto con CandidateRef y fases, y el modelo solo
devuelve hallazgos y evidencia. Cambia el contrato `leaf-result`, la skill y quién posee la forma del
evento. Requiere [grilling](../../../grilling/SKILL.md) y confirmación explícita con los datos del
prototipo delante.

## Acceptance Criteria
- [ ] La decisión está tomada con los números de APF-01 a la vista: lecturas, coste, tiempo.
- [ ] Están escritos los trade-offs: qué pierde el modelo en flexibilidad, qué gana el runner en control.
- [ ] Si se invierte la dirección, el cambio de contrato queda especificado en `to-spec` antes de ningún ticket de implementación.

## Frontier
Bloqueado por APF-01. Decisión humana; ningún agente la toma por inferencia.

## Step-by-Step Implementation Plan
1. Presentar los resultados del prototipo.
2. Grilling sobre la inversión del contrato.
3. Registrar la decisión y, si procede, la spec del nuevo contrato.

## Testing Plan
- La decisión registrada con fecha, alcance y los números que la sostienen.

## Out of Scope
- Implementar nada: es una decisión.
- Tomarla por inferencia o sin los números de APF-01.
- Extenderla a otros contratos (`stage`, gates, autoridad).
