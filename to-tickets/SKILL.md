---
name: "to-tickets"
description: "Break a spec into independently-grabbable tracer-bullet tickets and emit each versioned Ticket Envelope through the canonical ticket contract."
---

# To Tickets

Owns: Ticket Envelope production and executable tracer-bullet slicing. It does not
schedule, implement, audit, or preserve a separate Markdown schema.

Use [Ticket Envelope v1](../ticket-autopilot/references/ticket-envelope-v1.md) and
`"$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" ticket-emit` from the absolute ticket-autopilot
skill root resolved from the catalog, never repository cwd. Never hand-serialize front matter;
legacy input requires the explicit `migrate` command.

For explicit skills-only or runner-suspended work, use the same contract's pure serializer
and parser, not the runner CLI: follow the [skills-only contract](../execute-ticket/references/skills-only.md).
This is no alternate schema or hand-serialization. Preserve atomic writes and exact readback validation.

## Process

1. Locate and read the spec. Inspect the codebase only enough to understand ownership,
   conventions, tests, and vertical behavior boundaries.
2. Split work into thin end-to-end slices. Each ticket must be independently verifiable;
   avoid horizontal schema/API/UI/test-only batches.
3. Classify each slice as `AFK` or `HITL`. Make dependencies explicit and acyclic. Prefer
   AFK, but do not hide real decisions, credentials, or environment gates.
4. Present ticket title, mode, blockers, frontier state, and covered spec sections. In an
   explicitly autonomous request, record reasonable assumptions and continue.
5. Create `docs/tickets/<spec-slug>/<NN>-<ticket-slug>.md` in deterministic dependency
   order.

Every body includes one `## Artifact Graph` section with a stable Artifact ID,
`Role: ticket`, and one `Parent` link. Tickets are never standalone. Update the owning
spec or map with the reciprocal `Children` link in the same change. A research ticket
lists each durable output in `Produces`; every output points back to that ticket.

For each ticket, prepare an envelope JSON:

```json
{
  "ticket_schema": 1,
  "ticket_id": "NN",
  "execution_mode": "AFK",
  "blocked_by": []
}
```

Prepare a Markdown body:

```markdown
# <Ticket title>

## Artifact Graph
- Artifact ID: `artifact:<stable-id>`
- Role: `ticket`
- Parent: [<spec-filename>](../../specs/<spec-filename>)

## Parent Spec
[<spec-filename>](../../specs/<spec-filename>)

## What to Build
Narrow end-to-end behavior and the source spec sections.

## Acceptance Criteria
- [ ] Observable criterion.

## Frontier
Ready, dependency-blocked, or exact human decision required.

## Step-by-Step Implementation Plan
1. Change, reason, affected contract/module, and checkpoint.

## Testing Plan
Automated and manual checks, including unavailable boundaries.

## Out of Scope
- Explicit exclusion.
```

In the Autopilot lane, emit atomically through the CLI (skills-only uses the pure
serializer and atomic persistence described above):

```bash
python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  ticket-emit <envelope.json> <body.md> --output <ticket.md>
```

Read the emitted ticket back with the canonical parser (`ticket-parse` in the Autopilot lane,
`parse_ticket_markdown` in skills-only) and verify exact normalized envelope, body, unique
ID, dependency links, and reciprocal graph edge.

In skills-only, stop at the validated batch handoff; never invoke `finalize_batch.py` or
start wiki/provider work implicitly. Report wiki synchronization as deferred unless separately
requested and authorized through `llm-wiki`; require evidence for success/no-op. Ticket validation is unchanged.

In the Autopilot lane, after every ticket in the batch has been emitted and those checks
pass, invoke the owned post-batch boundary exactly once, never once per ticket:

```bash
python3 -B "$TO_TICKETS_ROOT/scripts/finalize_batch.py" \
  <project-root> <ticket-folder> <ticket-path>...
```

`$TO_TICKETS_ROOT` is the absolute skill root from the catalog. Pass configured wikis as
`--wiki-root <path>`; otherwise use `wiki-sync-v1` bounded discovery. Preserve the complete
`ticket-batch-finalize-v1` report: absent wiki is a successful no-op; failures never hide emitted tickets.
Keep a returned tracked-wiki candidate separate and docs-only; never add wiki files to the
ticket-source candidate. `wayfinder` does not own or call this hook.

## Report

Return the ticket folder, paths, ready frontier, blocked tickets, any HITL decisions, and the
normalized `wiki_sync` result from the post-batch report, or the explicit deferred wiki
synchronization state for skills-only.
