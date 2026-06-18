---
name: triangulate-diagnosis
description: Diagnose a hard bug from three independent angles at once, then record the consensus. Fans out the `diagnose` skill to 3 isolated subagents, finds where their root-cause analyses converge, and hands the agreed finding to `write-a-adr`. Use when a bug is high-stakes, has resisted a single diagnosis pass, or when the user asks to triangulate / cross-check / get a second (and third) opinion before committing to a fix or ADR.
---

# Triangulate Diagnosis

Run three **independent** diagnoses of the same bug in parallel, keep only what they
agree on, and turn the consensus into an ADR. One diagnosis can anchor on the first
plausible cause; three blind diagnoses that land on the same root cause are trustworthy,
and where they *disagree* you learn the bug is underspecified or multi-causal.

This skill orchestrates two existing skills — it does not replace them:

- [`diagnose`](../diagnose/SKILL.md) — the disciplined reproduce → hypothesise → fix loop each subagent runs.
- [`write-a-adr`](../write-a-adr/SKILL.md) — records the converged decision and creates the follow-up issue.

## Phase 0 — Write the shared brief

Before fanning out, distill **one** bug brief that every subagent receives verbatim.
This is the only shared context — keep it factual, not interpretive, so the three
diagnoses stay independent. Do **not** include your own hypothesis or suspected cause;
that would anchor all three and defeat the point.

The brief must contain:

- The exact symptom the user described (error text, wrong output, timing), quoted.
- How to reach the code: repo paths, service, entry point, relevant commands.
- Any known repro steps, fixtures, or environment notes already in the conversation.
- Hard constraints (what must keep working, what's out of scope).
- The required output contract from [REFERENCE.md](REFERENCE.md) — every subagent returns the same structured report.

If a fact that would change the brief is missing and only the user has it, ask **one**
concise blocking question before fanning out. Otherwise proceed.

## Phase 1 — Fan out three independent diagnoses

Spawn **3 subagents in parallel**, in a single batch so they run concurrently. Each one:

- Runs the `diagnose` skill against the shared brief — full discipline: build a feedback
  loop, reproduce, generate ranked hypotheses, instrument, identify the root cause.
- Works in **isolation**: do not give a subagent the brief plus your hunch, and do not
  let them see each other's results. Identical input, independent reasoning.
- Returns the structured **Diagnosis Report** defined in [REFERENCE.md](REFERENCE.md):
  root cause, evidence, the feedback loop it built, fix location, confidence, and any
  alternative causes it ruled out.

To force genuine divergence rather than three identical passes, give each subagent a
distinct **lens** in addition to the shared brief:

1. **Repro-first** — prioritise building the feedback loop and bisecting to the change that introduced the bug.
2. **Data-flow** — trace inputs through the modules end to end; suspect boundaries, types, and joins.
3. **Recent-change / environment** — suspect recent commits, config, dependencies, infra, and timing.

The lens shapes *where they look first*, not *what conclusion to reach*. Each must still
follow the evidence wherever it leads.

If a subagent reports it could not build a feedback loop (per the `diagnose` skill's
"cannot build a loop" clause), treat its report as low-confidence and say so in Phase 2 —
do not silently average it in.

## Phase 2 — Converge

Collect the three reports and compare them. Produce a short convergence summary:

- **Consensus root cause** — the cause ≥2 subagents independently identified, stated once.
  Reconcile wording; cite the strongest evidence from each agreeing report.
- **Divergences** — where they disagree, and *why* (different lens, different repro,
  genuinely different code path). Do not paper over these.
- **Unique insights** — a real finding only one subagent surfaced (a ruled-out alternative,
  an adjacent bug, a missing test seam) worth carrying into the ADR.
- **Confidence** — high if all three converge with a shared feedback loop; medium if 2/3
  agree; low/blocked if they split three ways or none built a loop.

Decision gate:

- **All 3 or 2/3 converge** → proceed to Phase 3 with the consensus root cause.
- **Three-way split, or the split is on something the user can resolve** → stop. Report the
  three candidate causes with their evidence and ask the user which to pursue, or optionally
  spawn one tiebreaker subagent scoped to the specific disputed question. Do **not** force a
  consensus that isn't there — a non-convergence is itself the finding.

Show the convergence summary to the user before writing anything.

## Phase 3 — Record the decision

Invoke the `write-a-adr` skill, passing the convergence summary as the already-gathered
context (it is built to consume existing agent context and not restart the interview):

- The **consensus root cause** is the problem the ADR frames.
- The agreed **fix location / approach** seeds the chosen option; surfaced alternatives
  become the considered options, including "do nothing".
- **Unique insights** (missing test seam, adjacent risk) go into Consequences.
- If confidence is medium/low, set the ADR status to `Proposed` and list the unresolved
  divergences as open questions.

Let `write-a-adr` produce the ADR and the follow-up implementation issue, then report their
paths to the user. Keep the final message short: consensus cause in one line, confidence,
the ADR path, the issue path, and any open question.

## Notes on portability

This skill is agent-agnostic: "spawn 3 subagents in parallel" maps to whatever delegation
primitive the host agent provides (e.g. parallel sub-tasks). If the host cannot run
subagents concurrently, run the three diagnoses sequentially with cleared context between
each so they stay independent — slower, same guarantee. If it cannot isolate context at
all, this skill's value drops; tell the user rather than running three anchored passes.
