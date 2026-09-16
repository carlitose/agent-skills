# Un caso de reconciliación autónoma falló una vez bajo la suite completa y no se reproduce aislado

## Artifact Graph
- Artifact ID: `artifact:autonomous-stack-reconcile-load-flake`
- Role: `spec`
- Standalone: true

## Type
Bug analysis

## Status
Abierto, sin causa identificada. Observado una vez el 16/09/2026; tres intentos de
reproducción posteriores pasaron.

## Observado

`test_cli.CliTests.test_autonomous_stack_reconciles_new_head_and_merges_child_without_revalidation`,
ejecutado dentro del escenario forward `autonomous-merge-grant` durante la verificación
completa con `--jobs 8`:

```
AssertionError: RuntimeError not raised
  test_cli.py:4804
Ran 1 test in 259.800s
```

El test inyecta un fallo en `AtomicLedger.save` que debe disparar `RuntimeError` en cuanto se
guarde un `pr-body` de schema 2 con `expected_head_sha` igual al nuevo head. Que no se dispare
significa que **ese guardado no llegó a producirse**: la reconciliación no alcanzó el rebind
del cuerpo.

## Evidencia de reproducción

| ejecución | carga | duración | resultado |
|---|---|---|---|
| suite completa, 8 shards | 8 shards con trabajo real de Git | 259,8 s | **fallo** |
| caso aislado | ninguna | 125,8 s | ok |
| escenario `autonomous-merge-grant` en solitario | ninguna | ~26 min | ok |
| caso con 7 procesos quemando CPU | 7 procesos CPU | 185,7 s | ok |

La duración se duplica en el caso que falla, así que la contención es real, pero no basta
para reproducirlo. **La variable no replicada es la naturaleza de la carga**: los shards de la
suite ejecutan trabajo intensivo en Git y disco, mientras la carga sintética solo consumía
CPU. La sospecha razonable es contención de sistema de ficheros, no de procesador.

## Hipótesis descartadas

- **Caducidad por lentitud**: no existe ningún TTL, expiración ni ventana temporal en el
  runner. `rg` sobre `finalizer.py`, `cli.py` y `kernel.py` no encuentra expiraciones, edades
  ni relojes en el camino de reconciliación. Una ejecución más lenta no invalida por sí misma
  un `render_request_hash` ni una aprobación de gate.
- **Regresión de los cambios de esta sesión**: el caso pasa con el mismo árbol de trabajo en
  tres configuraciones distintas, incluida una con carga. Si el rebind estuviese roto,
  fallaría también aislado.

## Diagnóstico pendiente

1. Reproducir con carga de **disco y Git**, no de CPU: varios shards ejecutando suites reales
   en paralelo mientras se repite solo este caso.
2. Con la reproducción, capturar el resultado devuelto por `resume_events_in_process` en la
   llamada que debía provocar el rebind. Un `gated` o un `deferred` ahí nombra la rama que se
   toma bajo contención; el arnés usado ya registra `result`, `reason` y `gate_id` por evento.
3. Solo entonces decidir si el defecto está en el runner (una condición de carrera que ante
   contención salta el rebind) o en el test (una precondición que asume una secuencia que la
   contención altera).

## Por qué no se cierra con un reintento

Marcar el caso como flaky o reintentarlo ocultaría precisamente lo que interesa: si bajo
contención la reconciliación puede **no** reenlazar el cuerpo del PR al nuevo head, eso sería
un defecto de producto, no del test. Un reintento verde no distingue esas dos posibilidades.

## No objetivos

- Reintentos automáticos, `skip` o tolerancia de fallos para este caso.
- Cambiar el test para que el aserto sea más laxo antes de conocer la causa.
- Atribuirlo al planificador de la suite: no hubo muerte por señal ni por timeout; el proceso
  terminó por su propio aserto.
