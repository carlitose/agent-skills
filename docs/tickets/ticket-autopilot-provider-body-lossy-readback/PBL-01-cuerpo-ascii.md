---
ticket_schema: 1
ticket_id: "PBL-01"
execution_mode: AFK
blocked_by: []
---

# El cuerpo que va al proveedor es ASCII

## Artifact Graph
- Artifact ID: `artifact:ticket-autopilot-provider-body-lossy-readback-PBL-01`
- Role: `ticket`
- Parent: [ticket-autopilot-provider-body-lossy-readback.md](../../specs/ticket-autopilot-provider-body-lossy-readback.md)

## Parent Spec
[ticket-autopilot-provider-body-lossy-readback.md](../../specs/ticket-autopilot-provider-body-lossy-readback.md)

## What to Build

Cambiar la flecha `→` por `->` en el cuerpo del PR de cambio de disposicion
(`ticket-autopilot/scripts/autopilot/tracked_status_delivery.py:549`), y anniadir un test que
impida que vuelva a entrar un caracter no-ASCII en ese cuerpo.

### La medida que lo justifica

`_validate_pr` compara el cuerpo byte a byte. `az` descarta el caracter al devolverlo, con aviso
propio: `Unable to encode the output with cp1252 encoding`. El hash lo demuestra al caracter:

```
esperado por el runner: 145b58fa...
devuelto por az       : 392544f8...
con la flecha repuesta: 145b58fa...   coincide exacto
```

La transaccion muere con `provider PR readback is contradictory` **despues** de haber creado el PR.

## Acceptance Criteria
- [ ] La linea 549 no contiene ningun caracter fuera de ASCII, y el cuerpo dice `open -> on-hold`.
- [ ] Un test afirma que el cuerpo generado es ASCII puro, para las tres transiciones
      (`open`, `on-hold`, `canceled`) y en las dos direcciones que el contrato permita.
- [ ] Ese test falla si alguien reintroduce cualquier caracter no-ASCII en la plantilla. Se
      comprueba desactivandolo: con la flecha puesta, el test debe caer.
- [ ] La comparacion byte a byte de `_validate_pr` **no se relaja**, y un test lo afirma: un cuerpo
      devuelto distinto sigue siendo contradictorio.
- [ ] **No** se anniade normalizacion del texto devuelto por el proveedor.
- [ ] La suite de `test_status_transaction.py` y la de entrega siguen igual o mejor, con el recuento
      antes y despues escrito en la entrega.

## Frontier

**Listo.** Sin bloqueos. No necesita proveedor: el cuerpo se genera en local y el test lo inspecciona
sin salir a la red.

Aviso de alcance: el motivo y la referencia de autoridad los escribe quien llama, y pueden traer
acentos. Este ticket **no** los toca, porque el recuento cubrio el codigo y no los datos. Si se
quiere cubrir tambien eso, es otro ticket, y conviene decidir antes si el runner debe rechazar un
motivo no-ASCII o transliterarlo. No lo decida este ticket por la puerta de atras.

## Step-by-Step Implementation Plan
1. Cambiar el caracter. Checkpoint: `grep` de no-ASCII sobre el modulo devuelve cero.
2. Test de la plantilla, ASCII puro, cubriendo las transiciones. Checkpoint: pasa.
3. Prueba causal: reponer la flecha y ver caer el test. Checkpoint: cae por ese motivo y no por otro.
4. Test que fija la comparacion byte a byte. Checkpoint: pasa.
5. Recuento de las suites antes y despues. Checkpoint: escrito en la entrega.

## Testing Plan
- **Unitario**: el cuerpo generado es ASCII; la comparacion byte a byte sigue rechazando un cuerpo
  distinto.
- **Manual**: repetir un `status-change-transaction` real en un repositorio de Azure DevOps sobre
  Windows y comprobar que la transaccion liquida en vez de morir en la lectura de vuelta. Esto no lo
  puede afirmar el test: pide proveedor.
