---
type: source
title: "Ammissione e rinnovo della capacità di lancio"
identity_key: artifact:solo-pi-jev-launch-admission
identity_strength: stable
source_path: docs/specs/solo-pi-jev-launch-admission.md
source_digest: sha256:0c804a9361cbd5804ba75c21438e71d263f78c35095b26af336cb1ff68173d8b
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-10-05
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Ammissione e rinnovo della capacità di lancio

Compiled from `docs/specs/solo-pi-jev-launch-admission.md`. Identity is `artifact:solo-pi-jev-launch-admission`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-05** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Child source: [[sources/ticket-solo-pi-jev-luna-pilot-spb-10]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"decisions":{"headings":[],"status":"not-identified"},"exclusions":{"headings":[],"status":"not-identified"},"goals":{"headings":[],"status":"not-identified"},"invariants":{"headings":[],"status":"not-identified"},"verification":{"headings":[],"status":"not-identified"}},"parts":[{"index":0,"path":"wiki/sources/artifact-solo-pi-jev-launch-admission.md","payload_bytes":2958,"payload_sha256":"0c804a9361cbd5804ba75c21438e71d263f78c35095b26af336cb1ff68173d8b"}],"payload_bytes":2958,"payload_sha256":"0c804a9361cbd5804ba75c21438e71d263f78c35095b26af336cb1ff68173d8b","schema":1,"source_digest":"sha256:0c804a9361cbd5804ba75c21438e71d263f78c35095b26af336cb1ff68173d8b","source_identity":"artifact:solo-pi-jev-launch-admission","source_kind":"spec"} -->

| Topic | Source sections |
|---|---|
| goals | no matching section identified in the source; complete source retained |
| exclusions | no matching section identified in the source; complete source retained |
| decisions | no matching section identified in the source; complete source retained |
| invariants | no matching section identified in the source; complete source retained |
| verification | no matching section identified in the source; complete source retained |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2958,"payload_sha256":"0c804a9361cbd5804ba75c21438e71d263f78c35095b26af336cb1ff68173d8b","schema":1,"source_digest":"sha256:0c804a9361cbd5804ba75c21438e71d263f78c35095b26af336cb1ff68173d8b","source_identity":"artifact:solo-pi-jev-launch-admission"} -->
```markdown
# Ammissione e rinnovo della capacità di lancio

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-launch-admission`
- Role: `spec`
- Standalone: true

### Children
- [SPB-10](../tickets/solo-pi-jev-luna-pilot/10-renew-launch-admission.md)

## Bug e nuovo mandato
SPB-09 verifica soldi e binding ma omette max_pi_launches prima del run: consumed10/limit10
produce ChainGate senza PID, richieste o nuova spesa. Il preflight aveva dichiarato ready
erroneamente. L'utente ora autorizza benchmark minimo su questo braccio, diagnosi/fix/riprova
fino a flusso funzionante; copre ulteriori lanci Yjs L4 Luna medium nel budget cumulativo
originale €1000. Non è un reset o autorizzazione ad altri modelli, scenari o delivery.
I dieci lanci passati e il gate di SPB-09 rimangono tali, non vengono cancellati o riprodotti.

## Modulo, interface e Seam
Budget possiede consumo, permessi, capacità e funds. Aggiungere API pubblica
`admit_launch(argv)` non avviante, riusata da launch: verifica gate/permessi/inflight,
argv/modello, costo completo/headroom e capacità cumulativa, con causa specifica prima
che il caller dichiari ready. Caller la usa soltanto prelaunch, non dopo un lancio attivo.
`renew_launch_capacity(actor, mandate_ref)` è una distinta operazione attestata dal caller:
richiede human:user, ref attribuito non vuoto, nessun gate/inflight, pi consentito e fondi
noti residui. Conserva autorità originale/hash, calls/charges/operator costs/launches e
soglie. Registra un binding append-only per il solo prossimo lancio (cap=max(base,consumed+1)),
con parent limit/actor/ref. È idempotente fino al consumo di quel lancio; nessun rilancio
automatico. Dopo consumo, lo stesso valido mandato di repair-loop può rinnovare il prossimo
binding; il caller verifica scope/revoca/fondi ogni volta. La API non inferisce consenso dal
solo ref e non certifica il contenuto umano: caller deve validarlo e mantenere artefatto/hash.
Non modificare il file finanziario originale né ricreare/resettare lo store. Rinnovo non
scavalca gate d'uso ignoto, exhausted monetary budget, permesso negato o processo inflight.
Seam esistente ChainSession/provider: fake solo ai port, account/file reali.

## Verifica e limiti
RED su API mancante; GREEN capacità esaurita riconosciuta nel preflight, rinnovo coperto
consente un solo prossimo launch conservando tutto, reentry/idempotenza, invalid actor/ref,
permessi/inflight/gate/funds ancora bloccanti. Targeted Budget/adapter regressioni; nessuna
suite controller invariata o nuova chiamata live nei test. Caller live successivo usa snapshot
congelato e mandato attestato, ammissione completa e ledger cumulativo copiato dal più recente.
Report del gate precedente e nuovo source separati; no hidden feedback, falsi score, cap
finanziario aumentato, install/runner/delega. Live coverage/funzionamento e release/CI restano
prove distinte; un difetto reale del prodotto è un risultato, non motivo per forzare PASS.

```
