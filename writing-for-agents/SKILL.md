---
name: writing-for-agents
description: Improve documents that agents consume, including skills, AGENTS.md, CLAUDE.md, prompts, and linked instructions. Use when creating or editing agent-facing guidance whose triggers, hierarchy, completion criteria, or wording need to be clearer.
---

# Writing for agents

Owns: writing clarity for agent-consumed documents.

This is a writing reference. `skill-creator` remains the scaffold owner. This skill does not create package structure,
choose installation locations, or register a skill. When the
document is a skill, use [SKILL-MECHANICS.md](SKILL-MECHANICS.md) for invocation and
frontmatter choices, then return package validation to `skill-creator`.

## Context pointers

A **Context pointer** names material outside the current context and states when to load it.
A skill description and an `AGENTS.md` link are both pointers. Sharpen the pointer before
inlining its target.

- Front-load the term that should trigger retrieval.
- Give each distinct branch one trigger; collapse synonymous restatements.
- Name what the target contains and the condition for reaching it.
- Remove identity already obvious from the target or surrounding document.

## The two loads

- **Context load** is always-loaded text that spends tokens and attention on every turn.
- **Cognitive load** is what a person must remember exists and choose deliberately.

Move branch-specific detail behind a pointer to reduce Context load. Preserve Cognitive
load where a human decision is valuable; remove it where selection is mechanical.

## Information hierarchy

Put material on the highest tier that needs it, and no higher:

1. **In-file step** — an action needed in the current sequence.
2. **In-file reference** — a definition or rule consulted during that sequence.
3. **Disclosed reference** — branch-specific material reached through a Context pointer.

Co-locate a concept's definition, rules, and caveats under one heading. Split by branch or
sequence when the main path becomes obscured; do not split merely to shorten a file.

## Steps and completion criteria

End every step with a **Completion criterion** that is both **checkable and exhaustive**.
Sharpen a vague bound before adding another process step. The criterion should name the
observable state that proves completion and the full set that must be accounted for.

Weak: “Improve the instructions.”

Strong: “Every pointer names its trigger branch, every local Markdown target resolves, and
no sentence duplicates an owned rule.”

Later visible steps can pull work toward premature completion. If a clear criterion still
does not prevent that behavior, disclose the later sequence across a real context boundary.

## Leading words

A **Leading word** is a compact, reusable concept that focuses execution and retrieval.
Prefer an established term such as _Seam_, _RED_, or _frontier_; define a new term only when
the existing vocabulary cannot carry the distinction.

Repeat the word where the concept must fire, not its full definition. State the positive target behavior first.
Keep a prohibition only for a necessary guardrail, paired with the
behavior that should replace it.

## Prune

- Keep each meaning in a **Single source of truth** and point to it elsewhere.
- Treat commands, configuration, and directory layout as discoverable environment state;
  document only the convention, reason, or gotcha that lookup does not reveal.
- Remove stale, irrelevant, and default no-op sentences instead of polishing them.
- Re-read every pointer after pruning: a live target behind a weak pointer is still hidden.

## Invocation examples

| Request | Owner |
| --- | --- |
| “Rewrite this AGENTS.md pointer so the right branch fires.” | Use this reference. |
| “Make these completion criteria observable and exhaustive.” | Use this reference. |
| “Prune duplicated guidance from this existing skill.” | Use this reference, then validate the existing package with its scaffold owner. |
| “Create a new reusable skill package and install it.” | Use `skill-creator`; consult this reference only for the words agents consume. |

Finish when the document's pointers, hierarchy, criteria, leading words, and ownership are
explicit; its links resolve; and each remaining line changes behavior or preserves a needed
guardrail.
