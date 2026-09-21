---
ticket_schema: 1
ticket_id: "NDW-01"
execution_mode: AFK
blocked_by: []
---

# Añadir el estado del árbol como sexta comprobación del checkpoint

## Artifact Graph
- Artifact ID: `artifact:no-dangling-work-01`
- Role: `ticket`
- Parent: [Ningún trabajo colgado al cerrar una fase](../../specs/no-dangling-work.md)

## Parent Spec
[Ningún trabajo colgado al cerrar una fase](../../specs/no-dangling-work.md)

## What to Build
Ampliar `ask-skills/PLAN-REVIEW-CHECKPOINT.md` con una sexta comprobación, **estado del árbol**: al
cerrar una fase se inventarían todos los checkouts del repositorio (`git worktree list` y
`worktree-gc-plan`) y cada ruta no limpia recibe exactamente una disposición —`commit` con su
ticket, `discard` con su razón, o `handoff` con destinatario y patch guardado—. La regla dice
explícitamente que «lo miro luego» no es una disposición, y que un worktree con proyección
aplicada y ticket no integrado nunca se descarta sin patch.

Añadir el spec del padre al repositorio y ampliar `test_plan_review_checkpoint.py` para que la
sexta comprobación y las tres disposiciones sean verificables estructuralmente.

## Acceptance Criteria
- [ ] La referencia del checkpoint enumera seis comprobaciones y la sexta es el estado del árbol.
- [ ] Nombra las tres disposiciones exactas y declara que no existe una cuarta.
- [ ] Dice que el inventario cubre todos los checkouts del repositorio, no solo el activo.
- [ ] Protege la única copia: proyección aplicada y ticket no integrado implica patch antes de
      cualquier descarte.
- [ ] La prueba estructural falla si desaparece cualquiera de esos puntos y la referencia sigue
      por debajo de su límite de palabras.
- [ ] El spec del padre queda añadido en la misma entrega.

## Frontier
Independiente. Es documentación de disciplina y su prueba estructural.

## Step-by-Step Implementation Plan
1. Ampliar primero la prueba para que falle.
2. Redactar la sexta comprobación en la referencia, respetando el límite de palabras.
3. Ejecutar la prueba y las suites de skills.

## Testing Plan
Prueba estructural ampliada, suites de skills y grafo, perfil quick en ambas plataformas.

## Out of Scope
- El barrido del runner y la resolución de los worktrees actuales, que son slices propios.
