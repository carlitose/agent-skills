---
ticket_schema: 1
ticket_id: "SPL-03"
execution_mode: AFK
blocked_by: []
---

# SPL-03 — Rilocare estensioni congelate senza modificare Pi personale

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-superpowers-luna:SPL-03`
- Role: `ticket`
- Parent: [delivery-bench-superpowers-luna.md](../../specs/delivery-bench-superpowers-luna.md)

## Parent Spec
[delivery-bench-superpowers-luna.md](../../specs/delivery-bench-superpowers-luna.md), Recovery of frozen extensions, Non-goals and invariants, Gates.

## What to Build
Aggiungere al runner esistente l'operazione `relocate-extension` e un sidecar verificato che
sposti solo indirizzi fisici a contenuto identico; nessun nuovo scheduler o protocollo di misura.

## Acceptance Criteria
- [ ] Il comando esige motivo, entrypoint originariamente legato e snapshot con nome e digest identici.
- [ ] Il caricamento applica il sidecar a ogni braccio interessato e mantiene il guard sul contenuto.
- [ ] Manifesto e autorità sono legati ai loro hash; metadati malformati/stale e altri drift bloccano.
- [ ] Celle attive impediscono la rilocazione; la pubblicazione è atomica e l'audit conserva esiti e IO falliti.
- [ ] Manifesto originale, giudizi, tentativi e configurazione personale non sono modificati o cancellati.
- [ ] I nuovi tentativi registrano i nuovi percorsi; un no-op identico conserva la provenienza precedente.
- [ ] Test offline verificano errori, immutabilità, CLI, guard post-rilocazione e continuazione della catena.

## Frontier
Ready: scelta «1» dell'utente; contenuto precedente recuperabile con digest esattamente corrispondente.
Il successivo resume rimane subordinato ai check, al readback dei binding e all'assenza di processi residui.

## Gates
- Attempt: implementazione SPL-03 attraverso handoff; il lotto SPL-02 continua nel suo attempt esistente.
- Budget per attempt: nessun limite impostato; SDK/costi mancanti non diventano zero.
- Time per attempt: nessun limite impostato.
- Maximum attempts: nessun limite impostato; nessun retry implicito dell'intero lotto.
- Approvals: scelta umana «1» per il recupero isolato; autorità Luna medium del lotto invariata.
  Nessun Anthropic/Jev, delegazione, installazione globale, modifica Pi personale, push/PR/merge o pubblicazione.
- Exact version: modello `openai-codex/gpt-6-luna`, thinking `medium`; contenuto delle estensioni deve
  corrispondere alle impronte già congelate, non alla versione personale aggiornata.
- Existing blocks searched: load_lot, bind/check_arm_extensions, CLI, lock e storia Git della dipendenza;
  manca un'API di rilocazione. La cartella originale è recuperabile da Git a hash identico.

## Step-by-Step Implementation Plan
1. Testare la rilocazione e la ripresa con fixture locali, prima dell'implementazione.
2. Incapsulare metadati/overlay in un modulo; integrare il comando nel runner proprietario.
3. Verificare diff, packaging e check causali; review e QA inline, senza dichiarare indipendenza.
4. Restituire handoff; applicare poi la nuova API al lotto esistente sotto l'autorità già registrata.

## Testing Plan
Unit/integration offline: shared bindings, digest e nomi errati, sorgente ignota, autorizzazione/manifesto
stale, metadati malformati, lock attivo, failure di pubblicazione, no-op, guard su snapshot modificato,
CLI e ripresa senza riscrivere giudizi precedenti. Regressioni dei binding/profili e dei consumer load_lot;
lint e profilo quick obbligatorio. Nessuna ripetizione automatica del preflight a pagamento o suite live.

## Out of Scope
- Cambiare contenuto, profili, richieste, suite, modello, budget o numero di posizioni.
- Aggiornare/retrocedere Pi personale, ricreare il lotto, rigiocare le 99 posizioni giudicate.
- Git/provider delivery, wiki synchronization o dichiarazioni di risultato finale.
