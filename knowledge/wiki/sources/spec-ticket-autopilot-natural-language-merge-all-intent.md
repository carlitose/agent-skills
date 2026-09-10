---
type: source
title: "Natural-language repository-wide merge-all intent"
identity_key: spec:ticket-autopilot-natural-language-merge-all-intent
identity_strength: stable
source_path: docs/specs/ticket-autopilot-natural-language-merge-all-intent.md
source_digest: sha256:972ab8d020af44be7752b6d63a5864202579973cc5f1aa146be046fe0cb84980
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-09-03
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Natural-language repository-wide merge-all intent

Compiled from `docs/specs/ticket-autopilot-natural-language-merge-all-intent.md`. Identity is `spec:ticket-autopilot-natural-language-merge-all-intent`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-03** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Child source: [[sources/ticket-ticket-autopilot-natural-language-merge-all-intent-mar-01]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"decisions":{"headings":[6],"status":"present"},"exclusions":{"headings":[9],"status":"present"},"goals":{"headings":[8],"status":"present"},"invariants":{"headings":[],"status":"not-identified"},"verification":{"headings":[11],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/spec-ticket-autopilot-natural-language-merge-all-intent.md","payload_bytes":6860,"payload_sha256":"972ab8d020af44be7752b6d63a5864202579973cc5f1aa146be046fe0cb84980"}],"payload_bytes":6860,"payload_sha256":"972ab8d020af44be7752b6d63a5864202579973cc5f1aa146be046fe0cb84980","schema":1,"source_digest":"sha256:972ab8d020af44be7752b6d63a5864202579973cc5f1aa146be046fe0cb84980","source_identity":"spec:ticket-autopilot-natural-language-merge-all-intent","source_kind":"spec"} -->

| Topic | Source sections |
|---|---|
| goals | 8: Goals |
| exclusions | 9: Non-Goals |
| decisions | 6: Decision |
| invariants | no matching section identified in the source; complete source retained |
| verification | 11: Verification Strategy |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":6860,"payload_sha256":"972ab8d020af44be7752b6d63a5864202579973cc5f1aa146be046fe0cb84980","schema":1,"source_digest":"sha256:972ab8d020af44be7752b6d63a5864202579973cc5f1aa146be046fe0cb84980","source_identity":"spec:ticket-autopilot-natural-language-merge-all-intent"} -->
```markdown
# Natural-language repository-wide merge-all intent

## Artifact Graph

- Artifact ID: `spec:ticket-autopilot-natural-language-merge-all-intent`
- Role: `spec`
- Standalone: true

### Children

- [MAR-01 — Restore natural-language merge-all intent](../tickets/ticket-autopilot-natural-language-merge-all-intent/done/01-restore-natural-language-merge-all-intent.md)

## Type

Bug-analysis specification.

## Status

Accepted for MAR-01. The legacy root-catalog repair, worktree-stable
repository-authority repair, and their separately protected tracked-wiki updates have
terminal receipts.

## Problem

Ticket Autopilot already implements repository-wide merge authority through
`grant-repository-autonomous-merge --scope current-and-future-runs` and consumes it through
`merge-all`. The runner correctly obtains and checks every live PR head itself before each
provider mutation.

The natural-language routing contract does not make that distinction explicit. A clear
imperative such as “merge all”, “merge everything”, or “mergia tutto” can therefore be
misinterpreted as a one-PR exact-head approval. The agent then asks the operator to supply a
SHA or says that the phrase applies only to the PR/head currently displayed. That defeats
the repository-wide feature and is the reported regression.

The defect is in agent-facing intent classification and orchestration guidance, not in the
expected-head safety check inside the runner. The current runner and README already expose
the repository-wide grant and `merge-all` commands; the missing contract is in
`ask-skills`, the mandatory policy injected by `mandatory-agent-skills`, Ticket Autopilot's
operator guidance, and their regression tests.

## Decision

An unambiguous, affirmative repository-wide imperative from the user routes directly to
Ticket Autopilot's repository authority flow:

1. identify the exact repository and provider from current durable context;
2. inspect the canonical repository-authority status;
3. if authority is absent, use the human actor and durable message reference from the
   affirmative instruction to invoke `grant-repository-autonomous-merge` with scope
   `current-and-future-runs`; if an exact grant is already active, preserve and use it
   without replacing its provenance; fail closed on revoked, legacy, malformed, or
   contradictory state;
4. invoke `merge-all` for that repository;
5. report every merged, gated, skipped, or reconciliation result.

The agent must not ask the user for a PR head SHA. Ticket Autopilot must continue to fetch
the live head, revalidate policy and eligibility, and bind the mutation to that expected
head immediately before each merge. Head drift invalidates volatile eligibility for the
individual attempt; it does not silently narrow or revoke the repository-wide grant.

The phrase does not grant conflict resolution, force push, code changes, source or wiki
publication, bootstrap, Pi synchronization, cleanup, visibility changes, or history
rewriting.

## Authority Classification

Imperative consent and discussion must remain distinct:

- “Mergia tutto in questo repository” is affirmative repository-wide merge intent when the
  repository identity and a durable message reference are available.
- “Quando dico ‘mergia tutto’, non chiedermi lo SHA” is a policy/change request, not an
  instruction to merge current PRs.
- Quoted text, examples, questions, negations, revocation, and bug reports never manufacture
  merge authority.
- An ambiguous repository identity still requires clarification; an absent user-supplied
  SHA does not.

No free-form locale parser is required in the runner. `mandatory-agent-skills` routes all
natural-language input to `ask-skills`; the durable contract belongs in `ask-skills`, the
mandatory policy, and Ticket Autopilot's operator guidance. Tests must pin both the positive
route and the quoted/descriptive non-authority boundary.

## Goals

- Restore the intended one-command repository-wide user experience.
- Keep expected-head TOCTOU protection internal and mandatory.
- Prevent an agent from narrowing “merge all” to one currently displayed PR.
- Prevent quoted or descriptive mentions from becoming provider authority.
- Keep repository-wide authority independently revocable and visible.

## Non-Goals

- Relaxing live checks, rules, approvals, mergeability, expected-head, queue, or readback.
- Adding a provider bypass or automatically resolving conflicts.
- Treating this bug report as a live `merge-all` authorization.
- Changing exact-head semantics for manual one-PR approval.
- Inferring a repository when multiple plausible repositories remain.

## Failure Modes

| Condition | Required result |
|---|---|
| Clear affirmative merge-all intent, exact repository known | Grant absent authority or reuse an exact active grant, then run `merge-all`; never request a SHA. |
| User supplies no SHA | Continue; the runner discovers each live head. |
| Head changes before mutation | Re-observe that PR and apply the existing expected-head contract. |
| Quoted/descriptive/negative mention | Do not grant or merge; route as discussion, diagnosis, or delivery work. |
| Repository identity is ambiguous | Ask only for repository disambiguation. |
| Authority is absent | Persist the new actor/evidence-bound grant before `merge-all`. |
| Authority is exact and active | Preserve its provenance and continue to `merge-all`. |
| Authority is revoked, legacy, malformed, or contradictory | Fail closed before provider mutation and report the authority problem. |
| Conflict or non-merge gate remains | Report it without consuming unrelated authority. |

## Verification Strategy

- Static contract tests assert that `ask-skills` routes affirmative repository-wide merge
  language to Ticket Autopilot and explicitly forbids asking for a caller-supplied head.
- Mandatory-policy tests assert the same distinction and the non-authority treatment of
  quotations, examples, negations, and bug reports.
- Existing repository merge-authority tests continue proving current and future run
  adoption, revocation, fresh live head validation, and expected-head mutation.
- Context/token tests ensure the clarified policy remains within project budgets.
- Full extension, Ticket Autopilot, compile, diff, and Artifact Graph checks remain green.

## Planned Slice

Emit **MAR-01 — restore natural-language merge-all intent** from the exact integrated
source after the wiki update receipt and integration/projection of the separate
worktree-stable repository-authority repair. The ticket updates only agent-facing
routing/operator contracts and their regression tests unless a fresh implementation pass
demonstrates another runner defect. Any newly observed runner defect must return through
diagnosis/specification rather than silently expanding this slice.

```
