# ¿Cuántos casos de `test_cli` no cubren nada que otro caso no cubra?

## Artifact Graph
- Artifact ID: `artifact:test-cli-coverage-redundancy`
- Role: `research`
- Parent: [suite-cost-one-percent-wayfinder.md](../specs/suite-cost-one-percent-wayfinder.md)

## Pregunta
«Quitar tests inútiles» era una intuición. Esta medición la convierte en una lista con
pruebas, o la desmiente.

## Método

`docs/prototypes/suite-cost-one-percent/coverage_matrix.py` ejecuta cada caso en su propio
intérprete bajo `trace` de la biblioteca estándar —nada que instalar— y guarda el conjunto de
líneas de `ticket-autopilot/scripts/autopilot/*.py` que ejecuta. Después compara conjuntos:

- **subconjunto estricto**: el caso no ejecuta ninguna línea de producto que otro no ejecute;
- **idénticos**: dos o más casos ejecutan exactamente las mismas líneas;
- **cobertura propia**: el resto.

98 casos medidos el 16/09/2026, en 3 procesos paralelos, sobre el árbol que ya incluye los
tickets 01 y 05.

## Resultado

| grupo | casos | % | ahorro si se actuara |
|---|---|---|---|
| subconjunto estricto | **6** | 7,1 % | 280 s |
| fusionables (3 grupos de 2) | **3** | 3,5 % | 136 s |
| **cobertura propia** | **73** | **85,9 %** | — |
| sin líneas de producto visibles (límite del método) | 12 | — | — |

**Redundancia total: 9 de 85 casos medidos, un 10,6 %.** El ahorro máximo combinado son 416 s
sobre los 6 062 s que costaba la suite: **un 6,9 %**.

### Los seis subconjuntos estrictos

| coste | caso | cubierto por |
|---|---|---|
| 65,3 s | `test_off_mode_uses_the_complete_delivery_lifecycle_without...` | `test_delivery_is_crash_resumable_idempotent...` |
| 61,9 s | `test_existing_manual_run_grant_continues_an_open_pr_through...` | `test_existing_run_grant_persists_before...` |
| 53,4 s | `test_stage_gate_reason_is_validated_before_drift_and_visib...` | `test_delivery_is_crash_resumable_idempotent...` |
| 38,0 s | `test_ignored_candidate_promotion_gates_before_commit_or_pr...` | `test_granted_completion_projection_deliv...` |
| 37,0 s | `test_resume_drives_stages_and_invalidates_stale_downstream...` | `test_candidate_invalidation_resets_stale...` |
| 24,0 s | `test_pre_feature_schema_three_ledger_remains_manual_on_sta...` | `test_candidate_invalidation_resets_stale...` |

### Los tres grupos idénticos

- `test_autonomous_grant_merges_an_eligible_exact_head_without_a_prompt` +
  `test_autonomous_merge_accepts_github_has_hooks_success_state` (59,8 s)
- `test_delivery_replays_after_crash_immediately_after_branch_creation` +
  `test_delivery_replays_after_crash_immediately_after_commit` (54,3 s)
- `test_hold_repoints_the_linking_map_and_reopen_repoints_it_back` +
  `test_resume_accepts_unchanged_crlf_ticket_sources` (22,3 s)

Los nombres del segundo y tercer grupo ya avisan de que las aserciones **no** son iguales
aunque las líneas sí lo sean: «después de crear la rama» y «después del commit» son dos
momentos distintos de caída; CRLF y repuntado del mapa son dos cosas sin relación. Son
candidatos a fusión, no a borrado.

## Conclusión: la hipótesis era falsa

`test_cli` no es caro por tener tests inútiles. El **86 %** de sus casos ejecuta líneas de
producto que ningún otro caso ejecuta. Es caro porque **cada caso arranca un ciclo de vida
completo contra Git real**, y eso cuesta lo que cuesta.

Consecuencia directa para el mapa: el ticket 06 no puede ser un borrado mecánico. Su propia
condición de revisión decía que por debajo del 20 % de subconjuntos habría que replantearlo, y
el dato real es 10,6 %. Bajar el coste de `test_cli` exige **reescribir** casos a la forma en
proceso de `test_kernel` (1,5 s frente a 60 s por caso), lo que cambia qué se cubre y con qué
fidelidad. Eso es exactamente la decisión humana del ticket 04, y ahora hay cifras para
tomarla.

## Límites declarados

- **Cobertura de líneas no es cobertura de comportamiento.** Un caso subconjunto puede
  afirmar algo que su superconjunto no afirma. Ninguna entrada de este documento es un
  veredicto de borrado; son candidatos para revisión humana.
- **12 casos no muestran líneas de producto.** Ejecutan la CLI solo como subproceso, y `trace`
  en el proceso padre no ve lo que ocurre en el hijo. No se puede afirmar nada sobre su
  redundancia con este método; quedan fuera del recuento en vez de contarse como «sin
  cobertura».
- Medido solo en Windows 11, sobre el árbol con los tickets 01 y 05 aplicados.
