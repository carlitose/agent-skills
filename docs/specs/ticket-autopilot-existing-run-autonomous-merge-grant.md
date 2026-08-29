# Existing-Run Autonomous Merge Grant Bug Analysis

## Artifact Graph

- Artifact ID: `artifact:ticket-autopilot-existing-run-autonomous-merge-grant`
- Role: `spec`
- Standalone: true

### Children

- [EMG-01 register an autonomous grant on an existing run](../tickets/ticket-autopilot-existing-run-autonomous-merge-grant/done/01-register-existing-run-autonomous-grant.md)

## Type

Bug analysis.

## Problem

Ticket Autopilot supports a standing autonomous merge grant only when a run is created with
`run --merge-policy autonomous --merge-actor ... --merge-evidence ...`. A run created with the
manual default cannot later record the same explicit run-scoped authority. When a human says
“merge everything without asking each time” after such a run exists, each otherwise eligible PR
still requires a new exact-head `approve` command.

The exact-head safety rule is correct. The regression is that the runner has no supported way to
bind later human authority once to the existing run and ticket set, leaving the agent to choose
between repetitive prompts and an unsupported ledger rewrite.

## Evidence and Current Behavior

- The public CLI exposes merge-policy inputs only on `plan` and `run`.
- `approve` records one ticket/head-bound decision; it does not create a run grant.
- Ledger validation correctly rejects a manual policy carrying an autonomous grant and rejects a
  grant whose repository, run ID, ticket-set digest, provider, or policy binding is forged.
- Existing autonomous runs already re-read the live PR head, checks, rules, approvals, mergeability,
  and provider capability before each expected-head mutation.
- The observed failure occurred on an existing manual run with a green, mergeable PR: prior generic
  authority could not be registered, so an exact SHA phrase was requested again.

## Root Cause

Grant creation is coupled to `Kernel.create()` and therefore to run initialization. There is no
validated append-only transition from `manual` to `autonomous` for a live existing run, even though
all data needed to construct the immutable binding is already present in the ledger.

## Target Behavior

Add one explicit command:

```text
ticket-autopilot grant-autonomous-merge <run-id> \
  --repo <repository> --actor <identity> --evidence <durable-ref>
```

The command records one immutable autonomous grant against the ledger's current repository identity,
run ID, ticket-set digest, provider, and autonomous policy. It then resumes normal scheduling so an
already open eligible PR can enter the existing exact-head merge critical path without another
per-PR approval.

The CLI does not parse natural-language authority. The calling agent translates the human decision
into explicit actor and durable evidence fields.

## Semantic Invariants

1. Manual remains the default for new runs.
2. The transition is allowed only for a non-terminal manual run whose ledger and history validate.
3. A PR may already be open, but an unresolved provider merge mutation or contradictory merge
   authority fails closed.
4. The first accepted grant is immutable. Exact replay with the same actor and evidence is
   idempotent; a different actor or evidence is rejected.
5. The grant remains bound to the existing repository, run ID, ticket-set digest, provider, and
   policy. It is never global across repositories or runs.
6. Every merge still requires fresh live eligibility and an atomic expected-head provider mutation.
   The grant does not contain or replace the current PR SHA.
7. Simulated, stale, pending, failed, unknown, queue-uncertain, or unsupported provider results
   remain gated.
8. Pause, ticket disposition, source identity, CandidateRef, delivery lineage, and wiki-sync
   authority remain separate and unchanged.
9. The transition and its authority metadata are append-only and visible in `status`.

## Failure Modes

- Missing actor or evidence: reject before mutation.
- Completed or aborted run: reject without changing the ledger.
- Already autonomous with identical grant: return the existing grant without appending history.
- Already autonomous with contradictory authority: reject.
- Existing merge intent/mutation with unresolved outcome: preserve it and fail closed rather than
  changing authority mid-critical-path.
- Provider head changes after the grant: re-read and bind the merge attempt to the newly observed
  eligible head; stale receipts are not reused.
- Crash after grant persistence: resume from the durable grant without requesting authority again
  or duplicating provider mutation.

## Security and Data Concerns

The durable evidence string is provenance, not authentication. The command must not infer identity,
accept silence/AFK as consent, redact or reinterpret existing evidence, or weaken expected-head
provider semantics. Normal command and ledger locking must serialize the policy transition with
scheduler mutations.

## Non-Goals

- A machine-wide or repository-wide “always merge” preference.
- Natural-language intent parsing inside the runner.
- Revoking, downgrading, or replacing an accepted autonomous grant.
- Transferring application authority to a tracked wiki-sync candidate.
- Bypassing checks, branch policy, approvals, queues, or provider readback.

## Implementation Slice

- Add the validated kernel/ledger transition and one public command.
- Reuse the existing autonomous eligibility and exact-head merge path unchanged.
- Project the accepted grant and transition through status and append-only history.
- Update command-surface documentation and context-budget fixtures only when measured output changes.

## Acceptance Outcomes

- A manual run stopped at `pr-open` accepts one explicit actor/evidence-bound grant and integrates the
  eligible exact head without a second approval.
- A multi-ticket run reuses that one run grant for later eligible PRs while re-reading each head.
- Replay is idempotent and contradictory or unsafe transitions fail without provider mutation.
- Existing manual and autonomous creation behavior remains unchanged.

## Verification Strategy

### Unit

- Grant construction, exact binding, transition validation, idempotence, contradiction, terminal
  state, and ledger-history integrity.

### Integration

- Real local Git plus deterministic provider adapter: manual run to `pr-open`, grant command, fresh
  eligibility, expected-head merge, readback, and integration.
- Multi-ticket reuse, changed-head revalidation, unresolved mutation rejection, and crash resume.

### Regression

- Full Ticket Autopilot suite, CLI help/command parsing, context-budget checks, and the forward-test
  autonomous merge scenario.

### Live boundary

A live provider run may prove GitHub transport and policy behavior, but local simulated evidence must
not be promoted to a live-provider claim.

## Assumptions

- The human supplies a durable actor/evidence reference through the calling agent.
- Backward compatibility is required for existing schema-4 manual ledgers because they are the
  affected inputs; no legacy command alias is required.

## Unresolved Questions

None. The command is deliberately run-scoped and append-only rather than a global preference.
