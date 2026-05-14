# BLUEPRINT — <project name>

Discovery date: <YYYY-MM-DD>. Root: <relative path>.

## Stack

- Language and runtime version
- Framework(s) and key libraries (with versions if visible in manifest)
- Persistence (DB, cache)
- AI / ML libraries if any
- Testing libraries
- ⚠️ Note any migration in flight (e.g., "on Skeleton 8.x but adopting v9 conventions in new code")

## Layers (from manifest)

```
<dependency diagram from csproj / package.json / go.mod references>
```

| Project / module | Role |
|---|---|
| `<path>` | <one-line description> |

## Vocabulary instantiated

| Building block | Present? | Notes |
|---|---|---|
| Entity / Aggregate | ✅ / ❌ | <count, examples> |
| Value object | ✅ / ❌ / ⚠️ partial | <notes> |
| Repository | ✅ / ❌ | <count> |
| Domain service | ✅ / ❌ | <examples> |
| Application service / Use case | ✅ / ❌ | <count and styles> |
| Domain event | ✅ / ❌ | <count or "not visible"> |
| Driver adapter | ✅ / ❌ | <kinds — HTTP, CLI, WS, queue> |
| Driven adapter | ✅ / ❌ | <kinds — DB, HTTP clients, etc.> |
| Port (interface) in Domain | ✅ / ❌ | <count, note asymmetries> |
| Options / Config class | ✅ / ❌ | <approach> |

## Dimensions

<If the project has internal verticals (channel-based, tenant-based, module-based), describe them here>

| Vertical | Marker patterns | Runtime model |
|---|---|---|
| <name> | <folders/namespaces that identify it> | <one-line runtime description> |
| **channel-agnostic** | <folders that serve all verticals> | Shared |

<If no dimensions: "None — single concern.">

## Slices

### Slice 1 — <Name>

- **Detected from**: <shape — regex/description of files that define membership>
- **Instances** (N=X): <list with dimension tags, e.g., "(text)", "(voice)", "(channel-agnostic)">
  - `<path1>` — <dimension>
  - `<path2>` — <dimension>
- **Canonical reference**: 
  - **Primary (start here)**: `<path>` — <LOC, last modified date, why this one>
  - **Advanced (richer example)**: `<path>` — <when to use this instead>
  - *(For single-canonical slices, just one bullet)*
- **Co-created files**: <DI registration line, test mirror folder, controller endpoint, options class, etc.>
- **Constraints**: 
  - <Imports allowed / forbidden>
  - <Naming convention>
  - <Framework / serializer / mapper choices>
  - <Signature requirements>
- **Variants** (if any):
  - <description of how some instances deviate and whether it's legitimate>
- **Status**: active | frozen | deprecated | candidate

### Slice 2 — <Name>

<same structure>

<repeat for all slices found>

## Singletons (not slices)

These are N=1 by design. Do not copy their shape to create new "slices". If a sibling concept emerges, it should implement the same **port**, not duplicate the structure.

| Item | Path | Role | Notes |
|---|---|---|---|
| <name> | `<path>` | <one-line role> | <special notes, anti-pattern flags, target shapes> |

## Cross-cutting conventions

### Mappers (if not a slice)

<table of boundary → location → example, with rules>

### Serialization

- HTTP: <JSON library and casing>
- Persistence: <BSON, ORM, etc.>

### Validation

- <framework and registration mechanism>
- <error code conventions if any>

### Error model

- <envelope shape>
- <code format>

### Logging / tracing

- <library and conventions>

### Dependency direction

- <confirmed from manifest graph; note any leaks>

## Variants and known asymmetries

Document architectural decisions that look weird but are intentional. A reader needs to know "this is weird but on purpose" so they don't try to fix it.

- <observation 1>
- <observation 2>

## Open questions

Things the discovery couldn't resolve. Often pointers to areas where the team's intent isn't yet codified.

- <question 1>
- <question 2>
