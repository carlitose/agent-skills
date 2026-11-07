# Requisiti e piano su Pi-full — confronto con i bracci già misurati

## Artifact Graph
- Artifact ID: `artifact:requirements-plan-execution-benchmark`
- Role: `research`
- Parent: [Esecuzione da requisiti e piano](../specs/requirements-plan-execution.md)

## Risultato osservato
Il lotto `plx-luna1`, completato il 2026-11-07, ha **36/36 giudizi validi**, nove celle,
**30/36 consegne accettate** e nessuna cella invalidata. Il nuovo ingresso mantiene il
totale del Pi-full precedente con una quota SDK nota inferiore del **32,6%**. È un confronto
con controlli conservati, non un nuovo A/B simultaneo: non dimostra causalità o non-inferiorità.

## Protocollo e provenienza
- Solo il nuovo candidato, tree `b2a7db18f1ec816aff6065f8f6dd41cca15c58c2`, 2.644 file
  materializzati esattamente dai blob Git; nessuna installazione personale per misurarlo.
- `openai-codex/gpt-6-luna`, thinking `medium`, Pi 1.5.0; tre scenari, quattro richieste
  concatenate e tre ripetizioni. Cap 5.400 secondi per richiesta, quattro celle contemporanee.
- Stesso profilo strumenti e stessi nomi delle 40 skill pubblicizzate del vecchio Pi-full;
  nuova policy e skill del candidato caricate da percorsi espliciti, senza discovery personale.
- Scenari/suite/request originali del commit privato `27cd388dcf408525ec92c10eb155c239bd085039`.
  I 144 giudizi del lotto `spl-luna1` sono stati verificati invariati tramite hash, non rilanciati.
- Controlli: [report Superpowers/Luna](delivery-bench-superpowers-luna-results.md).
  Pi nudo non ha `/goal`; gli altri bracci lo hanno. Non si isola quindi il solo contributo skill.

## Confronto completo

| Variante | Accettati | SDK quota nota (USD) | Ore-agent quota nota |
|---|---:|---:|---:|
| Pi nudo precedente | 1/36 | 0.229738 | 1.30 |
| Pi-tools precedente | 30/36 | 2.862951 | 10.73 |
| Pi-full precedente | 30/36 | 5.071227 | 15.64 |
| Pi-Superpowers precedente | 29/36 | 3.904384 | 11.90 |
| **Pi-full requisiti+piano** | **30/36** | **3.419855** | **10.44** |

Le quote includono la compaction una sola volta e i parziali storici noti. Pi-tools resta
il più economico tra i bracci a 30/36; il nuovo candidato costa il 19,5% in più di Pi-tools,
il 12,4% in meno di Superpowers e il 32,6% in meno del vecchio Full.

| Scenario | Full precedente | Requisiti+piano |
|---|---:|---:|
| CRDT/Yjs | 9/12 | 10/12 |
| Lua VM | 10/12 | 10/12 |
| SQL engine | 11/12 | 10/12 |

Il pareggio complessivo bilancia quattro posizioni guadagnate e quattro perse; non sono
le medesime consegne. McNemar descrittivo: p=1,0. Robustezza finale 80/99 in entrambi,
zero regressioni finali rilevate in entrambi, invarianti finali mai stabiliti 11 → 9.
Nessuna conclusione generale di equivalenza segue da questo campione.

## Consumo e comportamento osservato
- Tool call nei tentativi consolidati: 4.401 → 3.282, **-25,4%**.
- Token output nello stesso perimetro: 1.849.201 → 1.053.517, **-43,0%**.
  Questi due conteggi non aggiungono le tracce parziali storiche, rendicontate separatamente.
- Nuovo costo: assistant 3.330186 USD + compaction 0.089669 USD = 3.419855 USD.
  Tutti i 13 nuovi eventi di compaction hanno un costo esplicito; il precedente Full ne ha 22.
- Il vecchio Full include 0.055802 USD assistant di parziale conservato. Escludendolo,
  il delta dei tentativi consolidati più compaction è -31,8%.
- I due preflight aggiungono separatamente 0.017005 USD noti: misura più preflight 3.436860 USD.
  Il primo è conservato come respinto per catalogo; il secondo passa catalogo/tool/routing/scrittura.
- Processo principale 11.054,741 secondi, circa 3 h 04 min 15 s. Le ore-agent sono somme
  delle durate delle richieste parallele, non la latenza del lotto. Nessun nuovo timeout
  o retry infrastrutturale; un tentativo agent per posizione, 35 goal raggiunti e uno assente.
- Le tracce hanno 55 occorrenze del riferimento `execute-ticket/references/plan-execution.md`
  negli argomenti dei tool, nessuna di `to-spec/SKILL.md` o `to-tickets/SKILL.md`.
  Sono osservazioni di trace, non prova che non sia mai stato scritto un documento canonico.

## Limiti ed errori conservati
**Mancano i 36 diff per richiesta:** il harness ha registrato `git cat-file
--batch-check=%(objectname)` con exit 128. I 36 giudizi sono validi, gli assi coincidono
con quelli salvati e gli alberi sono rimasti invariati durante il giudizio, ma l'audit
richiesta-per-richiesta dei sorgenti/documenti non è disponibile. Non si inventano diff e
non si ripete il benchmark per nascondere il problema.

L'immagine Yjs è stata ricostruita dalla medesima ricetta, con base fissata per digest e
lockfile originale, ma ha un nuovo image ID. I nomi delle skill esterne sono allineati;
i loro contenuti completi storici non erano indipendentemente legati dal vecchio preflight.
I goal dei preflight si sono fermati nella fixture artificiale: non sono prove di successo prodotto.

USD SDK sono **stime parziali, non fatture**. Restano ignoti goal evaluator, tail storici
non persistiti, consumo del coordinatore e fatturazione reale; ignoto non significa zero.
Nessun claim di release, produzione o attivazione della sessione deriva da questo report.

## Evidenze
Il lotto esterno è `bench-lots/plx-luna-1`; l'evidence root separato è
`bench-evidence/plx-luna-1`, con `results.json`, `analyze.py`, `bindings.json`,
`launch-admission.json`, `run-result.json` e hash di tutti i giudizi. Sono riferimenti
ad artefatti locali conservati, non file pubblicati o sorgenti privati copiati qui.
Le osservazioni conservano l'identità dei candidati realmente misurati.
