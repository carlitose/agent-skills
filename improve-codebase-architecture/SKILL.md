---
name: improve-codebase-architecture
description: Explore a codebase to find opportunities for architectural improvement, focusing on making the codebase more testable by deepening shallow modules. Use when user wants to improve architecture, find refactoring opportunities, consolidate tightly-coupled modules, or make a codebase more AI-navigable.
---

# Improve Codebase Architecture

Explore a codebase like an AI would, surface architectural friction, discover opportunities
for improving testability, and propose module-deepening refactor RFCs. Use the shared
[codebase-design](../codebase-design/SKILL.md) vocabulary for modules, interfaces, depth,
seams, adapters, leverage, and locality instead of redefining those terms here.

Owns: a bounded survey of one requested area, candidate comparison, and its refactor RFC.
[codebase-improver](../codebase-improver/SKILL.md) remains the separate human-gated
full-repository workflow; this skill does not absorb its audit, implementation, or recursive
deepening ownership.

## Host portability

Without delegation authority, run exploration and design passes serially inline. Delegate
only when the user or an applicable host instruction explicitly authorizes distinct workers.
Do not claim inline passes are independent or parallel; if separate contexts are essential,
open an explicit human gate.

## Process

### 1. Explore the codebase

Start with recent-change hot spots: inspect unstaged changes, staged changes, and recent
commits within the user's requested area. Recent change is a seed, not proof of architectural
importance. Widen only when observed evidence crosses the initial boundary—for example,
callers, dependencies, failing tests, or repeated navigation reveal coupled behavior outside
it. Record the evidence and newly included scope whenever discovery widens.

Within that boundary, explore naturally and inline by default. Do NOT follow rigid heuristics—
explore organically and note where you experience friction:

- Where does understanding one concept require bouncing between many small files?
- Where are modules so shallow that the interface is nearly as complex as the implementation?
- Where have pure functions been extracted just for testability, but the real bugs hide in how they're called?
- Where do tightly-coupled modules create integration risk in the seams between them?
- Which parts of the codebase are untested, or hard to test?

The friction you encounter IS the signal.

### 2. Present candidates

Present a numbered list of deepening opportunities. For each candidate, show:

- **Cluster**: Which modules/concepts are involved
- **Why they're coupled**: Shared types, call patterns, co-ownership of a concept
- **Dependency category**: Use the shared [dependency categories](../codebase-design/DEEPENING.md)
- **Test impact**: What existing tests would be replaced by boundary tests

Do NOT propose interfaces yet. Ask the user: "Which of these would you like to explore?"

Visual reports are optional and ephemeral by default. Use a diagram or table in the
conversation only when it makes candidate relationships easier to understand. Do not write
or commit one unless the user explicitly asks. The refactor RFC is the only default durable
output of this workflow.

### 3. User picks a candidate

### 4. Frame the problem space

Before the design passes, write a user-facing explanation of the problem space for the chosen candidate:

- The constraints any new interface would need to satisfy
- The dependencies it would need to rely on
- A rough illustrative code sketch to make the constraints concrete — this is not a proposal, just a way to ground the constraints

Show this to the user, then immediately proceed to Step 5. The user can read while the design passes run.

### 5. Design multiple interfaces

Run 3+ [design exercises](../codebase-design/DESIGN-IT-TWICE.md), serially inline by default.
With explicit delegation authority they may use distinct workers and run concurrently. Each
produces a **radically different** interface for the deepened module.

Give each design pass the same technical brief (file paths, coupling details, dependency
category, and what should be hidden). This brief is independent of the user-facing explanation
in Step 4. Give each pass a different design constraint:

- Pass 1: "Minimize the interface — aim for 1-3 entry points max"
- Pass 2: "Maximize flexibility — support many use cases and extension"
- Pass 3: "Optimize for the most common caller — make the default case trivial"
- Pass 4 (if applicable): "Design around ports and adapters for cross-boundary dependencies"

Each pass outputs:

1. Interface signature (types, methods, params)
2. Usage example showing how callers use it
3. What complexity it hides internally
4. Dependency strategy (how deps are handled — see [REFERENCE.md](REFERENCE.md))
5. Trade-offs

Present designs sequentially, then compare them in prose.

After comparing, give your own recommendation: which design you think is strongest and why. If elements from different designs would combine well, propose a hybrid. Be opinionated — the user wants a strong read, not just a menu.

### 6. User picks an interface (or accepts recommendation)

### 7. Create refactor RFC

Create a refactor RFC as a Markdown file in the `docs/` folder. Use the template in [REFERENCE.md](REFERENCE.md). Do NOT ask the user to review before creating it; create it and share the path.
