# Qué comandos git emite el runner, cuántas veces y cuánto cuestan

## Artifact Graph
- Artifact ID: `artifact:runner-git-command-histogram`
- Role: `research`
- Parent: [suite-cost-one-percent-wayfinder.md](../specs/suite-cost-one-percent-wayfinder.md)

## Pregunta
De los comandos `git` que el runner emite en un ciclo de vida completo, ¿cuántos son
repeticiones del mismo argv dentro de la misma invocación, y cuánto cuesta cada familia?
Sin esta tabla no se sabe si quitar redundancia vale un 10 % o un 50 %.

## Método

`docs/prototypes/suite-cost-one-percent/sitecustomize.py` se coloca primero en `PYTHONPATH`,
así que Python lo importa en **todos** los intérpretes del árbol. Parchea
`subprocess.Popen.__init__` y `.wait`, por debajo de `capture_command`: no necesita hook de
importación, no puede perderse un punto de llamada y sigue siendo correcto si la captura
cambia. Un fichero JSONL por PID evita escrituras entrelazadas.

Atribuir la «operación» exigió cuidado. El frame más externo de `autopilot` nombra la
operación, pero un proceso ejecuta muchas en secuencia y varias comparten nombre. La identidad
del objeto frame separa la invocación N de la N+1; se guarda una referencia fuerte para que el
id de un frame liberado no se reutilice como clave. **Sin esto las cifras salen infladas**: la
primera medición contó 313 repeticiones donde había 271, porque fusionaba invocaciones
distintas del mismo nombre.

Tres casos de `test_cli`, cada uno solo, sin otros shards, el 16/09/2026.

**Corrección aplicada a estas cifras.** La primera pasada agrupaba por argv e ignoraba el
directorio, así que contaba como repetición dos preguntas iguales a repositorios distintos.
La clave corregida incluye directorio e invocación; el caso mediano tiene **265**
repeticiones de esa clave, no 271. Las tablas de abajo ya usan esa corrección.

**Límite adicional de la clave:** `measure_commands.summarize` agrupa por los primeros
cuatro tokens de argv normalizado, no por el argv literal completo. Puede juntar OIDs,
rutas o argumentos distintos. Los conteos describen familias repetidas, no prueban que
la pregunta completa ni el estado sean idénticos; por sí solos no autorizan una caché.

## Resultado

| caso | duración | comandos | git | repeticiones en una invocación |
|---|---|---|---|---|
| `test_candidate_invalidation_resets_stale_preparation_before_delivery_retry` | 40,4 s | 395 | 30,7 s | 265 |
| `test_enabled_preflight_exclusion_stays_on_the_full_lifecycle` | 32,0 s | 302 | 23,9 s | 204 |
| `test_approve_resolves_hitl_start_gate` | 9,9 s | 83 | 7,0 s | 38 |

El 67 % de los comandos del caso mediano repite la clave de familia dentro de una misma
invocación. **No prueba identidad completa ni reutilización segura**: ver los límites.

### Familias por coste, caso mediano (395 comandos, 39,0 s)

| total | n | media | argv | emisor principal |
|---|---|---|---|---|
| 15 210 ms | 4 | 3 802 ms | `<python> ticket-autopilot.py resume` | subproceso CLI |
| **8 468 ms** | **116** | 73,0 ms | `git rev-parse --show-toplevel` | `cli.main` |
| 3 870 ms | 1 | 3 869 ms | `<python> ticket-autopilot.py run` | subproceso CLI |
| 3 809 ms | 40 | 95,2 ms | `git write-tree` | `git_ops.semantic_candidate_ref` |
| 3 701 ms | 40 | 92,5 ms | `git add -A` | `git_ops.semantic_candidate_ref` |
| 3 352 ms | 36 | 93,1 ms | `git rev-parse <oid>^{tree}` | `git_ops.semantic_candidate_ref` |
| **2 546 ms** | **52** | 49,0 ms | `git rev-parse --git-common-dir` | `cli.main` |
| 1 702 ms | 17 | 100,1 ms | `git diff --name-only -z` | `git_ops.candidate_files` |
| 1 600 ms | 17 | 94,1 ms | `git ls-tree -r -z` | `cli.main` |
| 1 577 ms | 17 | 92,8 ms | `git ls-files -z --` | `cli.main` |

### Repeticiones de la clave de familia dentro de una misma invocación

| llamadas de más | argv |
|---|---|
| +110 (55 + 55) | `git rev-parse --show-toplevel` |
| +46 (29 + 17) | `git rev-parse --git-common-dir` |
| +20 | `git add -A` |
| +20 | `git rev-parse <oid>^{tree}` |
| +20 | `git write-tree` |
| +16 | `git ls-files -z --` |
| +16 | `git ls-tree -r -z` |
| +6 | `git diff --name-only -z` |

`rev-parse --show-toplevel` sale de `git_ops.repository_root`, que no guarda nada: cada
llamada vuelve a preguntar al disco por una respuesta que no ha cambiado dentro de la
invocación. `common_git_dir` llama a `repository_root` y añade su propio `rev-parse`, lo que
explica que las dos familias encabecen la lista juntas.

## Coste de la captura por comando

Sobre las formas reales, no sobre `git --version`. Mediana de 15 repeticiones, repositorio
temporal con 12 ficheros y un commit:

| directo | con captura | sobrecoste | factor | argv |
|---|---|---|---|---|
| 38,8 ms | 95,1 ms | +56,4 | ×2,45 | `git rev-parse --show-toplevel` |
| 38,9 ms | 97,1 ms | +58,2 | ×2,50 | `git rev-parse --git-common-dir` |
| 41,3 ms | 97,0 ms | +55,7 | ×2,35 | `git rev-parse HEAD` |
| 47,0 ms | 97,6 ms | +50,7 | ×2,08 | `git write-tree` |
| 46,8 ms | 95,7 ms | +48,9 | ×2,05 | `git add -A` |
| 41,8 ms | 98,0 ms | +56,2 | ×2,35 | `git ls-files -z --` |
| 45,5 ms | 98,7 ms | +53,2 | ×2,17 | `git ls-tree -r -z HEAD` |
| 42,5 ms | 97,3 ms | +54,7 | ×2,29 | `git diff --name-only -z` |
| 55,9 ms | 107,2 ms | +51,3 | ×1,92 | `git status --porcelain` |

**Sobrecoste mediano: 54,7 ms por comando.** Es el precio de la contención: ningún proceso
puede sobrevivir a su runner. La conclusión no es quitar la captura, es **emitir menos
comandos**: cada repetición evitada ahorra el comando *y* su contención, ~95 ms.

## Conclusión

Las repeticiones se dividen en tres grupos, y solo uno es mecánicamente reutilizable:

1. **Hechos de estructura** (`--show-toplevel`, `--git-common-dir` vía `git_ops`): la respuesta
   no cambia dentro de una invocación salvo que un comando de estructura la cambie. Reutilizable
   con invalidación demostrable. Implementado en el ticket 05: **116 → 54 llamadas, 8,8 s → 2,8 s**
   en el caso mediano.
2. **Revalidación deliberada** (`status_barrier._lexical_root`, +25 y +25): una barrera de
   ciclo de vida que vuelve a comprobar identidad y alias del repositorio en cada uso. Repetir
   *es* su trabajo. No se cachea; abaratarla sería una decisión de producto, no una
   deduplicación.
3. **Instantáneas de estado** (`add -A` + `write-tree` + `rev-parse <oid>^{tree}` desde
   `git_ops.semantic_candidate_ref`, 116 comandos y 11,4 s en un caso): reutilizar una de estas
   exige demostrar que nada escribió en el árbol entre dos llamadas, incluidas escrituras de
   Python que ningún comando `git` delata. No es demostrable con las costuras actuales. La
   pregunta real es de producto: **por qué una invocación necesita 40 instantáneas semánticas**.
   Queda registrada en el mapa, no se toca aquí.

Ahorro medido realmente obtenido por el ticket 05, sin tocar `capture_command` ni una sola
aserción: **−17 % a −27 %** del tiempo del caso.

## Límites declarados

- Medido solo en Windows 11. El sobrecoste de contención en POSIX usa otro mecanismo
  (supervisor con sesión propia) y **no está medido aquí**. La lógica de deduplicación es
  común; la cifra de ahorro no se puede dar por hecha fuera de Windows.
- Una estimación previa de «50–64 % de ahorro» asumía que toda repetición era reutilizable.
  Era falsa: los grupos 2 y 3 de la conclusión no lo son. El ahorro real medido es −17 % a
  −27 %. Se deja escrita la estimación errónea y su corrección en vez de sustituirla en
  silencio.
- Medición en solitario, no bajo contención de ocho shards.
