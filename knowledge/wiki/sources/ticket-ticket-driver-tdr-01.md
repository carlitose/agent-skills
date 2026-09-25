---
type: source
title: "TDR-01 — La skill `ticket-driver` lleva un encargo de principio a fin con una hoja (`c1a`)"
identity_key: ticket:ticket-driver/TDR-01
identity_strength: stable
source_path: docs/tickets/ticket-driver/01-drive-one-ticket-with-one-leaf.md
source_digest: sha256:59d5099f5cebd3b922c7bbd82a804b22bbcf3c693645294911c76dddfbe5c4f9
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-09-23
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# TDR-01 — La skill `ticket-driver` lleva un encargo de principio a fin con una hoja (`c1a`)

Compiled from `docs/tickets/ticket-driver/01-drive-one-ticket-with-one-leaf.md`. Identity is `ticket:ticket-driver/TDR-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-23** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-ticket-driver]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-ticket-driver-tdr-01.md","payload_bytes":5958,"payload_sha256":"59d5099f5cebd3b922c7bbd82a804b22bbcf3c693645294911c76dddfbe5c4f9"}],"payload_bytes":5958,"payload_sha256":"59d5099f5cebd3b922c7bbd82a804b22bbcf3c693645294911c76dddfbe5c4f9","schema":1,"source_digest":"sha256:59d5099f5cebd3b922c7bbd82a804b22bbcf3c693645294911c76dddfbe5c4f9","source_identity":"ticket:ticket-driver/TDR-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":5958,"payload_sha256":"59d5099f5cebd3b922c7bbd82a804b22bbcf3c693645294911c76dddfbe5c4f9","schema":1,"source_digest":"sha256:59d5099f5cebd3b922c7bbd82a804b22bbcf3c693645294911c76dddfbe5c4f9","source_identity":"ticket:ticket-driver/TDR-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "TDR-01"
execution_mode: AFK
blocked_by: []
---

# TDR-01 — La skill `ticket-driver` lleva un encargo de principio a fin con una hoja (`c1a`)

## Artifact Graph
- Artifact ID: `ticket:ticket-driver:01`
- Role: `ticket`
- Parent: [ticket-driver.md](../../specs/ticket-driver.md)

## Parent Spec
[ticket-driver.md](../../specs/ticket-driver.md)

## What to Build
La skill nueva `ticket-driver/` (SKILL.md breve, `scripts/ticket_driver.py`, `prompts/builder.md`,
`policy.json`, `tests/`) y su primer candidato: `run --candidate c1a (--ticket <path> | --task <path>)
--repo <path> [--base <ref>] [--leaf <ejecutable>]`. El driver crea un worktree aislado con
`git_ops.create_isolated_worktree`, lanza **una** hoja `pi -p` (cwd = worktree, `--session-dir` bajo el
run, prompt versionado con su hash) que ejecuta el giro de skills inline, observa el diff y el árbol
(`git write-tree`, `semantic_candidate_ref`), ejecuta él mismo la suite del proyecto con
`capture_command` y escribe recibos hasheados, hace commit del candidato, integra en la rama objetivo
local solo si es *fast-forward* con `merge-base --is-ancestor` y árbol comparado, y escribe
`summary.json` una vez (identidades, tiempos por hoja desde la sesión, coste y tokens, hash de
política y prompt). Registro append-only bajo `<repo>/.git/ticket-driver/runs/<run_id>/`. La hoja no
recibe CLI ni esquema: sus únicas salidas son ficheros y prosa. `--leaf` permite sustituir `pi` por un
ejecutable de prueba. Secciones de la spec: Decisión, Arquitectura (componentes, contrato de la hoja,
registro), Invariantes, Contratos externos (`pi -p`, biblioteca reutilizada), Modos de fallo, S1.

## Acceptance Criteria
- [ ] Con la hoja de sustitución sobre el repositorio sembrado del benchmark, `run --candidate c1a` termina `integrated`: la rama objetivo avanza *fast-forward* al commit del candidato, el árbol integrado es igual al observado en el worktree, y `summary.json` nombra base, árbol, commit, hoja y recibos.
- [ ] Ningún dato del registro procede de la hoja: el árbol lo calcula el driver, cada entrada de evidencia apunta a un recibo que el driver escribió, y el hash de cada recibo coincide con el fichero.
- [ ] Pruebas en rojo del proyecto → el run acaba `failed: tests` con el recibo, sin integrar y con el worktree intacto; hoja que excede el tiempo de política → `failed: leaf-timeout` con el árbol de procesos terminado y la sesión parcial conservada.
- [ ] `summary.json` existente, `--repo` que no es un repositorio, base inexistente o rama objetivo sucia → rechazo con motivo literal antes de crear el worktree.
- [ ] La skill entra en la infraestructura del repositorio: `ticket-driver` en `PYTHON_ROOTS` de `scripts/test-local.mjs`, `ticket-driver/SKILL.md` en `scripts/file-limits.json` con límite ≤ 40 líneas, y `pi_sync` la descubre como skill propia (35) sin cambiar ninguna otra.
- [ ] Ningún test lanza `pi` ni ningún modelo; ningún run en vivo forma parte de este ticket.

## Frontier
Listo: nada lo bloquea. Es la base de TDR-02, TDR-03 y TDR-04. Fuera del repositorio, y sin formar
parte de este candidato, el operador añade al harness privado el brazo `driver` (`start driver
c1a-<etiqueta>`) y las métricas de LOC sin pruebas y cobertura para todos los brazos; se anota aquí para
que TDR-05 lo exija, no para que este ticket lo verifique.

## Step-by-Step Implementation Plan
1. `ticket-driver/SKILL.md` (≤ 40 líneas): qué hace, un ejemplo de `run`, la prohibición de ejecutar en vivo sin autorización; registrar en `scripts/file-limits.json` y `PYTHON_ROOTS`.
2. `scripts/ticket_driver.py`: `argparse` con `run`/`status`/`report`; `policy.json` con proveedor, modelo, razonamiento, tiempo máximo de hoja, tope de bytes por recibo; importar solo funciones puras de `ticket-autopilot/scripts/autopilot` (`ticket_contract`, `candidate_contract`, `git_ops`, `command_capture`) resolviendo el root desde la ruta del propio script, sin `cli.py` ni `kernel`.
3. Registro: `ledger.jsonl` append-only, `receipts/<id>.json` con argv, cwd relativo, exit code, duración, hash y salida acotada; `summary.json` escrito una vez con `os.replace`.
4. Hoja: `leaf.py` construye el comando `pi -p --provider … --model … --thinking … --session-dir …` con el prompt de `prompts/builder.md`, lo ejecuta con `capture_command` (tiempo de política, sin stdin) y lee coste/turnos/tokens de la sesión `.jsonl`; `--leaf` sustituye el ejecutable.
5. Integrador: commit en la rama del worktree con autor del driver; `merge-base --is-ancestor <base> <candidate>` y `rev-parse <base>^{tree}` frente al árbol observado; `update-ref` de la rama objetivo solo si la rama no se movió desde el inicio del run; en caso contrario `failed: integration` con el candidato intacto.
6. `tests/`: hoja de sustitución (`tests/fake_leaf.py`) que escribe ficheros predeterminados en el worktree; casos de los cinco criterios sobre un repositorio temporal sembrado con `git_test_support`.

## Testing Plan
- Unitarias: identidad del candidato observada; hash estable de recibos y tope de salida; rechazos previos al worktree; `summary.json` no se sobrescribe; fallo cerrado si falta `pi` y no hay `--leaf`.
- Integración con hoja de sustitución: run completo `integrated`; run con pruebas en rojo `failed: tests`; hoja lenta `failed: leaf-timeout`; rama objetivo movida durante el run `failed: integration`.
- Infraestructura: `node scripts/test-local.mjs quick` incluye la suite nueva; `check_file_limits.py` pasa con la entrada nueva.
- En vivo: ninguna prueba; el primer run real pertenece a un lote de benchmark autorizado (TDR-05).

## Out of Scope
- Hojas de review y QA separadas (`c1b`): TDR-02.
- Árbitro, cascada y gates humanos: TDR-03.
- Entrega a proveedor (PR, merge remoto), varios tickets con dependencias, wiki, recolección de worktrees.
- Cambios en `ticket-autopilot`, `execute-ticket` o cualquier otra skill.

```
