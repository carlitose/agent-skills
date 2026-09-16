# La suite tarda 8,3 horas porque cada comando arranca un intérprete Python entero

## Artifact Graph
- Artifact ID: `artifact:autopilot-suite-execution-cost`
- Role: `spec`
- Standalone: true

### Children
- [01 Contener el objetivo en Windows lanzándolo suspendido](../tickets/autopilot-suite-execution-cost/01-windows-suspended-launch.md)
- [02 Repositorio de fixture construido una vez por clase](../tickets/autopilot-suite-execution-cost/02-shared-git-fixture.md)
- [03 Reparto por duración medida y timeout proporcional](../tickets/autopilot-suite-execution-cost/03-duration-aware-scheduling.md)

## Type
Architecture spec (con la evidencia diagnóstica que la motiva)

## Status
Medido el 16/09/2026 en Windows 11, Python 3.12.10, 22 núcleos, sobre el checkout local de
`agent-skills`. Las cifras provienen de `full-parallel-2.json` (464 registros de shard) y de
perfilado directo con `cProfile` sobre casos individuales. Ninguna medida de este spec
proviene de una ejecución hosted o de CI.

**Verificación final tras los tres slices (16/09/2026, 17:30 → 18:48, `--jobs 8`):**

| | referencia | final |
|---|---|---|
| check-time total | 29 882 s (8,3 h) | **14 317 s (3,98 h)**, −52 % |
| checks muertos por señal o timeout | 1 SIGKILL + 4 escenarios | **0** |
| checks | 277 | 190 (mismos casos, chunks por coste) |
| resultado | 7 fallos | **188 ok, 1 fallo, 1 skip POSIX** |
| reloj de pared | ~50 min *con 4 escenarios abortados* | 78 min *con todo completado* |

El reloj de pared **sube** y la razón importa: `autonomous-merge-grant` antes moría a los
365 s y ahora se ejecuta entero, 2 304 s. Antes no se medía el trabajo, se abandonaba. Con
todo completándose, el pared lo gobierna esa única unidad: 38 min de los 78. Un escenario
forward es indivisible para el planificador, así que la siguiente palanca no es más
paralelismo sino **partir ese escenario en sus casos**; queda anotado como trabajo futuro,
no como logro de este spec.

El único fallo restante, `test_autonomous_stack_reconciles_new_head_and_merges_child_without_revalidation`,
pasa aislado (125,8 s) y dentro de su escenario en solitario, y falló una vez con ocho
trabajos en paralelo tardando el doble (259,8 s). Es sensible a la contención y ajeno al
coste de ejecución; se diagnostica por separado.

**Primera verificación tras el slice 1 (16/09/2026, 13:44 → 14:35, `--jobs 8`):**

| | antes | después |
|---|---|---|
| check-time total | 29 882 s (8,3 h) | **19 238 s (5,34 h)**, −36 % |
| `capture_command` sobre `git --version` | 347 ms | **185 ms** |
| sobrecarga de contención por comando | +232 ms | **+69 ms** |
| checks muertos por señal | 1 (SIGKILL a 1800 s) | 0 por señal |
| reloj de pared | no terminaba en una asignación | 50 min |

De las 7 caídas de esa ejecución, ninguna es del slice 1: 4 eran escenarios forward matados
por **mi** primer estimador del slice 3 (media por suite: mediana 1 s, máximo 277 s; la media
no describe esa distribución), corregido a histórico por unidad; 3 eran `test_cli` heredando
`core.autocrlf=true` del operador, corregido haciendo que `CliTests` herede
`GitIsolatedTestCase` como el resto de suites.

## El síntoma

La verificación completa no cabe en ninguna asignación razonable. Medido:

| suite | segundos | % del total |
|---|---|---|
| `ticket-autopilot/tests/test_cli.py` | 15 884 | 53,2 % |
| `autopilot-forward-matrix` | 4 727 | 15,8 % |
| `ticket-autopilot/tests/test_worktree_gc.py` | 1 344 | 4,5 % |
| `ticket-autopilot/tests/test_post_merge_verification.py` | 731 | 2,4 % |
| resto (91 suites) | ~7 196 | 24,1 % |
| **total check-time** | **29 882 s** | **8,3 h** |

El paralelismo reparte ese coste, no lo reduce. Y lo reparte mal: `autopilot-forward-matrix
[2/16]` murió por SIGKILL a 1800,1 s, exactamente en el límite de la asignación.

Subir `--jobs` fue el parche equivocado: hace que el resultado dependa de la máquina, que es
justo lo que no queremos en un repo que se ejecuta en máquinas distintas.

## La causa raíz

Un caso representativo, `test_cli.CliTests.test_enabled_preflight_exclusion_stays_on_the_full_lifecycle`,
tarda **96 s**. Su perfil por tiempo acumulado:

```
119 llamadas   46,2 s   command_capture.capture_command      → 388 ms cada una
3162 llamadas  31,5 s   time.sleep  (espera del padre, 10 ms)
101 llamadas   37,2 s   git_ops.run_git
```

Micro-benchmark aislado del mismo comando (`git --version`, 8 repeticiones):

```
subprocess.run directo                :  102 ms
capture_command                       :  347 ms   (x3,4)
intérprete auxiliar -I -S -B en vacío :  145 ms
latencia del polling del padre        :   10 ms
```

`capture_command`
([`command_capture.py:287`](../../ticket-autopilot/scripts/autopilot/command_capture.py))
arranca **un intérprete Python completo por cada comando** —
[`_command_supervisor.py`](../../ticket-autopilot/scripts/autopilot/_command_supervisor.py) —
lo mete en un Job object de Windows y solo entonces lo libera creando un fichero `release`
que el hijo detecta con un bucle `time.sleep(0.01)`. El supervisor existe por una razón
correcta: el objetivo no debe ejecutarse antes de que la contención esté establecida. El
coste de esa corrección, sin embargo, es un **impuesto fijo de ~245 ms por comando**,
idéntico en cualquier máquina.

Todo `git` del runner pasa por ahí: `git_ops._run_captured` es el único camino. Un test que
ejecuta 119 comandos paga 29 s solo en contención. La suite entera ejecuta ese camino
decenas de miles de veces.

Dos hipótesis plausibles quedaron **descartadas por medición**, y no deben reabrirse sin
datos nuevos:

- `-B` (caché de bytecode desactivada) no es el problema: 389 ms vs 373 ms por invocación
  del CLI, un 4 %.
- La granularidad del `sleep` del lado del padre tampoco: bajarla de 10 ms a 0,5 ms mueve el
  coste de 347 ms a 338 ms. Los 232 `sleep` por comando son espera legítima mientras el hijo
  trabaja, no latencia desperdiciada.

## Consecuencia colateral: flakiness dependiente de carga

`test_provider_command_bounds.test_accepted_create_timeout_requires_readback_not_a_duplicate_create`
falló en la ejecución completa con `deadline 0.5s exceeded`. El deadline del test es de 0,5 s
y el camino que ejerce cuesta 0,347 s en una máquina ociosa. El margen es de 150 ms. Bajo
carga desaparece. No es un defecto del código bajo prueba: es el mismo impuesto de
contención, medido contra un presupuesto que no lo contempla.

## Objetivos

1. Que la verificación completa quepa en una asignación de una sola invocación, en una
   máquina modesta, sin ajustar `--jobs`.
2. Que el coste por comando capturado deje de estar dominado por el arranque de un
   intérprete auxiliar. Esto acelera **también las ejecuciones reales del runner**, no solo
   los tests.
3. Que ningún shard muera por timeout por estar mal balanceado.

## No objetivos

- No se relajan las garantías de contención, ni los bounds de salida, ni la semántica de
  timeout. Un comando más rápido que pierda propiedad del árbol de procesos es una
  regresión, no una mejora.
- No se reduce cobertura. Ningún caso se borra ni se marca `skip` para ganar tiempo.
- No se toca la ejecución hosted ni la verificación con proveedor en vivo.
- No se arregla aquí el defecto funcional observado de paso en
  `test_enabled_preflight_exclusion_stays_on_the_full_lifecycle` (`excluded_projection["plan"]`
  era `None` en shard y `ok` en aislamiento). Es un hallazgo adyacente que merece su propio
  diagnóstico.

## Invariantes que la implementación debe preservar

Estos son el contrato actual de `capture_command`. Cualquier slice que los rompa está mal,
por rápido que sea:

1. El objetivo **no se ejecuta** hasta que la contención del árbol de procesos está
   establecida. Un fallo al contener significa que no corrió nada.
2. `stdout`/`stderr` pertenecen **solo** al objetivo. Ningún proceso auxiliar escribe en
   ellos.
3. `stdin` heredado, `argv` literal y el entorno del objetivo llegan intactos.
4. La salida está acotada por `max_output_bytes`; excederlo es un fallo, nunca un resultado
   truncado que se presente como completo.
5. El estado de salida del objetivo viaja por un canal separado y acotado (8192 bytes), no
   mezclado con la salida.
6. Un timeout produce un fallo que declara el resultado **incierto**: una operación mutante
   puede haber tenido efecto y debe reobservarse antes de repetirla.
7. La limpieza termina el árbol completo, verificando pertenencia al job antes de terminar.
   Nunca se termina por PID suelto ni por un handle no verificado.
8. La cancelación cooperativa (`cancel_event`) sigue siendo observable antes y después de la
   liberación del objetivo.

## Comportamiento objetivo

### Slice 1 — Contención sin intérprete auxiliar, solo en Windows

En Windows el lanzamiento del objetivo se hace **directamente**, sin proceso Python
intermedio: crear el proceso con `CREATE_SUSPENDED | CREATE_NEW_PROCESS_GROUP` mediante un
lanzador `ctypes` (`CreateProcessW`), asignarlo al Job object, y solo entonces
`ResumeThread`. La suspensión sustituye al handshake por fichero: el objetivo no puede correr
antes de la contención porque no está planificado. Esto elimina el intérprete auxiliar
(145 ms) y el handshake (~50 ms). El lanzador debe gestionar explícitamente la herencia de
los handles de las pipes.

**POSIX no se toca.** La decisión está tomada sobre una lectura del código, no sobre
preferencia: el watchdog que mata el grupo si el llamante muere
(`_command_supervisor.py`, `if os.name == "posix"`) existe **solo** en POSIX, y es una
garantía real que un hilo del llamante no puede sustituir, porque un hilo muere con su
proceso. En Windows esa misma garantía ya la da el Job object, creado con
`KILL_ON_JOB_CLOSE` (`command_capture.py:91`): si el llamante muere, el handle se cierra y
los miembros mueren con él.

De ahí que en Windows el supervisor aporte **únicamente** el handshake de liberación, que es
exactamente lo que la suspensión sustituye. Se elimina sin perder ninguna garantía. En POSIX
aporta watchdog y liderazgo de sesión, y se conserva íntegro; su intérprete es además mucho
más barato ahí que los 145 ms medidos en Windows, y la plataforma donde duele está medida y
es Windows.

Coste esperado por comando: **~347 ms → ~120-150 ms**. Es una estimación derivada del
benchmark, no una medida; el ticket que la implemente debe volver a medir.

Como el presupuesto de `test_provider_command_bounds` deja de estar al límite, su flakiness
bajo carga debería desaparecer. El deadline de 0,5 s se mantiene tal cual: si el camino se
abarata, el test deja de ser marginal sin relajar nada.

### Slice 2 — Fixtures de repositorio compartidos

Cada caso reconstruye su repositorio con `git init` + `git config` + `git add` + `git commit`,
medido entre 260 y 330 ms por llamada, ~700 ms por caso. La plantilla se construye **una vez**
por clase (o por proceso) y cada caso trabaja sobre una copia de directorio.

`git_test_support.isolated_git_environment` ya aísla la configuración por clase; el aislamiento
no cambia. Lo que cambia es de dónde sale el repositorio inicial.

Requisito: la copia debe preservar el contenido byte a byte, incluidos finales de línea y el
estado del índice. Un repositorio copiado que difiera del inicializado invalidaría los tests
de fidelidad de texto en Windows.

### Slice 3 — Planificación del harness por duración medida

`scripts/test-local.mjs` reparte hoy los checks por posición (`position % total`,
[`selectShard`](../../scripts/test-local.mjs)), con un `--chunk-cases` fijo de 3 y un timeout
fijo de 1800 s por invocación, independientemente del tamaño del chunk. De ahí el SIGKILL del
shard de la forward matrix.

Objetivo:

- Persistir las duraciones observadas por caso/escenario y usarlas para chunkear por **coste
  estimado**, no por número de casos.
- Repartir los chunks longest-first entre shards en vez de round-robin por posición.
- Que la asignación de timeout sea proporcional al coste del chunk, con un mínimo.
- Primera ejecución sin histórico: comportamiento actual, degradación explícita, nunca un
  fallo.

El fichero de duraciones es caché reconstruible, no una entrada de verificación: un histórico
ausente, corrupto o obsoleto degrada al reparto actual y se dice en el informe.

## Alternativas consideradas

- **Supervisor persistente en pool**: un solo proceso auxiliar atendiendo muchos comandos por
  pipe. Amortiza el arranque, pero complica la contención (en Windows un proceso pertenece a
  un único job; haría falta anidamiento) y mantiene vivo un proceso con más autoridad de la
  necesaria entre comandos. Descartada frente a `CREATE_SUSPENDED`, que elimina el auxiliar en
  vez de reciclarlo.
- **Bajar la granularidad del polling**: medida, vale 9,5 ms por comando. Irrelevante.
- **Reducir `-B`**: medido, 4 %. Irrelevante.
- **Ejecutar el CLI in-process en los tests**: `test_cli` ya tiene ambos caminos
  (`resume_events` por subproceso, `resume_events_in_process`). Convertir más casos al camino
  in-process ahorraría ~380 ms por invocación, pero deja de ejercer el límite de proceso real.
  Queda fuera de este spec: es una decisión de cobertura, no de coste.
- **Subir `--jobs`**: ya probado. Hace el resultado dependiente de la máquina sin reducir el
  trabajo absoluto.

## Modos de fallo a cubrir

- El lanzador `ctypes` de Windows falla al crear, asignar o reanudar: debe producir un fallo
  de contención con el objetivo **no ejecutado**, no un objetivo suelto fuera del job.
- `ResumeThread` falla tras una asignación correcta: el job debe terminarse igualmente.
- Handles de pipe filtrados por herencia mal configurada: se detecta porque la lectura no
  alcanza EOF; el test debe distinguir ese caso de un objetivo colgado.
- Plantilla de repositorio corrupta o copia parcial: el caso debe fallar de forma visible, no
  ejecutar contra un repositorio a medias.
- Caché de duraciones ausente o inconsistente con los ids actuales: degradación al reparto
  actual, reportada.

## Seguridad y datos

El slice 1 toca el camino que garantiza que ningún proceso hijo sobreviva a un run. Un fallo
aquí deja procesos huérfanos con acceso al checkout. Los tests de bounds existentes
(`test_command_bounds`, `test_posix_command_bounds`, `test_command_capture_failures`,
`test_provider_command_bounds`) son la red de seguridad y deben pasar **sin modificarse**;
modificar uno de ellos para acomodar la implementación exige justificación explícita en el
ticket, no un ajuste silencioso.

## Estrategia de verificación

- **Unit**: los bounds de captura existentes, sin cambios, en Windows y POSIX.
- **Integration**: una suite representativa que hoy dependa de git (por ejemplo
  `test_docs_only`) antes/después, con la duración registrada.
- **System**: la verificación completa con `--jobs 1` y con el default, comparando el
  check-time total contra las 29 882 s de referencia.
- **Medición explícita**: el benchmark `git --version` raw vs `capture_command` debe volver a
  ejecutarse y reportarse en el handoff. Las cifras de este spec son el punto de partida, no
  una expectativa que se pueda dar por cumplida sin medir.
- **Manual**: ninguno.
- **Live**: ninguno.

Criterio de aceptación observable: la verificación completa termina sin ningún shard
terminado por señal, y el check-time total cae respecto a la referencia medida en una
proporción que el handoff documenta con números reales.

## Preguntas abiertas

1. ¿El lanzador `ctypes` de Windows sustituye a `subprocess.Popen` solo para el objetivo, o
   también para el resto de usos del módulo? (Propuesta: solo el objetivo.)
2. ~~¿El watchdog POSIX pasa a un hilo del llamante?~~ **Resuelta**: no se toca POSIX. El
   watchdog es una garantía que un hilo no puede dar, y en Windows el Job object con
   `KILL_ON_JOB_CLOSE` ya la cubre. El slice 1 es Windows-only.
3. ¿La caché de duraciones se versiona en el repo o vive en el directorio temporal del
   usuario? Versionarla la hace útil en la primera ejecución de cada máquina, pero la
   convierte en un fichero que cambia en casi cada commit. **Asunción para desbloquear**:
   temporal del usuario, reconstruible, fuera del control de versiones.
