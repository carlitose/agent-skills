# Contrato de verificación local: gate rápido y cobertura completa

## Artifact Graph
- Artifact ID: `artifact:local-verification-profile-contract`
- Role: `spec`
- Parent: [Mapa de verificación local](suite-cost-one-percent-wayfinder.md)

### Children
- [06 Implementar el gate rápido sin recortar `full`](../tickets/suite-cost-one-percent/06-test-cli-consolidation.md)

## Type
Decision

## Estado y confirmación

Decisión confirmada por el usuario el 16/09/2026 tras la entrevista `grilling` del ticket 04.
Respuesta final: **«Si conferma»**, mensaje `9886d004`, a las
`2026-09-16T20:07:43.645Z`, en la sesión Pi
`2026-09-16T10-53-30-845Z_01a0a9d9-af5c-70dc-9d3b-d5aee3d1124d.jsonl`.

El mapa mantiene este contrato vigente como hijo. El
[04 completado](../tickets/suite-cost-one-percent/done/04-profile-contract-decision.md)
conserva la decisión histórica y su fuente exacta; esta relación no altera su receipt.

La confirmación permite registrar este contrato y reformular el ticket 06. No acredita una
implementación, una corrida satisfactoria, integración, publicación ni autorización de merge.

## Objetivo y comportamiento actual

Reducir la espera cotidiana sin eliminar escenarios de la verificación completa. Actualmente
`npm test` ejecuta `quick`, que no incluye `test_kernel` ni la selección e2e de este contrato;
`npm run test:full` ejecuta `full`. El ticket 06 ampliará el gate por defecto existente, sin
crear otro planificador ni otro sistema de perfiles.

El presupuesto vigente es **≤240 s de reloj con `--jobs 8`** en la máquina de referencia
Windows, medido como reloj del proceso completo: descubrimiento, preparación, ejecución y
cierre del harness. Una única corrida decide contra ese umbral y el check-time se reporta por
separado. El nombre histórico «one-percent» ya no expresa una relación literal.

El objetivo original era ≤150 s y se midió sobre la base anterior a integrar el baseline
01–05 y la corrección PRQ-01. Mediciones reales del mismo gate y la misma selección:

| Base | Host | Condición | Reloj |
|---|---|---|---|
| Anterior a la integración | Windows | `--jobs 8` | 134,5 s |
| Integrada (`3294b48`) | Windows | `--jobs 8` | 150,84 s |
| Integrada (`3294b48`) | Windows | `--jobs 4` | 201,4 s |
| Integrada (`6fc7bc5`) | Windows | `--jobs 8` | 189,0 s |
| Integrada (`3294b48`) | Linux (WSL2 nativo) | `--jobs 8` | 26,3 s |
| Integrada (`6fc7bc5`) | Linux (WSL2 nativo) | `--jobs 8` | 29,2 s |

El aumento proviene de los casos que 01–05 y PRQ-01 añadieron a `test_kernel`, que el gate
ejecuta completo por decisión 1; no hay regresión conocida del harness ni de su planificación.
Las tres mediciones Windows con la misma selección y sin cambios de coste reales —134,5 s,
150,84 s y 189,0 s— muestran una dispersión superior al 25 % atribuible al host: contención de
procesos, antivirus y coste de `sh.exe` de Git para Windows. Un umbral cercano a esas cifras
convierte el gate en intermitente, de modo que el valor de **240 s es una decisión humana
registrada** que absorbe esa varianza; no refleja una mejora de coste ni un límite inferido de
la medición. Windows y WSL2 Linux son los entornos verificados; macOS no está disponible y no
se declara.

Los aproximadamente 120 s propuestos durante la entrevista eran una **estimación**, no un
resultado. La suma de costes dividida entre ocho no demuestra el reloj: influyen la duración
máxima indivisible, la distribución y la contención.

## Decisión 1: gate por defecto

Ampliar `quick`, conservando todo lo que selecciona actualmente, con:

1. Todos los casos de `ticket-autopilot/tests/test_kernel.py`.
2. Exactamente estos diez métodos de `test_cli.CliTests`, en
   `ticket-autopilot/tests/test_cli.py`:

| Área representada | Identificador |
|---|---|
| Preflight y ciclo de vida | `test_enabled_preflight_exclusion_stays_on_the_full_lifecycle` |
| Gate antes de la primera mutación | `test_autonomous_first_mutation_gates_if_queue_requirement_disappears` |
| Cola y replay | `test_autonomous_merge_queue_waits_and_replays_without_reenqueue` |
| Reconciliación y base del destino | `test_ignored_stack_reconciliation_gates_on_tracked_target_base` |
| Merge autónomo y checks | `test_autonomous_merge_gates_pending_and_failed_checks_then_retries` |
| Preservación del worktree sucio | `test_cleanup_never_discards_dirty_isolated_worktree` |
| Hold, reopen y cancel | `test_hold_reopen_and_cancel_are_receipted_cli_transitions` |
| Invalidación del candidato | `test_candidate_invalidation_resets_stale_preparation_before_delivery_retry` |
| Proyección exacta de completion | `test_granted_completion_projection_delivers_only_exact_done_source_path` |
| Adopción de una copia de integración | `test_integrate_adopts_single_parent_integration_copy_reachable_on_main` |

Los diez identificadores existen en el árbol inspeccionado. Son una muestra concreta, no una
prueba de exhaustividad por módulo o por familia. La selección debe ser exacta, sin filtros
por subcadena que incorporen otros métodos; si un identificador falta, se debe informar del
error, no omitirlo silenciosamente. Ninguna selección puede ejecutar dos veces el mismo caso.

## Decisión 2: cobertura y obligatoriedad de `full`

- `full` conserva **todos los tests actuales**, incluidos los diez del gate y los que no
  están en él. No se ejecuta el gate como una segunda pasada dentro de `full`.
- Es obligatorio antes de un PR que toque el runner o el harness; las rutas identificadas
  en la entrevista fueron `ticket-autopilot/scripts/` y `scripts/test-local*`.
- Es obligatorio antes de release. La forward matrix sigue siendo el comando explícito
  adicional de las releases de la familia de workflows, conforme al ticket 01.
- Un PR exclusivamente de documentación pasa con el gate rápido.
- Este contrato no introduce CI hospedado ni una exención general para otros ámbitos de
  código; sus requisitos existentes no se sustituyen por la regla de solo documentación.

## Decisión 3: riesgo aceptado

Se acepta que regresiones específicas de variantes fuera de los diez seleccionados —otros
puntos de caída y recuperación, compatibilidad CRLF y combinaciones de estados— se detecten
al ejecutar `full`, no necesariamente durante cada iteración rápida. No se acepta perder su
cobertura completa.

Quedar fuera del gate no convierte un fallo en válido: los casos costosos o con una
investigación de flake abierta siguen en `full`. No se permiten skips, reintentos que oculten
fallos, relajación de aserciones ni cambios de contención para cumplir el presupuesto. Si el
gate supera el presupuesto vigente, se informa del incumplimiento con su medición real; no se
cambia esta selección por inferencia ni se reescribe el presupuesto sin una decisión humana
registrada.

## Decisión 4: conservar los candidatos a consolidación

No borrar, fusionar ni migrar masivamente a la forma del kernel ningún test en este cambio.
En particular, se conservan los seis subconjuntos de líneas del ticket 03:

- `test_off_mode_uses_the_complete_delivery_lifecycle_without_projection_state`
- `test_existing_manual_run_grant_continues_an_open_pr_through_exact_head_merge`
- `test_stage_gate_reason_is_validated_before_drift_and_visible_in_status`
- `test_ignored_candidate_promotion_gates_before_commit_or_provider`
- `test_resume_drives_stages_and_invalidates_stale_downstream_evidence`
- `test_pre_feature_schema_three_ledger_remains_manual_on_status_and_resume`

También se conservan separados los tres pares con conjuntos de líneas idénticos:

- `test_autonomous_grant_merges_an_eligible_exact_head_without_a_prompt` y
  `test_autonomous_merge_accepts_github_has_hooks_success_state`.
- `test_delivery_replays_after_crash_immediately_after_branch_creation` y
  `test_delivery_replays_after_crash_immediately_after_commit`.
- `test_hold_repoints_the_linking_map_and_reopen_repoints_it_back` y
  `test_resume_accepts_unchanged_crlf_ticket_sources`.

Cubrir las mismas líneas no demuestra equivalencia de aserciones ni de comportamiento. Una
futura consolidación necesitaría evidencia de equivalencia y alcance propios; no forma parte
del 06 reformulado.

## Evidencia y correcciones

- [Ticket 02: histograma de Git](../research/runner-git-command-histogram.md): en el caso
  mediano, 395 comandos y 265 repeticiones por invocación/directorio; sobrecoste mediano de
  captura de 54,7 ms. Solo los hechos de estructura resultaron reutilizables con las costuras
  actuales. No justifica cachear instantáneas semánticas ni barreras de identidad.
- [Mapa y medidas previas](suite-cost-one-percent-wayfinder.md): `full` pasó de 14 322 s
  de check-time / 78 min de reloj a 7 803 s / 18 min tras 01 y 05. Son medidas históricas de
  Windows, no una ejecución del nuevo gate. En `full-t05.json`, las suites del `quick` actual
  sumaban aproximadamente 30 s y `test_kernel` 151 s de check-time.
- [Ticket 03: informe histórico](../research/test-cli-coverage-redundancy.md) y
  [matriz cruda](../prototypes/suite-cost-one-percent/coverage/report.json): hay **97 archivos
  por caso**, 85 con líneas visibles y 12 sin ellas; el archivo número 98 es `report.json`,
  no otro test. Los 97 payloads indican `ok: true`. El trace del padre no observa el producto
  ejecutado solo en subprocesos.
- La matriz contiene 6 subconjuntos estrictos, 3 pares idénticos (6 casos) y 73 casos restantes.
  **«Restantes» no significa «con líneas exclusivas».** El algoritmo compara cada conjunto
  con otro individual, no con la unión del resto. Queda corregida la afirmación previa de que
  el 86 % tenía cobertura exclusiva o que se había demostrado que no existían tests inútiles.
- El 10,6 % (`(6 + 3) / 85`) es una heurística de candidatos, no una tasa de redundancia de
  comportamiento demostrada. Los 280 s + 136 s = 416 s eran un ahorro hipotético usando
  duraciones históricas, condicionado a equivalencia que no se probó. El ahorro aprobado
  por borrados/fusiones es **cero**.

Estas correcciones prevalecen sobre las conclusiones más fuertes del informe histórico; no se
modifican sus datos crudos ni se presenta una nueva corrida de cobertura.

## Consecuencias y alternativas descartadas

- Se rechaza el gate exclusivamente en proceso: se conservan diez recorridos con Git real.
- Se rechazan el borrado mecánico y la migración masiva que proponía el antiguo ticket 06.
- Se mantiene el coste de `full`; este cambio reduce la selección cotidiana, no promete
  reducir el trabajo total de una corrida completa ni alcanzar un ahorro de 416 s.
- Se mantiene el ID, la ruta histórica y el Artifact ID del ticket 06, pero su padre pasa a
  ser este contrato y su alcance pasa a ser la selección y medición del gate.
- No se modifica la política de merge ni el estado canónico de los tickets. Los checkboxes y
  confirmaciones de documentos no son evidencia de integración del runner.

## Implementación y verificación

El único slice de implementación es el [06 reformulado](../tickets/suite-cost-one-percent/06-test-cli-consolidation.md):
selección exacta, pruebas del harness, documentación de uso y medición del gate. No requiere
cambiar código de producto, `test_cli`, `test_kernel`, fixtures ni la planificación existente.

Verificar inventario y selección antes de ejecutar; después probar el harness, medir el gate
con `--jobs 8` y ejecutar `full` por tratarse de un cambio al harness. Guardar reloj, check-time,
resultado, entorno y parámetros. Las corridas largas se lanzan desacopladas y se consultan;
no se solapan suites completas ni se delega a otros agentes sin petición explícita.

Preservar Windows/PowerShell, macOS y Unix/Linux, sin nuevas dependencias ni rutas absolutas
específicas de una máquina en la implementación. Medir Windows no verifica POSIX: ejecutar la
matriz disponible o declarar los entornos no ejecutados. No hay cambios de datos, acceso a
credenciales ni llamadas a proveedores reales en este slice.

Pendientes: reloj real del nuevo gate, resultados de `full`, evidencia multiplataforma y la
frontera canónica del runner. Ninguno se da por resuelto con la confirmación de esta decisión.
