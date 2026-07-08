# Reference: Diagnosis Report Contract and Convergence Rubric

## Diagnosis Report

Every subagent finishes its `diagnose` pass by returning a report in this shape. Keeping
the shape identical across all three reports makes convergence mechanical.

```markdown
## Diagnosis Report - lens: <repro-first | data-flow | recent-change>

### Root cause
<One paragraph: the single mechanism that produces the symptom. Name the file:line or
module/boundary where it originates.>

### Evidence
- <What in the feedback loop or instrumentation proves this: observed values, diffs,
  failing assertion, timing measurement. Concrete, not "it looks like".>

### Feedback loop built
<How the bug was reproduced: failing test path, curl script, harness, replay. State if no
loop could be built; this downgrades the report to low confidence.>

### Fix location and approach
<Where the fix goes and the shape of it. Not a full implementation.>

### Alternatives ruled out
- <Hypothesis considered and the evidence that falsified it.>

### Confidence: <high | medium | low>
<One line: why this confidence level.>
```

## Convergence Rubric

Match root causes across reports by mechanism, not by wording. Two reports describing the
same faulty code path in different words still count as agreement.

| Outcome | Condition | Action |
|---|---|---|
| **Strong consensus** | All three identify the same mechanism, and at least two have a working feedback loop | Proceed to diagnostic spec, confidence high |
| **Majority** | Two of three agree on the mechanism | Proceed to diagnostic spec, confidence medium; record the dissent as an open question |
| **Split** | All three differ, or the disagreement hinges on a fact the user holds | Stop. Report the candidates and evidence; ask the user or spawn one scoped tiebreaker |
| **Blocked** | No subagent could build a feedback loop | Do not write a spec. Report what each tried and what access or artifact is needed |

Carry forward into the spec, regardless of outcome:

- The consensus mechanism, or the candidate set if split.
- The strongest single piece of evidence from each agreeing report.
- Any unique insight, such as a missing test boundary, adjacent bug, or ruled-out
  alternative worth documenting.
