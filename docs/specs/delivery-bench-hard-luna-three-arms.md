# delivery-bench-hard: Luna su tre bracci, con lotto visibile dal vivo

## Artifact Graph
- Artifact ID: `artifact:delivery-bench-hard-luna-three-arms`
- Role: `spec`
- Parent: [`artifact:delivery-bench-hard-wayfinder`](delivery-bench-hard-wayfinder.md)

### Children
- [DBH-21](../tickets/delivery-bench-hard/done/21-arm-extension-profiles.md)
- [DBH-22](../tickets/delivery-bench-hard/done/22-live-lot-viewer.md)
- [DBH-23](../tickets/delivery-bench-hard/23-measure-luna-three-arms.md)
- [DBH-24](../tickets/delivery-bench-hard/done/24-judge-wait-and-request-diffs.md)

Tipo: feature con decisione di misura.

## Perché
Dopo MP13 (agent-skills `07c1f0a`, installato da pi-personal-config #65 `0dd13f5`) l'utente vuole
rimisurare «Pi nudo contro Pi con le skill aggiornate» con `gpt-6-luna`. Il braccio
`skills-only` di DBH-09 e del lotto Opus non è la configurazione reale: il runner lancia tutti i
bracci con `--no-extensions --no-context-files`, quindi riceve solo l'elenco delle skill e una
frase in coda al prompt. Mancano la regola obbligatoria (`mandatory-agent-skills.ts`) e gli
strumenti che le skill presuppongono (`code`, `todo`, plan mode, web).

Decisione dell'utente: tre bracci, per separare il contributo degli strumenti da quello delle
skill. L'utente vuole anche vedere le istanze di Pi sul proprio terminale mentre girano, non un
lotto in background.

## Fatti
- Pi 1.0.2. `--no-extensions` spegne la scoperta e le estensioni incluse (`builtin:*`), ma i
  percorsi passati con `-e` si caricano comunque; `--no-skills` spegne le skill.
- Il lotto lega già scenari, suite, autorità, comando di Pi, skill installate (DBH-17) e una sola
  estensione comune a tutti i bracci (`pi_extension`, DBH-18).
- Il tetto di spesa non è imposto dal runner: l'agente ferma il lotto prima di raggiungerlo.
- DBH-09 (Luna medium, skills del 24/09, Pi 0.87.1): catene da 4 `bare` 1/36, `skills-only`
  9/36 (Holm 0,031); catene da 12 13/72 contro 21/72, non distinguibili. Spesa di listino: catene
  da 4 0,27 $ / 0,78 $ / `autopilot` 1,65 $; catene da 12 1,85 $ / 3,90 $ / 10,72 $.
- Ogni richiesta di un braccio Pi è un processo `pi -p` che continua la sessione con
  `--continue`; la sessione è un JSONL in `<arm_dir>/sessions/`.

## Obiettivo
Un lotto `dbh-luna3` che misura, con lo stesso protocollo di DBH-09, tre bracci:

| Braccio | Skill | Estensioni caricate con `-e` | Suffisso al prompt |
|---|---|---|---|
| `bare` | no (`--no-skills`) | nessuna | nessuno |
| `pi-tools` | no (`--no-skills`) | profilo strumenti | nessuno |
| `pi-full` | sì | profilo strumenti + `mandatory-agent-skills.ts` | nessuno |

Profilo strumenti, elenco chiuso, dalla copia installata di pi-personal-config `0dd13f5`:
`extensions/pi-code-tool/index.ts` (`code`), `pi-code/extensions/todo.ts`,
`pi-code/extensions/plan-mode`, `pi-code/extensions/web.ts`.

Esclusi da tutti i bracci, perché falserebbero o sporcherebbero la misura: `memory` (memorie
personali), Telegram, pi-messenger, MCP, `subagent`, `reload-runtime`, `personal-update`,
`btw`, context7, `nonblocking-choices`, le regole di `~/.claude/rules` e i file di contesto.

`pi-full` non riceve frasi in coda: la regola obbligatoria fa quello che nella configurazione reale
fa lei. I bracci storici (`skills-only`, `autopilot`, `driver-*`) e i loro risultati restano
immutati.

## Comportamento atteso
1. **Profili legati al lotto.** `init-lot` registra per ogni braccio l'elenco delle estensioni con
   percorso e digest della cartella (come DBH-18). `load-lot` si ferma se un'estensione cambia o
   sparisce; ogni tentativo registra l'elenco con cui parte. Il campo `pi_extension` comune resta
   com'è.
2. **Argv per braccio.** `arm_argv` aggiunge un `-e` per ogni estensione del profilo del braccio,
   dopo `--no-extensions`; per `pi-tools` e `bare` aggiunge `--no-skills`.
3. **Prova prima di spendere.** Un comando `preflight` lancia per ciascun braccio una richiesta
   minima fuori dal lotto e verifica dalla sessione: elenco dei tool attivi, skill visibili o
   assenti, e che una chiamata a `code` che scrive un file vada a buon fine in `-p` senza
   approvazione umana. Se `code` resta in attesa di approvazione o fallisce, il lotto non parte.
4. **Lotto visibile.** Un viewer di sola lettura, `watch.py`:
   - `watch.py cell --lot L --cell C` segue dal vivo il JSONL della cella: messaggi, chiamate ai
     tool con argomenti abbreviati, risultati abbreviati, errori evidenziati, costo per turno;
   - `watch.py lot --lot L` mostra lo stato delle celle (richiesta corrente, giudicate,
     accettate) e la spesa di listino rispetto al tetto dell'autorità;
   - `watch.py open --lot L` apre una scheda di Windows Terminal per ogni cella in corso più una
     per lo stato; fuori da Windows stampa i comandi da lanciare.
   Il viewer non scrive nulla nel lotto né nelle sessioni. `run-lot` gira in primo piano in una
   finestra visibile.
5. **Misura.** Catene da 4 con 3 ripetizioni, poi catena da 12 alla ripetizione 1, sui tre
   scenari di DBH-09 (`lua-vm` `f90869af…`, `sql-engine` `5b029cb4…`, `crdt-yjs` `be281cb4…`),
   `openai-codex/gpt-6-luna` medium, tetto di 5400 s per richiesta. Una ripetizione intera alla
   volta (9 celle in parallelo), così i bracci appaiati girano nelle stesse condizioni del
   fornitore.
6. **Report.** `docs/research/delivery-bench-hard-luna3.md`: tre confronti appaiati con la regola
   di TBA-03 (`pi-tools`/`bare`, `pi-full`/`pi-tools`, `pi-full`/`bare`), spesa, guasti, e una
   nota sulle differenze rispetto a DBH-09 (Pi 1.0.2, skill `07c1f0a`, bracci diversi).

## Invarianti
- Skill installate e profili restano gli stessi per tutto il lotto: niente `update:personal`, né
  cambi al pin, né modifiche alle estensioni finché il lotto non è chiuso.
- I lotti `dbh`, `dbh-drivers*`, `dbh-opus` e `dbh-sonnet` non si modificano né si rilanciano.
- Il runner si sposta solo fra due `run-lot`; il preflight non conta come tentativo del lotto.
- Lane skills-only: nessun runner di ticket-autopilot, scheduler o grant.

## Spesa e autorità
- Stima con tre bracci e la regola obbligatoria, che spinge `pi-full` verso `to-spec` →
  `to-tickets` → `execute-ticket`: circa 11–19 $ di listino (`bare` ~2 $, `pi-tools` ~4 $,
  `pi-full` fra ~5 $ come `skills-only` e ~12 $ come `autopilot`). Non ancora misurata.
- Tetto deciso dall'utente: «metti anche 50 euro». Pi riporta USD di listino, quindi il tetto
  operativo è 50 $ di listino, che resta entro 50 € a qualunque cambio EUR/USD pari o superiore
  a 1,0.
- Le richieste passano dall'abbonamento ChatGPT via OAuth: gli USD sono una stima di listino di
  Pi, non una fattura.
- Prima di `init-lot` serve un file d'autorità nuovo con bracci, scenari, ripetizioni, modello e
  tetto confermati dall'utente. Se la spesa proiettata supera il tetto, l'agente si ferma prima.

## Fallimenti previsti
- `code` o plan mode in attesa di input umano in `-p`: il preflight lo rileva; si corregge la
  configurazione del braccio, non si toglie la verifica.
- Estensione che fallisce al caricamento: il preflight vede il tool mancante e il lotto non parte.
- Limiti di frequenza con 9 celle: li coprono i retry d'infrastruttura esistenti (DBH-14/15); se
  i guasti si ripetono si scende a meno celle fra due `run-lot`.

## Fuori ambito
- La TUI interattiva di Pi dentro i bracci: renderebbe il lotto non confrontabile.
- pi-messenger dentro i bracci: aggiungerebbe tool che gli altri bracci non hanno.
- Nuove ripetizioni o modelli oltre quanto sopra.

## Fette
1. Profili per braccio legati al lotto: `pi-tools` e `pi-full`, digest, controllo in
   `load-lot`, argv, registrazione per tentativo; comando `preflight`. Test unitari nel runner.
2. Viewer `watch.py` (`cell`, `lot`, `open`) di sola lettura, con test su JSONL di esempio.
3. Misura e report: autorità, preflight reale, `init-lot`, catene da 4 e da 12, giudizio, report.
   Dipende da 1 e 2.

## Verifica
- Unitari: argv per braccio, digest e rifiuto di un'estensione cambiata, rendering del viewer su
  JSONL sintetici (messaggio, tool call, errore, costo), nessuna scrittura del viewer.
- Sistema: preflight reale sui tre bracci prima della misura (costo trascurabile).
- Live: il lotto stesso; nessuna affermazione sui risultati prima del giudizio.

## Decisioni dell'utente
- Tre bracci `bare`, `pi-tools`, `pi-full` («ok mi piace di piu», dopo la spiegazione).
- Tetto 50 € («metti anche 50 euro»), 9 celle in parallelo («Va bene facciamo 9 celle»).
- Lotto visibile sul terminale, non in background.
