# Verify a changed merged source

Load when an unstarted successor has an open `post-merge-verification` technical gate and
its integrated predecessor's historical CandidateRef no longer describes the recorded merge
source. This branch provides fresh source quality; it does not reopen delivery or approve live
operations. CLI `post-merge-verify --help` owns argument syntax.

## Bind the source

Use the existing run and gate, plus a clean registered source worktree in the same Git common
directory. Its exact HEAD/tree must equal the gate's version-1 source record. The runner
resolves the uniquely matching integrated dependency and its immutable normalized ticket
snapshot, verifies Git identity without replacement objects, and freezes the new CandidateRef.
It does not trust caller-provided candidates, change either ticket, or own source cleanup.

```bash
"$TICKET_AUTOPILOT_PYTHON" -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  post-merge-verify <run> --repo <repository> --gate <gate-id> \
  --action bind --source-worktree <registered-exact-source>
```

Completion criterion: the runner returns a bound context for the recorded source, both tickets
retain their prior lifecycle/candidates, and the technical gate remains open. Wrong source,
dirt, replacement refs, ambiguous identity, pause/disposition barriers, or an unresolved start
approval must fail rather than creating an active implementation candidate.

## Assess and verify, read-only

Read `--action status` for the current context and budget. Compose serially inline unless
separate-context work was explicitly authorized; do not claim shared-context review is independent.
The phase order is:

1. `implement`: assess the existing implementation on the newly frozen source; do not implement
   the integrated ticket again or modify its worktree.
2. `simplify`: assess clarity/scope without editing this frozen source.
3. `review`, `qa-plan`, `qa-execute`, `verify`: fresh bounded quality for this CandidateRef.

Submit existing schema-3 leaf results with the context's authoritative file order and phase
contract. `--action leaf --input <json>` accepts exactly `leaf_result`, `tool_calls`, and
`wall_time`. Partial work retains its suffix and actual resource deltas. A complete leaf means
its work finished, not that every observation passed; canonical audit still decides readiness.
Same-candidate replay neither resets the budget nor charges an identical interaction again.
Source repairs require normal delivery and a new exact source decision, not edits in this lane.

QA quality references must be existing absolute regular files under the source worktree or the
owning run directory and carry their actual file SHA-256. The runner re-observes these content
addresses at each boundary. It never retrieves artifact URLs. Historical source observations
cannot be relabeled as fresh observations of a changed tree.

Completion criterion: all six read-only assessment/quality leaves are complete on the same
candidate, partial/failure observations remain available, and no source or live effect occurred.

## Canonical audit and condition resolution

Verification Audit consumes the context's normalized predecessor identity, `ticket_envelope_ref`,
CandidateRef and ordinal `criteria`. Each criterion maps to exactly one supported local/test
implementation or behavior claim with the same ID and text. Use the returned `stage_artifacts`
for the five completed assessments and `verify_artifact` for verification; the stable verification
reference avoids a bundle/leaf hash cycle. Copy each returned isolation limitation into its
stage record, including the verification leaf's observed isolation.

The complete verify leaf includes a schema-1 quality evidence item with:

- ID `post-merge:bundle` and result `pass`;
- the exact CandidateRef;
- SHA-256 of the bundle's canonical JSON (UTF-8, sorted keys, compact separators,
  non-ASCII preserved, no NaN and no trailing newline);
- artifact `post-merge-bundle://<that-sha256>`.

This is a semantic bundle address, not a file-content or verification-checkpoint address. The
canonical bundle is supplied to `--action complete --input <bundle.json>`. The runner loads
Verification Audit's actual validator/reducer, rechecks accepted stage/criteria/content bindings,
and requires supported offline readiness. Open live gates may keep release disposition blocked;
no claim tied to an unresolved source criterion can satisfy the technical condition.

The completion transaction first persists the validated audit while the gate remains open, then
rechecks source/artifacts and resolves only this condition with its audit receipt. Human approval
alone cannot resolve it. Interruption between these boundaries replays from the durable audit;
contradictory inputs and source drift fail closed. Other gates and historical delivery remain
unchanged. Ordinary scheduling, not this command, starts the successor afterward.

Completion criterion: the exact gate has its canonical audit receipt, the predecessor is still
integrated under its historical identity, and no successor implementation completion, provider
mutation, merge, canary, deployment, credential, DNS, policy or Pi authority has been inferred.
