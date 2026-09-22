# Entregar una PR de Azure DevOps desde Windows sin que cmd.exe reinterprete el cuerpo

## Artifact Graph
- Artifact ID: `spec:azure-windows-delivery`
- Role: `spec`
- Standalone: true

### Children
- [AWD-01](../tickets/azure-windows-delivery/01-batch-safe-description.md)

## Tipo y hechos
Reparación de bug confirmado (todo45). Skills-only, inline, sin runner.

En Windows, `shutil.which("az")` resuelve al envoltorio por lotes `az.CMD`. `CreateProcess`
ejecuta un `.cmd` a través de `cmd.exe`, que vuelve a parsear la línea de comandos que Python
construyó con `subprocess.list2cmdline`, y esa función **solo entrecomilla un elemento si
contiene espacio o tabulador**. `_azure_description_arguments` parte el cuerpo de la PR en un
elemento de argv por línea, así que una línea sin espacios llega a `cmd.exe` sin comillas.

Reproducido en este equipo con un envoltorio `.cmd` de prueba y el propio
`SubprocessCommandRunner` (Windows, Python 3.12.10):

- `awd45-probe-q1.json`: con el elemento `|---|---|` —una fila de separación de tabla, que
  aparece en casi todos nuestros cuerpos— el mandato termina con código 255 y el error
  «"---" no se reconoce como un comando interno o externo». El envoltorio no recibió nada.
- `awd45-probe-q2.json`: con el elemento `see>stray.txt` el mandato termina con código **0**,
  el envoltorio recibe solo `--description`, el resto se traga la redirección y aparece un
  fichero suelto `stray.txt` **dentro del `cwd` del runner**, que en la entrega es el worktree.
  Un éxito falso que además ensucia el árbol.

Dos problemas independientes del mismo camino:

- El límite de 4000 caracteres de la descripción de Azure DevOps se descubre después del viaje
  de ida y vuelta, no antes de llamar.
- `_run` y `_json` construyen el mensaje de error con `' '.join(command)`, así que el cuerpo
  entero —miles de caracteres— acaba dentro del motivo del gate y del ledger.

## Estado actual y objetivo
Hoy, desde Windows, la entrega a Azure DevOps se rompe o miente en cuanto el cuerpo tiene una
tabla o un `>`. El objetivo es que el cuerpo nunca pase por el parser de `cmd.exe`, que un
cuerpo demasiado largo se rechace antes de llamar, y que un fallo de proveedor no arrastre el
cuerpo entero al ledger.

## Decisión
- Cuando el ejecutable resuelto es un envoltorio por lotes de Windows (`.cmd` o `.bat`), el
  cuerpo se escribe en un fichero temporal propio y se pasa como un único valor `@fichero`,
  que es la convención documentada de Azure CLI para leer el valor de un argumento desde un
  fichero y saltarse la interpretación del shell. Así ningún carácter del cuerpo llega a la
  línea de comandos.
- Fuera de ese caso se conserva intacto el argv por línea que hoy funciona contra el servicio
  real. No se cambia un camino probado por un camino no probado.
- El fichero temporal vive en el directorio temporal del sistema, nunca dentro del worktree, y
  se borra al terminar la llamada.
- Antes de llamar, un cuerpo de más de 4000 caracteres se rechaza nombrando su longitud real y
  el límite.
- Los mensajes de error de proveedor dejan de volcar el argv completo: cada elemento largo se
  sustituye por su longitud y el total queda acotado. El detalle del fallo —`stderr`— se
  conserva entero.
- El readback sigue siendo la autoridad: si el servicio guardara algo distinto del cuerpo
  validado, el gate `delivery-pr-body` se abre igual que hoy.

Alternativas descartadas: entrecomillar a mano cada elemento para `cmd.exe` (obligaría a
cambiar el contrato de argv literal de `capture_command`, y `%VAR%` seguiría expandiéndose
dentro de las comillas); rechazar todo cuerpo con metacaracteres (dejaría sin entregar
cualquier cuerpo con tabla); usar `@fichero` también fuera de Windows (cambiaría un camino
probado contra el servicio real sin poder verificarlo aquí); llamar al intérprete de Azure CLI
saltándose el envoltorio.

## Invariantes
- El cuerpo entregado sigue siendo exactamente el cuerpo validado.
- Ningún fichero temporal se crea dentro del worktree.
- El argv literal de `capture_command` no cambia.
- El camino no-Windows conserva su argv por línea y su rechazo de líneas que `argparse` leería
  como opción.
- `stderr` del proveedor se conserva completo en el mensaje de error.

## Criterios de aceptación
1. Con envoltorio por lotes, el argv lleva `--description` seguido de un único `@fichero`, y
   ese fichero contiene el cuerpo tal cual.
2. Ningún elemento del argv contiene salto de línea, `|`, `>`, `<`, `&` o `^` cuando se usa el
   envoltorio por lotes.
3. El fichero temporal no está dentro del worktree y desaparece al terminar la llamada.
4. Sin envoltorio por lotes, el argv por línea de hoy no cambia.
5. Un cuerpo de más de 4000 caracteres se rechaza antes de ejecutar nada, nombrando longitud y
   límite.
6. El mensaje de error de un mandato fallido queda acotado y no contiene el cuerpo.
7. Las suites existentes de proveedores y de entrega siguen pasando.

## Verificación y límites
Un ticket AFK. Base observada `68fa779eb8423d773f4ff03f36dc2703aa3e8a96`, worktree aislado.
Máximo 900 s por comando. Las pruebas usan dobles y un envoltorio `.cmd` real en este equipo;
**no hay ninguna instancia de Azure DevOps disponible**, así que no se afirma nada sobre la
respuesta del servicio real. La cobertura del resto del repositorio la aporta el perfil
alojado sobre el head exacto.

## Fuera de alcance
GitHub, el cuerpo de 4000 caracteres como política de contenido, el límite de 900 s (#36) y la
autorización repository-wide (#35).
