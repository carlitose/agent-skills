# Cross-host Context Rollover Prototypes

## Prototype frame

- **Questions:** Can the frozen CR-01 policy complete the count → handoff → fresh session
  → bootstrap → authoritative reconstruction path through both the Codex App Server and a
  Claude Code stream controller without granting hooks authority they have not
  demonstrated?
- **Branch:** Logic and protocol. Authenticated provider behavior, interactive UI, and
  cross-host proof remain owned by CR-04.
- **Codex binding:** `codex-cli 0.147.0`; generated App Server protocol v2 bundle SHA-256
  `babfd5c98cd978dd858b4762cdfbc9fba941e1a0e4053de0050e4082ae1f075a`.
- **Claude binding:** Claude Code 2.1.223 selected user-local binary
  `~/.local/bin/claude`; version and help output are content-bound in the fixture. The
  separate Homebrew binary `/opt/homebrew/bin/claude` is 2.1.17 and was excluded because
  its help surface lacks `--include-hook-events` and `--forward-subagent-text`.
  `--autocompact` is recorded only as rejected parser evidence and grants the controller no
  compaction authority.
- **Disposable boundary:** Nothing here is imported by an installed skill or production
  runner. Keep the learned contract; discard the tracer-bullet code after a production
  design is accepted.

## Run

```bash
python3 -B -m unittest discover \
  -s docs/prototypes/cross-host-context-rollover -p 'test_*.py'
```

The Codex fixture was derived with:

```bash
codex app-server generate-json-schema --experimental --out <private-temp-dir>
```

The Claude fixture binds the selected binary's local `--version` and `--help` output and
adds sanitized synthetic stream, status-line, and hook events. The committed fixtures
contain no credentials, session transcripts, provider output, or live token observation.

## Codex answer

The tracer bullet supports the controller route under the frozen policy:

- `thread/read` is always requested with `includeTurns: true`; one accepted `userMessage`
  counts as a user message, and only a terminal `agentMessage` counts as an assistant
  message. Commentary, tools, reasoning, plans, and compaction do not affect the diagnostic
  count. A phase-less item requires unambiguous completed-turn correlation or makes the
  assistant and total counts unavailable.
- Only `thread/tokenUsage/updated.params.tokenUsage.last.totalTokens` drives the threshold.
  `149999` remains monitoring, `150000` arms one pending generation, accumulated
  `tokenUsage.total` is ignored, and a model context window at or below `150000` is a visible
  configuration error.
- The controller holds a next prompt, waits for both `turn/completed` and the explicit
  owner to become terminal, then validates a private one-hour, workspace/source-bound,
  pointer-only handoff before any `thread/start` side effect.
- The local App Server boundary performs `thread/read` → `thread/start` → bootstrap
  `turn/start`; reconstruction reads the Wayfinder pointer, calls `ticket-list`, optionally
  calls `status`, and recovers the next frontier. The source thread stays readable.
- Registry selection uses workspace, adapter, digested source identity, and generation;
  repeated events are idempotent, separate sources do not collide, and consumption occurs
  only after readback and a sub-threshold target are observed.
- The held prompt is sent only after the bootstrap. Invalid, missing, expired, mismatched,
  consumed, malformed, or non-private handoffs fail before a fresh-thread call.

## Claude Code answer

The Claude tracer bullet supports the controller route under the frozen policy for the
selected 2.1.223 command surface:

- The prospective controller assigns its own durable event identities around `stream-json`
  observations; it does not require a provider `uuid` on user or result records. The
  projection counts only direct, non-replayed user inputs and unique terminal `result`
  events with subtype `success`. Partial chunks, tool traffic, hook events, forwarded
  subagent traffic, failures, and duplicate controller identities do not count.
- Status-line `total_input_tokens + total_output_tokens` is the only token trigger.
  Percentage fields, `current_usage`, cumulative cost, and `PreCompact` remain separate
  observations. `149999` monitors, `150000` arms, and an unusable context window fails
  configuration.
- The controller starts without a compaction-control argument. It enables stream, hook,
  partial, subagent-forwarding, replay, and explicit UUID flags so the noisy event classes
  are exercised by the projection rather than assumed absent. A binary advertising
  `--autocompact` still receives no upgrade from the exact CR-05 `unobserved` prevention
  classification.
- `PreCompact` before the fixed threshold returns visible `incompatible-host:no-go`, never
  arms a generation, and permanently prevents that source from claiming the 150,000-token
  route. Once a generation is pending, `PreCompact` and observation-only `PostCompact`
  preserve its identity without creating a session receipt or consuming a restore attempt.
- `Stop` plus a terminal semantic owner establishes the safe boundary. The private handoff
  is validated and the source session is proven resumable before a target UUID is persisted
  and dispatched.
- A lost start response reuses the same persisted UUID without consuming another bounded
  attempt. A definitely observed start failure advances the attempt and may allocate a new
  UUID. The handoff is consumed only after bootstrap receipt, Wayfinder/ticket/run
  reconstruction, and sub-threshold target readback.
- The synthetic target receives only the handoff path and reconstruction instructions;
  held user work is released only after restoration.

This is local and simulated evidence. It does not establish provider authentication,
actual hook dispatch, interactive focus, or the behavior of a real long-running Claude
session.

## Hook and interactive-clear experiments

The version-bound surfaces expose `SessionStart`, `Stop`, `PreCompact`, and `PostCompact`.
Synthetic fixtures show how they report or preserve controller state, but none proves fresh
session creation or bootstrap authority. `PreCompact` cannot arm below the policy threshold;
an early event makes the synthetic host visibly incompatible.

Claude's selected CLI exposes an explicit `--session-id` surface that the simulated
controller uses to model a fresh session. Its interactive `/clear` path has no equivalent
non-interactive flag in the observed help surface and was not driven headlessly; safe
interactive behavior remains a CR-04 observation. The same limitation applies to a
hook-only Codex clear/new route.

## Keep

- The exact App Server message projection and unavailable-on-ambiguity behavior.
- The current-context trigger and incompatible-window check.
- Validate-before-create ordering, private registry key, idempotent receipts, and one-shot
  consumption.
- Pointer-only bootstrap and authoritative readback before releasing a held prompt.
- UUID persistence before Claude dispatch and different treatment of ambiguous versus
  definitely failed creation.
- Explicit separation between controller, App Server, stream, hook-only, and live evidence.
- Exact consumption of CR-05's fail-closed capability record rather than inference from help
  text, environment variables, or hook documentation.

## Discard or defer

- `FakeAppServer`, `FakeClaudeProcess`, and every filesystem model in this directory after
  production adapters replace them.
- Authenticated or UI behavior, real `/clear`, live token claims, global hook installation,
  and production module boundaries; CR-04 owns those observations.

## Sources and limits

The protocol names and shapes were checked against the installed generated schema, the
current `/openai/codex` documentation, and the current `/anthropics/claude-code` and
`/websites/code_claude` documentation resolved through Context7. The fake boundaries prove
local controller ordering and rejection behavior only. They do not prove that a live host
grants the same session-management authority, that an interactive UI submits text, or that
provider-side state survives every transport failure. No prototype path sets or claims the
runtime effect of `DISABLE_COMPACT`, a blocking hook, or `/compact`.
