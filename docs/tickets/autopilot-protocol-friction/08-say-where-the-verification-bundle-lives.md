---
ticket_schema: 1
ticket_id: "APF-08"
execution_mode: AFK
blocked_by:
  - "APF-01"
---

# APF-08 — El bundle de verificación se escribe donde la entrega lo lee, y el gate nombra el remedio

## Artifact Graph
- Artifact ID: `ticket:autopilot-protocol-friction:08`
- Role: `ticket`
- Parent: [autopilot-protocol-friction-wayfinder.md](../../specs/autopilot-protocol-friction-wayfinder.md)

## Parent Spec
[autopilot-protocol-friction-wayfinder.md](../../specs/autopilot-protocol-friction-wayfinder.md)

## What to Build
La entrega lee el bundle de `verify` desde `quality.evidence` (ids `verification-checkpoint:bundle-validated`
y `handoff-ready`) y exige que viva bajo el directorio del run. Nadie lo dice antes: en q3 el modelo
lo escribió en la raíz del benchmark y el gate `delivery-pr-body` respondió "is not in the subpath"
(turno 169) sin decir dónde debía estar ni que `verification-checkpoint` lo escribe ahí. Ningún run
(q1, q2, q3) ha usado `verification-checkpoint`: en q2 `verify` fue una copia de `qa-execute`; en q3 un
bundle tomado de la fixture de tests de `verification-audit` y recableado al CandidateRef. Tres
cambios: `leaf-result-template` a `verify` emite el evento `verification-checkpoint` en vez de un
`leaf-result` a mano y nombra el directorio; los dos `DeliveryBodyError` del bundle llevan
`detail` con directorio esperado y remedio; el resultado `gated` de `resume` publica el `detail` del
error, que hoy se pierde (`reason` solo).

## Acceptance Criteria
- [ ] `leaf-result-template` a `verify` devuelve el evento `verification-checkpoint` literal con `expected_tree_oid`, `verification_audit_root` y el marcador de `verification_inputs`, y nombra `<run dir>/<ledger>-checkpoints/<ticket>` como destino.
- [ ] Un `leaf-result` de `verify` cuyo artefacto vive fuera del run: el gate `delivery-pr-body` devuelve `detail` con `received`, `expected` (el directorio) y `next_step` (el evento `verification-checkpoint`).
- [ ] Todo resultado `gated` de `resume` publica `detail` cuando el error lo trae; `reason` no cambia.
- [ ] Un test aplica el `next_step` del gate y la entrega avanza.

## Frontier
Cierra QB-apf01-2. Bloqueado por APF-01 (#332). No decide quién construye el bundle: eso es APF-06 y su spec.

## Step-by-Step Implementation Plan
1. `DeliveryBodyError(phase, message, *, detail=None)`; los dos errores del bundle lo rellenan.
2. En `resume`, el `outcome` gated incluye `detail` si `getattr(error, "detail", None)`.
3. `_leaf_result_template`: rama `verify` con el evento `verification-checkpoint` y `after_acceptance` acorde.
4. Tests: plantilla a `verify`, gate con artefacto fuera del run, remedio aplicado.

## Testing Plan
- Test que recorre un ticket hasta `verify`, registra un `leaf-result` con artefacto fuera del run, pide `finalize` y lee el `detail` del gate.
- Test que la plantilla a `verify` es el evento `verification-checkpoint` y que, rellenado, `resume` lo acepta.

## Out of Scope
- Que el runner construya `verification_inputs` desde el ledger: es la inversión de APF-06.
- Cambiar el contrato del bundle o su validador.
