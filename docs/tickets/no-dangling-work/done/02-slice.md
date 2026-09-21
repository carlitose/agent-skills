---
ticket_schema: 1
ticket_id: "NDW-02"
execution_mode: AFK
blocked_by:
  - "NDW-01"
---

# Operación `worktree-sweep` para los temporales que el runner crea

## Artifact Graph
- Artifact ID: `artifact:no-dangling-work-02`
- Role: `ticket`
- Parent: [Ningún trabajo colgado al cerrar una fase](../../specs/no-dangling-work.md)

## Parent Spec
[Ningún trabajo colgado al cerrar una fase](../../specs/no-dangling-work.md)

## What to Build
Añadir al runner una operación `worktree-sweep` con dos modos: sin `--apply` informa; con `--apply`
retira. Su fuente de elegibilidad es exclusivamente `worktree-gc-plan`: retira los worktrees que
ese plan marca `eligible`, más los worktrees registrados bajo el directorio temporal del sistema con
prefijo `ticket-wiki-` cuya run no está viva (sin ledger que los referencie en estado no terminal).
Deja un recibo con cada ruta, su razón y el resultado, bajo el directorio de estado del runner.

No toca nada `protected`, ni rutas fuera del directorio temporal que no figuren en el plan, ni
worktrees de otros repositorios. No debilita el `finally` existente de `wiki_sync.py`: lo
complementa para el caso en que el proceso muere antes de ejecutarlo.

## Acceptance Criteria
- [ ] Sin `--apply`, la operación no modifica nada y devuelve la lista exacta de lo que retiraría.
- [ ] Con `--apply`, retira solo entradas `eligible` del `gc-plan` y temporales `ticket-wiki-*`
      huérfanos; un temporal cuya run sigue viva se conserva.
- [ ] Un worktree `protected` no se toca aunque esté sucio.
- [ ] Cada retirada deja recibo con ruta, razón y resultado, y el recibo es append-only.
- [ ] Pruebas con temporales sintéticos registrados como worktrees cubren los tres casos:
      huérfano elegible, run viva, y protegido.

## Frontier
Independiente en código; se entrega después del slice 01 para que la regla exista antes que la
herramienta que la ejecuta.

## Step-by-Step Implementation Plan
1. Escribir las pruebas con worktrees sintéticos que fallan hoy.
2. Implementar la operación sobre `worktree-gc-plan`, sin duplicar su clasificación.
3. Documentar el comando en la referencia de worktrees del runner.

## Testing Plan
Pruebas del runner con repositorios temporales, suites de worktree y CLI, y el perfil `full` en
Linux por tratarse de un cambio al runner; Windows según la limitación documentada del host.

## Out of Scope
- Borrar worktrees sucios no elegibles.
- Cambiar la clasificación de `worktree-gc-plan`.
