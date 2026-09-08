# Agent Skills

This repository contains composable skills for planning, executing, reviewing,
and improving code workflows. Its main end-to-end runner is `ticket-autopilot`:
it turns a folder of dependency-aware tickets into isolated, independently
reviewed changes and provider-neutral pull requests, while keeping merge
authority and evidence explicit.

## Pi package

The repository is also a Pi package. Its extension routes every natural-language
request through `ask-skills` and requires shippable development work to follow
`to-spec -> to-tickets -> ticket-autopilot`. Only explicit hold, cancel, or reopen
requests use the named [`change-status-ticket`](change-status-ticket/SKILL.md)
lifecycle-only lane. Slash commands and user `!` shell commands remain direct
operational controls. Neither mandatory lane grants merge authority;
`ticket-autopilot` keeps its manual merge default.

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

Use `/agent-skills-flow` inside Pi to check that the extension and its five
required workflow skills are available. Run the package tests with `npm test`.

### One-shot operational recovery

`/break-glass` is a default-off recovery surface for a deadlock in the local
workflow control plane. It is not a delivery or control-bypass mode.

```text
/break-glass
Fix the stuck local run state, verify status, and resume the run
```

The bare command arms immediately; there is no wizard, metadata form, magic
phrase, or per-tool confirmation. The next eligible ordinary-language prompt is
the complete scope of one recovery turn in the same durable session file and
working directory. The grant expires after 15 minutes. Slash commands, `!`
input, blank input, queued steering/follow-up input, and extension messages do
not consume or inherit it. Use `/break-glass status` to inspect an arm or
`/break-glass cancel` to discard it.

During the recovery turn, Pi exposes only unique canonical built-in `read`,
`bash`, `edit`, and `write`. These may directly inspect or repair local files
needed by the prompt, including tracked files and `.git/ticket-autopilot` state.
The turn must read back the result and use the applicable Ticket Autopilot
`status` or `resume` command before claiming local recovery. Candidate drift then
returns to the normal invalidation, review, QA, and verification flow. The prior
tool list is restored exactly, or Pi reports a restoration gate without claiming
success. The grant is consumed even when the turn fails or is aborted.

Break-glass grants no provider, PR, push, merge, remote-history,
terminal-integration, wiki-publication, cleanup, Pi-synchronization, secret
access, or `/reload` authority. Installing or synchronizing this feature does
not arm it, and an existing Pi session requires a separate user-controlled
`/reload` before the command becomes available.

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

- [`change-status-ticket`](change-status-ticket/SKILL.md) handles only an explicit
  administrative `open`, `on-hold`, or `canceled` decision through the
  repository transaction; it does not invoke implementation quality stages.
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

## Local checks (quick/full)

`npm test` now runs combined Node **and Python** checks, not an extension-only signal.
Use Node >=22.6 (the existing native TypeScript stripping command), Python >=3.12
(the supported filesystem-test baseline, including Windows junction checks), and Git
on PATH. No provider credentials, new test framework, hosted CI or global installation
is performed by this entry point.

```bash
npm test
npm run test:full
node scripts/test-local.mjs full --list
node scripts/test-local.mjs quick --python "/path with spaces/python"
node scripts/test-local.mjs full --timeout-seconds 60 --report "/path/local-checks.json"
```

Quick runs the Node extension/orchestrator tests plus Python ticket-contract, leaf-protocol,
history-codec, project-binding and verification-contract suites. Full discovers every
`test_*.py` file directly under `ticket-autopilot/tests`, `llm-wiki/tests`,
`to-tickets/tests` and `verification-audit/tests`, plus the accepted Autopilot forward
matrix. Both modes print exact included and omitted check IDs; `--list` inspects the
selection without executing checks. Throwaway `docs/prototypes` experiments and
hosted/live-provider verification are explicitly outside both local profiles.

The default timeout is 300 seconds **per check invocation**, configurable from 1 to 3600;
the stdout/stderr overflow guard is 16 MiB per stream. An unavailable required interpreter,
invalid selector, failed suite, timeout, signal, zero-test summary or incomplete result returns
nonzero. Python is never silently omitted. Automatic discovery tries `python3`, `python`
and, on Windows, `py -3`; `--python` or `PYTHON` selects one literal executable path,
not a shell command. An invalid explicit selection does not fall back to another Python.

Reports distinguish succeeded, failed, errored, all-skipped and not-run **check invocations**.
These are not summed individual test/subtest counts: framework case results, partial skips
and diagnostics remain in each retained stdout/stderr log. Prerequisite failure leaves
selected checks not-run and reports a separate diagnostic/nonzero exit. Quick omissions
are not-run, not successful or skipped tests. Full continues to later checks after a suite
failure. Log/report locations are printed; `--report` chooses the summary location.

Existing test failures remain visible, including fixture dependence on operator Git
configuration. This command does not rewrite that configuration or turn a quick pass into
a whole-repository claim. Timeouts do not prove effect-freedom or descendant-process cleanup;
inspect retained observations before repeating uncertain work. Windows, POSIX and live
provider evidence remain distinct.

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

The public commands include `prepare-zero-to-autopilot`, `zero-to-autopilot`,
`zero-to-autopilot-status`, `bootstrap-private-github`, `sync-local-pi`, `plan`, `run`,
`resume`, `status`, `context-budget`, `grant-autonomous-merge`,
`grant-completion-projection`, `grant-repository-autonomous-merge`,
`revoke-repository-autonomous-merge`, `repository-autonomous-merge-status`,
`grant-repository-autonomous-reconciliation`,
`revoke-repository-autonomous-reconciliation`,
`repository-autonomous-reconciliation-status`, `migrate-repository-authority`, `merge-all`,
`runner-defect-issue-grant`, `runner-defect-issue-revoke`,
`runner-defect-issue-status`, `runner-defect-issue-escalate`,
`prepare-legacy-recovery`, `apply-legacy-recovery`, `legacy-recovery-status`,
`revoke-legacy-retirement`, `wiki-delivery-retry-status`, `retry-wiki-delivery`,
`approve`, `abort`, `cleanup`, `compact-run-ledger`, `status-change-transaction`,
`ticket-parse`, `ticket-emit`, and `migrate`.
Commands emit structured JSON. Use
`<command> --help` as the syntax authority. `compact-run-ledger <run-id>` is the explicit, atomic path for shrinking a
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

### Opt-in runner-defect issue publication

When this branch applies, load [Runner-defect issue publication](ticket-autopilot/references/runner-defect-issues.md). That reference owns the procedure, prerequisites, evidence, replay, and stop conditions.

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

These operational references are conditional, not part of the fixed common manifest.
Load only the branch selected by the request or current stage:

- Bootstrap or import: [bootstrap](ticket-autopilot/references/bootstrap.md).
- Worktree adoption, abort, or cleanup: [worktrees](ticket-autopilot/references/worktrees.md).
- Post-integration installed-Pi refresh: [local Pi sync](ticket-autopilot/references/local-pi-sync.md).
- Merge grants, authority migration, or PR reconciliation: [merge and reconciliation](ticket-autopilot/references/merge-and-reconciliation.md).
- Tracked projection or source-mode recovery: [final-tree projection](ticket-autopilot/references/final-tree-projection.md).
- Post-integration wiki sync or delivery retry: [wiki delivery](ticket-autopilot/references/wiki-delivery.md).
- Separately authorized runner-defect issue publication: [issue publication](ticket-autopilot/references/runner-defect-issues.md).
- Legacy migration, retirement, compaction, or false budget exhaustion: [legacy recovery](ticket-autopilot/references/legacy-recovery.md).

`ticket-autopilot/tests/test_readme_dependencies.py` checks that both common and
conditional dependencies stay discoverable. The owning references retain the procedures;
this list does not grant authority or make every branch an unconditional load.

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
invokes the provider's atomic expected-head merge, and reads the result back.
Before recording `integrated`, it recursively derives the root delivery base,
freshly fetches that terminal branch, and persists a proof that the exact PR
head or explicit provider merge commit is reachable from its observed tip:

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
issuing another merge. This read-only path records `external-readback`
provenance only after the same fresh terminal-reachability proof; it grants no
provider mutation or merge authority.

A canonical `resume` integration event can also recover one narrower stale-head
case: the provider merged a different rebased single-commit head. Before updating
the current PR/delivery lineage, the runner requires both heads to be one commit
on their respective bases and accepts only two exact provider integration shapes:
`two-parent-head-merge`, whose second parent is the observed head, or
`single-parent-integration-copy`, a distinct sibling commit with the same observed
base and tree. The non-empty NUL-delimited
`diff-tree --raw --full-index --no-renames` transitions from the recorded base,
observed base, and provider integration base must be byte-identical. That binds
every changed path, status, mode, old blob, and new blob. The runner persists and
reads back a versioned immutable receipt before ordinary terminal proof. Historical
schema-1 two-parent receipts replay without rewrite; new receipts are schema 2 and
name their topology. Patch ID, commit message, provider method label, final-tree
similarity alone, multi-commit delivery, general squash, queue rewrite, conflict
resolution, or any extra/missing transition fails closed. This is technical
post-merge reconciliation, not merge approval.

For an unchanged exact recorded head, the existing operator form remains:

```bash
python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  approve my-change --repo . \
  --actor "alice@example.com" \
  --evidence "artifact://change-123/external-merge" \
  --ticket "01" --head-sha "$HEAD_SHA" --external-merge
```

### Canonical tracked-wiki delivery and exact local retry

When this branch applies, load [Post-integration wiki delivery and exact retry](ticket-autopilot/references/wiki-delivery.md). That reference owns the procedure, prerequisites, evidence, replay, and stop conditions.

### Worktree ownership and cleanup

When this branch applies, load [Worktree ownership and cleanup](ticket-autopilot/references/worktrees.md). That reference owns the procedure, prerequisites, evidence, replay, and stop conditions.

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

## Exact-inventory zero-to-autopilot bootstrap

When this branch applies, load [Bootstrap a private repository](ticket-autopilot/references/bootstrap.md). That reference owns the procedure, prerequisites, evidence, replay, and stop conditions.

## Tracked final-tree projection

When this branch applies, load [Final-tree projection and exact source recovery](ticket-autopilot/references/final-tree-projection.md). That reference owns the procedure, prerequisites, evidence, replay, and stop conditions.

## Exact tracked completion projection

When this branch applies, load [Final-tree projection and exact source recovery](ticket-autopilot/references/final-tree-projection.md). That reference owns the procedure, prerequisites, evidence, replay, and stop conditions.

## Private GitHub repository bootstrap

When this branch applies, load [Bootstrap a private repository](ticket-autopilot/references/bootstrap.md). That reference owns the procedure, prerequisites, evidence, replay, and stop conditions.

## Exact integrated local Pi synchronization

When this branch applies, load [Exact integrated local Pi synchronization](ticket-autopilot/references/local-pi-sync.md). That reference owns the procedure, prerequisites, evidence, replay, and stop conditions.

## Manual and autonomous merge policy

When this branch applies, load [Merge authority and reconciliation](ticket-autopilot/references/merge-and-reconciliation.md). That reference owns the procedure, prerequisites, evidence, replay, and stop conditions.

### Exact legacy-run recovery

When this branch applies, load [Legacy run recovery and budget repair](ticket-autopilot/references/legacy-recovery.md). That reference owns the procedure, prerequisites, evidence, replay, and stop conditions.

### Repository-wide merge-all

When this branch applies, load [Merge authority and reconciliation](ticket-autopilot/references/merge-and-reconciliation.md). That reference owns the procedure, prerequisites, evidence, replay, and stop conditions.

### Repository-wide autonomous reconciliation

When this branch applies, load [Merge authority and reconciliation](ticket-autopilot/references/merge-and-reconciliation.md). That reference owns the procedure, prerequisites, evidence, replay, and stop conditions.

## Stacked pull requests and evidence reuse

When this branch applies, load [Merge authority and reconciliation](ticket-autopilot/references/merge-and-reconciliation.md). That reference owns the procedure, prerequisites, evidence, replay, and stop conditions.

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
