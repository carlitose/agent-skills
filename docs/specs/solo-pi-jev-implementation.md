# Solo Pi + Jev — contratto implementativo confermato

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-implementation`
- Role: `spec`
- Parent: [Wayfinder](solo-pi-jev-wayfinder.md)

### Children
- [SPC-01: sessione persistente e accounting](../tickets/solo-pi-jev-implementation/01-persistent-session.md)
- [SPC-02: catena, prove e gate](../tickets/solo-pi-jev-implementation/02-observed-chain.md)
- [SPC-03: completion judge in-process](../tickets/solo-pi-jev-implementation/03-inprocess-judge.md)

## Type and Status
Feature/architecture spec derivata dalle scelte SPJ-02/03/04 confermate e dalla prova
SPJ-05, handoff locale `C:/dbench/tmp/spj05-handoff.json`, tree `3d8a38a1...`.
Nessuna nuova decisione umana necessaria. Implementazione seriale in tracer bullet;
non è un'autorizzazione live, benchmark, installazione o delivery.

## Goal and Boundaries
Uno script Python guida ticket canonici nello stesso worktree separato e nello stesso
processo/sessione Pi. Builder/review/analysis sono turni del Pi principale; judge è una
completion distinta nello stesso processo, con evidenze del candidato e senza tools o
cronologia builder. Non usare subagent, loop /goal o una nuova foglia per ruolo.

Fonte normativa: [fallback](solo-pi-jev-uncertainty-decision.md), [review](solo-pi-jev-review-decision.md),
[ownership](solo-pi-jev-script-ownership-decision.md), [prova e limiti](../research/solo-pi-jev-chain-prototype.md).
Lavoro locale verificato non è integrazione o delivery remoto. Non avviare questo candidato
per consegnare questi ticket: corsia skills-only inline, non nuovo runner/scheduler.

## Design Boundary
Tre prospettive inline, non indipendenti: SDK TypeScript unico nasconderebbe bene processi
ma cambierebbe lo script Python e il trasporto raccomandato; nuove CLI per turno avrebbero
un'interfaccia corta ma violerebbero continuità; Python owner + RPC persistente + completion
extension conserva linguaggio e separa la vera dipendenza esterna. Scelta quest'ultima.

Il caller conosce una sessione di catena e ticket pronti; l'owner nasconde framing, attesa,
cursori, accounting, stop/resume. Seam al processo controllato e alla completion/provider,
non un'interfaccia per ogni helper. Worktree/prove e policy stanno nel controller della
catena, non nella prosa del modello. Non clonare Verification Record o Autopilot ledger.

## SPC-01 — Sessione e facts
Modulo `ticket-driver/scripts/chain_session.py`: un owner del processo RPC per la catena,
non CLI/scheduler. API `ChainSession(argv, cwd, store, ...)`, `prompt(message)`, `sync()`,
`resume(...)`, `close()`; callers non gestiscono una foglia per ruolo. Constructor/start
non eseguiti nella consegna se non su peer fake esplicitamente forniti dai test.

- argv esplicito configurato dal caller; no default modello/provider ricavato dalle copie
  storiche. Rifiutare print/JSON/no-session per questa modalità; cwd e store persistenti.
- RPC LF byte framing, CRLF ammesso, U+2028/U+2029 non separatori; lettori stdout/stderr
  attivi, cap e deadline; id correlation, un prompt alla volta. Non parsing stderr.
- Prompt response accepted non PASS: started attende settled anche se precedente alla
  response; handled non richiede settled ma richiede idle/stato e output specifico;
  queued non è il turno richiesto. Error/aborted/length/deferred non sono output successo.
- Identità session ID/file, process PID e epoch; idle senza streaming/compacting/pending.
  Cambi inattesi fermano il caller, non nuova sessione automatica.
- get_entries append-order e cursore; ledger di sole charge/facts persistito atomicamente
  insieme al cursore, non scheduler state. Entry ID con contenuto diverso è errore.
  Native message usage, compaction, branch_summary e usage; kind ignoto conservato.
- Usage annidata judge separata con call ID; se già rappresentata nel registro nativo non
  sommare due volte. Pi estimates non fattura; assenza/incomplete usage ignota, non zero.
- Chiave Jev rimossa da child env senza copiarla in prompt/log. Non alterare credenziali
  esistenti del parent o usare un provider diverso per aggirare auth.
- Resume soltanto dopo morte osservata, checkpoint completo coerente e autorizzazione/
  budget validi; stessa storia, nuova epoch contata. Timeout non prova morte; no overlap.

Fonti primarie Pi 0.99.1 installate: docs/rpc.md, rpc-commands.md, json.md, sdk.md,
extensions.md e relativi session/message contracts; esempi SDK/RPC e dichiarazioni.
Context7 `/earendil-works/pi/v0.99.0` consultato, ma versione installata prevale.

## SPC-02 — Prove e controllo della catena
Modulo controller nuovo, senza sostituire copie storiche o aggiungere shim. Ingress:
Ticket Envelope/body/ref canonici, CandidateRef reali, ticket ordinati pronti, worktree
posseduto, permessi/budget e backend osservabili. Non normalizzare task legacy per inferenza.

Freeze reale e process-owned test receipts; inventario completo. High/uncertain/unclassified
seleziona review principale solo findings. Coverage globale resta necessaria. Soglie
0,2/0,8/0,75/2,5; Jev max 3 solo 429/529, non re-query di uncertain/no. Typed question,
contract/state digest e candidato sono bindings dello script, non attestate dal modello.

Semantica uncertain/unavailable/malformed/bound/vietato: judge solo con distinto permesso
per destinatario/dati e prove sufficienti; massimo uno per domanda/candidato. Negativo
deciso non aggirabile. Judge incerto/errore -> analisi condivisa e gate umano. Rischio
indecidibile -> review, non judge per funzione o basso rischio.

Qualità: massimo 3 fallimenti finali per ticket, non per ruolo. Non reset da fix/reentry/
resume; test interni builder non contano automaticamente come fallimento finale. Nuove
freeze/prove dopo fix. Ticket fallito preservato, dipendenti attendono; indipendenti da
ultimo albero valido con ripristino osservato. Stato globale/budget/ambiente dubbio ferma
anche indipendenti. Mutation/drift conservati e riconciliati senza riscrivere originali;
cache realmente classificate non sono prodotto. Gate specifico con cause, consumo e refs.

Completed-local consente uso nella copia e nel suo scope; no ticket move, commit/main,
push/PR/merge o certificazione release. Applicazione originale è operazione separata
con autorità, target pulito/fresco, albero e readback. Nessuna policy provider nuova.

## SPC-03 — Bridge del judge
Extension opt-in caricata soltanto dall'argv autorizzato del futuro caller, non installata
né attivata globalmente. Registrare command, non tool autonomamente richiamabile dal builder.
Command handler verifica idle, payload/candidato/question bindings, permesso e budget;
una sola completion tool-less, modello configurato esatto, nessun fuzzy fallback.

ModelRuntime.completeSimple con context nuovo (system, una richiesta contenente domanda,
criteri e prove), niente builder transcript/tools. Appended custom entry conserva receipt
non model-visible con call ID, bindings, modello, text/stop/usage o errore sanitizzato.
Persist metadata nativi non sono nuovi JSON che il modello deve inventare. Risposta valida
solo tramite parser finale canonico Answer, non parser permissivo /goal. Native prompt
handled e custom receipt sono distinti da un normale agent run.

## Verification and Non-goals
Ogni ticket TDD RED -> GREEN con sostituti causalmente controllati; niente test del
prototipo rinominati come produzione. Peer nativo-shaped per conformance owned adapter,
repo sintetico per workflow e backend completion stub per bridge. Esperimenti live,
auth/model binding reale, qualità, costi e robustezza ambientale restano gate separati.

Per futuro code PR selezionare profilo obbligatorio secondo contratto repo; CI sull'head
esatto e delivery authority aperti. Nessun benchmark, harness update, dati/copie storici,
Sonnet VOID, install/pin/reload, GC, wiki o compatibilità legacy aggiuntiva. Nessuna promessa
che un solo processo riduca spesa. La prima tracer bullet è SPC-01, non l'intero refactoring.
