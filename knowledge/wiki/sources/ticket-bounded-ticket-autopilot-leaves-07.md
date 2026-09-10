---
type: source
title: "Add a docs-only fast path to ticket-autopilot"
identity_key: ticket:bounded-ticket-autopilot-leaves/07
identity_strength: stable
source_path: docs/tickets/bounded-ticket-autopilot-leaves/done/07-add-docs-only-fast-path.md
source_digest: sha256:8353882a3fba2c6d26e93891a142bb7c1e13ab7cdfc5882fb26759140f466fb7
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-11
created_provenance: git-commit
disposition_changed: 2026-08-12
disposition_changed_provenance: git-rename
run_id: bounded-07-stable-user-root-20260812
---

# Add a docs-only fast path to ticket-autopilot

Compiled from `docs/tickets/bounded-ticket-autopilot-leaves/done/07-add-docs-only-fast-path.md`. Identity is `ticket:bounded-ticket-autopilot-leaves/07`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-11** via `git-commit`
- Disposition changed: **2026-08-12** via `git-rename`

## Graph

- Parent source: [[sources/artifact-bounded-ticket-autopilot-leaves-wayfinder]]

## Run

Completed under autopilot run `bounded-07-stable-user-root-20260812`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-bounded-ticket-autopilot-leaves-07.md","payload_bytes":5905,"payload_sha256":"8353882a3fba2c6d26e93891a142bb7c1e13ab7cdfc5882fb26759140f466fb7"}],"payload_bytes":5905,"payload_sha256":"8353882a3fba2c6d26e93891a142bb7c1e13ab7cdfc5882fb26759140f466fb7","schema":1,"source_digest":"sha256:8353882a3fba2c6d26e93891a142bb7c1e13ab7cdfc5882fb26759140f466fb7","source_identity":"ticket:bounded-ticket-autopilot-leaves/07","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":5905,"payload_sha256":"8353882a3fba2c6d26e93891a142bb7c1e13ab7cdfc5882fb26759140f466fb7","schema":1,"source_digest":"sha256:8353882a3fba2c6d26e93891a142bb7c1e13ab7cdfc5882fb26759140f466fb7","source_identity":"ticket:bounded-ticket-autopilot-leaves/07"} -->
```markdown
---
ticket_schema: 1
ticket_id: "07"
execution_mode: AFK
blocked_by: []
---

# Add a docs-only fast path to ticket-autopilot

## Artifact Graph

- Artifact ID: `artifact:bounded-ticket-autopilot-leaves-ticket-07`
- Role: `ticket`
- Parent: [Bounded Ticket-Autopilot Leaves](../../specs/bounded-ticket-autopilot-leaves-wayfinder.md)

## Parent Spec

[Bounded Ticket-Autopilot Leaves](../../specs/bounded-ticket-autopilot-leaves-wayfinder.md)

## What to Build

Add a fail-closed path for a prebuilt documentation candidate so `ticket-autopilot` can
validate and deliver it without invoking `execute-ticket`. The fast path is eligible only
through an explicit machine-readable request and an observed frozen diff restricted to the
approved project-documentation scope. It must retain CandidateRef identity, ticket scope,
documentation checks, honest claim ceilings, provider readback, and exact-head merge
authorization.

This slice addresses decision and spec tickets whose substantive output was already created
by a grilling or specification flow. It does not infer eligibility from ticket prose or
from an unverified filename extension.

## Acceptance Criteria

- [ ] A versioned, explicit docs-only candidate-adoption contract binds the normalized
      Ticket Envelope, ticket digest, base tree, candidate tree, expected changed paths,
      and approved documentation scope.
- [ ] An eligible adopted candidate whose complete frozen diff is restricted to approved
      `docs/**` Markdown and runner-owned ticket-completion artifacts reaches documentation
      validation and delivery with zero `execute-ticket` invocations and zero leaf-model
      interactions.
- [ ] Agent-executable instructions, skill definitions, manifests, configuration, scripts,
      source code, generated outputs, symlinks, submodules, and paths outside the approved
      documentation scope are ineligible even when their filenames look document-like.
- [ ] Eligibility is rechecked from Git at adoption, before every state mutation, and before
      delivery; missing paths, scope drift, unstaged changes, or tree mismatch fail closed.
- [ ] The fast path runs deterministic patch-integrity, artifact-graph, link, and applicable
      documentation regression checks and records content-addressed evidence for the exact
      CandidateRef.
- [ ] Verification cannot claim runtime behavior, independent review, live host behavior,
      or production readiness from the docs-only path; its maximum claim is bounded to the
      validated documentation implementation.
- [ ] Mixed or ambiguous candidates do not silently use the fast path. They return a clear
      gate or resume through the standard `execute-ticket` path without reusing docs-only
      evidence as a pass.
- [ ] Commit, guarded push, PR-body validation/readback, manual-versus-autonomous merge
      authority, and exact-head integration rules remain unchanged.
- [ ] `status` and the final report identify docs-only eligibility, the adopted candidate,
      checks performed, why a candidate was rejected, and the number of leaf interactions
      avoided.
- [ ] Regression coverage proves a valid docs-only delivery, a non-doc path rejection, a
      symlink/path-escape rejection, candidate drift rejection, interruption/resume, and
      idempotent replay without invoking `execute-ticket`.

## Frontier

Ready. The user has explicitly accepted that a documentation-only candidate does not need
the full `execute-ticket` loop; implementation must preserve the fail-closed scope and
delivery boundaries above.

## Step-by-Step Implementation Plan

1. Define the versioned docs-only adoption request and persisted ledger receipt without
   weakening Ticket Envelope v1 parsing or guessing intent from Markdown prose.
2. Resolve and freeze the complete Git diff, validate every path and file kind against the
   narrow documentation policy, and bind the result to a CandidateRef.
3. Add a deterministic documentation-validation pipeline that emits structured,
   content-addressed check evidence without leaf-model calls.
4. Add runner transitions that bypass `execute-ticket` only after adoption and validation,
   while preserving candidate invalidation and quality-failure semantics.
5. Feed the bounded documentation evidence into verification with an implementation-only
   claim ceiling and explicit runtime limitations.
6. Reuse the existing idempotent delivery and exact-head merge critical path unchanged.
7. Expose eligibility, progress, rejection causes, and avoided interactions in `status`,
   final reports, public skill guidance, and forward-test scenarios.

## Testing Plan

- Unit tests for adoption schema validation, path/file-kind policy, CandidateRef binding,
  drift detection, ledger replay, status projection, and claim reduction.
- Local Git integration tests for valid `docs/**` Markdown, ticket completion moves,
  unstaged changes, mixed code/docs diffs, symlinks, path traversal, interruption, and
  idempotent resume.
- Spy/fake executor tests asserting `execute-ticket` and leaf-model adapters are never
  called on the eligible path and are not bypassed for ineligible candidates.
- Documentation artifact audit, link validation, relevant regression suites, and the
  ticket-autopilot forward-test corpus.
- Provider tests remain simulated unless live credentials and explicit mutation authority
  are separately available; simulation does not authorize merge.

## Out of Scope

- Skipping checks merely because a ticket describes itself as documentation-only.
- Treating `SKILL.md`, agent instructions, manifests, configuration, or generated files as
  passive documentation.
- Weakening CandidateRef invalidation, evidence classification, provider readback, or
  exact-SHA merge authorization.
- Auto-merging or inferring human approval.
- Reusing docs-only evidence after any candidate or ticket-contract change.

```
