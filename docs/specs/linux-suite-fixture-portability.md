# Prerrequisito Linux: fixtures portables sin reducir garantías

## Artifact Graph
- Artifact ID: `artifact:linux-suite-fixture-portability`
- Role: `spec`
- Standalone: true

### Children
- [01 Corregir los fixtures y verificar ambos hosts](../tickets/linux-suite-fixture-portability/01-portable-fixtures.md)

## Tipo y alcance

Bug analysis. Prerrequisito separado del lote
[suite-cost-one-percent](suite-cost-one-percent-wayfinder.md), no ampliación de sus seis
tickets. El usuario autorizó diagnosticar y corregir los diez checks Linux preexistentes y
confirmó «Sí, aplicar y verificar»: cambios solo de tests/fixtures, incluido verificar
reaping con `ESRCH` sobre el mismo pidfd en vez de exigir `POLLHUP`. Hasta 20 ciclos de
calidad; sin skips nuevos, reintentos encubridores, cambios de contención ni autorización
implícita para publicar o integrar este prerrequisito.

## Evidencia y causas

Los diez checks fallan con las mismas firmas en `44c26f3` y en `4468e03` más las dos
correcciones de filemode de `test_cli`. Entorno observado: WSL Ubuntu, Python 3.12.3,
Git 2.43.0. No fue un `full` del padre. La comparación retenida es
`linux-failure-signature-comparison.json`; las intervenciones aisladas están en
`linux-prerequisite-causal-probes-v2.log` y su recibo `.result.json`, en el directorio local
de evidencia `prof/tk1/profile-contract-decision`. No son evidencia de candidato GREEN.

| Checks afectados | Causa demostrada | Corrección acotada |
| --- | --- | --- |
| Tres checks de `test_session_ingest` | Los hashes incluyen el tamaño del transcript; los goldens históricos corresponden a CRLF, pero Linux escribe LF. CRLF restaura todos los hashes originales. | Hacer explícitos los bytes CRLF solo en los fixtures de goldens; conservar y comprobar LF y CRLF. No modificar hashes ni serialización de producto. |
| Tres checks de `test_sync_project` y su wrapper `test_wiki_sync_forward_matrix` | Los filtros Git invocan `python`, ausente del PATH Linux. Un filtro opcional fallido deja los bytes originales. El intérprete actual hace pasar las mismas aserciones. | Configurar el intérprete en ejecución, con quoting para el shell de Git. Mantener bytes exactos, autocrlf, contadores, filtro inválido y fallos cerrados. |
| `BothPlatformsAdoptTests` | El spy de `fchmod` no aplica el modo; el temporal POSIX queda en 0600. Simular Windows no cambia ese comportamiento del filesystem anfitrión. | Delegar al `fchmod` real cuando existe; probar un modo POSIX no trivial. Para la rama Windows simulada, igualar el modo del origen al temporal. Conservar ambos casos en ambos hosts y distinguir simulación de ejecución nativa. |
| Modo ejecutable de `test_wiki_noop` | `update-index --chmod=+x` no cambia el modo del archivo: POSIX observa suciedad ajena al escenario. | Igualar archivo e índice; conservar rechazo por alcance y protección de HEAD/status. |
| `test_posix_command_bounds` | Este kernel conserva `POLLIN` sin `POLLHUP` tras recoger el proceso. Ambos pidfds ya devuelven `ESRCH` cuando falla la aserción original. | Conservar observación de salida y exigir `ESRCH` en los mismos pidfds dentro del plazo existente. No consumir wait status ni incorporar subreapers. |

La hipótesis de falta de reaping quedó descartada por el observador sin intervenciones.
El probe de lifetime distinguió proceso vivo, zombie y proceso recogido: señal 0 tiene
éxito antes de `wait()` y devuelve `ESRCH` después. Una intervención con `waitid(P_PIDFD)`
sí altera la propiedad del wait status; no forma parte de la solución.

## Contratos e invariantes

- [pidfd_send_signal(2)](https://man7.org/linux/man-pages/man2/pidfd_send_signal.2.html):
  `ESRCH` identifica un proceso terminado y recogido; el descriptor evita confundir PID
  reutilizados. Señal 0 observa, no mata ni recoge. Otros errores no cuentan como éxito.
- [gitattributes](https://git-scm.com/docs/gitattributes): un filtro ausente/fallido puede ser
  passthrough si no es requerido. Conservar el test independiente del filtro requerido.
- Mantener los tres motivos de contención: timeout, cancelación y límite de salida; plazo
  de retorno, salida de los dos procesos, reaping acotado, control no afectado y cleanup.
- Un control adicional debe demostrar que el nuevo predicado rechaza procesos vivos y
  zombies, acepta solo el proceso recogido y no roba su wait status.
- No modificar código de producto, snapshots, goldens, cobertura de escenarios, políticas
  de Git globales ni dependencias instaladas. Preservar Windows, macOS y POSIX.

## Implementación y aceptación

Una sola slice AFK, verificada de extremo a extremo, limitada a:
`llm-wiki/tests/test_session_ingest.py`, `test_sync_project.py`,
`test_root_catalog_adoption.py`, `ticket-autopilot/tests/test_wiki_noop.py` y
`test_posix_command_bounds.py`. El wrapper forward debe pasar sin editarlo.

1. Aplicar las cinco correcciones de fixtures y sus controles negativos.
2. Ejecutar una vez los diez checks originales y los módulos afectados en Linux y Windows.
   Conservar cada intento, incluidos fallos; una corrección produce un candidato nuevo.
3. Ejecutar `full --jobs 8` en ambos hosts, con procesos desacoplados y logs completos.
   El candidato final debe incluir las correcciones previas de revisión de la base.
4. Congelar el candidato y componer simplificación, review, QA y verificación canónica
   inline; una revisión en contexto compartido no se describe como independiente.

Aceptación: todos los checks anteriores pasan con hashes/aserciones preservados salvo el
predicado de reaping explícitamente autorizado; LF/CRLF, permisos reales y lifetime tienen
controles observables; `full` pasa en ambos hosts sobre el mismo contenido candidato.
macOS no disponible queda como límite de evidencia, nunca como ejecución inventada.
Las ramas Linux que no aplican a Windows conservan sus guardas existentes.

## Alternativas rechazadas y entrega

No instalar un alias global `python`, regenerar goldens por plataforma, desactivar filemode,
añadir skips, alargar deadlines, aceptar solo salida sin reaping ni cambiar el supervisor.
Ninguna prueba local resuelve gates de dependencia, provider, aprobación o merge. No
publicar el lote principal mientras este prerrequisito permanezca sin validar; su entrega
externa requiere autoridad separada. El ticket 06 principal sigue sujeto al estado canónico.
