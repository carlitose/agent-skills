# Un carácter que el proveedor devuelve mutilado invalida la transacción entera

## Artifact Graph
- Artifact ID: `artifact:ticket-autopilot-provider-body-lossy-readback`
- Role: `spec`

## Type
Diagnostic spec

## Status
Medido el 08/09/2026 en `ocr-dotnet-api` (Azure DevOps, Windows), sobre `agent-skills` en `b4a6535`.

## El síntoma

`status-change-transaction` sobre el ticket `16` recorre todo el camino, empuja la rama, **crea el
PR** — y entonces muere:

```
StatusTransactionError: provider PR readback is contradictory
```

Ni gate, ni recuperación. La transacción queda sin liquidar aunque el efecto en el proveedor ya
está hecho y es correcto.

## La causa, medida al carácter

`_validate_pr` (`tracked_status_delivery.py:604`) compara el cuerpo del PR **byte a byte** con lo
que envió. La comparación falla por un solo carácter:

```
esperado por el runner: 145b58faa585125091e2855ddb6d7f70a7b374399be80987bcb955f1c755bf28
devuelto por az       : 392544f8e84d26ee3a8d2c4d4e7429f4d9ae97b5cab505db2238b26874fee190
con la flecha repuesta: 145b58faa585125091e2855ddb6d7f70a7b374399be80987bcb955f1c755bf28
```

La tercera línea es la prueba: repongo la `→` (U+2192) en el texto devuelto y el hash **coincide
exacto** con el esperado. No hay nada más distinto.

La flecha entra en el cuerpo aquí (`tracked_status_delivery.py:549`):

```python
f"- Disposition: `{request['from_disposition']}` → `{request['to_disposition']}`\n"
```

Y `az` la descarta al devolver el PR:

```
WARNING: Unable to encode the output with cp1252 encoding. Unsupported characters are discarded.
```

Azure DevOps **guarda bien** el carácter. El que lo pierde es el CLI al imprimir su salida, porque
`knack` re-codifica con `ascii`/`ignore` cuando la codificación del entorno no da.

## Es la única línea expuesta

Recuento sobre los 38 módulos de `scripts/autopilot`: hay caracteres no-ASCII en once líneas, y
**diez son guiones em dentro de comentarios o docstrings**. La única que viaja a un cuerpo de PR es
la 549. Una sola.

## Por qué no se arregla desde el entorno

`az.cmd` arranca Python con `-I`, que ignora las variables de entorno. Probado y descartado:

| Intento | Resultado |
|---|---|
| `PYTHONIOENCODING=utf-8` | la flecha se pierde |
| `PYTHONUTF8=1` | la flecha se pierde |
| `chcp 65001` antes de `az` | la flecha se pierde |
| `AZURE_CORE_OUTPUT_ENCODING=utf-8` | la flecha se pierde |
| `PYTHONUTF8=1 python -m azure.cli` (sin el shim) | **la flecha sobrevive, el hash coincide** |

La última fila prueba que el problema es corregible, y también que **no** lo es desde donde el
runner llama: el runner invoca `az`, no el módulo interno.

## Qué se pide

Que el cuerpo que el runner manda al proveedor sea ASCII. Cambiar `→` por `->` en la línea 549.

Un carácter, y desaparece la clase entera de fallo para esta plantilla.

## Lo que no se pide, y por qué

- **No** relajar la comparación byte a byte. Es lo que garantiza que el PR publicado dice
  exactamente lo que la transacción aprobó. Aflojarla para tragar mutilaciones sería cambiar una
  garantía real por comodidad.
- **No** normalizar el texto devuelto antes de comparar. Escondería el aviso del CLI y dejaría
  pasar cualquier otra pérdida futura, no solo la flecha.
- **No** tocar el arranque de `az`. El runner no controla el shim, y hacerlo dependería de la
  instalación de cada máquina.

## El precedente que ya existía en el propio repo

`git_ops.py:42-43` advierte por escrito:

> A PR body, a file's contents, a diff — anything whose trailing newline is part of its identity —
> must not be read back through here.

La fidelidad del texto que vuelve del proveedor ya se sabía delicada. Lo que faltaba era la otra
mitad: **lo que el runner envía también tiene que sobrevivir al viaje de vuelta.**

## Alcance de lo medido

- Un proveedor (Azure DevOps via `az`), una máquina (Windows, consola cp1252).
- **No** medido en GitHub via `gh`: no sé si `gh` pierde el mismo carácter. La corrección propuesta
  no depende de la respuesta, porque quita el carácter en origen.
- **No** medido si otras plantillas de cuerpo del runner introducen no-ASCII por interpolación de
  datos del usuario, por ejemplo un motivo con acentos. El recuento cubre el código, no los datos.
- El efecto del PR fallido era correcto: se mergeó y el ticket quedó en `hold/` con su digest
  intacto. El defecto está en la autocomprobación, no en el efecto.
