# Ticket Driver: el runner es el proceso y el modelo solo hace el giro de skills

## Artifact Graph
- Artifact ID: `artifact:ticket-driver`
- Role: `spec`
- Standalone: true

### Children
- [TDR-01](../tickets/ticket-driver/01-drive-one-ticket-with-one-leaf.md)
- [TDR-02](../tickets/ticket-driver/02-review-and-qa-in-fresh-leaves.md)
- [TDR-03](../tickets/ticket-driver/03-typed-judgments-and-the-cascade.md)
- [TDR-04](../tickets/ticket-driver/04-risk-directed-review.md)
- [TDR-05](../tickets/ticket-driver/05-measure-the-candidates-and-choose.md)

## Type
Arquitectura (con la decisión de APF-06 registrada)

## Status
Active — tickets TDR-01..05 emitidos; las decisiones humanas pendientes están al final

## Por qué existe esta especificación

APF-06 preguntaba «¿quién guía a quién?». El benchmark interno (`bench38`, mismo encargo,
mismo modelo `claude-sonnet-4-6` con razonamiento medio, repositorio sembrado nuevo en cada run)
respondió con datos, no con convicción. Tiempos medidos desde la primera hasta la última línea de
la sesión; «latentes» son los cinco defectos de redondeo que ninguna prueba visible cubre.

| brazo | s | $ | turnos | latentes hallados | rasgo |
|---|---|---|---|---|---|
| Pi desnudo | 80 | 0,11 | 11 | 0/5 | sin skills |
| skills-only (giro de skills inline, sin runner) | 144 | 0,44 | 26 | **3/5** | la calidad viene de aquí |
| autopilot q1 | 910 | 3,98 | 137 | 3/5 | |
| autopilot q2 | 1 382 | 6,42 | 177 | 1/5 | |
| autopilot q3 (APF-01..04 instalados) | 1 470 | 7,40 | 203 | 0/5 | merge a mano fuera del runner |
| autopilot q4b (APF-01..08) | 2 107 | 9,14 | 229 | 0/5 | merge a mano fuera del runner |
| autopilot q4c (APF-01..08) | 2 377 | 9,55 | 222 | 1/5 | único run que entregó por el runner |

Clasificando cada turno de las sesiones con runner: **62–67 % de los turnos (hasta el 71 % del
coste) son protocolo** — el modelo invoca el CLI, lee JSON de estado, escribe eventos, recibe
`TransitionError`, corrige el formato y reintenta. Solo el 9–12 % toca el código del encargo. El
CLI en sí consume menos del 10 % del tiempo. El núcleo semántico son 20–26 turnos en **todos**
los brazos. Los ocho arreglos APF-01..08 quitaron muros y el modelo llegó al siguiente muro,
más lejos y más caro: llamadas al CLI 9 → 15 → 37 → 24 → 37; turnos 137 → 229.

Dos lecturas que sostienen todo lo que sigue:

1. **La calidad la produce el giro de skills** (`to-spec → to-tickets → execute-ticket` con
   review, QA y verificación). Sin runner, ese giro halla 3 de 5 latentes donde Pi desnudo halla
   0. No hay que sustituirlo: hay que envolverlo.
2. **Los contratos del kernel eran correctos; el protocolo no.** Worktree aislado, identidad del
   candidato por árbol, registro de hechos observados, gates con motivo literal, prueba de
   ancestría al integrar y autoridad humana nunca inferida son lo que hace posible el AFK.
   Lo que se fue de las manos es el *mecanismo* de participación del modelo: un `leaf-result` de
   doce campos obligatorios, evidencia autodeclarada, ficheros de eventos, `resume`, siete
   viajes de ida y vuelta. En ese mecanismo el modelo deja de hacer el giro de skills y pasa a
   ser el empleado del kernel, y además firma sus propios gates.

## Decisión (cierra APF-06)

**Se invierte la dirección de llamada.** El runner es el proceso: crea el worktree, lanza al
modelo como una *hoja* que ejecuta el giro de skills, observa lo que la hoja deja en el
worktree, ejecuta las pruebas él mismo, registra recibos con hash, consulta juicios tipados donde
hace falta significado, e integra con prueba de ancestría. **El modelo no ve el CLI, no rellena
ningún esquema y nunca es consultado sobre su propio trabajo.**

Lo que se conserva: los contratos del kernel, reutilizando sus funciones puras como biblioteca.
Lo que se sustituye: el protocolo de hoja (`leaf-result`, eventos, `resume`, máquina de
etapas guiada por el modelo).

Decisiones del usuario que fijan el marco (2026-09-23):

- Trabajo **skills-only permanente**; ningún runner ni driver se ejecuta sin autorización explícita
  por lote de benchmark.
- **Sin techos.** Se construyen candidatos, se miden todos con el mismo benchmark y después se
  elige el camino.
- Juicios tipados con **Jev** (TypeSafe System One, API alojada) para no añadir piezas; Laya
  (equivalente local) queda descartada por ahora.
- Métricas nuevas: **líneas de código generadas excluyendo pruebas** y **cobertura de pruebas**.
- Ante incertidumbre: **cascada Jev → LLM fresco → gate humano**, porque la función primaria del
  proyecto es AFK con calidad.
- Los candidatos viven como **una skill nueva en agent-skills**, un solo driver con
  `--candidate`, y el benchmark selecciona el candidato con un solo comando.
- `ticket-autopilot` queda **congelado e instalado**, sin funciones nuevas; su retirada se decide
  solo cuando haya un candidato ganador.

## Objetivos

- Un ticket (o un encargo en texto) se lleva de principio a fin, AFK, con las garantías del
  kernel, en un tiempo y coste del orden del brazo skills-only más lo que cuesten las garantías —
  medido, no prometido.
- Ningún gate lo aprueba quien produjo el trabajo.
- Cada hecho del registro es observado por el driver o es un juicio tipado con su probabilidad,
  su umbral y su salida de escalada; nunca una declaración del modelo.
- El benchmark privado mide cada candidato con las mismas métricas y un solo comando por brazo.

## No objetivos

- Programar varios tickets con dependencias (la frontera del scheduler). El driver toma **un**
  ticket; la frontera es trabajo posterior y hoy la cubre `ticket-autopilot` congelado.
- Entrega a proveedor (PR y merge en GitHub/Azure). Los candidatos integran en la rama objetivo
  **local** con prueba de ancestría; el proveedor llega después reutilizando `providers.py`.
- Sincronización de wiki, recolección de worktrees, autoridad repository-wide.
- Tocar `execute-ticket` ni las demás skills del giro.
- Laya, fine-tuning, calibración formal: solo se **registran** los datos que lo harían posible.

## Comportamiento actual y objetivo, por etapa

| etapa de `execute-ticket` | hoy (runner guiado por el modelo) | objetivo (driver como proceso) |
|---|---|---|
| implement, simplify | el modelo trabaja y luego redacta un `leaf-result` que `resume` valida | **hoja constructora** (`pi -p` en el worktree); el driver observa el diff y calcula el árbol |
| review | el mismo contexto se revisa y se declara `pass` | C1a: mismo contexto; C1b: **hoja revisora fresca** que solo ve ticket + diff; sus hallazgos se leen del Markdown que la skill ya escribe |
| qa-plan | el modelo declara `quality.evidence` | hoja QA (fresca en C1b) escribe el plan y pruebas; el driver **copia y hashea** el plan como artefacto redactado por el modelo |
| qa-execute | el modelo ejecuta por `bash` y lo cuenta | **el driver ejecuta** los comandos declarados en el plan y la suite del proyecto con `capture_command`; exit code, duración, hash y salida acotada van al registro |
| verify | el modelo copia una fixture y redacta el bundle a mano | el driver compone el bundle **desde el registro**; lo semántico (¿los hallazgos bloquean?, ¿la afirmación está sostenida?) lo decide el árbitro |
| finalize | gate `delivery-pr-body`, PR body a mano, merge manual fuera del runner | el driver hace commit del candidato, integra en la rama local con `merge-base --is-ancestor` y árbol comparado; el cuerpo de la PR se **renderiza** del bundle |

## Arquitectura

### Componentes

- **Driver** (`ticket-driver/scripts/ticket_driver.py`, Python, sin dependencias fuera de la
  biblioteca estándar salvo lo que importa de `ticket-autopilot/scripts/autopilot`): el único
  proceso de control. Subcomandos: `run --candidate <id> (--ticket <path> | --task <path>) --repo
  <path> [--base <ref>]`, `status <run_id>`, `report <run_id>`.
- **Hojas**: sesiones `pi -p` con `cwd` = worktree, `--session-dir` bajo el run, prompt tomado de
  `ticket-driver/prompts/<hoja>.md` (versionado, su hash va al registro). Las skills se cargan
  como en cualquier sesión; el prompt exige el giro inline y prohíbe arrancar runner alguno.
  Hojas: `builder`, `reviewer`, `qa`, `judge` (LLM fresco de la cascada).
- **Observador**: derivado de artefactos que posee el driver — `git` (diff, árbol, ficheros
  tocados), `capture_command` (pruebas), sistema de ficheros (artefactos Markdown de las skills),
  sesiones `pi` (turnos, coste, tokens por hoja).
- **Árbitro**: cliente de Jev (`POST https://api.typesafe.ai/v1/systemone`, `Authorization:
  Bearer`, cuerpo `{model, state, questions}`, respuesta `{answers, usage}`) con las preguntas
  de `ticket-driver/questions/*.json` y los umbrales de `ticket-driver/policy.json`.
- **Cascada**: Jev → hoja `judge` (sesión nueva; recibe solo diff, prosa y la pregunta) → gate
  humano con motivo literal. Cada paso queda en `escalations.jsonl`.
- **Integrador**: commit del candidato en la rama del worktree, integración en la rama objetivo
  local, prueba de ancestría, comparación de árboles.
- **Registro** (append-only, bajo `<repo>/.git/ticket-driver/runs/<run_id>/`): `ledger.jsonl`
  (hechos observados), `receipts/` (recibos hasheados), `sessions/<hoja>/`, `judgments.jsonl`,
  `escalations.jsonl`, `summary.json` (identidades, métricas, hash de política y prompts).

### Contrato de la hoja: cero salida estructurada

La hoja recibe un prompt y un worktree. Sus únicos productos son **ficheros en el worktree** y
**prosa** en los artefactos que las skills ya escriben. No existe ningún formato que la hoja
deba aprender ni ningún campo que pueda rellenar mal. Si el driver necesita saber algo, o lo
observa, o se lo pregunta al árbitro.

### Regla observable / semántico

Tres preguntas en orden; se para en la primera que responda sí.

1. **¿El driver puede calcularlo a partir de artefactos que posee?** (git, ficheros, exit code,
   hash, cobertura). → **Observable.** No se pregunta a ningún modelo. Prueba práctica: existe una
   función sin llamadas a modelo y un test que asevera su igualdad; dos ejecuciones sobre el mismo
   artefacto dan lo mismo.
2. **¿Puede volverse observable cambiando qué se captura?** «He lanzado las pruebas» → el driver
   las lanza. «La cobertura es adecuada» → se mide y se aplica un número de política. → Hacerlo
   observable. Cada pregunta que cae aquí es una pregunta menos al modelo.
3. **Si no, es un juicio sobre el significado**: dos lectores competentes pueden discrepar y no
   hay procedimiento determinista. → **Semántico.** Va al árbitro con el estado exacto (el
   texto o el hunk, no «el ticket»), una pregunta, un umbral de política y una salida de escalada.
   Nunca autoridad.

Piedra de toque: si la respuesta cambia al cambiar de lector pero no de artefacto, es semántica;
si solo cambia al cambiar el artefacto, es observable. La autoridad humana es una categoría
aparte: ni observable ni juicio.

| nodo del árbol decisional | parte observable (driver) | parte semántica (árbitro) |
|---|---|---|
| candidato (D6/D8) | árbol, diff, ficheros tocados, deriva | — |
| QA (qa-execute) | comando, exit code, hash, duración, cobertura, LOC sin pruebas | — |
| resultado de etapa (D4) | ¿hay hallazgos? severidad declarada en `[blocker\|should-fix\|nit]` | «¿este hallazgo bloquea?» cuando falta o es dudosa |
| alcance (D6) | ficheros del ticket frente a ficheros tocados | «¿cubre cada criterio de aceptación?» |
| clase de evidencia (Y1) | ¿el proceso abrió red, sockets, ficheros externos? | etiqueta unit/integration/simulated cuando la observación no basta |
| afirmaciones del cuerpo de PR (L4) | el `evidence_id` citado existe y tiene exit 0 | «¿el texto está sostenido por esa salida?» |
| reintento o parada | número de intentos, misma prueba fallida dos veces | «¿es corregible con otra pasada de implement?» |
| riesgo latente | funciones modificadas (AST), toca aritmética o límites | Score de «cambio semántico de redondeo/límites» por hunk |
| autoridad (H1–H7) | — | — → humana |

El formato de hallazgos `[blocker|should-fix|nit] path:line - …` que `code-review` ya escribe
es un **carril rápido** por expresión regular; si no aparece, la prosa va al árbitro. Nunca es un
error de formato.

### Contrato del árbitro

- Cada pregunta tiene identificador estable, tipo (`noul`, `choice`, `score`), instrucciones y
  criterios en `questions/*.json`; el estado se construye por código con campos nombrados.
- `policy.json` fija por pregunta: umbral de decisión, banda de incertidumbre, acción por rama y
  si la escalada va a `judge` o directamente a gate humano. Los umbrales iniciales son
  **conjeturas declaradas**, no calibraciones: cada juicio se registra con hash del estado,
  pregunta, probabilidades, `confidence`, umbral aplicado y resultado, para calibrar después.
- Preguntas independientes sobre el mismo estado van en **una** petición.
- `usage.input_tokens`/`output_tokens` de cada llamada van al registro; el benchmark publica el
  gasto de Jev separado del gasto del modelo generativo.
- **El estado sale de la máquina.** Solo se permite para repositorios en la lista
  `external_judgment_allowed` de la política (agent-skills y el proyecto del benchmark). Para
  cualquier otro, el árbitro no se llama: la cascada empieza en `judge`.
- Errores `429`/`529`: reintento con espera exponencial acotada; si persiste, la cascada sigue
  en `judge` y el registro dice `arbiter: unavailable`.

Preguntas iniciales (identificadores para el código):

| id | tipo | estado | uso |
|---|---|---|---|
| `review.findings_block` | noul | prosa de review + resumen del diff | ¿hay un defecto que impide integrar? |
| `review.scope_complete` | noul | criterios de aceptación + diff | ¿cubre todos los criterios? |
| `qa.evidence_class` | choice | argv + salida acotada + ficheros tocados | unit / integration / simulated / live / unknown |
| `verify.claim_supported` | noul | texto de la afirmación + extracto del recibo | citation check del bundle |
| `retry.recoverable` | choice | salida del fallo + hallazgo | fix-in-place / needs-redesign / environment-failure |
| `risk.semantic_change` | score | hunk de una función | niveles de «formato o renombre» a «cambia redondeo, límites o aritmética de dinero» |

### Contrato de la cascada

1. Árbitro. Si la probabilidad cae fuera de la banda de incertidumbre, el código actúa.
2. Hoja `judge`: sesión `pi -p` nueva, sin memoria del constructor, que recibe diff, prosa y la
   pregunta, y responde en prosa; el driver la vuelve a pasar por el árbitro o aplica el carril
   rápido. Una sola vez por pregunta.
3. Gate humano con motivo literal (pregunta, probabilidades, respuesta del juez). El driver se
   detiene; el estado del run queda íntegro para reanudar tras `approve`.

La hoja constructora **nunca** participa en la cascada.

### Candidatos como configuración

Un solo driver, `--candidate`:

| id | configuración | qué prueba |
|---|---|---|
| `c0` | referencia: brazo skills-only del benchmark, sin driver | la vara: 144 s / 0,44 $ / 3 latentes |
| `c1a` | una hoja por ticket (todo `execute-ticket` en una sesión) + envoltorio: worktree, pruebas observadas, recibos, integración local | cuánto cuestan las garantías cuando el modelo no conduce |
| `c1b` | hoja constructora (implement + simplify) + hojas frescas para review y QA | cuánto cuesta y cuánto rinde la independencia real de la review |
| `c2` | `c1a` o `c1b` + árbitro en `review.findings_block`, `review.scope_complete`, `qa.evidence_class`, `verify.claim_supported`, `retry.recoverable` + cascada | ¿desaparecen los gates autofirmados sin coste apreciable? |
| `c3` | `c2` + `risk.semantic_change` por función modificada → hoja de review dirigida a las funciones de alto riesgo | ¿sube el hallazgo de latentes? |
| `c4` | hoja única como `c0` + `risk.semantic_change` + review dirigida; **sin** worktree ni integración ni árbitro de gates | el valor de Jev aislado, al coste mínimo |

`c2`/`c3` llevan sufijo de base cuando importe (`c2a`, `c2b`). Ningún candidato se ejecuta en
vivo fuera de un lote de benchmark autorizado explícitamente por el usuario; el desarrollo y las
pruebas usan una hoja de sustitución.

### Contrato con el benchmark (privado, `bench38_harness.py`)

- Brazo `driver`: `start driver <candidate>-<etiqueta>` (p. ej. `start driver c1b-r1`) lanza
  `python -B <skills>/ticket-driver/scripts/ticket_driver.py run --candidate c1b --task TASK.md
  --repo <project>` en el proyecto sembrado. Un solo comando por brazo; nada que configurar a mano.
- `collect` lee `summary.json` del run y todas las sesiones bajo `sessions/**`; publica por hoja
  y en total: tiempo (desde la sesión), coste, turnos, tokens; gasto de Jev aparte; escaladas.
- Métricas nuevas para **todos** los brazos, incluidos los ya grabados (`annotate`): **LOC
  generadas sin pruebas** (líneas añadidas en `git diff --numstat <seed>..HEAD` fuera de `tests/`
  y `docs/`) y **cobertura** (`coverage run -m unittest discover` + `coverage json` si `coverage`
  está disponible en el intérprete del benchmark; si no, `unavailable`, nunca cero).
- Un `429` del proveedor en el primer turno es **muestra nula**, no un run; se registra y se
  excluye. Mínimo **tres runs por brazo** antes de cualquier afirmación; se informa mediana y rango.
- El tiempo de cada run se mide desde la sesión, no desde el momento del `collect`
  (`elapsed_basis: session-log-mtime`, corregido el 2026-09-23).

## Invariantes semánticos

- El candidato se identifica por el árbol que el driver calcula con `git write-tree` en el
  worktree; ninguna identidad la reporta el modelo.
- Toda entrada de evidencia apunta a un recibo que el driver escribió y hasheó; el modelo no
  puede añadir evidencia.
- Ninguna etapa pasa por la palabra del constructor: `pass` exige pruebas observadas en verde y,
  en `c2`+, el juicio del árbitro o la cascada.
- La hoja constructora nunca es consultada sobre su propio trabajo.
- La autoridad humana nunca se infiere; un gate se abre con motivo literal y el driver se detiene.
- El modelo no recibe CLI ni esquema; sus únicas salidas son ficheros en el worktree y prosa.
- Cada juicio tipado queda registrado con estado (hash), pregunta, probabilidades, umbral y
  resultado; los umbrales viven en la política versionada y su hash va al `summary.json`.
- Las escaladas se registran completas: son las etiquetas gratuitas para calibrar.
- El registro es append-only; `summary.json` se escribe una vez al terminar.

## Contratos externos

- **`pi -p`**: invocado con `--session-dir` propio por hoja, `--provider/--model/--thinking` de
  la política, `cwd` = worktree, entrada estándar cerrada, salida a fichero, tiempo máximo de la
  política con terminación del árbol de procesos. La sesión `.jsonl` es la fuente de coste y
  turnos. Si el SDK de Pi ofrece una vía más económica, se evalúa en un ticket aparte; la primera
  versión usa el CLI, que es lo que el brazo skills-only ya ejecuta.
- **TypeSafe / Jev**: `POST https://api.typesafe.ai/v1/systemone`, `model: "jev-latest"`;
  clave solo en la variable de entorno `TYPESAFE_API_KEY`, jamás en ficheros ni en el registro.
  Límites documentados: 255 opciones por `choice`, 2–10 niveles por `score`. Precio por token no
  publicado en la página de la API: se registran tokens y el gasto se comprueba en la cuenta. La
  mención a OpenRouter **no está verificada**; no se asume.
- **Biblioteca reutilizada de `ticket-autopilot/scripts/autopilot`** (funciones puras, sin pasar
  por `cli.py`): `ticket_contract` (`parse_ticket_markdown`, `normalize_ticket_envelope`,
  `validate_ticket_graph`, `ticket_source_digest`), `candidate_contract.semantic_candidate`,
  `git_ops` (`create_isolated_worktree`, `remove_isolated_worktree`, `worktree_is_clean`,
  `semantic_candidate_ref`, `candidate_files`, `assert_candidate`, `run_git`),
  `command_capture.capture_command`, `terminal_integration.validate_terminal_integration_proof`,
  `artifact_audit.audit_artifacts`; y de `verification-audit/scripts`, `verification_contract`
  para la forma del bundle y `reduce_claims`. Si alguna arrastra la máquina de estados, se copia
  la función pura en el driver y se anota.
- **Instalación**: la skill nueva entra en el manifiesto de `pi_sync` como una más
  (34 → 35 owned); ninguna otra skill cambia.

## Modos de fallo

| fallo | comportamiento |
|---|---|
| hoja excede el tiempo máximo | el driver termina el árbol de procesos, registra `leaf: timeout` con la sesión parcial, y el run acaba `failed` sin candidato |
| proveedor devuelve `429` a la hoja | el run acaba `failed` con causa; el benchmark lo cuenta como muestra nula |
| hoja escribe fuera del worktree | no observable por el diff; se declara como limitación; el prompt lo prohíbe; el worktree es el `cwd` |
| hoja modifica pruebas existentes | observable (diff en `tests/`); en `c2`+ pregunta `review.findings_block` con el hunk de pruebas en el estado; la política puede exigir gate |
| árbitro `429`/`529` o sin red | cascada continúa en `judge`; el registro dice `arbiter: unavailable`; el run no se detiene |
| repositorio no permitido para juicio externo | el árbitro no se llama; cascada desde `judge` |
| integración no *fast-forward* o árbol distinto | `failed: integration`, el candidato y su rama quedan intactos para revisión humana |
| salida de pruebas con secretos | los recibos guardan hash y salida acotada; el registro no se publica fuera del repositorio |
| `summary.json` ya existe | el driver rechaza sobrescribir; se pide un `run_id` nuevo |

## Seguridad y datos

- `TYPESAFE_API_KEY` solo por entorno; el driver falla cerrado si falta y el candidato lo
  necesita, sin pedir la clave por chat.
- El estado enviado al árbitro contiene diff y prosa: solo repositorios en
  `external_judgment_allowed`. Para código de cliente el árbitro está apagado por defecto.
- Los recibos no persisten salida cruda ilimitada: tope de bytes de la política y hash del total.
- El driver no ejecuta nada fuera del worktree y del directorio del run; no toca la rama objetivo
  salvo en la integración, que es *fast-forward* o falla.

## Alternativas descartadas

- **Seguir arreglando el protocolo** (APF-09…): ocho arreglos no cambiaron la pendiente; el
  problema es la dirección de llamada, no los mensajes.
- **Inversión parcial de la evidencia** (borrador `runner-built-verification`, RBV-01..04, no
  entregado): quitaba quizá 30–50 turnos de 200; no acercaba 2 100 s a 144. Superado.
- **Mini-JSON final de la hoja** (tres campos): es la semilla del `leaf-result`; devuelve al
  modelo el papel de quien informa. Rechazado en favor de observación + árbitro.
- **Laya (encoder local)**: quita el problema de que el diff salga de la máquina y el coste por
  juicio, pero añade una pieza (322 M de parámetros, torch) y su comportamiento sobre código no está
  probado. Se registra todo lo necesario para volver a ella; hoy, Jev.
- **Prototipos desechables en `prof/`**: cinco copias divergentes de un 90 % común, sin pruebas, y
  el ganador habría que reescribirlo. Rechazado: skill en agent-skills desde el primer día.
- **Driver fino sobre el kernel como máquina de estados**: obligaría a fabricar `leaf-result`
  desde código para satisfacer validadores pensados para otro flujo. Se reutilizan solo las
  funciones puras.

## Rebanadas de implementación

Cada rebanada entra por `to-tickets → execute-ticket` inline, con PR propia. Ninguna ejecuta un
driver en vivo salvo en un lote de benchmark autorizado.

1. **S1 — Skill `ticket-driver` con `c1a` y brazo `driver` del benchmark.** Estructura de la skill
   (SKILL.md breve, `scripts/`, `prompts/`, `policy.json`), `run --candidate c1a`: worktree,
   hoja constructora `pi -p`, observación del diff y del árbol, ejecución observada de la suite
   con recibos, registro, integración local con prueba de ancestría, `summary.json`. Hoja de
   sustitución para pruebas. En el benchmark privado: brazo `driver`, métricas LOC y cobertura
   para todos los brazos, `annotate` de los runs ya grabados.
2. **S2 — `c1b`.** Hoja constructora + hojas frescas de review y QA; carril rápido de hallazgos;
   un reintento de implement ante `blocker` o pruebas en rojo; parada con estado íntegro.
3. **S3 — Árbitro y cascada (`c2`).** Cliente de Jev, `questions/`, `policy.json` con umbrales
   declarados como conjetura, `judgments.jsonl`, hoja `judge`, gate humano con motivo literal,
   lista de repositorios permitidos, gasto de Jev en el registro.
4. **S4 — Riesgo dirigido (`c3`, `c4`).** Diff por función (AST de Python en la primera versión),
   `risk.semantic_change`, hoja de review dirigida a las funciones de alto riesgo.
5. **S5 — Lote de benchmark y decisión (HITL).** Con autorización por lote: ≥ 3 runs por candidato,
   informe con mediana y rango de todas las métricas, escaladas y gasto de Jev; el usuario elige
   el camino y se abre la especificación del destino de `ticket-autopilot`.

Dependencias: S2 y S3 dependen de S1; S4 de S3; S5 de todas. S1 y la parte del benchmark pueden
avanzar en paralelo dentro del mismo ticket porque el brazo `driver` no tiene sentido sin `c1a`.

## Estrategia de verificación

- **Unitarias** (sin modelo, sin red): árbol e identidad del candidato observados; recibos con
  hash estable y salida acotada; carril rápido de hallazgos; construcción del estado del árbitro;
  ramas de la cascada con un servidor Jev falso; prueba de ancestría e integración *fast-forward*
  sobre un repositorio temporal; rechazo de sobrescritura del registro; fallo cerrado sin clave.
- **Integración con hoja de sustitución**: un ejecutable que imita `pi -p` y escribe en el
  worktree ficheros predeterminados (código, pruebas, review con hallazgos); un run completo
  `c1a`/`c1b`/`c2` sobre el repositorio sembrado del benchmark termina `integrated` o `gated`
  según el guion, con el registro esperado. Se ejecuta en CI y en local por ticket.
- **En vivo** (solo con autorización explícita): un lote de benchmark por candidato; una llamada
  de humo a Jev con una pregunta y registro de `usage` antes del primer lote de `c2`.
- **Manual**: lectura del `summary.json` y del informe del benchmark por el usuario en S5.

Ninguna de estas afirma haber corrido hasta que el ticket correspondiente lo demuestre.

## Compatibilidad y migración

Ninguna por defecto. `ticket-autopilot` no cambia; sus runs, registros y comandos siguen igual.
La skill nueva no lee ni escribe `.git/ticket-autopilot/`. No hay alias ni formatos paralelos.

## Decisiones humanas pendientes

- **Nombre de la skill.** Propuesta: `ticket-driver` (conduce un ticket por el giro de skills).
  Alternativas: `skill-loop-driver`, `afk-conductor`.
- **Autorización de gasto en Jev** para la prueba de humo y los lotes de `c2`+ (crédito gratuito
  declarado: 5 €; se comprueba con `usage`).
- **Lista `external_judgment_allowed`**: agent-skills y el proyecto del benchmark; cualquier otro
  repositorio requiere decisión explícita.
- **Cada lote de benchmark**: autorización explícita, como en q4.

## Evidencia

- Mapa de fricción con los cinco muros y la medida de regresión:
  [autopilot-protocol-friction-wayfinder.md](autopilot-protocol-friction-wayfinder.md).
- Árbol decisional con la clasificación programática / LLM / humana / híbrida y sus anclajes:
  [autopilot-decision-tree.md](autopilot-decision-tree.md).
- Registros del benchmark (privados, fuera del repositorio): `bench38-*-q*.json`, `q4_pace.py`
  (tiempos desde la sesión), `q4_classify.py` (protocolo frente a semántico), `q4-authorization.md`.
- Skill `typesafe-ai` y página de la API de TypeSafe, leídas el 2026-09-23.
