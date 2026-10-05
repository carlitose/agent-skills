---
ticket_schema: 1
ticket_id: "MP13-02"
execution_mode: AFK
blocked_by: []
---

# MP13-02 — Session retro for Pi

## Artifact Graph
- Artifact ID: `artifact:mattpocock-skills-1-3-parity-mp13-02`
- Role: `ticket`
- Parent: [mattpocock-skills-1-3-parity.md](../../specs/mattpocock-skills-1-3-parity.md)

## Parent Spec
[mattpocock-skills-1-3-parity.md](../../specs/mattpocock-skills-1-3-parity.md): Upstream delta, Decision 2.

## What to Build
A new user-invoked `retro` skill adapted from upstream `retro`. It reads the Pi session log the
user names (default: the current session) and returns ranked suggestions to improve the agent's
environment: navigation pointers, missing or unwired automated checks (a repo with no guardrail is
a finding), no-op or oversized steering, expensive tool calls, missing information access. A
mechanical violation is proposed as a deterministic check, not a written rule. Read-only: it
proposes and never edits steering files, settings, or code. Secrets are redacted in every quoted
command, output, or log line.

## Acceptance Criteria
- [ ] `retro/SKILL.md` exists with `disable-model-invocation: true`, a one-line human-facing
      description, the categories above, and the ranked output shape (severity, evidence pointer,
      proposed change).
- [ ] It names where Pi session logs live and how to pick the session, and says to read the
      repo's own check commands/CI before proposing a new check.
- [ ] It states read-only, no-delegation, and redaction rules.
- [ ] `retro/agents/openai.yaml` matches the local skill metadata convention.
- [ ] A focused test checks frontmatter, user-invoked flag, and the read-only and redaction rules.

## Frontier
Ready; no blocker. Files: new `retro/` directory and its new test only.

## Step-by-Step Implementation Plan
1. Confirm the Pi session-log location and format on this host (read only).
2. Write `retro/SKILL.md` and `retro/agents/openai.yaml`, credited to upstream `retro`.
3. Add the focused test next to the existing skill tests (e.g. like
   `ticket-autopilot/tests/test_to_questionnaire_skill.py`).

## Testing Plan
Run the new test and `python -B -m pytest ticket-autopilot/tests/test_skill_graph.py -q`.
Manual: run the retro once on a recent short session and check the output is ranked and redacted.

## Out of Scope
- Applying any suggestion automatically.
- Reading other users' or other machines' logs; any provider or network access.
