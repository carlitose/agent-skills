---
ticket_schema: 1
ticket_id: "MAD-01"
execution_mode: AFK
blocked_by: []
---

# MAD-01 — Las tres reglas, con su número, donde el instrador ya mira

## Artifact Graph
- Artifact ID: `ticket:measurable-agent-discipline:01`
- Role: `ticket`
- Parent: [measurable-agent-discipline.md](../../specs/measurable-agent-discipline.md)

## Parent Spec
[measurable-agent-discipline.md](../../specs/measurable-agent-discipline.md)

## What to Build
Tres filas nuevas en la tabla de `ask-skills/OPERATING-DEFAULTS.md` —una sesión por ticket,
agrupar las llamadas independientes, comprobar la plataforma antes de invocar un shell— cada
una con la medida que la justifica, y una línea que diga que son defaults y no prohibiciones.
La misma sustancia en memoria persistente. La medición antes/después de esta sesión queda
registrada como evidencia con su método.

## Acceptance Criteria
- [ ] Las tres reglas están en `OPERATING-DEFAULTS.md` con su número.
- [ ] Cada regla dice cuándo no aplica.
- [ ] Una línea de tabla por regla: el fichero se lee muchas veces por sesión.
- [ ] La medición antes/después queda registrada con método y fecha.
- [ ] Se dice que no existe todavía una sesión nueva medida.
- [ ] La misma sustancia queda en memoria persistente.
- [ ] El grafo canónico de artefactos sigue válido.

## Frontier
Ready. Skills-only inline. Sin decisiones humanas pendientes.

## Step-by-Step Implementation Plan
1. Emitir y validar ticket, grafo y candidato con las funciones canónicas puras.
2. Medir la sesión partida por el instante de la crítica y guardar el registro.
3. Escribir las tres filas y la línea de excepciones.
4. Guardar la memoria persistente.
5. Entregar con evidencia: admisión, verificación, PR, integración y sincronización.

## Verification
- `sess55-rate-q1.json`: turnos, llamadas, agrupamiento y repeticiones por ventana.
- Auditoría del grafo canónico de artefactos sobre el candidato.
- Registro de verificación canónico con los recibos de cada ejecución.
