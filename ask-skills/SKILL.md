---
name: ask-skills
description: User-invoked router for selecting the right local skill or flow. Use when the user asks which skill to use, how to approach a loose idea, an existing spec, existing tickets, a hard bug, a huge or foggy effort, a messy codebase, or a review.
---

# Ask Skills

Route the user's situation to the smallest useful skill flow. This is a map, not a
process doc: recommend the path, explain the first step, and only start executing when
the user asked you to continue.

## Routing Map

### Loose idea or new feature

Use this flow:

`grill-me` if the idea needs sharpening -> `to-spec` -> `to-tickets` -> `execute-ticket`
for one ticket, or `ticket-autopilot` / `super-autopilote-ticket` for a folder.

If the user already gave enough context, skip grilling and write the spec directly.

### Already have a spec

- If there are no tickets yet, use `to-tickets`.
- If the user points to a single concrete work item inside the spec, use
  `execute-ticket` only when direct execution is clearly requested.
- If the spec is too broad or unclear to slice, use `wayfinder` to create research,
  prototype, grilling, or task tickets first.

### Already have tickets

- Use `execute-ticket` for one selected ticket.
- Use `ticket-autopilot` for an attended repo-local quality loop over a folder.
- Use `super-autopilote-ticket` when the user wants the self-contained AFK variant.

### Hard bug

Use `triangulate-diagnosis` when the bug is high-stakes, stubborn, or needs independent
cross-checking. Record the result as a diagnostic spec when durable context is useful,
then use `to-tickets` if the fix needs executable tickets.

### Huge or foggy effort

Use `wayfinder` when the destination, unknowns, or decision frontier cannot fit cleanly
in one agent session. Wayfinder creates a persistent map and investigation tickets; it
does not execute the final destination unless the user explicitly asks.

### Codebase feels messy

- Use `codebase-improver` for a whole-codebase improvement workflow.
- Use `improve-codebase-architecture` for focused architecture exploration.
- Use `wayfinder` first if the desired improvement is still too broad to frame.

### Want review

Use `code-review` for a diff review along both axes: repo standards and spec/ticket
compliance. Use `pr-antipattern-review` only when the user specifically wants blueprint
slice comparison.

## Response Shape

Return:

- **Recommended flow**: skill names in order.
- **Why**: one short reason tied to the user's situation.
- **First action**: the next prompt, file path, or command to run.
- **Artifact target**: expected spec or ticket location, if known.

If the user asked you to proceed, invoke the first skill in the recommended flow
immediately after giving the short routing note.