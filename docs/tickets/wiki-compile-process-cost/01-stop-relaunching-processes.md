---
ticket_schema: 1
ticket_id: "WCP-01"
execution_mode: AFK
blocked_by: []
---

# WCP-01 — Dejar de relanzar procesos para preguntas ya respondidas

## Artifact Graph
- Artifact ID: `ticket:wiki-compile-process-cost:01`
- Role: `ticket`
- Parent: [wiki-compile-process-cost.md](../../specs/wiki-compile-process-cost.md)

## Parent Spec
[wiki-compile-process-cost.md](../../specs/wiki-compile-process-cost.md)

## What to Build
En `date_provenance.py`, recordar por estado del repositorio la respuesta de `rev-parse` y el
conjunto de ficheros versionados, leyendo ese estado del sistema de ficheros (`.git` y su
índice). En `ingest_docs.py`, resolver los tickets de un árbol con un solo `ticket-list --json`
del CLI canónico, recordado con una huella barata del árbol, y dejar `ticket-parse` como camino
para lo que el inventario no nombre. Cubre los diez criterios de la spec.

## Acceptance Criteria
- [ ] Cinco artefactos del mismo repositorio cuestan un `rev-parse` y un `ls-files`.
- [ ] Un `commit` entre dos llamadas se ve en la segunda.
- [ ] Un directorio que se convierte en repositorio se ve.
- [ ] Dos repositorios distintos no comparten respuesta.
- [ ] Un árbol de tickets cuesta un solo proceso, y es `ticket-list`.
- [ ] Los bloqueos del ticket sobreviven al inventario.
- [ ] Un ticket editado o añadido nunca se responde con la lectura anterior.
- [ ] Un ticket malformado falla con el mensaje del analizador canónico.
- [ ] Un ticket fuera de la disposición habitual se sigue analizando.
- [ ] La suite completa de `llm-wiki` pasa, incluida la prueba de independencia.

## Frontier
Ready. Skills-only inline sobre `d4d69e07…`.

## Step-by-Step Implementation Plan
1. Medir por fases y atribuir el coste a procesos antes de tocar nada.
2. Escribir las pruebas de coste y de invalidación.
3. Recordar las respuestas del repositorio; inventariar el árbol de tickets en un proceso.
4. Volver a medir sobre la misma copia y ejecutar la suite completa.
5. Handoff con límites; entrega aparte con autoridad y readback frescos.

## Testing Plan
Suite completa de `llm-wiki` más una nueva de coste. La medición usa una copia desechable de una
wiki real; no se publica nada ni se toca el repositorio del proyecto.

## Out of Scope
Sync incremental con caché persistente, agrupar `git log --follow`, y el resto del coste del
lint.
