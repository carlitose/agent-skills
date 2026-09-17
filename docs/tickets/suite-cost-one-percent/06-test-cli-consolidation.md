---
ticket_schema: 1
ticket_id: "06"
execution_mode: AFK
blocked_by:
  - "03"
  - "04"
---

# Implementar el gate rápido sin recortar la cobertura de `full`

## Artifact Graph
- Artifact ID: `artifact:suite-one-percent-test-cli-consolidation`
- Role: `ticket`
- Parent: [local-verification-profile-contract.md](../../specs/local-verification-profile-contract.md)

## Parent Spec
[local-verification-profile-contract.md](../../specs/local-verification-profile-contract.md)

## What to Build
Aplicar las cuatro decisiones confirmadas del contrato: ampliar el `quick` existente con todo
`test_kernel` y exactamente los diez métodos de `test_cli.CliTests` enumerados allí. Mantener
la entrada cotidiana `npm test` y el comando explícito `full`.

Este slice sustituye por completo la antigua consolidación de `test_cli`. Conserva ID, ruta,
Artifact ID y dependencias para no romper sus referencias. No borra, fusiona, mueve ni
reescribe tests de producto. El resultado es una selección explícita y comprobable del
harness, documentada y medida de extremo a extremo.

## Acceptance Criteria
- [ ] `quick` conserva cada suite/caso que seleccionaba antes, añade todo `test_kernel` y
      exactamente los diez e2e del spec; no ejecuta dos veces un caso ni usa coincidencias
      parciales para resolver los diez identificadores. Un identificador ausente falla de
      forma visible, sin omisión silenciosa.
- [ ] `full` conserva todos los identificadores y aserciones existentes, incluidos los casos
      fuera del gate y los candidatos de la matriz del 03. La forward matrix sigue excluida
      de ambos perfiles y disponible como comando de release. No se encadena un segundo
      `quick` dentro de `full`.
- [ ] Tests del harness cubren la selección exacta, ausencia de duplicados, fallo por nombre
      ausente, preservación de `full` y reporting honesto de lo no ejecutado. La selección
      conserva la ejecución/distribución ya existente, sin ampliar el planificador.
- [ ] El gate pasa con `--jobs 8` y mide **≤150 s de reloj** desde inicio a cierre del proceso,
      incluyendo descubrimiento/preparación. Se registran comando, entorno, resultado,
      reloj y check-time por separado. Las estimaciones previas no cuentan como evidencia.
- [ ] `full` pasa con `--jobs 8`, sin recortar cobertura, relajar aserciones ni ocultar fallos
      mediante skips/reintentos. Se compara el inventario antes/después, no solo el total de
      shards, que puede variar por el histórico de duraciones.
- [ ] README documenta el nuevo `quick`, los diez e2e o su referencia exacta, y cuándo es
      obligatorio `full` (PRs de runner/harness y release); docs-only usa el gate rápido.
- [ ] Windows/PowerShell, macOS y Unix/Linux conservan comandos y selección portables. Se
      registran las plataformas realmente verificadas y las no disponibles, sin afirmar una
      matriz multiplataforma que no se haya ejecutado.

## Frontier
Las dependencias canónicas siguen siendo 03 y 04. La investigación está disponible y la
confirmación humana está registrada, pero `ticket-list` aún muestra sus ciclos de vida como
`unknown`. El runner debe resolver esa frontera antes de mutar el candidato; un checkbox no
es integración ni una autorización de merge.

El usuario ha pedido continuar este ticket hasta `done`. Es autoridad para trabajar, no para
inventar evidencia, saltar un gate o autorizar una integración que exija una decisión distinta.

## Step-by-Step Implementation Plan
1. Obtener el envelope normalizado y CandidateRef/scope del runner. Guardar el inventario
   actual de `quick`/`full` y comprobar que los diez IDs existen. Checkpoint: selección base
   e identidad del candidato conocidas.
2. Añadir pruebas del contrato de selección al harness; implementar la ampliación mínima
   de `quick`, reutilizando descubrimiento, chunks y captura existentes. Checkpoint: tests del
   harness en verde; inventario de `full` intacto.
3. Actualizar README; revisar y simplificar únicamente el diff del ticket. Checkpoint: no
   cambia código del runner ni tests/fixtures de producto.
4. Medir el gate con `--jobs 8` y luego ejecutar `full` desacoplados, sin solaparlos. Registrar
   logs y JSON, reloj, check-time y límites de plataforma; pasar review/QA/verificación sobre
   el candidato exacto antes de que el runner finalice.

Si el gate supera 150 s, registrar el resultado real y mantener el criterio abierto. No
reducir por cuenta propia los diez IDs, omitir kernel ni redefinir reloj como check-time.

## Testing Plan
- Unitario: `node --test scripts/test-local.test.mjs` y las demás pruebas del harness que
  resulten afectadas.
- Inventario: comparar descubrimiento completo antes/después y la unión exacta de `quick`
  anterior, kernel y diez IDs. Un listado no acredita ejecución.
- Integración local: `node scripts/test-local.mjs quick --jobs 8 --report <gate.json>`;
  medir también reloj externo del proceso. Sin carga artificial concurrente.
- Regresión completa: `node scripts/test-local.mjs full --jobs 8 --report <full.json>`.
  No es release de workflows: no repetir la forward matrix como parte de este slice.
- Manual: revisar README y referencias recíprocas. Registrar explícitamente POSIX/macOS
  no ejecutados si no hay entorno disponible.

## Out of Scope
- Borrar, fusionar, migrar o reescribir `test_cli`/`test_kernel` o sus aserciones/fixtures.
- Cambiar `git_ops`, snapshots semánticos, barreras de identidad o `command_capture`.
- Añadir shards, reintentos, timeouts adaptativos, otro planificador o dependencias externas.
- Resolver el flake ya investigado mediante exclusiones nuevas de `full`.
- Prometer ahorro adicional de `full`, equivalencia por líneas o cierre canónico sin evidencia.
