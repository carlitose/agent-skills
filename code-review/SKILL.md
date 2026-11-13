---
name: "code-review"
description: "Review a runner candidate or standalone PR, commit, local diff, or requested scope read-only for regressions, evidence gaps, and overclaims."
---

# Code Review

Owns: read-only review findings for one frozen scope. No edits, quality-loop execution,
Verification Record, final claim-ceiling decisions, or Git/provider mutations.

Use canonical [Verification Record](../verification-audit/references/verification-record.md)
vocabulary and fields. Flag missing/contradictory inputs; never clone its evidence/gate policy.

## Inputs

Accept one acquisition route:

- **Runner handoff:** frozen diff, CandidateRef, normalized Ticket Envelope, acceptance
  criteria, decisions, baseline, observed evidence, and draft record when one exists.
- **Standalone acquisition:** read a PR, commit, local diff, or user-requested scope;
  record observed head/commit/worktree identity, request constraints, repository rules,
  and available baseline/evidence. Stay read-only.

Do not infer a Ticket Envelope from Markdown. Without one, review the explicit request
and repository contract. A changed diff returns `stale-candidate`; stop.

## Volatile intake bound

- `max_volatile_bytes`: `107656` normalized UTF-8 bytes per invocation: observed candidate
  diff high-water 96,393 + ticket-body maximum 2,380 + implementation-handoff maximum
  4,459 + simplification maximum 4,424 bytes. Corpus: run TK-01/TK-02/TK-05/TK-07/TK-08
  normalized `git diff --no-ext-diff --no-color` observations, nine tickets, compact leaf results.
- `max_single_output_bytes`: `32596`, the observed TK-02 executable-code candidate diff.

Count diffs, raw file slices, handoffs, evidence and tool results after CRLF/lone-CR to LF
normalization. Acquire the manifest first; truncate command output before it enters context
and slice large diffs by file/hunk. Prefer path plus SHA-256 references over pasted artifacts;
read content only for a review axis. Before exceeding a cap, return a schema-3 partial result
with exact inspected/remaining scope and `budget-exhausted`; never skip scope or downgrade findings.

## Bounded runner handoff

Honor the runner's schema-3 bounded `LeafContext`: CandidateRef, canonical phase contract,
expected file manifest, prior inspection, remaining scope and resource limits define the
authoritative continuation boundary. Do not reread inspected immutable scope for that CandidateRef.

End every runner-owned turn, including timeout/interruption/exhaustion, with a schema-3
result: exact CandidateRef and review phase contract, ordered expected/inspected/remaining
files, commands, findings, current phase, canonical remaining-phase suffix, and a nonempty
stop reason for partial results.

Include normalized schema-3 `execution` from the observed route. A shared-context or
unknown isolation is not independent; report that limitation instead of upgrading it.

A complete review must reach `handoff-ready`, inspect the declared scope, and return
validated structured findings. Partial results resume, never pass. Findings may return
to implementation and consume a quality failure; timeout/interruption/exhaustion do not.
CandidateRef drift invalidates the handoff.

## Review axes

Review each axis separately and report only evidence-backed findings:

1. **Standards and maintainability** — project conventions, clarity, accidental
   complexity, unsafe error handling, security, data integrity, and unrelated scope.
   Search the repository for every file that documents how code should be written;
   `CODING_STANDARDS.md` or `CONTRIBUTING.md`, when present, is always on that list.
2. **Ticket acceptance** — every criterion has a concrete implementation path and
   observable check; non-goals remain untouched.
3. **Semantic regression** — externally meaningful behavior is preserved or explicitly
   authorized. Compare changed boundaries and invariants to the supplied baseline.
4. **Causal coverage** — tests/evidence exercise the changed mechanism, not merely an
   adjacent success path. Identify mocked or simulated boundaries explicitly.
5. **Claim safety** — wording does not exceed the evidence and open gates represented in
   the canonical record.

Inspect raw files and diffs rather than trusting summaries. Do not call
`verification-audit`; the caller supplies findings to its single audit pass.

## Finding format

Before reporting a finding, check it against the callers, guards, and tests that reach the
changed code, and drop it if they rule it out. Label a defect already present in the baseline
`pre-existing` in its problem text, separately from regressions this change introduces.
Zero findings is a valid result; do not invent one.

Sort by severity:

```text
[blocker|should-fix|nit] path:line - problem and impact. Suggested fix.
```

- `blocker`: correctness, security, data loss, ticket failure, missing causal coverage, or
  a material unsupported claim.
- `should-fix`: meaningful maintainability or non-critical coverage problem.
- `nit`: optional polish only.

Name each finding's violated criterion, invariant, boundary item or repository rule when
available. If none, say so and list residual evidence limits. A standalone output is a read-only draft; it cannot claim ticket completion or release.
Never report PASS for a CandidateRef or standalone scope you did not inspect.
