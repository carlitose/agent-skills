---
ticket_schema: 1
ticket_id: "TBF-01"
execution_mode: AFK
blocked_by: []
---

# TBF-01 — Congelar dataset, modelo y runtime local

## Artifact Graph
- Artifact ID: `ticket:terminal-bench-4-opus55:01`
- Role: `ticket`
- Parent: [terminal-bench-4-opus55.md](../../specs/terminal-bench-4-opus55.md)

## Parent Spec
[terminal-bench-4-opus55.md](../../specs/terminal-bench-4-opus55.md)

## What to Build
Preparar un manifiesto reproducible de Terminal-Bench 4.0 sin lanzar ningún agente: resolver el ref exacto del registro Harbor y los nombres/hash de las tareas; elegir tres tareas sin GPU para el piloto; comprobar el motor Docker local y la disponibilidad de `claude-opus-5-5` para la cuenta sin generar un completion. Mantener el entorno de Harbor aislado de instalaciones Pi ajenas. Registrar la configuración idéntica prevista para los cuatro brazos y el límite de $250 del piloto / $1.000 acumulado.

## Acceptance Criteria
- [x] El dataset queda fijado por una referencia versionada comprobada en el registro, con manifiesto/hash y número de tareas; ningún `latest` ni supuesto `@4.0.0` sin readback.
- [x] Tres tareas piloto quedan nombradas antes de la primera llamada al modelo; se identifica cuáles exigen GPU y cómo se cuentan las no ejecutables.
- [x] Docker responde con servidor Linux real y Harbor se resuelve en un entorno de benchmark aislado; los errores quedan como gates, no como éxitos supuestos.
- [x] El ID del modelo se contrasta con la documentación oficial y se comprueba su acceso para la cuenta sin revelar secretos ni gastar en generación inadvertidamente.
- [x] Se conserva un preflight que fija modelo, proveedor, razonamiento, límites, texto de tarea, ref de dataset, cuatro brazos y política de presupuesto/reintentos; ninguna run live se ha iniciado.

## Frontier
**Completado** e integrado por PR #346 (head `d062df2caaeec9da0c55f941ae69c867857908ba`, merge `ec0ee12dc99930cf1d0249a2a89a980e72e60e77`, ocho checks CI verdes): [manifest](../../../benchmarks/terminal-bench-4-opus55/manifest.json) con dataset `sha256:39d9f44b…`, 66 tasks, tres tareas piloto y tres exclusiones GPU; [preflight](../../../benchmarks/terminal-bench-4-opus55/preflight.md) sin run live. La comprobación de modelo Opus es histórica: el modelo se cambió luego a `openai-codex/gpt-6-sol` (ver spec) y esta evidencia no se reetiqueta. Movido a `done/` en ejecución skills-only, sin recibo de runner.

## Step-by-Step Implementation Plan
1. Crear entorno aislado, verificar versionado de Harbor y disponibilidad del motor Docker con resultados observados.
2. Resolver dataset 4.0 desde Harbor Hub y congelar tareas y restricciones GPU.
3. Comprobar el identificador/permiso del modelo mediante endpoint de modelos si está disponible, sin solicitud generativa.
4. Escribir y revisar manifiesto y preflight antes de pasar al adaptador.

## Testing Plan
Pruebas offline de lectura y consistencia del manifiesto; smoke no pagado de Docker/Harbor y endpoint del modelo si existe. No ejecutar tareas de evaluación ni suponer coste nulo ante resultado ambiguo.

## Out of Scope
- Implementar adaptador o ejecutar el benchmark.
- Renovar autorizaciones, instalar o actualizar Pi, ni publicar a terceros.
