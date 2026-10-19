---
type: source
title: "MP13-02 — Session retro for Pi"
identity_key: ticket:mattpocock-skills-1-3-parity/MP13-02
identity_strength: stable
source_path: docs/tickets/mattpocock-skills-1-3-parity/02-session-retro.md
source_digest: sha256:a018ef658d870720a961fc4403758d66b94b97c2ad4e32b78b442eb7b727ac05
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-10-05
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# MP13-02 — Session retro for Pi

Compiled from `docs/tickets/mattpocock-skills-1-3-parity/02-session-retro.md`. Identity is `ticket:mattpocock-skills-1-3-parity/MP13-02`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-05** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-mattpocock-skills-1-3-parity]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-mattpocock-skills-1-3-parity-mp13-02.md","payload_bytes":2445,"payload_sha256":"a018ef658d870720a961fc4403758d66b94b97c2ad4e32b78b442eb7b727ac05"}],"payload_bytes":2445,"payload_sha256":"a018ef658d870720a961fc4403758d66b94b97c2ad4e32b78b442eb7b727ac05","schema":1,"source_digest":"sha256:a018ef658d870720a961fc4403758d66b94b97c2ad4e32b78b442eb7b727ac05","source_identity":"ticket:mattpocock-skills-1-3-parity/MP13-02","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2445,"payload_sha256":"a018ef658d870720a961fc4403758d66b94b97c2ad4e32b78b442eb7b727ac05","schema":1,"source_digest":"sha256:a018ef658d870720a961fc4403758d66b94b97c2ad4e32b78b442eb7b727ac05","source_identity":"ticket:mattpocock-skills-1-3-parity/MP13-02"} -->
```markdown
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

```
