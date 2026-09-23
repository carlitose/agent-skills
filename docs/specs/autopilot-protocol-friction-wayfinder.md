# Por qué Autopilot es lento: la fricción del protocolo

## Artifact Graph
- Artifact ID: `artifact:autopilot-protocol-friction`
- Role: `wayfinder`
- Standalone: true

### Children
- [APF-01](../tickets/autopilot-protocol-friction/01-emit-leaf-result-template.md)
- [APF-02](../tickets/autopilot-protocol-friction/02-name-the-fix-in-every-resume-error.md)
- [APF-03](../tickets/autopilot-protocol-friction/03-preflight-run-before-touching-git.md)
- [APF-04](../tickets/autopilot-protocol-friction/04-make-the-skill-examples-runnable.md)
- [APF-05](../tickets/autopilot-protocol-friction/05-measure-runner-source-reads-as-regression.md)
- [APF-06](../tickets/autopilot-protocol-friction/06-decide-whether-the-runner-drives-the-leaf.md)

## Type
Wayfinding spec

## Status
Active

## Destination
Un run de Autopilot sobre el ticket sembrado del benchmark interno en el que **el modelo no
lea ni una línea del código fuente del runner** para completar el ciclo, y que por tanto
cueste y tarde una fracción de lo medido: por debajo de 2 $ y de 600 s por ticket, desde los
6,42 $ y 1 935 s del último run.

## Decisiones hasta ahora

### El diagnóstico: el modelo hace ingeniería inversa del runner en vez de usarlo

Perfil turno a turno del run q2 (`bench38-autopilot-q2.json`, sesión
`2026-09-22T20-38-46-275Z_01a0cad7…`), contrastado con q1:

| Fase | Turnos q2 | Qué hacía |
|---|---|---|
| Orientación | 1–14 | leer TASK, SKILL.md ×3, `--help` ×2, dos `status` mal invocados |
| Spec y tickets | 15–44 | escribirlos, emitirlos, corregir un ejemplo roto de la skill |
| Arrancar el runner | 45–54 | **5 intentos de `run`**: 2 `target-fetch-failed`, 1 «provider cannot be detected», 1 usage; luego orientarse en el worktree |
| **Implementar la feature** | **55–60** | **6 turnos**: 4 `write`, 1 `read` del test existente, 1 test |
| Construir el `leaf-result` a mano | 61–175 | **115 turnos**: 39 lecturas de código del runner, 36 `grep` sobre él, 19 `py -c` calculando árboles y digests, 9 ejecuciones de tests para producir evidencia, 10 `resume` de los que 5 son rechazados |

El trabajo real cabe en 6 turnos. Los otros 170 son el modelo descubriendo, leyendo el código,
qué JSON quiere el runner. Los números que lo fijan, recalculados por `apf59_profile.py` desde
las dos sesiones (rechazado = resultado con error o `"ok": false`):

| Medida | q1 | q2 |
|---|---|---|
| turnos | 136 | 176 |
| lecturas de código fuente del runner | 22 | 41 |
| bytes leídos que son código del runner | 76 KB de 207 (**37 %**) | 136 KB de 259 (**53 %**) |
| `grep` sobre el runner | 26 | 37 |
| `resume` rechazados | 0 de 5 | 5 de 10 |
| turnos con más de una llamada | 5 de 136 | **0 de 176** |

Es **estructural**: aparece en los dos runs. Y explica la subida entre q1 y q2 mejor que
cualquier otra cosa: q2 se perdió más veces en el mismo laberinto.

### Los cinco muros contra los que chocó, con su turno

1. **El `leaf-result` no tiene plantilla.** El esquema 3 vive en `leaf_protocol.py:578
   validate_leaf_result` y `cli.py:2629 _verification_checkpoint_leaf_result`; la skill lo
   describe en una frase. El modelo leyó `leaf_protocol.py` seis veces seguidas (turnos 67–72)
   y `cli.py` ocho, y aun así falló tres `resume` con «bounded leaf results require an active
   leaf stage» (T120), «another ticket is already active» (T128) y «quality leaf result requires
   structured quality evidence» (T131), volviendo al código tras cada uno.
2. **Los errores de `resume` no dicen qué falta.** Cada rechazo nombra el invariante violado,
   no el campo ni la forma correcta. Cada uno costó entre 3 y 12 turnos de lectura.
3. **`run` falla tarde y a ciegas.** `target-fetch-failed: cannot refresh configured target`
   dos veces y «remote provider cannot be detected» una, sobre un repo sembrado sin remoto:
   el runner exige un remoto que la tarea no tiene y lo descubre tras tocar Git.
4. **La skill tiene un ejemplo roto.** `--events` con `leaf-result` como si fuera un fichero
   produjo `[Errno 2] No such file or directory: 'leaf-result'` (T63). Y `python3` en Windows
   resolvió al alias de la Microsoft Store (T137): «Python was not found».
5. **Ninguna llamada se agrupó.** La regla de #55 está escrita en `OPERATING-DEFAULTS.md`; q2
   la llevaba instalada y q1 no. q1 agrupó 5 turnos de 136; q2, 0 de 176. Una regla escrita no
   fuerza nada, y aquí ni siquiera se correlaciona.

### Lo que este diagnóstico descarta

- **No es el modelo implementando mal.** La feature sale en 6 turnos y pasa la suite visible.
- **No es el tamaño del corpus.** Entre q1 y q2 el Markdown que lee el agente creció 1 070 bytes.
- **No son las correcciones anteriores.** #27/#45/#48/#35/#42 no tocan este camino; #54 solo
  actúa si hay compactación, y en este run hubo cero.

## No especificado todavía

- Si el `leaf-result` debe **generarlo el runner** a partir del estado del ledger y dejarle al
  modelo solo rellenar hallazgos y evidencia, o si basta con una plantilla y errores que
  nombren el campo. Es la decisión que más cambia el destino. APF-06.
- Cuánto del coste es **latencia de la API por turno** y cuánto contexto releído: la sesión
  no guarda tiempos por llamada; se mide en el prototipo de APF-01.
- Si el `run` sobre un repositorio sin remoto debe **funcionar en modo local** o **rechazarse
  antes de tocar nada** con el mensaje exacto. APF-03 lo decide con la evidencia de T45–T51.

## Fuera de alcance

- Cambiar el modelo, el nivel de razonamiento o el prompt del benchmark.
- Relajar los invariantes del kernel (CandidateRef exacto, evidencia direccionada, gates).
- Tocar `execute-ticket` para que salte etapas.

## Frontera / aristas que bloquean

- **Plantilla del `leaf-result`.** Sin ella, cada run rehace la ingeniería inversa. Desbloquea:
  un comando que emite el JSON esperado para el ticket activo y su etapa. APF-01.
- **Errores que nombran el campo.** Sin ello, cada rechazo cuesta lecturas. Desbloquea: cada
  `TransitionError`/`LeafProtocolError` de `resume` incluye campo, valor recibido y forma
  esperada. APF-02.
- **Preflight de `run`.** Desbloquea: remoto/proveedor comprobados antes de crear worktree, con
  la salida exacta. APF-03.
- **Ejemplos ejecutables.** Desbloquea: cada ejemplo de la skill se ejecuta en un test. APF-04.
- **Medida de regresión.** Sin ella, no se sabe si el destino se alcanzó. Desbloquea: contar
  lecturas de código del runner por run y fallarlo si son > 0. APF-05.
- **La decisión de arquitectura.** APF-06, HITL, con grilling.

## Plan de tickets

| ID | Tipo | Modo | Bloqueado por | Qué produce |
|---|---|---|---|---|
| APF-01 | prototype | AFK | — | `leaf-result-template <run_id>` que emite el JSON esperado; medido en el run sembrado |
| APF-02 | task | AFK | — | cada error de `resume` nombra campo, recibido y esperado; test por error de T120/T128/T131 |
| APF-03 | task | AFK | — | `run` comprueba remoto y proveedor antes de Git; T45/T49/T51 reproducidos como tests |
| APF-04 | task | AFK | — | los ejemplos de `ticket-autopilot/SKILL.md` se ejecutan en un test; `python3` → `py -B` en Windows |
| APF-05 | task | AFK | APF-01 | el harness cuenta lecturas de código del runner por run y las publica como métrica |
| APF-06 | decisión | HITL | APF-01 | ¿el runner construye el `leaf-result` y el modelo solo rellena? Grilling + confirmación |

## Medida de regresión (APF-05, entregado)

La métrica ya no se calcula a mano. `bench38_harness.py collect` publica `runner_use` en el
registro de cada brazo, `annotate <brazo> <q>` la añade a un registro ya recogido desde su
sesión guardada sin relanzar nada, y `compare` la muestra por brazo. Las definiciones viven en
la docstring de `runner_use()`; recalculadas sobre q1 y q2 dan exactamente la tabla de arriba:
22 y 41 lecturas, 76 y 136 KB, 26 y 37 `grep`, 0 de 5 y 5 de 10 `resume` rechazados, 5 y 0
turnos con más de una llamada. `bench38_runner_use_test.py` fija esa coincidencia con la mapa.

Tres contadores nuevos, publicados aparte para no mover los 22/41 de la tabla:

- `template`: llamadas a `leaf-result-template` (APF-01); 0 en q1/q2 por construcción.
- `runner_test_reads`: lecturas bajo `ticket-autopilot/tests/`; 0 en q1, 1 en q2. El run q3
  desplazó parte de la lectura del runner a sus tests, que la definición de la tabla no cuenta.
- `runner_shell_reads`: `sed -n`/`cat`/`head`/`tail` sobre `ticket-autopilot/scripts` desde
  `bash`; **22 en q1 y 38 en q2**. La tabla cuenta solo la herramienta `read`, así que sus
  22/41 son un límite inferior: la lectura real de código del runner fue 44 en q1 y 79 en q2.
  El diagnóstico no cambia de signo; cambia de tamaño.

## Próxima revisión
Resultado del prototipo APF-01 sobre el ticket sembrado: si con plantilla las lecturas de
código del runner bajan a cero y el coste baja de 2 $, APF-06 se decide con datos. Si no
bajan, el problema no era la plantilla y la mapa vuelve al diagnóstico. La medida es un
solo run (q3) con APF-01..04 instalados a la vez: combinada, no atribuible a la plantilla sola.
