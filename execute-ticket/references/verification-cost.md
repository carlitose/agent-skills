# Verification admission and cumulative cost

Load before executing checks, constructing a QA plan, or deciding whether candidate drift
requires another suite. This contract owns execution selection and accounting, not the
Verification Record, repository profile policy, command execution, or authorization.

## Preflight before cost

1. Confirm checkout ownership, the fresh remote target, implementation base, staged tree
   and allowed paths. Stop on unexplained drift; do not repair another checkout implicitly.
2. Inspect the **delivered tree**, not just the working directory: includes/exclusions,
   ignored or untracked source artifacts, required generated files, and artifact graph.
   Every delivered local link must resolve in that tree. Planning-only specs/tickets must
   not become dangling delivery links. Run the owning validators before expensive QA.
3. Inventory prior attempts and the proposed checks. Map each changed mechanism to its
   smallest causal check, plus all checks required by the repository and provider policy.

Completion criterion: identity and packaging checks have current results; every selected
check has a causal or mandatory-policy reason; prior cost and the remaining authorized
budget are recorded. A missing preflight blocks expensive execution, not an invitation to
run the suite first and inspect packaging afterward.

## Drift and reruns

Candidate drift invalidates current-candidate claims. Preserve each old observation with
its original CandidateRef, command, environment, source fingerprint and artifact hash.
An unchanged-code argument can justify a smaller **new** check selection; it cannot change
an old result's identity or claim a suite ran on the new candidate.

A documentation/packaging-only delta calls for packaging, graph and affected checks. It
does not by itself justify repeating every test. Before repeating a complete suite, record
what changed in its tested mechanism, which mandatory requirement demands it, or which
specific unresolved failure the rerun diagnoses. Also record what the rerun can distinguish
and its remaining budget. If none applies, do not launch it automatically. A timeout,
compaction, new shard number, new candidate or transition to skills-only is not a retry grant.

Required full profiles and exact-head CI remain required. Never delete tests, weaken
assertions, hide failures or turn an unavailable required check into PASS to avoid cost.
If policy requires a fresh full pass despite a small delta, state that reason explicitly.

Completion criterion: the selected checks cover changed mechanisms and required policy;
each full repeat has a specific reason and budget; old evidence remains unchanged and
unexecuted current checks remain visible gaps.

## One cumulative account

Use existing command receipts and QA evidence, not another scheduler or Verification Record
schema. Include, for each attempt/shard: original candidate, command/check IDs, source
fingerprint, environment, start/end or measured duration, outcome, artifact/hash, and the
reason it was executed. Include failures, timeouts, interruptions and superseded attempts.

Report separately:
- measured elapsed time of each invocation;
- summed invocation time across **all** attempts/shards (including parallel work);
- end-to-end elapsed time, only when actually measured;
- unknown durations/termination, plus any known lower bound;
- planned next cost and remaining authorized budget.

Do not call a sum of parallel invocation durations wall-clock latency. Missing timing is
unknown, never zero. A fresh candidate does not reset consumption. A process whose
termination was not observed remains unresolved; no overlapping replacement is admitted
until its state is known. Required checks exceeding the remaining budget create an explicit
gate, not a larger invented budget.

Completion criterion: every known attempt is present once, totals distinguish time measures,
unknowns remain explicit, and selection does not erase cost or relabel stale evidence.

## Enforcement boundary

The mandatory agent policy, execute-ticket and QA-plan construction require this checkpoint.
It is an agent workflow contract, **not a shell interceptor** or proof that an arbitrary
model will obey. Report an observed violation and retain its consumption; never claim an
unexecuted runtime guard prevented it.
