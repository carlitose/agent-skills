# Delivery Revalidation Efficiency Wayfinder

## Artifact Graph
- Artifact ID: `artifact:delivery-revalidation-efficiency-wayfinder`
- Role: `wayfinder`
- Standalone: true

### Children
- [DRV-01 — Map the completion-to-delivery revalidation flow](../tickets/delivery-revalidation-efficiency/done/01-map-current-flow-and-cost.md)
- [DRV-02 — Prototype exact projection proofs and lifecycle ordering](../tickets/delivery-revalidation-efficiency/done/02-prototype-projection-proof-options.md)
- [DRV-03 — Choose the final-tree validation architecture](../tickets/delivery-revalidation-efficiency/03-choose-final-tree-validation-architecture.md)

## Type
Wayfinding spec

## Status
Active. DRV-01 is terminally integrated through PR #199. DRV-02's standard-library-only
disposable comparison is complete in the current candidate, but it does not unblock DRV-03 until
its own exact delivery head is integrated. No implementation design or production bypass is
selected.

## Destination
Preserve the rule that every delivery claim binds the exact final tree while removing the
unconditional repetition of broad review, QA, and verification suites when the only tree
change is a runner-authored, deterministic tracked-completion projection.

The destination is not “skip verification.” It is one auditable final-tree validation cycle,
or a narrower proof that is demonstrably equivalent for an explicitly bounded projection.
Arbitrary semantic drift must continue to invalidate downstream evidence.

## Current Behavior

Observed repository behavior through repository commit
`693b9e18f15614589a0c55229cbdcbd763021f65`, tree
`dc74894e00a1da54b532f9ead12fcd19da4deb59`:

1. A ticket reaches `verified` against an implementation CandidateRef.
2. Delivery preparation may move the exact tracked ticket to `done/`, write a schema-1
   completion receipt, and repoint links, producing a different tree.
3. `prepare_delivery_revalidation()` in
   [`kernel.py`](../../ticket-autopilot/scripts/autopilot/kernel.py) accepts that new
   CandidateRef, resets state to `active` and stage to `review`, retains only `implement`
   and `simplify`, calls `_invalidate_leaf_artifacts()`, and emits
   `delivery-revalidation-required`.
4. The scheduler therefore requires another review, QA plan, QA execution, verification,
   and finalization before rendering or provider mutation.
5. [`cli.py`](../../ticket-autopilot/scripts/autopilot/cli.py) owns the
   `delivery-revalidate` operation; [`test_kernel.py`](../../ticket-autopilot/tests/test_kernel.py),
   [`test_cli.py`](../../ticket-autopilot/tests/test_cli.py), and
   [`test_ticket_sources.py`](../../ticket-autopilot/tests/test_ticket_sources.py) cover
   revalidation and completion-projection boundaries.

This is safe because the delivery tree is not silently treated as the implementation tree.
It is inefficient because the runner has no narrower representation for a proven deterministic
projection. OHR-02 consequently ran the broad 702/76/165/24/6-test set once for its
implementation tree and once again for its completion-projected delivery tree. Those timings
are one local case, not a general performance benchmark.

## Semantic Invariants

- **Exact final tree:** PR body, provider head, verification handoff, and terminal proof bind
  the same final CandidateRef.
- **Fail closed on unclassified drift:** no filename, docs-only, same-tree, or author label can
  substitute for a byte- and mode-exact proof.
- **Projection is narrow:** only runner-authored operations allowed by a versioned contract may
  receive narrower validation.
- **Evidence remains causal:** a projection proof may carry evidence only for unchanged causal
  segments; changed links, receipts, lifecycle state, and source paths need direct checks.
- **Literal history:** append-only ledgers, gates, receipts, prior CandidateRefs, and consumed
  budgets are not rewritten.
- **Separate authorities:** a projection proof grants no merge, reconciliation, source,
  completion, wiki, provider, status-change, terminal-proof, or local-Pi authority.
- **Crash-safe replay:** interruption before, during, or after projection must reconcile from
  durable intent and exact readback without duplicate moves or receipts.
- **Source-mode separation:** tracked, ignored, and external-unpublished ticket sources do not
  silently inherit one another's completion rules.

## Decisions So Far

- The existing second cycle remains mandatory until a replacement contract is implemented and
  verified. This frontier does not authorize a bypass.
- Broad-suite duplication is a design cost, not an intrinsic exact-tree requirement.
- The final architecture must make the final delivery tree and the proof that connects it to
  prior evidence explicit.
- Test selection cannot be based only on changed extensions or paths; it needs a versioned
  projection kind and complete effect manifest.
- No compatibility shim is assumed. Historical ledgers and receipts still require literal
  replay compatibility where the repository already guarantees it.

## DRV-01 Durable Facts

- The ordinary tracked path verifies an implementation CandidateRef `I`, projects the ticket
  move, completion receipt, and deterministic link repoints into delivery CandidateRef `D`, then
  clears every downstream leaf result and repeats `review -> qa-plan -> qa-execute -> verify ->
  finalize` against `D`.
- Exact final-tree identity, complete path/blob/mode and link transitions, lifecycle/effect
  ordering, receipt validation, final CandidateRef reduction, head/body/provider binding, and
  terminal reachability remain causally mandatory. Repeating unrelated broad semantic suites is
  not itself the invariant, but current evidence cannot prove those suites unaffected.
- Four completed samples consumed 16 additional delivery leaf interactions and 80 durable
  command/check labels. Three were completion-only at raw-tree level; CST-03 also changed
  `kernel.py` and `test_kernel.py`, proving that a completion-shaped delta is not necessarily a
  completion-only delta.
- Historical `wall_time: 0` values are missing measurements, not zero-cost observations. The
  sampled ledgers have no trustworthy monotonic timing or operating-system process manifest.
- Tracked, ignored, reconciliation, post-commit recovery, provider, terminal-proof,
  historical-ledger, wiki, and Pi paths retain separate topology and authority contracts; none
  automatically inherits a future ordinary tracked projection proof.
- The bounded evidence and reproducible extraction method are in the
  [current-flow and cost report](../research/delivery-revalidation-current-flow-and-cost.md).

## Candidate Designs — Unselected

### A. Project before the final quality cycle

Apply tracked completion before review, QA, and verification, then validate only the final tree.
This is structurally simple but must answer whether a ticket can be represented as completed in
the candidate before delivery and integration, how failure rollback remains literal, and how
ignored or externally owned sources behave.

### B. Proof-carrying deterministic projection

Keep implementation-tree verification, then issue a content-addressed projection proof binding
implementation tree, final tree, exact allowed effects, receipt, moved source bytes/mode, link
repoints, and negative extra-diff evidence. Re-run only projection-local checks and reduce a new
final-tree Verification Record from unchanged evidence plus the proof. This preserves lifecycle
ordering but introduces a security-critical proof and test-selection contract.

### C. Bounded hybrid

Project ordinary tracked tickets before final quality, while retaining proof-carrying or full
revalidation paths for ignored sources, reconciliation, recovery, or legacy histories. This may
minimize common-case cost but risks multiple lifecycle variants and must prove that classification
is deterministic and non-overlapping.

## DRV-02 Disposable Comparison Evidence

### Question and method

The logic prototype asked whether A, B, and C could preserve exact-final-tree truth while avoiding
unconditional broad delivery revalidation for one bounded ordinary tracked-completion projection.
It assumed every non-tracked, stale, tampered, duplicate, provider-mutated, reconciliation-drifted,
or ambiguous topology must leave the narrow path. A useful result required every design to consume
the same frozen fixtures, accept the same exact tracked case, fail closed for every mutation, and
replay each crash checkpoint without selecting a winner.

The prototype used only the Python standard library. Expected outcomes were frozen in a separate
contract before the model was implemented. Seven unit tests then exercised 17 fixtures against all
three designs, and two executions produced byte-identical result JSON. It did not download a
dependency, call a provider, modify a real run ledger, or execute production delivery code.

Durable, content-addressed evidence is retained outside the source candidate under the run's Git
common artifacts:

| Artifact | SHA-256 |
|---|---|
| `drv-02-prototype-contract.json` | `526dd4f3bbd9fe3ff1fb6330f03b3f9ce939e503e3e95a2a12f0c4abcd719fdb` |
| `drv-02-prototype-results.json` | `225e6166b7ffd0c71a5276a202b08186aa9ff2264d1307a49051fcb9018b2758` |
| `drv-02-prototype-run.log` | `07a00c2c8091e38866bc894ff6e89d5016208d9e25ee956c64a2b272c83a874b` |
| `drv-02-prototype-cleanup-proof.json` | `13a555ffa1d7ca22c5c7c6cee7960e892e207bbafc270131b8d690e3f509c5c2` |

The model script SHA-256 was
`3c162094c1af35d3f3cf06ec7a40738146d07cf1ffea12cf2dec0b5019e00c9b`.
The script and scratch directory were deleted after evidence capture; no prototype path, cache,
generated state, or provider receipt remains in the source worktree.

### Shared state/effect contract

Every design received the same model rather than a design-specific happy path:

- distinct non-empty implementation and delivery tree identities over complete sorted path,
  blob-SHA-256, and mode entries;
- one exact `100644` ticket blob removed from its pending path and added unchanged under `done/`;
- one canonical schema-1 completion receipt bound to the run, ticket digest, implementation
  CandidateRef, source mode, and validated stages;
- one approved link repoint with exact old/new blobs and unchanged mode;
- a complete diff manifest and SHA-256 negative proof over the entire diff, so an unlisted effect
  cannot be ignored;
- artifact generation `3 -> 4`, three explicit evidence segments, old/new leaf budgets, and
  unique effect keys;
- durable checkpoints for intent, effect readback, proof seal, and final-tree binding;
- provider, source-mode, reconciliation-target, and replay state as explicit fields rather than
  inferred labels.

The model tree identities are SHA-256 identities over the prototype's canonical entry format, not
claims that production Git emitted those object IDs. The contract's own digest is
`1370908de56cf37df43fb05b58c64df5570b3ed96de443df49f0230fdfb243cc`;
the positive proof digest is
`2696b1d50d496352f1f5e527d26db5bf2899104d3d394c5dddff4d88a921083b`.

The contract is reproducible without retaining prototype code:

1. Encode JSON as sorted, compact UTF-8 with one trailing LF and hash bytes with SHA-256.
2. Represent each tree as a complete path-sorted map of `{mode, blob_sha256}` entries; derive the
   tree identity from that canonical map.
3. Build `I`, then build `D` only from the exact ticket move, receipt, and approved link repoint.
4. Enumerate the union of paths in `I` and `D`; bind both the complete diff rows and their digest.
5. Validate proof digest, CandidateRefs, unique effects, ticket bytes/mode, receipt fields, link
   manifest, artifact generation, stable evidence segments, topology, provider state, and
   checkpoint before considering a narrow outcome.
6. Apply each frozen mutation independently. Block stale/tampered/duplicate/source/provider/crash
   ambiguity first; otherwise force full revalidation on any complete-diff, ticket, receipt, link,
   or reconciliation mismatch.
7. Assert all three designs consume every fixture, partial checkpoints return recoverable actions,
   exact final replay returns `already-applied`, and no selection field is populated.

### Fixture outcomes

| Outcome | Fixtures | Required behavior in all designs |
|---|---|---|
| Narrow-eligible | exact tracked move, same ticket blob/mode, canonical receipt, approved link repoint, complete negative extra-diff proof | Bind the exact final tree through the design-specific path. |
| Recoverable | crash after durable intent; crash after effect readback; crash after proof seal | Resume from the named checkpoint without duplicating an effect or rewriting history. |
| Already applied | exact replay at final-tree binding | Return `already-applied` and emit no new effect. |
| Full revalidation | extra path; changed implementation blob; changed ticket mode; changed receipt; unapproved link edit; reconciliation target drift | Discard the narrow path and run the current full revalidation contract. |
| Blocked | stale CandidateRef; tampered proof; duplicate effect; ignored-source digest/mode drift; prior provider mutation; ambiguous crash | Stop without provider or real-run mutation. |

Observed totals were 1 narrow, 3 recoverable, 1 already-applied, 6 full-revalidation, and 6
blocked. Every expected outcome matched, and every fixture produced an explicit action for A, B,
and C.

### Design comparison

The command figures below are modeled labels, not wall time or operating-system process counts.
They use DRV-01's durable 20-label delivery-revalidation sample as the common baseline. Proof
surface is compared through the explicit persisted obligations, not a numeric complexity score;
the prototype's illustrative scalar fields are not treated as measured evidence.

| Design | Lifecycle truthfulness | Recovery and proof surface | Test-selection risk | Compatibility impact | Modeled labels avoided for exact tracked case | Residual full revalidation |
|---|---|---|---|---|---:|---|
| A — project before final quality | Requires a durable `projected-not-integrated` state because completed source bytes exist before final quality and integration. | Persist intent and effects, then resume the sole final-tree quality cycle; it does not need evidence-segment composition. | Avoids causal test selection because all quality runs on `D`; lifecycle and rollback remain substantial risks. | New pre-quality completion state and historical replay rule. | 20 of 20 duplicate delivery labels; the one final quality cycle still runs. | All six arbitrary/exceptional mutation fixtures. |
| B — proof-carrying post-verification | Preserves `verified(I) -> proven D`, but the final record must separate carried semantic evidence from directly checked completion evidence. | Persist intent, effects, segment bindings, seal, final reduction, and replay receipts. | Causal evidence ownership becomes a security-critical test-selection contract. | Versioned proof, evidence-segment, and verification-composition schemas. | 14 of 20; six projection-local labels remain in the model. | All six arbitrary/exceptional mutation fixtures. |
| C — bounded hybrid | Truthful only if lane classification and the tracked projected state are durable before effects. | Persist a classifier receipt plus lane-specific A/B/full-revalidation checkpoints. | Ordinary tracked avoids selection, but classifier overlap or gaps can under-test. | Multiple lifecycle variants plus classifier-version replay. | 20 of 20 on the modeled ordinary tracked lane. | All six arbitrary/exceptional mutation fixtures. |

A avoided causal evidence selection but moved lifecycle complexity before final quality. B kept the
current lifecycle ordering but introduced a security-sensitive proof and evidence-composition
surface. C retained a simple ordinary tracked lane only by adding classification and lane-specific
replay surfaces. These are trade-offs for DRV-03, not a ranking or recommendation.

### Durable findings and limitations

1. All three designs can be made to fail closed for the frozen ordinary tracked fixture matrix;
   none proves that the production effect inventory is complete.
2. Complete negative extra-diff evidence is indispensable. Ticket-path presence, same bytes, or a
   canonical receipt alone would have missed extra implementation, mode, link, and reconciliation
   mutations.
3. Crash recovery needs named intent/effect/proof/final checkpoints. Exact replay is distinct from
   recoverable partial application, and ambiguity must block.
4. A can avoid a causal test-selection oracle only by changing lifecycle ordering. B preserves
   ordering only by making evidence segmentation part of the trusted proof. C adds a second trusted
   classifier before either behavior.
5. The modeled `20`, `14`, and `20` avoided-label values are prospective logical counts only. The
   prototype's scalar proof-surface fields were illustrative inputs and are not reported as
   measurements. No wall-time reduction, provider behavior, migration compatibility, or production
   security claim was measured.
6. Historical ledgers, ignored sources, provider-mutated runs, reconciliation, arbitrary recovery,
   wiki, Pi, and terminal proof remain outside the narrow ordinary tracked contract.
7. No architecture, schema version, threshold, bypass, or production ticket is selected or
   authorized by DRV-02.

## Unresolved Proof Questions

- Can one contract prove a complete deterministic link-repoint set, including the absence of
  eligible missed links and unrelated edits?
- Which evidence segments can declare stable causal ownership without turning the proof verifier
  into an unsafe general test-selection oracle?
- How should crash checkpoints distinguish pre-projection, post-projection/pre-ledger, and
  post-commit/pre-provider states without rollback or history rewriting?
- Can tracked, ignored, reconciliation, and recovery topologies share one deterministic,
  non-overlapping classifier, or must some always retain full revalidation?
- How should historical ledgers without projection manifests, command timing, or causal evidence
  segmentation replay under a future contract?
- Does the implementation CandidateRef remain externally meaningful after final-tree proof, or
  become an internal predecessor only?
- What prospective wall-time reduction and duplicate-command reduction justify the added proof,
  budget, artifact-generation, checkpoint, and compatibility complexity?

## Out of Scope

- Weakening exact-tree, exact-head, terminal-reachability, or provider readback requirements.
- Treating arbitrary docs-only or same-content drift as deterministic projection.
- Changing merge, reconciliation, bootstrap, publication, wiki, status, or local-Pi authority.
- Rewriting historical ledger events, receipts, gates, branches, or verification claims.
- Selecting design A, B, C, or a production test threshold before DRV-03.
- Implementing the optimization in this frontier publication.

## Frontier / Blocking Edges

1. **Current-flow evidence — DRV-01:** terminally integrated through PR #199. It maps completion
   and revalidation entry points, effect classes, replay paths, mandatory checks, counterexamples,
   and observed duplicate cost, and now unblocks DRV-02.
2. **Disposable design evidence — DRV-02:** the current candidate compares A, B, and C against
   one frozen state/effect matrix with exact, tampering, crash, replay, ignored-source,
   reconciliation, provider, and arbitrary-drift cases. It unblocks DRV-03 only after terminal
   integration.
3. **Human architecture decision — DRV-03:** grill the trade-offs and choose one contract or
   explicitly retain full revalidation. It depends on DRV-01 and DRV-02 and is HITL.
4. Only after DRV-03 may `to-spec` define implementation behavior and `to-tickets` emit production
   slices. No production ticket is present on this frontier.

## Ticket Plan

| ID | Type | Mode | Blocked by | Title | Expected output |
|---|---|---|---|---|---|
| DRV-01 | research | AFK | — | Map the completion-to-delivery revalidation flow | Evidence section in this map plus a bounded current-state/cost report |
| DRV-02 | prototype | AFK | DRV-01 | Prototype projection-proof options | Disposable comparison and durable findings folded into this map |
| DRV-03 | decision | HITL | DRV-01, DRV-02 | Choose final-tree validation architecture | Confirmed decision spec or explicit decision to retain full replay |

## Verification Strategy for the Future Change

- Unit tests for projection normalization, proof digesting, allowlist rejection, replay, and
  tamper detection.
- Integration tests proving exact implementation/final tree linkage and unchanged evidence
  composition.
- State-machine tests across tracked, ignored, reconciliation, recovery, provider-before/after,
  and crash checkpoints.
- Metamorphic negative tests: any extra path/blob/mode/receipt/link/parent change forces full
  revalidation.
- Golden historical-ledger replay without mutation.
- A real repository tracer comparing command count and wall time while demonstrating identical
  final claims and terminal proof.
- Live provider evidence remains separate; this optimization must be testable without provider
  mutation.

## Next Review

After DRV-02 is terminally integrated, DRV-03 must use `grilling` to challenge proof completeness,
lifecycle truthfulness, recovery, compatibility, classifier overlap, and under-testing risk before
confirming a design. Until that human decision, keep the current full delivery-revalidation cycle
unchanged.
