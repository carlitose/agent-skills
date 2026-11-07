---
type: source
title: "SPL-03 — Rilocare estensioni congelate senza modificare Pi personale"
identity_key: ticket:delivery-bench-superpowers-luna/SPL-03
identity_strength: stable
source_path: docs/tickets/delivery-bench-superpowers-luna/03-relocate-frozen-extension.md
source_digest: sha256:06ae30f91245ab2b72873c288ba463cb7664d003f903d821ae12f4a25f61091f
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-11-07
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# SPL-03 — Rilocare estensioni congelate senza modificare Pi personale

Compiled from `docs/tickets/delivery-bench-superpowers-luna/03-relocate-frozen-extension.md`. Identity is `ticket:delivery-bench-superpowers-luna/SPL-03`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-11-07** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-delivery-bench-superpowers-luna]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[9],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[8],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-delivery-bench-superpowers-luna-spl-03.md","payload_bytes":3803,"payload_sha256":"06ae30f91245ab2b72873c288ba463cb7664d003f903d821ae12f4a25f61091f"}],"payload_bytes":3803,"payload_sha256":"06ae30f91245ab2b72873c288ba463cb7664d003f903d821ae12f4a25f61091f","schema":1,"source_digest":"sha256:06ae30f91245ab2b72873c288ba463cb7664d003f903d821ae12f4a25f61091f","source_identity":"ticket:delivery-bench-superpowers-luna/SPL-03","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 8: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 9: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3803,"payload_sha256":"06ae30f91245ab2b72873c288ba463cb7664d003f903d821ae12f4a25f61091f","schema":1,"source_digest":"sha256:06ae30f91245ab2b72873c288ba463cb7664d003f903d821ae12f4a25f61091f","source_identity":"ticket:delivery-bench-superpowers-luna/SPL-03"} -->
```markdown
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

```
