---
ticket_schema: 1
ticket_id: "WPI-01"
execution_mode: AFK
blocked_by: []
---

# Invoke installed Pi natively on Windows

## Artifact Graph

- Artifact ID: `ticket:pi-sync-windows:WPI-01`
- Role: ticket
- Parent: [Local Pi synchronization](../../specs/agent-skills-post-task-pi-sync.md)

## Parent Spec

[Local Pi synchronization](../../specs/agent-skills-post-task-pi-sync.md), especially the confirmed Windows exception, package installation/filtering, transaction recovery, and acceptance outcomes 8–9.

## What to Build

Make the existing exact-integrated local sync transaction invoke an already-installed npm Pi CLI on native Windows without zsh. Expose a small package-command seam to the transaction; hide platform command construction in the runner. Resolve the PATH-selected npm shim, declared installed entry point and native Node consistently. Preserve POSIX zsh behavior and all exact-head, ownership, configuration, recovery and receipt semantics.

The human selected native Windows support. The old zsh-only exclusion is superseded on Windows only. No consent, quality, delivery or runtime evidence is inferred from that design decision.

## Acceptance Criteria

- [ ] Supported npm Pi on Windows without zsh runs install/list through native Node with literal argv and the approved child-only `PI_CODING_AGENT_DIR`; no cmd.exe program, `shell=True`, Pi binary update or parent-environment mutation.
- [ ] The selected npm launcher, package identity/bin metadata and executable/entry-point files agree; missing, unsupported or contradictory layouts fail closed without guessing another install.
- [ ] Spaces, Unicode, percent and exclamation sequences and other shell-sensitive legal path characters survive the Windows process boundary literally; output is strict UTF-8.
- [ ] Disposable full transaction tests prove install, filtered package readback, replay without a second install, external preservation and rollback on command/decoding/readback failures.
- [ ] POSIX retains the zsh wrapper and existing transaction tests pass; no persisted schema/history, integration trigger, ownership authorization or merge gate changes.
- [ ] Operator guidance states the supported Windows layout, failure behavior and mandatory `/reload` boundary; tests and reports distinguish fixtures/disposable CLI checks from real installation.

## Frontier

Ready: AFK, no dependency blockers. Native support was explicitly selected. Live user installation remains a separate post-integration transaction with observed configuration and ownership.

## Step-by-Step Implementation Plan

1. Reproduce the unconditional zsh dependency and add a failing native process-boundary test with disposable inputs.
2. Replace shell-program coupling with the narrow Pi package-command interface; implement Windows resolution and native invocation, retaining POSIX behavior.
3. Exercise success/replay/failure through the existing transaction and add targeted resolver/path/output tests. Keep rollback and historical state literal.
4. Update the owned local-sync reference and affected current guidance, simplify, then run fresh final-candidate review, QA and verification through the normal runner.

## Testing Plan

- Unit tests: supported/missing/contradictory npm layout, Node preference, operation construction, strict decoding, environment isolation and POSIX wrapper.
- Process tests: native Node fixture receives literal argv/environment for shell-sensitive and Unicode paths; unavailable platforms/executables are explicit skips.
- Integration: disposable Git/source/settings/agents roots exercise normal transaction success, exact replay, external preservation and failure recovery. Never touch real user settings in tests.
- Regression: `test_pi_sync.py`, focused CLI sync tests, applicable documentation/static checks, and relevant forward scenarios. Record unrelated baseline failures and timeouts without relabeling them.
- Live boundary: only after durable integration and separate exact local configuration, ordinary `sync-local-pi` may update user resources. Do not claim an active session reloaded.

## Out of Scope

- Installing/updating Pi, Node or shells; core Pi patches, custom launchers, other package managers or standalone Pi distributions.
- New persistent transaction/authority schemas, automatic gate resolution, bypassing readback or destructive drift authorization.
- Ticket scheduling changes, continuation/prototype PSC work, provider/wiki merge policy or historical evidence repair.
