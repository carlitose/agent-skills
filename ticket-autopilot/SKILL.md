---
name: "ticket-autopilot"
description: "Drive a ticket folder AFK through implementation, independent review, classified QA, verification audit, PRs, and claim gates."
---

# Ticket Autopilot

Drive a folder of local Markdown tickets through the dependency graph. For each ready
ticket run:

`implement -> simplify -> independent review -> fix -> QA plan -> execute available QA -> verification audit -> claim firewall -> PR -> explain and verify PR`

Continue until all executable work is complete or only explicit human or environment gates
remain.

Delegate expensive independent steps when the host permits it. Keep the main thread as
orchestrator and serialize work with overlapping file footprints.

## AFK contract

- Do not wait for the user during the run.
- Never fabricate approvals, credentials, environment access, live observations, or human
  decisions.
- Fail forward: one blocked ticket does not abort unrelated ready tickets.
- Track ready, active, done, failed, and human-gated states visibly.
- Separate implementation completion from behavior verification and release readiness.

## Defaults

- `GIT_STRATEGY=branch-pr`: create a branch, commit, push, and open a PR per completed
  ticket; never auto-merge.
- `MAX_QUALITY_ITERATIONS=3`.
- `REVIEW_BLOCKING_LEVEL=blocker`, matching `code-review` output
  (`blocker | should-fix | nit`).
- `CODE_SIMPLIFICATION_SKILL=code-simplification`.
- `PR_EXPLANATION_SKILL=explain-pr`.

Honor explicit user overrides.

## Deterministic runner

Use the versioned runner for graph, state, resume, gate, and cleanup mechanics. It emits
one schema-versioned JSON object on stdout and uses only the Python standard library:

```text
python3 -B ticket-autopilot/scripts/ticket-autopilot.py plan <folder> --repo <repo> --provider github
python3 -B ticket-autopilot/scripts/ticket-autopilot.py run <folder> --repo <repo> --provider azure-devops
python3 -B ticket-autopilot/scripts/ticket-autopilot.py status <run-id> --repo <repo>
python3 -B ticket-autopilot/scripts/ticket-autopilot.py resume <run-id> --repo <repo> --events <events.json>
python3 -B ticket-autopilot/scripts/ticket-autopilot.py approve <run-id> <gate-id> --repo <repo> --actor <actor> --evidence <artifact>
python3 -B ticket-autopilot/scripts/ticket-autopilot.py abort <run-id> --repo <repo> --actor <actor> --reason <reason>
python3 -B ticket-autopilot/scripts/ticket-autopilot.py cleanup <run-id> --repo <repo>
python3 -B ticket-autopilot/scripts/ticket-autopilot.py migrate <folder> --write
```

`run` validates the ticket contract, DAG, provider capabilities, and run identity before
creating a detached isolated worktree. The locked ledger and retained artifacts live under
the Git common directory. Provider adapters build normalized GitHub or Azure DevOps
commands; the runner does not contact or merge through a provider without a later explicit
worker action and current-head human authorization.

The versioned event document drives `activate`, fixed-tree `stage`, idempotent `delivery`,
provider-observed `integrate`, and stacked-PR `reconcile` operations. Each accepted event is
persisted before the next one runs. GitHub exposes exact-head merge capability; Azure
DevOps does not document an atomic expected-head completion precondition, so that
capability fails closed and requires an external human-controlled merge observation.

## Phase 0: Build the work graph

1. Resolve the ticket folder once.
2. List pending `*.md` files, excluding `done/`.
3. Parse `## Blocked By` and build the dependency DAG.
4. Treat `done/` as implementation-ticket completion, not automatic release readiness.
5. Detect approval, credential, environment, design, go/no-go, and human-observation gates.
6. Create tasks and log ready, dependency-blocked, and human-gated sets.

Stop if no pending ticket exists.

## Phase 1: Per-ticket quality loop

### A. Implement

Invoke `execute-ticket` for only the chosen ticket. Require:

- files changed;
- acceptance-criteria state;
- External Boundary Delta;
- Invariant Register;
- commands and classified evidence;
- Verification Record and Claim Ceiling;
- blockers and HITL gates.

A hard implementation blocker ends this ticket's loop. A verification-only gate leaves the
implementation available but constrains status and language.

### B. Simplify

Invoke `code-simplification` only on the ticket diff. Preserve behavior, public contracts,
errors, side effects, ordering, concurrency, performance constraints, tests, and the
Invariant Register.

Retain simplification only when evidence supports preservation. A blocked optional
simplification must not corrupt or hide a valid implementation.

### C. Run an independent review

The first reviewer receives only:

- raw ticket or spec;
- fixed diff;
- known-good baseline and relevant documentation;
- repository standards.

Do not provide the implementer's PR body, completion narrative, proposed claim, or prior
review conclusions until the reviewer freezes initial findings.

Require `code-review` output for standards, spec compliance, and verification semantics,
including semantic invariant changes, causal gaps, injection points, and overclaims.
Require a complete External Boundary Delta for every changed SDK/API/browser/provider/CLI/
infrastructure/public contract. Any `regression` or high-impact `unknown` row is a blocker.
Reject broad intent as authorization for a specific boundary-field change; require an exact
requirement, decision, or current contract for that item.

If a second strict maintainability reviewer is available, run it independently and merge
and deduplicate structured findings.

### D. Fix review findings

Fix blocking findings within ticket scope. Re-run affected checks and update the Invariant
Register and evidence. Repeat simplification only when fixes created meaningful complexity.

### E. Generate the QA plan

Invoke `qa-test-plan` against the fixed current diff. Require:

- External Boundary Delta with each changed item mapped to a QA step or gate;
- causal chains and external or human-controlled boundaries;
- step action and expected observable result;
- environment and planned evidence class;
- injection point and observed segment;
- artifact to retain and limitation;
- explicit HITL or environment gates.

Plan creation is not evidence.

### F. Execute available QA

Execute each feasible step against the real application or named environment when
available. Otherwise simulate only when useful and label it `simulated`.

For each step return:

```text
{step, result: pass|fail|inconclusive|skipped,
 evidence_class, environment, injection_point,
 observed_segment, artifact, limitations}
```

Never convert an unavailable live step into a simulated pass for the live criterion. Never
guess a pass.

### G. Run verification audit

Invoke `verification-audit` with:

- raw ticket/spec and acceptance criteria;
- fixed diff, baseline, External Boundary Delta, and Invariant Register;
- review findings;
- all classified test and QA evidence;
- injection points and causal coverage;
- open dependencies and HITL gates;
- proposed ticket, PR, and release wording.

Require a Verification Record, forbidden claims, blocking gaps, next evidence, and Claim
Ceiling.

If the audit reveals an implementation defect or unauthorized semantic regression, fix and
return to independent review. If it reveals only missing human or environment evidence,
record the gate and stop iterating on code.

If a changed external boundary lacks a complete delta, treat the audit as unsupported and
return to review. Do not allow tests, QA simulation, or a later live observation to bypass
this structural blocker.

### H. Apply the release-claim firewall

All downstream status, ticket notes, commits, PR bodies, and final reports must stay at or
below the Claim Ceiling.

With any open critical HITL, live-environment, approval, or credential gate, allowed release
language is limited to precise scoped statements such as:

- "Implementation completed."
- "Declared local checks passed."
- "Deployable to <environment> for verification."
- "Release blocked pending <specific gate>."

Do not use `verified`, `working in production`, `production-ready`, `release-ready`,
or equivalent language.

A ticket may enter `done/` only when its own acceptance criteria are met. If a separate
downstream gate remains open, record the ticket as implementation-complete while the
release graph remains `release-blocked`. If the ticket itself requires that gate, leave it
pending as `blocked-needs-human`.

### I. Finalize and open PR

After the quality loop is stable:

- apply `GIT_STRATEGY`;
- never auto-merge;
- capture an evidence bundle containing the raw ticket, diff summary, invariant changes,
  simplification result, independent review, commands, classified test and QA evidence,
  Verification Record, Claim Ceiling, open gates, and known risks.

Opening a PR does not raise the Claim Ceiling.

### J. Explain and verify the PR

Invoke `explain-pr` with the evidence bundle. Require the real GitHub body to explain the
change, rationale, before/after behavior, code flow, verification scope, risks, and reviewer
checks, with exactly one evidence-based GitHub-compatible Mermaid diagram.

Read the PR back and verify:

1. required sections exist;
2. exactly one Mermaid block exists;
3. every verification and readiness statement respects the Claim Ceiling;
4. skipped, simulated, and live evidence are distinguished;
5. open critical gates are visible;
6. PR and branch match the ticket.

Retry mutation or readback once. If still invalid, mark `blocked-needs-human`, preserve the
generated body in the structured result, and continue with other tickets.

## Phase 2: Outer-loop decisions

After each ticket:

- recompute the DAG;
- continue with unrelated ready work;
- stop only when no ready executable ticket remains;
- calculate the release-level Claim Ceiling as the lowest ceiling among release-critical
  tickets and gates.

Do not interpret all tickets in `done/` as production readiness.

## Final report

Report:

- tickets implementation-complete and PR links;
- simplification outcome;
- independent review result;
- evidence classes and causal segments actually observed;
- per-ticket and release-level Claim Ceilings;
- tickets and releases blocked by exact HITL or environment gates;
- remaining ready and dependency-blocked work;
- autonomous decisions requiring later review.

Use exact wording from the verification audit. Do not paste large diffs or full PR bodies.
