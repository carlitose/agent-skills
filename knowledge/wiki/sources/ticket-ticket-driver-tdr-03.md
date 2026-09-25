---
type: source
title: "TDR-03 — Árbitro Jev, cascada a LLM fresco y gate humano (`c2`)"
identity_key: ticket:ticket-driver/TDR-03
identity_strength: stable
source_path: docs/tickets/ticket-driver/03-typed-judgments-and-the-cascade.md
source_digest: sha256:a53ce2397f76c63a6447d149f7d3834311ad74e043ebed7d586728dd07f1715b
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-09-23
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# TDR-03 — Árbitro Jev, cascada a LLM fresco y gate humano (`c2`)

Compiled from `docs/tickets/ticket-driver/03-typed-judgments-and-the-cascade.md`. Identity is `ticket:ticket-driver/TDR-03`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-23** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-ticket-driver]]
- Blocked by: [[sources/ticket-ticket-driver-tdr-01]] — `ticket:ticket-driver/TDR-01`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-ticket-driver-tdr-03.md","payload_bytes":4490,"payload_sha256":"a53ce2397f76c63a6447d149f7d3834311ad74e043ebed7d586728dd07f1715b"}],"payload_bytes":4490,"payload_sha256":"a53ce2397f76c63a6447d149f7d3834311ad74e043ebed7d586728dd07f1715b","schema":1,"source_digest":"sha256:a53ce2397f76c63a6447d149f7d3834311ad74e043ebed7d586728dd07f1715b","source_identity":"ticket:ticket-driver/TDR-03","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":4490,"payload_sha256":"a53ce2397f76c63a6447d149f7d3834311ad74e043ebed7d586728dd07f1715b","schema":1,"source_digest":"sha256:a53ce2397f76c63a6447d149f7d3834311ad74e043ebed7d586728dd07f1715b","source_identity":"ticket:ticket-driver/TDR-03"} -->
```markdown
---
ticket_schema: 1
ticket_id: "TDR-03"
execution_mode: AFK
blocked_by:
  - "TDR-01"
---

# TDR-03 — Árbitro Jev, cascada a LLM fresco y gate humano (`c2`)

## Artifact Graph
- Artifact ID: `ticket:ticket-driver:03`
- Role: `ticket`
- Parent: [ticket-driver.md](../../specs/ticket-driver.md)

## Parent Spec
[ticket-driver.md](../../specs/ticket-driver.md)

## What to Build
`--candidate c2a|c2b`: sobre `c1a` o `c1b`, el driver consulta al árbitro en los puntos semánticos
—`review.findings_block`, `review.scope_complete`, `qa.evidence_class`, `verify.claim_supported`,
`retry.recoverable`— con un cliente de `POST https://api.typesafe.ai/v1/systemone` (`model:
jev-latest`, clave solo de `TYPESAFE_API_KEY`), preguntas en `questions/*.json`, umbrales y bandas
de incertidumbre en `policy.json` declarados como conjetura. Cada juicio va a `judgments.jsonl` con
hash del estado, probabilidades, `confidence`, umbral y resultado; `usage` se acumula aparte. En la
banda de incertidumbre la cascada lanza una hoja `judge` nueva (solo diff, prosa y pregunta) y, si
sigue incierto, abre un gate humano con motivo literal y detiene el run con el estado íntegro. El
árbitro solo se llama si el repositorio está en `external_judgment_allowed`; si no, o ante
`429`/`529`/sin red tras reintentos acotados, la cascada empieza en `judge` y el registro dice
`arbiter: unavailable`. La hoja constructora nunca participa. Secciones de la spec: Contrato del
árbitro, Contrato de la cascada, Preguntas iniciales, Seguridad y datos, Modos de fallo, S3.

## Acceptance Criteria
- [ ] Con un servidor Jev falso, cada pregunta se construye con el estado exacto (campos nombrados, hunk o prosa, no rutas), y las preguntas independientes sobre el mismo estado viajan en una sola petición.
- [ ] Probabilidad fuera de la banda → el código actúa sin hoja; dentro de la banda → una hoja `judge` nueva sin turnos del constructor; aún incierto → run `gated` con motivo que incluye pregunta, probabilidades y respuesta del juez, reanudable tras `approve`.
- [ ] Repositorio fuera de `external_judgment_allowed`, clave ausente, o servidor que responde `429`/`529` → ninguna llamada exitosa al árbitro, `arbiter: unavailable` en el registro, y el run continúa por `judge`; ninguna clave aparece en ficheros, registro ni `summary.json`.
- [ ] `summary.json` publica tokens y llamadas de Jev separados del gasto del modelo generativo, y el hash de `policy.json` y de cada `questions/*.json`.
- [ ] Un `pass` de review en `c2` nunca procede del constructor: exige carril rápido sin blocker **y** `review.findings_block` bajo el umbral, o la cascada.

## Frontier
Bloqueado por TDR-01. Independiente de TDR-02: `c2a` corre sobre `c1a`; `c2b` requiere además TDR-02 y se
prueba cuando ambos estén integrados. La prueba de humo en vivo contra Jev y la autorización del gasto
no son de este ticket: TDR-05.

## Step-by-Step Implementation Plan
1. `arbiter.py`: cliente `urllib` con reintentos acotados (`429`/`529`), tiempo máximo, sin dependencias nuevas; `questions/*.json` con id, tipo, instrucciones y criterios de la tabla de la spec; `policy.json` añade `arbiter: {enabled, model, thresholds, uncertainty_band, external_judgment_allowed}`.
2. `state.py`: constructores de estado por pregunta (prosa de review + resumen de diff; criterios + diff; argv + salida acotada; afirmación + extracto de recibo; salida de fallo + hallazgo).
3. `cascade.py`: árbitro → `judge` (prompt `prompts/judge.md`, una vez por pregunta) → gate; `escalations.jsonl` y `judgments.jsonl` append-only; `approve <run_id> --actor --reason` para reanudar.
4. Integración en el bucle de calidad de `c1a`/`c1b` en los cinco puntos; gasto de Jev en `summary.json`.
5. `tests/`: servidor HTTP falso en hilo con guiones (seguro, incierto, `429`, `529`), y los cinco criterios.

## Testing Plan
- Unitarias: construcción de estado y agrupación de preguntas; umbrales y banda; redacción de la clave en todo lo persistido; reintentos acotados.
- Integración con hojas y servidor falsos: `integrated` sin cascada; `judge` invocado una vez; `gated` y reanudado con `approve`; `arbiter: unavailable` por lista, clave y errores.
- En vivo: ninguna aquí; humo con `usage` en TDR-05 con autorización explícita.

## Out of Scope
- `risk.semantic_change` y review dirigida: TDR-04.
- Calibración de umbrales o fine-tuning: solo se registran los datos.
- Laya u otro proveedor de juicios; OpenRouter (no verificado).

```
