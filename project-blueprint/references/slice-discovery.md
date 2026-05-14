# Slice discovery — detailed heuristics

How to find slices in a codebase without applying architectural theory.

A **slice** is a repeated structural pattern: a group of files that gets created together when a developer adds new work of the same kind. Discovery means finding clusters of similar structures and classifying them.

---

## Detection mechanics

### 1. Walk the tree, capture shapes

Walk directories at depth 2-4, excluding `bin/obj/node_modules/.venv/dist/target/__pycache__/.next`.

For each directory, capture its child filenames (no subdirectories at this level). The list of filenames is the directory's **shape**.

### 2. Cluster directories by shape similarity

Two directories share a shape if their filenames match the same pattern. Normalize by replacing the entity name with `{X}`:

- `<application_layer>/UseCases/CreateInvoice/` → `[I{X}Service.<ext>, {X}Service.<ext>, {X}Request.<ext>, {X}Response.<ext>, {X}Validator.<ext>]`
- `<application_layer>/UseCases/CancelInvoice/` → same normalized shape

Both match → same slice cluster.

The example uses `<ext>` instead of a specific extension because the same shape applies in C#, Java, Kotlin, TypeScript — only the file extension and import syntax change.

### 3. Cluster directories by parallel filenames

Some slices aren't directories but parallel files at the same level:

- `<domain>/<strategies_folder>/EmailNotifier.<ext>`
- `<domain>/<strategies_folder>/SmsNotifier.<ext>`
- `<domain>/<strategies_folder>/PushNotifier.<ext>`

All three match `{X}Notifier.<ext>` in `<domain>/<strategies_folder>/`. Cluster them.

### 4. Apply the N rule

| Count | Treatment |
|---|---|
| N ≥ 2 | **Candidate slice** — proceed to canonical selection and constraint extraction |
| N = 1 | **Singleton candidate** — require human classification (singleton / template / smell) |
| N = 0 | Not a slice. Skip. |

---

## Canonical selection

Once a slice has N ≥ 2 instances, pick the canonical (the one a new developer should copy).

**Priority order** (apply each criterion; pick the first instance that satisfies all higher-priority criteria when comparing):

1. **Full shape exercised** — every file in the slice is non-trivially populated. No empty Response records, no validators with `RuleSet.None`, no stub services.
2. **Has accompanying tests** — sibling test folder/file exists with real test methods.
3. **Recent activity** — last modified within ~6 months (use `git log --format=%ad -1 <path>`).
4. **No findings against it** — doesn't appear in audit history or known anti-pattern lists.
5. **Descriptive name** — name tells a reader what the slice does (`CreateInvoice` ✓ vs `ProcessV2Handler` ✗).
6. **Non-trivial output** — the response/result is moldable, not just an ack.

### Tie-breaking

When two instances tie on all criteria, **don't pick one arbitrarily**. Use a two-tier canonical:

- **Primary**: the simpler complete example. *"Start here for your first slice."*
- **Advanced**: the richer example with more validation, more orchestration, more variants. *"Reference when you need X."*

If you can't decide between two-tier vs single, **ask the user**.

---

## Constraint extraction

For each slice, document what the canonical implies the developer must do. Look for:

| Constraint | Where to look |
|---|---|
| Imports allowed / forbidden | `using` / `import` statements at the top of canonical files |
| Naming convention | Class names, file names, method names in the canonical |
| Framework choice | Which serializer/validator/mapper/HTTP client is used |
| Co-created artifacts | Files that always appear together in commits creating new instances |
| Wire-up location | Where the new instance gets registered (DI container, route table, plugin host) |
| Test pattern | Where and how tests are written for the slice |
| Specific signatures | Method names, return types — anything that's consistently the same |

Frame constraints as **rules a new instance must follow**, not as "what the canonical happens to do". The new dev should be able to read this section and know what to write.

---

## Variant detection

Within a slice, some instances may deviate from the canonical shape. Classify each:

| Type | Signal |
|---|---|
| **Legitimate variant** | Documented in CLAUDE.md / README / ADR, or follows a consistent sub-pattern (e.g., read-only use cases share a response file with siblings) |
| **Advanced shape** | More layered version solving an additional concern (caching, fallback, retries). Often worth marking as "recommended evolution when X" |
| **Frozen variant** | Legacy shape, kept for compatibility but new instances must use the canonical |
| **Accidental divergence** | No documentation, no consistent sub-pattern — looks like the author copied the wrong sibling or hand-rolled |

The first three are **acceptable**. The fourth is the one to flag.

**Important: don't guess between "advanced" and "accidental"**. Ask the user when uncertain.

---

## Singleton vs template vs smell (N=1 cases)

When a structural pattern appears only once, three valid interpretations exist:

### Singleton
A structurally unique role. There's only one composition root. One config loader. One main entry point. These don't replicate by design — if you need a sibling concept, it should implement the same port, not duplicate the shape.

**Examples**: `Program.cs`, `main.py`, `Startup`, `ConfigurationReloader`, `OpenTelemetry source for X`.

### Template
First of its kind. Looks like a slice that just hasn't replicated yet. Often appears when a project is young or when a new pattern is being introduced.

**Examples**: the first hosted service in a project that has none, the first `*Plugin` when more are planned, the first feature folder.

### Smell
Should have been split into multiple cohesive pieces but lives as one big class. The classic god service or god controller.

**Examples**: a 670-line orchestrator doing 7 different responsibilities, a controller with 25 methods spanning 5 different resources.

### How Claude can pre-classify

Some signals are observable:
- A file with one well-named class and ≤ 200 lines → likely singleton or template
- A file with many unrelated methods and high LOC → likely smell
- A file with no tests and recent activity → likely template (still in flux)
- A file matching common single-purpose roles (`Program.cs`, `main.py`, `*Settings.cs`) → almost certainly singleton

But the final call requires human judgment because **intent is invisible to structure alone**. A 200-line class might be a singleton or a template. A 1000-line class might be a smell or a legitimately complex aggregate root.

Always batch-ask:
> *"Found N N=1 cases. Classify each as singleton / template / smell:"*
> *• [path]: ..."*

---

## Cross-cutting things that are NOT slices

Some repeated artifacts are co-created with slices, not slices themselves:

- **Mappers** — usually accompany a slice (response mapper for a use case, persistence mapper for a repository). Document them as *cross-cutting conventions*, not as their own slice.
- **DTOs / Records** — also co-created with slices.
- **Validators** — co-created with use cases or commands.
- **Test fixtures / factories** — accompany the test of the slice they support.

These belong in a "Cross-cutting conventions" section of the blueprint, not under "Slices".

---

## What about the architectural pattern label?

The pattern label (DDD, Hexagonal, Layered, MVC) is a **summary**, not a discovery target. After finding the slices and vocabulary, the pattern label should fall out:

- Vocabulary has Entities + Value Objects + Aggregates + Domain Services + Domain Events → DDD vocabulary
- `domain/` + `application/` + `infrastructure/` with imports pointing inward → Hexagonal layering
- `controllers/` + `services/` + `repositories/` without domain isolation → Layered

Use `references/patterns.md` for the signature cheatsheet.

If the project mixes patterns or doesn't fit cleanly, label it as **"Pragmatic mix"** and describe what it actually is. Forcing a single label hides reality.

---

## Output: slice catalog section format

Each slice in the BLUEPRINT.md follows this structure:

```markdown
### Slice N — <Name>

- **Detected from**: <shape definition>
- **Instances** (N=X): <list with dimension tags>
- **Canonical reference**: <path> — <justification>
  - *Or, for two-tier*: **Primary**: <path>. **Advanced**: <path>.
- **Co-created files**: <DI registration, test mirror, controller endpoint, etc.>
- **Constraints**: <imports, naming, framework, signatures the new dev must follow>
- **Variants** (if any): <how they deviate and whether it's legitimate>
- **Status**: active | frozen | deprecated | candidate
```

The point of this format is that a developer can read just one slice section and know: where to put their new file, what to name it, what shape it must follow, what to import, where to register it, and which sibling to use as reference.
