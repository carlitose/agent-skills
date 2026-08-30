# Agent Skills

This repository contains composable skills for planning, executing, reviewing,
and improving code workflows. Its main end-to-end runner is `ticket-autopilot`:
it turns a folder of dependency-aware tickets into isolated, independently
reviewed changes and provider-neutral pull requests, while keeping merge
authority and evidence explicit.

## Pi package

The repository is also a Pi package. Its extension routes every natural-language
request through `ask-skills` and requires shippable development work to follow
`to-spec -> to-tickets -> ticket-autopilot`. Slash commands and user `!` shell
commands remain direct operational controls. The mandatory lane does not grant
merge authority; `ticket-autopilot` keeps its manual merge default.

Install globally for every Pi session:

```bash
pi install git:github.com/carlitose/agent-skills@<tag-or-commit>
# During local development:
pi install /absolute/path/to/agent-skills
```

Keep only one loaded copy of each skill. If the same repository is already
installed under `~/.agents/skills`, use Pi's package filtering to disable the
package's `skills` resources while leaving its extension enabled, or remove the
older duplicate installation.

Use `/agent-skills-flow` inside Pi to check that the extension and its four
required workflow skills are available. Run the package tests with `npm test`.

## How the workflow fits together

The usual path is:

```text
to-spec -> to-tickets -> ticket-autopilot
                         |
                         +-> execute-ticket
                              +-> code-simplification
                              +-> code-review
                              +-> qa-test-plan
                              +-> verification-audit
                         +-> explain-pr -> provider readback -> guarded merge
```

- [`to-spec`](to-spec/SKILL.md) captures the decision, behavior, and
  constraints.
- [`to-tickets`](to-tickets/SKILL.md) splits the spec into executable tracer
  bullets and emits each one through the canonical
  [Ticket Envelope v1](ticket-autopilot/references/ticket-envelope-v1.md)
  serializer.
- [`ticket-autopilot`](ticket-autopilot/SKILL.md) snapshots the ticket set,
  schedules its dependency graph, owns the isolated worktree and delivery
  lifecycle, and records durable run state.
- [`execute-ticket`](execute-ticket/SKILL.md) implements one normalized ticket
  and composes simplification, independent review, causal QA planning/execution,
  and [`verification-audit`](verification-audit/SKILL.md). It does not commit,
  push, open a PR, or merge.
- [`explain-pr`](explain-pr/SKILL.md) renders the PR body from the already
  validated bundle. The runner validates it before publication and again after
  reading the actual body and head back from the provider.

The runner creates one branch and PR per ticket. `pr-open` and `integrated` are
distinct states, and no leaf worker can claim either one.

## Requirements and command surface

Use Python 3, Git, and the CLI for the selected provider. Live provider work
also requires real credentials and repository permissions; the runner never
invents them.

Resolve the installed skill directory once, then inspect the authoritative help:

```bash
export TICKET_AUTOPILOT_ROOT="/absolute/path/to/agent-skills/ticket-autopilot"
python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" --help
python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" run --help
```

The public commands include `bootstrap-private-github`, `plan`, `run`, `resume`, `status`, `context-budget`,
`grant-autonomous-merge`, `approve`, `abort`, `cleanup`, `compact-run-ledger`,
`ticket-parse`, `ticket-emit`, and `migrate`. Commands emit structured JSON. Use `<command> --help` as the syntax
authority. `compact-run-ledger <run-id>` is the explicit, atomic path for shrinking a
validated historical ledger; ordinary status and resume operations never rewrite it.

Measure the repository-controlled fixed context in normalized UTF-8 bytes without a
provider or network call:

```bash
python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  context-budget . --install-root "$HOME/.agents/skills" --json
```

The versioned field contract and canonical listing representation are documented in
[Context budget report v1](ticket-autopilot/references/context-budget-v1.md).
Operator practices for context reset, bounded delegation, cache-friendly prefixes, and
unchanged verification duties are in the
[Autopilot context-cost guide v1](docs/autopilot-context-cost-guide.md).

### Run dependencies

Beyond Python 3, Git, and the provider CLI, a run loads a fixed set of skills and
references. The scheduler composes only the first two entries; the leaf workers
are composed inside [`execute-ticket`](execute-ticket/SKILL.md) and never by the
folder scheduler.

| Composed by | Skill | Role in the run |
| --- | --- | --- |
| scheduler | [`execute-ticket`](execute-ticket/SKILL.md) | One implementation attempt and the ticket-local quality loop |
| scheduler | [`explain-pr`](explain-pr/SKILL.md) | Deterministic PR-body rendering during finalization |
| `execute-ticket` | [`code-simplification`](code-simplification/SKILL.md) | Clarity pass over the candidate diff |
| `execute-ticket` | [`code-review`](code-review/SKILL.md) | Review findings against the candidate |
| `execute-ticket` | [`qa-test-plan`](qa-test-plan/SKILL.md) | Causal QA planning and execution |
| `execute-ticket` | [`verification-audit`](verification-audit/SKILL.md) | Validated Verification Record and claim ceiling |

These references are loaded with them:

- [Context budget report v1](ticket-autopilot/references/context-budget-v1.md) —
  fixed-prefix measurement, leaf-bound composition, and the versioned ceiling check.
- [Ticket Envelope v1](ticket-autopilot/references/ticket-envelope-v1.md) — the
  canonical front matter contract.
- [PR-body handoff v1](ticket-autopilot/references/delivery-pr-body-v1.md) — the
  delivery body shape.
- [Merge critical path v1](ticket-autopilot/references/merge-critical-path-v1.md)
  — the resumable approval-to-merge path.
- [Verification Record](verification-audit/references/verification-record.md) —
  artifact and claim rules.

`ticket-autopilot/tests/test_readme_dependencies.py` fails when this list drifts
from the composition the skills actually declare, so the section cannot rot
silently.

## Minimal tracked-ticket run

Every executable ticket starts with a strict Ticket Envelope. Do not hand-write
the final front matter. Save this producer input as `/tmp/ticket-envelope.json`:

```json
{
  "ticket_schema": 1,
  "ticket_id": "01",
  "execution_mode": "AFK",
  "blocked_by": []
}
```

Save the ticket body as `/tmp/ticket-body.md`, beginning with a title and
including its acceptance criteria, plan, tests, and exclusions. Emit and parse
the canonical ticket:

```bash
mkdir -p docs/tickets/my-change
python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  ticket-emit /tmp/ticket-envelope.json /tmp/ticket-body.md \
  --output docs/tickets/my-change/01-implement-change.md
python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  ticket-parse docs/tickets/my-change/01-implement-change.md
```

Tracked tickets must be clean and present at the selected base. Commit the
ticket folder, then preview the source classification, provider capabilities,
dependency order, merge policy, and gates without creating a run:

```bash
git add docs/tickets/my-change
git commit -m "plan my change"
python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  plan docs/tickets/my-change --repo . --provider github --base HEAD
```

Start a manual-by-default live run with explicit resource limits:

```bash
python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  run docs/tickets/my-change --repo . --provider github --provider-mode live \
  --run-id my-change \
  --max-quality-failures 3 --max-leaf-interactions 20
```

Inspecting status is read-only. `resume` continues from durable state after a
gate clears or an interrupted process restarts:

```bash
python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  status my-change --repo .
python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  resume my-change --repo .
```

In manual mode, copy the exact PR head reported by `status`. Approval performs a
fresh live readback, records authorization for that ticket and head only,
invokes the provider's atomic expected-head merge, reads the result back, and
records `integrated` in the same resumable critical path:

```bash
HEAD_SHA="<exact head_sha reported by status>"
python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  approve my-change --repo . \
  --actor "alice@example.com" \
  --evidence "artifact://change-123/merge-approval" \
  --ticket "01" --head-sha "$HEAD_SHA"
```

There is no separate public `integrate` command. If the exact recorded PR head
was already merged outside the runner, reconcile that observation without
issuing another merge:

```bash
python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  approve my-change --repo . \
  --actor "alice@example.com" \
  --evidence "artifact://change-123/external-merge" \
  --ticket "01" --head-sha "$HEAD_SHA" --external-merge
```

Abort records who stopped the run and why. Cleanup removes only the safe
isolated worktree and preserves the ledger; it never deletes remote branches or
PRs. Aborted or failed runs require `--confirm`, waiting runs require `--force`,
and running runs cannot be cleaned:

```bash
python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  abort my-change --repo . --actor "alice@example.com" --reason "requirements changed"
python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  cleanup my-change --repo . --confirm
```

After a normally completed run, use the same `cleanup` command without
`--confirm`.

## Git-ignored ticket sources

`plan` and `run` also accept a fully Git-ignored ticket folder inside the
repository. The folder must be wholly ignored: a mixed tracked/ignored set, an
untracked non-ignored file, an external path, or a symlink escape fails before
worktree creation.

For example, commit the ignore rule, create the canonical ticket with
`ticket-emit`, confirm Git's ignore decision, and use the same lifecycle:

```bash
printf '\ndocs/private-tickets/\n' >> .gitignore
git add .gitignore
git commit -m "ignore private ticket plans"
mkdir -p docs/private-tickets/my-change
python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  ticket-emit /tmp/ticket-envelope.json /tmp/ticket-body.md \
  --output docs/private-tickets/my-change/01-implement-change.md
git check-ignore -v docs/private-tickets/my-change/01-implement-change.md
python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  plan docs/private-tickets/my-change --repo . --provider github --base HEAD
python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  run docs/private-tickets/my-change --repo . --provider github \
  --provider-mode live \
  --run-id private-my-change
```

Before creating the isolated worktree, the runner stores an immutable,
normalized snapshot under the run's managed Git-common state. Resume reads that
snapshot, not mutable planning files. On completion, ignored mode moves the
exact digest-matched source to its ignored `done/` path and writes the
completion summary beside it; neither file is staged for the implementation PR.
If the source changes, disappears, escapes its folder, or conflicts with the
destination, finalization opens a source-drift gate instead of overwriting data.

## Private GitHub repository bootstrap

A new local repository can establish its private GitHub target and first base branch without
an operator-side `gh` or `git push` prerequisite. Supply one exact bootstrap authority before
starting a folder run:

```bash
BASE_SHA=$(git rev-parse refs/heads/main)
python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  bootstrap-private-github --repo "$PWD" --target owner/repository \
  --visibility private --base main --base-sha "$BASE_SHA" \
  --actor "alice@example.com" --evidence "artifact://change-123/bootstrap"
```

`--repo` must be an absolute repository-root path. Before any create, remote edit, push, or
default-branch update, the command stores one immutable actor/evidence-, target-, branch-, and
SHA-bound intent under Git common state and holds its lock. It creates or adopts only the exact
private repository, accepts only an absent or equivalent `origin`, pushes a non-force exact-SHA
refspec only when the remote base is absent, and verifies live repository, visibility, branch,
SHA, URL, and default-branch readback. Exact replay is byte-stable and performs no second create
or push; crash recovery re-observes each boundary. Any contradiction fails without delete,
visibility change, remote rewrite, force, or overwrite.

This authority is a one-repository prerequisite transaction. It grants no delivery, PR, merge,
wiki-sync, cleanup, or future bootstrap authority. Public/internal creation, transfer, rename,
delete, visibility changes, and divergent-base adoption remain unsupported.

## Manual and autonomous merge policy

`manual` is the default. A ticket's `execution_mode: AFK` means it can proceed
without interactive implementation decisions; it is **not merge consent**.
Credentials, write access, silence, or an absent response are not consent
either.

Autonomous merge is opt-in for a whole run and requires an actor plus durable
evidence. It can be selected at creation time:

```bash
python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  run docs/tickets/my-change --repo . --provider github --provider-mode live \
  --run-id autonomous-my-change --merge-policy autonomous \
  --merge-actor "alice@example.com" \
  --merge-evidence "artifact://change-123/autonomous-run-grant"
```

A non-terminal run created with the manual default can receive that authority
later without rewriting its ledger or approving every PR separately:

```bash
python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  grant-autonomous-merge my-change --repo . \
  --actor "alice@example.com" \
  --evidence "artifact://change-123/autonomous-run-grant"
```

The command appends one immutable grant under the run lock and immediately
continues an eligible open PR through the normal autonomous path. Exact replay
with the same actor and evidence is idempotent. Terminal runs, conflicting
authority, and unresolved provider merge mutations fail without replacing the
grant or contacting the provider.

The immutable grant is bound to the repository, run, ticket-set snapshot,
provider, and policy version. It replaces only the per-PR prompt. Before every
merge attempt the runner still verifies the frozen semantic candidate, reads the
current PR/head and provider policy live, checks required checks and approvals,
and uses only an operation atomically pinned to that head. Pending, failed,
unknown, simulated, stale-head, unsupported-provider, or unproven merge-queue
results gate instead of weakening the operation.

On a private repository whose GitHub plan does not provide branch rules, the
active-rules API returns a structured 403 saying that GitHub Pro or a public
repository is required. The adapter accepts only that exact status, message, and
rules-endpoint documentation URL as live `feature-unavailable` evidence. It
records an empty active-rule set and direct mode without relaxing either merge
path: autonomous merge still proves the exact head, mergeability, checks,
approvals, and run grant; manual merge still requires exact-head authority and
uses no provider-policy bypass. Every generic/malformed 403, scope error, or
other policy readback failure still gates; a successfully observed merge-queue
rule still forbids direct fallback.

## Stacked pull requests and evidence reuse

Stacking is limited to a single-parent chain. A ticket with several blockers
waits until all of them are integrated instead of creating a multi-parent stack.
When a parent merges or an ordinary parentless PR's recorded base advances, the
runner guards the PR's recorded remote head, derives the old anchor and target
from delivery lineage, rebases it, pushes with force-with-lease, retargets its
PR, publishes a new head-bound body, and reads the provider state back before
considering merge eligibility again. Parentless reconciliation never invents a
dependency solely to enter this path.

Quality evidence is bound to semantic CandidateRef v2: base tree OID, candidate
tree OID, normalized ticket digest, and contract version. Commit, branch, PR,
base, and head lineage are tracked separately. If reconciliation changes only
lineage while all four semantic fields remain exactly equal, prior review, QA,
verification, cache identity, and claim ceiling are preserved; provider checks
are still rerun for the new head, and a one-shot manual approval is cleared. A
changed base tree, candidate tree, ticket digest, or contract version forces the
complete quality loop again. Remote divergence, a rebase conflict, unresolvable
trees, or contradictory retarget/readback evidence always gates.

See the implemented decisions for
[autonomous stacked delivery](docs/specs/ticket-autopilot-autonomous-stacked-delivery.md),
[ignored ticket sources](docs/specs/ticket-autopilot-ignored-ticket-sources.md),
and the
[merge critical path](ticket-autopilot/references/merge-critical-path-v1.md).

## Recovery and safety boundaries

For most interruptions, run `status`, then `resume` as shown above. Durable
intent/applied/readback receipts make provider and finalization effects
replay-safe.

Use the reported gate and evidence, not guesswork:

- **Provider capability unavailable:** configure a supported provider/operation
  or leave the gate open. Never replace a missing atomic expected-head
  capability with a raw or unguarded merge.
- **Checks pending or failed:** wait for the provider state to change or fix the
  candidate, then resume. Pending, failed, unknown, and simulated results are
  not passes.
- **Stale PR head:** the old manual authorization is invalid. Reconcile the new
  head and, after any required semantic revalidation, approve that exact
  reported head again.
- **Already merged externally:** use the exact-head `approve --external-merge`
  form above. It only observes and reconciles; it never invokes a provider
  merge.
- **Remote divergence or rebase conflict:** resolve the recorded Git
  lineage/conflict explicitly, then resume. The runner never force-overwrites an
  unexpected remote head and never preserves evidence when semantic identity
  cannot be derived exactly.
- **Ticket-source drift:** restore the exact snapshot-matching source or
  destination state; do not overwrite the contradictory ignored file. Resume
  rechecks the durable effect.
- **Active ledger or CandidateRef version error:** do not hand-edit or silently
  reinterpret persisted state. The current `migrate` command is for legacy
  ticket Markdown, not active ledgers; preserve the old ledger and start a new
  run unless a separately validated ledger migration is provided.
- **Crash or lost provider response:** run `status`, then `resume`. The runner
  reads durable state and the provider before deciding whether any mutation
  remains; it does not assume success or blindly issue a second merge.

Never invent credentials, approvals, provider responses, or verification
evidence. Never use `--admin`, bypass branch policy, call an unguarded provider
merge on the runner's behalf, or describe simulated/local evidence as live.
Claims must stay at or below the ceiling in the canonical
[Verification Record](verification-audit/references/verification-record.md);
unobserved provider and environment boundaries remain explicit gates.

## Attribution

A substantial portion of this repository is copied from, adapted from, or
inspired by [Matt Pocock's `skills`
repository](https://github.com/mattpocock/skills).

The derived skills are not limited to a fixed list here. Some retain their
upstream names, while others have been renamed, reorganized, or substantially
adapted for this repository's top-level skill layout, local Markdown
specs/tickets, and agent-agnostic execution style. They should not be treated as
exact copies of the upstream versions.

Credit for the original ideas and upstream versions belongs to Matt Pocock and
contributors to `mattpocock/skills`.

The `code-simplification` skill is adapted from Addy Osmani's
[`code-simplification`](https://github.com/addyosmani/agent-skills/blob/main/skills/code-simplification/SKILL.md),
which in turn credits Anthropic's Code Simplifier agent. The adaptation keeps
the behavior-preservation principles while scoping the workflow to the current
ticket diff so it can compose cleanly with `ticket-autopilot`.
