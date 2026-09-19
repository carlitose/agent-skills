# Sesiones de Pi en la sincronización del wiki

## Artifact Graph
- Artifact ID: `spec:llm-wiki-pi-sessions-in-sync`
- Role: `spec`
- Standalone: true

## Type
Feature con una parte de seguridad.

## Resumen
El proveedor Pi ya existe en `llm-wiki`: descubrimiento, extracción y despacho se entregaron en
[llm-wiki-pi-session-provider](llm-wiki-pi-session-provider.md). Lo que falta es que las sesiones de
Pi entren de verdad en la sincronización cotidiana de un proyecto, y que hacerlo sea seguro y
barato. Hoy fallan tres cosas distintas:

1. **No se consulta por defecto.** `project_binding.DEFAULT_SESSION_PROVIDERS` es
   `("claude-code", "codex")`. Un binding nuevo nunca mira Pi, y los bindings ya escritos tampoco:
   no existe ninguna ruta para añadir Pi a un binding existente sin editarlo a mano.
2. **La ingesta no es incremental de verdad.** `session_ingest.ingest` vuelve a extraer cada
   transcript completo en cada pasada; `_is_current` solo evita *escribir* el puntero. El coste lo
   paga la lectura, no la escritura, y los transcripts de Pi son justamente los grandes.
3. **Nada redacta secretos.** `extract` copia frases de decisión literales del transcript al
   digest. Un transcript de agente contiene salida de herramientas, y esa salida puede contener
   credenciales. Escribirlas en una página del wiki las vuelve duraderas y, en un wiki versionado,
   publicables.

El tercer punto es el que ordena el trabajo: la redacción debe existir **antes** de que Pi entre por
defecto, porque activar Pi sin ella multiplica exactamente la superficie que hoy no está protegida.

## Objetivo y no objetivos
El objetivo es que `llm-wiki` ingiera sesiones de Pi en la sincronización normal, sin releer lo que
no ha cambiado y sin escribir secretos.

No es objetivo cambiar el contrato del digest (200-400 palabras, puntero sin contenido), ni el
límite de transcript grande, ni la extracción específica de Pi, ni el catálogo de sesiones, ni
tocar los proveedores Claude Code y Codex más allá de lo que la redacción implique.

## Decisión 1: redacción en la frontera del digest
Antes de que cualquier texto tomado del transcript llegue a un puntero o a un digest, se sustituyen
las credenciales por el marcador exacto `<REDACTED>`, con el mismo criterio que ya usa el contrato
de [redacción de secretos](../../diagnose/references/secret-redaction.md) de `diagnose`: tokens,
cabeceras de autorización, cookies, claves privadas y credenciales de conexión.

La redacción se aplica en la frontera, no en el consumidor: cualquier campo derivado del transcript
—frases de decisión, rutas de fichero, identificadores de ticket— pasa por ella. Se conserva la
señal no secreta circundante: si una frase de decisión menciona un token, se conserva la frase con
el token sustituido, no se descarta la frase entera.

Un digest ya escrito por una versión sin redacción es una afirmación de esa versión: se reescribe
en la siguiente pasada, igual que hoy hace `_is_current` con los punteros corregidos.

## Decisión 2: ingesta incremental por identidad del transcript
`ingest` deja de extraer un transcript cuando su identidad observada no ha cambiado respecto de la
ingesta anterior y el puntero en disco lo escribió esta misma versión del código.

La identidad observada es el tamaño en bytes y el mtime en nanosegundos del fichero, junto a la
versión del contrato de ingesta. No se usa solo el mtime: un transcript reanudado crece, y el
tamaño lo delata aunque el reloj del sistema mienta.

El recuerdo de esa identidad vive en el propio wiki, junto a los punteros, como estado generado
regenerable. Si falta, está corrupto o pertenece a otra versión del contrato, se vuelve a extraer
todo: la ausencia de recuerdo nunca se interpreta como «sin cambios».

Un fichero cuya identidad no ha cambiado no se lee, y su puntero y digest se cuentan como
`skipped`, con la misma semántica que hoy.

## Decisión 3: Pi entra por defecto, con adopción explícita
`DEFAULT_SESSION_PROVIDERS` pasa a incluir `pi`. Los bindings nuevos consultan los tres
proveedores conocidos.

Para los bindings existentes se añade una adopción explícita: una operación que añade `pi` a
`session_providers` de un binding ya escrito, registrando qué se añadió. No se reescribe un binding
por inferencia durante una sincronización: un binding que declara proveedores sigue mandando, y
añadir Pi es una acción pedida, no un efecto colateral.

Cuando el almacén de Pi no existe en la máquina, el descubrimiento devuelve cero transcripts sin
error, y el informe lo distingue de no haber mirado: `pi: 0` solo puede aparecer si Pi se consultó.

## Invariantes semánticas
1. Ningún puntero ni digest contiene una credencial procedente del transcript; el marcador es
   exactamente `<REDACTED>`.
2. La redacción no descarta la señal no secreta que rodea al secreto.
3. Un transcript sin cambios no se lee; uno cambiado, nuevo o con recuerdo ausente o corrupto sí.
4. El estado incremental es regenerable y su ausencia nunca se lee como «sin cambios».
5. El informe distingue un proveedor no consultado de un proveedor consultado con cero sesiones.
6. El contrato del digest y del puntero, el límite de transcript grande y el catálogo de sesiones
   no cambian.
7. Añadir Pi a un binding existente es una acción explícita y registrada, nunca un efecto de la
   sincronización.

## Contratos externos
- **Almacén de Pi**: `~/.pi/agent/sessions` por defecto, configurable, ya implementado. Puede no
  existir; su ausencia no es un error.
- **Wiki en Git**: los punteros y digests se versionan, de modo que un secreto escrito sería
  además publicable. Es la razón del orden de las decisiones.
- **Catálogo de sesiones**: se refresca como hoy; este spec no cambia su forma.

## Modos de fallo previstos
- Un patrón de redacción demasiado amplio vacía el digest de señal útil; por eso la invariante 2 se
  verifica con casos que conservan la frase.
- Un transcript reanudado que conserva tamaño y mtime se saltaría; por eso el recuerdo incluye la
  versión del contrato y se invalida al cambiarla.
- Un binding compartido entre máquinas puede declarar `pi` donde el almacén no existe; eso debe
  reportar cero, no fallar.

## Slices de implementación
1. **Redacción** en la frontera de extracción, con sus casos positivos y negativos.
2. **Incremental**, apoyado en la identidad observada del transcript.
3. **Pi por defecto y adopción** de bindings existentes.

El tercero depende de los dos primeros: activar Pi antes de tener redacción publicaría lo que este
spec quiere evitar.

## Estrategia de verificación
Pruebas unitarias de redacción con formas sintéticas de credencial —nunca reales— comprobando el
marcador exacto y la señal conservada. Pruebas de ingesta que ejecuten dos pasadas y comprueben que
la segunda no vuelve a leer el transcript, y que sí lo hace cuando el fichero crece o cuando el
recuerdo falta o está corrupto. Pruebas de binding para el valor por defecto y para la adopción.
Después, el perfil local correspondiente y la CI del repositorio.

Límites declarados: las pruebas usan fixtures sintéticos, no transcripts reales; la cobertura de
patrones de credencial es la declarada y no una garantía universal; no se afirma comportamiento en
macOS.

## Alternativas y exclusiones
Se descarta cifrar o excluir del wiki los digests con secretos: el problema es escribirlos, no
protegerlos después. Se descarta un índice incremental global fuera del wiki, porque el estado
dejaría de ser regenerable junto a lo que describe. Quedan fuera la búsqueda semántica, el
retrieval híbrido y cualquier cambio al formato del digest.
