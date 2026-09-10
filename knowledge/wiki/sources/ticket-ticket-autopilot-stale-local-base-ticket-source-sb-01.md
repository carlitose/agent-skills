---
type: source
title: "Resolve a fast-forward upstream before ticket-source classification"
identity_key: ticket:ticket-autopilot-stale-local-base-ticket-source/SB-01
identity_strength: stable
source_path: docs/tickets/ticket-autopilot-stale-local-base-ticket-source/done/01-resolve-fast-forward-upstream-base.md
source_digest: sha256:25eb8abd5aba56e0053b5b6da29b6954dfa253685656b40213c7ee99d2b09610
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-29
created_provenance: git-commit
disposition_changed: 2026-08-29
disposition_changed_provenance: git-rename
run_id: 43a6a5280ff64630
---

# Resolve a fast-forward upstream before ticket-source classification

Compiled from `docs/tickets/ticket-autopilot-stale-local-base-ticket-source/done/01-resolve-fast-forward-upstream-base.md`. Identity is `ticket:ticket-autopilot-stale-local-base-ticket-source/SB-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-29** via `git-commit`
- Disposition changed: **2026-08-29** via `git-rename`

## Graph

- Parent source: [[sources/artifact-ticket-autopilot-stale-local-base-ticket-source-diagnostic]]

## Run

Completed under autopilot run `43a6a5280ff64630`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-ticket-autopilot-stale-local-base-ticket-source-sb-01.md","payload_bytes":3203,"payload_sha256":"25eb8abd5aba56e0053b5b6da29b6954dfa253685656b40213c7ee99d2b09610"}],"payload_bytes":3203,"payload_sha256":"25eb8abd5aba56e0053b5b6da29b6954dfa253685656b40213c7ee99d2b09610","schema":1,"source_digest":"sha256:25eb8abd5aba56e0053b5b6da29b6954dfa253685656b40213c7ee99d2b09610","source_identity":"ticket:ticket-autopilot-stale-local-base-ticket-source/SB-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3203,"payload_sha256":"25eb8abd5aba56e0053b5b6da29b6954dfa253685656b40213c7ee99d2b09610","schema":1,"source_digest":"sha256:25eb8abd5aba56e0053b5b6da29b6954dfa253685656b40213c7ee99d2b09610","source_identity":"ticket:ticket-autopilot-stale-local-base-ticket-source/SB-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "SB-01"
execution_mode: AFK
blocked_by: []
---

# Resolve a fast-forward upstream before ticket-source classification

## Artifact Graph

- Artifact ID: `artifact:sb-01-resolve-fast-forward-upstream-base`
- Role: `ticket`
- Parent: [stale local base ticket-source diagnostic](../../specs/ticket-autopilot-stale-local-base-ticket-source-diagnostic.md)

## Parent Spec

[Ticket-autopilot stale local base ticket-source diagnostic](../../specs/ticket-autopilot-stale-local-base-ticket-source-diagnostic.md)

## What to Build

Make `ticket-autopilot plan` and `run` resolve an already-fetched, fast-forward upstream of a
selected local base branch before ticket-source classification and worktree creation. Keep
the user's local branch and checkout untouched.

## Acceptance Criteria

- [ ] When a selected local base branch has a configured upstream that is a strict
      fast-forward descendant, tracked and ignored ticket sources are classified and
      snapshotted against the upstream commit.
- [ ] `selected_base_sha` records that resolved upstream SHA and `run` creates its isolated
      worktree from the same commit.
- [ ] The resolver performs no fetch, provider mutation, local-branch update, checkout
      mutation, or implicit merge.
- [ ] Equal refs and a local branch ahead of its upstream retain the explicit local commit;
      divergent histories fail closed with an actionable base-divergence error.
- [ ] Full commit SHAs and explicitly remote-tracking refs preserve literal behavior.
- [ ] A genuinely untracked, non-ignored ticket source remains rejected.
- [ ] Regression tests reproduce the stale-local/fresh-upstream plan and run paths, assert
      local `main` is unchanged, and cover ahead, equal, divergent, ignored, and literal-ref
      controls.
- [ ] Ticket-source, CLI, Git-boundary, context-boundary, and full ticket-autopilot suites
      pass.

## Frontier

Ready. The exact fail/pass reproduction, ancestry proof, responsible classifier, and
non-mutating resolution policy are pinned in the diagnostic.

## Step-by-Step Implementation Plan

1. Add failing ticket-source and CLI fixtures for a stale local branch whose configured
   upstream contains the ticket folder.
2. Implement a pure local-ref resolver that distinguishes fast-forward, equal, ahead,
   divergent, and literal-ref cases.
3. Feed the resolved SHA through existing classification, manifest persistence, and isolated
   worktree creation without adding a network or checkout side effect.
4. Add controls for ignored and genuinely untracked tickets, then run causal and full suites.

## Testing Plan

Use TDD around `test_ticket_sources.py`, then run CLI source-mode tests, Git boundary tests,
the context-passing/model-invocation contract modules, and the complete
`ticket-autopilot/tests` suite. Record the selected SHA, local branch SHA before/after, and
the exact untracked/divergence diagnostics.

## Out of Scope

- Fetching or polling a remote during `plan`.
- Advancing, resetting, merging, or checking out the user's local base branch.
- Weakening the tracked-or-ignored ticket-source invariant.
- Changing reconciliation or post-merge local-branch policy.

```
