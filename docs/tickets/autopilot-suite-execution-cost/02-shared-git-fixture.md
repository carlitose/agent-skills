---
ticket_schema: 1
ticket_id: "02"
execution_mode: AFK
blocked_by: []
---

# Construir el repositorio de fixture una vez por clase y copiarlo por caso

## Artifact Graph
- Artifact ID: `artifact:suite-cost-shared-git-fixture`
- Role: `ticket`
- Parent: [autopilot-suite-execution-cost.md](../../specs/autopilot-suite-execution-cost.md)

## Parent Spec
[autopilot-suite-execution-cost.md](../../specs/autopilot-suite-execution-cost.md)

## What to Build
Un soporte de fixture en `git_test_support` que construya una plantilla de repositorio una sola
vez por clase y entregue a cada caso una copia de directorio, en lugar de repetir
`git init` + `git config` + `git add` + `git commit` por caso (260-330 ms por llamada medidos).

Cubre la sección «Slice 2» del spec.

## Acceptance Criteria
- [x] Un caso que hoy inicializa su repositorio obtiene una copia y no invoca `git init`.
      `CliTests.setUp` ahora copia una plantilla construida una vez por clase.
- [x] La copia es idéntica byte a byte a lo que producía la inicialización: contenido,
      finales de línea, e índice. Verificado comparando `HEAD`, `write-tree`,
      `status --porcelain` y los bytes de un fichero LF y uno CRLF.
- [x] Cada caso sigue recibiendo un repositorio propio: mutarlo no afecta a ningún otro caso,
      verificado por un test que muta y otro que observa.
- [x] El aislamiento de configuración de `isolated_git_environment` no cambia.
- [x] Una plantilla corrupta o una copia parcial falla de forma visible, no ejecuta contra un
      repositorio a medias.
- [x] Se reporta la duración antes/después de al menos una suite convertida. Medido en la
      misma máquina y bajo la misma carga: inicializar cuesta **1292 ms** por caso, copiar
      **271 ms**; 1021 ms menos por caso, ~103 s sobre los 101 casos de `CliTests`.

## Frontier
Done.

## Step-by-Step Implementation Plan
1. Añadir a `git_test_support` la construcción de plantilla por clase y la entrega de copias,
   sin convertir todavía ninguna suite. Checkpoint: el soporte tiene su propio test y
   `test_git_test_support` sigue verde.
2. Verificar equivalencia byte a byte entre repositorio inicializado y copiado, incluido el
   índice, con un test que compare ambos. Checkpoint: ese test pasa antes de convertir nada.
3. Convertir una suite representativa que hoy pague inicialización por caso. Checkpoint: la
   suite pasa y su duración baja de forma medible.
4. Convertir el resto de suites que compartan ese patrón, una a una. Checkpoint tras cada una.

## Testing Plan
- Automático: `test_git_test_support` ampliado; equivalencia byte a byte; aislamiento entre
  casos; las suites convertidas.
- Automático: las suites de fidelidad de texto en Windows, que son las que detectarían una
  copia que altere finales de línea.
- Manual: ninguno.

## Out of Scope
- Compartir un repositorio **mutable** entre casos.
- Cambiar el aislamiento de configuración de Git.
- Convertir suites cuyo objeto de prueba sea la propia inicialización del repositorio.
