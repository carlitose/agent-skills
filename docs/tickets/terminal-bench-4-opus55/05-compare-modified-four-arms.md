---
ticket_schema: 1
ticket_id: "TBF-05"
execution_mode: HITL
blocked_by:
  - "TBF-03"
---

# TBF-05 — Comparar cuatro brazos en un harness local modificado

## Artifact Graph
- Artifact ID: `ticket:terminal-bench-4-opus55:05`
- Role: `ticket`
- Parent: [terminal-bench-4-opus55.md](../../specs/terminal-bench-4-opus55.md)

## Parent Spec
[terminal-bench-4-opus55.md](../../specs/terminal-bench-4-opus55.md)

## What to Build
Tras el piloto estándar y una nueva autorización de lote, comparar Pi bare, Pi skills-only y variantes adaptadas c1a/c3a sobre los tres tasks congelados con el mismo overlay Git. `openai-codex/gpt-6-sol` y el verificador separado de Harbor permanecen fijados. Esta comparación es un experimento **local modificado**, no un score Terminal-Bench estándar ni una reproducción del ticket-driver original si las fases o tests cambian.

## Acceptance Criteria
- [ ] Un mandato nuevo fija tareas, cuatro variantes, número de starts, coste máximo y diferencias metodológicas; no reutiliza los tres starts del piloto estándar ni el viejo lote de doce celdas.
- [ ] El overlay, tool boundary, credenciales y límites son iguales cuando se afirma paridad; los cambios inevitables quedan nombrados antes de ejecutar.
- [ ] Las fases driver/QA se observan en el sandbox sin tests ocultos, suites inventadas declaradas funcionales o resultados tempranos del verifier; una fase imposible sigue como gate.
- [ ] Cada start y gasto se reconcilia con recibos propios; incertidumbre detiene el lote sin retry automático.
- [ ] El informe separa estos resultados del método Harbor original y no publica puntuaciones en un leaderboard.

## Frontier
Bloqueado por TBF-03, por contrato técnico c1a/c3a y por una autorización de lote futura. El usuario aprobó preparar el overlay común, no convertir pruebas offline en un resultado pagado ni transferir presupuesto entre métodos.

## Step-by-Step Implementation Plan
1. Elegir y validar el contrato de fases/test local sin revelar el verificador separado.
2. Revalidar las imágenes Git derivadas y la identidad de los cuatro brazos con GPT-6 Sol.
3. Obtener autorización exacta, reservar gasto y ejecutar únicamente starts cubiertos.
4. Reducir y etiquetar los resultados como harness local modificado.

## Testing Plan
Pruebas offline del sandbox y política de coste; pruebas live solo dentro del nuevo lote autorizado, sin asumir equivalencia con el piloto estándar.

## Out of Scope
- Reetiquetar el piloto estándar, leer tests/soluciones ocultas o publicar en leaderboard.
