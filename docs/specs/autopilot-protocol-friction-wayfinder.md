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
- [APF-07](../tickets/autopilot-protocol-friction/07-refuse-a-relative-origin-before-the-run.md)
- [APF-08](../tickets/autopilot-protocol-friction/08-say-where-the-verification-bundle-lives.md)

## Type
Wayfinding spec

## Status
Decidido el 2026-09-23: la frontera se cierra en la especificación del driver; ver «Decisión APF-06». Los tickets APF-01..08 están entregados.

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

## Decisión APF-06 (2026-09-23)

Con APF-01..08 instalados, q4 dio tres runs: `q4a-r1` ignoró el runner por completo (137 s,
0,42 $, 1/5 latentes, 0 llamadas al CLI); `q4b` 2 107 s, 9,14 $, 229 turnos, 0/5, merge a mano
fuera del runner como en q3; `q4c` 2 377 s, 9,55 $, 222 turnos, 1/5, único run que entregó por el
runner. Frente a skills-only sin runner: 144 s, 0,44 $, **3/5**. Clasificados los turnos, el
62–67 % (hasta el 71 % del coste) es protocolo: el modelo conduce el CLI. Los tiempos de este párrafo se recalcularon desde la sesión; los registros anteriores y los «1 935 s» del Destination incluían la espera hasta el `collect` (q1 1 213 → 910 s, q2 1 935 → 1 382 s, q3 1 638 → 1 470 s).

Decisión del usuario, tras grilling: **no se sigue por aquí**. El destino de este mapa —bajar
las lecturas a cero y el coste por debajo de 2 $ arreglando el protocolo— no se alcanza
quitando muros, porque el modelo siempre llega al siguiente. Se invierte la dirección de
llamada: el runner es el proceso y el modelo solo hace el giro de skills como hoja, con
juicios tipados (Jev) donde hace falta significado y cascada a LLM fresco y a gate humano.
La arquitectura, los candidatos a medir y las rebanadas están en
[ticket-driver.md](ticket-driver.md). `ticket-autopilot` queda congelado e instalado.

## No especificado todavía

- ~~Si el `leaf-result` debe generarlo el runner~~ — decidido arriba: ni el runner ni el modelo
  lo generan; desaparece con el protocolo.
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
- **Los dos muros nuevos de q3, en la entrega.** Con APF-01..04 instalados, la máquina de etapas
  costó 112 turnos (q2: 121) y los gates de entrega 46 (q2: 13). Causas con turno: un origin
  relativo que `run` aceptó desde la raíz y el gate rechazó desde el worktree (T157), y el bundle
  de verificación escrito fuera del run sin que nadie dijera dónde va (T169). APF-07 y APF-08.

## Plan de tickets

| ID | Tipo | Modo | Bloqueado por | Qué produce |
|---|---|---|---|---|
| APF-01 | prototype | AFK | — | `leaf-result-template <run_id>` que emite el JSON esperado; medido en el run sembrado |
| APF-02 | task | AFK | — | cada error de `resume` nombra campo, recibido y esperado; test por error de T120/T128/T131 |
| APF-03 | task | AFK | — | `run` comprueba remoto y proveedor antes de Git; T45/T49/T51 reproducidos como tests |
| APF-04 | task | AFK | — | los ejemplos de `ticket-autopilot/SKILL.md` se ejecutan en un test; `python3` → `py -B` en Windows |
| APF-05 | task | AFK | APF-01 | el harness cuenta lecturas de código del runner por run y las publica como métrica |
| APF-06 | decisión | HITL | APF-01 | ¿el runner construye el `leaf-result` y el modelo solo rellena? Grilling + confirmación |
| APF-07 | task | AFK | APF-03 | `run` rechaza un origin relativo con el `set-url` absoluto escrito; causa reproducida en test |
| APF-08 | task | AFK | APF-01 | la plantilla a `verify` emite `verification-checkpoint`; el gate del bundle publica `detail` con directorio y remedio |

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
El resultado de q3 y q4 llegó: con plantilla y los siete arreglos siguientes, las lecturas de
código del runner no bajaron a cero (q4b: 36 `read` + 43 por shell) y el coste subió a 9 $.
El problema no era la plantilla ni ningún muro concreto. Este mapa no se revisa más; la
siguiente medida es el primer lote de candidatos de [ticket-driver.md](ticket-driver.md).
