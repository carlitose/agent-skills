---
name: pr-antipattern-review
description: Review a diff (pull request, commit, or local changes) by comparing it against the project's BLUEPRINT.md slice catalog. Auto-detects the input format (git diff, GitHub/GitLab PR URL or number, commit SHA, pasted diff). Loads the blueprint for each project the diff touches and classifies findings as deviations from declared slices, universal anti-patterns, or improvements. Human-in-the-loop on ambiguity (slice classification, severity, ambiguous deviations). Output is ephemeral — emitted to chat or saved on request, never auto-committed. Use whenever the user asks "review this PR", "check my changes", "any anti-patterns in this commit", "is this safe to merge", "look at PR #N", "review my diff", pastes a diff, mentions a commit SHA, or wants a pre-merge sanity check on their code changes.
---

# PR Anti-pattern Review

Review a diff by comparing it against the project's slice catalog. Find deviations from declared slices and universal anti-patterns. Output a review with `path:line` references suitable for pasting as PR comments.

This skill is **comparative**, not encyclopedic. It compares the diff against `BLUEPRINT.md` rather than running a generic checklist.

**Output is ephemeral by default.** Findings go to chat. Save to a file only if the user asks.

---

## Core principles

1. **Blueprint is the rulebook**. If the project has a `BLUEPRINT.md`, that determines what's right vs wrong. Findings without a blueprint anchor are weaker (suggestions, not violations).
2. **Slices are the unit of comparison**. The question isn't "does this PR violate generic principles" but "does this PR follow the slice it's working in".
3. **Human-in-the-loop on judgment calls**. Don't decide severity in ambiguous cases. Don't classify deviations as deliberate vs accidental — ask.
4. **Boy scout rule**. Pre-existing problems in touched files are not held against the PR unless it makes them worse.
5. **Output is ephemeral**. Findings emitted to chat. Never auto-write a file. Never auto-commit.

---

## Workflow

### Step 1 — Detect the input format

Route based on what the user provided:

| Input | Action |
|---|---|
| URL `github.com/<owner>/<repo>/pull/<N>` | `gh pr diff <URL>` — fallback: fetch `<URL>.diff` with the available browser/web tool or `curl -L` |
| URL `gitlab.com/.../merge_requests/<N>` | `glab mr diff <N>` — fallback: fetch `<URL>.diff` with the available browser/web tool or `curl -L` |
| `PR #<N>` or just `<N>` | `gh pr diff <N>` in the current repo |
| 40-char hex / "commit <X>" | `git show <sha>` |
| Diff text starting with `diff --git` | use as-is |
| Nothing specific | `git diff <base>...HEAD` where `<base>` is the default branch; fallback `git diff HEAD~1` |

If ambiguous, check `git status` and `git log -1` first.

### Step 2 — Identify which project(s) the diff touches

For each file in the diff:
- Match its path against the projects in the repo
- Group changes by project

**⏸ Stop-and-ask checkpoint 1** (only if diff spans multiple projects):
> *"This diff touches projects A and B. Review both, only A, only B, or treat as a single cross-project change?"*

If diff stays within one project: no checkpoint, proceed.

### Step 3 — Load the blueprint(s)

For each touched project, look for `BLUEPRINT.md` at:
- `docs/architecture/<project>/BLUEPRINT.md` (monorepo convention)
- `docs/architecture/BLUEPRINT.md` (single-project convention)
- `docs/BLUEPRINT.md`

If a monorepo has `docs/architecture/SYSTEM_MAP.md`, load it too — needed when the diff includes cross-project boundary changes.

**If no blueprint found**:
- Tell the user: *"No BLUEPRINT.md found for project X. Running with universal checks only — findings are weaker and may miss project-specific conventions. Want me to suggest running `project-blueprint` first?"*
- Continue with reduced confidence

### Step 4 — Parse the diff

For each changed file:
- Status: added / modified / deleted / renamed
- Hunks with `+` and `-` lines
- New imports (high signal for layering)
- New file paths (high signal for slice/non-slice)
- Net line change and public API delta

### Step 5 — Classify each change against slices

For each file in the diff:

1. **Locate the slice it belongs to** based on its path and shape
2. If unclear which slice, **⏸ ask**:
   > *"File X doesn't clearly fit slice Y or Z. Which slice does this belong to, or is it a new slice?"*
3. Apply the slice's declared **constraints** against the file's new contents:
   - Imports match what the slice allows?
   - Naming matches the slice convention?
   - Framework/library matches the canonical?
   - Co-created files present (test, DI registration, etc.)?
4. Check **status** of the slice:
   - `frozen` — flag new instances as regression
   - `deprecated` — flag any addition
   - `active` — normal comparison
5. Check for **variants**:
   - Instance matches an existing variant → fine, document
   - Instance is a new variant → ⏸ ask if deliberate (decision spec needed) or accidental

### Step 6 — Apply universal checks

Independent of any blueprint:
- Secrets introduced in committed files
- Manifest-level dependency inversion (a `.csproj` / `package.json` gains a reference that reverses the architectural arrow)
- Security regression (auth removed, validation removed, CORS opened)
- Test removed without explanation
- Catch-and-swallow exception introduced
- Type-checker silencing without justification

See `references/universal-checks.md` for the full list with detection commands.

### Step 7 — Boy scout filter

For each finding, check whether the problem **existed before this PR** in the same file:

- If yes and the PR doesn't worsen it → demote to "pre-existing context" (mention once, don't count against PR)
- If yes and the PR worsens it (e.g., adds the 26th method to a god service) → count against PR

Pre-existing problems that the PR happens to touch but doesn't worsen are not findings.

### Step 8 — Classify severity

| Tier | Justifies verdict |
|---|---|
| **Blocker** | Request changes |
| **Should-fix** | Comment (recommend before merge) |
| **Nit** | LGTM with notes |

When ambiguous between blocker and should-fix, **⏸ ask**:
> *"This finding [description] could be blocker or should-fix depending on context. The PR has [context]. How do you want it classified?"*

Don't decide unilaterally on severity for things that could go either way.

### Step 9 — Compute verdict

| Conditions | Verdict |
|---|---|
| Any **blocker** present | ❌ Request changes |
| 4+ should-fix, or repeated should-fix of the same kind | ⚠️ Comment |
| 1-3 should-fix with viable workarounds, or nits only | ✅ LGTM with notes |
| Nothing flagged | ✅ LGTM |

### Step 10 — Pre-submit summary

Before emitting the final review:

**⏸ Stop-and-ask checkpoint 2** (only when posting, saving, or when severity/classification is ambiguous):
> *"Findings: N blockers, M should-fix, K nits. Verdict: [X]. Confirm or want to adjust any classification before I write the review?"*

This is the last chance to catch a miscall before the output goes out.

### Step 11 — Emit review

Emit the review to chat using `assets/review-template.md`. Findings are formatted with `path:line` so the user can paste them as PR comments.

Then offer:
> *"Want me to save this as a markdown file? Otherwise it stays in chat history."*

Save to file only on explicit yes. Default is chat-only.

---

## Stop-and-ask checkpoints summary

| # | Checkpoint | When |
|---|---|---|
| 1 | Multi-project review scope | Step 2, only if diff spans projects |
| 2 | Slice classification of file | Step 5, only if ambiguous |
| 3 | Variant deliberate vs accidental | Step 5, only if new variant detected |
| 4 | Severity ambiguous | Step 8, only when blocker/should-fix is genuinely contested |
| 5 | Pre-submit confirmation | Step 10, only when posting, saving, or ambiguity remains |

Additional pauses if anything unexpected — never invent decisions.

---

## What the agent observes vs what the human decides

**The agent observes**:
- Which slice a file belongs to (from path + shape)
- Whether the file matches the slice's canonical shape
- Whether imports respect the layer/slice constraints
- Whether tests are present
- Manifest-level dependency changes
- Greppable anti-patterns (secrets, env-var sprinkles, catch-and-swallow)

**Human decides**:
- Whether a new variant is deliberate or accidental
- Severity when contested (security regression intentional? legacy workaround?)
- Whether to count pre-existing problems against this PR
- Whether to save the review as a file

---

## What this skill does NOT do

- Generate the blueprint (use `project-blueprint`)
- Auto-commit anything
- Auto-write files unless the user explicitly asks
- Apply generic anti-pattern catalogs as if they were project rules
- Ignore the blueprint if one exists

---

## When no blueprint exists

Without `BLUEPRINT.md`, the skill falls back to universal checks only:
- Secrets, manifest inversion, security regression, removed tests, type-checker silencing, catch-and-swallow

Output explicitly notes: *"No project blueprint found — review is based on universal checks only. Findings may miss project-specific conventions. Run `project-blueprint` to enable slice-based comparison."*

---

## See also

- `references/slice-comparison.md` — how to check a diff against a slice catalog
- `references/universal-checks.md` — project-independent observations
- `references/diff-checks.md` — greppable patterns useful regardless of project
- `assets/review-template.md` — output format
