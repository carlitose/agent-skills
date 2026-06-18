# Reference — Diagnosis Report contract & convergence rubric

## Diagnosis Report (each subagent returns exactly this)

Every subagent finishes its `diagnose` pass by returning a report in this shape. Keeping
the shape identical across all three is what makes Phase 2 convergence mechanical.

```markdown
## Diagnosis Report — lens: <repro-first | data-flow | recent-change>

### Root cause
<One paragraph: the single mechanism that produces the symptom. Name the file:line
or module/boundary where it originates.>

### Evidence
- <What in the feedback loop / instrumentation proves this — observed values, diffs,
  failing assertion, timing measurement. Concrete, not "it looks like".>

### Feedback loop built
<How the bug was reproduced: failing test path, curl script, harness, replay. State if
NO loop could be built — this downgrades the report to low confidence.>

### Fix location & approach
<Where the fix goes and the shape of it. Not a full implementation.>

### Alternatives ruled out
- <Hypothesis considered and the evidence that falsified it.>

### Confidence: <high | medium | low>
<One line: why this confidence level.>
```

## Convergence rubric (Phase 2)

Match root causes across reports by **mechanism**, not by wording — two reports describing
the same faulty code path in different words still count as agreement.

| Outcome | Condition | Action |
|---|---|---|
| **Strong consensus** | All 3 identify the same mechanism, ≥2 with a working feedback loop | Proceed to ADR, confidence high |
| **Majority** | 2 of 3 agree on the mechanism | Proceed to ADR, confidence medium; record the dissent as an open question |
| **Split** | All 3 differ, or the disagreement hinges on a fact the user holds | Stop. Report 3 candidates + evidence; ask user or spawn one scoped tiebreaker |
| **Blocked** | No subagent could build a feedback loop | Do not write an ADR. Report what each tried and what access/artifact is needed (per the `diagnose` skill's no-loop clause) |

Carry forward into the ADR, regardless of outcome:

- The **consensus mechanism** (or the candidate set, if split).
- The **strongest single piece of evidence** from each agreeing report.
- Any **unique insight** — a missing test seam, an adjacent bug, a ruled-out alternative
  that's still worth documenting — even from a non-consensus report.
