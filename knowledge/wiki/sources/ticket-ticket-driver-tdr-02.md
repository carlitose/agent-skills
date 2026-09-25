---
type: source
title: "TDR-02 — Hoja constructora más hojas frescas de review y QA (`c1b`)"
identity_key: ticket:ticket-driver/TDR-02
identity_strength: stable
source_path: docs/tickets/ticket-driver/02-review-and-qa-in-fresh-leaves.md
source_digest: sha256:30335f71b3b47a165d1cafabdf5de5aebf70981521e7f593d7157e70bc8e75eb
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-09-23
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# TDR-02 — Hoja constructora más hojas frescas de review y QA (`c1b`)

Compiled from `docs/tickets/ticket-driver/02-review-and-qa-in-fresh-leaves.md`. Identity is `ticket:ticket-driver/TDR-02`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-23** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-ticket-driver]]
- Blocked by: [[sources/ticket-ticket-driver-tdr-01]] — `ticket:ticket-driver/TDR-01`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-ticket-driver-tdr-02.md","payload_bytes":3692,"payload_sha256":"30335f71b3b47a165d1cafabdf5de5aebf70981521e7f593d7157e70bc8e75eb"}],"payload_bytes":3692,"payload_sha256":"30335f71b3b47a165d1cafabdf5de5aebf70981521e7f593d7157e70bc8e75eb","schema":1,"source_digest":"sha256:30335f71b3b47a165d1cafabdf5de5aebf70981521e7f593d7157e70bc8e75eb","source_identity":"ticket:ticket-driver/TDR-02","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3692,"payload_sha256":"30335f71b3b47a165d1cafabdf5de5aebf70981521e7f593d7157e70bc8e75eb","schema":1,"source_digest":"sha256:30335f71b3b47a165d1cafabdf5de5aebf70981521e7f593d7157e70bc8e75eb","source_identity":"ticket:ticket-driver/TDR-02"} -->
````markdown
---
ticket_schema: 1
ticket_id: "TDR-02"
execution_mode: AFK
blocked_by:
  - "TDR-01"
---

# TDR-02 — Hoja constructora más hojas frescas de review y QA (`c1b`)

## Artifact Graph
- Artifact ID: `ticket:ticket-driver:02`
- Role: `ticket`
- Parent: [ticket-driver.md](../../specs/ticket-driver.md)

## Parent Spec
[ticket-driver.md](../../specs/ticket-driver.md)

## What to Build
`--candidate c1b`: la hoja `builder` ejecuta implement y simplify; una hoja `reviewer` **nueva**
(sesión sin memoria, prompt `prompts/reviewer.md`) recibe ticket y diff y escribe su review con la skill
`code-review`; una hoja `qa` nueva (`prompts/qa.md`) escribe plan y pruebas con `qa-test-plan`. El driver
lee los hallazgos del Markdown que la skill ya produce por el carril rápido
`[blocker|should-fix|nit] path:line - …`; un `blocker` o pruebas en rojo devuelven **una** vez al
`builder` con los hallazgos como estado, y tras el segundo fallo el run se detiene `stopped` con el
worktree y el registro íntegros. Cada hoja tiene su sesión, su coste y su tiempo en `summary.json`.
El plan de QA se copia y hashea como artefacto redactado por el modelo, nunca como prueba ejecutada.
Secciones de la spec: Comportamiento por etapa (review, qa-plan, qa-execute), Contrato de la hoja,
Regla observable/semántico (carril rápido), Candidatos (`c1b`), S2.

## Acceptance Criteria
- [ ] Con hojas de sustitución, `run --candidate c1b` lanza tres sesiones distintas; la de review y la de QA no contienen ningún turno del constructor, y `summary.json` las nombra por separado con su coste.
- [ ] Un `[blocker]` en la review o pruebas en rojo producen exactamente una segunda pasada del `builder` cuyo estado incluye los hallazgos; un segundo `blocker` deja el run `stopped` sin integrar y con el registro completo.
- [ ] Sin hallazgos de severidad reconocible, el driver no rechaza ni inventa: registra `findings: unparsed` y, en este candidato, deja el run `gated` con motivo literal (la cascada llega en TDR-03).
- [ ] El plan de QA aparece en el registro como recibo con hash y `kind: authored-by-model`; los comandos del plan que el driver ejecuta aparecen como recibos `kind: observed`.
- [ ] `c1a` sigue comportándose igual que en TDR-01 (misma suite verde).

## Frontier
Bloqueado por TDR-01: reutiliza worktree, registro, hoja e integrador.

## Step-by-Step Implementation Plan
1. `prompts/reviewer.md` y `prompts/qa.md`: solo ticket + diff + instrucción de usar la skill correspondiente inline y escribir el artefacto en una ruta fija del worktree (`.ticket-driver/review.md`, `.ticket-driver/qa-plan.md`).
2. `findings.py`: carril rápido por expresión regular sobre el formato de `code-review`; devuelve lista tipada o `unparsed`, nunca excepción.
3. Bucle de calidad en el driver: `builder → reviewer → qa → pruebas`, un reintento, `stopped` al segundo fallo; el estado del reintento se pasa como fichero en el worktree, no por argumento.
4. Recibos `authored-by-model` para plan y review; ejecución de los comandos del plan si están en un bloque ```bash``` bajo el título «Automated Checks», acotada por política.
5. `tests/`: hojas de sustitución con guiones (review limpia, review con blocker, QA con plan) y los cinco criterios.

## Testing Plan
- Unitarias: carril rápido (formatos válidos, ruidosos, ausentes); un solo reintento; recibos por tipo.
- Integración con hojas de sustitución: `integrated` con review limpia; `stopped` tras dos blockers; `gated` con review ilegible; `c1a` regresión.
- En vivo: ninguna.

## Out of Scope
- Árbitro Jev, cascada, hoja `judge`: TDR-03.
- Review dirigida por riesgo: TDR-04.
- Más de un reintento o reintentos configurables.

````
