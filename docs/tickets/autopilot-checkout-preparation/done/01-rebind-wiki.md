---
ticket_schema: 1
ticket_id: "APM-PREP-01"
execution_mode: AFK
blocked_by: []
---

# Rebind the existing wiki to the selected Windows checkout

## Artifact Graph
- Artifact ID: `artifact:autopilot-checkout-preparation-apm-prep-01`
- Role: `ticket`
- Parent: [Practical Reliability for Ticket Autopilot](../../specs/autopilot-practical-reliability.md)

## Parent Spec
[Practical Reliability for Ticket Autopilot](../../specs/autopilot-practical-reliability.md), S0 — Checkout Preparation.

## What to Build
Change only `project_root` in `knowledge/llm-wiki-project.json` from the nonexistent Mac checkout to `C:/Users/rdpuser/projects/agent-skills`, as explicitly requested by the user. Preserve existing configuration and use the existing resolver rather than changing application behavior.

## Acceptance Criteria
- [ ] The resolver returns the selected existing Windows checkout even when invoked from a different cwd.
- [ ] `schema`, `auto_sync`, `docs_globs`, `git_mode`, and `session_providers` are unchanged; `project_root` is the only changed JSON value.
- [ ] Git recognizes the resolved project and its committed APM spec/ticket sources; artifact discovery includes the eight implementation tickets.
- [ ] No generated wiki pages, raw sources, prompt files, installed copies, or global settings are part of this configuration candidate.
- [ ] A follow-up sync no longer fails for the obsolete Mac project root; unrelated lint/provider/publication failures remain visible and do not justify widening this change.

## Frontier
Ready after the parent spec and canonical ticket sources have been committed as planning inputs. Execute inline; no subagents are authorized or needed.

## Step-by-Step Implementation Plan
1. Read the original binding and the existing `read_binding`, `resolve_project_root`, and artifact-discovery behavior. Capture the broken-root baseline.
2. Update only the configured `project_root` in the isolated runner candidate.
3. Check exact configuration parity, resolution from another cwd, Git identity, and discovery of the committed APM sources.
4. Run the ticket-local quality stages and return the config-only candidate to the runner. Keep any generated wiki candidate separate.

## Testing Plan
- Local integration: existing binding resolver against the actual selected checkout, including invocation from a temporary cwd.
- Exact JSON before/after comparison allowing only `project_root`, and real Git tracking/discovery checks.
- Run existing project-binding tests. Report any later wiki lint issue separately; these planned checks are not evidence until executed.

## Out of Scope
- Portable relative-root support, binding-schema changes, automatic fallback, or a new configuration mechanism.
- Executing APM-01 through APM-08, modifying historical wiki references, or generating wiki pages in this ticket's diff.
- Changing global Git/Pi settings, creating a subagent, or claiming full wiki synchronization from binding-only checks.
