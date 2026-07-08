# Slice comparison — how to check a diff against a blueprint

The blueprint declares slices with shapes, canonical references, constraints, and statuses. The review compares the diff against those declarations.

This file walks through how that comparison works in practice.

---

## Locating which slice a changed file belongs to

For each file in the diff:

### 1. Match the file's path against slice shapes

The blueprint declares each slice with a "Detected from" pattern. Match the file path against those patterns.

Examples — the principle is the same regardless of language:

- A file at `<app_layer>/<UseCaseName>/<UseCaseName>Service.<ext>` matches a slice declared as *"folder containing `{X}Service.<ext>` and siblings"*
- A file at `<infrastructure>/<Vendor>/<Vendor>Options.<ext>` matches a slice declared as *"`{X}Options.<ext>` inside `<infrastructure>/{X}/`"*
- A file at `<domain>/<Strategies>/{X}Strategy.<ext>` matches a slice declared as *"any `{X}Strategy.<ext>` in `<domain>/<Strategies>/`"*

The matching logic is: take the slice's regex from the blueprint, substitute `{X}` with the actual filename token, check if the path matches.

### 2. If the file is new and the path matches no existing slice

Three possibilities:

- The file is a new instance of an existing slice → check shape and constraints
- The file is part of a new slice (the first instance) → ⏸ ask the user
- The file is a one-off (singleton) → ⏸ ask the user

### 3. If the file is modified

Same slice as before (the change doesn't move it). Apply constraints to the modified lines.

### 4. If the file is deleted

Note deletion. Check whether it's the canonical of its slice — if yes, the slice loses its reference and someone needs to pick a new canonical.

---

## Applying constraints

For each file mapped to a slice, walk the slice's declared constraints and check the file against each.

Constraints come from the blueprint, not from theory. A blueprint might declare for an application-service slice:
- *"Service constructor receives only ports (interfaces from the domain layer) — no concrete adapter types"*
- *"Library X is forbidden globally"*
- *"Error codes must match the project's prefix convention (e.g., `XYZ\d{4}`)"*

For each constraint, formulate a check appropriate to the language. The principle is the same; the grep changes.

| Constraint kind | Approach |
|---|---|
| Forbidden import / library | Grep the diff's `+` lines for the forbidden symbol; respect the project's import syntax (`using`, `import`, `require`, `use`) |
| Required co-created file | Check `git diff --name-only` for the expected sibling path |
| Naming convention | Compare the new symbol against the slice's canonical naming regex |
| Error code prefix | Grep new error-emitting lines for the prefix |

Constraint violation in added lines = **finding** scoped to the slice.

---

## Checking slice status

The blueprint marks each slice's status. The review uses this directly:

| Status | New instance added | Existing instance modified |
|---|---|---|
| `active` | ✅ normal comparison | ✅ normal comparison |
| `frozen` | ❌ blocker / should-fix — new instances should use the active replacement | ✅ allowed (touching existing legacy is fine) |
| `deprecated` | ❌ blocker — slice being removed | ⚠️ should-fix — modifications should migrate, not entrench |
| `candidate` | ⚠️ flag for discussion — slice not yet promoted to active | normal |

Example: if a slice is marked `frozen` (e.g., a legacy CQRS path the project has stopped extending), a new file with the frozen shape is a regression — the active replacement slice should be used instead.

---

## Variant detection

If the new file matches the slice shape but deviates in some aspect (different framework, different naming, missing co-created file), check whether it matches a **declared variant** in the blueprint.

- Matches a declared variant → fine, mention in review for context
- Matches no declared variant → new variant introduced by this PR. **⏸ Ask**:
  - *"This PR introduces a new variant of slice X (deviation: [description]). Is this deliberate (needs a decision spec) or accidental (should match canonical)?"*

A common pattern: a project has 3 instances of an outbound integration slice using framework A. A new instance arrives using framework B. Two valid interpretations:
- The new instance is the **advanced variant** — solves an additional concern (caching, fallback, retries) that the simpler shape can't. Should be documented in the blueprint as "recommended evolution when X".
- The new instance is **accidental divergence** — author copied the wrong sibling or hand-rolled without considering existing convention.

The skill cannot tell these apart from structure alone. **⏸ Always ask** when a new variant is detected.

---

## Co-created files check

For each new slice instance, the blueprint lists what should be co-created:
- DI registration
- Test mirror
- Controller endpoint
- Options class
- Migration

Check the diff for each. Missing co-created files = finding.

Example for a new use-case slice instance: if the blueprint declares it ships with a test mirror + DI registration + controller endpoint, then a diff adding only the service file is incomplete.

```bash
# 1. Was a sibling test file added?
git diff <base>...HEAD --name-only | grep -E 'test|spec' | grep '<UseCaseName>'

# 2. Was DI wiring touched?
git diff <base>...HEAD --name-only | grep -iE 'dependencyinjection|startup|module|registry|main\.(py|go|ts|rs)'

# 3. Was the controller/route endpoint added?
git diff <base>...HEAD --name-only | grep -iE 'controller|router|routes|handler\.(py|ts|js|go|rs)'
```

Adjust the regex to your project's naming. The principle holds: every slice declares its co-created artifacts; missing any in the diff is a finding.

If any are missing in the diff, **⏸ ask** if they live in another PR/branch, or are genuinely missed.

---

## Cross-slice considerations

Some changes affect multiple slices at once. Examples:

- A new request handler that also adds a new business logic unit → check both the entry-point slice and the logic slice
- A new persistence record that also adds a new domain entity → check both the persistence slice and the domain rules
- A new external integration that adds config + adapter + port → check the integration slice + the port placement (which layer owns the interface, per the project's pattern)

When a change spans slices, structure the findings by slice in the output — not by file. The reader sees the architectural impact, not just a file list.

---

## When the blueprint is silent

If a slice constraint isn't declared, **don't invent it**. Don't enforce "should be like the rest" without basis. Either:

1. The constraint is genuinely declared and the file violates it → finding
2. The constraint is implicit (matches all other instances but isn't documented) → ⏸ ask the user whether to enforce it (and add to blueprint if so)
3. The constraint isn't there → no finding

The blueprint should grow as deviations get classified. A PR review that discovers an undocumented convention is a signal to update the blueprint, not just to fail the PR.

---

## Output of slice comparison

For each finding produced by slice comparison:

```markdown
**`<path>:<line>`** — [blocker | should-fix | nit] · `arch`

Slice: <slice name from blueprint>
Constraint violated: <which declared constraint>

> ```language
> <offending line from diff>
> ```

**Direction**: <one or two sentences referencing the slice's canonical or its constraints>
```

The reader sees not just "this is wrong" but "this is wrong **with respect to the slice** the file belongs to". The slice anchor makes the finding teachable.
