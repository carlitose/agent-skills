# Checkpoint de revisión del plan

## Artifact Graph
- Artifact ID: `spec:plan-review-checkpoint`
- Role: `spec`
- Standalone: true

## Type
Decision sobre disciplina de ejecución.

## Problema observado
Durante la sesión que integró los tickets 01–06 el plan se degradó dos veces por la misma causa:
después de una compactación de contexto, la lista de tareas seguía viva pero su relación con el
objetivo y con la evidencia ya no se había revisado. Los síntomas fueron concretos: tareas
terminadas que seguían abiertas, tareas nuevas anotadas sin prioridad ni dependencia, y varias
«próximas acciones» plausibles al mismo tiempo, lo que obliga a reconstruir el estado a mano en
cada retoma.

Las reglas de ejecución actuales dicen mantener exactamente un paso `in_progress` y refrescar el
plan «en cambios de estado relevantes», pero no dicen **cuándo** hay que reconciliar el plan
completo contra la evidencia, ni **qué** hay que comprobar al hacerlo. Un refresco no es una
revisión: reescribir el plan con la misma información equivocada lo deja igual de equivocado.

## Objetivo y no objetivos
El objetivo es que exista un momento nombrado y obligatorio en el que el plan se reconcilie con el
objetivo y con la evidencia, y que ese momento produzca exactamente una próxima acción.

No es objetivo crear una herramienta de planificación nueva, ni sustituir la frontera de
`wayfinder`, ni el estado del runner, ni convertir el plan en evidencia: un plan describe
intención, no resultados observados.

## Decisión 1: tres disparadores explícitos
El checkpoint se ejecuta al ocurrir cualquiera de estos tres hechos, y no «cuando parezca
oportuno»:

1. **Compactación de contexto**, porque el resumen conserva el texto de las tareas pero pierde por
   qué estaban en ese orden.
2. **Fin de fase**, entendido como un ticket que alcanza un estado terminal o un artefacto que se
   integra, porque es cuando las dependencias del resto cambian de verdad.
3. **Bloqueo**, cuando una acción queda esperando una decisión humana, una autorización o un
   entorno que no está, porque la lista deja de describir lo que se puede hacer.

## Decisión 2: qué comprueba
El checkpoint reconcilia la lista completa, no la tarea activa. Sobre cada elemento comprueba:

- **Objetivo**: para qué resultado existe; un elemento que no sirve al objetivo declarado se
  retira o se reformula, no se arrastra.
- **Evidencia**: si se afirma terminado, qué observación lo respalda. Marcar completado sin
  observación es la forma más barata de perder el hilo.
- **Omisiones**: trabajo que la sesión ya sabe necesario y que no está escrito en ninguna parte.
- **Duplicados**: dos entradas que describen el mismo resultado, que se funden conservando la
  redacción más precisa.
- **Prioridad y dependencias**: qué desbloquea qué, para que el orden no dependa de la memoria.

## Decisión 3: una sola próxima acción
El checkpoint termina fijando exactamente una próxima acción, nombrada de forma que se pueda
empezar sin volver a decidir. Si quedan varias candidatas, el checkpoint no ha terminado: elegir
es parte del trabajo, no del siguiente turno.

## Decisión 4: integración con lo que ya existe
El checkpoint usa las herramientas presentes y declara la que falte, sin inventar estado:

- Con **Pi Plan** disponible, la reconciliación se refleja allí y se mantiene un único paso
  `in_progress`; sin él, se declara el sustituto usado en vez de fingir que hay plan.
- Con **wayfinder** en juego, la frontera manda sobre el plan: el plan puede reordenar, pero no
  declarar resuelto un borde de investigación que la frontera mantiene abierto.
- El estado del runner y sus gates no se reescriben nunca desde el plan; el plan los refleja.

## Invariantes semánticas
1. Los tres disparadores están nombrados y son verificables; «cuando parezca oportuno» no es uno.
2. La reconciliación abarca la lista completa, no solo la tarea activa.
3. Un elemento marcado como terminado cita la observación que lo respalda.
4. El checkpoint termina con exactamente una próxima acción.
5. El plan nunca es evidencia ni autoridad: no cierra gates, no concede permisos y no reescribe
   estado del runner ni frontera de investigación.
6. La ausencia de una herramienta de plan se declara; no se sustituye por una afirmación.

## Dónde vive
En las reglas de ejecución de `ask-skills`, junto al resto de disciplina que ya aplica después de
enrutar. Es el sitio donde una regla de este tipo se lee sin cargar nada más, y donde ya vive la
instrucción de mantener un único paso en curso.

## Estrategia de verificación
Una prueba del repositorio comprueba que la regla existe con sus tres disparadores, sus cinco
comprobaciones, la salida de acción única y la prohibición de tratar el plan como evidencia o
autoridad. Es verificación estructural: que el texto esté y diga lo que debe decir. No demuestra
que un agente lo obedezca, y el spec no afirma lo contrario.

## Alternativas y exclusiones
Se descarta una skill nueva dedicada al checkpoint: sería una regla de dos párrafos con un fichero
propio, y el coste de descubrirla superaría al de aplicarla. Se descarta también atarla a un
temporizador o a un número de turnos, porque el problema no es el tiempo transcurrido sino la
pérdida de contexto. Quedan fuera cualquier cambio a la herramienta de todos, al runner y a la
frontera de `wayfinder`.
