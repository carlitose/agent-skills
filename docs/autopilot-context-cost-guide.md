# Autopilot context-cost guide v1

This guide describes operator practices for reducing the context carried through a
`ticket-autopilot` run. It does not estimate model tokens, prices, cache-hit rates, or live
session savings. Those outcomes are unmeasured until the `TK-09` live observation.

## Reproducible baseline

`TK-02` established the repository-controlled static-prefix measurement in
`normalized-utf8-bytes`; `EMG-01` refreshed it after adding the existing-run grant command,
`TIP-01` refreshed terminal integration proof and external-readback guidance, `ICP-02` and
`PCR-01` refreshed completion-projection reauthorization and post-commit recovery,
`PIS-01` refreshed exact integrated local Pi synchronization, `PLS-01` refreshed
Pi-normalized package source identity guidance, `PSM-01` refreshed explicit owned-manifest
source migration guidance, `RD-04` refreshed the orthogonal issue-publication lifecycle,
`EHR-01` refreshed exact post-merge equivalent-head reconciliation guidance, `ICR-01`
added the strict single-parent integration-copy receipt topology, `CST-04` added the
visible `change-status-ticket` routing pointer without adding that branch to Ticket
Autopilot's static closure, `FTV-01` refreshed non-authoritative final-tree observation,
`FTV-02` added durable enabled-mode projected-state recovery guidance, `FTV-03`
connected that transaction to one exact-`D` final-quality generation, `MRA-01`
refreshed worktree-stable repository-authority and explicit migration guidance, `WDT-01`
added canonical cross-checkout wiki delivery and exact local retry guidance, `WGC-01`
added manifest-owned provider-free worktree planning, `WGC-02` added exact guarded
application and replay guidance, and `MAR-01` restored affirmative repository-wide
merge-all routing. `SW-05` refreshes the controlled measurements for stage-gate cause
and structured-status guidance. `APM-07` moves infrequent procedures behind explicit
retrieval triggers. The configured `176,903`-byte ceiling remains unchanged; the controlled
preset is now within it. This upper-bound result is not observed live consumption.
The repository-level fixture installs the same controlled skill inventory on every run, so
documentation can quote these values without depending on an operator's changing personal
installation:

| Surface | Controlled result | Scope |
| --- | ---: | --- |
| Always-on listing | `5,260` normalized UTF-8 bytes | `23` installed model-visible skills |
| Ticket-autopilot static closure | `58,561` normalized UTF-8 bytes | `12` workflow files |
| Combined static prefix | `63,821` normalized UTF-8 bytes | Arithmetic sum of the two measured surfaces |
| Worst-case composed total | `171,477` normalized UTF-8 bytes | Static prefix plus the `107,656`-byte code-review volatile-input bound |

### Progressive operational references

APM-07 preserves the same controlled installation, twelve-source manifest, byte unit,
volatile-input bound, and ceiling. Its before/after comparison changes the common skill
text, not those measurement rules. README procedures and eight disclosed operational
references are outside that fixed manifest. Load a reference when its trigger fires;
its bytes are additional, not free or part of the reported fixed-prefix reduction.
In particular, enabled tracked projection requires its reference even during an ordinary
tracked-ticket run. The fixed preset is therefore not a whole-session upper bound once
conditional material is loaded. Bootstrap, cleanup, Pi synchronization, and other
unrelated procedures need not be loaded for ordinary implementation.

The local comparison below measures normalized UTF-8 bytes only. It excludes transcripts,
provider prompts/responses, runtime tool output, installation differences, and actual
branch-selection frequency. It demonstrates neither model-token nor currency savings.

| Surface | Before SW-05-based edit | After APM-07 |
| --- | ---: | ---: |
| Ticket Autopilot SKILL.md | 27,200 | 14,419 |
| Fixed workflow closure | 71,342 | 58,561 |
| Fixed preset plus volatile bound | 184,258 | 171,477 |

Conditional branch sizes (each added only when loaded):

| Reference | Normalized UTF-8 bytes |
| --- | ---: |
| `bootstrap.md` | 5,978 |
| `final-tree-projection.md` | 11,815 |
| `legacy-recovery.md` | 2,015 |
| `local-pi-sync.md` | 3,894 |
| `merge-and-reconciliation.md` | 14,700 |
| `runner-defect-issues.md` | 4,004 |
| `wiki-delivery.md` | 6,520 |
| `worktrees.md` | 4,687 |

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

- Inline serial composition is the portable default. Apply the
  [operating defaults](../ask-skills/OPERATING-DEFAULTS.md): distinct workers require
  explicit authority from a user request; AFK and host capability are not that request.
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
