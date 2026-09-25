---
type: source
title: "AWD-01 — Pasar el cuerpo por fichero cuando `az` es un envoltorio por lotes"
identity_key: ticket:azure-windows-delivery/AWD-01
identity_strength: stable
source_path: docs/tickets/azure-windows-delivery/01-batch-safe-description.md
source_digest: sha256:9b3e55bcd5b6c6141227486e3f0acc63e57365a8673b03fea43912f9983528e7
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-09-22
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# AWD-01 — Pasar el cuerpo por fichero cuando `az` es un envoltorio por lotes

Compiled from `docs/tickets/azure-windows-delivery/01-batch-safe-description.md`. Identity is `ticket:azure-windows-delivery/AWD-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-22** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/spec-azure-windows-delivery]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-azure-windows-delivery-awd-01.md","payload_bytes":2582,"payload_sha256":"9b3e55bcd5b6c6141227486e3f0acc63e57365a8673b03fea43912f9983528e7"}],"payload_bytes":2582,"payload_sha256":"9b3e55bcd5b6c6141227486e3f0acc63e57365a8673b03fea43912f9983528e7","schema":1,"source_digest":"sha256:9b3e55bcd5b6c6141227486e3f0acc63e57365a8673b03fea43912f9983528e7","source_identity":"ticket:azure-windows-delivery/AWD-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2582,"payload_sha256":"9b3e55bcd5b6c6141227486e3f0acc63e57365a8673b03fea43912f9983528e7","schema":1,"source_digest":"sha256:9b3e55bcd5b6c6141227486e3f0acc63e57365a8673b03fea43912f9983528e7","source_identity":"ticket:azure-windows-delivery/AWD-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "AWD-01"
execution_mode: AFK
blocked_by: []
---

# AWD-01 — Pasar el cuerpo por fichero cuando `az` es un envoltorio por lotes

## Artifact Graph
- Artifact ID: `ticket:azure-windows-delivery:01`
- Role: `ticket`
- Parent: [azure-windows-delivery.md](../../specs/azure-windows-delivery.md)

## Parent Spec
[azure-windows-delivery.md](../../specs/azure-windows-delivery.md)

## What to Build
Detectar que el ejecutable resuelto es un envoltorio por lotes de Windows y, en ese caso,
escribir el cuerpo en un fichero temporal fuera del worktree y pasarlo como un único valor
`@fichero`. Conservar intacto el argv por línea en el resto de casos. Rechazar antes de llamar
un cuerpo de más de 4000 caracteres, nombrando longitud y límite. Acotar el mensaje de error de
un mandato fallido para que no arrastre el cuerpo. Cubre Decisión, Invariantes y Criterios de
la spec.

## Acceptance Criteria
- [ ] Con envoltorio por lotes: `--description` seguido de un único `@fichero` cuyo contenido
      es el cuerpo tal cual.
- [ ] Ningún elemento del argv con salto de línea ni metacaracteres de `cmd.exe` en ese caso.
- [ ] El fichero temporal no está dentro del worktree y desaparece al terminar.
- [ ] Sin envoltorio por lotes, el argv por línea no cambia.
- [ ] Un cuerpo de más de 4000 caracteres se rechaza antes de ejecutar nada.
- [ ] El mensaje de error queda acotado y conserva `stderr` completo.
- [ ] Las suites existentes de proveedores y entrega siguen pasando.

## Frontier
Ready. Skills-only inline. Sin decisiones humanas pendientes. Integración es un gate aparte.

## Step-by-Step Implementation Plan
1. Emitir y validar ticket, grafo y candidato con las funciones canónicas puras.
2. Conservar los dos recibos de reproducción en este equipo como evidencia causal.
3. Escribir en RED las pruebas de argv por fichero, ausencia de metacaracteres, ubicación y
   borrado del temporal, camino no-Windows intacto, límite de longitud y error acotado.
4. Implementar la detección del envoltorio, el paso por fichero, el límite y el renderizado.
5. Ejecutar las suites de proveedores y entrega y el packlist; revisar, QA causal y auditoría.
6. Handoff con límites; entrega aparte, con autoridad y readback frescos, y perfil alojado
   sobre el head exacto.

## Testing Plan
Máximo 900 s por comando, cada intento registrado. Dobles y un envoltorio `.cmd` real en este
equipo; sin instancia de Azure DevOps, así que no se afirma nada sobre el servicio real.

## Out of Scope
GitHub, política de contenido del cuerpo, #35 y #36.

```
