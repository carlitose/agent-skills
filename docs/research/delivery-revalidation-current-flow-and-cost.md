# Delivery Revalidation Current Flow and Cost

## Artifact Graph
- Artifact ID: `artifact:delivery-revalidation-current-flow-and-cost`
- Role: `research`
- Parent: [DRV-01 — Map the completion-to-delivery revalidation flow](../tickets/delivery-revalidation-efficiency/done/01-map-current-flow-and-cost.md)

## Status

DRV-01 current-state investigation complete at repository commit
`693b9e18f15614589a0c55229cbdcbd763021f65`, tree
`dc74894e00a1da54b532f9ead12fcd19da4deb59`. This report describes existing behavior; it does
not select a design, test-selection rule, compatibility policy, or production change.

## Bounded Question

Which exact state transitions and completion effects force delivery revalidation today, and which
parts of the repeated quality cycle are causally necessary for an exact final-tree claim?

## Terminology and Binding

A schema-2 `CandidateRef` is the tuple owned by
[`candidate_contract.py`](../../ticket-autopilot/scripts/autopilot/candidate_contract.py):

- `base_tree_oid` — the frozen comparison tree;
- `candidate_tree_oid` — the exact staged candidate tree;
- `ticket_digest` — the frozen ticket bytes normalized by the ticket contract;
- `contract_version` — currently `2`.

An implementation CandidateRef (`I`) and a completion-projected delivery CandidateRef (`D`) may
share the base tree and ticket digest while differing in candidate tree. All leaf handoffs,
quality evidence, rendered PR bodies, provider heads, and verification claims are exact-CandidateRef
claims; similarity between `I` and `D` is not a proof.

The current runner also has an **ignored-source completion projection authority**. That authority
is a source-ownership mechanism and is not the future projection-proof optimization studied by
this frontier.

## Owning Production Modules

| Concern | Owner and current responsibility |
|---|---|
| Candidate identity and Git tree derivation | [`candidate_contract.py`](../../ticket-autopilot/scripts/autopilot/candidate_contract.py) defines the contract; [`git_ops.py`](../../ticket-autopilot/scripts/autopilot/git_ops.py) derives a CandidateRef from the exact index and base tree. |
| Scheduler entry points | [`cli.py`](../../ticket-autopilot/scripts/autopilot/cli.py) derives current Git state and handles `stage`, `delivery-revalidate`, `delivery`, reconciliation, integration, recovery, and post-integration commands. |
| State machine and invalidation | [`kernel.py`](../../ticket-autopilot/scripts/autopilot/kernel.py) owns stage order, CandidateRef adoption, artifact generations, leaf budgets, delivery/reconciliation revalidation, effects, gates, merge authority, and integration state. |
| Leaf evidence | [`leaf_protocol.py`](../../ticket-autopilot/scripts/autopilot/leaf_protocol.py) binds review, QA, and verification handoffs and budgets to one CandidateRef. |
| Tracked and ignored delivery effects | [`finalizer.py`](../../ticket-autopilot/scripts/autopilot/finalizer.py) owns source-mode checks, tracked/ignored finalization, completion summaries, delivery commit/push, render requests, and provider PR creation. |
| Link changes | [`link_repoint.py`](../../ticket-autopilot/scripts/autopilot/link_repoint.py) computes Markdown links that must move with a tracked ticket. |
| Source snapshot and classification | [`ticket_source.py`](../../ticket-autopilot/scripts/autopilot/ticket_source.py) freezes source bytes, folder identity, disposition, tracking mode, and selected base in a content-addressed manifest. |
| Lifecycle truth | [`ticket_lifecycle.py`](../../ticket-autopilot/scripts/autopilot/ticket_lifecycle.py) validates source disposition independently from execution state. |
| Docs-only exception | [`docs_only.py`](../../ticket-autopilot/scripts/autopilot/docs_only.py) and [`docs_only_contract.py`](../../ticket-autopilot/scripts/autopilot/docs_only_contract.py) revalidate their narrow receipt instead of using the ordinary full pipeline. This is a separate existing contract, not a generic completion proof. |
| Durable ledgers and replay | [`ledger.py`](../../ticket-autopilot/scripts/autopilot/ledger.py) validates schema-4 envelopes and lifecycle/projection receipts; [`history_codec.py`](../../ticket-autopilot/scripts/autopilot/history_codec.py) preserves canonical snapshot/delta replay and event hashes. |
| Reconciliation | [`reconciliation_intent.py`](../../ticket-autopilot/scripts/autopilot/reconciliation_intent.py) validates exact target-only intent refreshes; [`repository_reconciliation_authority.py`](../../ticket-autopilot/scripts/autopilot/repository_reconciliation_authority.py), `cli.py`, and `kernel.py` keep reconciliation authority, prepared lineage, and revalidation separate. |
| Provider operations | [`providers.py`](../../ticket-autopilot/scripts/autopilot/providers.py) normalizes PR read/write, expected-head merge, policy, and readback operations. |
| Terminal proof | [`terminal_integration.py`](../../ticket-autopilot/scripts/autopilot/terminal_integration.py) fetches a fresh terminal ref and proves the exact PR head or merge commit reaches it. |
| Incompatible historical runs | [`legacy_recovery.py`](../../ticket-autopilot/scripts/autopilot/legacy_recovery.py) applies actor-authorized, digest-bound migration or retirement without converting old evidence into a new final-tree claim. |
| Post-integration consumers | [`wiki_sync.py`](../../ticket-autopilot/scripts/autopilot/wiki_sync.py) and [`pi_sync.py`](../../ticket-autopilot/scripts/autopilot/pi_sync.py) are separately authorized consumers after integration; neither establishes delivery verification or terminal proof. |

## Exact Normal Tracked Call Graph

1. `cli._resume()` handles `stage` events. It derives the current CandidateRef from the isolated
   worktree and either calls `Kernel.adopt_implementation_candidate()`, calls
   `Kernel.invalidate_for_candidate_drift()`, or records the exact stage result.
2. `Kernel.record_stage()` validates structured leaf handoffs for `review`, `qa-plan`,
   `qa-execute`, and `verify`. A passing `finalize` transition leaves the ticket `verified`, with
   every `validated_stages` entry bound to `I`.
3. A `delivery` event calls `DeliveryFinalizer.apply()`:
   1. `_ensure_branch()` binds the branch base tree.
   2. `finalize_done()` rechecks tracked source mode, moves the pending path to `done/`, calls
      `repoint_moved_file()`, stages the source/destination/repoint set, and records the
      `move-done-and-stage` effect.
   3. `_ensure_summary()` writes and stages `done/<ticket>.completion.json`, then records the
      `completion-summary` effect.
   4. `candidate_ref()` derives `D` from the exact index; `Kernel.record_delivery_candidate()`
      stores it separately from `I`; `delivery.prepared` freezes it.
   5. `_ensure_commit()` rejects any staged tree other than `D`; `_ensure_push()` publishes the
      exact delivery head; `_render_request()` creates a content-addressed request.
4. A subsequent `delivery-revalidate` event derives the current CandidateRef again. If it differs
   from `I`, `Kernel.prepare_delivery_revalidation()`:
   - sets both `candidate_ref` and `delivery_candidate_ref` to `D`;
   - changes `verified -> active`, `stage: null -> review`;
   - retains only `implement` and `simplify` in `validated_stages`;
   - replaces the leaf budget, clears leaf progress/handoff/results and reservation completion;
   - increments `artifact_generation`;
   - clears merge authorization and docs-only state;
   - removes stale PR-body request/body, PR, provider simulation, and result records;
   - emits `delivery-revalidation-required`.
5. The scheduler repeats `review -> qa-plan -> qa-execute -> verify -> finalize` against `D`.
   No implementation stage is rerun because the runner treats the completion effects as a
   delivery projection, but there is no narrower proof for any downstream stage.
6. `DeliveryFinalizer.apply()` rechecks `D`, creates or recovers the exact commit/push, renders a
   new request from the `D` verification bundle, executes `create-or-update-pr`, validates live
   body/head readback, and records the PR lineage.
7. Merge authorization remains separate. Integration performs provider `get-pr-state` readback,
   then `build_terminal_integration_proof()` fetches the terminal branch, checks stable remote
   readback, and proves exact-head or merge-commit ancestry before `Kernel.record_integration()`
   or `record_external_integration()` can mark terminal integration.
8. Wiki publication and local Pi synchronization may run only under their own post-integration
   contracts. They do not amend the CandidateRef or retroactively strengthen delivery evidence.

### Provider-before/after detail

The first delivery preparation may create and push the Git delivery commit before revalidation.
Historical OHR-02 sequences 99–111 show branch, move, summary, delivery CandidateRef, commit,
push, and render-request records before sequence 112 triggers revalidation. No provider PR was
created: the stale render request/result were removed. After revalidation, sequences 123–132
recover commit/push idempotently, bind a new render request/body to `D`, and only then create PR
#193. Thus a remote branch effect may precede full revalidation, but provider PR mutation cannot
consume the stale implementation-tree render bundle.

## Effect and Evidence-Invalidation Inventory

| Effect | Exact path/blob/mode/tree/receipt/link/ledger change | Evidence invalidated or preserved |
|---|---|---|
| Source snapshot | Records each ticket path, exact content digest, disposition, source mode, selected base SHA, and ignored-folder device/inode in `ticket-source/manifest.json`. No candidate tree changes. | Preserved for the run. Any source/path/mode/base contradiction fails before delivery; it is not repaired by quality reruns. |
| Tracked move | Pending path becomes absent; `done/<name>.md` appears with the identical ticket blob and mode. Git represents this as delete/add unless rename detection is requested. Index tree changes `I -> D`. Ledger `current_source_relative_path` becomes `done/...`, disposition becomes `completed`, and an effect key binds run, ticket, effect, and CandidateRef. | Invalidates every leaf result and verification bundle whose CandidateRef contains `I`; preserves the frozen ticket digest and bytes. |
| Link repoint | Every repository-owned Markdown link to the old path is rewritten to the new path and staged in the same tree. Link blobs change; modes must not. | Invalidates claims over changed linking documents and Artifact Graph/link integrity. It does not inherently invalidate semantic claims over untouched implementation paths, but the current ledger cannot express that separation. |
| Completion summary | Adds `done/<name>.completion.json` with schema, run/ticket identity, ticket digest, source mode, CandidateRef/provenance data, and validated stages. Its blob is part of `D`; effect is append-only. | Requires direct receipt schema/content validation. Broad implementation tests are not causally required unless they consume the receipt or changed graph. |
| Delivery CandidateRef | Recomputes the exact index tree after move, summary, and links; stores `delivery_candidate_ref=D` and `delivery.prepared`. No path changes itself. | Makes the mismatch with `I` explicit. Merge authorization is cleared whenever candidate identity changes. |
| Delivery revalidation transition | No file changes. Rebinds `candidate_ref` to `D`, increments artifact generation, resets downstream state and budgets, and removes stale render/provider records. | Ledger references to review, QA, verification handoffs are invalidated wholesale. Artifact files remain on disk as historical evidence but are no longer current leaf results. |
| Repeated quality cycle | No required tree changes. Adds new CandidateRef-bound leaf events/results, QA artifacts, cache decisions, and a verification bundle for `D`. | Establishes a final-tree claim. Current behavior cannot carry forward unchanged causal segments, so all downstream evidence is regenerated. |
| Commit and push | Commit tree must equal `D`; branch/head lineage and idempotent effects are recorded; remote branch becomes that head. File modes/blobs are exactly those in `D`. | Invalidates any render request for another head or CandidateRef. Push is Git remote mutation, not merge or terminal-proof authority. |
| PR render/provider mutation | Render request hash binds ticket, `D`, artifact generation, changed paths, verification bundle, branch/base, and expected head. Provider body/head readback must be exact. | Stale body, bundle, head, or request hash is rejected. PR creation grants no merge authority. |
| Merge and terminal proof | Provider intent precedes expected-head mutation; live readback records head/base/merge commit. Fresh terminal proof records terminal branch SHA/tree, reachable object, provider-observation digest, delivery-lineage digest, and provenance. | A provider `merged` label without fresh reachability is insufficient. Terminal proof does not authorize wiki, Pi, reconciliation, or publication effects. |
| Ignored-source move | Outside Git, exact source bytes move to `done/` using no-clobber rename; a canonical summary is atomically written. Git tree and file modes are unchanged. Ledger stores intent then applied receipt and `move-done-and-summarize-external`; terminal result remains externally unpublished. | CandidateRef-bound Git evidence can remain current only if the tree is unchanged. Source digest, folder identity, source mode, destination uniqueness, and explicit completion-projection authority remain independently mandatory. |
| Reconciliation revalidation | Rebase/target refresh changes base/head and may change candidate tree. Prepared intent binds old/new heads, target branch/ref/SHA/tree, expected remote SHA, and provider readback. Kernel resets to review or, for arbitrary late drift, to implement; sealing appends old render receipts and new lineage. | Invalidates old-base CandidateRef evidence, PR body, head-bound authorization, and stale reconciliation intent. Reconciliation authority cannot carry quality evidence by itself. |
| Recovery/replay | Durable intent/effect/readback records distinguish not-started, applied, and ambiguous states. Exact repeated effects return no-op; source/destination contradiction, duplicate destination, unproven branch, or changed CandidateRef gates/fails. | Preserves literal history and only reuses evidence with an identical CandidateRef and valid receipt. Recovery authority is not gate approval or merge authority. |
| Historical ledger migration/retirement | Schema-3 migration appends a lifecycle event; schema-1/2 retirement writes a separate receipt. Schema-4 event snapshots/deltas and optional fields replay literally. No candidate tree is synthesized. | Historical evidence is never upgraded into a projection proof. Missing optional fields remain missing; tampered event hashes, deltas, receipts, or terminal-proof bindings fail. |

## State/Effect Matrix

| Scenario | Entrance and state transition | Required exact checks/effects | Replay and authority boundary |
|---|---|---|---|
| Normal tracked completion | `verified(I)` → finalizer effects → `delivery_candidate_ref=D` → `active(D, review)` → `verified(D)` → `pr-open` | Same ticket blob/mode at new path; old path absent; canonical summary; exact allowed link blobs; no extra index delta; exact commit tree/head/body/bundle. | Move, summary, commit, and push have CandidateRef-bound idempotency keys. Runner source ownership does not imply merge authority. |
| Ignored source | `verified(I)`; external move/summary; Git CandidateRef normally remains `I` | Frozen source digest and folder inode/device; ignored remains ignored in checkout/base; no-clobber destination; exact intent/applied receipts; no Git staging. | Crash after move resumes from persisted intent and exact destination. Tracking drift, duplicate paths, or changed bytes fail. Publication remains external/unpublished. |
| Reconciliation | `pr-open(old base/head)` → prepared exact reconciliation → `active(new candidate, review)` or arbitrary drift → `implement` → verified/sealed new head | Exact target-only intent refresh; base tree, old/new local heads, expected remote head, lease, provider PR identity, new CandidateRef, new body/head. | Reconciliation grant is separate; stale/ambiguous provider or branch state gates. Old render records move to append-only history when sealed. |
| Post-commit recovery | Runner-authored completion commit exists but later CandidateRef/source mode differs | Prove exact prepared branch, parent tree, head tree, commit marker, terminal non-reachability, active successor grant, and source classification. | Identical recovery replays; historical grants cannot become active for a reverted/new CandidateRef; arbitrary or already-integrated heads cannot consume the gate. |
| Crash during tracked move | Source and destination/index/ledger may be between checkpoints | Both existing or both absent contradict finalization; ledger effect must agree with worktree; staged tree must equal prepared CandidateRef. | Existing exact effect returns no-op. Contradiction is a visible gate/error, never a second blind move. |
| Crash during ignored move | Intent may be durable while source has moved and applied receipt is absent | Destination digest must equal frozen source; summary digest must equal intent; destination must not predate intent. | Resume writes summary/applied receipt once. Concurrent destination never gets overwritten. |
| Provider before revalidation | Branch commit/push and stale render request may exist; ticket is still `verified(I)` with `delivery_candidate_ref=D` | Delivery commit tree is `D`; later `delivery-revalidate` must derive `D`, clear stale request/result, and complete quality stages before PR creation. | Git remote branch is recoverable but conveys no provider, merge, or terminal authority. |
| Provider after PR mutation | `pr-open` with exact branch/head/base and body readback | Candidate drift is not an ordinary verified-state revalidation; it requires bounded PR reconciliation/update with fresh body, head, authorization, and readback. | Expected-head/provider receipts prevent stale mutation replay. External merge remains observation unless exact merge authority was consumed. |
| Terminal proof | Provider reports merged exact PR | Fresh fetch, stable `ls-remote`, terminal SHA/tree, commit existence, and ancestry of exact head or merge commit; proof digests bind provider observation and lineage. | Replayed proof must be byte-equivalent. Provider state alone cannot mark integration. |
| Historical schema/receipt | Old envelope or event history is loaded | Canonical event hash chain/deltas, literal snapshots, optional-field compatibility, exact migration/retirement authority. | Append migration/retirement only; never rewrite events or infer a modern projection proof. |
| Post-integration wiki/Pi | Ticket is durably integrated | Exact integrated head plus separate actor/evidence-bound consumer configuration; wiki publication may create a separate frozen candidate. | Integration remains final if consumer sync gates. No active-session reload is inferred. |

## Causally Necessary Final-Tree Checks

The following checks are necessary even if broad suite repetition is removed in a future design:

1. Re-derive `D` from the exact index with replacement objects disabled where raw object proof is
   required; bind base tree, ticket digest, and contract version.
2. Prove an exact, complete path/blob/mode transition: old tracked ticket absent, new tracked ticket
   present, same non-empty blob and mode, canonical completion receipt present, and no unlisted
   path or index-stage change.
3. Validate every changed link blob against a complete deterministic repoint manifest, including
   a negative proof that no eligible link was missed and no unrelated text changed.
4. Validate lifecycle ordering and append-only ledger effects: intent before mutation, one effect,
   current source/disposition agreement, artifact generation, and crash-safe replay.
5. Re-run checks that consume changed paths or receipts: ticket-source, lifecycle, link/Artifact
   Graph, summary schema, source-mode, and delivery commit cleanliness.
6. Reduce a final verification record whose current CandidateRef is exactly `D`; unchanged
   evidence may be carried only through a future explicit causal proof.
7. Bind render request, PR body, commit tree, pushed head, provider readback, expected-head merge,
   and fresh terminal reachability to the same final delivery lineage.

## Broad Checks Repeated Because No Narrow Proof Exists

The current kernel clears all leaf results, not just those causally touched by projection. It
therefore repeats:

- full semantic review of unchanged implementation modules;
- reconstruction of a QA plan whose implementation-risk groups are unchanged;
- repository-wide Ticket Autopilot, verification-audit, LLM Wiki, extension, and often Artifact
  Graph suites even when only ticket lifecycle paths changed;
- full verification checkpoint and bundle reduction rather than composing unchanged evidence with
  direct completion checks.

These checks are not declared unnecessary in general. They are **unclassified**: the current
ledger cannot prove which evidence segments are unaffected. A changed-path heuristic is
insufficient because receipt readers, graph edges, generated links, source classification, and
lifecycle code can have non-local consequences.

## False Positives and Must-Revalidate Negatives

### Conservative full-revalidation false positives

A “false positive” here means the current runner required the complete downstream cycle although
raw inspection found only runner-authored completion effects and the broad suites returned the
same results. It does not mean the checks were unauthorized or that they may now be skipped.

- **CST-04:** `5ec4eca9… -> 794d6f86…` changed only the status spec link, moved the exact ticket,
  and added its completion receipt. Both cycles reported 702 Ticket Autopilot, 76
  verification-audit, 165 LLM Wiki, and 6 extension tests passing.
- **OHR-01:** `f902ee98… -> c5334135…` changed two linked research/map documents, moved the exact
  ticket, and added its receipt. Both cycles reported 702/76/165/24/6 tests passing.
- **OHR-02:** `3cd90d9b… -> 572141fa…` changed three linked documents, moved the exact ticket, and
  added its receipt. Both cycles reported 702/76/165/24/6 tests passing.

### Must-revalidate negatives

- **CST-03 is the real counterexample:** `e5dd1086… -> 1e110c43…` included the ordinary spec
  repoint, ticket move, and receipt **plus new blobs in `kernel.py` and `test_kernel.py`** after a
  provider-free finalization attempt exposed optional-field migration. A classifier based on
  “contains a completion move” would have under-tested a semantic runner fix.
- Any extra path, changed ticket blob or mode, noncanonical receipt field, unexpected link edit,
  unmerged/duplicate index entry, stale CandidateRef, or mismatched base requires full
  invalidation.
- Ignored-source digest, folder identity, source-mode, destination, or authority drift is not a
  tracked deterministic projection.
- Reconciliation base/head/target/lease drift, arbitrary post-commit head changes, or provider
  mutation introduces independent effects and authority; these cannot inherit an implementation
  proof.
- Tampered proof/ledger history, duplicate effect, ambiguous crash state, or missing negative
  extra-diff evidence must fail closed.

## Completed-Run Cost Measurements

### Reproducible method

The samples are read-only schema-4 ledgers under Git common state. The method:

1. Load the ledger envelope’s `payload.history`.
2. For each ticket, split history at its `delivery-revalidation-required` event.
3. Select the last complete CandidateRef epoch before the split and the epoch after it.
4. Count `leaf-result-recorded` events as leaf interactions.
5. Count each string in the structured leaf handoff `commands_run` arrays recovered from the
   corresponding `stage-passed.snapshot_delta` as one **recorded command/check label**. This is
   the runner’s durable count, not an operating-system process count.
6. Sum `leaf-result-recorded.details.wall_time` for each epoch.
7. Cross-check broad-suite counts against the candidate-bound QA result artifacts and raw logs.
8. Hash the source ledgers before and after inspection.

Equivalent read-only extraction can be reproduced with:

```bash
python3 - <<'PY'
import json
from pathlib import Path

runs = Path('/Users/carlogiuseppesergi/Projects/agent-skills/.git/ticket-autopilot/runs')
samples = [
    ('change-status-ticket-production-20260831', 'CST-03'),
    ('change-status-ticket-production-20260831', 'CST-04'),
    ('llm-wiki-obsidian-hybrid-retrieval-v2-20260901', 'OHR-01'),
    ('llm-wiki-obsidian-hybrid-retrieval-v2-20260901', 'OHR-02'),
]
for run_id, ticket_id in samples:
    history = json.loads((runs / run_id / 'ledger.json').read_text())['payload']['history']
    cut = next(i for i, event in enumerate(history)
               if event.get('ticket_id') == ticket_id
               and event.get('event') == 'delivery-revalidation-required')
    print(run_id, ticket_id, 'revalidation_sequence', history[cut]['sequence'])
    for label, epoch in (('implementation', history[:cut]), ('delivery', history[cut + 1:])):
        relevant = [event for event in epoch if event.get('ticket_id') == ticket_id]
        if label == 'implementation':
            starts = [i for i, event in enumerate(relevant)
                      if event.get('event') in {'candidate-adopted', 'candidate-invalidated'}]
            if starts:
                relevant = relevant[starts[-1] + 1:]
        command_labels = []
        wall_time = []
        for event in relevant:
            if event.get('event') == 'leaf-result-recorded':
                wall_time.append(event['details']['wall_time'])
            if event.get('event') != 'stage-passed':
                continue
            stage = event['details'].get('stage')
            for operation in event.get('snapshot_delta', {}).get('operations', []):
                if operation.get('path', [])[:4] == ['tickets', ticket_id, 'leaf_results', stage]:
                    command_labels.extend(operation['value'].get('commands_run', []))
        print(label, len(command_labels), len(wall_time), sum(wall_time))
PY
```

### Results

| Run / ticket | `I -> D` | Implementation labels / leaf interactions | Delivery labels / leaf interactions | Broad repeated evidence | Durable wall time |
|---|---|---:|---:|---|---|
| `change-status-ticket-production-20260831` / CST-03 | `e5dd1086… -> 1e110c43…` | 24 / 4 | 20 / 4 | Runner 695→696, verification 76→76, wiki 165→165, extension 6→6; not a pure projection because runner code/tests changed | Unavailable: all eight ledger samples are `0` |
| `change-status-ticket-production-20260831` / CST-04 | `5ec4eca9… -> 794d6f86…` | 21 / 4 | 20 / 4 | Runner 702→702, verification 76→76, wiki 165→165, extension 6→6 | Unavailable: all eight ledger samples are `0` |
| `llm-wiki-obsidian-hybrid-retrieval-v2-20260901` / OHR-01 | `f902ee98… -> c5334135…` | 24 / 4 | 20 / 4 | Runner 702→702, verification 76→76, wiki 165→165, Artifact Graph 24→24, extension 6→6 | Unavailable: all eight ledger samples are `0` |
| `llm-wiki-obsidian-hybrid-retrieval-v2-20260901` / OHR-02 | `3cd90d9b… -> 572141fa…` | 21 / 4 | 20 / 4 | Runner 702→702, verification 76→76, wiki 165→165, Artifact Graph 24→24, extension 6→6 | Unavailable: all eight ledger samples are `0` |

Across these four tickets, delivery revalidation consumed 16 additional leaf interactions and 80
recorded command/check labels. Three pure completion samples repeated at least the four broad
repository suites; both OHR samples repeated a fifth Artifact Graph suite.

Wall time is **not measured**. Inline shared-context handoffs recorded `wall_time: 0`, and the
historical logs have no trustworthy monotonic start/end timestamps. Zero is a missing measurement,
not a claim of zero duration. Re-running old commands now would measure a different repository,
cache, toolchain, and machine state, so this report does not manufacture retrospective timing.
Future tracers need runner-recorded monotonic duration and an OS-process manifest at execution
time.

Source ledger SHA-256 identities before and after the read-only measurement were:

- `change-status-ticket-production-20260831/ledger.json`:
  `cb5e2b8c3a9013c678193f8ba608fcae787fa6e212eb4b7cb962aff3eb3fbf2d`;
- `llm-wiki-obsidian-hybrid-retrieval-v2-20260901/ledger.json`:
  `705c949644f31d1885cd5c48f85042e47d92a388f9b108aee5e9852c5d406f07`.

## Representative Raw Tree Evidence

All representative entries were read with `GIT_NO_REPLACE_OBJECTS=1 git diff-tree -r --raw I D`.
Every ticket move preserved its exact `100644` blob:

- OHR-02 ticket blob `e091e04b…` was deleted from the pending path and added unchanged at the
  `done/` path; receipt blob `d8fab3b0…` was added; three Markdown link blobs changed.
- OHR-01 ticket blob `89d1a66a…` was preserved across the move; receipt blob `be6fe1a7…` was
  added; two link blobs changed.
- CST-04 ticket blob `3a9f988f…` was preserved; receipt blob `e814f4fa…` was added; one spec link
  blob changed.
- CST-03 ticket blob `d38df735…` was preserved and receipt blob `e80c674e…` added, but the same
  transition also changed `kernel.py` blob `c0cdf249… -> 361a278b…` and `test_kernel.py` blob
  `d22862b8… -> ac51c7c…`. This is the required negative proof that completion-shaped deltas are
  not necessarily completion-only.

## Representative Test Families

- [`test_kernel.py`](../../ticket-autopilot/tests/test_kernel.py): CandidateRef invalidation,
  delivery/reconciliation revalidation, artifact-generation and budget reset, effect idempotency,
  schema-4 lifecycle compatibility, canonical event replay, history/terminal-proof tamper
  rejection, and terminal reachability.
- [`test_cli.py`](../../ticket-autopilot/tests/test_cli.py): end-to-end tracked completion commit,
  move/summary/link single-tree property, delivery revalidation commit/push/render replacement,
  provider readback, expected-head integration, crash recovery, and equivalent-head paths.
- [`test_ticket_sources.py`](../../ticket-autopilot/tests/test_ticket_sources.py): tracked and
  ignored source classification, exact ignored moves, no-clobber and post-move crash replay,
  digest/folder/source-mode drift, completion projection grants, and post-commit successor proof.
- [`test_history_codec.py`](../../ticket-autopilot/tests/test_history_codec.py): canonical compact
  deltas and exact snapshot reconstruction.
- [`test_legacy_recovery.py`](../../ticket-autopilot/tests/test_legacy_recovery.py): authorized
  migration/retirement, intent-before-effect, crash replay, and literal historical preservation.
- [`test_repository_reconciliation_authority.py`](../../ticket-autopilot/tests/test_repository_reconciliation_authority.py):
  exact repository authority, target refresh, concurrency, and reconciliation replay.
- [`test_provider_pr_body.py`](../../ticket-autopilot/tests/test_provider_pr_body.py): exact body
  transport and provider readback fidelity.
- [`test_pi_sync.py`](../../ticket-autopilot/tests/test_pi_sync.py),
  [`test_wiki_sync.py`](../../ticket-autopilot/tests/test_wiki_sync.py), and
  [`test_wiki_sync_forward_matrix.py`](../../ticket-autopilot/tests/test_wiki_sync_forward_matrix.py):
  post-integration authority separation and exact-head consumer behavior.

## Durable Findings

1. Exact-final-tree verification is necessary; unconditional broad-suite duplication is not itself
   the invariant.
2. The current implementation safely treats any `I != D` drift as unclassified and resets every
   downstream leaf result.
3. A future narrow proof would need complete path/blob/mode/receipt/link/ledger and negative
   extra-diff evidence. “Ticket moved to done” is not a safe classifier.
4. Ignored-source, reconciliation, recovery, provider, terminal-proof, historical-ledger, wiki,
   and Pi boundaries require separate handling and authority even if the common tracked case is
   optimized.
5. Existing ledgers do not provide trustworthy wall time or OS-command counts; future comparison
   must instrument those values prospectively.

## Unresolved Proof Questions for DRV-02/DRV-03

- Can one contract prove a complete deterministic link-repoint set, including the absence of
  eligible missed links and unrelated edits?
- Which evidence segments can declare stable causal ownership without turning the proof verifier
  into an unsafe general test-selection oracle?
- How should crash checkpoints distinguish pre-projection, post-projection/pre-ledger, and
  post-commit/pre-provider states without rollback or history rewriting?
- Can tracked, ignored, reconciliation, and recovery topologies share one non-overlapping
  classifier, or must some always retain full revalidation?
- How are historical ledgers handled when they have no projection manifest, command timing, or
  causal evidence segmentation?
- What proof complexity and prospective wall-time reduction would justify replacing the current
  conservative transition?

## Non-Conclusion

No architecture (pre-quality projection, proof-carrying projection, or bounded hybrid), proof
schema, test-selection policy, compatibility rule, or optimization threshold is selected here.
The current full delivery-revalidation cycle remains mandatory until DRV-02 evidence and the
human DRV-03 decision are complete.
