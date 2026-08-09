---
name: triangulate-diagnosis
description: Diagnose a hard bug from three independent angles at once, then record the consensus as a diagnostic or decision spec and create follow-up tickets when needed. Use when a bug is high-stakes, has resisted a single diagnosis pass, or when the user wants to triangulate or cross-check before committing to a fix.
---

# Triangulate Diagnosis

Run three independent diagnoses of the same bug in parallel, keep only what they agree
on, and turn the consensus into a diagnostic or decision spec. One diagnosis can anchor
on the first plausible cause; three blind diagnoses that land on the same root cause are
more trustworthy. Where they disagree, you learn the bug is underspecified or
multi-causal.

This skill orchestrates other small skills:

- [`diagnose`](../diagnose/SKILL.md): the disciplined reproduce, hypothesize, and locate
  loop each subagent runs.
- [`to-spec`](../to-spec/SKILL.md): records the converged diagnosis or decision as a spec.
- [`to-tickets`](../to-tickets/SKILL.md): creates follow-up tickets when executable work is
  needed.
- [`wayfinder`](../wayfinder/SKILL.md): maps a bug area that is still too broad or foggy
  for one diagnostic pass.

## Phase 0: Write the shared brief

Before fanning out, distill one bug brief that every subagent receives verbatim. This is
the only shared context. Keep it factual, not interpretive, so the three diagnoses stay
independent. Do not include your own hypothesis or suspected cause.

The brief must contain:

- The exact symptom the user described, including error text, wrong output, timing, or
  screenshots.
- How to reach the code: repo paths, service, entry point, and relevant commands.
- Known repro steps, fixtures, or environment notes already in the conversation.
- Hard constraints: what must keep working and what is out of scope.
- The required output contract from [REFERENCE.md](REFERENCE.md).

Apply the canonical [`diagnose` secret-redaction boundary](../diagnose/references/secret-redaction.md)
to evidence before it enters the shared brief, a delegated pass, or a durable report.

If a fact that would change the brief is missing and only the user has it, ask one
concise blocking question before fanning out. Otherwise proceed.

## Phase 1: Fan out three independent diagnoses

Spawn three subagents in parallel. Each one:

- Runs the `diagnose` skill against the shared brief.
- Works in isolation. Do not give a subagent your hunch, and do not let subagents see each
  other's results.
- Returns the structured Diagnosis Report defined in [REFERENCE.md](REFERENCE.md):
  root cause, evidence, feedback loop, fix location, confidence, and alternatives ruled
  out.

To force useful divergence, give each subagent a distinct lens in addition to the shared
brief:

1. **Repro-first**: prioritize building the feedback loop and bisecting to the change that
   introduced the bug.
2. **Data-flow**: trace inputs through modules end to end; suspect boundaries, types, and
   joins.
3. **Recent-change / environment**: suspect recent commits, config, dependencies,
   infrastructure, and timing.

The lens shapes where they look first, not what conclusion to reach. Each must follow the
evidence wherever it leads.

If a subagent reports it could not build a feedback loop, treat its report as
low-confidence and say so in Phase 2.

## Phase 2: Converge

Collect the three reports and compare them. Produce a short convergence summary:

- **Consensus root cause**: the cause at least two subagents independently identified,
  stated once. Reconcile wording and cite the strongest evidence from each agreeing
  report.
- **Divergences**: where they disagree and why.
- **Unique insights**: a real finding only one subagent surfaced, such as a ruled-out
  alternative, adjacent bug, or missing test boundary.
- **Confidence**: high if all three converge with a shared feedback loop; medium if two
  of three agree; low or blocked if they split three ways or none built a loop.

Decision gate:

- **All three or two of three converge**: proceed to Phase 3 with the consensus root
  cause.
- **Three-way split, or the split depends on information only the user has**: stop. Report
  the candidate causes with evidence and ask which to pursue, or optionally spawn one
  tiebreaker subagent scoped to the disputed question.

Show the convergence summary to the user before writing anything unless the user
explicitly asked for fully autonomous execution.

## Phase 3: Record the consensus as a spec

Invoke `to-spec`, passing the convergence summary as already-gathered context:

- The consensus root cause becomes the core of a diagnostic spec.
- The agreed fix location or approach seeds `Decision / Solution`.
- Ruled-out alternatives become `Options Considered`.
- Unique insights go into `Evidence`, `Testing Decisions`, or `Open Questions`.
- If confidence is medium or low, set status to `Proposed` and list unresolved divergences
  as open questions.

Save or update the spec under `docs/specs/<slug>.md`.

## Phase 4: Create follow-up tickets when needed

If the consensus implies executable work, invoke `to-tickets` using the diagnostic or
decision spec as the parent. The resulting tickets should go under:

`docs/tickets/<spec-slug>/<NN>-<ticket-slug>.md`

Each ticket should include what to build, acceptance criteria, explicit blockers, frontier
state, and verification expectations.

If the user asked only for diagnosis and documentation, leave follow-up work as a section
inside the spec and do not create ticket files.

## Final Response

Keep the final response short:

- Consensus cause in one line.
- Confidence.
- Spec path.
- Ticket folder or ticket paths, if created.
- Any open question or human gate.

## Notes on Portability

"Spawn three subagents in parallel" maps to whatever delegation primitive the host agent
provides. If the host cannot run subagents concurrently, run the three diagnoses
sequentially with cleared context between each. If the host cannot isolate context at all,
say so rather than running three anchored passes.
