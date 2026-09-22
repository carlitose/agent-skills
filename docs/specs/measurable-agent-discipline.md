# Escribir las tres reglas de disciplina que las sesiones ya pagaron

## Artifact Graph
- Artifact ID: `spec:measurable-agent-discipline`
- Role: `spec`
- Standalone: true

### Children
- [MAD-01](../tickets/measurable-agent-discipline/01-write-the-three-rules.md)

## Tipo y hechos
Corrección de hábito con evidencia medida (todo #55, remedios 2, 4 y 5 de la crítica de
sesiones). Skills-only, inline, sin runner. No cambia código ejecutable.

Tres hechos medidos sobre los registros de sesión del propio operador:

1. **La longitud de la sesión cuesta dinero.** De 3 099 $ repartidos en 51 sesiones, una sola
   costó 815 $ con 4 638 llamadas y 41 compactaciones. Pagó **0,176 $ por llamada**; la mediana
   de las sesiones cortas queda por debajo de 0,10 $. El 96 % de los tokens son lectura de
   caché: una sesión de 4 638 turnos relee su prefijo 4 638 veces.
2. **Las llamadas van de una en una.** De 17 315 turnos del asistente con herramientas,
   **16 859 (97,4 %) llevan una sola llamada**; 282 llevan dos y 174 tres o más. La regla de
   agrupar lo independiente ya existe en el prompt del sistema y aun así casi nunca se cumple.
3. **Los errores de shell son de plataforma.** 523 resultados de `bash` marcados como error:
   256 son códigos de salida de PowerShell leídos a través de `cmd.exe`, 114 tracebacks de
   Python, 69 «not found» —casi todos rutas con `\` frente a `/`— y 49 timeouts.

## Estado actual y objetivo
Las tres reglas viven hoy en un documento de crítica privado que ninguna sesión lee. El
objetivo es que vivan donde el instrador ya mira —`ask-skills/OPERATING-DEFAULTS.md`— y en la
memoria persistente, que sobrevive al cierre de la sesión.

## Decisión
- Tres filas nuevas en la tabla de `OPERATING-DEFAULTS.md`, cada una con **el número que la
  justifica**. Una regla sin su medida se discute; una regla con su medida se aplica.
- Redacción corta a propósito: ese fichero se lee muchas veces por sesión —17 en la sesión
  medida— así que cada línea se paga muchas veces.
- Se escriben como **defaults, no como prohibiciones**. Una llamada que depende de la anterior
  sigue esperando su entrada, y un ticket que de verdad continúa el trabajo anterior sigue en
  su sitio. Una regla que no admite su excepción se incumple entera.
- La misma sustancia se guarda en memoria persistente, que es lo único que cruza el final de
  una sesión.

## Lo que esta spec no puede probar
Una sesión nueva no se puede medir desde dentro de la sesión que se está midiendo. La sesión
donde se escribe esto es una de las que forman la línea base, así que el «después» limpio no
existe todavía.

Lo que sí se puede medir es esta misma sesión partida por el instante en que se escribió la
crítica, que es un corte real en los datos:

| Ventana | Turnos | Turnos con más de una llamada | Llamadas repetidas |
|---|---|---|---|
| Antes de la crítica | 2 627 | 24 (**0,91 %**) | 89 (3,31 %) |
| Después | 295 | 11 (**3,73 %**) | 2 (0,65 %) |

Es una instantánea: la sesión seguía abierta al medir, así que la ventana «después» crece. Una
segunda lectura diez turnos más tarde da 3,61 % y 0,63 %, y la ventana «antes» no se mueve.

El agrupamiento se multiplica por cuatro y las repeticiones caen a una quinta parte. Y sigue
siendo el 3,7 %: la mejora es real y pequeña. Además mide atención, no reglas: en esa ventana
el agente sabía que estaba siendo medido. Por eso hay que escribirlas, porque la atención no
sobrevive a una compactación y el texto sí.

## Criterios de aceptación
1. Las tres reglas están en `OPERATING-DEFAULTS.md`, cada una con su número.
2. Cada regla dice cuándo no aplica.
3. El documento sigue siendo corto: no más de una línea de tabla por regla.
4. La medición antes/después queda registrada con su método y su fecha.
5. Se dice explícitamente que no existe todavía una sesión nueva medida.
6. La misma sustancia queda en memoria persistente.
7. El grafo canónico de artefactos sigue válido.

## Límites declarados
- No cambia código: nada aquí obliga a nada, solo lo hace visible donde se decide.
- La medida del «después» es de la misma sesión y del mismo operador; no es un experimento
  controlado y no se presenta como tal.
- El coste por llamada de las sesiones largas frente a las cortas es una comparación entre
  sesiones, no una medición directa del tributo de la longitud.
