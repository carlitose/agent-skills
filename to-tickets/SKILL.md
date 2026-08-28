---
name: "to-tickets"
description: "Break a spec into independently-grabbable tracer-bullet tickets and emit each versioned Ticket Envelope through the canonical scheduler contract."
---

# To Tickets

Owns: Ticket Envelope production and executable tracer-bullet slicing. It does not
schedule, implement, audit, or preserve a separate Markdown schema.

Use the canonical
[Ticket Envelope v1](../ticket-autopilot/references/ticket-envelope-v1.md) and
`"$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" ticket-emit`. The placeholder is
the absolute ticket-autopilot skill root resolved from the skill catalog, never from
repository cwd. Never hand-serialize front matter. Legacy input is accepted only through
the explicit `migrate` command.

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

Emit atomically:

```bash
python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  ticket-emit <envelope.json> <body.md> --output <ticket.md>
```

Parse the emitted ticket back with `ticket-parse` and verify exact normalized envelope,
body, unique ID, dependency links, and reciprocal graph edge.

After every ticket in the batch has been emitted and those checks pass, invoke the owned
post-batch boundary exactly once, never once per ticket:

```bash
python3 -B "$TO_TICKETS_ROOT/scripts/finalize_batch.py" \
  <project-root> <ticket-folder> <ticket-path>...
```

`$TO_TICKETS_ROOT` is the absolute skill root resolved from the skill catalog. Pass each
explicitly configured wiki as `--wiki-root <path>`; otherwise let `wiki-sync-v1` perform its
bounded discovery. Preserve the complete returned `ticket-batch-finalize-v1` report. An
absent wiki is a successful no-op. A sync failure does not erase or hide emitted ticket paths.
If the result contains a tracked-wiki candidate, keep it as a separate docs-only candidate;
never add wiki files to the ticket-source candidate. `wayfinder` does not own or call this
hook.

## Report

Return the ticket folder, paths, ready frontier, blocked tickets, any HITL decisions, and the
normalized `wiki_sync` result from the post-batch report.
