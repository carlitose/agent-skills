# Actualizar una pull request sin mandar campos que no cambian

## Artifact Graph
- Artifact ID: `spec:pr-update-field-scope`
- Role: `spec`
- Standalone: true

### Children
- [PUF-01](../tickets/pr-update-field-scope/01-changed-fields-only.md)

## Tipo y hechos
Análisis de bug y reparación (todo27). Skills-only, inline, sin runner.

`CREATE_OR_UPDATE_PR` en `GitHubProvider`, cuando la pull request ya existe, envía siempre
un PATCH con `base`, `title` y `body` a la vez. En la entrega de PR27 esa llamada, hecha
después del merge, recibió `gh: Validation Failed (HTTP 422)` y sin embargo el cuerpo
quedó guardado: el readback posterior mostraba exactamente el cuerpo pretendido
(`pi55-postsync-publication-error-q1.json`, `pi55-provider-after-publication-error-q1.json`).
El título no cambiaba y la base tampoco; aun así se mandaban.

Eso deja dos daños. El adaptador informa de un fallo sobre un efecto que sí ocurrió, así
que quien llama no sabe qué quedó aplicado. Y manda campos que no necesita cambiar, lo que
expone la petición a validaciones que no tienen nada que ver con lo que se quería hacer.

No se ha reproducido contra el servicio a propósito: reintentar una mutación para
investigar está fuera de lo permitido. La reparación se diseña para ser correcta con
cualquiera de las explicaciones posibles del 422.

## Estado actual y objetivo
Hoy el adaptador manda tres campos sin mirar el estado actual de la pull request. El
objetivo es que mande solo lo que difiere, que no intente lo que el servicio no puede
hacer, y que un fallo informe de lo que quedó aplicado.

## Decisión
- Antes del PATCH, leer la pull request. Comparar `base`, `title` y `body` con lo pedido y
  construir la petición solo con los que difieren.
- Si no difiere nada, no hay petición: la operación es idempotente y sigue devolviendo el
  recibo del readback.
- Si lo que cambia es la base y la pull request ya no está abierta, rechazar con un error
  que nombre el estado, sin intentarlo.
- Si el PATCH falla, leer una vez más y añadir al error qué campos pedidos ya están
  guardados. No se reintenta la mutación.
- `gh pr view` pasa a pedir también el título, que hace falta para comparar.

Alternativas descartadas: reintentar sin `base` tras el 422 (es un reintento de mutación);
mandar siempre solo el cuerpo (impediría mover la base de una pull request abierta, que es
una operación legítima); usar `gh pr edit` u otra ruta directa; tratar el 422 como éxito.

## Invariantes
- Crear una pull request nueva no cambia.
- El readback final y sus contradicciones siguen igual de estrictos.
- No se añaden reintentos ni rutas nuevas al proveedor.
- Azure DevOps no se toca.
- Una base distinta en una pull request abierta se sigue enviando.

## Criterios de aceptación
1. Con todo igual, no se manda ningún PATCH.
2. Con solo el cuerpo distinto, el PATCH lleva solo `body`.
3. En una pull request fusionada con la misma base, el PATCH lleva solo lo que cambia y no
   `base`.
4. Mover la base de una pull request fusionada se rechaza nombrando el estado, sin petición.
5. Un PATCH fallido produce un error que dice qué campos quedaron aplicados, y no se
   reintenta.
6. Las suites existentes de proveedor, kernel y wiki siguen pasando.

## Verificación y límites
Un ticket AFK. Base observada `66e7bdb6df472a95c54abf48043b9dae16acde0e`, checkout aislado.
Máximo 900 s por comando, hasta 3 correcciones de calidad. Todo se prueba con dobles del
CLI: no se llama a GitHub y no se reproduce el 422 real, porque eso exigiría mutar una pull
request de verdad. La suite `tests/test_cli.py` es demasiado larga para una sola invocación
y se cubre por partes. Integración es un gate distinto.

## Fuera de alcance
Azure DevOps y #45, el límite de 4000 caracteres, reintentos, rutas nuevas del proveedor,
#42 y reactivar el runner.
