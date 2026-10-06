# Blocchi citati e percorso diretto misurato

## Artifact Graph
- Artifact ID: `artifact:lane-discipline`
- Role: `spec`
- Standalone: true

### Children
- [LD-01](../tickets/lane-discipline/done/01-cited-blocks-and-measured-direct-lane.md)

## Type
Decision

## Problem
Il 2026-10-06 l'utente ha segnalato due sessioni Pi su altri progetti.

1. **Blocco inventato.** Un vincolo "solo codice, niente live" dato a un altro agente è stato
   applicato dall'agente principale a sé stesso, come divieto anche di semplici letture su host,
   ledger e database. Sotto `/goal` l'agente ha risposto "bloccato, serve autorizzazione" per 8
   turni di fila (circa 1,6 milioni di token), senza fare nulla, finché `/goal` si è messo in
   pausa. Alla domanda dell'utente "dove è sto gate?" ha ammesso che il gate non esisteva.
2. **Percorso diretto sforato.** Un'altra sessione ha scelto il percorso diretto per una
   correzione che decide a chi si addebita un pagamento. Il cambio finale era di 4 file e 160
   righe, test compresi (2 file e 46 righe di codice di produzione). L'agente non è passato a
   skills-only e ha fatto un commit locale senza revisione né criteri di accettazione.

La policy obbligatoria di oggi (`extensions/mandatory-agent-skills.ts`, voce 2) fissa il
percorso diretto a «about three files and 100 changed lines», senza dire se i test contano né
quando misurare, ed esclude contratti, schemi, migrazioni, dipendenze e policy, ma non i soldi.
Nessuna regola chiede di citare un blocco prima di fermarsi.

## Decisions
L'utente ha chiesto di aggiungere entrambe le regole («Aggiungi anche questo problema», poi
«va bene» sulla descrizione in chiaro).

1. **Blocco citato.** Prima di fermarsi per un blocco o di chiedere un permesso, l'agente
   cita la fonte: la `## Gates` della spec o del ticket, un rifiuto reale di uno strumento o
   del runtime, oppure le parole esatte dell'utente. Un vincolo dato a un altro agente o a
   un altro compito non lo vincola. Quello che non sa citare non è un gate, quindi continua.
   Una decisione che manca davvero si chiede una volta, in chiaro, con le opzioni, invece di
   ripetere uno stato "bloccato" a `/goal` o a un altro loop.
2. **Percorso diretto misurato.**
   - I limiti di circa 3 file e 100 righe contano anche i test.
   - Prima del commit l'agente misura l'intera modifica (`git diff --stat`). Se supera i
     limiti, o ha richiesto una decisione di design, non la consegna come diretta: lo dice
     all'utente e passa a skills-only, dando il lavoro fatto a `execute-ticket` come candidato.
   - Soldi (addebiti, pagamenti, fatturazione), autenticazione e permessi, cancellazione di
     dati non usano mai il percorso diretto, qualunque sia la dimensione, a meno che l'utente
     lo chieda esplicitamente per quella modifica.

## Non-goals
- Modificare `goal.ts` (decisione precedente dell'utente).
- Aggiungere nuovi passaggi di approvazione o cambiare Autopilot.
- Cambiare `ask-skills/OPERATING-DEFAULTS.md`, misurato dal tetto di contesto.

## Target
- Voce 2 della policy obbligatoria: i limiti con i test, la misura prima del commit, le
  esclusioni sempre valide e il passaggio a `execute-ticket`.
- Voce 8 della policy obbligatoria: la regola del blocco citato.
- `ask-skills/SKILL.md` e `README.md`: la stessa definizione breve del percorso diretto.
- `extensions/mandatory-agent-skills.test.ts`: controlla le frasi nuove.

## Gates
- Tentativo: una PR con le modifiche ai testi e ai test.
- Budget: nessuna spesa a pagamento (solo testo, test locali e CI).
- Tempo e tentativi massimi: nessun limite indicato dall'utente.
- Approvazioni: merge con CI 8/8 e `--match-head-commit`; poi pin in `pi-personal-config`,
  `update:personal` e reload, come descritto all'utente prima del suo «va bene».
- Versione esatta: nessuna.
- Blocchi cercati:
  - le asserzioni sul testo attuale in `extensions/mandatory-agent-skills.test.ts`;
  - il tetto di contesto di `ticket-autopilot/tests/test_context_budget.py`, che misura
    `OPERATING-DEFAULTS.md` e non i file toccati qui;
  - il giudizio di qualità in corso usa `benchmarks/` dal checkout principale, che questo
    cambio non tocca.
