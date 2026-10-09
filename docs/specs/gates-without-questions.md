# Gate senza domande inutili

## Artifact Graph
- Artifact ID: `artifact:gates-without-questions`
- Role: `spec`
- Standalone: true

### Children
- [GQ-01](../tickets/gates-without-questions/done/01-default-gates.md)

## Type
Decision. Cambia la decisione 1 di [explicit-gates](explicit-gates.md).

## Problem
Dal 6 ottobre `to-spec` impone di chiedere all'utente tutte le gate in un solo giro prima di
scrivere la spec: cos'è un tentativo, budget e tempo, tentativi massimi, approvazioni, versione.
`to-tickets` chiede «any missing one before emitting».

Nel lotto `dbh-vague` (richieste vaghe con utente simulato, 2026-10-08):
- 28 delle 37 domande di `pi-full` riguardano il processo (tentativi, gate, ticket), non il lavoro;
- la risposta tipica è «No lo sé, decide tú»;
- un agente si è fermato su un limite che si era dato da solo: «El ticket fijó máximo 3
  intentos y ya llegué al 3/3. ¿Autorizas un intento 4?».

`pi-full` consegna 5/36 contro 7/36 dei bracci senza queste skill, e costa il doppio. L'utente le
chiama «domande idiote» (2026-10-09) e chiede di correggerle subito.

## Decision
Decisione dell'utente, 2026-10-09:

1. `## Gates` resta in ogni spec e ticket. Resta anche la ricerca dei blocchi reali prima di
   scrivere (pin di versione, budget cumulativi, controlli di approvazione): era la causa del
   problema di EG-01.
2. Una gate si riempie con le parole dell'utente o con quello che la ricerca ha trovato.
   Altrimenti prende il suo default, **senza chiedere**:
   - tentativo: il lavoro fino al passaggio di consegne;
   - budget, tempo e tentativi massimi: nessuno fissato;
   - approvazioni: solo quelle già date. Una che il lavoro richiede e manca (merge, deploy,
     pubblicazione, spesa esterna) è `open`;
   - versione esatta: nessuna, salvo quella nominata dall'utente.
3. Si chiede all'utente, una volta, solo per un'approvazione `open` che il lavoro richiede
   davvero, o per un blocco trovato che contrasta con la richiesta. Modifiche e test locali non
   ne hanno mai bisogno.
4. Un limite scelto dall'agente non è una gate: l'agente non si ferma su di esso e non chiede di
   estenderlo.

Restano uguali: per tentativo (decisione 2 di explicit-gates) e nessun legame di versione
(decisione 3).

## Non-goals
- Il runner `ticket-autopilot`, `/goal`, il banco `delivery-bench`.
- Le domande sul lavoro (contratto, comportamento): restano quando cambiano davvero il risultato.

## Verification
- Un test di testo delle skill: `to-spec` dà i default senza chiedere e vieta di fermarsi su un
  limite proprio; `to-tickets` non chiede più le gate mancanti.
- Limiti di righe dei file (`scripts/check_file_limits.py`) e test delle skill.
- Misura dopo l'installazione, nel primo lotto con `pi-full`: le domande sul processo, attese
  vicine a zero.

## Gates
- **Attempt:** il lavoro fino alla merge. **Budget, tempo, tentativi massimi:** nessuno fissato.
- **Approvals:** merge con CI verde da parte dell'agente; poi pin in `pi-personal-config`,
  `update:personal` e reload (regola di sincronizzazione dopo ogni passo integrato). Nessuna
  spesa esterna né pubblicazione.
- **Exact version:** nessuna.
- **Existing blocks:** nessun lotto in corso (cercato: `dbh-vague` finito 2026-10-08T23:54Z,
  nessun `run-lot` attivo). Il pin delle skill installate cambia solo con una PR in
  `pi-personal-config` (memoria `installed-skills-reviewed-pin`).
