---
ticket_schema: 1
ticket_id: "01"
execution_mode: AFK
blocked_by: []
---

# Corregir los fixtures Linux y verificar ambos hosts

## Artifact Graph
- Artifact ID: `artifact:linux-suite-fixture-portability:01`
- Role: `ticket`
- Parent: [linux-suite-fixture-portability.md](../../specs/linux-suite-fixture-portability.md)

## Parent Spec
[linux-suite-fixture-portability.md](../../specs/linux-suite-fixture-portability.md)

## What to Build
Corregir las cinco causas de fixtures demostradas en el spec, que explican los diez checks
Linux preexistentes. Hacer explícitos los bytes de goldens, el intérprete de filtros Git,
los modos del filesystem anfitrión y la observación exacta de reaping mediante pidfd.

## Acceptance Criteria
- [ ] Los diez checks originales pasan sin editar el wrapper forward ni los hashes golden.
- [ ] LF y CRLF son deterministas; los filtros usan el intérprete actual con quoting seguro.
- [ ] El spy POSIX aplica el modo real y la rama Windows sigue sin llamar a fchmod.
- [ ] El índice y el archivo ejecutable coinciden sin desactivar filemode.
- [ ] El predicado pidfd rechaza vivo/zombie y acepta ESRCH tras wait; no consume wait status.
- [ ] Timeout, cancelación, límite de salida, control vivo, plazos y cleanup se conservan.
- [ ] Los módulos afectados y full --jobs 8 pasan en Linux y Windows sobre el candidato final.
- [ ] Review, QA y verificación registran límites, incluidos macOS no observado y ausencia
  de aislamiento independiente. No se modifica runtime ni se inventa autoridad de entrega.

## Frontier
Ready: alcance y predicado ESRCH confirmados por el usuario. AFK, sin dependencias internas.
La implementación local está autorizada; publicación/merge de este prerrequisito no se
infieren de la autorización del lote principal. Máximo 20 ciclos de calidad.

## Step-by-Step Implementation Plan
1. Preservar el RED registrado y vincular el candidato a la base corregida de revisión.
2. Cambiar exclusivamente los cinco archivos de tests listados en el spec; añadir controles
   negativos y de bytes/modos sin retirar escenarios. Checkpoint: checks focales GREEN.
3. Ejecutar módulos afectados y full en ambos hosts sin bloquear el foreground. Checkpoint:
   recibos completos de cada ejecución y mismo contenido candidato.
4. Congelar, simplificar, revisar, planificar/ejecutar QA y auditar con los contratos canónicos.
   Checkpoint: handoff validado o gates exactos pendientes, nunca un done manual.

## Testing Plan
- Linux nativo WSL: repetir los diez checks de linux-failure-signature-comparison.json;
  ejecutar los cinco módulos afectados y el wrapper forward sin patches diagnósticos.
- Windows nativo: ejecutar esos módulos con sus guardas de plataforma existentes.
- Control pidfd: hijo vivo, salida sin wait, ESRCH después de wait; preservar status propio.
- Ambos hosts: node scripts/test-local.mjs full --jobs 8 con logs y exit code.
- Mantener el límite explícito de macOS no ejecutado. Simulación de ramas no es host nativo.

## Out of Scope
- Runtime, goldens nuevos, eliminación de casos, skips nuevos, retries encubridores o deadlines mayores.
- Instalaciones globales, cambios de configuración global Git y ajustes del contrato de perfiles.
- Publicación, integración, resolución de dependencias o done del lote principal sin sus gates.
