---
type: source
title: "La propiedad de un run no se libera nunca, y bloquea los cambios de estado de toda la carpeta"
identity_key: artifact:ticket-autopilot-run-ownership-deadlock
identity_strength: stable
source_path: docs/specs/ticket-autopilot-run-ownership-deadlock.md
source_digest: sha256:d460798d16d99c94bded88aeb82987e8d657758f1017020f4c441d8598d20a75
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-09-08
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# La propiedad de un run no se libera nunca, y bloquea los cambios de estado de toda la carpeta

Compiled from `docs/specs/ticket-autopilot-run-ownership-deadlock.md`. Identity is `artifact:ticket-autopilot-run-ownership-deadlock`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-08** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"decisions":{"headings":[],"status":"not-identified"},"exclusions":{"headings":[],"status":"not-identified"},"goals":{"headings":[],"status":"not-identified"},"invariants":{"headings":[],"status":"not-identified"},"verification":{"headings":[],"status":"not-identified"}},"parts":[{"index":0,"path":"wiki/sources/artifact-ticket-autopilot-run-ownership-deadlock.md","payload_bytes":5985,"payload_sha256":"d460798d16d99c94bded88aeb82987e8d657758f1017020f4c441d8598d20a75"}],"payload_bytes":5985,"payload_sha256":"d460798d16d99c94bded88aeb82987e8d657758f1017020f4c441d8598d20a75","schema":1,"source_digest":"sha256:d460798d16d99c94bded88aeb82987e8d657758f1017020f4c441d8598d20a75","source_identity":"artifact:ticket-autopilot-run-ownership-deadlock","source_kind":"spec"} -->

| Topic | Source sections |
|---|---|
| goals | no matching section identified in the source; complete source retained |
| exclusions | no matching section identified in the source; complete source retained |
| decisions | no matching section identified in the source; complete source retained |
| invariants | no matching section identified in the source; complete source retained |
| verification | no matching section identified in the source; complete source retained |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":5985,"payload_sha256":"d460798d16d99c94bded88aeb82987e8d657758f1017020f4c441d8598d20a75","schema":1,"source_digest":"sha256:d460798d16d99c94bded88aeb82987e8d657758f1017020f4c441d8598d20a75","source_identity":"artifact:ticket-autopilot-run-ownership-deadlock"} -->
````markdown
# La propiedad de un run no se libera nunca, y bloquea los cambios de estado de toda la carpeta

## Artifact Graph
- Artifact ID: `artifact:ticket-autopilot-run-ownership-deadlock`
- Role: `spec`

## Type
Diagnostic spec

## Status
Medido el 08/09/2026 en `ocr-dotnet-api`, sobre `agent-skills` en `4771011`.

## El síntoma

`status-change-transaction` no puede cambiar la disposición de **ningún** ticket de la carpeta
`docs/tickets/langfuse-ocr-dotnet-api`. Devuelve siempre lo mismo, sin efecto alguno:

```
transaction_phase: gated
gate: ambiguous-run-ownership
result: (ninguno)
```

Dos intentos, con transacciones distintas (`48dcb080…` y `eb259310…`), el mismo gate. El repositorio
quedó intacto las dos veces, que es lo correcto: el gate hace su trabajo.

Lo que no es correcto es que **no exista forma de salir de él**.

## Las tres piezas del cerrojo

### 1. La propiedad ignora el ciclo de vida del run

`_resolve_owner` (`ticket-autopilot/scripts/autopilot/status_transaction.py:560`) recorre todos los runs y
considera **usable** a cualquiera cuyo ledger contenga ese ticket, en esa ruta, con ese digest. Si hay más
de uno, gate (`:641` y `:649`).

Lo que no mira, medido por conteo sobre el módulo entero:

```
apariciones de run_state, aborted y cleanup en status_transaction.py: 0
```

**Un run abortado sigue siendo dueño.** Se comprobó en vivo: aborté los tres runs de la carpeta con el
comando `abort` —los tres pasaron a `aborted`— y el gate no se movió ni un milímetro. Quedaban dos runs
reclamando el ticket `16` con su digest exacto, `03cd58742c6f452b` y `9381188224a14e07`.

### 2. `cleanup` se niega si el run custodia **cualquier** ticket en espera

La salida natural sería limpiar esos runs. No se puede:

```
ticket disposition forbids worktree:cleanup: on-hold
```

El bucle de `cleanup` (`cli.py:6457`) llama a `preflight_mutation_boundary` **por cada ticket del run**, y
esa función (`kernel.py:3519`) rechaza la operación si la disposición de ese ticket es `on-hold` o
`canceled`.

Los dos runs custodian el ticket `08`, que está legítimamente en `hold/`. Así que la negativa es correcta
en su intención —no destruir el registro de una espera— y a la vez **convierte el run en inmortal**: no se
puede limpiar mientras exista ese `hold`, y el `hold` no tiene motivo para desaparecer.

Merece decirse claro: esos dos runs **no son basura**. Custodian 11 y 12 tickets completados, con sus rutas
en `done/`, y el registro del `08` en espera. Borrarlos a mano no es «limpiar restos»: es tirar el
historial de la carpeta.

### 3. El retiro solo existe para ledgers legacy

`_active_retirement` (`status_transaction.py:587`) es la única vía por la que un run deja de ser dueño. Se
apoya en `legacy_recovery`, que rechaza explícitamente cualquier ledger que no sea de esquema 1 o 2
(`legacy_recovery.py:383`):

```python
if requested["action"] == "retire" and schema not in {1, 2}:
    raise LegacyRecoveryError("legacy recovery requested retirement for a non-schema-1/2 ledger")
```

Los ledgers actuales son **esquema 4**. La puerta existe, y está tapiada para todo lo moderno.

## Por qué se cierra el círculo

Las tres piezas por separado son defendibles. Juntas producen un estado sin salida:

| Vía | Por qué no sirve |
|---|---|
| `abort` | La propiedad no mira el estado del run |
| `cleanup` | Se niega mientras el run custodie un ticket en `hold` |
| retiro | Solo para esquema 1 y 2 |
| borrar a mano | Destruye el historial de tickets completados y el registro del `hold` |

**Condición para caer en el cerrojo**: que dos runs de una misma carpeta contengan el mismo ticket con el
mismo digest, y que alguno custodie un ticket en `hold` o `canceled`. Eso no es raro. Es lo que pasa
naturalmente cuando una carpeta se trabaja en varias sesiones: cada `run` nuevo hace su instantánea de
**todos** los tickets de la carpeta.

## Por qué no se había visto

Por lo mismo que el defecto de las rutas Windows de `WPS-01`: nadie había recorrido el camino. Los cambios
de disposición se habían hecho hasta ahora en carpetas con un solo run vivo. En `ocr-dotnet-api`, la
carpeta `langfuse-ocr-dotnet-api` acumuló **ocho** runs a lo largo de la semana, tres de ellos vivos, y al
primer intento de poner un ticket en espera apareció el cerrojo.

## Qué se pide

Que la resolución de propiedad **descarte los runs cuyo ciclo de vida ya terminó**. Un run abortado, fallido
o limpiado no debe competir por la propiedad de un ticket: no va a ejecutar nada nunca más.

Esa es la corrección mínima, y no toca ninguna de las otras dos piezas:

- **no** relaja la negativa de `cleanup`, que protege el registro del `hold`;
- **no** abre el retiro a esquema 4;
- **no** pide borrar historial.

## Lo que no se pide, y por qué

- **No** tocar el gate. Cuando de verdad hay dos runs vivos compitiendo, pararse es lo correcto.
- **No** permitir que la transacción elija run con un parámetro. Trasladaría la decisión a quien llama, y
  el ambiguo es un estado del repositorio, no de la llamada.
- **No** cambiar la proyección de completado ni la instantánea por carpeta.

## Verificación

Reproducible sin proveedor: una carpeta con dos runs que contengan el mismo ticket, al menos uno de ellos
abortado y con otro ticket en `hold`; pedir `status-change-transaction` sobre el primer ticket. Antes de la
corrección da `ambiguous-run-ownership`; después debe resolver contra el único run vivo, o contra ninguno si
todos terminaron.

## Alcance de lo medido

- Medido en **una** máquina (Windows) y **un** repositorio, con `agent-skills` en `4771011`.
- El conteo de `run_state`/`aborted`/`cleanup` es sobre `status_transaction.py` completo, no una muestra.
- Las citas de línea son de ese commit exacto.
- **No** se ha medido si otras rutas del runner comparten la misma ceguera al ciclo de vida del run. La
  corrección propuesta se limita a la resolución de propiedad de los cambios de disposición.

````
