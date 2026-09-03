# Worktree-stable repository authority

## Artifact Graph

- Artifact ID: `spec:ticket-autopilot-worktree-stable-repository-authority`
- Role: `spec`
- Standalone: true

## Type

Bug-analysis and migration specification.

## Status

Deferred until the legacy root-catalog repair and its separate tracked-wiki update are terminal.

## Observed Regression

Repository merge and reconciliation authorities are stored under the Git common directory,
so every linked worktree reads the same authority file. Schema 1 also binds
`repository_identity` to the exact worktree root used when the authority was granted.
Every sibling worktree has a different root and therefore rejects the shared state.

The current Agent Skills files are valid and active when inspected through
`/Users/carlogiuseppesergi/Projects/.agent-skills-runner-latest`, but both the main checkout
and the clean wiki intake worktree report that the binding contradicts the repository. The
first `resume` of run `llm-wiki-legacy-root-catalog-adoption-20260903` consequently failed
before implementation with:

```text
repository reconciliation authority binding contradicts repository
```

That run is manual and has no reconciliation proposal. A stale checkout-local optional
authority should neither authorize it nor prevent unrelated implementation. More broadly,
a repository-wide grant cannot fulfill `current-and-future-runs` if moving to an isolated
linked worktree makes it unusable.

## Decision

Introduce a new repository-authority binding schema whose repository identity is stable
across linked worktrees and does not transfer to independent clones. The binding is the
exact Git common directory plus provider and normalized remote; an individual worktree
root is observational context, not authority identity.

Schema-1 checkout-bound authority is never widened automatically. A dedicated explicit
migration transaction must:

- select exactly one authority kind (`merge` or `reconciliation`);
- require the exact old state SHA-256 plus actor and durable evidence;
- validate the complete schema-1 envelope, its original checkout identity, shared Git
  common directory, provider, and normalized remote;
- persist migration intent before replacement;
- produce a schema-2 successor that retains predecessor grant/revocation provenance and
  records the migration authority;
- read back the exact successor and return an idempotent receipt;
- reject absent, malformed, symlinked, drifted, wrong-common-dir, wrong-remote, wrong-kind,
  contradictory, or ambiguous state before mutation.

Until migration, inspection from a sibling worktree reports
`legacy-binding-migration-required` rather than generic corruption. Consumers remain
fail-closed: `merge-all` or reconciliation adoption cannot use that authority. Unrelated
manual implementation may continue when no run-local merge adoption, open reconciliation
gate, or matching proposal needs the legacy authority.

## Goals

- Make repository authority genuinely stable across linked worktrees.
- Keep independent clones, remotes, and providers isolated.
- Unblock manual, non-conflicted runs from unrelated legacy authority state.
- Preserve and expose all grant, revocation, and migration provenance.
- Keep authority consumption fail-closed until explicit migration succeeds.

## Non-Goals

- Treating this specification or the current bug report as migration consent.
- Copying authority to an independent clone or a different Git common directory.
- Revoking, renewing, or broadening merge/reconciliation authority implicitly.
- Relaxing expected-head, provider eligibility, conflict proposal, or readback checks.
- Recovering the already-created WCA run by rewriting its ledger or shared authority files.

## Failure Modes

| Condition | Required result |
|---|---|
| Same Git common directory, provider, and remote; schema 2 | All linked worktrees inspect the same exact authority. |
| Independent clone with same remote | No shared authority; explicit grant is required there. |
| Schema 1 observed from its original root | Report active/revoked legacy state and migration availability. |
| Schema 1 observed from a sibling worktree | Report migration-required; do not classify as corrupt. |
| Manual run needs no repository authority | Continue without adopting or consuming legacy state. |
| `merge-all` or reconciliation needs legacy state | Fail before provider/Git mutation with exact migration guidance. |
| Migration digest or identity differs | Preserve old bytes and fail closed. |
| Exact migration replay | Return the existing receipt without a second write. |

## Verification Strategy

- Create a repository plus two linked worktrees and one independent clone with the same
  remote.
- Prove schema-2 grant/status/revocation equivalence across linked worktrees and absence in
  the clone.
- Freeze schema-1 fixtures for active and revoked merge/reconciliation authority; test
  inspection, explicit migration, replay, tamper, path, common-dir, remote, and kind drift.
- Prove a manual implementation resume proceeds with irrelevant legacy authority while
  merge/reconciliation consumption remains blocked.
- Preserve all existing repository authority, merge-all, reconciliation, context/token,
  CLI, static, forward, and Artifact Graph tests.

## Planned Slice

After the WCA tracked-wiki receipt, emit **MRA-01 — make repository authority
worktree-stable**. Its implementation owns schema-2 binding, explicit schema-1 migration,
lazy/need-based consumption, status/docs, and cross-worktree tests. It grants no authority
and does not apply a live migration.

After MRA-01 is integrated and projected, emit MAR-01 from the natural-language merge-all
spec. A live authority migration, grant, or `merge-all` invocation remains a separate
operator-authorized transaction after both code fixes are integrated.
