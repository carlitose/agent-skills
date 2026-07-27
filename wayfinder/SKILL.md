---
name: "wayfinder"
description: "Maintain a persistent map and investigation frontier for huge or vague work, using canonical normalized tickets and opt-in compatibility."
---

# Wayfinder

Owns: investigation map, durable frontier, and uncertainty routing. It plans by default;
it does not execute the destination or define another ticket format.

All emitted or consumed ticket metadata uses the canonical
[Ticket Envelope v1](../ticket-autopilot/references/ticket-envelope-v1.md). Delegate
serialization to `to-tickets` or the shared CLI.

## Defaults

- Maps live at `docs/specs/<slug>.md` or `docs/specs/<slug>-wayfinder.md`.
- Tickets live at `docs/tickets/<spec-slug>/`.
- Backward compatibility is opt-in. Still flag destructive migrations, breaking external
  contracts, and irreversible changes.
- Ask one concise question only when the destination itself is ambiguous; otherwise state
  assumptions.

## Process

1. Reconstruct only enough context to identify destination, decisions, unknowns,
   exclusions, and the next blocking edges.
2. Create or update the map:

```markdown
# <Title>

## Type
Wayfinding spec

## Status
Active

## Destination
Reachable target outcome.

## Decisions So Far
- Decision, evidence, and durable record.

## Not Yet Specified
- Unknown that blocks reliable execution.

## Out of Scope
- Explicit exclusion.

## Frontier / Blocking Edges
- Edge, why it blocks, unblock condition, and owning ticket.

## Ticket Plan
- ID, type, mode, blockers, title, expected output.

## Next Review
- What the next agent or human inspects.
```

3. Record durable architecture/product/diagnostic decisions through `to-spec`, then link
   them from the map.
4. Create narrow `research`, `prototype`, `grilling`, or `task` tickets through
   `to-tickets`. Each must name its question/outcome, evidence, frontier, work plan, and
   exclusions.
5. Parse existing tickets with the shared `ticket-parse` command before using their mode,
   blockers, or ID. Do not infer those fields from headings such as `Blocked By`.
6. Stop at the map unless the user explicitly requests execution. Route one ready ticket
   to `execute-ticket` or a folder to `ticket-autopilot`.

## Maintenance

- Fold completed-ticket evidence and decisions back into the map.
- Remove resolved unknowns instead of leaving stale questions.
- Keep the frontier to the next few material edges.
- Prefer another investigation ticket over guessing.
- Report map path, ticket folder, ready/blocked frontier, and recommended next step.
