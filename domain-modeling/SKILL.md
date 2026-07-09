---
name: domain-modeling
description: Build and sharpen a project's domain model and ubiquitous language while planning or changing software. Use when the user wants glossary work, bounded-context language, domain terminology cleanup, ADR-worthy decisions, or docs that keep product language aligned with code.
---

# Domain Modeling

Build, challenge, and maintain the project's domain model as an active discipline. Do not merely read `CONTEXT.md`; use it to sharpen language while decisions are being made.

## Files

- `CONTEXT.md`: root glossary for resolved domain terms only.
- `CONTEXT-MAP.md`: optional map of bounded contexts. If present, use it to choose which context glossary or terms apply.
- `docs/adr/`: durable architecture decision records.

Create files lazily. Do not create `CONTEXT.md`, `CONTEXT-MAP.md`, or `docs/adr/` just because the skill is active. Create or update them only when there is resolved content worth preserving.

## Core Rules

- Treat language as part of the design. Challenge fuzzy words, overloaded terms, and terms that conflict with existing usage.
- Discuss concrete scenarios before naming abstractions. Prefer examples from real workflows, users, data, and code paths.
- Cross-reference the codebase when possible. If a term already appears in code, inspect the relevant files before asking the user to define it.
- Keep `CONTEXT.md` as a glossary only. Do not use it as an implementation spec, scratchpad, backlog, decision log, or meeting notes file.
- Update `CONTEXT.md` inline when a term is resolved. Keep entries short, stable, and useful to future agents.
- The user owns product meaning. Recommend clearer language, but ask before overwriting contested terminology.

## Modeling Loop

1. Identify the current context. If `CONTEXT-MAP.md` exists, use it to find the relevant bounded context. If not, work from root `CONTEXT.md` and the codebase.
2. Extract the terms currently being used in the conversation, docs, tickets, UI, APIs, schemas, and code.
3. Flag ambiguity, synonyms, conflicts, and terms whose meaning changes by context.
4. Ask one focused question that resolves the most important ambiguity.
5. Provide your recommended term or definition, plus the scenario that supports it.
6. When the user accepts or clarifies the term, update the glossary entry if the content is durable.
7. Repeat until the model is sharp enough for the current planning or implementation decision.

## Glossary Format

Use concise Markdown entries:

```markdown
# Context

## Glossary

### <Term>

Definition: <one or two sentences>

Use when: <short concrete usage rule>

Do not use for: <nearby concept or common confusion, if useful>
```

For multiple bounded contexts, prefer headings or context-specific files only if the existing project already uses that pattern. Otherwise keep the root glossary simple and use `CONTEXT-MAP.md` only when multiple contexts are real and useful.

## ADR Discipline

Offer an ADR sparingly. Create one only when all three are true:

- The decision is hard to reverse.
- The decision would be surprising without context.
- There is a real trade-off between plausible options.

Do not create ADRs for routine implementation details, temporary plans, or obvious local choices. If an ADR is warranted, write it under `docs/adr/<yyyy-mm-dd>-<slug>.md` using:

```markdown
# <Decision>

## Status

Proposed | Accepted | Superseded

## Context

What forced this decision, including relevant domain language.

## Decision

The chosen option.

## Consequences

What this enables, constrains, or makes harder.

## Options Considered

- <Option>: benefit and drawback.
```

Ask before writing an ADR unless the user explicitly requested documentation as part of the workflow.
