---
ticket_schema: 1
ticket_id: "PBE-01"
execution_mode: HITL
blocked_by: []
---

# PBE-01 — Importe autorizado y decisión sobre el demonio de Docker

## Artifact Graph
- Artifact ID: `ticket:public-benchmark-evaluation:01`
- Role: `ticket`
- Parent: [public-benchmark-evaluation-wayfinder.md](../../specs/public-benchmark-evaluation-wayfinder.md)

## Parent Spec
[public-benchmark-evaluation-wayfinder.md](../../specs/public-benchmark-evaluation-wayfinder.md)

## What to Build
Nada de código. Dos decisiones del usuario, confirmadas explícitamente, antes de que exista
gasto: el **importe máximo** autorizado para la medida, y si se levanta el **demonio de Docker**
en esta máquina o se usa un sandbox remoto de pago.

Requiere [grilling](../../../grilling/SKILL.md) sobre la decisión antes de confirmarla: la
proyección de coste viene de una sola tarea sembrada y puede quedarse corta.

## Acceptance Criteria
- [ ] Hay un importe máximo escrito, no un «adelante».
- [ ] Está decidido si se levanta Docker en local o se paga un sandbox remoto.
- [ ] Está decidido qué brazos se miden: los tres o solo dos.
- [ ] La decisión queda registrada donde el siguiente agente la lea.

## Frontier
Bloqueante. Es una decisión humana; ningún agente la toma por inferencia.

## Step-by-Step Implementation Plan
1. Presentar la proyección de coste con su origen y su incertidumbre.
2. Grilling sobre los supuestos: tareas más largas, reintentos, tareas con GPU.
3. Registrar importe, runtime y brazos elegidos.

## Verification
- La decisión registrada, con fecha y alcance.
