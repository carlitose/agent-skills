# Pi Break Glass natural-language local repair

## Artifact Graph

- Artifact ID: `spec:pi-break-glass-natural-language-local-repair`
- Role: `spec`
- Parent: [Agent Skills repair-to-Omicron work queue](agent-skills-repair-to-omicron-wayfinder.md)

### Children

- [BGR-01 — Enable one-turn natural-language local repair](../tickets/pi-break-glass-natural-language-local-repair/01-enable-one-turn-local-repair.md)

## Type

Feature correction and interaction-design specification.

## User decision

Break Glass must be a real escape hatch from a broken Ticket Autopilot control plane, not a
read-only diagnostic mode and not another miniature approval workflow. The operator wants to
arm it with one command and describe the repair in ordinary language.

## Current behavior

`/break-glass arm` asks for an incident class, target, reason, actor, a scope confirmation,
and an exact confirmation phrase. The next natural-language turn receives only canonical
`read` and individually confirmed `bash`. Its injected policy forbids tracked edits and sends
any repair back through `to-spec -> to-tickets -> ticket-autopilot`.

That design cannot escape the failure it exists to handle. When routing, a run ledger, a runner
transition, or completion projection is itself broken, the operator is forced back through the
same control plane. Even though confirmed Bash is technically capable of changing a file, the
policy forbids the required repair.

## Target interaction

The complete operator flow is:

```text
/break-glass
<one ordinary-language repair request>
```

Examples of the second line include:

```text
Ticket Autopilot is stuck on run X. Fix the local ledger or runner file that is blocking it,
read the resulting status, and resume the normal flow.
```

The slash command immediately arms the next eligible natural-language turn. It asks for no
incident taxonomy, actor, evidence URI, target form, repeated confirmation, or magic phrase.
`/break-glass status` and `/break-glass cancel` remain available.

The natural-language prompt is the complete one-turn scope. The session already stores that
prompt; the append-only Break Glass state stores its SHA-256, session identity, working
directory, creation/expiry times, and exact prior/recovery tool lists.

## Local repair capability

For the consumed turn, expose only unambiguous canonical Pi built-ins:

- `read`
- `bash`
- `edit`
- `write`

The tools execute without a second per-call dialog. This explicitly permits the minimum local
repair requested by the prompt, including:

- tracked files in a worktree;
- local runner code or configuration;
- `.git/ticket-autopilot` run state, receipts, or ledgers when that state is the deadlock;
- direct local commands needed to inspect, repair, validate, and invoke `status` or `resume`.

The turn must preserve a preimage before replacing control-plane state when practical, must not
fabricate evidence, and must describe manual state changes truthfully. A changed CandidateRef is
allowed: normal Ticket Autopilot re-entry may invalidate stale review/QA/verification and rerun
them. A ledger edit is not automatically trusted merely because Break Glass allowed it; the
normal command must read it back successfully or the result remains an explicit failed repair.

At `agent_end`, session shutdown, or interrupted-session recovery, restore the exact prior tool
list and close the grant. The next ordinary prompt is routed through Agent Skills again.

## Authority boundary

The explicit `/break-glass` command authorizes one local repair turn. It does not authorize:

- provider calls, PR publication, merge, push, force-push, or remote history changes;
- claiming a ticket completed, verified, integrated, or synchronized without normal readback;
- repository cleanup unrelated to the named prompt;
- local Pi synchronization or claiming `/reload` occurred;
- copying or revealing secrets.

The extension enforces the local boundary by replacing the active tool set with only the four
canonical built-ins. It cannot grant Ticket Autopilot or provider authority. If the prompt asks
for a remote boundary, the turn stops there and returns that operation to its normal explicit
authorization path.

## State contract

Introduce a v2 Break Glass custom-entry type and policy marker rather than silently widening an
already armed v1 grant. V1 entries remain historical session data but confer no v2 capability.

The v2 transition chain is intentionally small:

```text
armed -> consumed -> closed
armed -> cancelled
armed -> expired
```

`armed` binds the durable canonical session file and cwd. `consumed` additionally binds the
natural-language prompt hash, input source, exact prior tool list, and exact restricted tool
list. `closed` binds the turn outcome and restoration result. Digests, predecessor links,
monotonic sequence numbers, same-session/cwd checks, TTL, prompt identity, tool identity, and
restoration checks continue to fail closed.

Tool calls themselves are already durable session messages. The extension does not duplicate
full commands, patches, or file contents into custom audit entries, avoiding secret copies and
unnecessary approval ceremony.

## Semantic invariants

- Break Glass is inactive by default and never triggers from descriptive prose alone.
- Only the explicit slash command arms it.
- The next eligible non-command natural-language prompt consumes it exactly once.
- Slash commands, user `!` commands, blank input, extension input, and queued streaming input do
  not consume it.
- A consumed turn cannot acquire non-canonical or duplicate tool implementations.
- Prompt, session, cwd, policy-marker, state-chain, or active-tool drift revokes all recovery
  tools rather than broadening access.
- Exact prior tools are restored once or a visible restoration gate remains.
- Ordinary mandatory routing is byte-equivalent before arming and after closure.
- No Break Glass state is merge, provider, completion, verification, wiki, Pi-sync, or reload
  authority.

## Compatibility

Backward compatibility for active v1 grants is intentionally not provided. V2 uses a new custom
entry type and policy marker, so old entries cannot be reinterpreted as wider edit permission.
After the package is integrated and locally synchronized, the operator must run `/reload` before
the new command semantics are active. Reload is not performed by this feature.

## Failure modes

- No durable canonical session or cwd: refuse to arm.
- Another v2 grant is armed/consumed: refuse a second grant.
- TTL expires before a prompt: append `expired` and route normally.
- Canonical `read` is missing or ambiguous: expose no tools and fail visibly.
- Any selected tool is replaced, duplicated, removed, or changed after consumption: revoke tools.
- Prompt identity changes between consume and agent start: revoke tools.
- Tool restoration cannot be proven: expose no new tools, close with a restoration gate, and
  refuse re-arm until reload/session recovery restores a trustworthy baseline.
- Local repair or normal `status`/`resume` fails: report the exact remaining defect; do not claim
  the control plane recovered.

## Implementation slice

One tracer-bullet ticket replaces the v1 interaction and policy with the v2 natural-language
one-turn local repair boundary, updates the package documentation, and exercises the complete Pi
extension lifecycle in the existing fake runtime.

## Verification strategy

- **Unit:** v2 digest chain, expiry, single consumption, old-v1 non-adoption, canonical tool
  selection, prompt identity, and corruption failures.
- **Extension integration:** `/break-glass` arms without dialogs; ordinary language consumes it;
  `read`/`bash`/`edit`/`write` execute without per-call confirmation; every other tool is blocked;
  agent end restores the exact prior list and ordinary routing.
- **Negative:** commands/queued input do not consume, session/cwd/prompt/tool drift revokes,
  forked sessions do not inherit, expiry/cancel is terminal, and restoration ambiguity gates.
- **Regression:** all Agent Skills extension and Ticket Autopilot context/token tests remain green.
- **Manual after integration:** run `/reload`, arm with `/break-glass`, issue one plain-language
  local test repair in a disposable checkout, confirm direct mutation/readback and next-turn
  routing. This manual check grants no merge or production claim.

## Acceptance outcomes

1. `/break-glass` arms in one step without asking for metadata or a confirmation phrase.
2. One ordinary-language prompt receives canonical `read`, `bash`, `edit`, and `write` without
   per-tool confirmation.
3. The injected policy explicitly allows direct local tracked and Ticket Autopilot control-plane
   repair and tells the agent to validate `status`/`resume` before claiming recovery.
4. The turn closes once, restores the exact previous tools, and the next prompt follows mandatory
   routing.
5. Corrupt identity, state, prompt, marker, or tool provenance fails closed.
6. V1 grants never acquire v2 mutation scope.
7. No local-repair grant is treated as remote/provider/merge/completion/wiki/Pi authority.

## Non-goals

- A generic validator that can make every arbitrarily hand-edited ledger semantically valid.
- Automatic merge, push, PR, wiki publication, local Pi synchronization, or reload.
- Long-lived unrestricted mode or a global switch that disables Agent Skills permanently.
- Replacing normal Ticket Autopilot recovery paths when they are functioning.
