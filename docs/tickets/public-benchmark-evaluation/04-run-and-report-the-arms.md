---
ticket_schema: 1
ticket_id: "PBE-04"
execution_mode: AFK
blocked_by:
  - PBE-03
---

# PBE-04 — Los brazos completos y un informe que diga de qué depende el número

## Artifact Graph
- Artifact ID: `ticket:public-benchmark-evaluation:04`
- Role: `ticket`
- Parent: [public-benchmark-evaluation-wayfinder.md](../../specs/public-benchmark-evaluation-wayfinder.md)

## Parent Spec
[public-benchmark-evaluation-wayfinder.md](../../specs/public-benchmark-evaluation-wayfinder.md)

## What to Build
El conjunto autorizado en PBE-01, con los brazos autorizados, y un informe con las mismas
magnitudes que publica el índice público: `pass@1` promediado sobre los intentos acordados,
coste de API por tarea y tiempo de reloj activo por tarea.

El informe debe decir, en su primera afirmación, que la cifra mide **modelo más andamiaje** y
que la comparación entre harnesses no está publicada todavía en el índice de referencia.

## Acceptance Criteria
- [ ] `pass@1` por brazo con el número de intentos declarado.
- [ ] Coste por tarea y tiempo activo por tarea, por brazo.
- [ ] Las tareas no ejecutadas —GPU u otras— se declaran como cobertura perdida, no se sustituyen.
- [ ] El informe dice que el número depende del andamiaje y que la comparación entre harnesses
      del índice sigue sin publicarse.
- [ ] Ningún cambio en Pi, skills o Autopilot para puntuar mejor.

## Frontier
Bloqueado por PBE-03.

## Step-by-Step Implementation Plan
1. Ejecutar el conjunto autorizado por brazo con intentos iguales.
2. Reducir a las tres magnitudes del índice.
3. Escribir el informe con la cobertura perdida y la dependencia del andamiaje.

## Verification
- Registros por intento y la reducción a las tres magnitudes.
- Lista de tareas no ejecutadas con su motivo.
