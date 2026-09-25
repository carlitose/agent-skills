---
type: source
title: "WGR-01 — Probar que el head está retenido, aunque la rama ya no exista"
identity_key: ticket:worktree-cleanup-retention/WGR-01
identity_strength: stable
source_path: docs/tickets/worktree-cleanup-retention/01-prove-retention-by-integration.md
source_digest: sha256:ad10babaa2447ca807fabb5d8547eb2a48e495a96e30b8ff93385a5af55ea8b0
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-09-22
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# WGR-01 — Probar que el head está retenido, aunque la rama ya no exista

Compiled from `docs/tickets/worktree-cleanup-retention/01-prove-retention-by-integration.md`. Identity is `ticket:worktree-cleanup-retention/WGR-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-22** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/spec-worktree-cleanup-retention]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-worktree-cleanup-retention-wgr-01.md","payload_bytes":2792,"payload_sha256":"ad10babaa2447ca807fabb5d8547eb2a48e495a96e30b8ff93385a5af55ea8b0"}],"payload_bytes":2792,"payload_sha256":"ad10babaa2447ca807fabb5d8547eb2a48e495a96e30b8ff93385a5af55ea8b0","schema":1,"source_digest":"sha256:ad10babaa2447ca807fabb5d8547eb2a48e495a96e30b8ff93385a5af55ea8b0","source_identity":"ticket:worktree-cleanup-retention/WGR-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2792,"payload_sha256":"ad10babaa2447ca807fabb5d8547eb2a48e495a96e30b8ff93385a5af55ea8b0","schema":1,"source_digest":"sha256:ad10babaa2447ca807fabb5d8547eb2a48e495a96e30b8ff93385a5af55ea8b0","source_identity":"ticket:worktree-cleanup-retention/WGR-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "WGR-01"
execution_mode: AFK
blocked_by: []
---

# WGR-01 — Probar que el head está retenido, aunque la rama ya no exista

## Artifact Graph
- Artifact ID: `ticket:worktree-cleanup-retention:01`
- Role: `ticket`
- Parent: [worktree-cleanup-retention.md](../../specs/worktree-cleanup-retention.md)

## Parent Spec
[worktree-cleanup-retention.md](../../specs/worktree-cleanup-retention.md)

## What to Build
Añadir a `ticket-autopilot/scripts/autopilot/git_ops.py` una prueba de retención por integración y
consultarla en `assert_cleanup_safe` **solo** cuando la comprobación por rama ya ha fallado: head
sin upstream, head por delante del upstream, rama ausente o en otro head, y head separado distinto
del `base_sha`. La prueba observa la rama por defecto del remoto con `ls-remote` y demuestra la
contención localmente con `git merge-base --is-ancestor`, sin `fetch` ni escritura remota. Si el
SHA de la rama por defecto no está en el repositorio local, la prueba no vale y la limpieza se
rechaza diciéndolo. Cubre Decisión, Invariantes y Criterios de la spec.

## Acceptance Criteria
- [ ] Un head contenido en la rama por defecto del remoto permite limpiar, con la rama borrada por
      el proveedor, con la ref de seguimiento podada o sin upstream configurado.
- [ ] Un head no contenido se sigue rechazando, y el mensaje nombra la rama por defecto observada
      y su SHA.
- [ ] Sin el objeto de la rama por defecto en local, el rechazo dice que la prueba no se pudo hacer
      y nombra el `git fetch` que la haría posible.
- [ ] Un worktree sucio se sigue rechazando aunque el head esté contenido.
- [ ] La comprobación no ejecuta `fetch` ni ninguna escritura remota, demostrado con un doble que
      registra cada comando.
- [ ] Las suites `tests/test_git_ops.py` y `tests/test_worktree_gc.py` pasan enteras.

## Frontier
Ready. Skills-only inline. Sin decisiones humanas pendientes. Integración es un gate aparte.

## Step-by-Step Implementation Plan
1. Emitir y validar ticket, grafo y candidato con las funciones canónicas puras.
2. Escribir las pruebas nuevas sobre repositorios Git reales desechables y registrarlas en RED.
3. Implementar la prueba de retención y engancharla en los cuatro puntos de rechazo.
4. Ejecutar lint y las suites afectadas; revisar, QA causal y auditoría.
5. Handoff con límites; entrega aparte, con autoridad y readback frescos, y perfil alojado sobre
   el head exacto.

## Testing Plan
Máximo 900 s por comando, cada intento registrado. Las pruebas crean repositorios temporales
propios; ningún worktree de la máquina se toca.

## Out of Scope
Las protecciones de run en curso, run en espera y ticket en espera administrativa; el borrado
automático o en lote; consultar la API del proveedor.

```
