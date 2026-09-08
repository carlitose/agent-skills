---
ticket_schema: 1
ticket_id: "ROD-01"
execution_mode: AFK
blocked_by: []
---

# La resolución de propiedad descarta los runs cuyo ciclo de vida ya terminó

## Artifact Graph
- Artifact ID: `artifact:ticket-autopilot-run-ownership-deadlock-ROD-01`
- Role: `ticket`
- Parent: [ticket-autopilot-run-ownership-deadlock.md](../../specs/ticket-autopilot-run-ownership-deadlock.md)

## Parent Spec
[ticket-autopilot-run-ownership-deadlock.md](../../specs/ticket-autopilot-run-ownership-deadlock.md)

## What to Build

Que `_resolve_owner` (`ticket-autopilot/scripts/autopilot/status_transaction.py:560`) **no cuente como
usable** un run cuyo ciclo de vida ya terminó. Hoy cuenta cualquiera cuyo ledger contenga el ticket, en la
ruta exacta y con el digest exacto, sin mirar en qué estado está el run.

Medida que lo demuestra: `run_state`, `aborted` y `cleanup` aparecen **cero veces** en ese módulo.

### El cerrojo que esto abre

Con dos runs abortados reclamando el mismo ticket, `status-change-transaction` gatea para siempre con
`ambiguous-run-ownership`, y ninguna de las tres salidas existentes funciona: `abort` no libera la
propiedad, `cleanup` se niega mientras el run custodie un ticket en `hold` (`cli.py:6457` →
`kernel.py:3519`), y el retiro solo admite ledgers de esquema 1 y 2 (`legacy_recovery.py:383`) cuando los
actuales son de esquema 4.

Detalle completo y citas en la spec.

## Acceptance Criteria
- [ ] `_resolve_owner` descarta los runs terminados. Un run terminado no aparece en `usable` ni en
      `ambiguous_run_ids`.
- [ ] Con **un** run vivo y **N** terminados que contienen el mismo ticket, la transacción resuelve contra
      el vivo y **no** gatea.
- [ ] Con **cero** runs vivos y N terminados, la transacción resuelve sin proyección
      (`run_projection: not-applicable`) y **no** gatea.
- [ ] Con **dos o más** runs vivos, sigue gateando con `ambiguous-run-ownership`. Esto no se relaja: es el
      caso que el gate existe para atrapar.
- [ ] `run-source-drift` sigue teniendo prioridad sobre la ambigüedad cuando hay digest distinto en un run
      **vivo**. Un run terminado con digest distinto tampoco debe producir drift.
- [ ] La negativa de `cleanup` ante un ticket en `hold` **no se toca**, y un test lo afirma: protege el
      registro de la espera.
- [ ] El retiro legacy **no se abre** a esquema 4.
- [ ] Test de regresión que reproduce el cerrojo completo: dos runs con el mismo ticket, uno abortado, uno
      con un ticket en `hold`, y la transacción resolviendo en vez de gatear.
- [ ] La suite del módulo (`ticket-autopilot/tests/test_status_transaction.py`) pasa igual o mejor que
      antes del cambio, con el recuento antes/después escrito en la entrega.

## Frontier

**Listo.** Sin bloqueos. No necesita proveedor, ni credenciales, ni acceso externo: el defecto se reproduce
con runs locales.

Aviso de autorreferencia, igual que en `WPS-01`: este ticket arregla el runner que lo entrega. La entrega
en sí no usa `status-change-transaction`, así que el camino defectuoso no interviene en su propia
corrección.

## Step-by-Step Implementation Plan
1. Definir qué es «terminado» leyendo el propio ledger, sin adivinar: los estados de run que el kernel ya
   considera finales. Checkpoint: la lista sale del código, no de una suposición.
2. Aplicar el descarte en `_resolve_owner`, antes de acumular en `usable`. Checkpoint: los cuatro casos de
   los criterios.
3. Test de regresión del cerrojo completo. Checkpoint: falla antes del cambio, pasa después.
4. Recuento de la suite antes y después. Checkpoint: escrito en la entrega.

## Testing Plan
- **Unitario**: los cuatro casos de propiedad (un vivo, cero vivos, dos vivos, drift en vivo contra drift
  en terminado), más el test que afirma que `cleanup` sigue negándose con un `hold`.
- **Manual**: reproducir el escenario real que lo destapó — carpeta con ocho runs, tres vivos, un ticket en
  `hold` — y comprobar que la transacción deja de gatear.
