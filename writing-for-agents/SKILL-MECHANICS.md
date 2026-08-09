# Skill mechanics

This is the skill-specific branch of [SKILL.md](SKILL.md). It covers invocation
and routing only; `skill-creator` still owns scaffolding and package validation.

## Invocation choice

A skill's description is the always-loaded context pointer. Choose one mode deliberately:

- **Model-invoked** — keep a model-facing description with the distinct trigger branches.
  Use this when the agent or another skill must discover the reference without the user
  naming it. Explicit user invocation remains available.
- **User-invoked** — set `disable-model-invocation: true` and make the description a short
  human-facing summary. Use this when only the person should decide to invoke it.

Model invocation spends Context load for discoverability. User invocation spends Cognitive
load because the person must remember the skill. Do not claim both costs are absent.

## Splitting by invocation

Split a model-invoked reference only when it has a distinct Leading word that should fire on
its own, or when multiple callers need one shared reference. Otherwise keep the branch behind
an existing pointer.

## Router skills

A **Router skill** reduces Cognitive load by naming user-invoked skills and when a person
should choose each one. It recommends; it does not silently invoke a user-only skill. Keep
workflow ownership with the routed skill and keep scaffold ownership with `skill-creator`.

Complete the mechanics pass when invocation mode matches the intended caller, the description
contains only real trigger branches, and every referenced local Markdown file resolves.
