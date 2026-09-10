---
type: source
title: "El cuerpo que va al proveedor es ASCII"
identity_key: ticket:ticket-autopilot-provider-body-lossy-readback/PBL-01
identity_strength: stable
source_path: docs/tickets/ticket-autopilot-provider-body-lossy-readback/done/PBL-01-cuerpo-ascii.md
source_digest: sha256:f92696deeb991174569a4ea11f5626c71d4edc22942d576344bf7274a9dff56d
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-08
created_provenance: git-commit
disposition_changed: 2026-09-08
disposition_changed_provenance: git-rename
run_id: 725268613b774963
---

# El cuerpo que va al proveedor es ASCII

Compiled from `docs/tickets/ticket-autopilot-provider-body-lossy-readback/done/PBL-01-cuerpo-ascii.md`. Identity is `ticket:ticket-autopilot-provider-body-lossy-readback/PBL-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-08** via `git-commit`
- Disposition changed: **2026-09-08** via `git-rename`

## Graph

- Parent source: [[sources/artifact-ticket-autopilot-provider-body-lossy-readback]]

## Run

Completed under autopilot run `725268613b774963`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[5],"status":"present"},"exclusions":{"headings":[],"status":"not-identified"},"frontier":{"headings":[6],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[8],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-ticket-autopilot-provider-body-lossy-readback-pbl-01.md","payload_bytes":3367,"payload_sha256":"f92696deeb991174569a4ea11f5626c71d4edc22942d576344bf7274a9dff56d"}],"payload_bytes":3367,"payload_sha256":"f92696deeb991174569a4ea11f5626c71d4edc22942d576344bf7274a9dff56d","schema":1,"source_digest":"sha256:f92696deeb991174569a4ea11f5626c71d4edc22942d576344bf7274a9dff56d","source_identity":"ticket:ticket-autopilot-provider-body-lossy-readback/PBL-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 5: Acceptance Criteria |
| testing | 8: Testing Plan |
| frontier | 6: Frontier |
| exclusions | no matching section identified in the source; complete source retained |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3367,"payload_sha256":"f92696deeb991174569a4ea11f5626c71d4edc22942d576344bf7274a9dff56d","schema":1,"source_digest":"sha256:f92696deeb991174569a4ea11f5626c71d4edc22942d576344bf7274a9dff56d","source_identity":"ticket:ticket-autopilot-provider-body-lossy-readback/PBL-01"} -->
````markdown
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

````
