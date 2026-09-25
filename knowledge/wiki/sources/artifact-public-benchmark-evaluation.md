---
type: source
title: "Medir Pi y Autopilot en un benchmark público duro"
identity_key: artifact:public-benchmark-evaluation
identity_strength: stable
source_path: docs/specs/public-benchmark-evaluation-wayfinder.md
source_digest: sha256:15421a42888984a096ff2eeefdc0370c6021c90c3d0daf4884f392899e744bbb
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-09-22
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Medir Pi y Autopilot en un benchmark público duro

Compiled from `docs/specs/public-benchmark-evaluation-wayfinder.md`. Identity is `artifact:public-benchmark-evaluation`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-22** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Child source: [[sources/ticket-public-benchmark-evaluation-pbe-01]]
- Child source: [[sources/ticket-public-benchmark-evaluation-pbe-02]]
- Child source: [[sources/ticket-public-benchmark-evaluation-pbe-03]]
- Child source: [[sources/ticket-public-benchmark-evaluation-pbe-04]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"decisions":{"headings":[],"status":"not-identified"},"exclusions":{"headings":[],"status":"not-identified"},"goals":{"headings":[5],"status":"present"},"invariants":{"headings":[],"status":"not-identified"},"verification":{"headings":[],"status":"not-identified"}},"parts":[{"index":0,"path":"wiki/sources/artifact-public-benchmark-evaluation.md","payload_bytes":6074,"payload_sha256":"15421a42888984a096ff2eeefdc0370c6021c90c3d0daf4884f392899e744bbb"}],"payload_bytes":6074,"payload_sha256":"15421a42888984a096ff2eeefdc0370c6021c90c3d0daf4884f392899e744bbb","schema":1,"source_digest":"sha256:15421a42888984a096ff2eeefdc0370c6021c90c3d0daf4884f392899e744bbb","source_identity":"artifact:public-benchmark-evaluation","source_kind":"spec"} -->

| Topic | Source sections |
|---|---|
| goals | 5: Destination |
| exclusions | no matching section identified in the source; complete source retained |
| decisions | no matching section identified in the source; complete source retained |
| invariants | no matching section identified in the source; complete source retained |
| verification | no matching section identified in the source; complete source retained |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":6074,"payload_sha256":"15421a42888984a096ff2eeefdc0370c6021c90c3d0daf4884f392899e744bbb","schema":1,"source_digest":"sha256:15421a42888984a096ff2eeefdc0370c6021c90c3d0daf4884f392899e744bbb","source_identity":"artifact:public-benchmark-evaluation"} -->
```markdown
# Medir Pi y Autopilot en un benchmark público duro

## Artifact Graph
- Artifact ID: `artifact:public-benchmark-evaluation`
- Role: `wayfinder`
- Standalone: true

### Children
- [PBE-01](../tickets/public-benchmark-evaluation/01-authorize-budget-and-runtime.md)
- [PBE-02](../tickets/public-benchmark-evaluation/02-write-the-harbor-adapter.md)
- [PBE-03](../tickets/public-benchmark-evaluation/03-run-a-three-task-pilot.md)
- [PBE-04](../tickets/public-benchmark-evaluation/04-run-and-report-the-arms.md)

## Type
Wayfinding spec

## Status
Active

## Destination
Una cifra de Pi —desnudo, skills-only y Autopilot— en un benchmark público poco contaminado,
obtenida con **un solo harness**, con coste y tiempo por tarea al lado, y con la afirmación
explícita de que el número depende del andamiaje tanto como del modelo.

## Decisiones hasta ahora

### El harness elegido: Harbor con Terminal-Bench 4.0

Es el único candidato que cumple las tres condiciones a la vez:

1. **Entra en un índice público comparable.** El Coding Agent Index v1.5 de Artificial
   Analysis se compone de DeepSWE v1.1 (113 tareas), **Terminal-Bench 4.0 (66 tareas)** y
   SWE-Atlas-QnA (124 tareas), a partes iguales. Puntúa `pass@1` promediado sobre **tres
   intentos por tarea**, y publica coste de API por tarea y tiempo de reloj activo.
2. **Admite un agente ajeno sin meterlo en el contenedor.** Harbor documenta dos vías:
   `BaseInstalledAgent`, que instala el CLI del agente dentro del entorno de la tarea, y
   `BaseAgent`, cuyo bucle vive en Harbor y actúa sobre el entorno vía `environment.exec(...)`.
   La segunda sirve para Pi sin tener que instalarlo dentro de cada contenedor.
3. **Corre en local.** El sandbox por defecto de Harbor es `docker`, con `podman`,
   `apple-container` y `singularity` como alternativas locales. Los remotos —Modal, Daytona,
   E2B y una veintena más— son opcionales y de pago.

Terminal-Bench 4.0 ya no se ejecuta con el CLI `terminal-bench`: se ejecuta con Harbor
(`harbor run -d terminal-bench/terminal-bench@4.0.0 …`).

### Lo que se descarta, y por qué

- **Multi-SWE-bench para cubrir C#.** No cubre C#. Sus 1 632 instancias son Java, TypeScript,
  JavaScript, Go, Rust, C y C++. La premisa era falsa y aquí queda corregida: si se quiere una
  medida en C#, este benchmark no la da.
- **SWE-bench Pro (held-out).** La parte no contaminada es precisamente la que no se puede
  ejecutar en local: vive detrás del leaderboard comercial de Scale. La parte pública sí se
  puede correr, pero entonces se pierde la propiedad que la hacía interesante.
- **LiveCodeBench.** Mide modelos, no agentes con herramientas. No dice nada sobre el
  andamiaje, que es justo lo que aquí se quiere medir.
- **SWE-rebench.** Se mantiene como segundo candidato real: es un pipeline de tareas frescas
  y descontaminadas por construcción, con el argumento publicado de que parte del rendimiento
  en SWE-bench Verified está inflado por contaminación. Se descarta como **primera** medida
  solo porque no entra en el índice con el que queremos compararnos.

### El coste, proyectado desde números propios

El benchmark interno (#38) midió, sobre un ticket sembrado, coste y tiempo reales por brazo:

| Brazo | $/tarea | s/tarea | Proyección a 66 tareas × 3 intentos |
|---|---|---|---|
| Pi desnudo | 0,112 | 80 | **≈ 22 $**, ≈ 4,4 h |
| Skills-only | 0,436 | 144 | **≈ 86 $**, ≈ 7,9 h |
| Autopilot | 3,977 | 1 213 | **≈ 787 $**, ≈ 67 h |

Es una proyección desde **una** tarea sembrada en un repositorio pequeño, no desde tareas de
Terminal-Bench. Sirve para decidir si se pide autorización, no para prometer una factura.

## No especificado todavía

- Si el demonio de Docker puede levantarse en esta máquina: está instalado (29.5.2) pero el
  motor no responde. Sin eso no hay sandbox local.
- Cuántas tareas de Terminal-Bench 4.0 exigen GPU. La documentación advierte que algunas la
  necesitan y recomienda un sandbox con GPU; eso saca esa fracción del alcance local.
- Si el adaptador `BaseAgent` puede dar a Pi un bucle de herramientas equivalente al que usa
  fuera del sandbox, o si hay que degradarlo, lo que cambiaría lo que se está midiendo.
- Qué parte del índice es reproducible: la comparación entre harnesses en Artificial Analysis
  sigue marcada como «coming soon», así que hoy **no existe** una referencia publicada de
  harness contra harness.

## Fuera de alcance

- Publicar resultados en ningún leaderboard.
- Cambiar Pi, las skills o el Autopilot para puntuar mejor. Si se hiciera, se mediría otra
  cosa.
- Cualquier gasto de API sin autorización explícita por importe.

## Frontera / aristas que bloquean

- **Presupuesto y runtime.** Sin un importe autorizado y sin demonio de Docker no hay medida
  posible. Desbloquea: el usuario fija el importe y decide si se levanta Docker. Ticket PBE-01.
- **Adaptador.** Sin un `BaseAgent` que arranque Pi contra `environment.exec`, Harbor no puede
  ejecutar nada nuestro. Desbloquea: adaptador escrito y cargado por `módulo:Clase`. PBE-02.
- **Piloto.** Sin tres tareas reales no se sabe si la proyección de coste vale. Desbloquea: un
  piloto de tres tareas a un intento con coste y tiempo medidos. PBE-03.
- **Tareas con GPU.** Fracción desconocida del conjunto; se declara como cobertura perdida en
  el informe en vez de sustituirla por otra cosa. Se resuelve dentro de PBE-03.

## Plan de tickets

| ID | Tipo | Modo | Bloqueado por | Qué produce |
|---|---|---|---|---|
| PBE-01 | decisión | HITL | — | Importe autorizado y decisión sobre el demonio de Docker |
| PBE-02 | task | AFK | — | Adaptador `BaseAgent` para Pi, con prueba de que arranca |
| PBE-03 | task | AFK | PBE-01, PBE-02 | Piloto de 3 tareas: coste, tiempo y fracción con GPU |
| PBE-04 | task | AFK | PBE-03 | Los tres brazos completos y el informe comparable |

## Próxima revisión
Que el usuario resuelva PBE-01: importe y Docker. Hasta entonces el mapa queda quieto; escribir
el adaptador (PBE-02) no cuesta dinero y puede adelantarse.

```
