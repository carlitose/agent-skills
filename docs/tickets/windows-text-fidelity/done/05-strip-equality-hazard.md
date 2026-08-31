---
ticket_schema: 1
ticket_id: "WT-05"
execution_mode: AFK
blocked_by: []
---

# Resolve the deferred `.strip()` equality hazard

## Artifact Graph
- Artifact ID: `artifact:wt-05-strip-equality-hazard`
- Role: `ticket`
- Parent: [windows-text-fidelity-wayfinder.md](../../specs/windows-text-fidelity-wayfinder.md)

## Parent Spec
[windows-text-fidelity-wayfinder.md](../../specs/windows-text-fidelity-wayfinder.md)

## What to Build
`SubprocessCommandRunner.run` returns `CommandResult(stdout=result.stdout.strip(),
stderr=result.stderr.strip(), ...)`. `WD-02` explicitly declined to touch it and named it
what it is:

> The `.strip()` applied to stdout and stderr in the same method, which is a separate
> latent equality hazard and needs its own decision.

That decision is now overdue, because the family has produced a third instance of the same
failure shape. `WT-01` fixed a lost **trailing newline** that broke a literal comparison at
`finalizer.py:1103`; `.strip()` destroys trailing whitespace and newlines on every command
result that passes through this runner. Any current or future value read through it and
then compared for equality carries the same defect, silently.

The task is to determine which consumers depend on the stripping, which would break if it
were removed, and whether stripping belongs at the call sites that want it rather than in
the shared runner.

## Acceptance Criteria
- [ ] Every consumer of `CommandResult.stdout` / `.stderr` is enumerated, with whether it
      relies on the value being stripped.
- [ ] A decision is recorded: strip at the runner, strip at the call sites, or expose both
      raw and stripped.
- [ ] No consumer that feeds an equality, digest, or readback comparison receives a value
      that was silently trimmed.
- [ ] A test covers a command whose output legitimately ends in whitespace.
- [ ] `WD-02`'s deferral is marked resolved.

## Frontier
Ready. This is investigative before it is corrective: the enumeration in step 1 may show
the hazard is inert, in which case the outcome is a documented invariant rather than a code
change. Do not remove the `.strip()` before knowing who depends on it.

## Step-by-Step Implementation Plan
1. Enumerate consumers of `CommandResult`. Checkpoint: a list, with each one classified as
   whitespace-sensitive or not.
2. Identify any consumer feeding an equality or digest check. Checkpoint: named, or the
   hazard is declared inert with evidence.
3. Apply the chosen shape. Checkpoint: suite no worse than the `WT-06` baseline.
4. Add the trailing-whitespace test.

## Testing Plan
Automated: a unit test driving a child process whose stdout ends with whitespace and a
newline, asserting the contract the decision chose. Regression: the full suite, compared
against the baseline established by `WT-06`.

## Out of Scope
- The `errors` policy in the same method, which is `WT-02` and `WT-03`.
- The body round trip, which is `WT-01`.
