# Limpiar los avisos de lint pendientes en el recolector de worktrees

## Artifact Graph
- Artifact ID: `spec:worktree-gc-lint-debt`
- Role: `spec`
- Standalone: true

### Children
- [WGL-01](../tickets/worktree-gc-lint-debt/01-clean-the-two-files.md)

## Tipo y hechos
Reparación de deuda de lint (todo42). Skills-only, inline, sin runner.

Durante la QA de WGC-04 se midió con Ruff 0.16.8 el estado de los dos archivos tocados y se
anotaron siete avisos que ya existían en la base `1ae97269a2a9f898c4b746d234650cd16885eee5`
(`wt57-qa-lint-baseline-q4.json`): `I001` y `UP035` en
`ticket-autopilot/scripts/autopilot/worktree_gc.py`, y `I001` dos veces, `SIM117` y `B023` dos
veces en `ticket-autopilot/tests/test_worktree_gc.py`. Al volver a medir sobre
`f4c65a10bd23720a52d97395587caf2169054516` aparece además un octavo aviso de la misma familia,
`B904`, en la línea 242 del primer archivo.

El repositorio **no tiene ninguna configuración de lint registrada**: ni `ruff.toml`, ni
`pyproject.toml`, ni un paso de lint en el flujo de CI. Esos avisos se midieron con una
selección elegida en la QA (`I,UP,SIM,B`), no con una política del proyecto. Medido hoy sobre
todo el repositorio, esa misma selección da 384 avisos, y añadiendo `E,F` sube a 3452, de los
cuales 2916 son `E501` con el límite por defecto de 88 columnas, que el proyecto claramente no
sigue.

## Estado actual y objetivo
Los dos archivos del trabajo de WGC arrastran ocho avisos. El objetivo es dejarlos limpios
bajo la selección con la que se midieron, sin cambiar comportamiento y sin inventar una
política de lint para todo el repositorio.

## Decisión
- Arreglar los ocho avisos en los dos archivos, a mano y respetando el estilo que ya usa cada
  archivo.
- `UP035`: `Callable`, `Iterable` y `Mapping` pasan a `collections.abc`; `Any` se queda en
  `typing`.
- `I001`: ordenar el bloque y quitar la línea en blanco sobrante. Los dos imports largos con
  `# type: ignore[import-not-found]` se parentizan dejando el comentario en la línea de la
  sentencia, que es como ya está escrito el import de `autopilot.worktree_gc` en ese mismo
  archivo. El arreglo automático de Ruff movía el comentario dentro del paréntesis, junto al
  nombre importado, y eso cambia a qué línea se aplica la supresión.
- `SIM117`: unir el `with` anidado del `assertRaisesRegex` al `with` que ya combina `subTest`
  y `mock.patch`.
- `B023`: el callback `interrupt` se queda con el valor de `phase` de su iteración mediante un
  parámetro por defecto. El callback se invoca con dos argumentos, así que el tercero no
  cambia ninguna llamada.
- `B904`: la `ProviderError` que se captura es una rama esperada —el repositorio no es de un
  proveedor conocido—, no la causa del fallo; se relanza con `from None` y se explica en un
  comentario.
- **No** se añade configuración de lint del repositorio ni se adopta la selección de la QA
  como política. Con 384 avisos vivos bajo esa selección, un fichero de configuración que
  fallase desde el primer día sería peor que ninguno. Queda registrado el número, no aceptado
  el silencio.

Alternativas descartadas: aplicar `ruff --fix` en bloque (movía los comentarios de supresión);
añadir `noqa` en lugar de arreglar; ampliar el arreglo al resto del repositorio dentro de este
ticket.

## Invariantes
- Ningún cambio de comportamiento: mismas excepciones, mismos mensajes y mismas firmas
  públicas.
- La suite `tests/test_worktree_gc.py` sigue pasando entera.
- No se añade ni se modifica ninguna configuración del repositorio.
- La supresión de tipos sigue aplicando a la sentencia de import a la que pertenece.

## Criterios de aceptación
1. Los dos archivos quedan sin avisos bajo la selección `I,UP,SIM,B` de Ruff 0.16.8.
2. Los ocho avisos concretos del inventario desaparecen.
3. La suite de `worktree_gc` pasa entera.
4. El diff no toca otros archivos ni añade configuración.

## Verificación y límites
Un ticket AFK. Base observada `f4c65a10bd23720a52d97395587caf2169054516`, worktree aislado.
Máximo 900 s por comando; la suite tarda unos diez minutos por sí sola. La cobertura completa
del repositorio la aporta el perfil alojado sobre el head exacto, no esta medida local.

## Fuera de alcance
Una política de lint del repositorio, los 384 avisos restantes, `E501`/`E402`, el límite de
900 s (#36) y la entrega en Windows (#45).
