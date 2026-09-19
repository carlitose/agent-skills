---
type: source
title: "Ningún trabajo colgado al cerrar una fase"
identity_key: spec:no-dangling-work
identity_strength: stable
source_path: docs/specs/no-dangling-work.md
source_digest: sha256:75a7febe1eae708bfd6d09fdce3f83a794d325c6edbd6c5b71c1ae3da23e8368
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-09-19
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Ningún trabajo colgado al cerrar una fase

Compiled from `docs/specs/no-dangling-work.md`. Identity is `spec:no-dangling-work`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-19** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"decisions":{"headings":[],"status":"not-identified"},"exclusions":{"headings":[],"status":"not-identified"},"goals":{"headings":[],"status":"not-identified"},"invariants":{"headings":[],"status":"not-identified"},"verification":{"headings":[],"status":"not-identified"}},"parts":[{"index":0,"path":"wiki/sources/spec-no-dangling-work.md","payload_bytes":7608,"payload_sha256":"75a7febe1eae708bfd6d09fdce3f83a794d325c6edbd6c5b71c1ae3da23e8368"}],"payload_bytes":7608,"payload_sha256":"75a7febe1eae708bfd6d09fdce3f83a794d325c6edbd6c5b71c1ae3da23e8368","schema":1,"source_digest":"sha256:75a7febe1eae708bfd6d09fdce3f83a794d325c6edbd6c5b71c1ae3da23e8368","source_identity":"spec:no-dangling-work","source_kind":"spec"} -->

| Topic | Source sections |
|---|---|
| goals | no matching section identified in the source; complete source retained |
| exclusions | no matching section identified in the source; complete source retained |
| decisions | no matching section identified in the source; complete source retained |
| invariants | no matching section identified in the source; complete source retained |
| verification | no matching section identified in the source; complete source retained |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":7608,"payload_sha256":"75a7febe1eae708bfd6d09fdce3f83a794d325c6edbd6c5b71c1ae3da23e8368","schema":1,"source_digest":"sha256:75a7febe1eae708bfd6d09fdce3f83a794d325c6edbd6c5b71c1ae3da23e8368","source_identity":"spec:no-dangling-work"} -->
```markdown
# Ningún trabajo colgado al cerrar una fase

## Artifact Graph
- Artifact ID: `spec:no-dangling-work`
- Role: `spec`
- Standalone: true

## Type
Bug analysis con decisión de disciplina.

## Síntoma
Al terminar de trabajar en un repositorio quedan «archivos sin guardar»: cambios sin commitear,
ficheros sin seguimiento y worktrees que nadie recuerda. El 19/09 un inventario de los 27
checkouts de `agent-skills` en esta máquina encontró estado colgado en 9 de ellos. No es un caso:
es un patrón, y el trabajo colgado es exactamente el que se pierde.

## Diagnóstico: cuatro clases, cuatro causas
El inventario (`dirty-state-inventory-v1.json`) separa el síntoma en clases con mecanismo propio.

**A. Proyecciones de completion staged y nunca commiteadas** (5 worktrees, 6–47 rutas cada uno:
`foundation-delivery`, `foundation-delivery-v2`, `suite-cost-deps-04-05-final-v4`,
`linux-fixtures-prerequisite`, `suite-cost-one-percent-final`, `suite-cost-ticket06-execution`).
El runner aplica la proyección final —mover el ticket a `done/`, escribir el recibo, repuntar
enlaces— en el índice del worktree, y solo la commitea al entregar. Cuando el candidato se
invalida, la run se supera por otra o la sesión se abandona, el índice se queda a medias y el
worktree conserva para siempre un estado que ya no representa a nadie. `worktree-gc-plan` lo ve
(`worktree-dirty`, `run-not-completed`) y lo protege, correctamente; pero nadie vuelve a leer ese
plan.

**B. Temporales de wiki-sync huérfanos** (`Temp/ticket-wiki-delivery-*`, 1 408 rutas sucias, y dos
`ticket-wiki-source-*`, todos registrados como worktrees de Git). `wiki_sync.py` los crea con
`mkdtemp` y los retira en un `finally`. El `finally` es correcto y no se ejecutó: el proceso fue
terminado desde fuera —el `timeout` de un cliente que lo envolvía— antes de llegar. En Windows la
terminación no da opción al `finally`. Y no hay barrido posterior: el runner nunca vuelve a mirar
un temporal que él mismo creó.

**C. Salidas de herramientas sin política de seguimiento** (120 JSON en
`docs/prototypes/suite-cost-one-percent/coverage/` del checkout principal). El prototipo escribe
un fichero por test además del `report.json` que sí se commiteó. Ni `.gitignore` ni el prototipo
dicen qué hacer con ellos, así que quedan como `??` indefinidamente.

**D. Specs que el agente escribe en el checkout de origen y luego copia al worktree**
(`C:/s06src`, 3 ficheros `??`). Es un hábito de esta sesión: redactar el spec en `s06src` para
tener el path canónico, copiarlo al worktree del run, y no volver a borrarlo del origen. El
worktree entrega la copia; el original queda colgado.

Las cuatro comparten una sola raíz: **el fin de una fase no tiene un paso que mire el estado del
árbol y decida qué hacer con cada ruta**. Cada mecanismo deja algo a medias por una razón
razonable, y nada lo recoge.

## Decisión 1: el cierre de fase incluye un inventario de estado y una disposición por ruta
Al terminar una fase —ticket integrado, run terminal, sesión que se entrega— se inventaría el
estado de **todos** los checkouts del repositorio (`git worktree list` más `worktree-gc-plan`), y
cada ruta no limpia recibe exactamente una disposición: `commit` (con su ticket), `discard` (con
la razón), o `handoff` (a quién y con qué patch guardado). «Lo miro luego» no es una disposición.
Este paso se integra en el checkpoint de revisión del plan ya existente, como su sexta
comprobación: estado del árbol.

## Decisión 2: el runner barre lo que él mismo crea
`ticket-autopilot` gana una operación explícita de barrido de temporales propios: worktrees
registrados bajo el directorio temporal del sistema con prefijo `ticket-wiki-*`, y worktrees de
runs cuyo estado terminal ya está probado. El barrido usa `worktree-gc-plan` como única fuente de
elegibilidad, exige `--apply` para borrar y deja recibo. Un temporal cuya run sigue viva no se toca.
Es la corrección de B: el `finally` sigue siendo la primera línea; el barrido es la segunda, para
cuando la primera no llega a ejecutarse.

## Decisión 3: los worktrees protegidos por proyección a medias se declaran, no se heredan
Para A no hay borrado automático: esas rutas contienen la única copia de una proyección que el
runner aplicó con autoridad. La disposición correcta es la de la Decisión 1 aplicada una vez:
cada uno se resuelve como `discard` si su ticket ya integró por otra vía —comprobable con
`merge-base --is-ancestor` y comparando blobs, como se hizo con LW-07— o como `handoff` con patch
si no. Después, la Decisión 1 impide que vuelvan a acumularse.

## Decisión 4: las salidas de herramientas declaran su seguimiento
Todo script bajo `docs/prototypes/` o `scripts/` que escriba ficheros dentro del repositorio dice
en su docstring cuál de dos cosas pasa con ellos: se commitean como evidencia, o se ignoran por
`.gitignore`. Para C se decide **ignorar** los JSON por test: el `report.json` agregado ya está
versionado y es la evidencia; los 120 ficheros son su materia prima regenerable.

## Decisión 5: el spec se escribe donde se entrega
Corrección de D, sin herramienta: el spec se redacta directamente en el worktree del run, o se
escribe en el origen y se **mueve**, no se copia. El checkpoint de la Decisión 1 detecta el fallo si
ocurre igualmente.

## Invariantes semánticas
1. Al cerrar una fase, ninguna ruta de ningún checkout del repositorio queda sin disposición
   registrada.
2. El runner borra únicamente lo que `worktree-gc-plan` declara elegible, y solo con `--apply`
   explícito y recibo.
3. Un worktree con proyección aplicada y ticket no integrado nunca se borra sin patch guardado.
4. El `finally` de wiki-sync no se debilita: el barrido lo complementa.
5. Toda salida de herramienta dentro del repositorio está o versionada o ignorada, nunca en
   tierra de nadie.

## Slices de implementación
1. **Checkpoint**: añadir «estado del árbol» como sexta comprobación del checkpoint de revisión
   del plan, con la regla de disposición por ruta. Documentación y prueba estructural.
2. **Barrido**: operación `worktree-sweep` en el runner (plan/apply, recibo, solo elegibles por
   `gc-plan`, temporales `ticket-wiki-*` incluidos), con pruebas de que no toca runs vivas.
3. **Cobertura**: `.gitignore` para los JSON por test del prototipo de cobertura y docstring que
   lo declare.
4. **Resolución de A**: aplicar la Decisión 3 a los 6 worktrees actuales, con patches guardados y
   recibo; es operación, no código, y requiere autorización explícita para cada `discard`.

## Estrategia de verificación
Para 1, prueba estructural como la del checkpoint. Para 2, pruebas del runner con temporales
sintéticos registrados como worktrees: uno huérfano y elegible se retira con recibo; uno cuya run
está viva se conserva; sin `--apply` nada cambia. Para 3, `git status` limpio tras regenerar la
cobertura. Para 4, inventario antes y después con los patches verificables por hash.

Límites: esto elimina el trabajo colgado del proceso, no el de un proceso matado a mitad —para
ese existe el barrido, que corre en la siguiente fase, no en el instante.

## Alternativas y exclusiones
Se descarta borrar automáticamente cualquier worktree sucio: la Clase A demuestra que un árbol
sucio puede ser la única copia de trabajo con autoridad. Se descarta un hook de Git que impida
salir con cambios: el problema son los árboles que nadie vuelve a abrir, y un hook no se ejecuta
en ellos. Quedan fuera los checkouts de otros repositorios y el estado del wiki generado.

```
