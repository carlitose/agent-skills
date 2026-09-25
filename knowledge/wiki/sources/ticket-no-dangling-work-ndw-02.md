---
type: source
title: "Operación `worktree-sweep` para los temporales que el runner crea"
identity_key: ticket:no-dangling-work/NDW-02
identity_strength: stable
source_path: docs/tickets/no-dangling-work/done/02-slice.md
source_digest: sha256:75b47198bcc5c0fdef0b5dd4ca17a9bc0f495a15df2fb2be96b5555d5b8f2718
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-21
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Operación `worktree-sweep` para los temporales que el runner crea

Compiled from `docs/tickets/no-dangling-work/done/02-slice.md`. Identity is `ticket:no-dangling-work/NDW-02`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-21** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/spec-no-dangling-work]]
- Blocked by: [[sources/ticket-no-dangling-work-ndw-01]] — `ticket:no-dangling-work/NDW-01`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-no-dangling-work-ndw-02.md","payload_bytes":2483,"payload_sha256":"75b47198bcc5c0fdef0b5dd4ca17a9bc0f495a15df2fb2be96b5555d5b8f2718"}],"payload_bytes":2483,"payload_sha256":"75b47198bcc5c0fdef0b5dd4ca17a9bc0f495a15df2fb2be96b5555d5b8f2718","schema":1,"source_digest":"sha256:75b47198bcc5c0fdef0b5dd4ca17a9bc0f495a15df2fb2be96b5555d5b8f2718","source_identity":"ticket:no-dangling-work/NDW-02","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2483,"payload_sha256":"75b47198bcc5c0fdef0b5dd4ca17a9bc0f495a15df2fb2be96b5555d5b8f2718","schema":1,"source_digest":"sha256:75b47198bcc5c0fdef0b5dd4ca17a9bc0f495a15df2fb2be96b5555d5b8f2718","source_identity":"ticket:no-dangling-work/NDW-02"} -->
```markdown
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

```
