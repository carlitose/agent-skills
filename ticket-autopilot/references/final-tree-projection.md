# Final-tree projection and exact source recovery

Load only for this operational branch. [Ticket Autopilot](../SKILL.md) owns scheduling; this
reference owns this branch's operator procedure. CLI `<command> --help` remains the syntax
authority.

## Contract

New `plan`/`run` persist `--final-tree-mode off|observe|enabled`, default `enabled`; historical
absence stays literal and malformed values fail closed. For tracked completion, observe builds a
content-addressed manifest from implementation CandidateRef `I`, binding ticket identity, receipt,
link closure, unique effects, complete raw no-renames `I → D` rows, and no-extra-row proof;
finalizer records parity/discrepancy. Enabled persists intent before effects, applies/reads each
move, receipt, and link once, proves the complete tree, then binds `D` at `final-tree-bound` as
`projected-not-integrated`. Prefixes resume; final replay is `already-applied`; contradictions block
rollback, publication, provider mutation, integration, and pending restoration. After
simplification, enabled scheduling adopts `D` as a fresh generation, clears leaf evidence, runs
`review → qa-plan → qa-execute → verify → finalize` once on `D`, and binds `quality-complete` before
delivery. Final stage failure retries the same local `D`; semantic implementation drift archives
lineage and restarts `implement` without path rollback; projection only contradiction stays in exact
recovery. Neither mode transfers evidence, satisfies gates, or grants completion, publication,
recovery, provider, or merge authority.
Ignored/recovery/reconciliation/provider/drift/ambiguity/untracked/extra-effect cases retain the
full process; `status` exposes checkpoints, quality, and all-false authority. For an ignored-source
ticket containing a same-digest regular non-executable canonical `done/` receipt,
`grant-completion-projection <run> --repo <repository> --ticket <id> --expected-tree <tree> --actor
<identity> --evidence <durable-ref>` records an exact
repository/run/ticket/snapshot/CandidateRef/destination grant and may resolve only its
`source-mode-drift` gate after index/tree and caller-source bytes/mode validation. Replay is
idempotent; drift, contradiction, tracked source, extra paths, or unrelated gates fail closed. Drift
never retargets authority: a new actor/evidence call appends a successor; only the newest exact
match is active. Legacy singleton grants remain entry one; mutated, deleted, reordered, branching,
or same-candidate contradictory lineage fails closed. A tracked-base gate requires: lock-held proof
of the same run branch, runner-shaped prepared commit and parent/tree, ignored CandidateRef lineage,
newest grant, and a fresh terminal branch lacking destination and head ancestry. Preserve its
observation; integrated, fetched, reconciled, arbitrary, stale, changed-branch, or multiple-gate
cases remain blocked. Grants and delivery-head proofs never migrate source ownership or grant merge,
provider, wiki, finalization, or implementation-evidence authority; descendants never inherit them.

## Operator procedure

## Tracked final-tree projection

New `plan` and `run` invocations persist `--final-tree-mode off|observe|enabled`;
the default is `enabled`. Explicit `observe` and `off` remain supported, strict operator
selections. Historical ledgers without this configuration remain literal and continue
through the established delivery path. Unknown or malformed configuration fails closed.

In `observe` mode, an ordinary tracked ticket is inspected immediately before the
existing completion move. The runner builds the expected completion receipt from the
implementation CandidateRef `I`, computes the full link-repoint closure, simulates the
exact `I → D` index/tree transition in a temporary Git object database, and writes a
canonical content-addressed manifest. The manifest binds source bytes, mode and digest,
the receipt, every unique completion effect, the complete raw no-renames tree diff, and
a negative proof that no extra row exists. After the unchanged finalizer produces `D`,
a second content-addressed artifact records parity or the exact discrepancy.

Projection requires the tracked ticket's working-tree bytes to equal its staged Git
blob. LF and CRLF are both supported when those bytes agree; Git can report a clean
worktree even when EOL conversion makes them differ. A `source-content-drift`
exclusion occurs before completion effects and does not normalize ticket content.
Inspect `git check-attr text eol -- <ticket>` and
`git config --show-origin --get core.autocrlf`, then make the ticket's declared
attributes/EOL policy and checkout/index bytes agree before retrying. Do not change
global settings or renormalize the whole repository to repair one source. Disposable
Git tests use their own configuration and explicit UTF-8/LF fixture writes; intentional
CRLF cases traverse the real Git clean/index boundary.

These artifacts are observations only. They do not move a ticket, record a completion
effect, transfer review/QA/verification evidence, change the authoritative CandidateRef,
publish, recover, open or merge a PR, or satisfy any gate.

In `enabled` mode, the same exact eligible manifest becomes a durable local transaction.
The runner persists immutable intent before touching the repository, applies each unique
move, receipt, and link effect at most once, and persists readback after each effect. It
then records `effects-read-back` only after the index, worktree, raw no-renames `I → D`
rows, and no-extra-path boundary all match the manifest. Only that complete readback may
bind `D` at `final-tree-bound` and record `projected-not-integrated`. A crash after intent,
a partial effect, aggregate readback, or final binding resumes from the persisted prefix;
exact final replay returns `already-applied`. Changed files, contradictory checkpoints,
duplicate identities, unexpected paths, or an impossible source/destination topology
block without rollback, publication, provider mutation, or integration claims. An
interrupted transaction is never moved back to pending.

After simplification, `enabled` mode (the default for new runs) completes this transaction
before review, adopts exact `D` as a new artifact generation, clears all leaf evidence, and runs
`review → qa-plan → qa-execute → verify → finalize` once against `D`. A versioned
`quality-complete` checkpoint binds those stages and their generation to the immutable
transaction; delivery rejects a projected tree without that binding. A failed final stage
stays local and resumes that stage on the same `D`. Semantic implementation drift archives
the projection lineage and restarts at `implement` without moving the ticket back to its
pending path; projection-only contradictions remain in exact transaction recovery. Ignored
sources, existing provider or reconciliation state, recovery paths, source/mode/digest
drift, ambiguous indexes, untracked files, or any extra effect are excluded before intent.
The content-addressed exclusion binds that artifact generation, so later delivery cannot
re-enter the lane after final quality; these cases retain the complete lifecycle. `status`
exposes the selected mode and contract version, lane plan or exclusion reason, projection state
and checkpoints, quality binding, rollback behavior, and explicit all-false projection authority.
To roll back new projections, select `off`; a persisted intent still
finishes exact replay or remains visibly blocked under its recorded contract version, and
history is never rewritten. Before integration, failed final quality remains remediation on the
original active ticket at exact `D`; after integration, a discovered defect requires a linked
follow-up ticket. None of these states grants completion, provider, merge, terminal, wiki, Pi,
status-change, cleanup, or active-session reload authority.

For a retained, deterministic rollout check, run
`python3 ticket-autopilot/scripts/final_tree_forward_test.py <fixture.json> --output <report.json>`.
The fixture must bind exact `I`, `D`, completion receipt, final Verification Record, rendered
body, provider head/readback, and fresh terminal proof. The harness re-plans production observe
and enabled state in disposable repositories, proves exact replay and `off` rollback behavior,
and runs the frozen negative-classification matrix without provider mutation. Its report contains
logical counts only and grants no authority. See
[Final-Tree Observation, Parity, and Rollback
Evidence](../../docs/research/delivery-revalidation-final-tree-observation-evidence.md).

## Exact tracked completion projection

A narrow exception permits an ignored-source run to publish one candidate-only
completion receipt at the canonical tracked `done/<original-name>` path. It requires
an explicit actor/evidence-bound grant for the exact repository, run, ticket, source
snapshot, CandidateRef tree, digest, and destination:

```bash
python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  grant-completion-projection private-my-change --repo . \
  --ticket MY-01 --expected-tree <candidate-tree-oid> \
  --actor "alice@example.com" \
  --evidence "artifact://change-123/exact-completion-projection"
```

The command first validates the Git index/tree, the ignored CandidateRef base, the
caller-owned source, exact normalized digest, canonical destination, and regular
non-executable mode. It then persists an immutable grant before resolving only the
matching open `source-mode-drift` gate. Exact replay is idempotent; conflicting
identity, source, destination, mode, digest, candidate, base, or gate state fails
closed.

A gate that literally recorded `base_classification: tracked` remains forbidden except
for one post-commit recovery. Under the run lock, the command must prove that the
current branch has the recorded run branch, that `HEAD` is the runner-shaped
`ticket <id>: complete` commit whose parent and tree equal the prior prepared
CandidateRef, that the current candidate has the same ignored base lineage, and that a
freshly fetched terminal branch neither contains the destination nor contains that
head. The content-addressed proof binds the repository, run, ticket, snapshot, newest
grant, CandidateRef, gate, branch/head/parent, terminal observation, and provenance;
it is stored on the unchanged tracked-base gate. Integrated, fetched, reconciled,
arbitrary, changed-branch, stale-preparation, or multiple-gate cases remain blocked.
Grant persistence occurs before proof-bound resolution, so a crash can leave only a
valid successor plus an open gate; replay cannot duplicate the grant or infer proof. A
source already marked completed is admitted only at that exact recovery gate or on exact
resolved-grant replay; ordinary completed tickets remain terminal.

Candidate drift never retargets a grant. A later exact candidate requires another
explicit invocation with its own actor and durable evidence. The command appends that
successor after the immutable predecessor, and only the newest exact matching grant is
active; status reports its sequence, identity, predecessor, and total lineage count.
Legacy singleton grants remain readable as entry one. Reusing different actor/evidence
for a candidate that already has a grant remains a contradiction, while deleting,
reordering, mutating, or branching grant lineage is ledger corruption.

The open/current source remains ignored and caller-owned, the candidate may track only
that one same-digest `done/` blob, and finalization still performs the normal
ignored-source move and completion summary outside the PR. This authority does not
migrate source ownership, propagate to descendants or drifted candidates, authorize
merge/provider/wiki actions, or allow the projection to serve as implementation
evidence.
