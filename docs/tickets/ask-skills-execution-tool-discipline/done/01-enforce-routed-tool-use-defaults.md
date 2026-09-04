---
ticket_schema: 1
ticket_id: "ATD-01"
execution_mode: AFK
blocked_by: []
---

# Enforce routed tool-use defaults

## Artifact Graph

- Artifact ID: `ticket:ask-skills-execution-tool-discipline:ATD-01`
- Role: `ticket`
- Parent: [Ask Skills Execution Tool Discipline](../../specs/ask-skills-execution-tool-discipline.md)

## Parent Spec

[Ask Skills Execution Tool Discipline](../../specs/ask-skills-execution-tool-discipline.md)

## What to Build

Add a concise execution-discipline section to Ask Skills. For non-trivial routed work, require
agents to keep `update_plan` current, consult a compatible project-bound LLM Wiki before broad
research, and prefer the `code` tool for suitable compositional/programmatic code workflows.
Keep trivial and unavailable-tool fallbacks explicit and preserve all routing and authority
boundaries.

Update the LLM Wiki query operation to use RAG/hybrid retrieval only when the active skill
contract and selected wiki binding both name a supported adapter and that adapter is already
usable within the request's declared boundary. Otherwise select the existing compiled-Markdown
query and state the concrete fallback reason. Retrieval results remain derived context and
material claims must resolve to canonical pages and primary-source provenance.

## Acceptance Criteria

- [ ] `ask-skills/SKILL.md` names `llm-wiki`, `code`, and `update_plan` as conditional execution defaults for non-trivial routed work.
- [ ] A compatible bound wiki is queried as an index before broad research, while primary sources remain authoritative and no wiki is scaffolded by inference.
- [ ] RAG/hybrid availability requires both a supported bound configuration and an already usable adapter; recipes, installed artifacts, MCP declarations, caches, and roadmap prose are insufficient.
- [ ] A valid RAG/hybrid binding is preferred and identified; the current no-adapter baseline visibly selects `compiled-markdown` with `no-supported-rag-binding` or another concrete reason.
- [ ] Fallback performs no install, download, service start, authentication, provider call, index creation, or wiki mutation.
- [ ] `code` is preferred for loops, aggregation, repeated inspection, derived transformations, and programmatic checks, but is not forced for one small authored edit.
- [ ] `update_plan` is initialized and refreshed at meaningful state changes for non-trivial work, keeps one step in progress, and grants no workflow authority.
- [ ] Existing delivery, lifecycle, merge-all, single-ticket, and exact-authority routing contracts remain intact.
- [ ] Focused static contract tests, existing Ask Skills tests, skill budgets, Artifact Graph audit, and diff checks pass.

## Frontier

Ready. This is one bounded documentation-and-contract-test tracer bullet with no runtime RAG
integration or provider mutation.

## Step-by-Step Implementation Plan

1. Add the minimal cross-cutting execution defaults to `ask-skills/SKILL.md` without duplicating specialist workflows.
2. Amend the `llm-wiki/SKILL.md` query steps with strict capability detection, mode visibility, provenance grounding, and compiled-Markdown fallback.
3. Add focused regression assertions and adjust only the explicit Ask Skills line budget if the concise contract exceeds its current cap.
4. Run targeted and full repository checks against the exact implementation and delivery trees.

## Testing Plan

- Assert Ask Skills contains all three tool defaults, non-trivial/trivial bounds, and no authority widening.
- Assert LLM Wiki requires the two-part RAG availability condition and rejects weak availability signals.
- Assert the repository baseline reports compiled-Markdown fallback rather than claiming active RAG.
- Run existing skill-graph, merge-all routing, context-budget, and Artifact Graph tests.
- Verify no dependency, generated index/cache, service configuration, or unrelated file enters the candidate diff.

## Out of Scope

- Selecting or implementing the OHR retrieval tier.
- Installing or configuring qmd, embeddings, vector stores, HTTP services, or MCP servers.
- Changing `pi-code-tool`, `update_plan`, Pi settings, local Agent Skills, or the active Pi session.
- Publishing, merging, synchronizing, reloading, or mutating a provider without their separate exact authorities.
