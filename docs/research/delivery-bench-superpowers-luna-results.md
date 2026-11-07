# Superpowers su Pi con Luna medium — risultati del lotto contemporaneo

## Artifact Graph
- Artifact ID: `artifact:delivery-bench-superpowers-luna-results`
- Role: `research`
- Parent: [SPL-02 — Misura e report](../tickets/delivery-bench-superpowers-luna/02-measure-and-report.md)

## Stato e sintesi
Lotto `spl-luna1`, completato il 2026-11-07: **144/144 posizioni giudicate**, 36 celle,
nessuna cella invalidata e nessun errore residuo. «Giudicata» non significa «accettata».

**Superpowers non ha aumentato l'accettazione totale in questo lotto:** 29/36 contro
30/36 sia di Pi-tools sia di Pi-full. La regola appaiata esistente non distingue questi tre
bracci nell'accettazione; sceglie Pi-tools per il pareggio al braccio più semplice, non
per una superiorità statisticamente dimostrata sugli altri due. Pi-full e Superpowers
superano più controlli latenti di Pi-tools: è un compromesso, non un unico punteggio globale.

## Protocollo
- `openai-codex/gpt-6-luna`, thinking `medium`, per tutti i bracci; Pi gestito 1.5.0.
- Tre scenari originali: `lua-vm`, `sql-engine`, `crdt-yjs`; quattro richieste concatenate,
  tre ripetizioni per braccio/scenario: 4 × 3 × 3 × 4 = 144 posizioni.
- Stesso lotto e runner di benchmark esistente, fino a quattro celle in parallelo;
  cap di richiesta 5.400 s, cap di catena predefinito 21.600 s, nessun tetto economico imposto.
- Pi-tools, Pi-full e Pi-Superpowers usano anche `/goal`; Pi nudo no. Il confronto con
  Pi nudo non isola quindi l'effetto delle sole skill o dei soli strumenti.
- Superpowers è misurato **su Pi**, con il fallback seriale upstream e senza pacchetti di
  subagent aggiuntivi; non è una misura di Claude Code o del workflow multi-agent upstream.
- Il giudice è la suite nascosta originale. Nessun giudice generativo sostituisce i controlli;
  Jev non è stato usato. Non si mescolano dati di lotti storici o modelli diversi.

## Accettazione — richieste accettate / giudicate
Una richiesta è accettata quando supera tutti i controlli di accettazione previsti per
quella richiesta; robustezza e regressioni restano dimensioni separate.

| Configurazione | Yjs | Lua | SQL | Totale |
|---|---:|---:|---:|---:|
| Pi nudo | 0/12 | 1/12 | 0/12 | 1/36 (2.8%) |
| Pi-tools | 9/12 | 9/12 | 12/12 | 30/36 (83.3%) |
| Pi-full | 9/12 | 10/12 | 11/12 | 30/36 (83.3%) |
| Pi-Superpowers | 10/12 | 10/12 | 9/12 | 29/36 (80.6%) |

## Cinque dimensioni
Robustezza e compass sono letti nello **stato finale di ciascuna catena**, non sommati
quattro volte. «Mai stabilite» distingue condizioni mai raggiunte da regressioni di
condizioni precedentemente dimostrate. Non equivale a una regressione temporanea intermedia.

| Configurazione | Latenti superati | Regressioni finali | Inv. mai stabilite | SDK quota nota (USD) | Ore agente quota nota | Compaction | Timeout |
|---|---:|---:|---:|---:|---:|---:|---:|
| Pi nudo | 25/99 | 1 | 80/126 | 0.230 | 1.30 | 0 | 0 |
| Pi-tools | 77/99 | 0 | 9/126 | 2.863 | 10.73 | 6 | 1 |
| Pi-full | 80/99 | 0 | 11/126 | 5.071 | 15.64 | 22 | 1 |
| Pi-Superpowers | 80/99 | 0 | 8/126 | 3.904 | 11.90 | 10 | 1 |

Le suite riportano **zero trappole misurabili**: nessuna conclusione sulla resistenza a
trappole si può ricavare da questi zeri. Le tre configurazioni strutturate non presentano
regressioni finali misurate, ma differiscono nelle condizioni mai stabilite e nella robustezza.
Le differenze sui controlli latenti sono descrittive: qui non è stato aggiunto un test
statistico separato su questa dimensione.

## Confronto appaiato
Output dell'implementazione esistente di McNemar esatto con correzione Holm, base `pi-tools`,
36 posizioni allineate per confronto. La regola TBA-03 richiede anche una differenza assoluta
superiore a tre richieste; a parità preferisce il braccio più semplice.

| Confronto contro Pi-tools | Solo altro | Solo Pi-tools | Delta accettate | p esatto | p Holm | Regola |
|---|---:|---:|---:|---:|---:|---|
| Pi nudo | 1 | 30 | -29 | 2.98023e-08 | 8.9407e-08 | worse |
| Pi-full | 2 | 2 | +0 | 1 | 1 | indistinguishable |
| Pi-Superpowers | 2 | 3 | -1 | 1 | 1 | indistinguishable |

«Indistinguishable» indica che questa regola non rileva una differenza, non una prova di
equivalenza. Tre ripetizioni e richieste dipendenti dentro una catena non autorizzano
conclusioni universali sui framework. Non sono state aggiunte ripetizioni per cambiare l'esito.

## Costi e tempi: cosa è noto e cosa no
Le cifre sono **stime SDK registrate**, non fatture o costo totale del servizio.
Nelle tabelle il separatore decimale è il punto.
La tabella include i parziali persistiti dei due tentativi interrotti sul disco pieno,
che il riepilogo nativo non conosce; non assume che i placeholder zero del recupero siano
consumi effettivamente nulli. Restano ignoti eventuali tail non persistiti, costi del
goal evaluator e fatturazione reale. I costi del coordinatore non sono nel confronto.

Quota assistant SDK nota del lotto: **11.802306 USD**, inclusi 0,135688 USD persistiti nei due tentativi interrotti.
La compaction è registrata separatamente dal riepilogo assistant: aggiunge **0.265994 USD**,
inclusi 0.006630 USD del parziale Pi-tools. Quota SDK nota del lotto, compaction inclusa una sola volta:
**12.068300 USD**. La tabella conta anche quell'evento parziale (sei compaction Pi-tools).
I preflight, separati dai punteggi, aggiungono **0,029767 USD SDK** (originale più recupero, fallimento incluso).
Quota nota combinata: **12.098067 USD SDK**; costi mancanti non sono zero.
Questa correzione di aggregazione non cambia giudizi o tentativi e non rilancia il lotto.

Le ore per braccio sono la **somma delle durate agente registrate** nelle sue nove catene,
con i minimi temporali persistiti dei due tentativi interrotti. Non sono latenza wall-clock
dell'intero esperimento e non includono tutte le operazioni di preparazione/giudizio.

- Intervallo osservato nel ledger: `2026-11-06T13:49:07Z` → `2026-11-07T05:45:06Z`,
  **15 h 55 min 59 s**, incluse le pause fra le riprese. Non è il tempo dalla prima richiesta dell'utente.
- Somma delle durate dei tre comandi `run-lot`: **50.151,282 s**, circa 13 h 55 min 51 s;
  esclude le pause fra comandi ed è distinta dalla somma parallela delle durate dei bracci.

## Interruzioni conservate e recupero
1. Il primo comando è terminato con `WinError 112`/disco pieno. L'origine del precedente
   consumo di spazio non è stata identificata; non si attribuisce per deduzione al benchmark.
   Sono stati preservati 72 giudizi e le due sessioni interrotte, con costi e durate parziali.
2. La prima ripresa ha aggiunto risultati fino a 99 giudizi. Un aggiornamento di `pi-code-tool`
   durante l'esecuzione ha attivato il guard del contenuto: 12 celle sono uscite con errore.
   Questi errori infrastrutturali non sono stati trasformati in insuccessi del modello.
3. L'utente ha approvato il recupero isolato. SPL-03 ha aggiunto un sidecar verificato al
   runner: versione precedente ricostruita con digest identico, nessun rollback di Pi personale,
   manifesto originale immutato, log e giudizi precedenti conservati. I 99 giudizi sono stati
   verificati invariati prima della seconda ripresa e nel controllo finale.
4. La seconda ripresa ha completato solo le 45 posizioni mancanti. Il ledger contiene
   esattamente 144 eventi `judged`, senza replay dei giudizi conclusi. I tre `infra:host`
   comprendono due interruzioni con consumo parziale e un guard prima dell'avvio del modello.
   Sono conservate anche sette attese/riprove del giudice; non resta alcuna posizione non giudicata.
5. Il preflight mirato della copia ha prima raggiunto il timeout di 180 s scelto dall'assistente
   pur mostrando strumenti e scrittura. Il tentativo è conservato; quello al limite standard
   originario di 600 s è passato in 41,219 s. Non è stato rigiocato il preflight completo dei quattro bracci.

## Provenienza e limiti
- Scenari privati: commit `27cd388dcf408525ec92c10eb155c239bd085039`, esportazione dei byte Git.
- Superpowers: commit `22f0b463e7a5e579904dd6211a520321035526f7`, versione 7.0.2.
- Controller iniziale: albero `9cf702edb4ce55c625883db43eeba768deb58ee1`; recupero SPL-03:
  `3162a6ca95e9007b051399d91570c2ad0d7204bf`. Il delta cambia solo gli indirizzi verificati,
  non criteri, modello, prompt, profili o cap. Le osservazioni conservano la loro provenienza.
- Cartella originale `pi-code-tool`: SHA-256
  `5928b0c1ce16b89fc003392b98b1a9d6bd8f35508acd1ac36c3985ccd23c9f76`, 13 file con CRLF.
- L'immagine SQL inizialmente preparata era stata rimossa. È stata ricostruita e verificata
  prima di qualunque posizione SQL; tutte le posizioni SQL del lotto usano quel binding.
  GCC è rimasto sul binding iniziale; Yjs era già completo quando la sua immagine non era più disponibile.
  Gli ID sono conservati negli admission: non si pretende un ID registrato per ogni singolo giudizio.
- Ogni giudizio finale conserva l'impronta della suite congelata, assi coerenti col record
  della richiesta e albero del progetto invariato dal giudice. Questo non è una certificazione
  di sandbox ostile né una verifica indipendente del contenuto delle suite.
- Il preflight prova visibilità/caricamento e scrittura, non che il modello abbia seguito
  tutta la metodologia Superpowers. La review è inline/shared-context, non indipendente.
- Il profilo quick conserva il fallimento Node preesistente sui CRLF: non è dichiarato PASS.
  Nessuna conclusione di release, integrazione, pubblicazione o production readiness.

## Evidenze locali e riproduzione della sola aggregazione
Evidenze private sull'host: `C:/Users/rdpuser/bench-evidence/spl-luna-1/`.
`final/native-profile.json` e `final/native-report.md` sono prodotti dal reporter originale;
`final/integrity.json` lega i 144 record e i rispettivi giudizi ai loro hash.
`final/lot-snapshot` è stato verificato identico al lotto finale. `recovery-01` e `recovery-02`
conservano fallimenti, partial usage, autorità, preflight, modifiche di binding e audit.
Qui si registrano nel solo checkout locale aggregati, non nomi dei controlli nascosti o sorgenti private.

```bash
python -B benchmarks/delivery-bench/profile_report.py --lot PATH_TO_EXISTING_LOT --through 4 --base pi-tools
```

Sullo stesso host il comando legge gli artefatti e i riferimenti ai giudizi: **non rilancia modelli o giudici**.
Al termine di questa misura non erano state eseguite installazione, modifica di Pi personale,
commit/push/PR/merge o pubblicazione esterna; la successiva delivery richiede il suo mandato separato.
Il [benchmark requisiti+piano](requirements-plan-execution-benchmark.md) aggiunge solo il nuovo
braccio: i 144 giudizi qui descritti restano le osservazioni originali, non controlli rilanciati.

Gli archivi raw conservano percorsi assoluti originali; per spostarli su un altro host
serve risolvere quei riferimenti. Il JSON aggregato resta disponibile separatamente.
