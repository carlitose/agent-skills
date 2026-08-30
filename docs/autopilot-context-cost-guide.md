# Autopilot context-cost guide v1

This guide describes operator practices for reducing the context carried through a
`ticket-autopilot` run. It does not estimate model tokens, prices, cache-hit rates, or live
session savings. Those outcomes are unmeasured until the `TK-09` live observation.

## Reproducible baseline

`TK-02` established the repository-controlled static-prefix measurement in
`normalized-utf8-bytes`; `TIP-01` refreshed it after adding terminal integration proof
and external-readback guidance, while `ICP-02` and `PCR-01` refreshed completion-projection
reauthorization and post-commit recovery.
The repository-level fixture installs the same controlled skill inventory on every run, so
documentation can quote these values without depending on an operator's changing personal
installation:

| Surface | Controlled result | Scope |
| --- | ---: | --- |
| Always-on listing | `4,999` normalized UTF-8 bytes | `22` installed model-visible skills |
| Ticket-autopilot static closure | `60,255` normalized UTF-8 bytes | `11` workflow files |
| Combined static prefix | `65,254` normalized UTF-8 bytes | Arithmetic sum of the two measured surfaces |
| Worst-case composed total | `172,910` normalized UTF-8 bytes | Static prefix plus the `107,656`-byte code-review volatile-input bound |

Reproduce the report from a controlled installation with the repository test:

```bash
python3 -B -m unittest \
  ticket-autopilot.tests.test_context_budget.ContextBudgetTests.test_repository_baseline_reproduces_the_autopilot_inventory
```

For an operator's current installed inventory, run:

```bash
python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  context-budget . --install-root "$HOME/.agents/skills" --json
```

That second report is environment-specific and may differ from the TK-02 fixture. Treat
its values as a new local measurement, not as a replacement for the versioned baseline.

## Reset context at a safe boundary

Operator behavior:

- Consider a fresh session only at a ticket or other durable checkpoint, never while a
  mutation or delivery critical path is active.
- Reconstruct from Git, the Ticket Envelope, run status, CandidateRef-bound artifacts, and
  evidence pointers instead of pasting the preceding transcript into the new session.
- Keep the old session until the new one has recovered the authoritative state.

Why it can help: continuing a session retains accumulated chat and volatile tool output,
while a fresh session starts without that history. A reset also reloads the static prefix,
so it is not automatically cheaper. The break-even point and actual reduction are
unmeasured; `TK-09` is required before making a live per-run claim.

Contract behavior: the runner persists ticket state and content-addressed evidence, but it
does not create or replace conversations. Automatic cross-host rollover is a separate
policy and host-capability problem.

## Keep delegated context small

Operator behavior:

- Inline serial composition is the portable default. Delegate only when the user or an
  applicable host instruction grants explicit authority.
- When delegation is authorized, send the normalized ticket facts, exact CandidateRef,
  bounded file scope, acceptance criteria, and artifact references needed for that leaf.
  Prefer paths and digests over pasted evidence bodies.
- Do not label inline shared-context work as independent. A distinct worker must actually
  provide the isolation being claimed.

Why it can help: a distinct worker can avoid inheriting unrelated conversation history,
but it also loads its own required static instructions and task context. The net context
effect is unmeasured and still requires `TK-09` evidence.

Contract behavior: `execute-ticket` keeps delegation opt-in and records execution mode,
isolation, parallelism, and the authority reference. Leaf intake bounds constrain volume;
they do not relax scope, evidence, or verification duties.

## Preserve cache-friendly prefixes

Operator behavior:

- Keep stable skills and shared references stable. Avoid rewriting the static prefix for a
  small ticket-local edit when the contract itself has not changed.
- Put volatile diffs, logs, and reports behind narrow paths or content-addressed artifacts,
  and load only the portions required by the active stage.
- Inject large volatile material as late as practical and do not resend it after a durable
  pointer is available.

Why it can help: an unchanged prefix is the portion a provider may reuse, whereas changed
early content invalidates that opportunity. Local repository checks do not observe provider
cache behavior, so any cache reuse, hit rate, or resulting saving remains unmeasured.

Contract behavior: `context-budget` measures the repository-controlled static surfaces and
the leaf contracts bound volatile intake. It neither detects provider cache hits nor turns
cache expectations into a scheduler, delivery, or merge gate.

## Verification is not a reduction lever

Never save context by skipping review or QA, cropping evidence needed for causal coverage,
weakening an invariant, changing an evidence class, or raising a claim beyond the validated
bundle. If the required work does not fit comfortably, stop at a durable bounded handoff or
reset at a safe boundary, then resume the same verification contract.

The local evidence supports repository-controlled byte measurements and declared bounds.
Live per-run totals, actual model-token reduction, monetary impact, and provider cache
behavior remain unmeasured until `TK-09` records them with explicit limitations.
