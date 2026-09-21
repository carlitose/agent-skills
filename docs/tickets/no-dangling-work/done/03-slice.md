---
ticket_schema: 1
ticket_id: "NDW-03"
execution_mode: AFK
blocked_by: []
---

# Declarar el seguimiento de los JSON por test del prototipo de cobertura

## Artifact Graph
- Artifact ID: `artifact:no-dangling-work-03`
- Role: `ticket`
- Parent: [Ningún trabajo colgado al cerrar una fase](../../specs/no-dangling-work.md)

## Parent Spec
[Ningún trabajo colgado al cerrar una fase](../../specs/no-dangling-work.md)

## What to Build
Añadir a `.gitignore` los JSON por test que `docs/prototypes/suite-cost-one-percent/coverage_matrix.py`
escribe en `docs/prototypes/suite-cost-one-percent/coverage/`, conservando versionado el
`report.json` agregado, y declarar esa decisión en el docstring del script: el agregado es la
evidencia, los ficheros por test son materia prima regenerable.

## Acceptance Criteria
- [ ] Tras regenerar la cobertura, `git status` no muestra los JSON por test como sin seguimiento.
- [ ] `report.json` sigue versionado y sin cambios de política.
- [ ] El docstring del script dice qué se versiona y qué se ignora.
- [ ] Ninguna otra ruta cambia de estado de seguimiento.

## Frontier
Independiente y pequeño.

## Step-by-Step Implementation Plan
1. Comprobar qué escribe el script y que `report.json` es el agregado.
2. Añadir la regla de `.gitignore` y el docstring.
3. Verificar con el propio script que el estado queda limpio.

## Testing Plan
Ejecución del prototipo y `git status`; perfil quick en ambas plataformas.

## Out of Scope
- Cambiar el contenido o el formato de la cobertura.
