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
- [ ] El dataset queda fijado por una referencia versionada comprobada en el registro, con manifiesto/hash y número de tareas; ningún `latest` ni supuesto `@4.0.0` sin readback.
- [ ] Tres tareas piloto quedan nombradas antes de la primera llamada al modelo; se identifica cuáles exigen GPU y cómo se cuentan las no ejecutables.
- [ ] Docker responde con servidor Linux real y Harbor se resuelve en un entorno de benchmark aislado; los errores quedan como gates, no como éxitos supuestos.
- [ ] El ID del modelo se contrasta con la documentación oficial y se comprueba su acceso para la cuenta sin revelar secretos ni gastar en generación inadvertidamente.
- [ ] Se conserva un preflight que fija modelo, proveedor, razonamiento, límites, texto de tarea, ref de dataset, cuatro brazos y política de presupuesto/reintentos; ninguna run live se ha iniciado.

## Frontier
Ready para preparación técnica; una credencial ausente, el daemon apagado o un ref no verificable detiene el ticket en el gate correspondiente. La selección humana de Docker local ya está registrada. El piloto tiene autoridad propia separada.

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
