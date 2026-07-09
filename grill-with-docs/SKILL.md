---
name: grill-with-docs
description: A relentless interview to sharpen a plan or design, while also creating or updating domain-modeling docs such as CONTEXT.md glossary entries and sparse ADRs when justified.
disable-model-invocation: true
---

# Grill With Docs

Run the `grilling` workflow while applying the `domain-modeling` discipline.

If slash commands are available, `/grilling` with `/domain-modeling` is equivalent. If they are not, load and follow both local skills directly:

- Use `grilling` for the interview loop: one question at a time, recommended answer included, wait for feedback, and do not enact the plan until the user confirms shared understanding.
- Use `domain-modeling` for durable language: inspect existing context docs and code, challenge fuzzy terms, update `CONTEXT.md` only when terms are resolved, and create ADRs only when the ADR criteria are met.

Documentation remains subordinate to the interview. Do not create docs just because this variant is active; create or update them lazily when the conversation produces durable domain language or a genuinely important decision.
