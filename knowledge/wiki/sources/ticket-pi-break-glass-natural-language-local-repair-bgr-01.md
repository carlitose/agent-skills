---
type: source
title: "Enable one-turn natural-language local repair"
identity_key: ticket:pi-break-glass-natural-language-local-repair/BGR-01
identity_strength: stable
source_path: docs/tickets/pi-break-glass-natural-language-local-repair/done/01-enable-one-turn-local-repair.md
source_digest: sha256:807c3f5fee1450cf9e6d7ca716ccb6404d009f73c8c4d824307df770b33f003f
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-03
created_provenance: git-commit
disposition_changed: 2026-09-03
disposition_changed_provenance: git-rename
run_id: pi-break-glass-natural-language-local-repair-v3-20260903
---

# Enable one-turn natural-language local repair

Compiled from `docs/tickets/pi-break-glass-natural-language-local-repair/done/01-enable-one-turn-local-repair.md`. Identity is `ticket:pi-break-glass-natural-language-local-repair/BGR-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-03** via `git-commit`
- Disposition changed: **2026-09-03** via `git-rename`

## Graph

- Parent source: [[sources/spec-pi-break-glass-natural-language-local-repair]]

## Run

Completed under autopilot run `pi-break-glass-natural-language-local-repair-v3-20260903`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-pi-break-glass-natural-language-local-repair-bgr-01.md","payload_bytes":4341,"payload_sha256":"807c3f5fee1450cf9e6d7ca716ccb6404d009f73c8c4d824307df770b33f003f"}],"payload_bytes":4341,"payload_sha256":"807c3f5fee1450cf9e6d7ca716ccb6404d009f73c8c4d824307df770b33f003f","schema":1,"source_digest":"sha256:807c3f5fee1450cf9e6d7ca716ccb6404d009f73c8c4d824307df770b33f003f","source_identity":"ticket:pi-break-glass-natural-language-local-repair/BGR-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":4341,"payload_sha256":"807c3f5fee1450cf9e6d7ca716ccb6404d009f73c8c4d824307df770b33f003f","schema":1,"source_digest":"sha256:807c3f5fee1450cf9e6d7ca716ccb6404d009f73c8c4d824307df770b33f003f","source_identity":"ticket:pi-break-glass-natural-language-local-repair/BGR-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "BGR-01"
execution_mode: AFK
blocked_by: []
---

# Enable one-turn natural-language local repair

## Artifact Graph

- Artifact ID: `ticket:pi-break-glass-natural-language-local-repair/BGR-01`
- Role: `ticket`
- Parent: [Pi Break Glass natural-language local repair](../../specs/pi-break-glass-natural-language-local-repair.md)

## Parent Spec

[Pi Break Glass natural-language local repair](../../specs/pi-break-glass-natural-language-local-repair.md)

## What to Build

Replace the current metadata-heavy, read/confirmed-Bash Break Glass with the spec's v2 one-command, one-natural-language-turn local repair boundary. The consumed turn must permit direct local tracked and Ticket Autopilot control-plane repair through canonical `read`, `bash`, `edit`, and `write`, then read back and re-enter the normal workflow without transferring any remote or completion authority.

## Acceptance Criteria

- [ ] `/break-glass` arms immediately without an incident-class/target/reason/actor wizard, scope confirmation, repeated phrase, or per-tool confirmation; `status` and `cancel` remain explicit subcommands.
- [ ] The next eligible ordinary-language prompt is the exact one-turn scope, is digest-bound in durable session state, and receives only unambiguous canonical built-in `read`, `bash`, `edit`, and `write`.
- [ ] The injected policy positively permits the minimum direct local repair described by the prompt, including tracked files and `.git/ticket-autopilot` state, and requires truthful `status`/`resume` readback before claiming recovery.
- [ ] Agent end, shutdown, interruption, expiry, cancellation, session/cwd drift, prompt drift, state corruption, marker conflict, or tool provenance drift closes or revokes the grant without widening access; exact prior tools are restored or visibly gated.
- [ ] V2 uses a distinct custom-entry type and policy marker; historical v1 entries cannot arm, resume, or inherit v2 mutation capability.
- [ ] Break Glass supplies no provider, PR, push, merge, terminal integration, completion, verification, wiki, Pi-sync, cleanup, secret-disclosure, or reload authority.
- [ ] Extension tests causally prove direct `edit`/`write`/`bash` access without dialogs, blocking of non-recovery tools, one-turn closure, normal next-turn routing, fail-closed corruption paths, and v1 non-adoption.
- [ ] README and command status text explain the two-line natural-language flow without reintroducing forms or magic confirmations; package, context/token, compile, diff, and Artifact Graph checks remain green.

## Frontier

Ready by explicit operator priority override. WCA-01 remains frozen at final tree `14ac5eb88beb20e366f23e2d940ac4d6361aea6c` until this correction is integrated and locally synchronized.

## Step-by-Step Implementation Plan

1. Replace the v1 grant identity/policy contract with a non-upgrading v2 state chain whose arm has no form metadata and whose consume binds the exact prompt and tool snapshots.
2. Select only canonical built-in `read`, `bash`, `edit`, and `write`, remove per-call approval ceremony, and retain fail-closed prompt/tool/restoration checks.
3. Rewrite the injected policy and visible command/status copy around direct local repair and normal `status`/`resume` re-entry.
4. Update lifecycle, corruption, old-version, direct mutation-tool, and restoration tests before updating README usage.
5. Run focused extension tests and full repository regression checks on the exact final tree.

## Testing Plan

Use the existing fake Pi runtime to test slash-command arming, natural-language consumption, exact v2 chain replay, canonical tool selection, direct Bash/edit/write calls without UI prompts, non-selected tool rejection, close/restore, next-turn routing, expiry, cancel, fork/session/cwd/prompt/tool drift, policy-marker conflict, interrupted recovery, and historical-v1 isolation. Then run all package and Python suites, context/token checks, compileall, diff checks, and Artifact Graph audit.

## Out of Scope

- A generic semantic repair engine for arbitrary corrupt ledgers.
- Automatic provider, PR, push, merge, wiki publication, Pi synchronization, cleanup, or reload.
- Long-lived unrestricted mode or disabling mandatory Agent Skills routing outside the consumed turn.
- Replacing working Ticket Autopilot recovery paths.

```
