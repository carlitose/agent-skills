---
type: source
title: "Ticket Driver — lanzamiento de la hoja Pi en Windows"
identity_key: spec:ticket-driver-windows-pi-launch
identity_strength: stable
source_path: docs/specs/ticket-driver-windows-pi-launch.md
source_digest: sha256:22a7f8a04475507cf0883c53511fb31ef6214d6eee1f7b96c1c33a1beceb2a7e
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-09-23
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Ticket Driver — lanzamiento de la hoja Pi en Windows

Compiled from `docs/specs/ticket-driver-windows-pi-launch.md`. Identity is `spec:ticket-driver-windows-pi-launch`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-23** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Child source: [[sources/ticket-ticket-driver-windows-pi-launch-tdw-01]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"decisions":{"headings":[],"status":"not-identified"},"exclusions":{"headings":[],"status":"not-identified"},"goals":{"headings":[],"status":"not-identified"},"invariants":{"headings":[],"status":"not-identified"},"verification":{"headings":[],"status":"not-identified"}},"parts":[{"index":0,"path":"wiki/sources/spec-ticket-driver-windows-pi-launch.md","payload_bytes":3517,"payload_sha256":"22a7f8a04475507cf0883c53511fb31ef6214d6eee1f7b96c1c33a1beceb2a7e"}],"payload_bytes":3517,"payload_sha256":"22a7f8a04475507cf0883c53511fb31ef6214d6eee1f7b96c1c33a1beceb2a7e","schema":1,"source_digest":"sha256:22a7f8a04475507cf0883c53511fb31ef6214d6eee1f7b96c1c33a1beceb2a7e","source_identity":"spec:ticket-driver-windows-pi-launch","source_kind":"spec"} -->

| Topic | Source sections |
|---|---|
| goals | no matching section identified in the source; complete source retained |
| exclusions | no matching section identified in the source; complete source retained |
| decisions | no matching section identified in the source; complete source retained |
| invariants | no matching section identified in the source; complete source retained |
| verification | no matching section identified in the source; complete source retained |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3517,"payload_sha256":"22a7f8a04475507cf0883c53511fb31ef6214d6eee1f7b96c1c33a1beceb2a7e","schema":1,"source_digest":"sha256:22a7f8a04475507cf0883c53511fb31ef6214d6eee1f7b96c1c33a1beceb2a7e","source_identity":"spec:ticket-driver-windows-pi-launch"} -->
```markdown
# Ticket Driver — lanzamiento de la hoja Pi en Windows

## Artifact Graph
- Artifact ID: `spec:ticket-driver-windows-pi-launch`
- Role: `spec`
- Standalone: true

### Children
- [01 — lanzar Pi sin pasar por la shim CMD](../tickets/ticket-driver-windows-pi-launch/01-launch-the-pi-leaf-as-a-contained-executable.md)

## Observacion y causa

En el primer intento autorizado de TDR-05, `c1a-r1` (2026-09-23), `ticket-driver/scripts/leaf.py` paso `pi -p …` a `autopilot.command_capture.capture_command`. En Windows, ese modulo crea el proceso **suspendido**, lo incorpora a un job y luego lo reanuda. En este host `pi` no es un ejecutable nativo: `shutil.which('pi')` resuelve `pi.CMD`. La recepcion original `C:/bench38/driver-c1a-r1/project/.git/ticket-driver/runs/tdr-1790191265-0a618dacfc/receipts/leaf.json` registra `failure: launch`, sin sesion ni llamada al modelo. La reproduccion aislada `capture_command(['pi','--version'])` devuelve `FileNotFoundError [WinError 2]`, `started=False`.

El harness antiguo lanzaba normalmente la shim `pi.CMD` resuelta por `shutil.which`; no se puede copiar ese mecanismo al driver sin perder la propiedad del arbol de procesos. El `package.json` instalado de `@earendil-works/pi-coding-agent` v0.87.1 declara `bin.pi = dist/bundle/cli.js`. La shim npm ejecuta Node con ese JS. La invocacion sin modelo `capture_command([node.exe, cli.js, '--version'])` ya devolvio 0 y `0.87.1`. Fuentes: documentacion Pi local `docs/cli.md`, `docs/cli-integration.md`, metadatos instalados; Context7 `/earendil-works/pi` confirma el binario del paquete.

## Objetivo y contrato

- En una hoja **live** sobre Windows, resolver `pi` en PATH. Si resulta ser una shim npm `.cmd`/`.bat`, localizar el paquete Pi instalado junto a ella, leer el destino `bin.pi` de su `package.json` e invocar **Node nativo** con el JS y los mismos argumentos `-p`, proveedor/modelo, sesion, extension, `--` y prompt. No usar `cmd.exe`, `shell=True` ni la shim `.CMD` dentro del job.
- Si `pi` es un `.exe` nativo en Windows, usarlo directamente. En POSIX, conservar la ruta del ejecutable Pi del PATH. Las hojas de sustitucion `--leaf` no cambian.
- Antes de crear worktree o ledger, rechazar Pi o Node ausentes, shim sin paquete/bin valido, o JS fuera del paquete con un error util. No llamar al modelo para comprobar la instalacion. No adivinar rutas para otros layouts npm.
- Mantener `capture_command` como unico propietario del proceso y de sus limites, recibos, tiempo, cwd y entorno. No reiniciar `c1a-r1` ni modificar el presupuesto del lote TDR-05.

## Verificacion

1. Pruebas unitarias portables con una shim `.CMD` ficticia, un paquete npm temporal, metadatos `bin.pi` y Node `.exe` ficticio: argv exacta, prompt literal, rechazo temprano si falta una pieza o si el bin sale del paquete. Pruebas POSIX y `.exe` nativo; sin modelo.
2. En Windows, prueba de integracion **sin modelo** por la misma via contenida: `--version` con Node/JS Pi instalados; salida 0 y version; sin sesion.
3. Suite causal del driver, grafo de artefactos, limites y CI del head exacto. `r2` queda fuera de este ticket: solo despues de merge, sincronizacion y verificacion de la instalacion, bajo su autorizacion de lote previa.

## Fuera de alcance

No modificar Pi, `command_capture`, el harness, la autorizacion benchmark, Jev ni `ticket-autopilot`. No alterar el protocolo de hojas ni iniciar benchmarks live. No se promete compatibilidad con cualquier shim npm ajena al paquete reconocido: se falla de forma cerrada.

```
