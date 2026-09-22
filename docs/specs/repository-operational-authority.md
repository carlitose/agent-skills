# «Autorizzo tutto»: una autorización operativa por repositorio, duradera y revocable

## Artifact Graph
- Artifact ID: `spec:repository-operational-authority`
- Role: `spec`
- Standalone: true

### Children
- [ROA-01](../tickets/repository-operational-authority/01-one-durable-operational-grant.md)

## Tipo y hechos
Decisión de producto con implementación (todo35). Skills-only, inline, sin runner.

Hoy el repositorio tiene dos autoridades duraderas, ambas por repositorio, ambas revocables,
ambas con su propio fichero de estado dentro del directorio común de Git:

- `merge` (`rma-…`), consumida por `merge-all` y por cada fusión con head esperado.
- `reconciliation` (`rar-…`), consumida por las propuestas exactas de reconciliación.

Y hay una frase natural ya enrutada: «merge all» / «mergia tutto» abre la transacción de
autoridad de fusión en vez de pedir un SHA.

Lo que no existe es el resto. Cada vez que la entrega llega a publicar una PR, a mover la
instalación local de skills al head integrado o a pedir una recarga del runtime, la
autorización se apoya en una instrucción de conversación: no queda registrada en ningún sitio,
no sobrevive a una compactación y no se puede revocar de un modo comprobable. Esta misma
sesión lo muestra: la sincronización local se ejecutó una y otra vez «bajo la directiva
permanente del usuario», una frase, no un registro.

El usuario pide poder decir una vez «autorizzo tutto» y que eso valga —de forma duradera y
revocable— para las operaciones repetitivas de ese repositorio.

## Problema
«Todo» no puede significar «cualquier cosa». Una autorización sin lista cerrada es
indistinguible de no tener autorización: nadie puede decir después qué se consintió. A la vez,
pedir permiso operación por operación, en cada sesión y después de cada compactación, es
exactamente el ruido que el usuario quiere quitarse.

Faltan tres cosas concretas:

1. Un registro duradero para las operaciones que hoy solo tienen una frase.
2. Una lista cerrada y versionada de qué cubre esa frase, y qué no cubre nunca.
3. Una lectura única que diga, para un repositorio, qué autoridades están activas, quién las
   concedió, con qué provenance y cómo se revocan.

## Decisión
Se añade una tercera clase de autoridad por repositorio, `operations` (`roa-…`), con la misma
maquinaria que ya usan `merge` y `reconciliation`: estado versionado con envoltorio de
integridad, historial encadenado, escritura atómica bajo cerrojo, estable entre worktrees, y
concesión idempotente que falla en cerrado ante estado revocado, heredado, malformado o con
provenance contradictoria.

La concesión fija una **versión de política** (`policy_version: 1`) que corresponde a una lista
cerrada de capacidades escrita en el código y en esta spec:

- `publish-pr` — crear o actualizar la PR de un candidato de este repositorio.
- `sync-local-install` — mover la instalación propia de skills al head y árbol exactos ya
  integrados.
- `request-runtime-reload` — pedir al host una recarga después de sincronizar una extensión.

La fusión y la reconciliación **no** entran en esa lista: conservan sus propias concesiones,
su propia provenance y su propia revocación. «Autorizzo tutto» no las sustituye ni las
reescribe; abre la transacción de cada una por separado y preserva la que ya esté activa.

Lo que la frase no concede nunca, en ninguna versión de política: otro repositorio; nada fuera
del repositorio (configuración global, credenciales, administración de la cuenta del
proveedor); operaciones destructivas o de reescritura (`push --force`, reescritura de
historia, borrado de ramas o worktrees, limpieza de GC); arrancar un runner o un scheduler
cuando el usuario ha elegido skills-only; y, sobre todo, nada relativo a la prueba: la
autoridad responde «puedo hacerlo», jamás «está demostrado».

Se añade además una lectura combinada, `repository-authority-status`, que devuelve el estado de
las tres clases a la vez, con sus capacidades y su estado de revocación, para que una sola
llamada baste para saber qué hay concedido.

El enrutado natural se amplía en `ask-skills`: una orden afirmativa e inequívoca del usuario
—«autorizzo tutto», «authorize everything», «autorizo todo»— sobre un repositorio conocido abre
la transacción de autoridad de las tres clases, preservando las concesiones exactas que ya
existan, y responde enumerando qué queda cubierto, qué no y cómo revocarlo. Texto citado,
ejemplos, preguntas, negaciones, revocaciones, peticiones de política e informes de error no
crean autoridad, igual que ya ocurre con «merge all».

## Invariantes
- La concesión es idempotente para el mismo actor y la misma evidencia, y contradictoria para
  otros: nunca se sustituye una provenance existente en silencio.
- Una autoridad revocada no se puede volver a conceder sobre el mismo estado; hace falta una
  decisión humana explícita y visible.
- Una capacidad que no está en la lista de la versión de política vigente se rechaza, aunque la
  concesión esté activa.
- Ampliar la lista exige una versión de política nueva; una concesión hecha bajo la versión
  anterior no se amplía sola.
- La autoridad no relaja ningún gate de evidencia, readback ni head esperado.
- El estado vive en el directorio común de Git y es idéntico desde cualquier worktree.

## Criterios de aceptación
- Conceder, leer y revocar la autoridad de operaciones funciona desde la CLI y desde cualquier
  worktree del mismo repositorio.
- Una operación cubierta se puede comprobar contra la concesión activa; una no cubierta se
  rechaza con su nombre.
- Con la autoridad ausente o revocada, cualquier comprobación falla en cerrado.
- `repository-authority-status` devuelve las tres clases en una sola lectura.
- El enrutado de `ask-skills` documenta la frase afirmativa, el alcance cerrado, la exclusión
  de fusión/reconciliación de esa lista y el límite de las menciones citadas o negadas, con
  prueba de regresión sobre el texto.

## Fuera de alcance
Migrar estado heredado de esta clase nueva (nunca ha existido), autoridad entre repositorios,
autoridad por proveedor o por cuenta, y cualquier cambio en la semántica de fusión o
reconciliación existentes.
