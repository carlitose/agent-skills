---
name: codebase-improver
description: End-to-end, self-contained Python/TypeScript workflow that maps and audits a whole repo, then recursively deepens modules. Use to improve or modernize a codebase, reduce technical debt, make this more testable, find refactoring opportunities, deepen shallow modules, consolidate tightly-coupled modules, make codebase AI-navigable, or run a full-repo audit. Worker delegation is optional and human-gated.
---

# Codebase Improver

Take a codebase from "I think there are problems" to "the problems are mapped, prioritized, and fixed" — end to end, human in control at every gate.

The improvement engine is built on **deep modules** (John Ousterhout, *A Philosophy of Software Design*): a deep module has a *small interface hiding a large implementation*. Deep modules are more testable, more AI-navigable, and let you test at the boundary instead of inside. The goal of the Deepen stage is to turn shallow, tightly-coupled clusters into deep modules.

This skill is **self-contained** (Python/TS); worker roles run inline by default and may use explicitly authorized delegation.

```
Map ──► Audit ──► Deepen (recursive) ──► (next round)
 │        │          │
scan    parallel   explore → candidates → design N interfaces
        subagents  → RFC → optionally implement → recurse
```

---

## Host portability

Without delegation authority, run every worker role serially inline; this requires zero
AgentTool calls. Delegate only when the user or an applicable host instruction explicitly
authorizes distinct workers; capability, AFK mode, and silence are not authority.
Do not claim inline roles are independent or parallel. If separate contexts are essential, open
an explicit human gate.

---

## Core principles

1. **Self-contained.** Mapping is inline; checks and contracts live in bundled `references/`. No other skill required.
2. **Blueprint is a bonus, not a requirement.** Use a `BLUEPRINT.md` as stronger anchors if one exists; otherwise rely on the lightweight scan + bundled checks.
3. **Deep modules are the target.** Improvement means *deepening*: shrinking interfaces, hiding complexity, testing at the boundary. Friction encountered while reading the code IS the signal.
4. **Compose worker roles; delegate only with authority.** The main agent sequences the workflow, aggregates results, runs checkpoints, and owns stateful decisions. Authorized hosts may delegate read-only or heavy roles; otherwise the same roles run inline.
5. **Human-in-the-loop at every gate.** Never decide scope, which candidate to pursue, which interface to adopt, whether to recurse, or whether to commit/push. Pause and ask. (This skill is HITL by design — unlike an AFK autopilot, it does not fabricate human-gate decisions.)
6. **Evidence over assertions.** Every finding cites a real `path:line`.
7. **Recursion is bounded and gated.** Never auto-recurse. Each deeper level needs an explicit user yes, and there is a default depth cap (see Recursion control).
8. **Respect conscious decisions.** A choice documented in `CLAUDE.md`, a decision spec, or a blueprint is not a finding.
9. **Simplicity over brevity.** Clarity is the goal — never line count. When a transformation makes code simpler to read (explicit over clever, named intermediate steps, flat over nested), prefer it *even if it adds lines*. A longer, obvious implementation beats a short, dense one. This applies to the implementation *inside* a module; the module's interface still stays small. Behavior must be preserved and proven by tests, and code is never padded for its own sake. See `references/simplify-playbook.md`.
10. **Implementation is test-driven and quality-looped.** Code changes go through a TDD + review + QA loop (tests first → implement → review → fix → QA-simulate → fix → repeat until clean, capped). See `references/quality-loop.md`.

---

## Stage 1 — Map

Understand the repo's shape. Read-only; can be a single subagent, or inline for a small repo.

1. **Detect the stack.** Targets **Python** and **TypeScript** (manifests: `pyproject.toml`/`requirements.txt`/`setup.py`; `package.json`/`tsconfig.json`). Neither → say so and stop. Both → treat each as its own project.
2. **Lightweight structural scan:**
   ```bash
   find . -maxdepth 2 -type f \( -name 'pyproject.toml' -o -name 'requirements.txt' \
     -o -name 'setup.py' -o -name 'package.json' -o -name 'tsconfig.json' \) \
     -not -path '*/node_modules/*' -not -path '*/.venv/*'
   tree -L 3 -I 'node_modules|.venv|venv|dist|build|.next|__pycache__' 2>/dev/null || \
     find . -maxdepth 3 -type d -not -path '*/node_modules/*' -not -path '*/.venv/*' | sort
   ```
   Note project roots, apparent layers, and repeated folder patterns.
3. **Opportunistic blueprint.** If a `BLUEPRINT.md` exists (`.claude/…`, `docs/…`), read it for stronger anchors. If not, proceed — do not block.
4. **(Optional) Pack context for an LLM** via `repomix` / `tree -L 3` if the user wants a single-file snapshot.

---

## Stage 2 — Audit (whole repo)

The main agent composes read-only audit roles and may delegate them when authorized. Catalogs:
- `references/universal-checks.md` — language-agnostic anti-patterns.
- `references/audit-catalog.md` — Python/TS health signals + detection commands.
- `references/audit-worker.md` — the contract every audit subagent follows.

1. **Partition** the repo into scopes from the Stage 1 scan: one **per-subtree** worker per significant module (local checks), plus one **cross-cutting** worker (duplication, manifest dependency direction, stale deps, repo-wide secrets). ~1 worker per module; 2–4 for a small repo.
2. **Run every worker.** Inline roles run serially; explicitly authorized delegations may run concurrently. Each gets its scope, catalogs, blueprint path, and scratch output path. Workers are **read-only**.
3. **Aggregate** (main agent): merge fragments, dedupe repeated `path:line`, assign IDs, sort by severity.
4. **Fallback:** no subagents → run the same partition serially; say so briefly. Output is identical.

Present the findings inventory:

| ID | Finding | Evidence (`path:line`) | Category | Anchor | Severity |
|----|---------|------------------------|----------|--------|----------|

**⏸ Checkpoint A (always):**
> *"Audit found N findings: X blockers, Y should-fix, Z nits. Review before I look for deepening opportunities? Any you consider intentional / out of scope?"*

The inventory feeds the Deepen stage: it points exploration at the friction-heavy areas. Ephemeral by default; save to `docs/audit/findings-<YYYY-MM-DD>.md` only if asked.

---

## Stage 3 — Deepen (recursive)

This stage replaces a flat "plan then execute". It runs the deep-module flow, then **recurses** in the three forms below. Each candidate handled is one **deepening pass**; passes nest.

### 3.1 Explore for deepening opportunities

Dispatch an **exploration subagent** (an Explore-type agent if the runtime has one; otherwise inline) to navigate the codebase the way an AI would — organically, not by rigid heuristics — seeded by the audit findings. Note where you hit friction:
- Understanding one concept requires bouncing between many small files.
- A module is so shallow its interface is nearly as complex as its implementation.
- Pure functions were extracted only for testability, but the real bugs hide in how they're called.
- Tightly-coupled modules create integration risk in the seams between them.
- Parts that are untested or hard to test.

The friction IS the signal.

### 3.2 Present candidates

A numbered list of deepening opportunities. For each:
- **Cluster** — which modules/concepts are involved.
- **Why coupled** — shared types, call patterns, co-ownership of a concept.
- **Dependency category** — one of the four in `references/deep-module-reference.md`.
- **Test impact** — which existing tests would be replaced by boundary tests.

Do NOT propose interfaces yet.

**⏸ Checkpoint B:** *"Which of these would you like to explore?"*

### 3.3 Frame the problem space

For the chosen candidate, write a user-facing explanation: the constraints any new interface must satisfy, the dependencies it must rely on, and a rough illustrative code sketch to ground the constraints (a sketch, not a proposal). Show it, then immediately proceed to 3.4 — the user thinks while the design subagents work.

### 3.4 Design multiple interfaces

Run **3+ design roles** (see `references/interface-designer.md`) serially inline by default;
explicitly authorized distinct workers may run concurrently. Each produces a **radically
different** interface under a different constraint:
- Agent 1: minimize the interface — 1–3 entry points max.
- Agent 2: maximize flexibility — many use cases, extension points.
- Agent 3: optimize for the most common caller — make the default case trivial.
- Agent 4 (if cross-boundary deps): ports & adapters.

Each returns: interface signature, a usage example, what complexity it hides, dependency strategy, trade-offs.

Present the designs sequentially, compare them in prose, then **give your own opinionated recommendation** — strongest design and why, or a hybrid if elements combine well. The user wants a strong read, not a menu.

**⏸ Checkpoint C:** user picks an interface or accepts the recommendation.

### 3.5 Capture as an RFC

Create a refactor RFC as a markdown file in `docs/` using the template in `references/deep-module-reference.md`. Don't ask for pre-review — create it and share the path.

### 3.6 (Optional) Implement — TDD + QA quality loop

The deep-module flow ends at the RFC by design. If the user wants it built now, run the **quality loop** in `references/quality-loop.md`. It is test-driven, delegates heavy steps to subagents, and iterates review→fix→QA→fix until clean (capped). The main agent orchestrates and keeps the git/HITL gates.

**⏸ Checkpoint D (before any code change):** *"Build this RFC now on a branch, or leave it as an RFC for later? (If building: I'll go TDD — tests first — then implement, review, and simulate QA, looping until clean.)"*

On a yes, in order:
1. **Branch** `git switch -c improve/<rfc-slug>` (confirm; never push/PR without explicit go-ahead).
2. **Tests first (red).** A test-writer role writes boundary tests from the RFC's acceptance criteria and preserved behavior; run them to define the target.
3. **Implement (green).** An implementer role makes the tests pass in small steps, applying `references/simplify-playbook.md`.
4. **Review.** Run correctness and maintainability review roles following `references/review-rubric.md`; merge and dedupe findings.
5. **QA plan + simulate.** Run QA-plan and QA-simulation roles; retain pass/fail/skip evidence.
6. **Fix & loop.** Blocking findings or QA failures → a fix role addresses them → step 4. Cap at `MAX_QUALITY_ITERATIONS` (default 3), then report "needs human".
7. **Report** what changed, tests, review + QA status, `path:line`.

The loop runs to completion then reports — it does **not** prompt mid-loop, but it also never fabricates a decision: anything genuinely needing a human (a blocked dependency, an ambiguous behavior change) stops that branch and is flagged, per principle 5.

### Configuration (defaults, override in plain language)

- **`MAX_QUALITY_ITERATIONS` = 3** — review→fix→QA cycles before flagging "needs human".
- **`REVIEW_BLOCKING_SEVERITY` = high** — only findings at this severity or above block; lower ones are recorded, not blocking.
- **`GIT_STRATEGY` = branch** — create branch + commit; **PR/push only on explicit go-ahead; never auto-merge.**

### 3.7 Recurse — three forms, each gated

After a pass, offer the user the next move. **Never recurse automatically.**

- **Decompose (downward).** If the chosen candidate is too big to deepen as one unit, split it into sub-parts and run 3.1–3.6 on each sub-part. The sub-parts inherit the parent's framing.
- **Re-explore (deeper).** After implementing a refactor, re-run 3.1 *scoped to the changed area* — deepening one module often exposes the next layer of friction underneath. A **simplify pass** (apply `references/simplify-playbook.md` to the changed code) is a valid lightweight form of this.
- **Re-audit (outward).** When the chosen candidates are done, optionally re-run Stage 2 to surface the next round across the repo, then return here.

**⏸ Checkpoint E (after each pass):**
> *"Pass complete. Recurse? (a) decompose this candidate further, (b) re-explore the area I just changed, (c) re-audit the whole repo for the next round, or (d) stop here."*

---

## Recursion control

Recursion is powerful and easy to run away with, so it is bounded:
- **Default depth cap = 3** nested levels (a pass inside a pass inside a pass). To go deeper, ask explicitly: *"We're 3 levels deep. Keep going?"*
- **Always gated.** Every deeper level passes through Checkpoint E first. No silent continuation.
- **Track the stack.** Keep a short visible trail of where you are, e.g. `payments → refund flow → idempotency key`, so the user never loses the thread.
- **Diminishing returns stop.** If a level surfaces only nits, say so and recommend stopping rather than recursing for its own sake.

---

## Where files go

| Artifact | Location | When |
|----------|----------|------|
| Findings inventory | chat by default; `docs/audit/findings-<YYYY-MM-DD>.md` if asked | Stage 2 |
| Refactor RFC | `docs/<rfc-slug>.md` | Stage 3.5 |
| QA test plan | `docs/qa/test-plan-<branch>.md` | Stage 3.6, when implementing |
| Code changes | edited in place on branch `improve/<rfc-slug>` | Stage 3.6 |
| Repomix snapshot (optional) | `repomix-output.xml` at repo root | Stage 1, if requested |
| `BLUEPRINT.md` | only *read* if it exists — this skill never writes one | Stage 1 |

Audit/exploration/design subagents write intermediate fragments to a scratch workspace, **not** the repo. Only RFCs and (if asked) the saved inventory land in `docs/`. Never write outside the repo; never overwrite a same-day file without asking.

---

## Stop-and-ask checkpoints summary

| # | Checkpoint | When |
|---|-----------|------|
| A | Review findings inventory | End of Stage 2, always |
| B | Pick a candidate to explore | Stage 3.2, always |
| C | Pick an interface design | Stage 3.4, always |
| D | Implement now vs RFC-only | Stage 3.6, before any code change |
| E | Recurse vs stop | After each pass, always |
| — | Branch / commit / push | Whenever a git side-effect is about to happen |

Add pauses anytime something is genuinely ambiguous. Never invent a decision the human should make.

---

## What this skill does NOT do

- It does **not** depend on any other skill — mapping, checks, and design contracts are bundled.
- It does **not** propose interfaces before the user picks a candidate, nor implement before the user okays it.
- It does **not** recurse on its own, exceed the depth cap silently, or do big-bang rewrites.
- It does **not** push branches, open PRs, or commit without explicit per-action approval.

---

## See also

- `references/deep-module-reference.md` — the four dependency categories + the RFC template.
- `references/simplify-playbook.md` — clarity-first transformations (simpler, even if longer; behavior-preserving).
- `references/interface-designer.md` — contract for the parallel interface-design subagents.
- `references/quality-loop.md` — TDD + review + QA implementation loop (subagent-delegated, capped).
- `references/review-rubric.md` — correctness (recall-biased) + maintainability (thermo-nuclear) review rubrics.
- `references/qa-test-plan.md` — manual e2e QA plan pipeline + format.
- `references/audit-worker.md` — contract for the audit subagents.
- `references/universal-checks.md` — language-agnostic anti-pattern catalog.
- `references/audit-catalog.md` — Python/TS health signals + detection commands.
