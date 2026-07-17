---
name: research
description: Research a factual, codebase, product, or external-documentation question using primary sources and return an evidence-backed answer. Use when the user asks to investigate, compare docs, find current behavior, answer a research ticket, or gather facts before a spec, prototype, or implementation.
---

# Research

Answer a bounded question with evidence. Prefer primary sources over commentary, and
trace every important claim back to the source that owns it.

If the host can run a background agent and the question is broad enough to benefit from
parallel reading, delegate the reading pass while you keep the main thread focused. If
not, do the same workflow directly.

## Process

### 1. Pin the question

Write a one-sentence research question before collecting evidence. Include:

- The decision the research should support.
- The scope: repo-local, external documentation, product behavior, market/tooling, or a
  mix.
- The expected output location if this came from a ticket or wayfinding map.

Ask one concise question only when the research target is too ambiguous to begin.

### 2. Collect primary sources

Use the strongest available sources for the claim:

- Repo source, tests, configs, logs, migrations, specs, tickets, and commit history for
  project-local behavior.
- Official documentation, source repositories, API references, standards, release notes,
  changelogs, schemas, or first-party examples for external behavior.
- The user's supplied artifacts for product, design, or business context.

Use secondary sources only as pointers to primary sources. Do not base the final answer
on a blog post, forum reply, generated summary, or search-result snippet when an owning
source is available.

### 3. Check the evidence

- Compare at least two independent primary anchors for risky or surprising claims when
  possible.
- Note versions, dates, flags, environment constraints, and repository state when they
  affect the answer.
- Run small local commands or tests when they can verify repo behavior cheaply.
- Separate observed facts from inference.

For fast-changing external facts, verify current documentation before answering.

### 4. Save durable findings

If this research is tied to a local research ticket, spec, or wayfinding map, update that
artifact or write a short report under `docs/research/<slug>.md` when no repo convention
exists. Create the folder only when a durable artifact is useful.

For quick questions, a concise final answer with evidence is enough.

## Output

Use this shape when the answer is more than a quick reply:

```markdown
## Answer

<Direct answer in one or two paragraphs.>

## Evidence

- <Source path or citation> - <fact supported by that source>.

## Unknowns

- <Remaining uncertainty, or "None".>

## Next Step

<Decision, prototype, spec update, or implementation step this research enables.>
```

Keep the output proportionate. Do not dump notes, transcripts, or long quotes unless the
user asked for raw research materials.