# GitHub required-check policy readback

## Artifact Graph
- Artifact ID: `artifact:github-required-check-readback`
- Role: `spec`
- Standalone: true

### Children
- [GP-01](../tickets/github-required-check-readback/01-observe-required-checks.md)

## Bug analysis
Todo #58: `ProviderExecutor` reads active rulesets but not classic branch protection.
On `agent-skills/main`, the rules endpoint returns `[]` while classic protection requires
`local-profile`. A required check absent from the PR rollup is consequently omitted.
Todo #62: ruleset `integration_id` is ignored; a successful same-name check does not prove
that the required GitHub App produced it. These are adapter defects, not merge authority.

Primary contracts: [branch protection](https://docs.github.com/en/rest/branches/branch-protection#get-branch-protection),
[check runs](https://docs.github.com/en/rest/checks/runs#list-check-runs-for-a-git-reference), and
[GitHub OpenAPI](https://github.com/github/rest-api-description).
Read-only probes distinguish `Branch not protected` from `Branch not found` and generic
404s. The private-plan 403 has the exact upgrade message and endpoint documentation URL;
it is capability evidence, not proof of passing CI or a permission waiver.

## Target and invariants
- Observe active rulesets and classic protection for the base read from the exact-head PR.
- Union their required contexts, including classic `contexts` and `checks`; deduplicate
  identical requirements without discarding app-specific constraints.
- Missing checks remain pending. A known required app (`app_id` / `integration_id`) needs
  a current-head check-run readback for that app, not merely a name in the rollup.
- Treat null or unspecified app identity as no declared app constraint; classic `-1`
  explicitly denotes any app. Never infer a concrete app from these values.
- Use paginated check-run reads with `app_id` and `filter=latest`; validate returned head
  and app identity. Preserve the existing GitHub CLI 2.35 contract: `--paginate` emits JSON
  object pages; consume every document without the newer `--slurp` flag (candidate defect #63).
  A foreign, incomplete, malformed, or failed read must not become PASS.
- Only the exact observed unprotected-branch 404 means absent classic protection.
  Missing branches, generic 404s, permissions, rate limits, and malformed responses fail
  closed. Preserve the exact private-plan limitation as `feature-unavailable`, separately
  from absence and successful observations, without discarding other observed policies.
- Keep merge-queue selection, approval checks, expected-head mutation guards, authority,
  existing non-passing rollup checks, and Azure behavior unchanged.

## Design and scope
Keep the existing `ProviderExecutor.execute(GET_CHECKS_AND_POLICIES, ...)` boundary.
Private helpers own external response validation and required-check normalization; the
existing command runner is the test seam. Alternatives are an independent policy adapter
(extra interface and migration for one caller) or caller-side compensation (duplicates
policy logic and misses future callers). Prefer locality for this bounded change.
Receipt additions distinguish classic-policy observations; do not label classic policy
as a ruleset. No remote policy mutations, new scheduler, generic authorization mechanism,
ledger rewrite, credential changes, or unrelated provider refactor.

## Implementation and verification
One AFK ticket, GP-01, covers both defects through the same policy-readback boundary.
First reproduce missing classic requirements and incorrect app satisfaction with public
adapter tests. Cover both sources together, deduplication, unprotected/private-plan cases,
ordinary errors, malformed data, head/app mismatch, pagination, and pass/pending/failure.
Update existing command fakes to explicitly model unprotected branches; do not loosen
assertions or silently accept unknown commands. Run affected normalization and merge-gate
regressions, then required current-head CI. A controlled live read verifies the adapter
against existing protection without modifying it. Inline review is not independent review.

Execution remains skills-only and serial. Every command/job is bounded at 900 seconds or
less; retained failures and cumulative verification cost survive retries. Wiki sync and
active runtime reload remain deferred, not successful. Publication and merge need their
separate existing authority and exact-head CI/readback; tests alone prove neither.
