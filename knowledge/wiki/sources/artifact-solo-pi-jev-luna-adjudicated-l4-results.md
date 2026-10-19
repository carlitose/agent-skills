---
type: source
title: "Luna adjudicated L4 — SPB-09, admission-gated"
identity_key: artifact:solo-pi-jev-luna-adjudicated-l4-results
identity_strength: stable
source_path: docs/research/solo-pi-jev-luna-adjudicated-l4-results.md
source_digest: sha256:7ac17658ad3f28c70f92a5c50b85f45fec17bf6aeda888c28edf1b576e1a1f5f
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-10-05
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Luna adjudicated L4 — SPB-09, admission-gated

Compiled from `docs/research/solo-pi-jev-luna-adjudicated-l4-results.md`. Identity is `artifact:solo-pi-jev-luna-adjudicated-l4-results`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-05** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/ticket-solo-pi-jev-luna-pilot-spb-09]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"evidence":{"headings":[],"status":"not-identified"},"findings":{"headings":[],"status":"not-identified"},"limitations":{"headings":[],"status":"not-identified"},"method":{"headings":[],"status":"not-identified"},"question":{"headings":[],"status":"not-identified"}},"parts":[{"index":0,"path":"wiki/sources/artifact-solo-pi-jev-luna-adjudicated-l4-results.md","payload_bytes":1268,"payload_sha256":"7ac17658ad3f28c70f92a5c50b85f45fec17bf6aeda888c28edf1b576e1a1f5f"}],"payload_bytes":1268,"payload_sha256":"7ac17658ad3f28c70f92a5c50b85f45fec17bf6aeda888c28edf1b576e1a1f5f","schema":1,"source_digest":"sha256:7ac17658ad3f28c70f92a5c50b85f45fec17bf6aeda888c28edf1b576e1a1f5f","source_identity":"artifact:solo-pi-jev-luna-adjudicated-l4-results","source_kind":"research"} -->

| Topic | Source sections |
|---|---|
| question | no matching section identified in the source; complete source retained |
| method | no matching section identified in the source; complete source retained |
| findings | no matching section identified in the source; complete source retained |
| evidence | no matching section identified in the source; complete source retained |
| limitations | no matching section identified in the source; complete source retained |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1268,"payload_sha256":"7ac17658ad3f28c70f92a5c50b85f45fec17bf6aeda888c28edf1b576e1a1f5f","schema":1,"source_digest":"sha256:7ac17658ad3f28c70f92a5c50b85f45fec17bf6aeda888c28edf1b576e1a1f5f","source_identity":"artifact:solo-pi-jev-luna-adjudicated-l4-results"} -->
```markdown
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

```
