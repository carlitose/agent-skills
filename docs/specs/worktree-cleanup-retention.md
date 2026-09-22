# Limpieza de worktrees: probar la retención, no suponerla

## Artifact Graph
- Artifact ID: `spec:worktree-cleanup-retention`
- Role: `spec`
- Standalone: true

### Children
- [WGR-01](../tickets/worktree-cleanup-retention/01-prove-retention-by-integration.md)
- [WGR-02](../tickets/worktree-cleanup-retention/02-name-the-exit-in-each-refusal.md)

## Problema

La limpieza oficial de un worktree aislado pregunta, con razón, si borrarlo perdería trabajo.
Hoy responde esa pregunta mirando **una sola rama remota**: la rama de la propia run. Si esa rama
ya no está donde se esperaba, concluye que el trabajo no está retenido y se niega a limpiar.

Esa conclusión es falsa en el caso más frecuente de todos: el proveedor borra la rama de origen al
fusionar la PR. El commit está en `main`, no se pierde nada, y aun así la limpieza se niega.
Reproducido en repositorios desechables (`wgr48-probe-q1.json`, `wgr48-probe-q2.json`) contra
`agent-skills` main `8c779cc9875cbf7e078658878094c6f1cfaaf1bd`:

| Situación | Head contenido en `main` remoto | Resultado hoy |
| --- | --- | --- |
| Rama publicada, sin fusionar | no | permite limpiar |
| Fusionada, rama borrada por el proveedor, ref de seguimiento viva | sí | `branch 'feat/x' is not retained at its current head` |
| Fusionada, rama borrada con la ref de seguimiento podada | sí | `branch 'feat/x' has no retained upstream` |
| Rama nunca publicada, head idéntico al `main` remoto | sí | `branch 'feat/local' has no retained upstream` |
| Fusionada, rama viva | sí | permite limpiar |

Las tres filas del medio son negativas equivocadas: el trabajo está retenido en el remoto y la
herramienta dice lo contrario. El efecto acumulado lo reportó el usuario: veinte worktrees que la
limpieza oficial rechaza, alrededor de 1,1 GB, creciendo con cada run que fusiona con borrado de
rama.

## Decisión

La pregunta correcta no es «¿sigue existiendo esta rama?», sino «¿está este head contenido en la
rama por defecto del remoto?». Se añade esa comprobación como **prueba de retención por
integración**, y solo se consulta cuando la comprobación por rama ya ha fallado.

1. Se observa la rama por defecto del remoto y su SHA con `ls-remote`, igual que hoy.
2. Se prueba la contención **localmente**, con `git merge-base --is-ancestor`, sin traer nada:
   la limpieza no hace `fetch` ni escribe en el remoto.
3. Si el objeto de esa rama por defecto no está en el repositorio local, la prueba **no** se da
   por buena: se rechaza la limpieza diciendo exactamente eso y nombrando el `git fetch` que la
   haría posible. Un rechazo honesto por falta de prueba, no una suposición.

Ninguna de las protecciones existentes se relaja:

- Un worktree sucio sigue bloqueando la limpieza: el trabajo sin confirmar no está en ningún sitio.
- Una rama con commits que no están en la rama por defecto sigue bloqueando la limpieza.
- Las protecciones que resguardan decisiones humanas —run en curso, run en espera, ticket en
  espera administrativa— viven en otra capa y este cambio no las toca.

El mensaje de cada rechazo pasa a decir qué se comprobó y contra qué SHA, para que nadie tenga que
adivinar por qué se negó.

## Invariantes

- La limpieza nunca borra nada por sí sola: sigue siendo una operación que alguien pide.
- La prueba de retención es local y verificable: un ancestro demostrado, no una inferencia.
- Sin prueba no hay permiso. La ausencia de una rama nunca se interpreta como integración.
- No se hace `fetch`, ni `push`, ni ninguna escritura en el remoto dentro de la comprobación.
- Un worktree sucio o con commits fuera de la rama por defecto se sigue rechazando igual.

## Criterios de aceptación

1. Un head contenido en la rama por defecto del remoto permite limpiar, exista o no la rama de la
   run, y tenga o no upstream configurado.
2. Un head no contenido en la rama por defecto se sigue rechazando, con un mensaje que nombra la
   rama por defecto observada y su SHA.
3. Si el SHA de la rama por defecto no está presente localmente, se rechaza indicando que la
   prueba no se pudo hacer y qué comando la haría posible.
4. Un worktree sucio se sigue rechazando aunque su head esté contenido en la rama por defecto.
5. La comprobación no ejecuta `fetch` ni ninguna escritura remota.

## Segunda parte: nombrar la salida

Las protecciones que quedan no son errores: resguardan decisiones humanas. El problema es otro,
y también está medido: **no dicen cómo se abren**.

| Rechazo de hoy | Salida que sí existe | ¿La nombra? |
| --- | --- | --- |
| `cleanup of failed run requires --confirm` | `--confirm` | sí |
| `cleanup of waiting run requires --force` | `--force` | sí |
| `running run cannot be cleaned up` | abortar la run, o esperar a que termine | no |
| `run is paused before worktree:cleanup` | `unpause` | no |
| `ticket disposition forbids worktree:cleanup: on-hold` | reabrir el ticket | no |

Los tres últimos se cambian para que el mensaje nombre el acto exacto que los abre, con el
comando y los datos que pide. No se relaja ninguna condición: lo que hoy se rechaza se sigue
rechazando, y quien quiera abrirlo tiene que hacer ese acto, que queda registrado. La diferencia
es que deja de haber que leer el código para saber cuál es.

## Fuera de alcance

- Relajar las protecciones de run en curso, run en espera o ticket en espera administrativa: WGR-02 solo cambia lo que dicen, nunca lo que permiten.
- Borrar worktrees automáticamente o en lote.
- Consultar al proveedor: la prueba es de Git, no de la API de la plataforma.
