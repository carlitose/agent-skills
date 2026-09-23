# Ticket Envelope v1

`ticket-autopilot/scripts/autopilot/ticket_contract.py` is the single owner of Ticket
Envelope parsing, validation, normalization, serialization, explicit migration, and folder
DAG construction.

## Canonical front matter

Every executable ticket starts on its first line with exactly these fields:

```yaml
---
ticket_schema: 1
ticket_id: "06"
execution_mode: AFK
blocked_by:
  - "04"
  - "05"
---
```

- `ticket_schema` is the integer `1`.
- `ticket_id` is a non-empty token matching `[A-Za-z0-9][A-Za-z0-9._-]*`.
- `execution_mode` normalizes to `AFK` or `HITL`.
- `blocked_by` is an ordered, unique list of ticket IDs. A ticket cannot block itself.
- Unknown or missing fields fail closed.
- The body begins after one blank line following the closing delimiter.

The dependency order is meaningful and is preserved during round-trip serialization.
Folder planning additionally rejects duplicate IDs, missing dependencies, and cycles.

## Public CLI

`TICKET_AUTOPILOT_ROOT` below is the absolute skill root resolved from the skill catalog
or this reference's parent skill, never from repository cwd.

Parse and normalize:

```bash
"$TICKET_AUTOPILOT_PYTHON" -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  ticket-parse <ticket.md>
```

Serialize and atomically write:

```bash
"$TICKET_AUTOPILOT_PYTHON" -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  ticket-emit <envelope.json> <body.md> --output <ticket.md>
```

Normal parse/emit operations never guess legacy fields. Conversion is explicit:

```bash
"$TICKET_AUTOPILOT_PYTHON" -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  migrate <ticket-or-folder> --write
```

### Explicit legacy migration forms

The legacy `## Blocked By` section is fail-closed. An absent or empty section means no
dependencies. The only no-dependency bullets are `- None` and
`- None - can start immediately.`. Otherwise every nonempty line must be one of:

- `- 04`, with the ID optionally enclosed by matching backticks or quotes;
- `- [04-parser.md](./04-parser.md)`, where label and relative target filename match.
- The same link may use the exact repository-proven suffix ` — completed.`. No other
  status or ASCII suffix is accepted.

A numeric filename prefix such as `04-parser.md` migrates to ticket ID `04`. `None` cannot
be combined with another entry. Free text, empty bullets, mismatched links, absolute/remote
links, and any other form are errors. Migration validates every generated candidate
through this canonical contract before returning or writing it. Folder migration
preflights all files. Single-file migration preflights the containing ticket set in memory
but writes only its explicit target. Any invalid candidate leaves every file unchanged.

## Pure contract use (skills-only)

When the runner is suspended, use the existing pure functions in `autopilot.ticket_contract`
instead of its CLI: `normalize_ticket_envelope`, `parse_ticket_markdown`,
`serialize_ticket_markdown`, and `ticket_source_digest`. They do not schedule, mutate a
ledger, or deliver work. The caller owns atomic file persistence and readback, not parsing
or serialization logic. Follow the
[skills-only contract](../../execute-ticket/references/skills-only.md) for candidate and
authority binding. Missing canonical code is a gate; it is not permission to clone it.

## Ownership rules

- `to-tickets` is the producer and uses `ticket-emit` or the same pure serializer in skills-only.
- `ticket-autopilot` parses folders and schedules the resulting DAG.
- `wayfinder` and `execute-ticket` consume normalized envelopes supplied by the caller.
- Downstream verification receives contract-normalized identity and an artifact reference;
  it does not parse Ticket Markdown.
- No other skill defines a front-matter parser, serializer, schema, or fallback.
