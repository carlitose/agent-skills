# Reparar el baseline del grafo de artifacts sin reescribir su historia

## Artifact Graph

- Artifact ID: `spec:artifact-graph-baseline-repair`
- Role: `spec`
- Parent: [Integridad de enlaces](artifact-link-integrity-wayfinder.md)

### Children

- [AGB-01 — Restaurar un grafo verificable](../tickets/artifact-graph-baseline-repair/01-restore-artifact-graph.md)

## Tipo y diagnóstico

Bug analysis. En `d82b9d17257f44ab4358a428ff3d2fb4c38d52c2`, el auditor canónico
encuentra 45 errores preexistentes. WGC-04 no añade ninguno, pero el preflight confirma
15 enlaces a archivos ausentes y no permite gastar QA ni entregar un árbol con ese bloqueo.
La reparación pertenece a este ticket, no a WGC-04.

Hay cuatro causas de datos: referencias a fuentes no incluidas en el árbol entregado;
campos/colecciones fuera de la gramática aceptada; relaciones recíprocas incompletas o
propiedad confundida con referencia; y dependencias NDW cuyos tickets ignorados no se
incluyeron en Git aunque sus implementaciones sí se integraron.

La política sigue siendo [la decisión canónica](artifact-graph-decision.md). No se cambian
el parser, severidades, raíces, tolerancia de disposición ni validación de dependencias.

## Decisiones

1. **Fuentes presentes.** Corregir únicamente documentos editables. Conservar IDs; expresar
   `Children`/`Related` con sus encabezados canónicos y enlaces sin comentarios anexos.
   Conservar los comentarios históricos fuera de la sección canónica. Añadir reciprocidad
   solo donde el hijo ya declara inequívocamente su Parent. Si otra relación contradice esa
   propiedad, conservarla como Related, no crear un segundo dueño.
2. **Fuentes ausentes.** Un enlace no puede declarar un hijo inexistente. Mantener el título,
   identificador y ruta original en una sección de fuentes históricas no incluidas, como
   referencias textuales y no enlaces locales falsamente resolubles. No inventar cuerpo,
   estado, entrega o autoridad. Esto no cancela ni reabre tickets; describe qué contiene Git.
3. **NDW-01/02/03.** Recuperar su contenido desde el snapshot inmutable validado por
   `load_ticket_snapshot`; la serialización canónica debe reproducir exactamente el digest
   normalizado original. Restaurar en `done/` únicamente tras comprobar marcadores de
   completion y ascendencia de los commits integrados 101871b, d99b5b8 y d4702e2. No fabricar
   recibos ni ejecutar lifecycle. Mantener NDW-04 y sus dependencias byte a byte.
4. **Roots explícitos.** Los diagnósticos que carecen de Parent y no tienen otro dueño
   declarado se registran expresamente como specs standalone; `diagnostic` sigue siendo
   tipo de documento, no un quinto Role. No inferir padres por similitud de nombres.
5. **Recursos fuera del grafo.** Guías y prototipos fuera de las raíces administradas
   conservan sus enlaces en prosa, no como aristas canónicas. No adoptar esos recursos.
6. **Prevención acotada.** Una prueba de repositorio invoca el auditor existente y exige
   cero errores y presencia de la decisión canónica. No endurecer warnings legacy ni
   sustituir el auditor por reglas paralelas.

## Invariantes

- Ningún ticket ya versionado cambia de bytes, ID, dependencias o disposición.
- Ningún ledger, snapshot, completion, grant, sesión ni worktree ajeno se modifica.
- Cada fuente recuperada conserva su digest normalizado comprobable y la procedencia;
  no se afirma conservar los terminadores físicos de un original que no está disponible.
- Todo enlace canónico resuelve a un artifact único y la propiedad es recíproca y acíclica.
- Las referencias a fuentes ausentes se conservan visibles; cero errores no significa
  que se hayan recuperado esos cuerpos o que se haya probado su entrega.
- Los warnings legacy permanecen visibles y separados; no se convierten en errores ni
  desaparecen por rebajar la validación.

## Implementación y verificación

Un único slice AFK AGB-01: prueba causal RED sobre el corpus real; reparación de datos y
recuperación NDW con controles previos; GREEN del mismo auditor; comparación de IDs,
tickets existentes, warnings y referencias conservadas. Comprobar el árbol que se entrega,
no solo archivos locales. Simplificación, review compartida, QA y auditoría canónica inline.

Presupuesto local de QA: 90s acumulados, separado de preparación/TDD y CI. Cada comando
como máximo 900s. Máximo tres ciclos de calidad. CI exact-head requerido permanece como
puerta independiente; no repetir perfiles completos por cambios documentales sin causa.

## Procedencia

Evidencias locales fuera del paquete: `wt57-artifact-audit-baseline-v1.json` (45 errores),
`wt57-candidate-q1.json` (15 targets ausentes, QA bloqueada), y snapshot de la run
`no-dangling-work-v1`, manifest digest
`c6a44fe235f1f7759e63aa951e90142cfcf347466bd668576fb1945c4cadb708`.
Recuperación comprobada: el serializer canónico reproduce estos digests del snapshot; los
bundles publicados vinculan esos mismos digests a los árboles exactos de los commits,
y los tres commits son ancestros de d82b9d1 con el marcador de run/ticket correspondiente.
No se modifica ninguno de esos registros.

| Fuente recuperada | Digest normalizado | Commit de completion |
| --- | --- | --- |
| NDW-01 | `3810f8334b66e7dcb62e1dce585b637cad6aca0abf58074a11e0f3d29427bd41` | `101871b98654761fedf2866223770ffd7b2ee9e5` |
| NDW-02 | `75b47198bcc5c0fdef0b5dd4ca17a9bc0f495a15df2fb2be96b5555d5b8f2718` | `d99b5b8c4ffc00e4c9b6f9dd331a7bea3affe7b2` |
| NDW-03 | `a766da805b80b74d81722c1529b9f10bc2be35c20339d8b94851c33d7592ecaa` | `d4702e23050ebd41fc0bf4ce8be52937d4574667` |

Corregir la gramática de la arista GPM-01 reveló otra fuente ausente, antes oculta por
`malformed-relationship`: son 16 referencias históricas conservadas, no 15 cuerpos
recuperados. La nota original sobre run abortada y no entregada permanece visible.
El auditor pasa de 45 errores a cero; ello no afirma recuperar estas fuentes ausentes.

## Fuera de alcance

No implementar WGC-04 ni otros bugs; no ejecutar inventario, planner, cleanup, scheduler o
runner reales; no cambiar mandatos, estados de tickets ni la política del grafo; no regenerar
wiki; no rehacer el corpus legacy. No afirmar independencia de revisión, éxito nativo macOS,
activación de Pi ni recuperación de fuentes no demostradas.
