---
type: source
title: "Bajar el coste cotidiano de verificación sin perder la cobertura completa"
identity_key: artifact:suite-cost-one-percent-wayfinder
identity_strength: stable
source_path: docs/specs/suite-cost-one-percent-wayfinder.md
source_digest: sha256:6cd8d2a720c80d377e0293a39b5a49440f2e50bef2706532bf6620080f45d73c
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-09-17
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Bajar el coste cotidiano de verificación sin perder la cobertura completa

Compiled from `docs/specs/suite-cost-one-percent-wayfinder.md`. Identity is `artifact:suite-cost-one-percent-wayfinder`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-17** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Child source: [[sources/ticket-suite-cost-one-percent-01]]
- Child source: [[sources/ticket-suite-cost-one-percent-02]]
- Child source: [[sources/ticket-suite-cost-one-percent-03]]
- Child source: [[sources/ticket-suite-cost-one-percent-04]]
- Child source: [[sources/ticket-suite-cost-one-percent-05]]
- Child source: [[sources/artifact-runner-git-command-histogram]]
- Child source: [[sources/artifact-test-cli-coverage-redundancy]]
- Child source: [[sources/artifact-local-verification-profile-contract]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"decisions":{"headings":[6],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"goals":{"headings":[5],"status":"present"},"invariants":{"headings":[],"status":"not-identified"},"verification":{"headings":[],"status":"not-identified"}},"parts":[{"index":0,"path":"wiki/sources/artifact-suite-cost-one-percent-wayfinder.md","payload_bytes":9314,"payload_sha256":"6cd8d2a720c80d377e0293a39b5a49440f2e50bef2706532bf6620080f45d73c"}],"payload_bytes":9314,"payload_sha256":"6cd8d2a720c80d377e0293a39b5a49440f2e50bef2706532bf6620080f45d73c","schema":1,"source_digest":"sha256:6cd8d2a720c80d377e0293a39b5a49440f2e50bef2706532bf6620080f45d73c","source_identity":"artifact:suite-cost-one-percent-wayfinder","source_kind":"spec"} -->

| Topic | Source sections |
|---|---|
| goals | 5: Destination |
| exclusions | 8: Out of Scope |
| decisions | 6: Decisions So Far |
| invariants | no matching section identified in the source; complete source retained |
| verification | no matching section identified in the source; complete source retained |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":9314,"payload_sha256":"6cd8d2a720c80d377e0293a39b5a49440f2e50bef2706532bf6620080f45d73c","schema":1,"source_digest":"sha256:6cd8d2a720c80d377e0293a39b5a49440f2e50bef2706532bf6620080f45d73c","source_identity":"artifact:suite-cost-one-percent-wayfinder"} -->
```markdown
# Bajar el coste cotidiano de verificación sin perder la cobertura completa

## Artifact Graph
- Artifact ID: `artifact:suite-cost-one-percent-wayfinder`
- Role: `wayfinder`
- Standalone: true

### Children
- [01 Sacar la forward matrix del perfil `full`](../tickets/suite-cost-one-percent/done/01-forward-matrix-out-of-full.md)
- [02 Histograma de comandos git por operación del runner](../tickets/suite-cost-one-percent/done/02-runner-git-command-histogram.md)
- [03 Matriz de cobertura por caso de `test_cli`](../tickets/suite-cost-one-percent/done/03-test-cli-coverage-redundancy.md)
- [04 Decidir el contrato de perfiles y la cobertura e2e irrenunciable](../tickets/suite-cost-one-percent/done/04-profile-contract-decision.md)
- [05 Quitar comandos git redundantes del runner](../tickets/suite-cost-one-percent/done/05-runner-git-dedup.md)
- [Histograma de comandos Git](../research/runner-git-command-histogram.md)
- [Matriz de líneas por caso](../research/test-cli-coverage-redundancy.md)
- [Contrato vigente de perfiles](local-verification-profile-contract.md)

## Type
Wayfinding spec

## Status

Activo. Abierto el 16/09/2026 tras
[autopilot-suite-execution-cost.md](autopilot-suite-execution-cost.md). La decisión humana del
04 está confirmada y registrada en
[local-verification-profile-contract.md](local-verification-profile-contract.md). El 06 deja
de ser una consolidación de tests: implementará ese contrato.

Las evidencias y checkboxes históricos de 01, 02, 03 y 05 describen trabajo local, no
integración canónica. La consulta `ticket-list` del 16/09/2026 devuelve los seis con
`disposition: open`, `lifecycle: unknown`; 01–03 están `ready`, 04 y 05 están bloqueados por
sus dependencias y 06 por 03 y 04. No se modifican esos estados mediante este documento.

## Destination

El gate cotidiano por defecto debe costar **≤150 s de reloj con `--jobs 8`**, no 150 s de
check-time. Será el `quick` actual ampliado con todo `test_kernel` y los diez e2e con Git real
nombrados en el contrato. `full` conserva todos los tests; es obligatorio antes de PRs que
toquen runner/harness y antes de release. Los PRs exclusivamente de documentación usan el
gate rápido. La forward matrix sigue siendo un comando explícito de release.

El nombre histórico «one-percent» no es una afirmación aritmética del nuevo objetivo de reloj.
Los 95–120 s sugeridos durante la entrevista eran estimaciones, no medidas. El reloj real del
nuevo gate sigue pendiente. Se mantiene la referencia de ≤20 min para `full`, observado en
18 min tras 05, sin prometer un ahorro adicional de `full` por separar perfiles.

## Decisions So Far

**No repetir la forward matrix en `full`.** El ticket 01 quitó una segunda ejecución de 85
casos ya descubiertos: 3 857 s de check-time de la referencia y una cola larga de release.
La cobertura de esos casos permanece en `full`; cambia dónde se produce la evidencia de
release, no sus aserciones.

**Deduplicar hechos de estructura, no estado.** El
[histograma del 02](../research/runner-git-command-histogram.md) midió un sobrecoste mediano de
captura de 54,7 ms por comando. El 05 añadió un ámbito por invocación de CLI para
`repository_root()` y `common_git_dir()`, invalidado por cambios estructurales. No cachea
fallos, instantáneas semánticas ni las revalidaciones de identidad de `status_barrier`.

**La matriz de líneas no autoriza a borrar tests.** El
[informe del 03](../research/test-cli-coverage-redundancy.md) identificó 6 subconjuntos estrictos
y 3 pares idénticos entre 85 casos con líneas observables. El 10,6 % (`9/85`) es una heurística
de candidatos, no equivalencia de comportamiento. Sus 73 casos restantes no se compararon
contra la unión del resto: la antigua afirmación «86 % con cobertura exclusiva» no está
probada. Hay 97 archivos por caso, 12 sin líneas de producto visibles al trace del padre;
el archivo adicional es el resumen. Los 416 s de ahorro propuestos eran hipotéticos.

**Decisión confirmada del 04.** El usuario eligió conservar Git real en una selección de diez
casos, mantener todos los tests en `full` y aceptar que las variantes restantes puedan detectar
regresiones solo en `full`. No se borra, fusiona ni migra masivamente ningún caso en el 06.
El contrato registra los identificadores, las correcciones de evidencia y la confirmación
final «Si conferma» del 16/09/2026.

**No confundir check-time con reloj.** El antiguo cálculo de 101 casos × 100 comandos ×
47 ms = 475 s describe trabajo acumulado aproximado, no un límite inferior del reloj con ocho
workers. Tampoco dividir sumas entre ocho demuestra un tiempo alcanzable. El 06 debe medir,
sin convertir esa aritmética ni la selección aprobada en una garantía de ≤150 s.

## Not Yet Specified

- Reloj real del nuevo gate y margen frente a 150 s con `--jobs 8`. Si no cumple, registrar
  la medida y volver a decidir; no reducir la selección ni relajar pruebas por inferencia.
- Coste de captura por comando y ahorro del dedup en macOS/POSIX. Solo hay medidas Windows.
- Si existe una reducción segura de las 40 instantáneas semánticas observadas en un caso.
  Requeriría demostrar ausencia de escrituras entre llamadas; no es parte del 06.

Resueltas: composición del gate, obligatoriedad de `full`, riesgo aceptado y conservación de
los candidatos de la matriz. La entrevista 04 ya no es una incógnita de producto; su cierre
canónico sigue siendo responsabilidad del runner.

## Out of Scope

- Más planificación, timeouts adaptativos, shards o paralelismo en el harness.
- Borrar/fusionar tests o sustituir Git real por un fake o una migración masiva al kernel.
- Relajar aserciones, saltarse flakes, ocultar fallos con reintentos o cambiar contención.
- Cachear `semantic_candidate_ref` o `status_barrier._lexical_root`.
- CI hospedado y verificación con proveedor en vivo como evidencia de este cambio local.

## Frontier / Blocking Edges

1. Hay evidencia local de 01 (forward matrix), 02 (histograma), 03 (matriz) y 05 (dedup).
2. La entrevista del 04 está confirmada y su spec enlazado. Ningún test cambia en ese slice.
3. [06 Implementar el gate rápido sin recortar `full`](../tickets/suite-cost-one-percent/done/06-test-cli-consolidation.md)
   pasa a ser hijo del contrato. Conserva ID, Artifact ID, ruta y dependencias 03 y 04.
4. El usuario ha pedido ejecutar el 06 hasta `done`. Antes de mutar su candidato, el runner
   debe resolver su frontera real: los documentos no sustituyen integración ni autorizaciones.
   Una consulta de disponibilidad tampoco concede merge ni permite saltar gates.

## Ticket Plan

| ID | tipo | modo | bloqueado por | alcance vigente | evidencia / siguiente paso |
|---|---|---|---|---|---|
| 01 | task | AFK | — | Sacar la forward matrix de `full` | Medida local disponible |
| 02 | research | AFK | — | Histograma de Git por operación | Informe disponible |
| 03 | research | AFK | — | Matriz de líneas por caso | Informe disponible; no demuestra equivalencia |
| 04 | grilling | HITL | 02, 03 | Contrato de perfiles | Decisión confirmada y spec registrado |
| 05 | task | AFK | 02 | Dedup de hechos de estructura | Código y medida local disponibles |
| 06 | task | AFK | 03, 04 | Gate rápido con `quick` + kernel + diez e2e | Implementar, medir reloj y verificar `full` mediante el runner |

El lote inicial se emitió el 16/09/2026 con `ticket-batch-finalize-v1`. Tras la reformulación,
la frontera y la sincronización wiki las vuelve a calcular el finalizador canónico; esta tabla
no constituye un ledger ni convierte trabajo local en integración.

## Progreso medido

| corrida histórica, `--jobs 8` | check-time | reloj | resultado |
|---|---|---|---|
| Referencia antes de este mapa | 14 322 s | 78 min | 188 OK / 1 fallo |
| Tras ticket 01, sin forward matrix | 9 646 s | 22 min | 175 OK / 0 fallos |
| Tras ticket 05, dedup de estructura | 7 803 s | 18 min | 174 OK / 0 fallos |
| Gate del contrato 04 | No medido | No medido | No ejecutado |

Las corridas 01 y 05 están en `full-t01.json` y `full-t05.json`, bajo el directorio local de
medición `C:/Users/CGS03/prof/tk1/`. No son evidencia portable de POSIX ni resultados del 06.
Ahorro acumulado observado: −46 % de check-time y −77 % de reloj, sin eliminar aserciones.

## Evidence and Related Work

- [Contrato confirmado](local-verification-profile-contract.md): decisiones vigentes e IDs.
- [Histograma Git](../research/runner-git-command-histogram.md): medidas y límites de caché.
- [Matriz de líneas](../research/test-cli-coverage-redundancy.md): candidatos, no redundancia demostrada.
- [Optimización anterior](autopilot-suite-execution-cost.md): captura Windows, fixtures y reparto.
- [Stall de EOF Windows](windows-stderr-eof-stall.md): diagnóstico previo.
- [Flake de reconciliación bajo carga](autonomous-stack-reconcile-load-flake.md): investigación abierta.

## Next Review

El umbral del 20 % del plan original disparó su revisión y se atendió mediante el 04: el 06
ya no borra ni reescribe tests. La próxima revisión compara inventarios del gate y de `full`,
la medida de reloj real y sus resultados, con límites multiplataforma explícitos. Si falla el
presupuesto o una prueba, registrar el fallo; no convertir una estimación en cumplimiento.

```
