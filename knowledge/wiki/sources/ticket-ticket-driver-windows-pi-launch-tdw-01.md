---
type: source
title: "TDW-01 — Lanzar Pi live como ejecutable contenido en Windows"
identity_key: ticket:ticket-driver-windows-pi-launch/TDW-01
identity_strength: stable
source_path: docs/tickets/ticket-driver-windows-pi-launch/01-launch-the-pi-leaf-as-a-contained-executable.md
source_digest: sha256:6c5515a202584d5831135808bd1dd6f1861a003fd9a52dae57556692ee54a912
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-09-23
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# TDW-01 — Lanzar Pi live como ejecutable contenido en Windows

Compiled from `docs/tickets/ticket-driver-windows-pi-launch/01-launch-the-pi-leaf-as-a-contained-executable.md`. Identity is `ticket:ticket-driver-windows-pi-launch/TDW-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-23** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/spec-ticket-driver-windows-pi-launch]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-ticket-driver-windows-pi-launch-tdw-01.md","payload_bytes":2718,"payload_sha256":"6c5515a202584d5831135808bd1dd6f1861a003fd9a52dae57556692ee54a912"}],"payload_bytes":2718,"payload_sha256":"6c5515a202584d5831135808bd1dd6f1861a003fd9a52dae57556692ee54a912","schema":1,"source_digest":"sha256:6c5515a202584d5831135808bd1dd6f1861a003fd9a52dae57556692ee54a912","source_identity":"ticket:ticket-driver-windows-pi-launch/TDW-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2718,"payload_sha256":"6c5515a202584d5831135808bd1dd6f1861a003fd9a52dae57556692ee54a912","schema":1,"source_digest":"sha256:6c5515a202584d5831135808bd1dd6f1861a003fd9a52dae57556692ee54a912","source_identity":"ticket:ticket-driver-windows-pi-launch/TDW-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "TDW-01"
execution_mode: AFK
blocked_by: []
---

# TDW-01 — Lanzar Pi live como ejecutable contenido en Windows

## Artifact Graph
- Artifact ID: `ticket:ticket-driver-windows-pi-launch:01`
- Role: `ticket`
- Parent: [ticket-driver-windows-pi-launch.md](../../specs/ticket-driver-windows-pi-launch.md)

## Parent Spec
[ticket-driver-windows-pi-launch.md](../../specs/ticket-driver-windows-pi-launch.md)

## What to Build
Corregir `ticket-driver/scripts/leaf.py` y el preflight del driver: en Windows npm presenta `pi.CMD`, que el contenedor `CREATE_SUSPENDED` no puede arrancar como `pi` a secas. Invocar Node nativo sobre `bin.pi` declarado en el `package.json` instalado, preservando argv, cwd, sesion, extension, limites y propiedad del job. No usar el modelo en las pruebas. Vease la spec: Observacion, Objetivo y Verificacion.

## Acceptance Criteria
- [ ] En Windows, una shim npm `.CMD`/`.BAT` reconocida produce argv con `node.exe`, JS interno al paquete y argumentos `-p`/provider/model/thinking/session/extension/`--`/prompt identicos; no se llama a `cmd.exe` ni `shell=True`.
- [ ] Pi/Node ausentes, shim sin paquete/bin o metadatos que apuntan fuera del paquete fallan en preflight antes de worktree/ledger, con un error operativo y ninguna llamada al modelo.
- [ ] Un Pi `.exe` nativo en Windows, un comando Pi POSIX y una hoja `--leaf` ficticia conservan la semantica previa; pruebas deterministas sin modelo.
- [ ] En este Windows `capture_command([node, bin.pi, '--version'])` sale 0 dentro del job y no crea sesion; la suite del driver y el perfil CI requeridos pasan sin ningun benchmark live.

## Frontier
Ready: sin dependencias. Autorizacion de corregir desde el mensaje del usuario «ok correggi sta cosa». `c1a-r2/r3` quedan fuera del ticket y bloqueados hasta merge y sincronizacion.

## Step-by-Step Implementation Plan
1. Test RED de `.CMD`/`.EXE` temporales y POSIX, preflight y preservacion de argv; conservar la evidencia de `r1` y la comprobacion `--version` sin modelo.
2. Implementar el resolver sin wrapper shell; leer `package.json` junto a la shim npm, comprobar la ruta del bin y resolver Node nativo.
3. Test GREEN en Windows y regresiones del driver; auditoria de empaquetado, review, QA y verificacion antes de la entrega autorizada por separado.

## Testing Plan
Pruebas unitarias portables con paquete ficticio y PATH simulado; smoke Windows `--version` de Pi instalado; suite del driver y perfil CI. Ninguna peticion LLM ni benchmark r2/r3.

## Out of Scope
- Repetir `c1a-r1` o iniciar `c1a-r2/r3` durante este ticket.
- Modificar el fork Pi, `ticket-autopilot` o `command_capture`.
- Soportar toda shim npm arbitraria que no se reconozca.

```
