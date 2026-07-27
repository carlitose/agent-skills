---
name: "code-review"
description: "Review a runner candidate or standalone PR, commit, local diff, or requested scope read-only for regressions, evidence gaps, and overclaims."
---

# Code Review

Owns: read-only review findings for one frozen scope. It never edits files, runs a quality
loop, produces a Verification Record, decides the final claim ceiling, or mutates
Git/provider state.

Use the semantic vocabulary and required fields from the canonical
[Verification Record](../verification-audit/references/verification-record.md). Flag
missing or contradictory inputs; do not reconstruct a second evidence/gate policy.

## Inputs

Accept one acquisition route:

- **Runner handoff:** frozen diff, CandidateRef, normalized Ticket Envelope, acceptance
  criteria, decisions, baseline, observed evidence, and draft record when one exists.
- **Standalone acquisition:** acquire a PR, commit, local diff, or user-requested scope
  read-only; record its observed head/commit/worktree identity, request constraints,
  relevant repository rules, and available baseline/evidence.

Do not parse Markdown to infer a Ticket Envelope. If standalone context has no normalized
ticket, review against the explicit request and repository contract. If the diff changes,
return `stale-candidate` and stop.

## Review axes

Review independently and report only evidence-backed findings:

1. **Standards and maintainability** — project conventions, clarity, accidental
   complexity, unsafe error handling, security, data integrity, and unrelated scope.
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

Sort by severity:

```text
[blocker|should-fix|nit] path:line - problem and impact. Suggested fix.
```

- `blocker`: correctness, security, data loss, ticket failure, missing causal coverage, or
  a material unsupported claim.
- `should-fix`: meaningful maintainability or non-critical coverage problem.
- `nit`: optional polish only.

For every finding, name the violated acceptance criterion, invariant, boundary item, or
repository rule when available. If no finding exists, say so and list residual evidence
limits. A standalone output is a read-only draft; it cannot claim ticket completion or release.
Never report PASS for a CandidateRef or standalone scope you did not inspect.
