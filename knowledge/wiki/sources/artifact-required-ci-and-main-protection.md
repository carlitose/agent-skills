---
type: source
title: "CI obligatoria en PRs y protección de `main`"
identity_key: artifact:required-ci-and-main-protection
identity_strength: stable
source_path: docs/specs/required-ci-and-main-protection.md
source_digest: sha256:bbe972abaad41a4c6f2ced148a5c54b697767e940716e8c437d4b6ab754eba6d
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-09-19
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# CI obligatoria en PRs y protección de `main`

Compiled from `docs/specs/required-ci-and-main-protection.md`. Identity is `artifact:required-ci-and-main-protection`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-19** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"decisions":{"headings":[],"status":"not-identified"},"exclusions":{"headings":[],"status":"not-identified"},"goals":{"headings":[],"status":"not-identified"},"invariants":{"headings":[],"status":"not-identified"},"verification":{"headings":[],"status":"not-identified"}},"parts":[{"index":0,"path":"wiki/sources/artifact-required-ci-and-main-protection.md","payload_bytes":6374,"payload_sha256":"bbe972abaad41a4c6f2ced148a5c54b697767e940716e8c437d4b6ab754eba6d"}],"payload_bytes":6374,"payload_sha256":"bbe972abaad41a4c6f2ced148a5c54b697767e940716e8c437d4b6ab754eba6d","schema":1,"source_digest":"sha256:bbe972abaad41a4c6f2ced148a5c54b697767e940716e8c437d4b6ab754eba6d","source_identity":"artifact:required-ci-and-main-protection","source_kind":"spec"} -->

| Topic | Source sections |
|---|---|
| goals | no matching section identified in the source; complete source retained |
| exclusions | no matching section identified in the source; complete source retained |
| decisions | no matching section identified in the source; complete source retained |
| invariants | no matching section identified in the source; complete source retained |
| verification | no matching section identified in the source; complete source retained |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":6374,"payload_sha256":"bbe972abaad41a4c6f2ced148a5c54b697767e940716e8c437d4b6ab754eba6d","schema":1,"source_digest":"sha256:bbe972abaad41a4c6f2ced148a5c54b697767e940716e8c437d4b6ab754eba6d","source_identity":"artifact:required-ci-and-main-protection"} -->
```markdown
# CI obligatoria en PRs y protección de `main`

## Artifact Graph
- Artifact ID: `artifact:required-ci-and-main-protection`
- Role: `spec`
- Standalone: true

## Type and status
Decision. El repositorio `carlitose/agent-skills` es público y con Actions habilitado, de modo que
las reglas de rama están disponibles sin coste. Hoy no existe ningún workflow ni protección: todo
lo fusionado hasta `afbb259` se validó solo en máquinas locales.

## Objetivo y comportamiento actual
Actualmente cualquier PR puede fusionarse sin que nadie haya ejecutado las suites, y `main` acepta
push directo y force-push. La única barrera real es el runner de Ticket Autopilot, que consulta
checks y políticas del proveedor antes de fusionar; si no hay checks, no hay nada que consultar.

El objetivo es que el proveedor exija evidencia ejecutada antes de integrar, y que esa evidencia
sea exactamente la que ya define el
[contrato de perfiles de verificación local](local-verification-profile-contract.md): `quick` como
gate por defecto y `full` obligatorio en PRs que tocan `ticket-autopilot/scripts/` o
`scripts/test-local*`. Este spec no redefine los perfiles ni su selección.

## Decisión 1: plataforma de CI
CI se ejecuta **solo en Linux** (`ubuntu-latest`). Windows y macOS quedan fuera de la verificación
obligatoria y siguen siendo verificación local cuando corresponda.

Motivo registrado: en el host Windows disponible, el perfil `full` falló 3 de 4 intentos con
`sh.exe: fatal error - add_item (...) errno 1` de Git para Windows bajo concurrencia, y su reloj
ronda los 25-40 minutos. No hay datos de fiabilidad en runners limpios de GitHub. Esta decisión es
una elección explícita de alcance, no una afirmación de que Windows esté verificado.

Consecuencia declarada: **un PR aprobado por CI no demuestra comportamiento en Windows ni en
macOS.** Cualquier cambio sensible a la plataforma sigue requiriendo evidencia local, declarada con
su alcance.

## Decisión 2: qué ejecuta CI
Un workflow disparado por `pull_request` contra `main` y por `push` a `main`, con:

1. Un job de toolchain que fija Node y Python compatibles con el arnés (Node ≥ 22.6 por la orden
   nativa de TypeScript; Python 3.12 según `.python-version`) y verifica que Git existe.
2. Un check llamado `local-profile` que decide su perfil a partir de los archivos cambiados: `full`
   si el PR toca `ticket-autopilot/scripts/**` o `scripts/test-local*`, y `quick` en el resto.
   El nombre del check es estable e independiente del perfil elegido, para que pueda exigirse sin
   que el filtrado de rutas deje el check en estado pendiente indefinido.
3. Publicación del informe JSON del arnés y de los logs crudos como artefactos del workflow, con la
   misma semántica de conteo que ya usa el informe local.

El workflow no relaja aserciones, no reintenta checks fallidos y no oculta omisiones: la matriz
forward sigue siendo un comando explícito de release, fuera de ambos perfiles.

## Decisión 3: protección de `main`
Una regla sobre `main` que exige:

- PR obligatorio: prohibido el push directo.
- El check `local-profile` en verde antes de integrar.
- Prohibido el force-push y el borrado de la rama.

Y que **no** exige:

- Aprobaciones humanas (0 revisores). Exigirlas rompería la entrega autónoma del runner, que
  fusiona sin revisor por diseño y con su propia autoridad registrada.
- Historial lineal, porque el runner integra mediante merge commits y su prueba terminal se apoya
  en ellos.

La regla se aplica también a administradores; de lo contrario no protege nada frente al propio
flujo autónomo, que es justo el que más se usa aquí.

## Invariantes semánticas
1. La selección de perfiles y sus aserciones son las del contrato de perfiles; CI las ejecuta, no
   las redefine.
2. El nombre del check requerido es estable aunque cambie el perfil interno.
3. Un check ausente, pendiente o fallido bloquea la integración: nunca se interpreta como éxito.
4. La entrega autónoma del runner sigue siendo posible sin revisor humano y sin bypass de checks.
5. CI no adquiere autoridad de merge, de publicación ni de cambio de alcance: sigue siendo el
   proveedor quien bloquea y el runner quien decide con su autorización existente.
6. Ni el workflow ni la regla modifican historia ya integrada.

## Contratos externos
- **GitHub Actions**: workflow declarativo en `.github/workflows/`. Se fija la versión de las
  acciones usadas; los runners son efímeros y no comparten estado con las máquinas locales.
- **GitHub Rules/Branch protection**: se configura vía API sobre `main`. Requiere autorización
  explícita del titular del repositorio; no se aplica por inferencia desde este spec.
- **Ticket Autopilot**: su camino crítico de merge ya lee checks y políticas vivas y gatea ante
  resultados pendientes, fallidos o inciertos. No requiere cambios para respetar el nuevo check.

## Modos de fallo previstos
- El arnés asume `python3`/`python` en PATH: si el runner de CI no lo expone, el toolchain debe
  fallar visiblemente en vez de saltarse checks.
- El reloj de `full` en un runner hospedado es desconocido; si supera el límite del job, el check
  falla y eso debe verse como dato real, no como flake a reintentar.
- Una regla mal configurada puede bloquear la entrega autónoma; por eso aprobaciones y historial
  lineal quedan explícitamente fuera.

## Estrategia de verificación
- Validar el workflow en un PR real: comprobar que elige `quick` en un cambio docs-only y `full` en
  uno que toca `scripts/test-local*`.
- Comprobar que el check aparece con nombre estable en la API de checks del PR.
- Medir y registrar el reloj real de ambos perfiles en CI; no se declara ningún presupuesto de CI
  sin medición.
- Comprobar, tras aplicar la regla, que un PR sin checks en verde no puede integrarse y que la
  entrega autónoma del runner sí puede integrarse cuando están en verde.
- Límite explícito: ninguna de estas comprobaciones demuestra comportamiento en Windows o macOS.

## Alternativas y exclusiones
Se descarta exigir el `full` de Windows mientras no haya datos de fiabilidad en runners limpios, y
se descarta ejecutar la matriz forward en cada PR por su coste. Quedan fuera: caché de
dependencias, publicación de releases, firma de commits, entornos de despliegue, cobertura y
cualquier cambio a la selección de tests.

```
