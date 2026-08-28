# Cross-host Context Rollover Policy

## Artifact Graph

- Artifact ID: `artifact:cross-host-context-rollover-decision`
- Role: `spec`
- Parent: [Cross-host Context Rollover](cross-host-context-rollover-wayfinder.md)

## Type

Decision spec

## Status

Accepted on 2026-08-11. Authority: the explicit user confirmation recorded by the `CR-01`
grilling interview. Amended on 2026-08-28 by the user's explicit decision to remove
`--autocompact` as a controller dependency because it does not provide the required behavior.

## Source

- [CR-01 Freeze the rollover policy](../tickets/cross-host-context-rollover/done/01-freeze-rollover-policy.md)
- [Cross-host Context Rollover](cross-host-context-rollover-wayfinder.md)

## Context

Codex and Claude Code expose different conversation events, session controls, and token
telemetry. A portable controller must decide when to move work out of a context-heavy chat
without parsing unstable transcripts, interrupting active work, or giving a model general
authority to replace conversations.

This decision freezes the provider-neutral policy. `CR-02` and `CR-03` may adapt current
host APIs to it, but may not redefine its message projection, trigger, authority, registry,
retry, or fallback semantics.

## Decision

### Context usage is the only trigger

The controller projects `current_context_tokens` from the host's current-context signal:

- Codex: `thread/tokenUsage/updated.params.tokenUsage.last.totalTokens`;
- Claude Code: status-line
  `context_window.total_input_tokens + context_window.total_output_tokens`.

Codex `tokenUsage.total`, Claude cumulative cost/usage, transcript size, message count, and
controller-observed byte counts are invalid trigger inputs. The host decides which message,
tool, reasoning, and system material contributes to its context. The controller consumes the
reported current-context total and never reconstructs that total from event categories.

The arming edge is exact:

| Observed current context | Transition |
| --- | --- |
| `149999` or lower | Remain `monitoring` |
| `150000` or higher | Persist one source-session-bound `rollover_pending` generation |

Crossing the edge never interrupts an active turn. A pending generation executes only after
the host proves that no turn is active and any explicit multi-turn owner, including a Codex
goal or ticket-autopilot ticket, is terminal. A next prompt submitted at that boundary is
held until restore succeeds; it is neither discarded nor run in the source chat.

### Message count is diagnostic only

The controller reports `user_messages`, `assistant_messages`, and
`total_messages = user_messages + assistant_messages`. It counts completed logical messages,
not stream chunks or token-bearing context items:

| Case | Codex projection | Claude Code projection | Message effect |
| --- | --- | --- | --- |
| User input | One accepted `userMessage`, including a distinct steer input | One accepted controller-observed user input event | `user_messages += 1` |
| Final assistant answer | Completed `agentMessage` with phase `final_answer` | One terminal assistant response correlated with the completed host turn | `assistant_messages += 1` |
| Commentary or progress | `agentMessage` with phase `commentary` | Non-terminal assistant/progress text when exposed | None |
| Tool activity | Tool-call and tool-result items | `tool_use`, `tool_result`, and hook tool events | None |
| Reasoning | Reasoning item when exposed | Thinking/reasoning block when exposed | None |
| Plan | `plan` item | Plan-mode or non-terminal planning event when exposed | None |
| Compaction | `contextCompaction` item | `PreCompact` or `PostCompact` event | None |
| Aborted turn without a final answer | No completed final answer | No terminal assistant response | None |

Deltas with the same item or turn identity are deduplicated. If a Claude Code version does
not expose a stable terminal discriminator, its adapter correlates the structured completion
or `Stop` boundary; it must not fall back to raw transcript parsing. These events may still
contribute to host-reported context tokens even when they do not increment a message count.

Codex `agentMessage.phase` is optional. When absent, the adapter may count the item only if a
structured `turn/completed` correlation proves it is the terminal response. If structured
events remain ambiguous, the adapter reports the assistant count as unavailable; it neither
guesses nor parses the transcript.

Example Codex turn:

```text
item/completed userMessage                         -> user +1
item/completed agentMessage phase=commentary      -> no message
item/completed commandExecution                    -> no message
item/completed agentMessage phase=final_answer    -> assistant +1
```

Example Claude Code stream turn (the tracer bullet must bind the versioned field names):

```text
controller-accepted type=user human input         -> user +1
type=assistant partial text/thinking/tool_use      -> no message yet
type=user tool_result generated by the tool loop  -> no message
type=result correlated with the terminal response -> assistant +1
```

The Claude example deliberately distinguishes a human input from a tool result even if the
wire representation gives both a `user` role. Exactly one terminal assistant response is
counted for the completed host turn.

### Rollover state machine

The shared controller implements these semantic states:

| State | Exit condition | Required failure behavior |
| --- | --- | --- |
| `monitoring` | Context reaches `150000` | Persist one pending generation; continue active work |
| `rollover-pending` | Safe task boundary is observed | Hold a submitted next prompt |
| `task-stopped` | No host turn or explicit owner remains active | Keep the source session recoverable |
| `handoff-validated` | Private bound handoff and registry entry validate | Do not replace the source on validation failure |
| `restore-attempt` | Replacement bootstrap and authoritative readback finish | Resume the same attempt phase idempotently after interruption |
| `restored` | Target identity/mode, context, and durable frontier read back successfully | Consume the handoff, clear pending, and release the held prompt |
| `failed` | A non-retryable error or third failed attempt occurs | Keep the prompt held and surface an actionable terminal error |

A normal restore requires a target session identity distinct from the source. The degraded
compaction fallback records `target_mode: compacted-source` instead of claiming a new
identity. Both modes require an unexpired handoff, successful bootstrap, authoritative
frontier reconstruction, and an observed `current_context_tokens < 150000`.

After rollover the source generation cannot arm again until the controller has observed a
sub-threshold context for the restored target. A target that remains at or above `150000`
fails its restore attempt. This latch preserves the exact `149999`/`150000` edge while
preventing an immediate rollover loop.

### Retry and fallback policy

One rollover generation allows at most three end-to-end restore attempts: the initial
attempt plus two retries. The attempt count is persisted before an external mutation.
Interruption resumes the recorded phase of the same attempt instead of allocating another
target speculatively.

The retry route is deterministic:

1. Prefer a true fresh session whenever the host declares that capability.
2. Retry the fresh-session route for transient creation, bootstrap, or readback failures.
3. Use `compaction + bootstrap` only when fresh-session creation is explicitly unsupported,
   not merely because one fresh-session attempt failed.
4. Reuse the exact bound handoff and rollover generation for every attempt.
5. Stop after the third failed attempt; never continue because of silence or AFK mode.

Expired, consumed, malformed, workspace-mismatched, or source-session-mismatched handoffs
fail closed and are not retryable. A transient transport error, an incomplete idempotent
phase, or a target that fails freshness/readback is retryable within the shared limit. The
fresh-session route keeps the source session recoverable throughout. A failed generation
retains its unconsumed handoff only until expiry so a human can diagnose or explicitly retry
it.

Compaction is a degraded fallback, not a normal successful rollover. It may run only after
the threshold armed a generation, the task stopped, and the handoff validated. The result
must remain labeled as degraded and must pass the same context and frontier readback.
Compaction mutates the source context, so that route cannot claim that the original context
remains recoverable. After compaction, recovery is limited to the compacted session plus the
validated handoff and authoritative durable pointers.

### Compaction compatibility

No adapter may require, set, or invoke `--autocompact`. A version-specific help entry is not
evidence that the flag controls the effective automatic-compaction boundary. The controller
may rely only on a supported surface whose runtime effect `CR-05` observes in isolation.

`PreCompact` never arms rollover below `150000`. If the host's effective automatic
compaction boundary prevents the configured context from reaching `150000`, the controller
reports a visible incompatible-configuration error rather than silently lowering the
threshold or calling compaction a fresh-session rollover.

`DISABLE_COMPACT`, a blocking `PreCompact` hook, `PostCompact`, and `/compact` are capability
candidates, not assumed replacements. If none can safely preserve the fixed threshold, the
Claude controller direction is `no-go`. The retrofit must not install a global hook or change
global environment configuration during local verification.

If a generation is already pending, `PreCompact` and `PostCompact` preserve its identity,
handoff binding, held prompt, and attempt budget. Compaction cannot clear or supersede an
already armed generation.

### Private handoff and registry

The rollover entry point preserves the existing `handoff` security contract:

- create a private OS-temporary directory with mode `0700` and `HANDOFF.md` mode `0600`;
- store redacted durable pointers and reconstruction commands, never a raw transcript;
- keep the artifact outside the repository and synced folders;
- expire it exactly one hour after creation;
- delete it immediately after a verified restore;
- use it only as temporary transport, never as scheduler or verification state.

Ticket-driven work needs no model-created semantic summary. The handoff points the target at
the authoritative Wayfinder map, ticket folder, Git state, and ticket-autopilot ledger, then
provides exact reconstruction commands. Minimal redacted context may explain a pointer but
cannot duplicate the durable artifact.

The private registry key is:

```text
(workspace_key, host_adapter_id, source_session_key, rollover_generation)
```

`workspace_key` is the SHA-256 digest of the canonical workspace real path.
`source_session_key` is a digest of the host's source-session identity; the raw
identity need not be exposed in reports. `rollover_generation` is a monotonic generation for
that source session, allocated atomically when the threshold first arms. The registry stores
the generated `rollover_id`, exact handoff path and digest, expiry, state, attempt count,
target receipts, and consumption receipt.

The registry lives outside the workspace under a controller-private OS-temporary root with
directory mode `0700` and entry mode `0600`. Create-or-read, attempt increments, receipts,
consumption, and expiry transitions use an inter-process lock or compare-and-swap plus atomic
rename; a partially written entry is invalid and never authorizes a side effect.

Duplicate events for the same source and generation resolve to the same registry entry and
`rollover_id`. Different source sessions in one workspace receive independent entries and
distinct target sessions. An atomic create-or-read transition prevents two controllers from
owning the same generation. Neither a directory timestamp nor a global "latest handoff"
pointer participates in selection.

The handoff becomes consumed only after the target readback proves the bound durable
frontier and sub-threshold context. Consumption is one-shot. A replay of a consumed entry,
an expired entry, or a target receipt owned by another source fails closed.

### AFK authority boundary

Enabling rollover for a workspace grants the narrow controller standing authority to:

1. observe the host's stable metrics and structured events;
2. create and validate the private rollover handoff;
3. create or select the replacement mode at the safe boundary;
4. submit the pointer-only bootstrap;
5. close, retire, or move focus away from the source chat only after verified restoration;
   and
6. release the held user prompt after verified restoration.

The narrow controller is the only automated actor authorized to replace or retire the source
chat and submit the bootstrap. Host UI or API actions that cannot be attributed to that
controller remain operator actions and cannot be inferred from model output.

No per-rollover prompt is required. That grant does not authorize interrupting an active
task, weakening handoff validation, exceeding the retry limit, merging ticket work, or
inventing a host capability.

The general-purpose `handoff` skill remains user-invoked with
`disable-model-invocation: true` and `allow_implicit_invocation: false`. The automatic
controller uses a narrow entry point or shared non-model library that enforces the same
privacy contract. A model cannot decide ad hoc to invoke the generic skill, replace a chat,
or submit a bootstrap.

## Consequences and trade-offs

- Message reports are comparable across hosts but intentionally omit commentary, tools,
  reasoning, plans, and compaction as messages.
- Host-reported context remains authoritative even when it includes categories excluded
  from the message report.
- The one-hour handoff lifetime supports bounded retries while minimizing residual private
  state.
- A true fresh session is stronger than compaction. The fallback preserves continuity but
  must remain visibly degraded.
- A host that always compacts below `150000` cannot implement this policy without a visible
  configuration change; the controller does not silently change the confirmed edge.
- Removing `--autocompact` trades a convenient-looking version-bound flag for a capability
  check backed by observed supported behavior. Unsupported hosts fail visibly.
- Three attempts improve resilience without allowing an AFK retry storm or uncontrolled
  chat creation.

## Rejected alternatives

- Triggering on message count: it does not measure context pressure.
- Reconstructing context usage from messages or transcript bytes: it disagrees with host
  token accounting and misses hidden or compacted material.
- Parsing raw transcripts as the portable message contract: formats are unstable and may
  expose unnecessary sensitive content.
- Selecting the newest temporary handoff by timestamp: concurrent chats can restore the
  wrong state.
- Treating pre-threshold auto-compaction as successful rollover: it neither observes the
  arming edge nor proves a fresh-session restore.
- Treating `--autocompact` help text as a working control contract: the user reports that it
  does not work for the required boundary, and official material does not establish it as the
  supported guarantee.
- Falling back to compaction after any transient fresh-session error: it degrades behavior
  before the preferred capability is proven unavailable.
- Unlimited retries or immediate re-arming above the threshold: both permit rollover loops.
- Making the generic `handoff` skill implicitly model-invocable: it grants broader authority
  than the deterministic controller requires.
- Copying tickets, ledgers, or transcripts into `HANDOFF.md`: those artifacts already have
  durable owners.

## Implementation slices

1. `CR-02` implements a disposable Codex adapter against App Server tagged items, current
   token usage, fresh thread creation, bootstrap, and compaction fallback.
2. `CR-03` implements the equivalent Claude Code controller against structured stream/hook
   events, status-line context data, fresh UUID sessions, and compaction fallback.
3. Both tracer bullets share registry fixtures, exact threshold scenarios, idempotent retry
   cases, expiry/consumption cases, and collision cases.
4. `CR-05` separates supported compaction controls, local help surfaces, and observed runtime
   effects without changing global configuration.
5. `CR-06` removes `--autocompact` from the Claude prototype, fixtures, tests, and docs and
   implements the decided fail-closed capability result.
6. `CR-04` observes one real rollover per host only after the retrofit and records capability
   or authority gaps without upgrading unobserved behavior into a claim.

## Verification strategy

`CR-01` changes documentation only and claims no runtime proof.

- **Decision checks:** every ticket acceptance criterion maps to an explicit invariant,
  example, failure rule, or rejected alternative in this document.
- **Artifact graph:** the decision and parent map have reciprocal ownership links and
  `artifact-audit` reports no new error.
- **Unit fixtures for CR-02/CR-03:** cover `149999`/`150000`, every message/event category,
  duplicate events, pending preservation, expiry, one-shot consumption, and three-attempt
  exhaustion.
- **Integration fixtures:** prove held-prompt release only after authoritative readback and
  prove source recovery after each failure phase.
- **System prototypes:** prove the structured event and session boundaries separately for
  Codex and Claude Code.
- **Compaction-control evidence:** `CR-05` binds official material and isolated observations;
  CLI help alone is insufficient.
- **Live evidence:** remains owned by `CR-04`; local fixtures cannot claim production host
  authority or behavior.

## Assumptions and unresolved implementation facts

No product-policy decision remains open. Exact versioned field shapes, supported compaction
control, command receipts, host authentication, UI focus behavior, and backoff timing remain
adapter facts for `CR-05`/`CR-06`. An adapter may choose bounded backoff, but it cannot change
the shared three-attempt limit, restore `--autocompact`, or weaken any semantic gate above.
