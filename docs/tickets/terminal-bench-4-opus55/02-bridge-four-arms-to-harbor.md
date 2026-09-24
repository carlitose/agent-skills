---
ticket_schema: 1
ticket_id: "TBF-02"
execution_mode: AFK
blocked_by:
  - "TBF-01"
---

# TBF-02 — Conectar cuatro brazos de Pi al sandbox Harbor

## Artifact Graph
- Artifact ID: `ticket:terminal-bench-4-opus55:02`
- Role: `ticket`
- Parent: [terminal-bench-4-opus55.md](../../specs/terminal-bench-4-opus55.md)

## Parent Spec
[terminal-bench-4-opus55.md](../../specs/terminal-bench-4-opus55.md)

## What to Build
Revalidar el cambio de modelo de la spec a `openai-codex/gpt-6-sol` para los cuatro brazos sin reetiquetar la observación histórica de Opus en TBF-01. Implementar un adaptador `BaseAgent` de Harbor para Pi externo y configurar cuatro variantes de andamiaje: bare, skills-only, ticket-driver c1a y c3a. Pi debe ver exactamente la tarea aprobada y ejercer herramientas exclusivamente mediante `environment.exec` dentro del contenedor. Para c1a/c3a, probar una transformación fiel del encargo al contrato ticket/Git sin modificar el verificador del benchmark. Recopilar trayectorias, identidades de intento y usage de modelo; aislar secretos del contenedor y de las hojas.

## Acceptance Criteria
- [ ] La clase del adaptador se carga mediante la ruta de importación admitida por Harbor y un test offline verifica `setup`/`run` contra un entorno simulado.
- [ ] Una prueba de frontera demuestra que shell y ficheros escritos por Pi afectan solo al sandbox, nunca al checkout anfitrión, para los cuatro brazos.
- [ ] Los cuatro brazos mantienen idénticos modelo `openai-codex/gpt-6-sol`, razonamiento `high`, task text y límites; un readback de catálogo/OAuth sin completion respalda el cambio y cada diferencia de andamiaje queda visible.
- [ ] c1a/c3a aceptan tareas representativas sin inventar entradas/salidas o alterar el éxito del verificador; si no existe puente fiel, el resultado es un gate explícito antes del piloto.
- [ ] Las claves del proveedor y del judge no llegan a las hojas ni a los contenedores; un test cubre la herencia real del entorno hijo antes de una solicitud live. Un `.env` externo puede alimentar solamente el proceso host autorizado, sin incluir su valor en repo, logs o argumentos.
- [ ] El registro por intento conserva resultado, coste/tokens atribuibles, tiempo, fallos y presupuesto acumulado; un resultado ambiguo bloquea retry y otro gasto.

## Frontier
Depende de TBF-01 para el dataset y sus tareas fijas; su comprobación Opus no valida el nuevo modelo. La lectura del catálogo Pi muestra GPT-6 Sol y OAuth `ready`, pero la generación, el coste real y el aislamiento de todos los brazos siguen como gates. El usuario confirmó el permiso de usar Jev para los contenidos/diffs Terminal-Bench de este piloto; el archivo externo se pudo aislar del entorno de un proceso hijo sin llamar a la API. Eso no prueba validez de la credencial, precio ni una ruta c3a: la allowlist actual niega un repositorio Terminal-Bench. Para el task versionado `html-js-filter`, los hashes de metadatos e instrucción públicos coinciden con el manifiesto, y el verificador está en un entorno separado; el driver requiere Git y una suite local distinta, con timeout de hoja menor. El usuario reafirmó **los cuatro brazos**, no autorizó reducir a dos. Mantener el gate técnico antes del piloto; no sustituir el verificador oculto, fabricar un repo/test ni contar un brazo bloqueado como ejecución. Ninguna llamada live ni smoke pagado fuera de los doce intentos del lote piloto.

## Step-by-Step Implementation Plan
1. Revalidar el modelo GPT, proveedor, razonamiento y tarifa estimada sin completion; leer las referencias actuales de Pi y Harbor antes de implementar el contrato de herramientas externas.
2. Implementar adaptador y variantes; dejar que Harbor sea dueño del ambiente y que el modelo no acceda a herramientas host directas.
3. Demostrar frontera y paridad en tests con dobles no pagados; registrar límites si una tarea no es convertible a ticket.
4. Validar persistencia de trayectorias, usage y presupuesto antes del primer intento autorizado.

## Testing Plan
Tests de integración local sin modelo para carga, tool bridging, scopes de credenciales, manifiesto de intentos y budget fail-closed. Una prueba real de tarea consumiría uno de los doce intentos autorizados y se realiza solo en TBF-03.

## Out of Scope
- Instalar Pi dentro de cada contenedor, llamar modelo durante tests offline, o cambiar el benchmark/verificador.
- Arrancar el runner antiguo `ticket-autopilot`.
