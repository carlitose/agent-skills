---
name: prototype
description: Build a throwaway prototype to answer one design, logic, data-model, state-machine, or UI question before committing to production code. Use when the user asks to prototype, sanity-check an approach, mock up a UI, explore design options, compare flows, or reduce uncertainty with disposable code.
---

# Prototype

Build a disposable prototype that answers one question. The prototype is not the
feature, and the answer is the only artifact that must survive.

At the top of the prototype notes or final response, state:

- The question being answered.
- The branch: logic or UI.
- The assumption if the branch was ambiguous.
- What result would make the prototype useful.

## Choose the branch

The branches produce different artifacts. Getting this wrong wastes the prototype.

- **Logic branch**: use for state machines, domain models, algorithms, API shapes,
  parsing, validation, persistence behavior, or business rules.
- **UI branch**: use for screens, components, visual hierarchy, interaction models,
  content layout, or comparing product flows.

If the question is genuinely ambiguous and the user is not reachable, default to the
branch that matches the surrounding code: backend/module questions use logic; page or
component questions use UI. State the assumption before building.

## Shared rules

- Keep the work isolated in the repo's scratch/prototype convention. If none exists,
  prefer `docs/prototypes/<slug>/`, `prototype/<slug>/`, or another clearly disposable
  local folder.
- Do not edit production paths unless the question can only be answered inside the real
  app shell. If you must touch production paths, keep the diff easy to delete.
- Use the existing runtime and task runner when possible.
- Make the prototype runnable with one command.
- Keep state in memory unless the question is about persistence. If persistence is part
  of the question, use a scratch database or local file with a clear
  `PROTOTYPE-wipe-me` name.
- Avoid broad new dependencies. Add one only when it directly answers the question and
  is easy to remove.
- Capture the answer somewhere durable: the final response, the parent ticket, the
  parent spec, an ADR, or a `NOTES.md` next to the prototype.

## Logic branch

Build the smallest runnable model of the behavior:

- Use a terminal script, unit-test-style harness, REPL command, fixture runner, or tiny
  local service.
- Encode important states, transitions, invariants, and failure cases directly in the
  prototype.
- Use realistic sample data, but keep it small and local.
- Print or assert the scenarios that answer the question.
- Stop once the model proves or disproves the design; do not build UI around it.

The logic branch should make hidden behavior visible. Prefer a clear transcript or test
output over polished presentation.

## UI branch

Build several meaningfully different variations, not one polished mock:

- Put the variations on one route, page, or local preview surface.
- Use tabs, toggles, query params, or a segmented control to switch between variations.
- Mock data locally unless the question is specifically about live data behavior.
- Reuse the app's existing components, styling tokens, and layout conventions where
  that helps the comparison.
- Verify the prototype in the browser or preview environment when available.

The UI branch should expose tradeoffs quickly. Prefer divergent options that answer the
design question over minor visual tweaks.

## Output

Report:

- Prototype path and run command.
- Which branch was used and why.
- The answer learned from the prototype.
- What should be kept, discarded, or turned into production work.
- Any uncertainty that remains.

Delete or mark the prototype as disposable when the user asks to move from exploration
to implementation.