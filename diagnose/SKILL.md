---
name: diagnose
description: Diagnose one bug by reproducing it, testing hypotheses, locating the root cause, and returning an evidence-backed diagnosis report. Use when the user wants root-cause analysis before implementation, or when triangulate-diagnosis delegates an independent diagnostic pass.
---

# Diagnose

Find the mechanism that produces a bug. This skill diagnoses; it does not implement the
fix unless the user explicitly asks for implementation after the diagnosis.

When invoked by `triangulate-diagnosis`, use the provided lens and return the exact
Diagnosis Report shape from
[`triangulate-diagnosis/REFERENCE.md`](../triangulate-diagnosis/REFERENCE.md).

## Inputs

Accept any of:

- A bug report, error message, failing behavior, screenshot, log, or pasted stack trace.
- Reproduction steps or a failing test.
- A local issue, spec, ticket, PR, commit, branch, or file path already available in
  context.
- A diagnostic lens from `triangulate-diagnosis`: repro-first, data-flow, or
  recent-change / environment.

Ask one concise question only when the symptom or target repository area is too ambiguous
to start. Otherwise proceed with explicit assumptions.

## Secret-safe evidence boundary

Apply the [secret-redaction boundary](references/secret-redaction.md) before displaying,
quoting, delegating, or durably capturing any diagnostic command, output, or artifact.
Replace secret values and secret-bearing arguments with `<REDACTED>` while retaining the
smallest non-secret context that carries the diagnostic signal. Build feedback loops with
environment-variable references rather than literal credentials.

If redaction removes evidence required to distinguish the remaining hypotheses, stop at
that boundary and request only a safely redacted artifact or separately authorized
instrumentation. Never ask for, echo, or persist the raw secret.

## Process

### 1. Restate the symptom and boundary

Write a short working brief:

- The observed behavior.
- The expected behavior.
- The affected entry point, module, workflow, or command.
- The constraints and non-goals.
- What evidence is already available.

Keep this factual. Do not start from a favored cause.

### 2. Build the feedback loop

Prefer an automated reproduction:

- Existing failing test.
- New targeted failing test.
- Minimal script, command, curl request, fixture, replay, or manual sequence.

If no loop can be built, continue only far enough to identify what artifact or access is
missing. Mark the final confidence low.

### 3. Inspect current behavior

Trace the bug from the observable symptom toward the responsible boundary:

- Inputs, persisted state, configuration, environment, and feature flags.
- Callers and callees across the affected path.
- Error handling, fallback paths, caching, timing, and concurrency.
- Recent changes, migrations, dependency changes, or deployment differences when relevant.

Keep exploration proportional to the symptom. Read nearby code and tests before broad
searching.

### 4. Form and falsify hypotheses

Maintain a short list of candidate mechanisms. For each serious candidate:

- Name the mechanism precisely.
- Predict what evidence should appear if it is true.
- Run the smallest check that can confirm or falsify it.
- Record alternatives ruled out with concrete evidence.

Do not treat "this code looks suspicious" as evidence.

### 5. Locate the root cause

Stop when the evidence identifies the mechanism that produces the symptom. Name the
originating file, module, interface, data boundary, or configuration source. Use line
numbers when they are stable and useful, but prefer durable module/function anchors.

If several causes remain plausible, report the split instead of forcing a single answer.

### 6. Recommend the fix path

Describe the smallest coherent fix location and approach:

- What should change.
- Why that change addresses the mechanism.
- What test or feedback loop should prove the fix.
- Risks or nearby behavior to watch.

Do not edit files unless the user explicitly asked to fix the bug in the same turn.

## Output

Use this shape:

```markdown
## Diagnosis Report - lens: <single-pass | repro-first | data-flow | recent-change>

### Root cause
<One paragraph: the mechanism that produces the symptom and where it originates.>

### Evidence
- <Concrete observation from a test, command, log, instrumentation, code path, or trace.>

### Feedback loop built
<Failing test, command, script, replay, or manual sequence. State if none could be built.>

### Fix location and approach
<Where the fix goes and the smallest coherent shape of it.>

### Alternatives ruled out
- <Hypothesis and the evidence that falsified it.>

### Confidence: <high | medium | low>
<One line explaining the confidence level.>
```

If the user asked for implementation too, finish the diagnosis first, then either proceed
with the requested fix or route the result into `to-spec`, `to-tickets`, or
`execute-ticket` depending on the requested workflow.
