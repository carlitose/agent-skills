# Luna Yjs L4 — benchmark minimo del braccio e repair loop

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-luna-repair-loop`
- Role: `spec`
- Standalone: true

### Children
- [SPB-11](../tickets/solo-pi-jev-luna-pilot/11-benchmark-minimum-arm.md)
- [SPB-13](../tickets/solo-pi-jev-luna-pilot/13-retest-minimum-arm.md)

## Mandato e minimo
Utente: «Comunque fai sti cazzo di benchmark minimo su questo braccio e vedi se funziona o
ci sono bug nel braccio! Se c’è fixa, è riprova il benchmark fino ad arrivare funzionante e
valutarlo davvero». Inline serial skills-only, nessuna delega/runner/delivery.
Minimo: una nuova catena Yjs L4 Luna medium sul braccio corretto SPB-10; R1 Counter,
R2 readOnly/lint/format, R3 replica undo/redo e replace, R4 add/reset. Stesso processo/sessione,
quattro richieste cumulative e protocollo di dipendenze originario. Fixed source separato;
nessun replay dello storico e nessun feedback oracle privato al partecipante.

## Criterio di funzionamento
Osservare i port reali e distinguere codice insufficiente da infrastruttura/protocollo errato.
Riparare soltanto difetti dimostrati del braccio, mantenere candidato/evidenze/fallimenti,
poi nuova prova con source congelato e admission completa. Non iterare finché oracle dà 4/4:
un NO fondato o test falliti è un risultato del modello; dipendenti non tentati restano tali.
Flusso locale completato e score dell'oracle sono giudizi separati. Se la catena non esercita
un segmento, dichiarare il limite invece di fingere copertura end-to-end.

## Ammissione
Validare handoff/verification SPB-10, target/graph/envelope/snapshot/SDK/model/skills/input,
immagini e originale €1000/costi cumulativi correnti. Copiare il più recente SPB-09 budget
10/47/7/367, nessun reset. Pubblica renew_launch_capacity sotto mandato attribuito, poi
admit_launch prelaunch; nessuna modifica manuale di authority/store. Renew dà un solo prossimo
slot; la richiesta umana di repair-loop, non budget residuo, autorizza nuove prove coerenti.
Ogni eventuale prova ulteriore usa nuova identità e consumo precedente intero. Unknown costo,
limite monetario, revoca, port irrecuperabile o scope diverso rimangono confini reali.

## Output
Preservare tutti gli attempt, input/charge/source/history refs, candidato e consegnato, score
per R e motivi di arresto. Rapporto di copertura reale, difetti corretti e limiti del braccio;
mai upgrade di test fake a prove live. SDK estimate non invoice/FX finale. Nessun cambio di
modello/soglie/dati, intervento manuale sul prodotto per forzare score, pubblicazione/installazione.
