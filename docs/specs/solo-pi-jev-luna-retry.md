# Luna Yjs — retry singolo e riduzione del lavoro operatore

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-luna-retry`
- Role: `spec`
- Standalone: true

### Children
- [SPB-07: retry Luna e lavoro operatore misurato](../tickets/solo-pi-jev-luna-pilot/07-efficient-single-retry.md)

## Mandato e diagnosi
L'utente autorizza correggere il consumo del turno, poi un solo nuovo Yjs L4 Luna medium,
skills-only con budget cumulativo e storico invariato. Non autorizza altre repliche o delivery.
La finestra goal precedente 11:36:34.582–12:48:55.190 UTC contiene 17.519.912 token:
17.084.928 cacheRead, 345.846 input, 89.138 output; stima SDK $3,1483694, 110 tool call.
Il numero segnalato 17,6M non equivale a nuovi token generati o a costo del benchmark.
Causa operativa: lungo prefisso della sessione dal 28/09 ripetuto fra molte chiamate,
letture/script/audit ripetuti e più ticket; benchmark nativo precedente 396,453 s.

## Correzione del flusso, non del contatore
Usare piccoli packet di metriche/ref e helper già verificati. Accorpare ammissione,
preparazione ed esecuzione seriale in un caller per la sola cella autorizzata, non scheduler.
Non riscrivere grandi audit, ristampare file/receipt/log integrali o ripetere suite invariate.
Preservare costi/failed attempts. Preferire un vero taglio di sessione al ticket successivo.
Il tool di reset della sessione corrente non è disponibile: questa continuazione limitata
resta nella sessione esistente, dichiarata; batching non significa reset o cache eliminata.
Non creare un altro agente operatore, runner o app per fingere indipendenza/sessione fresca.
Il confronto finale misura chiamate/token/costi del segmento, non promette un risparmio noto.

## Nuova misura
Una nuova cella persistente crdt-yjs L4 con runtime congelato SPB-06 tree
56caabacc475c0fff4d3c246f6ca5876a0c5acbd. Stesse quattro richieste pubbliche canoniche,
seed/suite/question/policy/settings e openai-codex/gpt-6-luna medium. Clone LF separato,
nuovo processo/sessione del partecipante, Jev parent-isolated e judge in-process.
SPB-05 e source/prep precedenti non vengono modificati o rieseguiti. Gate/fallimenti,
candidato e delivered separati, tre dipendenze bloccate non sono tentativi del modello.
Oracle privato immutabile caller-only; nessun hidden feedback ai partecipanti.

## Ammissione e costi
Validare SPB-06, current tree/target/graph, source/SDK/skills/input/immagini. Copiare il
più recente ledger cumulativo in un nuovo store: 9 launch, 41 reservation, 7 semantic call,
310 charge già consumati. Non usare la vecchia preview con soli 8 launch. Budget originale
€1.000 e limiti restano invariati; nuova authority di scope autonoma e attribuita al messaggio
umano corrente. Refresh operatore prima di ogni reservation; SDK ≠ fattura/FX finale/hard cap.
Un futuro cambio di sessione richiede continuità esplicita dei segmenti di costo, non zero
né ricerca cieca dell'ancora originaria nel file più recente.

## Verifica e limiti
Solo packaging/serializer/source e readback causale della nuova cella, senza ripetere i 24
test SPB-06 invariati o oracle storici. Report solo aggregati, stessi vecchi confronti con
ref già verificati, confronto descrittivo non appaiato. Review/QA/audit inline shared-context,
non indipendenti. Release profile/exact-head CI/delivery/install/wiki sync restano gate.
Nessun secondo lancio per sostituire un errore e nessuna autorità derivata dal residuo.
