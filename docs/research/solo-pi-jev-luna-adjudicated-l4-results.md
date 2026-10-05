# Luna adjudicated L4 — SPB-09, admission-gated

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-luna-adjudicated-l4-results`
- Role: `research`
- Parent: [SPB-09](../tickets/solo-pi-jev-luna-pilot/09-run-adjudicated-l4.md)

## Risultato osservato
L'invocazione autorizzata del caller termina gated dopo 3,672s, prima del lancio Pi.
Budget max_pi_launches=10 e launches=10; nessuna session directory/PID/session ID o richiesta.
**Nessun nuovo score**, non 0/4: R1-R4 tutte non tentate. Zero nuovo spend sperimentale.
Ledger invariato 10 launch, 47 reservation, 7 semantic call, 367 charge. Source SPB-08
91e21087aec680c0a0a94c7144fb70d87269b54f e manifest/cell/budget preservati nel lotto
`spj-luna-corrected-l4-3`. Il preflight verificava fondi ma non capacità cumulativa di lancio:
questo è un difetto del caller/ammissione, non un risultato del modello.
Al checkpoint prelaunch: esperimento $0,183562666, operatore $23,434818600,
combinato $23,618381266 SDK; successivo uso operatore/fattura/FX finale ignoti.
Nessun oracle o hidden consultato; nessun replay o PASS di release/delivery.
Il successivo mandato umano chiede fix/riprova del braccio fino a flusso funzionante;
SPB-10 gestisce preflight/rinnovo attribuito, senza riscrivere questi artefatti.
