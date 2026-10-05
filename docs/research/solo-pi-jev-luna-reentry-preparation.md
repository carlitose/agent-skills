# Luna Pi + Jev — riconciliazione e preparazione della sola prova corretta L4

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-luna-reentry-preparation`
- Role: `research`
- Parent: [Pilota Luna](../specs/solo-pi-jev-luna-pilot.md)

## Scope e stato
SPB-04 prepara, non lancia. «Fallo» segue l'offerta di riconciliare i costi e preparare
una catena separata di quattro richieste. Non rinnova la ripetizione del lotto originale,
non autorizza nuove chiamate sperimentali Pi/Jev/judge né consegna/pubblicazione/installazione.

Un solo nuovo input posseduto: `spj-luna-corrected-l4-prep-1`, persistente `crdt-yjs`, L4,
seriale, stesso `openai-codex/gpt-6-luna` medium. Yjs attraversa il parser dei findings JS
che nel pilota era `unparsed`; non è una nuova comparazione, un successo o una superiorità
misurata. Bare, Lua, SQL, lotto completo, L12 e ulteriori ripetizioni esclusi.

## Costi attribuiti: checkpoint, non fattura
La cifra precedente circa €0,12 era soltanto la stima sperimentale, non il lavoro
operatore. Ora sono disponibili usage SDK della sessione, compresa la storia compattata.
La ricostruzione parte dall'intent Luna `2026-10-01T21:31:19.174Z`, non addebita i giorni
precedenti di attività estranea e conserva tutte le entry nel periodo, non solo il ramo
attuale. L'owner Pi installato somma assistant/toolResult usage, usage entries e
compaction/branch-summary usage; `usage-totals` somma `usage.cost.total` senza inventare
fatture. Le entry sono uniche e hanno un costo finito osservato al checkpoint.

| Componente al checkpoint | Stima USD |
| --- | ---: |
| Esperimento storico, smoke incluso | 0.134416986 |
| Operatore: setup, misura, riparazioni, preparazione contabilizzata | 14.027075900 |
| Totale attribuito | 14.161492886 |

Cambio contabile originale: 1 EUR = 1.1298 USD. Totale di riferimento **€12,5345**,
residuo stimato del tetto €1.000 **€987,4655**. Sono stime SDK/Jev, non conto/fattura né
hard cap lato provider. Fattura e cambio finale ignoti; attività operatore successiva al
checkpoint non inclusa e da aggiornare prima di ogni futura reservation.

296 record nel periodo; prefisso sessione di 34.579.025 byte, SHA-256
`d5b3d5704f0b3f58e69c4c74866c217a0c12faa5c742c275ee154890dd6cd9d9`.
Provenienza completa e metadata senza prompt/credenziali nel checkpoint privato. Le
osservazioni iniziali rimangono intatte e riferite sotto la loro identità, non rinominate
come ultime. Nessun nuovo launch/reservation/semantic call: conservati **8 launch,
36 reservation, 7 semantic calls, 268 charge**. Il ledger originale non è modificato.

## Input preparati
- Runtime: CandidateRef SPB-03, tree `6e78e725a4c3eee881c1d8b54a1a1abb4facf320`,
  implementation-complete/release-blocked. La copia via Git archive è distinta dal
  candidato documentale SPB-04. Le prove simulate/locali SPB-03 restano sotto quel tree;
  non sono verifica live della nuova cella.
- Seed, prime quattro richieste, metadata e hidden suite hanno gli hash originali.
  Hidden soltanto digest/provenienza nel caller; mai contenuto in progetto/ticket/prompt.
  Nessuna suite/oracle eseguita ora.
- Nuovo clone con `core.autocrlf=false`, `core.eol=lf`, no hardlink/origin; tree iniziale
  uguale al seed: `527f80f140b6d2eff364e5c53c5d99e25988cd54`.
- R1–R4 serializzati con il contratto ticket canonico, dipendenze R2→R1, R3→R2, R4→R3.
  I process-owned request input non sono nuovi ticket di consegna del repository.
- SDK Pi **1.0.0**, file SDK e skill manifest uguali alla binding del pilota; immagini
  locali richieste presenti. Soltanto `docker image inspect`, nessun pull/start/build.
- Budget in copia separata parte dai byte originali; owner Budget aggiunge osservazioni
  operatore cumulative e conserva contatori/charge. Questa preview non è autorità live.
  Vecchio limite di launch: due posti residui, non consenso per una nuova ripetizione.

Artefatti locali principali:
- `C:/dbench/runs/spj-luna-corrected-l4-prep-1/prepared-manifest.json` — input iniziale immutabile.
- `C:/dbench/runs/spj-luna-corrected-l4-prep-1/financial-checkpoint.json` — checkpoint aggiornato, riferisce la nuova preview senza alterare l'iniziale.
- `C:/dbench/tmp/spb04-inputs.json` — ammissione documentale/identità e scope.

## Gate per procedere
1. Autorizzazione esplicita per questa sola nuova catena e ammissione fresca: vecchio
   scope/repetition consumati, nessuna deduzione di consenso da un budget residuo.
2. Costi cumulativi operatore aggiornati, quote/model/SDK/skills/source/input ancora
   identici, headroom per reservation; ignoti restano gate, mai zero simulato.
3. Auth/provider/modello/routing e comportamento corretto Pi/Jev/Luna da osservare
   durante la futura prova; il preflight statico non li dimostra.
4. Profile release, exact-head CI, delivery e publication authority restano separati.

SPB-04 non produce nuove chiamate dei partecipanti sperimentali Pi/Jev/judge o risultati
del benchmark. Le chiamate dell'assistente operatore continuano e la loro parte successiva
al checkpoint è ancora da contabilizzare. Review/QA/audit inline condividono contesto;
non sono indipendenti. Source/risultati/costi storici SPB-01/02
restano immutati; Lua non diventa confrontabile e richieste dependency-blocked non diventano
fallimenti del modello per effetto di questa preparazione.
