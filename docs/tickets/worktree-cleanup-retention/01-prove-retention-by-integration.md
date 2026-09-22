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
