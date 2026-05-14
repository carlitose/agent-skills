# SYSTEM_MAP — <repo name>

Discovery date: <YYYY-MM-DD>.

## Projects

| Project | Type | Role | Blueprint |
|---|---|---|---|
| **<name>** | <language + framework> | <one-line role> | [`docs/architecture/<project>/BLUEPRINT.md`](<project>/BLUEPRINT.md) |

## Cross-project calls

<ASCII diagram or mermaid showing who calls whom>

```
<diagram>
```

### Detail

| Caller | Callee | Protocol | Contract | Notes |
|---|---|---|---|---|
| <project> | <project / external> | <HTTP / queue / DB / SDK> | <where the contract lives> | <special considerations> |

## Cross-language boundaries

For each boundary where one project's language differs from another (e.g., .NET ↔ Python):

### N. <From> → <To>
- **Form**: <REST, queue, shared DB, etc.>
- **Contract authority**: <which side owns the schema>
- **Rule for this boundary**: <how changes should be coordinated>
- **Mitigations in place**: <what protects against silent breakage>

## Same-language boundaries

<List or "None" — projects within the repo that share a language but call each other separately>

## External shared dependencies

| Dependency | Used by | Form |
|---|---|---|
| <name> | <projects> | <how it's used> |

## Conscious decisions

Architectural choices that look like anti-patterns but are intentional. Documented here so they're not flagged on every audit.

- <decision and its trade-off>

## Open questions

- <unresolved aspects of the system map>
