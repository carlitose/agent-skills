# Canonical artifact graph decision

## Status

Accepted on 2026-08-08. Authority: explicit user decisions for ticket `OI-05`.

## Type

Decision spec

## Artifact Graph

- Artifact ID: `artifact:artifact-graph-decision`
- Role: `spec`
- Parent: [Open GitHub Issues Remediation](./open-github-issues-wayfinder.md)

## Source

- [Open GitHub Issues Remediation](./open-github-issues-wayfinder.md)
- GitHub issue [#30](https://github.com/carlitose/agent-skills/issues/30)
- Ticket `OI-05`, "Define artifact roots and canonical relationships"

## Context

Tickets use normalized envelopes plus heterogeneous Markdown relationship sections. Specs
and research documents use inconsistent source links, accepted decisions may intentionally
stand alone, and paths or slugs are not stable identities. A scanner cannot distinguish an
intentional root from a missing relationship without an explicit contract.

This decision defines that contract for Wayfinder maps, specs, canonical tickets, and
research results. `OI-06` owns any scanner, CLI, migration helper, or test implementation.

## Decision

Every new, modified, or explicitly migrated managed artifact declares one visible
`## Artifact Graph` section. Only relationships inside that section are canonical graph
edges; links elsewhere remain useful prose but do not establish identity or ownership.

### Identity and role

Every strict artifact declares:

- `Artifact ID`: one explicit, repository-unique, stable identifier;
- `Role`: exactly one of `wayfinder | spec | ticket | research`;
- exactly one root/ownership choice: `Standalone: true` or one `Parent` link.

An Artifact ID is an opaque identity chosen at creation or explicit migration. Moving or
renaming a file does not change it. The audit never derives, repairs, or equates an ID,
parent, or role from a path, title, filename, or slug.

`Role` describes graph behavior. A ticket's product/workflow `Type` such as `Grilling`,
`Prototype`, `Task`, or `Research` remains a separate field and never changes `Role:
ticket`. Every canonical Ticket Envelope source is a ticket artifact, regardless of its
Type or execution mode.

Tickets may not declare `Standalone: true`; every ticket has exactly one Parent. A
Wayfinder map, spec, or research result may be standalone only when that root intent is
explicit. `Standalone: false`, multiple Parent links, or both Standalone and Parent are
invalid for strict artifacts.

### Relationship fields

The graph section may declare these explicit Markdown-link collections:

- `Children`: owned planning or decomposition children;
- `Produces`: outputs created by a ticket;
- `Related`: non-owning cross-references.

A non-standalone artifact's Parent must point to exactly one artifact. Its parent must point
back through exactly one matching `Children` or `Produces` entry. Conversely, every
`Children` or `Produces` target must point back to that owner as its single Parent.
Duplicating one target across `Children` and `Produces` is invalid.

`Produces` is the output-ownership edge for tickets. A ticket whose Type is `Research`
lists every produced research document, spec, or other managed output in `Produces`; every
listed output declares that exact ticket as Parent. An output cannot use a broad program
spec as Parent while also claiming a research ticket as producer. Non-owning context can
be represented with `Related`.

`Related` is symmetric only when authors explicitly add both links; reciprocity is not
required. Related edges may form cycles and never establish reachability from a root.
Parent, Children, and Produces form one ownership hierarchy and must be acyclic.

### Canonical section examples

Intentional root:

```markdown
## Artifact Graph

- Artifact ID: `artifact:example-wayfinder`
- Role: `wayfinder`
- Standalone: true

### Children

- [Decision](./decision.md)
```

Owned artifact:

```markdown
## Artifact Graph

- Artifact ID: `artifact:example-decision`
- Role: `spec`
- Parent: [Example Wayfinder](./wayfinder.md)
```

Research ticket and result:

```markdown
## Artifact Graph

- Artifact ID: `artifact:research-ticket-01`
- Role: `ticket`
- Parent: [Investigation map](../../specs/investigation.md)

### Produces

- [Observed result](../../research/observed-result.md)
```

The result uses `Role: research` and points back to that ticket in `Parent`.

## Validation and diagnostic policy

For a new or modified managed artifact, the contract is strict. These are errors:

- missing or malformed Artifact Graph section, Artifact ID, closed Role, or root/Parent
  choice;
- a standalone ticket, multiple parents, or both Standalone and Parent;
- a broken canonical link or a target outside configured artifact roots;
- duplicate Artifact IDs, including two paths with identical content;
- a cycle through Parent, Children, or Produces;
- any Parent-to-Children/Produces reciprocity mismatch;
- an incomplete Research ticket Produces list or an output whose Parent does not point
  back to its producing ticket.

`Related` cycles are allowed, but a declared Related link is still canonical and therefore
must resolve to a unique managed Artifact ID.

A legacy managed Markdown file that has not been explicitly migrated produces a warning,
not a fabricated node or error solely because the section is absent. A Markdown file that
is not referenced canonically and is not an explicit standalone artifact is reported as an
`unreferenced` candidate with informational severity. The audit does not infer that the
candidate is an orphan, because it may be legacy, ancillary, or intentionally outside the
managed graph.

Errors, warnings, and informational unreferenced candidates remain separate collections.
Changing severity by guessing a slug match is forbidden.

## Scope and discovery

The initial graph covers:

- canonical tickets discovered by the repository ticket inventory under `docs/tickets/`;
- explicit graph sections under `docs/specs/` and `docs/research/`;
- Wayfinder maps represented by `Role: wayfinder`, normally under `docs/specs/`.

Discovery roots are configuration/input, not identity. Markdown outside these roots is
not silently adopted. Within them, an explicit graph section opts an artifact into strict
validation; known new or modified managed artifacts are also strict even if their section
is absent.

## Migration and compatibility

Existing Markdown remains readable and reportable. It is not auto-migrated and does not
receive an inferred ID, role, root, or parent. Until explicitly migrated, it emits a legacy
warning and may also appear as an informational unreferenced candidate.

Migration is an explicit content change that:

1. assigns a stable Artifact ID and closed Role;
2. chooses Standalone or one Parent;
3. updates the reciprocal Children or Produces link in the same change;
4. validates the complete graph before treating the artifact as migrated.

New and modified artifacts must satisfy the strict contract immediately. There is no
compatibility alias for heterogeneous `Parent Spec`, `Source`, or `Sources` sections; those
may remain prose but do not count as canonical edges. OI-06 must expose legacy state rather
than silently accepting or rewriting it.

## Audit safety

The artifact audit is report-only and non-destructive. It may read, normalize, classify,
and render diagnostics. It may not move, delete, rename, rewrite, auto-link, or assign IDs
to any artifact. A migration helper, if separately authorized by OI-06, must only propose
or apply explicit user-selected edits and is not part of the audit command.

Paths are resolved relative to the declaring artifact, normalized within configured roots,
and checked for symlink or path escape. A malformed or contradictory graph fails closed;
the audit preserves all source files.

## Decision scenarios

| Scenario | Required classification |
| --- | --- |
| Active Wayfinder with explicit Standalone | Valid intentional root |
| Standalone accepted decision spec | Valid root when Role and Artifact ID are explicit |
| Ticket with no Parent | Error, even if its filename resembles a spec |
| Research ticket omits one produced result | Error for incomplete Produces reciprocity |
| Produced research result points to another Parent | Error for reciprocity/ownership mismatch |
| Parent and child links agree | One valid hierarchy edge |
| Related documents link in a cycle | Valid if every link resolves |
| Parent/Children/Produces cycle | Error |
| Two artifacts reuse one Artifact ID | Error |
| Canonical link target is missing | Error |
| Unmigrated legacy spec lacks Artifact Graph | Warning; no inferred identity |
| Unreferenced Markdown has no explicit root | Informational candidate; no mutation |
| New artifact lacks required graph fields | Error under strict validation |

## Rejected alternatives

- Infer relationships from matching filenames, titles, folders, or slugs: rejected because
  renames and common names produce false ownership.
- Treat every unreferenced Markdown file as an orphan error: rejected because legacy and
  ancillary documents require classification.
- Let tickets be standalone: rejected because executable work must retain an owning
  decision, map, spec, or producing ticket.
- Combine Role with ticket Type: rejected because graph role and work method answer
  different questions.
- Allow multiple parents: rejected because it makes ownership, reachability, and migration
  ambiguous; Related carries non-owning context.
- Make Related part of hierarchy cycle checks: rejected because Related is deliberately
  non-owning and may cycle.
- Repair missing reciprocals automatically: rejected because the scanner cannot infer
  which side expresses the intended authority.
- Delete, move, or rename reported candidates: rejected because audit findings are not
  authorization for destructive cleanup.

## Verification plan for OI-06

No scanner behavior is claimed as executed by this decision ticket.

- **Unit:** parse exact fields and closed roles; distinguish ticket Role from Type; validate
  unique IDs, root/Parent exclusivity, reciprocity, and hierarchy cycles.
- **Integration:** scan canonical tickets plus specs/research; cover research Produces,
  legacy warnings, informational candidates, broken links, duplicate IDs, and path escape.
- **Negative safety:** inject slug collisions and prove no relationship is inferred; guard
  filesystem mutations and prove audit does not move, delete, rename, or rewrite files.
- **CLI/system:** versioned JSON keeps errors, warnings, and unreferenced information
  distinct; text output remains deterministic and report-only.
- **Migration:** validate explicit paired Parent/Children or Parent/Produces edits while
  preserving unmigrated files unchanged.

## Implementation boundary

OI-06 may choose parser and report schemas only if they preserve this contract. Adding a
role, permitting standalone tickets, weakening reciprocity, inferring from slugs, changing
severity, or allowing audit mutation requires a new explicit human decision.

## Unresolved questions

None for the artifact root and relationship policy. CLI spelling, JSON field layout, and
migration-tool ergonomics remain bounded OI-06 implementation choices.
