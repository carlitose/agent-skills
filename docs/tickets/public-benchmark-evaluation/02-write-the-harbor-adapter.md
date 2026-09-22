---
ticket_schema: 1
ticket_id: "PBE-02"
execution_mode: AFK
blocked_by: []
---

# PBE-02 — Un `BaseAgent` de Harbor que arranque Pi

## Artifact Graph
- Artifact ID: `ticket:public-benchmark-evaluation:02`
- Role: `ticket`
- Parent: [public-benchmark-evaluation-wayfinder.md](../../specs/public-benchmark-evaluation-wayfinder.md)

## Parent Spec
[public-benchmark-evaluation-wayfinder.md](../../specs/public-benchmark-evaluation-wayfinder.md)

## What to Build
Un módulo Python con una clase que herede de `harbor.agents.base.BaseAgent` e implemente
`name()`, `version()`, `setup(environment)` y `run(instruction, environment, context)`. El bucle
de Pi vive en Harbor y actúa sobre la tarea a través de `environment.exec(...)`; no se instala
Pi dentro del contenedor. Se invoca como `-a modulo.ruta:Clase`.

Tres variantes del mismo adaptador, una por brazo: Pi desnudo, Pi con skills, Pi con Autopilot.
La diferencia entre brazos es el andamiaje, no el modelo ni el prompt de la tarea.

## Acceptance Criteria
- [ ] El adaptador carga por `módulo:Clase` sin registrarse en Harbor.
- [ ] Arranca contra la tarea `hello-world` y deja trayectoria legible.
- [ ] Los tres brazos comparten modelo, nivel de razonamiento y texto de la tarea.
- [ ] El coste y los tokens de cada intento salen del fichero de sesión del propio brazo.
- [ ] Si Pi no puede ejercer alguna herramienta dentro del sandbox, queda escrito cuál.

## Frontier
Ready: escribir el adaptador no cuesta dinero de API. Validarlo contra tareas reales depende de
PBE-01.

## Step-by-Step Implementation Plan
1. Leer la referencia de `BaseAgent` y el ejemplo `marker_agent.py`.
2. Escribir el adaptador y las tres variantes de brazo.
3. Probar contra `hello-world` con un sandbox local.
4. Registrar qué herramientas de Pi quedan degradadas dentro del sandbox, si alguna.

## Verification
- Trayectoria de `hello-world` por cada brazo.
- Lista explícita de capacidades degradadas, o su ausencia.
