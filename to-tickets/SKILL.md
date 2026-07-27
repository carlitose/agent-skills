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
body, unique ID, and dependency links. Do not modify the parent spec unless requested.

## Report

Return the ticket folder, paths, ready frontier, blocked tickets, and any HITL decisions.
