---
ticket_schema: 1
ticket_id: "WS-01"
execution_mode: AFK
blocked_by: []
---

# Map the existing wiki sync and docs-only boundary

## Artifact Graph
- Artifact ID: `artifact:ws-01-map-current-sync-boundary`
- Role: `ticket`
- Parent: [llm-wiki-docs-only-autosync-wayfinder.md](../../specs/llm-wiki-docs-only-autosync-wayfinder.md)

## Parent Spec
[llm-wiki-docs-only-autosync-wayfinder.md](../../specs/llm-wiki-docs-only-autosync-wayfinder.md)

## Produces
- `docs/research/llm-wiki-docs-only-autosync-contract.md`, which must point back to this ticket.

## What to Build
An evidence-backed research report that maps the current `llm-wiki`, `docs-only-adopt`,
`to-tickets`, and `ticket-autopilot` boundaries. It must distinguish an absent wiki, a bound
untracked wiki, a bound tracked wiki, and broken or ambiguous discovery without proposing
implementation as observed behavior.

## Acceptance Criteria
- [ ] The report identifies the current public commands, call sites, versioned contracts,
      and exact files that own discovery, project binding, docs-only path policy, candidate
      identity, integration state, and wiki validation.
- [ ] It proves whether project-to-wiki discovery exists and defines what evidence can
      classify generated wiki content as tracked, untracked, partial, or external.
- [ ] It traces both requested triggers: once after a complete `to-tickets` batch and once
      after durable `integrated` state in `ticket-autopilot`.
- [ ] It identifies every current invariant that a docs-only wiki profile must preserve,
      including mixed-candidate rejection and claim ceiling.
- [ ] Facts, inferences, unknowns, and recommended experiments are separated.

## Frontier
Ready. Its report is the evidence input for `WS-02`.

## Step-by-Step Implementation Plan
1. Inspect the binding, ingest, timeline, lint, docs-only contract, runner state, and caller
   code. Checkpoint: every claimed owner has a source path.
2. Model the state matrix and candidate identities. Checkpoint: absent, untracked, tracked,
   partial, external, multiple, and broken cases are accounted for.
3. Write the report with an Artifact Graph pointing to this ticket and update this ticket's
   `Produces` entry to a reciprocal Markdown link in the same change.

## Testing Plan
Run read-only CLI help, dry-run, and repository searches where useful. Verify every local
link and run the canonical artifact audit against the completed report/ticket graph.

## Out of Scope
- Implementing sync, changing docs-only policy, or mutating a real wiki.
- Choosing the unresolved HITL policy owned by `WS-03`.
