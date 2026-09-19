---
type: source
title: "El lanzamiento suspendido de Windows puede dejar un `git.exe` sin liberar y esperar hasta el timeout"
identity_key: artifact:windows-stderr-eof-stall
identity_strength: stable
source_path: docs/specs/windows-stderr-eof-stall.md
source_digest: sha256:7b908240baa78de87b57c3ca146234e0a2a1d2b59fdb191697e4a894ef206a95
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-09-17
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# El lanzamiento suspendido de Windows puede dejar un `git.exe` sin liberar y esperar hasta el timeout

Compiled from `docs/specs/windows-stderr-eof-stall.md`. Identity is `artifact:windows-stderr-eof-stall`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-17** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"decisions":{"headings":[],"status":"not-identified"},"exclusions":{"headings":[],"status":"not-identified"},"goals":{"headings":[],"status":"not-identified"},"invariants":{"headings":[],"status":"not-identified"},"verification":{"headings":[],"status":"not-identified"}},"parts":[{"index":0,"path":"wiki/sources/artifact-windows-stderr-eof-stall.md","payload_bytes":5608,"payload_sha256":"7b908240baa78de87b57c3ca146234e0a2a1d2b59fdb191697e4a894ef206a95"}],"payload_bytes":5608,"payload_sha256":"7b908240baa78de87b57c3ca146234e0a2a1d2b59fdb191697e4a894ef206a95","schema":1,"source_digest":"sha256:7b908240baa78de87b57c3ca146234e0a2a1d2b59fdb191697e4a894ef206a95","source_identity":"artifact:windows-stderr-eof-stall","source_kind":"spec"} -->

| Topic | Source sections |
|---|---|
| goals | no matching section identified in the source; complete source retained |
| exclusions | no matching section identified in the source; complete source retained |
| decisions | no matching section identified in the source; complete source retained |
| invariants | no matching section identified in the source; complete source retained |
| verification | no matching section identified in the source; complete source retained |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":5608,"payload_sha256":"7b908240baa78de87b57c3ca146234e0a2a1d2b59fdb191697e4a894ef206a95","schema":1,"source_digest":"sha256:7b908240baa78de87b57c3ca146234e0a2a1d2b59fdb191697e4a894ef206a95","source_identity":"artifact:windows-stderr-eof-stall"} -->
```markdown
# El lanzamiento suspendido de Windows puede dejar un `git.exe` sin liberar y esperar hasta el timeout

## Artifact Graph
- Artifact ID: `artifact:windows-stderr-eof-stall`
- Role: `spec`
- Standalone: true

## Type
Bug analysis

## Status
Causa reproducida el 16/09/2026 en Windows 11. Corrección implementada; pendiente de una
verificación completa posterior al cambio.

## Síntoma original

En una orquestación real, la salida normal (`stdout`) alcanzó EOF en 0,45 s pero el canal de
errores (`stderr`) no cerró. El captador esperó hasta su límite de 300 s y marcó el comando
como fallido. Como planificar una ejecución necesita decenas de comandos `git`, el runner no
llegaba a arrancar.

La primera hipótesis fue que otro proceso —por ejemplo el EDR corporativo— retenía un handle
de la tubería. Era plausible, pero no estaba medida y resultó insuficiente.

## Reproducción y causa raíz

La inspección posterior encontró evidencia directa del mecanismo:

- Dos `git.exe` creados por verificaciones anteriores seguían vivos con sus procesos padre ya
  muertos.
- `Win32_Thread` mostró en ambos un único hilo con `ThreadState=5` y
  `ThreadWaitReason=5`: el proceso estaba **suspendido**, no terminado con una tubería retenida.

`autopilot-forward-matrix [2/12]` también agotó 1463,4 s durante esa ejecución, pero **no era
una reproducción del bloqueo**: aislado y ya corregidos otros fallos, el escenario completó
en ~26 min. El timeout anterior era 24,4 min porque la primera muerte a 365 s solo había
aportado ese suelo al histórico. La siguiente asignación queda en el máximo de 3600 s. No se
usa ese timeout como evidencia causal de la suspensión.

El slice 1 de [autopilot-suite-execution-cost.md](autopilot-suite-execution-cost.md) crea el
objetivo con `CREATE_SUSPENDED`, lo asigna a un Job object y lo libera con `ResumeThread`.
La inspección encontró dos mecanismos capaces de producir o prolongar exactamente ese estado;
no hay traza histórica suficiente para decidir cuál dejó cada uno de los dos zombis:

1. Los dos hilos lectores de salida se arrancaban **antes** de asignar el objetivo al Job.
   Bajo carga esa operación puede tardar; si el runner muere durante esa ventana, queda un
   proceso suspendido todavía no contenido.
2. Solo se comprobaba que `ResumeThread` no devolviera error. La API devuelve el contador de
   suspensión **anterior**: un valor mayor que 1 significa que nuestra llamada decrementó el
   contador pero el hilo sigue suspendido. Ese resultado se trataba como liberación correcta,
   por lo que el captador esperaba EOF hasta su timeout.

Documentación primaria:

- [`ResumeThread`](https://learn.microsoft.com/windows/win32/api/processthreadsapi/nf-processthreadsapi-resumethread)
  define ese valor de retorno y cuándo el hilo llega a ejecutarse.
- [`CreateToolhelp32Snapshot`](https://learn.microsoft.com/windows/win32/api/tlhelp32/nf-tlhelp32-createtoolhelp32snapshot)
  solo prescribe reintentar `ERROR_BAD_LENGTH` para snapshots de módulos. No respalda hacerlo
  para `TH32CS_SNAPTHREAD`; el reintento considerado inicialmente se descartó.

No hay evidencia para atribuir la suspensión adicional al EDR. Puede intervenir, pero el
defecto del captador es independiente: debía interpretar el contador y fallar de forma
acotada, cualquiera que fuese el actor que lo elevó.

## Corrección

En `ticket-autopilot/scripts/autopilot/command_capture.py`:

1. La asignación al Job sucede inmediatamente después de `Popen`, antes de crear lectores.
   Solo queda la ventana mínima e inevitable `Popen → assign`; el objetivo aún no puede
   ejecutar durante ella.
2. `_resume_windows_target` inspecciona el contador anterior de cada `ResumeThread`:
   - `1`: ese hilo ha quedado ejecutable;
   - `>1`: sigue suspendido y se informa inmediatamente;
   - `0xFFFFFFFF`: error Win32.
3. Una liberación no confirmada entra en la limpieza existente, que termina el Job, espera al
   proceso y verifica que el objetivo no ejecutó ninguna instrucción.

## Evidencia de regresión

- `test_windows_elevated_suspend_count_fails_instead_of_waiting_for_timeout` modela un retorno
  `2` y exige el diagnóstico `remain suspended`, en vez de esperar al timeout.
- `test_windows_release_failure_terminates_target_before_it_can_execute` fuerza un fallo de
  liberación real y comprueba que el proceso terminó y no creó su fichero marcador.
- Las cuatro suites de límites/captura: **34 tests, OK, 4 skips, 10,386 s**.
- Estrés directo: **120 capturas** de `git --version`, 8 workers, 8,026 s, 0 fallos.
- Benchmark comparado contra `HEAD` (`44c26f3`): 215 ms con intérprete auxiliar frente a
  115 ms con lanzamiento directo.

El escenario real `autonomous-merge-grant` terminó correctamente en ~26 min y no dejó un
`git.exe` suspendido. Falta como criterio de cierre una suite completa posterior al arreglo.

## Impacto y mitigación

`ticket-parse` y `ticket-emit` no pasan por esta captura y siempre siguieron disponibles. El
fallo afectaba a la orquestación automática y a cualquier verificación que encontrase la
suspensión bajo carga. Mientras se verificaba, el carril se podía ejecutar a mano en un
worktree sin fabricar autoridad de proveedor.

## No objetivos

- Atribuir el contador extra a un proceso concreto sin una traza de handles/hilos.
- Ignorar EOF o devolver salida parcial: convertiría un fallo visible en un resultado falso.
- Reanudar repetidamente hasta borrar contadores de suspensión que pertenecen a otro actor.
  Ante esa condición, el captador falla y termina su propio árbol.

```
