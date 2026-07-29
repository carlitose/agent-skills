# Candidate invalidation decision

Status: Accepted

Date: 2026-07-29

Decision: Preserve D6

Authority: explicit human decision in the ticket-06 execution session

## Decision

Any candidate-content or ticket-contract change creates a new CandidateRef and invalidates
all prior review, QA execution, verification, and merge authorization. Merge authorization
always remains bound to the currently observed PR head SHA.

Same-CandidateRef caching is the optimization ceiling. Exact cache hits may reuse validated
content-addressed evidence under the ticket-05 cache contract. A changed CandidateRef may
carry plans, templates, or facts forward only as untrusted inputs; it may not inherit a pass,
finding disposition, live observation, claim ceiling, or authorization.

## Context and measured cost

Issue #9 exposed both the cost and the safety value of invalidation:

- An incomplete review initially reported zero findings and was correctly rejected.
- A complete review found a blocker: one refresh path did not preserve terminal `expired`.
- It also found a should-fix: the kill-switch no longer had causal coverage.
- Fixing those findings changed CandidateRef, so review and tests ran again.
- The final focused QA passed 95 tests with 43 skips; full QA passed 393 tests with 53 skips
  and zero failures.

Ticket 05 removes the proven avoidable work without weakening D6: an exact complete cache hit
avoids three deterministic verification commands and consumes no additional leaf interaction.
Candidate, input, artifact, command, scope, contract, or environment drift produces a miss.

## Alternatives

| Category | Preserve D6 — accepted | Limited non-semantic carry-forward | Semantic selective reuse — rejected |
| --- | --- | --- | --- |
| Review | Rerun against the complete new candidate. | Prior findings may seed an inspection checklist but carry no disposition. | Reuse “unaffected-file” findings using a dependency/path proof. |
| QA plan | Rebind and validate the plan against the new candidate before use. | Test ideas and fixtures may be copied as untrusted inputs. | Treat an old plan as still complete for a computed change slice. |
| QA execution | Rerun causally relevant execution. | Commands may be proposed again; old results are not evidence. | Reuse results whose declared dependency slice did not change. |
| Verification | Rebuild or exact-cache only within the new CandidateRef. | Schema templates may carry forward without claims. | Reuse evidence records after graph-based impact analysis. |
| Static environment facts | Re-observe or exact-match environment identity. | Stable tool/version facts may seed inspection but are revalidated. | Reuse facts until an independently tracked environment key changes. |
| Live evidence | Re-observe the live boundary. | Endpoint identity may seed the next check; observations never carry. | Reuse time-bounded observations under a provider-specific TTL. |
| Merge authorization | Always invalidate and request exact-current-head authority. | None. | No alternative is acceptable. |

### Alternative requirements and failure modes

Preserve D6 needs no new authorization beyond this decision. Its cache identity is the full
CandidateRef plus the ticket-05 contract. A mismatch fails closed by rerunning work. Its
implementation cost is already paid and its residual cost is semantic work after mutation.

Limited non-semantic carry-forward is compatible with D6 because carried material has no pass
or claim authority. Each consumer must explicitly revalidate it. If provenance or identity is
missing, it is discarded. Implementation cost is low and no new evidence category is needed.

Semantic selective reuse would require independently validated dependency graphs for code,
generated artifacts, configuration, tests, hidden callers, environment identity, provider
state, and claim propagation. Unknown edges must invalidate. The required proof and forward
tests would be expensive, and a single missing edge can silently preserve stale evidence.
No human authorization was given for this replacement contract.

## Stale-result attacks

1. A refresh-path mutation appears local, but a reused review misses that terminal `expired`
   is no longer preserved.
2. Kill-switch wiring changes outside a test’s declared slice, so reused QA execution retains
   a green result without exercising the causal injection point.
3. A generated artifact or hidden caller changes behavior without appearing in a path-based
   dependency declaration.
4. Tool, provider, credential scope, or policy changes while cached environment facts remain
   syntactically valid.
5. A live observation ages or the remote head changes after verification.
6. Merge approval names an older SHA and is incorrectly carried to a new head.

Under D6, the two real issue-9 findings remain discoverable after mutation: the new candidate
must receive a complete review, which rechecks `expired`, and causal QA must replay the
kill-switch injection point. Selective semantic reuse cannot guarantee either result unless
it recreates the same fail-closed scope, at which point it offers little advantage over D6.

## Consequences

- Ticket 05 remains the authorized performance optimization.
- No selective-invalidation implementation or forward-test tickets are emitted.
- Review/QA plans and static facts may reduce preparation effort only as non-authoritative
  inputs.
- Missing live evidence and partial inspection cannot survive as a stronger claim.
- A future D6 replacement requires a new explicit human decision, a precise causal contract,
  independent evidence, and separate implementation plus integrated forward-test tickets.
