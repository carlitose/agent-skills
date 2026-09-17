---
ticket_schema: 1
ticket_id: "01"
execution_mode: AFK
blocked_by: []
---

# Contener el objetivo en Windows lanzándolo suspendido, sin intérprete supervisor

## Artifact Graph
- Artifact ID: `artifact:suite-cost-windows-suspended-launch`
- Role: `ticket`
- Parent: [autopilot-suite-execution-cost.md](../../specs/autopilot-suite-execution-cost.md)

## Parent Spec
[autopilot-suite-execution-cost.md](../../specs/autopilot-suite-execution-cost.md)

## What to Build
En Windows, `capture_command` deja de arrancar `_command_supervisor.py` y lanza el objetivo
directamente con `CREATE_SUSPENDED | CREATE_NEW_PROCESS_GROUP`, lo asigna al Job object y solo
entonces lo reanuda. La suspensión sustituye al handshake por fichero `release`.

POSIX no se toca: allí el supervisor aporta el watchdog de grupo y el liderazgo de sesión, que
son garantías reales. Cubre la sección «Slice 1» del spec y los invariantes 1-8.

## Acceptance Criteria
- [x] En Windows no se crea ningún proceso Python auxiliar por comando capturado: un conteo de
      procesos hijo durante una captura observa solo el objetivo. Cubierto por
      `test_windows_launches_no_auxiliary_python_process`, que observa el único `Popen`
      realizado y comprueba que su `argv` es el del objetivo.
- [x] El objetivo no ejecuta ninguna instrucción antes de estar asignado al Job object. La
      asignación ocurre inmediatamente después de `Popen`, antes de arrancar los lectores.
- [x] Un fallo en creación, asignación o reanudación produce un `CaptureFailure` de contención
      con el objetivo no ejecutado, y nunca un proceso fuera del job. Cubierto por
      `test_windows_release_failure_terminates_target_before_it_can_execute`: el proceso
      termina y su fichero marcador no existe.
- [x] Una reanudación que no deja el hilo ejecutable se reporta en el acto en vez de esperar
      al timeout. `ResumeThread` devuelve el contador **anterior**; un valor mayor que uno es
      un fallo. Cubierto por
      `test_windows_elevated_suspend_count_fails_instead_of_waiting_for_timeout`.
- [x] `stdout`/`stderr` del resultado contienen exactamente la salida del objetivo, byte a byte,
      sin mezcla de ningún auxiliar.
- [x] `stdin` heredado, `argv` literal y entorno del objetivo llegan intactos.
- [x] El bound `max_output_bytes`, el bound de estado de 8192 bytes, la semántica de timeout
      incierto y la cancelación cooperativa siguen comportándose igual.
- [x] `test_command_bounds`, `test_posix_command_bounds` y `test_provider_command_bounds`
      pasan **sin modificarse**. Las cuatro suites de límites juntas: 34 tests, OK, 4 skips.
- [ ] Colisión medida, registrada antes de implementar:
      `test_command_capture_failures.test_missing_or_invalid_target_status_never_returns_valid_stdout_as_complete`
      (`:117`) no está acotado por plataforma y suplanta el supervisor vía
      `patch("autopilot.command_capture.subprocess.Popen")` para validar el protocolo
      `result.json` (casos `missing`, `shape`, `boolean`, `oversize`, `malformed`). Ese
      protocolo deja de existir en Windows por diseño, luego el test **no puede** pasar sin
      modificarse. Se acota a POSIX y se añade cobertura Windows equivalente del mismo
      invariante: el estado de salida procede del sistema operativo y ningún proceso auxiliar
      puede falsificarlo. Reducir cobertura en lugar de trasladarla es una regresión.
- [x] El camino POSIX queda idéntico, verificado por diff: el `else` conserva
      `request.json`/`release`/`result.json` y `start_new_session=True` sin cambios de
      comportamiento. En este checkout Windows no se puede ejecutar; `test_posix_command_bounds`
      queda como skip declarado, no como paso.
- [x] El benchmark `git --version` raw vs `capture_command` se vuelve a medir y se reporta el
      antes/después real. Comparado contra un worktree limpio en `HEAD` (`44c26f3`) en la
      misma máquina: **215 ms con intérprete auxiliar → 115 ms con lanzamiento directo**.
      Estrés adicional: 120 capturas con 8 hilos en 8,026 s, 0 fallos y ningún proceso
      superviviente.

## Frontier
Done.

## Corrección posterior a la primera implementación
La primera versión dejaba dos huecos que produjeron `git.exe` vivos y suspendidos
(`ThreadState=5`, `ThreadWaitReason=5`) con sus padres ya muertos: los lectores se
arrancaban antes de asignar al Job, y un contador de suspensión ajeno se interpretaba como
liberación correcta. Ambos están corregidos y cubiertos; el análisis vive en
[windows-stderr-eof-stall.md](../../specs/windows-stderr-eof-stall.md).

## Step-by-Step Implementation Plan
1. Aislar el lanzamiento del objetivo tras una costura interna con dos implementaciones
   (Windows directa, POSIX por supervisor), para que el resto de `capture_command` —lectores,
   bounds, limpieza, cancelación— no cambie. Checkpoint: los tests de bounds siguen pasando
   con la costura introducida y ambas implementaciones delegando en el supervisor.
2. Implementar el lanzador `ctypes` `CreateProcessW` con `CREATE_SUSPENDED`, creando las pipes
   de salida con handles heredables explícitos y cerrando en el padre los extremos del hijo.
   Checkpoint: un comando trivial devuelve su salida completa y su código de salida.
3. Ordenar contención antes de ejecución: crear el proceso suspendido, asignarlo al job,
   verificar pertenencia, y solo entonces `ResumeThread`. Cualquier fallo intermedio termina el
   job y reporta contención. Checkpoint: los tests de fallo de contención existentes pasan.
4. Retirar en Windows la escritura de `request.json`/`release` y la lectura de `result.json`,
   tomando el código de salida directamente del objetivo. Checkpoint: el bound de 8192 bytes
   del estado deja de aplicar en Windows por construcción, y los tests que lo ejercen siguen
   verdes en POSIX.
5. Volver a medir el benchmark y registrarlo en el handoff.

## Testing Plan
- Automático: las cuatro suites de bounds sin modificar; `test_docs_only` como integración
  representativa, con duración antes/después.
- Automático: un test nuevo que observe que durante una captura en Windows no aparece ningún
  proceso Python adicional.
- Manual: ninguno.
- No disponible aquí: la verificación del camino POSIX en un POSIX real. Este checkout es
  Windows; el camino POSIX se preserva por no-cambio y se verifica por diff, no por ejecución.

## Out of Scope
- Cualquier cambio en el camino POSIX.
- Reutilización o pooling de procesos auxiliares.
- Cambiar los deadlines de los tests de bounds.
