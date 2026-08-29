# Cross-host Context Rollover

## Artifact Graph

- Artifact ID: `artifact:cross-host-context-rollover-wayfinder`
- Role: `wayfinder`
- Parent: [Autopilot Token Economics](autopilot-token-economics-wayfinder.md)

### Children

- [Cross-host Context Rollover Policy](cross-host-context-rollover-decision.md)
- [CR-01 Freeze the rollover policy](../tickets/cross-host-context-rollover/done/01-freeze-rollover-policy.md)
- [CR-02 Prototype Codex rollover](../tickets/cross-host-context-rollover/done/02-prototype-codex-rollover.md)
- [CR-03 Prototype Claude Code rollover](../tickets/cross-host-context-rollover/done/03-prototype-claude-code-rollover.md)
- [CR-04 Prove cross-host rollover live](../tickets/cross-host-context-rollover/04-prove-cross-host-rollover-live.md)
- [CR-05 Map supported compaction controls](../tickets/cross-host-context-rollover/done/05-map-supported-compaction-controls.md)
- [CR-06 Remove the autocompact dependency](../tickets/cross-host-context-rollover/done/06-remove-autocompact-dependency.md)

## Type

Wayfinding spec

## Status

Active — HITL live-proof frontier

## Destination

Provide Codex and Claude Code with a deliberate context-rollover workflow that reports a
defined count of chat messages, arms rollover when the live context reaches 150,000 tokens,
waits for a safe task boundary, creates a private pointer-based `HANDOFF.md`, starts a fresh
conversation, and restores the current Wayfinder, ticket, and runner frontier from durable
sources.

The target has two modes with the same safety contract:

- an operator-visible mode that prepares the handoff and waits for an explicit new-chat or
  clear action;
- a controller-managed mode that may create the fresh session and submit its bootstrap turn
  only after the handoff passes validation and no task is active.

The handoff remains temporary transport. Wayfinder maps, Ticket Envelopes, Git, issues, PRs,
and ticket-autopilot ledgers remain authoritative.

No Claude adapter may require, configure, or claim control through `--autocompact`. The
controller may use only a separately verified supported compaction surface, and it must report
`no-go` when the host compacts before the fixed threshold without a proven prevention seam.

## Decisions So Far

- `CR-01` freezes the provider-neutral policy in
  [Cross-host Context Rollover Policy](cross-host-context-rollover-decision.md). The adapter
  tracer bullets may validate host facts but may not reopen its trigger, message projection,
  authority, registry, retry, or fallback semantics.
- Use a host-neutral rollover state machine with host adapters. Counting, context pressure,
  conversation creation, and bootstrap injection are host facts; handoff redaction,
  expiry, pointer discipline, and one-shot restoration are shared invariants.
- Preserve the current `handoff` boundary while prototyping. Both installed copies carry
  `disable-model-invocation: true`, and the Codex metadata also disables implicit
  invocation. Automatic rollover must not silently make the general-purpose handoff skill
  model-invocable. The narrow controller entry point is defined by `CR-01`.
- Do not treat transcript parsing as the portable counting contract. Codex explicitly says
  its hook `transcript_path` format is unstable. Claude Code exposes the transcript to hooks,
  but a cross-host feature should count stable App Server items or controller-observed stream
  events and reserve raw transcript parsing for version-bound recovery diagnostics.
- A message count and a context bound answer different questions. The informational report
  counts accepted user inputs and terminal assistant answers separately and in total.
  Commentary, tools, reasoning, plans, compaction markers, stream deltas, and aborted turns
  without a final answer do not increment it. Message count never arms rollover or gets
  relabeled as token usage.
- The rollover threshold is 150,000 tokens in the live context, not 150,000 cumulative
  session tokens. For Codex the version-bound signal is
  `thread/tokenUsage/updated.params.tokenUsage.last.totalTokens`; `tokenUsage.total` is an
  accumulated sum across completions and is explicitly excluded. For Claude Code the signal
  is `context_window.total_input_tokens + context_window.total_output_tokens` from status-line
  input; those fields describe the live context from the most recent API response.
- Crossing `current_context_tokens >= 150000` is an arming edge only. It persists
  `rollover_pending` bound to the source session and observed turn, but never interrupts an
  active task. Rollover executes after the active turn reaches `Stop`/`turn/completed`, or is
  forced before the controller accepts the next task. `149999` does not arm; `150000` does.
- A safe task boundary requires no active host turn. When an explicit multi-turn owner exists
  (for example, an active Codex goal or ticket-autopilot ticket), it must also be terminal;
  otherwise `Stop`/`turn/completed` is the task boundary. A pending next prompt is held and
  replayed only after the replacement session restores successfully.
- The desired operating mode is controller-managed automatic rollover. The controller may
  create and validate the handoff, create the replacement session, and submit the bootstrap
  only at the safe boundary. The generic `handoff` skill remains explicit-only with
  `disable-model-invocation: true`; a narrow rollover entry point must enforce the same
  privacy and expiry contract instead of making that generic skill implicitly invocable.
- The user rejected `--autocompact` as a controller dependency because the observed flag does
  not provide the required runtime guarantee. `PreCompact`, `PostCompact`,
  `DISABLE_COMPACT`, and `/compact` remain host facts to verify, not assumed replacements.
  Before 150,000, compaction reports an incompatible host and does not arm rollover. An
  already pending generation survives compaction, but compaction never counts as a fresh
  session.
- Never clear or replace a live conversation before the handoff exists, is private,
  unexpired, bound to the intended workspace/session, and contains enough durable pointers
  to reconstruct the frontier. On the fresh-session route, a failed bootstrap leaves the
  source conversation recoverable. The compaction fallback mutates the source context and
  can recover only from the compacted session, validated handoff, and durable pointers.
- Restoring ticket work means reading the handoff pointer, then querying the authoritative
  ticket folder and run ledger with `ticket-list` and `status`. It does not mean copying
  Ticket Envelopes or transcript text into the handoff.
- Bind each generation through a private registry key derived from workspace, host adapter,
  source session, and monotonic generation. Duplicate source events converge; concurrent
  source sessions remain independent. Timestamp-only latest-handoff discovery is forbidden.
- A handoff expires exactly one hour after creation, is reused for at most three end-to-end
  restore attempts, and is consumed and deleted only after a verified sub-threshold restore.
  Prefer a true new session, retry it for transient failures, and use visibly degraded
  `compaction + bootstrap` only when fresh-session creation is explicitly unsupported.

## Evidence Collected

### Codex CLI 0.147.0

- Official [developer commands](https://learn.chatgpt.com/docs/developer-commands?surface=cli)
  document `/status` token usage, `/statusline` context/token fields, `/compact`, `/new`, and
  `/clear`. `/clear` creates a fresh chat and is disabled while a task is in progress.
- Official [hooks documentation](https://learn.chatgpt.com/docs/hooks) exposes
  `UserPromptSubmit`, `Stop`, `PreCompact`, `PostCompact`, and `SessionStart`. `SessionStart`
  distinguishes `startup`, `resume`, `clear`, and `compact`; hook input includes a session ID
  and optional transcript path. Command handlers are supported today, while prompt and agent
  handlers are parsed but skipped.
- The official [App Server contract](https://learn.chatgpt.com/docs/app-server) provides a
  stable, versioned route for full automation: `thread/read(includeTurns: true)` returns
  turns and tagged items such as `userMessage` and `agentMessage`; `thread/start` creates a
  fresh conversation; `turn/start` submits the bootstrap input.
- The installed 0.147.0 generated schema exposes
  `thread/tokenUsage/updated` with `tokenUsage.last.totalTokens` and
  `tokenUsage.modelContextWindow`. The protocol defines `total` as accumulated across
  completions and `last` as the most recent completion, so only the latter can represent
  live context occupancy for the 150,000-token trigger.
- Desktop deep links can open a new chat with prefilled text, but official docs state that
  the text is not sent automatically. They are an operator aid, not a complete controller.
- The CR-02 disposable tracer bullet now binds the relevant generated schema files by
  SHA-256, projects the frozen message count, proves the exact trigger edges and
  validate-before-create ordering with a local App Server fake, reconstructs durable
  pointers, and preserves the old thread. Its hook-only report does not establish `/clear`
  or fresh-thread authority; authenticated and UI proof remains with CR-04.

### Claude Code 2.1.223 selected user-local binary

- Context7 resolved the official `anthropics/claude-code` source. Its hook-development
  material documents `SessionStart`, `Stop`, transcript access, and prompt/command hook
  patterns; the changelog records `PreCompact` and `PostCompact` plus blocking support.
- Two installations were observed without changing either one. The selected
  `~/.local/bin/claude` is 2.1.223 and its help text lists `--autocompact`; the Homebrew
  `/opt/homebrew/bin/claude` is 2.1.17 and does not. A help entry proves parsing surface, not
  runtime control, and the user reports that the flag does not work for this purpose.
- The selected CLI also exposes `--session-id`, `--resume`, `--fork-session`,
  `--input-format stream-json`, `--output-format stream-json`, and
  `--include-hook-events`, plus partial, replay, and forwarded-subagent event controls. Those
  independent surfaces remain eligible for the controller prototype.
- Indexed official material reports `/context` warnings and status-line
  `context_window.used_percentage` / `remaining_percentage`. Current official status-line
  documentation also exposes `total_input_tokens`, `total_output_tokens`,
  `context_window_size`, and `current_usage`; these are current-context fields rather than
  cumulative session totals and remain separate from message count.
- Current official changelog material describes internal automatic compaction,
  `DISABLE_COMPACT`, `/compact`, threshold changes, thrash-loop protection, and blocking
  `PreCompact` hooks. Context7 did not find an official stable `--autocompact` contract.
  CR-05 bound the official source at commit
  `f1af9b1f4b1fd4c776135381606edada82ef638e` (changelog 2.1.251), the two local versions and
  sanitized help hashes, and one process-local configuration-isolation probe.
- CR-05 classifies the local prevention effect of `DISABLE_COMPACT` and blocking `PreCompact`
  as unobserved, `PostCompact` as an official observation-only surface, `/compact` as an
  operator command rather than automatic prevention, and `--autocompact` as unsupported for
  this controller. CR-06 therefore has no proven replacement switch: it must report visible
  `no-go` when compaction occurs below 150,000 rather than lowering the threshold or claiming
  control.
- The CR-06 retrofit consumes that classification as an exact fixture contract. The stream
  controller passes no compaction-control argument even when a help surface advertises one.
  Early `PreCompact` becomes `incompatible-host:no-go`; a pending generation survives both
  `PreCompact` and observation-only `PostCompact` without process or registry side effects.
- The CR-03 disposable tracer bullet wraps observations in controller-owned event
  identities, projects direct user events and unique `result`/`success` terminal answers,
  rejects replay/partial/hook/tool/subagent noise, preserves a source-bound pending
  generation through `PreCompact`, persists a fresh target UUID before simulated dispatch,
  and reconstructs Wayfinder/ticket/run pointers before consumption.
- The interactive `/clear` path has no non-interactive flag in the observed selected help
  surface and was not driven headlessly. Actual process transport, hook dispatch, provider
  behavior, and interactive clear remain live CR-04 questions.

## Host Capability Matrix

| Capability | Codex | Claude Code | Portable conclusion |
| --- | --- | --- | --- |
| Live context tokens | App Server `tokenUsage.last.totalTokens` plus `modelContextWindow` | Status-line `total_input_tokens + total_output_tokens` plus `context_window_size` | Arm at `>= 150000`; never use cumulative session totals |
| Stable message count | App Server `thread/read` tagged items | Prospective direct user events plus unique `result`/`success` terminal events | Define a shared projection; do not parse raw transcripts by default |
| Fresh conversation | `/clear` or `/new`; App Server `thread/start` | New UUID/session through CLI; interactive clear needs proof | Full automation requires a controller that owns session creation |
| Bootstrap | `SessionStart` context or App Server `turn/start` | `SessionStart` hook or initial CLI prompt | Inject only the handoff path and durable reconstruction commands |
| Compaction prevention | Host fact for live proof | CR-05 prevention effect is unobserved; CR-06 fails closed | Never infer control from parser/help evidence; early compaction is `no-go` |
| Hook-only full rollover | Not established; hooks cannot issue `/clear` while work is active | Not established | Treat hook-only rollover as a prototype question, not a claim |

## Recommended State Machine

| State | Exit condition | Failure behavior |
| --- | --- | --- |
| `monitoring` | Live context reaches 150,000 tokens | Persist source-bound `rollover_pending`; continue active task |
| `incompatible-host` | Compaction is observed before a pending generation exists | Return visible `no-go`; do not arm, create a receipt, or lower the threshold |
| `rollover-pending` | Current turn stops, or a next task is submitted while no turn is active | Hold the next task; never interrupt active tools |
| `task-stopped` | Host proves no active turn/task mutation remains | Keep old session; do not create a replacement yet |
| `handoff-validated` | Private, redacted, bound, unexpired artifact exists | Keep old session; surface validation error |
| `new-session-created` | Host returns a new session/thread identity | Old session remains recoverable |
| `bootstrap-submitted` | New session receives the handoff path and reconstruction command | Retry only with the same bound handoff |
| `restored` | Map, tickets, run status, and next frontier are read back | Mark handoff consumed and clear pending for this generation |

## Provider Facts Left to the Tracer Bullets

- The CR-03 fixture binds the versioned Claude Code terminal-response discriminator to a
  unique `result` event with subtype `success`; live process output and UI correlation remain
  CR-04 evidence rather than transcript-derived assumptions.
- The exact idempotent receipts for fresh-session creation, supported compaction observation,
  bootstrap, and restored-frontier readback must be proven independently. `CR-05` owns the
  supported-control evidence and `CR-06` owns the Claude retrofit.
- Live host authorization, UI focus, and session-lifecycle gaps remain evidence questions
  for `CR-04`, not reasons to weaken the frozen policy.

## Out of Scope

- Copying a full chat transcript into `HANDOFF.md` or treating transcript storage as the
  durable project record.
- Repurposing a handoff as ticket-autopilot scheduler state, a verification checkpoint, or
  merge authorization.
- Clearing a conversation while tools are active, before artifact validation, or because a
  best-effort counter drifted.
- Making the generic `handoff` skill implicitly model-invocable without an explicit policy
  decision and regression coverage for its privacy boundary.
- Claiming that message count measures tokens, cost, cache hits, or remaining context.
- Implementing the production controller during this Wayfinder pass.

## Frontier / Blocking Edges

- **Rollover policy** — accepted by the HITL interview and recorded in the decision spec;
  candidate validation and delivery remain with `CR-01`.
- **Codex tracer bullet** — blocked by `CR-01`. It must prove count → private handoff → new
  thread → bootstrap → ticket/run reconstruction with App Server and hook fallbacks. Owning
  ticket: `CR-02`.
- **Claude Code tracer bullet** — the CR-03 candidate covers the local stream JSON, hook,
  registry, and fresh UUID-bound simulated path without claiming transcript stability or a
  live provider boundary. Owning ticket: `CR-03`.
- **Supported Claude compaction controls** — CR-05 candidate complete. Official source,
  local parser surfaces, and isolated configuration loading are separated from unobserved
  provider-backed compaction effects. No global configuration changed. Owning ticket: `CR-05`.
- **Claude prototype retrofit** — CR-06 candidate complete. The flag, token fixture,
  validation rule, and process argument are gone; exact CR-05 capability input and visible
  early-compaction `no-go` behavior are covered by local regression tests. Owning ticket:
  `CR-06`.
- **Cross-host live proof** — next after CR-06 integration, HITL. One user-controlled run per host
  must establish the real clear/new-session boundary and expose any host UI, auth, or early
  compaction gap. Owning ticket: `CR-04`.

## Ticket Plan

| ID | Type | Mode | Blockers | Title | Expected output |
| --- | --- | --- | --- | --- | --- |
| `CR-01` | grilling | HITL | none | Freeze the rollover policy | Decision spec preserving the confirmed 150,000-token pending/safe-boundary policy and resolving message, task, registry, and fallback details |
| `CR-02` | prototype | AFK | `CR-01` | Prototype Codex rollover | Disposable App Server/hook tracer bullet with causal evidence and explicit limits |
| `CR-03` | prototype | AFK | `CR-01` | Prototype Claude Code rollover | Disposable stream-JSON/hook tracer bullet with causal evidence and explicit limits |
| `CR-05` | research | AFK | `CR-03` | Map supported compaction controls | Version-bound report separating official behavior, local help, and observed effects |
| `CR-06` | task | AFK | `CR-05` | Remove the autocompact dependency | Retrofitted Claude prototype, fixtures, tests, and docs with fail-closed early-compaction behavior |
| `CR-04` | live proof | HITL | `CR-02`, `CR-03`, `CR-06` | Prove cross-host rollover live | User-controlled observations and a production-design recommendation |

## Next Review

Integrate `CR-06`, then execute only the explicitly authorized `CR-04` live proof. The local
prototype frontier is otherwise closed: the fixed 150,000-token edge remains unchanged, and
an early compaction reports the host as incompatible instead of silently lowering it.
