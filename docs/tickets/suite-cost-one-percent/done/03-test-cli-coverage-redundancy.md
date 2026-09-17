---
ticket_schema: 1
ticket_id: "03"
execution_mode: AFK
blocked_by: []
---

# Matriz de cobertura por caso de `test_cli`: qué casos no cubren nada que otro no cubra

## Artifact Graph
- Artifact ID: `artifact:suite-one-percent-test-cli-coverage-redundancy`
- Role: `ticket`
- Parent: [suite-cost-one-percent-wayfinder.md](../../specs/suite-cost-one-percent-wayfinder.md)
- Produces: `docs/research/test-cli-coverage-redundancy.md`

## Parent Spec
[suite-cost-one-percent-wayfinder.md](../../specs/suite-cost-one-percent-wayfinder.md)

## What to Build
Investigación. Convierte «quitar tests inútiles» en una lista con pruebas. Para cada uno de
los 101 casos de `test_cli` se obtiene el conjunto de líneas de `ticket-autopilot/scripts/`
que ejecuta. Con esa matriz:

- un caso cuyo conjunto es **subconjunto estricto** del de otro caso es candidato objetivo a
  borrar: no ejecuta ninguna línea que el otro no ejecute;
- dos casos con conjunto **idéntico** y aserciones distintas son candidatos a fusionar en uno;
- el resto son casos con cobertura propia, y se listan como tales.

Sin `coverage.py` instalado: se usa `trace` de la biblioteca estándar, que no requiere
instalar nada y es suficiente para líneas ejecutadas. Cubre la arista 3 del mapa.

## Acceptance Criteria
- [x] Un arnés reproducible ejecuta cada caso de `test_cli` por separado bajo `trace` y
      guarda su conjunto de líneas de `scripts/autopilot/*.py`, excluyendo los tests.
- [x] Se publica la matriz resumida: por caso, tamaño del conjunto, casos de los que es
      subconjunto, casos con conjunto idéntico, y su duración según el histórico.
- [x] Se publican tres listas separadas: **subconjunto estricto**, **idénticos**, **con
      cobertura propia**, cada una con el ahorro en segundos si se actuara sobre ella.
- [x] El documento advierte explícitamente que cobertura de líneas no es cobertura de
      comportamiento: un caso subconjunto puede afirmar algo que el superconjunto no afirma. Por
      eso las listas son **candidatos**, y la decisión es humana (ticket 04).
- [x] Nada de `test_cli` cambia en este ticket.

## Frontier
Done.

## Resultado medido

Informe: [test-cli-coverage-redundancy.md](../../research/test-cli-coverage-redundancy.md).
Arnés: `docs/prototypes/suite-cost-one-percent/coverage_matrix.py`. 98 casos medidos.

| grupo | casos | ahorro |
|---|---|---|
| subconjunto estricto | 6 (7,1 %) | 280 s |
| fusionables (3 grupos de 2) | 3 (3,5 %) | 136 s |
| **cobertura propia** | **73 (85,9 %)** | — |
| sin líneas visibles (límite del método) | 12 | — |

**La hipótesis de partida era falsa.** `test_cli` no es caro por tener tests inútiles: el
86 % de sus casos ejecuta líneas de producto que ningún otro ejecuta. El ahorro máximo por
borrar y fusionar es 416 s de 6 062 s, un **6,9 %**. Es caro porque cada caso arranca un ciclo
de vida completo contra Git real.

**Efecto sobre el ticket 06**: se dispara la condición de revisión que el mapa escribió por
adelantado («si menos del 20 % son subconjunto, es reescritura, no borrado»). El dato es
10,6 %. El 06 deja de ser ejecutable como borrado mecánico y depende de la decisión humana
del 04, ahora con cifras.

**Límite del método, declarado**: 12 casos ejecutan la CLI solo como subproceso y `trace` en
el proceso padre no ve el hijo. Quedan fuera del recuento en vez de contarse como «sin
cobertura».

## Step-by-Step Implementation Plan
1. Arnés que lanza `python -m trace --count --coverdir` por caso, o `trace.Trace(count=1)`
   en proceso, filtrando a `scripts/autopilot/`. Checkpoint: un caso produce un conjunto no
   vacío y estable entre dos ejecuciones.
2. Ejecución completa, en solitario. Coste estimado: los 101 casos × ~29 s ≈ 50 min más la
   sobrecarga de `trace`; se lanza en segundo plano.
3. Cálculo de subconjuntos e idénticos; cruce con `agent-skills-test-durations.json` para
   el ahorro. Checkpoint: la suma de duraciones de la lista «subconjunto» está calculada.

## Testing Plan
- Automático: ninguno nuevo en el repo.
- Manual: muestreo de tres pares subconjunto/superconjunto leyendo ambos tests para
  confirmar que la relación de cobertura es real.

## Out of Scope
- Borrar o fusionar casos: ticket 06, tras la decisión de 04.
- Extender la matriz a otras suites; `test_cli` es el 42 % y va primero.
