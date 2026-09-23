---
ticket_schema: 1
ticket_id: "TDR-05"
execution_mode: HITL
blocked_by:
  - "TDR-02"
  - "TDR-04"
---

# TDR-05 — Lote de benchmark por candidato y decisión del camino

## Artifact Graph
- Artifact ID: `ticket:ticket-driver:05`
- Role: `ticket`
- Parent: [ticket-driver.md](../../specs/ticket-driver.md)

## Parent Spec
[ticket-driver.md](../../specs/ticket-driver.md)

## What to Build
Con autorización explícita del usuario por lote: prueba de humo contra Jev (una pregunta, `usage`
registrado, gasto comprobado en la cuenta) antes del primer run de `c2`+; después, ≥ 3 runs por
candidato `c1a`, `c1b`, `c2a`, `c2b`, `c3a`, `c3b`, `c4` con el harness privado (`start driver
<candidato>-r<n>`), en serie, con `collect` desde la sesión y `annotate` de LOC sin pruebas y
cobertura para los brazos ya grabados. Informe con mediana y rango de tiempo, coste, turnos,
latentes/5, feature, regresiones, LOC sin pruebas, cobertura, quota de protocolo, escaladas y gasto de
Jev, frente a `c0` (skills-only) y a los runs q1–q4 del runner. El usuario elige el camino; la elección
y sus consecuencias (destino de `ticket-autopilot`, siguiente spec) se escriben en la spec. Secciones de
la spec: Contrato con el benchmark, Candidatos, Decisiones humanas pendientes, S5.

## Acceptance Criteria
- [ ] Existe una autorización durable del usuario por cada lote, con candidatos y número de runs, antes de ejecutar nada en vivo; un `429` en el primer turno se registra como muestra nula y no cuenta.
- [ ] La prueba de humo a Jev queda registrada con `usage` y coste observado antes del primer run de `c2`+.
- [ ] Cada candidato tiene ≥ 3 runs válidos; el informe da mediana y rango por métrica, separa el gasto de Jev, y nombra cada run con su sesión y su `summary.json`.
- [ ] La decisión del usuario está escrita en `docs/specs/ticket-driver.md` (Status y sección de decisión) con la evidencia enlazada; si ningún candidato convence, se escribe eso.
- [ ] Ningún merge, publicación ni retirada de `ticket-autopilot` se ejecuta en este ticket: solo se decide y se abre la siguiente spec.

## Frontier
Bloqueado por TDR-02 y TDR-04 (y por tanto TDR-01 y TDR-03). Decisiones humanas exactas: autorización de
gasto en Jev; autorización de cada lote (candidatos, runs); lista `external_judgment_allowed`; la
elección final del camino.

## Step-by-Step Implementation Plan
1. Pedir y guardar la autorización del lote (`prof/…/tdr-authorization.md`, mismo patrón que `q4-authorization.md`).
2. Humo Jev: una pregunta real desde `arbiter.py`, `usage` al registro, comprobación del saldo.
3. Runs en serie con el brazo `driver`; `collect` tras cada uno; `annotate` de LOC y cobertura para q1–q4, bare y skills-only.
4. `compare` extendido a los candidatos; informe en `prof/…/tdr-report-q1.md`.
5. Sesión de decisión con el usuario; actualizar Status y decisión en la spec; abrir la spec siguiente.

## Testing Plan
- Manual: lectura del informe por el usuario.
- Los runs en vivo son la medida; no hay pruebas automáticas nuevas en este ticket.
- Límite declarado: n ≥ 3 por brazo distingue diferencias de 2× o más, no del 20 %.

## Out of Scope
- Implementar el camino elegido.
- Retirar o modificar `ticket-autopilot`.
- Benchmark público (PBE), Laya, fine-tuning.
