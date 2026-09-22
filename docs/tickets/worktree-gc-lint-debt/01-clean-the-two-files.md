---
ticket_schema: 1
ticket_id: "WGL-01"
execution_mode: AFK
blocked_by: []
---

# WGL-01 — Dejar limpios los dos archivos del recolector de worktrees

## Artifact Graph
- Artifact ID: `ticket:worktree-gc-lint-debt:01`
- Role: `ticket`
- Parent: [worktree-gc-lint-debt.md](../../specs/worktree-gc-lint-debt.md)

## Parent Spec
[worktree-gc-lint-debt.md](../../specs/worktree-gc-lint-debt.md)

## What to Build
Arreglar a mano los ocho avisos de Ruff 0.16.8 en
`ticket-autopilot/scripts/autopilot/worktree_gc.py` y `ticket-autopilot/tests/test_worktree_gc.py`
—`I001` ×3, `UP035`, `SIM117`, `B023` ×2 y `B904`— sin cambiar comportamiento y sin añadir
configuración de lint al repositorio. Cubre Decisión, Invariantes y Criterios de la spec.

## Acceptance Criteria
- [ ] Los dos archivos sin avisos bajo la selección `I,UP,SIM,B`.
- [ ] Los ocho avisos del inventario desaparecidos, uno a uno.
- [ ] La suite `tests/test_worktree_gc.py` pasa entera.
- [ ] El diff no toca otros archivos ni añade configuración.
- [ ] La supresión `# type: ignore[import-not-found]` sigue en la línea de la sentencia.

## Frontier
Ready. Skills-only inline. Sin decisiones humanas pendientes. Integración es un gate aparte.

## Step-by-Step Implementation Plan
1. Emitir y validar ticket, grafo y candidato con las funciones canónicas puras.
2. Registrar el inventario de la base y el de después, aviso por aviso.
3. Aplicar los ocho arreglos a mano, respetando el estilo de cada archivo.
4. Ejecutar lint y la suite completa de `worktree_gc`; revisar, QA causal y auditoría.
5. Handoff con límites; entrega aparte, con autoridad y readback frescos, y perfil alojado
   sobre el head exacto.

## Testing Plan
Máximo 900 s por comando, cada intento registrado. La suite tarda unos diez minutos. La
cobertura del resto del repositorio la aporta el perfil alojado, no esta medida local.

## Out of Scope
Política de lint del repositorio, los 384 avisos restantes, `E501`/`E402`, #36 y #45.
