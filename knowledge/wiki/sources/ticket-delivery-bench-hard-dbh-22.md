---
type: source
title: "DBH-22 — Viewer dal vivo del lotto, sul terminale"
identity_key: ticket:delivery-bench-hard/DBH-22
identity_strength: stable
source_path: docs/tickets/delivery-bench-hard/done/22-live-lot-viewer.md
source_digest: sha256:9b613b36767b25dd9839852d43b0d4fb5c7ed8fb4ab734fd72fc12668299eb59
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-10-05
created_provenance: git-commit
disposition_changed: 2026-10-05
disposition_changed_provenance: git-rename
---

# DBH-22 — Viewer dal vivo del lotto, sul terminale

Compiled from `docs/tickets/delivery-bench-hard/done/22-live-lot-viewer.md`. Identity is `ticket:delivery-bench-hard/DBH-22`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-05** via `git-commit`
- Disposition changed: **2026-10-05** via `git-rename`

## Graph

- Parent source: [[sources/artifact-delivery-bench-hard-luna-three-arms]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-delivery-bench-hard-dbh-22.md","payload_bytes":2429,"payload_sha256":"9b613b36767b25dd9839852d43b0d4fb5c7ed8fb4ab734fd72fc12668299eb59"}],"payload_bytes":2429,"payload_sha256":"9b613b36767b25dd9839852d43b0d4fb5c7ed8fb4ab734fd72fc12668299eb59","schema":1,"source_digest":"sha256:9b613b36767b25dd9839852d43b0d4fb5c7ed8fb4ab734fd72fc12668299eb59","source_identity":"ticket:delivery-bench-hard/DBH-22","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2429,"payload_sha256":"9b613b36767b25dd9839852d43b0d4fb5c7ed8fb4ab734fd72fc12668299eb59","schema":1,"source_digest":"sha256:9b613b36767b25dd9839852d43b0d4fb5c7ed8fb4ab734fd72fc12668299eb59","source_identity":"ticket:delivery-bench-hard/DBH-22"} -->
```markdown
---
ticket_schema: 1
ticket_id: "DBH-22"
execution_mode: AFK
blocked_by: []
---

# DBH-22 — Viewer dal vivo del lotto, sul terminale

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:22`
- Role: `ticket`
- Parent: [delivery-bench-hard-luna-three-arms.md](../../../specs/delivery-bench-hard-luna-three-arms.md)

## Parent Spec
[delivery-bench-hard-luna-three-arms.md](../../../specs/delivery-bench-hard-luna-three-arms.md),
sezione *Comportamento atteso* 4.

## What to Build
`benchmarks/delivery-bench/watch.py`, di sola lettura, per seguire un lotto mentre gira:
- `cell --lot L --cell C`: segue il JSONL della sessione della cella e stampa messaggi
  dell'assistente, chiamate ai tool con argomenti abbreviati, risultati abbreviati, errori
  evidenziati e costo per turno; continua quando la richiesta successiva riprende la sessione;
- `lot --lot L`: tabella aggiornata delle celle (richiesta corrente, giudicate, accettate,
  errori) e spesa di listino totale rispetto al tetto dell'autorità;
- `open --lot L`: su Windows apre con `wt.exe` una scheda per ogni cella in corso più una per lo
  stato; altrove stampa i comandi.

## Acceptance Criteria
- [x] Su un JSONL sintetico, `cell` stampa nell'ordine messaggio, tool call, risultato, errore e
      costo; righe nuove aggiunte al file compaiono senza rilanciare.
- [x] `lot` legge `lot.json`, `cells/*/cell.json` e il ledger e mostra la spesa contro il tetto
      dell'autorità.
- [x] `open` costruisce un comando `wt.exe` con una scheda per cella; il test ne verifica
      l'argv senza lanciarlo.
- [x] Nessun comando scrive nel lotto né nelle sessioni (test: digest della cartella prima e
      dopo).
- [x] Funziona con le sole librerie standard di Python, anche fuori da Windows.

## Frontier
Done.

## Step-by-Step Implementation Plan
1. Lettore incrementale del JSONL (posizione in byte, righe parziali ignorate fino al `\n`).
2. Rendering degli eventi di sessione di Pi 1.0.2 (messaggi, `toolCall`, `toolResult`, `usage`).
3. Vista di stato da `lot.json`, `cell.json` e ledger, con aggiornamento periodico.
4. `open` con `wt.exe new-tab` per cella.
5. Test in `benchmarks/delivery-bench/test_watch.py`.

## Testing Plan
- Unitari su JSONL e lotti sintetici; prova manuale su un lotto esistente (`dbh-opus`) in sola
  lettura.

## Out of Scope
- Interagire con le istanze di Pi o fermarle dal viewer.
- pi-messenger o estensioni dentro i bracci.

```
