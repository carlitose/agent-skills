---
ticket_schema: 1
ticket_id: "TDR-04"
execution_mode: AFK
blocked_by:
  - "TDR-03"
---

# TDR-04 — Riesgo por función y review dirigida (`c3`, `c4`)

## Artifact Graph
- Artifact ID: `ticket:ticket-driver:04`
- Role: `ticket`
- Parent: [ticket-driver.md](../../specs/ticket-driver.md)

## Parent Spec
[ticket-driver.md](../../specs/ticket-driver.md)

## What to Build
El driver calcula el diff **por función** del candidato (AST de Python en esta versión: funciones
añadidas o modificadas con su hunk), pregunta `risk.semantic_change` (score) por cada una en una sola
petición, y las funciones por encima del umbral de política reciben una hoja `reviewer` nueva dirigida
solo a ellas (`prompts/reviewer-directed.md`: hunk, criterios del ticket, pregunta explícita por
redondeo, límites y aritmética de dinero). `--candidate c3a|c3b` = `c2x` + esto. `--candidate c4` =
una sola hoja como el brazo skills-only + riesgo + review dirigida, **sin** worktree propio,
integración ni árbitro de gates: mide el valor de Jev aislado. Todo juicio y su función van a
`judgments.jsonl`. Secciones de la spec: Regla observable/semántico (riesgo latente), Preguntas
iniciales (`risk.semantic_change`), Candidatos (`c3`, `c4`), S4.

## Acceptance Criteria
- [ ] Sobre el diff del repositorio sembrado con la hoja de sustitución, el driver enumera exactamente las funciones Python añadidas o modificadas con su hunk; ficheros no Python se registran como `unsupported`, no se omiten en silencio.
- [ ] Con el servidor falso devolviendo scores altos para dos funciones y bajos para el resto, la hoja dirigida recibe solo esas dos y sus hallazgos entran en el bucle de calidad como los de la review general.
- [ ] `c4` termina en el mismo directorio de trabajo (sin worktree) con `summary.json`, juicios y hoja dirigida, y sin ninguna llamada al integrador ni a los gates del árbitro.
- [ ] `c2` y `c1` no cambian de comportamiento (suites verdes).

## Frontier
Bloqueado por TDR-03: usa el árbitro, la cascada y los recibos.

## Step-by-Step Implementation Plan
1. `function_diff.py`: `ast` sobre base y candidato por fichero `.py` tocado; emparejar por nombre calificado; hunk por función con `difflib`.
2. `questions/risk.semantic_change.json` con niveles concretos (de «formato o renombre» a «cambia redondeo, límites o aritmética de dinero»); umbral en `policy.json`.
3. `prompts/reviewer-directed.md`; hoja dirigida integrada en el bucle tras la review general.
4. Configuración `c4`: bandera que desactiva worktree, integrador y árbitro de gates, conserva riesgo y review dirigida.
5. `tests/`: fixtures con funciones añadidas, modificadas, renombradas y un fichero no Python; guiones del servidor falso; los cuatro criterios.

## Testing Plan
- Unitarias: diff por función (añadida, modificada, renombrada, borrada, decoradores, métodos anidados); agrupación en una petición; umbral.
- Integración con hojas y servidor falsos: `c3a` con dos funciones dirigidas; `c4` sin worktree.
- En vivo: ninguna; el comportamiento real de Jev sobre hunks se mide en TDR-05.

## Out of Scope
- Otros lenguajes que Python.
- Cambiar la review general o `code-review`.
- Calibración del umbral de riesgo.
