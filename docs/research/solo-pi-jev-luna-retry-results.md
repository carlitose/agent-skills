# Retry Luna Yjs — risultato e lavoro operatore

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-luna-retry-results`
- Role: `research`
- Parent: [SPB-07](../tickets/solo-pi-jev-luna-pilot/07-efficient-single-retry.md)

## Unico nuovo tentativo osservato
Runtime SPB-06 `56caabacc475c0fff4d3c246f6ca5876a0c5acbd`, stesso Luna medium,
Yjs e quattro richieste pubbliche canoniche. Un processo/sessione nativi nuovi, chiusi
con exit 0; **561,375 s** di invocazione misurata, oracle incluso. Nessun replay.

| Richiesta | Tentata | Stato | Delivered accettato |
|---|---|---|---|
| R1 | sì | failed dopo tre tentativi di qualità | no |
| R2 | no | dependency-blocked | no |
| R3 | no | dependency-blocked | no |
| R4 | no | dependency-blocked | no |

**0/4 delivered accettati, una richiesta tentata e tre non tentate.** Non sono quattro
fallimenti del modello. L'ultimo candidato R1 è conservato e oracle-rejected separatamente;
i delivered restano sul tree valido iniziale. Oracle immutabili/caller-only, nessun hidden
feedback. Exit 0 del processo non certifica il prodotto o una catena riuscita.

## Percorso reale, distinto dal vecchio gate
Tre test pubblici attribuiti a tre candidati: exit **2, 0, 0**, senza capture failure.
Il review finale è parsato e contiene **uno should-fix, zero blocker e zero nit**. Il
contratto attuale richiede review clean, non distingue should-fix come approvazione: perciò
il controller consuma il fallimento di qualità e non chiama la decisione esterna.
Non cambiamo questo contratto o inferiamo una nuova soglia da un solo risultato.

Il digest dello stato/domanda dell'ultimo candidato è stato ricostruito esattamente:
input coverage **25.622 B**, dentro il bound **65.536 B**. Il precedente gate da 102.108 B
non è il meccanismo di questo arresto. **Zero chiamate Jev/judge**: test verdi più review
non clean rendono l'evidenza insufficiente per il port. Non è un provider outage, un nuovo
input-bound gate o esaurimento del denaro. Il source fix non prova una decisione live
Jev riuscita; l'oracle candidato resta indipendentemente negativo.

## Confronto storico descrittivo, sempre Yjs Luna
| Cella | Accettati | Richieste tentate / non tentate |
|---|---:|---:|
| SPB-02 bare | 1/4 | 4 / 0 |
| SPB-02 persistente | 0/4 | 1 / 3 |
| SPB-05 corretto prima del fix coverage | 0/4 | 1 / 3 |
| SPB-07 singolo retry su SPB-06 | 0/4 | 1 / 3 |

Nessun miglioramento di consegna dimostrato. Il bare accetta solo R4, non una catena valida
senza regressioni. Nei prefissi DBH R1-R4 × tre repliche: skills-only 5/12, autopilot 3/12,
bare 1/12, driver-c1a/c3a 0/12; anche DBH-drivers2 driver-c1a/c3a 0/12. Le identità dei
84 task storici/modello/seed/suite erano verificate e i riferimenti restano invariati.
Protocolli, repliche, SDK/skill e correzioni diversi: non è un controllo appaiato fresco,
una nuova esecuzione degli storici o una misura di superiorità generale.

## Consumo operatore: causa e mitigazione misurata
Finestra goal precedente 11:36:34.582–12:48:55.190 UTC: 17.519.912 token, di cui
17.084.928 cacheRead; 345.846 input, 89.138 output; **110 tool call e $3,1483694 SDK**.
La sessione operatore iniziata il 28/09 ripeteva un lungo prefisso fra molte chiamate,
letture/script/audit ripetuti e più ticket. Questo spiega il consumo segnalato di circa
17,6M: non è il numero di token nuovi prodotti dal benchmark Luna/Jev.

Mitigazione applicata: small fact packet, helper/validator verificati riusati, preparazione
raggruppata, singola invocazione seriale della cella, log integrali lasciati su disco,
nessun nuovo agente/scheduler, nessuna suite runtime invariata ripetuta.

Dall'esatta richiesta corrente al checkpoint `spb07-report-operator`: **27 tool call,
5.195.483 token**, di cui 5.086.464 cacheRead, 79.776 input e 29.243 output,
**$0,9606284 SDK**. È un segmento ancora incompleto al checkpoint e con scope diverso
dal vecchio goal: non è un benchmark causale di efficienza né una garanzia di risparmio
finale. Il costo successivo non è zero. Sono osservati meno roundtrip/letture, non un reset.

**La sessione operatore non è stata azzerata:** manca un tool di cambio della sessione
corrente. Il prefisso continua a essere lungo; il vero taglio al successivo ticket resta
una misura operativa da applicare. Il processo nuovo del partecipante non è una nuova
sessione operatore. Non è stato falsificato un reset o inventata autorità per altri agenti.

## Costi cumulativi al checkpoint
Nuova cella: **$0,030739960**. Esperimento cumulativo: **$0,183562666**;
operatore cumulativo dall'intento Luna: **$19,565080100**; totale: **$19,748642766**.
Al cambio contabile originario 1 EUR = 1,1298 USD: **€17,4798** stimati cumulativi,
non una fattura/FX finale/hard cap. Uso operatore successivo al checkpoint da prezzare.
Consumo cumulativo: **10 launch, 47 reservation, 7 semantic call, 367 charge**.
Tutti i 9/41/7/310 consumi precedenti sono conservati; un launch e sei reservation Pi
aggiunti, zero semantic call. L'autorità di questa unica nuova misura è consumata.

## Verifica e limiti
Fonti private: nuova authority, admission/prelaunch SDK/skill/source/input/immagini/costi,
raw turn/test/review/diff, tre candidati, checkpoint e snapshot delivered, oracle immutabili,
packet aggregato, binding del payload, segmenti usage con prefissi hashati. Lo storico,
i source/prep vecchi e i loro ledger non sono stati modificati. Il documento è aggregato,
senza credenziali, canary, sorgenti hidden o output grezzi.
Review/QA/audit inline seriali shared-context, non indipendenti. Runtime invariato rispetto
ai 24 test SPB-06: mantenuti con identità originale, non dichiarati rieseguiti. Release
profile/exact-head hosted CI, nuovo trial e delivery/install/wiki sync restano gate.
Nessun commit/push/PR/merge/install/reload, altro modello/cella, sostituzione o replay.
