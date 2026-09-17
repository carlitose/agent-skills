---
type: source
title: "Histograma de comandos git por operación del runner"
identity_key: ticket:suite-cost-one-percent/02
identity_strength: stable
source_path: docs/tickets/suite-cost-one-percent/done/02-runner-git-command-histogram.md
source_digest: sha256:01e2a8e1535383ac1f99efd59db0e01bf383ddcfc31bfd2bd3c203a936a29d67
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-17
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
run_id: suite-cost-one-percent-final
---

# Histograma de comandos git por operación del runner

Compiled from `docs/tickets/suite-cost-one-percent/done/02-runner-git-command-histogram.md`. Identity is `ticket:suite-cost-one-percent/02`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-17** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-suite-cost-one-percent-wayfinder]]

## Run

Completed under autopilot run `suite-cost-one-percent-final`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[9],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[8],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-suite-cost-one-percent-02.md","payload_bytes":5169,"payload_sha256":"01e2a8e1535383ac1f99efd59db0e01bf383ddcfc31bfd2bd3c203a936a29d67"}],"payload_bytes":5169,"payload_sha256":"01e2a8e1535383ac1f99efd59db0e01bf383ddcfc31bfd2bd3c203a936a29d67","schema":1,"source_digest":"sha256:01e2a8e1535383ac1f99efd59db0e01bf383ddcfc31bfd2bd3c203a936a29d67","source_identity":"ticket:suite-cost-one-percent/02","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 8: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 9: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":5169,"payload_sha256":"01e2a8e1535383ac1f99efd59db0e01bf383ddcfc31bfd2bd3c203a936a29d67","schema":1,"source_digest":"sha256:01e2a8e1535383ac1f99efd59db0e01bf383ddcfc31bfd2bd3c203a936a29d67","source_identity":"ticket:suite-cost-one-percent/02"} -->
```markdown
---
ticket_schema: 1
ticket_id: "02"
execution_mode: AFK
blocked_by: []
---

# Histograma de comandos git por operación del runner

## Artifact Graph
- Artifact ID: `artifact:suite-one-percent-runner-git-command-histogram`
- Role: `ticket`
- Parent: [suite-cost-one-percent-wayfinder.md](../../specs/suite-cost-one-percent-wayfinder.md)
- Produces: `docs/research/runner-git-command-histogram.md`

## Parent Spec
[suite-cost-one-percent-wayfinder.md](../../specs/suite-cost-one-percent-wayfinder.md)

## What to Build
Investigación. Pregunta: de los ~200 comandos `git` que el runner emite en un ciclo de vida
completo, ¿cuántos son repeticiones del mismo argv sobre el mismo estado, y cuánto cuesta cada
familia? Sin esta tabla no se sabe si quitar redundancia vale un 10 % o un 50 % del coste del
runner, que es donde vive el 90 % de los 28,9 s medidos por caso.

Evidencia previa: los `git.exe` que quedaron suspendidos eran `rev-parse --show-toplevel` y
`diff --name-only`, dos comandos que sugieren repetición por operación. Cubre la arista 2 del
mapa y la incógnita «cuántos comandos git por operación son redundantes».

## Acceptance Criteria
- [x] Un arnés reproducible envuelve `capture_command` y registra, por comando: argv
      normalizado (sin OIDs ni rutas temporales), `cwd` relativo, duración, y la operación del
      runner en curso (`run`, `activate`, `stage`, `delivery`, `reconcile`).
- [x] Se ejecuta sobre al menos tres casos de `test_cli` de coste distinto (uno de la
      mediana, ~67 s; uno del p90, ~100 s; uno pequeño) y se publica la tabla argv × frecuencia
      × coste total × operación.
- [x] La tabla distingue repeticiones **idénticas dentro de la misma operación** (candidatas
      a cachear) de repeticiones entre operaciones (que pueden ser legítimas por cambio de
      estado).
- [x] Se reporta el coste de captura por comando: duración con `capture_command` frente al
      mismo `git` directo, sobre la muestra real, no sobre `git --version`.
- [x] El documento cierra con una estimación del ahorro máximo si se eliminaran solo las
      repeticiones idénticas dentro de operación, en segundos y en porcentaje del caso.
- [x] Nada del runner cambia en este ticket.

## Frontier
Done.

## Resultado medido

Informe: [runner-git-command-histogram.md](../../research/runner-git-command-histogram.md).
Arneses: `docs/prototypes/suite-cost-one-percent/{sitecustomize,measure_commands,measure_capture_overhead}.py`.

- El caso mediano emite **395 comandos** en 39,0 s, de los cuales **271 son repeticiones
  idénticas dentro de una misma invocación** (76 %).
- La familia más cara es `git rev-parse --show-toplevel`: **116 llamadas, 8,5 s**, de las que
  110 son repeticiones. Le sigue `rev-parse --git-common-dir`, 52 llamadas con 46 repeticiones;
  `common_git_dir` llama a `repository_root`, que no guarda nada.
- El sobrecoste mediano de la contención es **+54,7 ms por comando** (×2,0–×2,5 sobre `git`
  directo), medido sobre las formas reales. No se toca: cada repetición evitada ahorra el
  comando y su contención juntos, ~95 ms.
- **Ahorro realmente alcanzable, tras separar lo reutilizable de lo que no lo es: −17 % a
  −27 % por caso** (medido ya con el ticket 05 implementado). La primera estimación de
  «50–64 %» asumía que toda repetición era reutilizable y era falsa; queda escrita y corregida
  en el informe, no sustituida en silencio.

Desviación del plan, declarada: los arneses viven en `docs/prototypes/` (área desechable
declarada y excluida del descubrimiento de tests), no en `docs/research/`, que contiene
informes. El informe sí está en `docs/research/`.

Dos correcciones aplicadas a la propia medición, ambas antes de dar cifras por buenas:

1. La primera pasada contó 313 repeticiones donde había 271, porque fusionaba invocaciones
   distintas con el mismo nombre de operación. Se corrigió identificando la invocación por
   identidad del objeto frame.
2. La segunda agrupaba por argv **ignorando el directorio**, contando como repetición dos
   preguntas iguales a repositorios distintos. Con la clave corregida (argv + directorio +
   invocación) el caso mediano tiene 265 repeticiones, no 271.

## Step-by-Step Implementation Plan
1. Arnés en `docs/research/` que parchea `autopilot.command_capture.capture_command` y
   `autopilot.git_ops.run_git` para registrar sin alterar resultados. Checkpoint: un caso
   pequeño produce un CSV coherente con su duración total.
2. Ejecutar los tres casos, solos, sin otros shards. Checkpoint: los totales del arnés
   cuadran con la duración del caso ±5 %.
3. Agrupar y redactar. Checkpoint: cada fila de la tabla nombra la operación y el motivo
   probable de repetición, o dice que no se conoce.

## Testing Plan
- Automático: ninguno nuevo en el repo; el arnés es de investigación.
- Manual: revisión de la tabla contra el código que emite cada comando.
- No disponible aquí: la cifra de captura en POSIX. Se declara.

## Out of Scope
- Implementar cachés o quitar comandos: ticket 05.
- Medir bajo contención; la medida es en solitario, porque la contención se mide aparte.

```
