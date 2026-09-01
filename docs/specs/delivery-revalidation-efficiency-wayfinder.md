# Delivery Revalidation Efficiency Wayfinder

## Artifact Graph
- Artifact ID: `artifact:delivery-revalidation-efficiency-wayfinder`
- Role: `wayfinder`
- Standalone: true

### Children
- [DRV-01 — Map the completion-to-delivery revalidation flow](../tickets/delivery-revalidation-efficiency/done/01-map-current-flow-and-cost.md)
- [DRV-02 — Prototype exact projection proofs and lifecycle ordering](../tickets/delivery-revalidation-efficiency/02-prototype-projection-proof-options.md)
- [DRV-03 — Choose the final-tree validation architecture](../tickets/delivery-revalidation-efficiency/03-choose-final-tree-validation-architecture.md)

## Type
Wayfinding spec

## Status
Active. DRV-01 current-flow evidence is complete in the candidate linked below; it does not
become terminal frontier evidence or unblock DRV-02 until its exact delivery head is integrated.
No implementation design is selected.

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

1. **Current-flow evidence — DRV-01:** the candidate maps completion and revalidation entry
   points, effect classes, replay paths, mandatory checks, counterexamples, and observed duplicate
   cost. It unblocks DRV-02 only after terminal integration.
2. **Disposable design evidence — DRV-02:** compare A, B, and C with state-machine/proof fixtures,
   including tampering, crash, ignored-source, reconciliation, and arbitrary-drift negatives.
   It depends on DRV-01.
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

After DRV-01 is terminally integrated, run DRV-02's disposable comparison. Then DRV-03 must use
`grilling` to challenge proof complexity, lifecycle truthfulness, recovery, and under-testing
risk before confirming a design. Until that human decision, keep the current full
delivery-revalidation cycle unchanged.
