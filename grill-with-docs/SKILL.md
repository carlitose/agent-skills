---
name: grill-with-docs
description: A relentless interview to sharpen a plan or design, while also creating or updating domain-modeling docs such as CONTEXT.md glossary entries and sparse ADRs when justified.
disable-model-invocation: true
---

# Grill With Docs

Compose canonical [grilling](../grilling/SKILL.md) with
[domain-modeling](../domain-modeling/SKILL.md).

If slash commands are available, `/grilling` with `/domain-modeling` is equivalent.
Otherwise load and follow both linked skills directly:

- Use `grilling` for the interview loop: one question at a time, recommended answer included, wait for feedback, and do not enact the plan until the user confirms shared understanding.
- Use `domain-modeling` for durable language: inspect existing context docs and code, challenge fuzzy terms, update `CONTEXT.md` only when terms are resolved, and create ADRs only when the ADR criteria are met.

Interview ownership remains with `grilling`; documentation is subordinate. Do not create
docs before the confirmation gate or just because this variant is active. Create or update
them lazily only when the confirmed conversation produces durable domain language or a
genuinely important decision.
