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
