# El sandbox del `code` tool promete módulos que no entrega y pierde el estado que dice conservar

## Artifact Graph
- Artifact ID: `artifact:pi-code-tool-sandbox-defects`
- Role: `spec`
- Standalone: true

## Type
Bug analysis

## Status
Observado el 16/09/2026 durante el trabajo sobre `autopilot-suite-execution-cost`, en esta
sesión de Pi sobre Windows. Las trazas son literales del propio tool. El código propietario
del `code` tool vive en `pi-code-tool`, **fuera de este repositorio**: aquí solo queda el
análisis y la reproducción.

## Observado

Tres fallos distintos, todos del entorno y ninguno del código escrito:

### 1. `os` es un stub incompleto que no se anuncia como tal

```
tool.py:207:1: error[unresolved-attribute] Module `os` has no member `makedirs`
tool.py:8:7:   error[unresolved-attribute] Module `os` has no member `path`
tool.py:9:9:   error[unresolved-attribute] Module `os` has no member `path`
```

La documentación del tool declara `os` entre los módulos disponibles. Lo que se entrega es un
`os` sin `path` ni `makedirs`. Un módulo que existe pero al que le faltan sus miembros más
usados es peor que un módulo ausente: el `ModuleNotFoundError` es inmediato y legible, y este
error aparece en la línea 207 de un script ya escrito.

### 2. El estado restaurado pierde los imports y los nombres que dice conservar

```
tool.py:10:20: error[unresolved-reference] Name `pathlib` used when not defined
tool.py:3:26:  error[unresolved-reference] Name `bodies` used when not defined
tool.py:4:21:  error[unresolved-reference] Name `plan` used when not defined
tool.py:6:13:  error[unresolved-reference] Name `tmp` used when not defined
[note: session state was restored from an earlier conversation]
```

El contrato dice que variables y funciones persisten entre llamadas. Tras una restauración de
sesión persiste **la promesa**, no el estado: los nombres y los módulos importados
desaparecen. El aviso llega como nota al pie de un error, no antes de ejecutar.

### 3. Fallo de sintaxis en construcciones que el lenguaje acepta

```
tool.py:16:33: error[invalid-syntax] Compound statements are not allowed on the same line as simple statements
tool.py:16:42: error[invalid-syntax] Expected :, found else
tool.py:16:47: error[invalid-syntax] Expected :, found None
```

Un `if ...: x = 1` en una línea, y una expresión condicional, son Python válido. El validador
del tool los rechaza. El límite es real y puede ser deliberado, pero no está documentado
junto a las otras restricciones declaradas.

### 4. `ticket-emit` culpa a su fichero temporal de una carpeta que falta (ya corregido)

```
{"command":"ticket-emit","error":{"message":"[Errno 2] No such file or directory:
'...\\docs\\tickets\\pepper-voice-bench-harness\\.01-grilling-alcance-y-politica.md.dh0gfp_a.tmp'",
"type":"FileNotFoundError"},"ok":false}
```

Este sí es de este repositorio y ya está arreglado. `_atomic_write_text` creaba su temporal
en `path.parent`; si la carpeta de tickets aún no existía, el sistema reportaba el nombre del
temporal —que el llamante nunca eligió y sobre el que no puede actuar— en lugar de la carpeta
que sí eligió. Dos cambios en `scripts/autopilot/cli.py`:

- `ticket-emit` crea la carpeta de destino: una carpeta de tickets nace con su primer ticket,
  y exigir que exista antes hace fallar el camino normal de `to-tickets` antes de empezar.
- `_atomic_write_text` falla con `ContractError` nombrando la carpeta ausente, para el resto
  de llamantes donde la carpeta sí debe preexistir.

Cubierto por `test_emitting_the_first_ticket_of_a_folder_creates_that_folder` y
`test_an_unwritable_destination_names_the_folder_not_a_temporary_file`.

## Comportamiento esperado

1. Que la lista de módulos disponibles describa lo que realmente se entrega, incluyendo qué
   miembros faltan cuando un módulo está recortado; o que el módulo recortado no se ofrezca.
2. Que una sesión restaurada sin estado lo diga **antes** de ejecutar, no dentro del error
   que provoca, y que el contrato de persistencia distinga «persiste en esta sesión» de
   «persiste tras una restauración».
3. Que las restricciones de sintaxis estén documentadas con el resto de límites.

## Reproducción

Ejecutar en el `code` tool, en una sesión restaurada:

```python
import os
print(os.path.join("a", "b"))   # unresolved-attribute: os has no member path
```

y, en una llamada posterior a la que definió `tmp`:

```python
print(tmp)                      # unresolved-reference pese al contrato de persistencia
```

## Alcance y propiedad

Los defectos 1-3 son de `pi-code-tool`. Este repositorio no puede cerrarlos. El defecto 4 era
de aquí y está cerrado. Lo accionable para el resto:

- La mitigación ya aplicada en esta sesión: no usar `os.path` ni `os.makedirs` dentro del
  tool, reimportar en cada fragmento, y usar `bash`/`write` cuando el fragmento necesite
  sistema de ficheros.
- Un ticket de reporte aguas arriba, que es una acción humana: requiere decidir dónde se
  reporta y con qué credenciales.

## No objetivos

- Reimplementar el sandbox aquí.
- Envolver `os` con un adaptador propio en este repositorio para tapar el stub: escondería el
  defecto en vez de corregirlo, y el siguiente módulo recortado volvería a sorprender.

## Preguntas abiertas

1. ¿El reporte aguas arriba va a un repositorio de `pi-code-tool`, a un canal interno, o se
   queda como nota local? Es una decisión humana y bloquea el ticket de reporte.
2. ¿La restricción de sintaxis es deliberada? Si lo es, el arreglo es documental; si no, es
   un defecto del validador. No se puede decidir desde fuera del tool.
