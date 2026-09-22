# Compilar una wiki no debe pagar dos veces por la misma respuesta

## Artifact Graph
- Artifact ID: `spec:wiki-compile-process-cost`
- Role: `spec`
- Standalone: true

### Children
- [WCP-01](../tickets/wiki-compile-process-cost/01-stop-relaunching-processes.md)

## Tipo y hechos
Análisis de rendimiento y reparación (todo #52). Skills-only, inline, sin runner.

Un `sync_project.py` sobre la wiki de `.ai-agent-python-api-luna-paridad` —690 páginas, 6,5 MB,
200 tickets— tarda minutos. Medido por fases sobre una copia desechable, en la misma máquina y
con la misma wiki:

| Fase | Antes |
|---|---|
| copia de trabajo | 6,3 s |
| inventarios (hash de todo) | 1,9 s |
| **ingest** | **261,4 s** |
| timeline | 0,6 s |
| **lint** | **265,4 s** |

Ingest y lint son el 97 % del tiempo. Y un segundo ingest sobre una copia ya compilada, sin
ningún cambio, cuesta 255,9 s: el trabajo no depende de lo que cambió.

Dentro del ingest, la medición es inequívoca: **1 792 procesos lanzados, 260,0 s de los 261,4**.
Es decir, el 99,5 % del tiempo está en arrancar procesos, no en compilar. Los procesos son de dos
clases: 1 592 invocaciones de `git` y 200 arranques del intérprete de Python para
`ticket-autopilot.py ticket-parse`, uno por ticket.

Conviene decir qué **no** es la causa, porque era la sospecha razonable: el catálogo de sesiones
de ese proyecto (1,7 GB en disco) se resuelve en **0,08 s** y devuelve 43 entradas. Las sesiones
no participan del coste.

De los 1 592 `git`, 1 380 son dos preguntas repetidas una vez por artefacto: si el directorio es
un repositorio (`rev-parse`) y si el fichero está versionado (`ls-files --error-unmatch`). Ambas
son propiedades del repositorio, no del fichero. Los 212 restantes, más uno por artefacto
versionado, son `git log --follow` por ruta: ésos sí son preguntas distintas.

## Estado actual y objetivo
Hoy el coste crece con el número de páginas multiplicado por el número de preguntas repetidas.
El objetivo es cobrar cada respuesta una vez, sin cambiar ninguna respuesta.

## Decisión
- **Recordar por repositorio, no por fichero.** `rev-parse` y el conjunto de ficheros versionados
  se resuelven una vez por estado del repositorio. El estado se lee del sistema de ficheros: la
  aparición de `.git` y el estado del índice. Un `git add` o un `commit` cambian el índice, así
  que una respuesta anterior nunca sobrevive a un cambio real.
- **Cruzar la frontera del proceso una vez por árbol, no una por ticket.** El inventario
  canónico `ticket-list --json` responde por todo el árbol de tickets en un solo proceso. La CLI
  sigue siendo el único analizador, y sigue estando detrás de un proceso separado: `llm-wiki` no
  importa nada fuera de la biblioteca estándar, y eso no cambia.
- **Lo que el inventario no nombre se sigue analizando de uno en uno.** Un ticket malformado, o
  uno fuera de la disposición habitual, cae en `ticket-parse` y falla con su propio mensaje en
  lugar de desaparecer en silencio.
- El inventario se recuerda con una huella barata del árbol —cuántos ficheros, cuánto ocupan y
  cuál es el más reciente—, así que un ticket editado, añadido o borrado nunca se responde con
  una lectura anterior.

Alternativas descartadas: importar el analizador canónico dentro de `llm-wiki` (más rápido, pero
rompe la independencia que una prueba del repositorio ya exige, y esa prueba tiene razón);
agrupar los `git log --follow` en una sola llamada (`--follow` solo admite una ruta, y perder el
seguimiento de renombrados cambiaría las fechas que este módulo existe para justificar); guardar
una caché en disco entre ejecuciones (es la vía para el siguiente salto, y necesita decidir su
invalidación con cuidado).

## Invariantes
- Ninguna fecha, identidad, bloqueo ni clasificación cambia.
- `llm-wiki` sigue importando solo la biblioteca estándar.
- El analizador canónico sigue siendo el único que lee un ticket.
- Una respuesta recordada nunca sobrevive al cambio que la invalida.
- Dos repositorios distintos no comparten respuesta.

## Criterios de aceptación
1. Resolver cinco artefactos del mismo repositorio cuesta un `rev-parse` y un `ls-files`.
2. Un `commit` entre dos llamadas se ve en la segunda.
3. Un directorio que se convierte en repositorio se ve.
4. Dos repositorios distintos no comparten respuesta.
5. Un árbol de tickets cuesta un solo proceso, y es `ticket-list`.
6. Los bloqueos del ticket sobreviven al inventario.
7. Un ticket editado o añadido nunca se responde con la lectura anterior.
8. Un ticket malformado falla con el mensaje del analizador canónico.
9. Un ticket fuera de la disposición habitual se sigue analizando.
10. La suite completa de `llm-wiki` sigue pasando, incluida la prueba de independencia.

## Verificación y límites
Base observada `d4d69e073a9e80819f04663c08577c953c290126`, worktree aislado. Máximo 900 s por
comando. La medición se hace sobre una copia desechable de una wiki real: no se publica nada, no
se toca el repositorio del proyecto ni su historia.

## Fuera de alcance
Hacer el sync incremental de verdad —saltarse lo que no cambió desde el commit anterior— que
necesita una caché persistente; agrupar `git log --follow`; y el coste del lint que no venga de
estas mismas preguntas.
