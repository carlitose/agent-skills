# Cross-host Context Rollover Prototypes

## Prototype frame

- **Question:** Can the frozen CR-01 policy complete a Codex count → handoff → fresh
  thread → bootstrap → authoritative reconstruction path against the installed App Server
  contract without granting hooks authority they have not demonstrated?
- **Branch:** Logic and protocol. Authenticated App Server, desktop UI, and cross-host proof
  remain owned by CR-04.
- **Version binding:** `codex-cli 0.147.0`; generated App Server protocol v2 bundle SHA-256
  `babfd5c98cd978dd858b4762cdfbc9fba941e1a0e4053de0050e4082ae1f075a`.
- **Disposable boundary:** Nothing here is imported by an installed skill or production
  runner. Keep the learned contract; discard the tracer-bullet code after a production
  design is accepted.

## Run

```bash
python3 -B -m unittest discover \
  -s docs/prototypes/cross-host-context-rollover -p 'test_*.py'
```

The fixture was derived with:

```bash
codex app-server generate-json-schema --experimental --out <private-temp-dir>
```

The committed fixture stores only sanitized synthetic events and hashes of the relevant
generated schema files. It contains no credentials, session transcripts, provider output,
or live token observation.

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

## Hook-only experiment

The installed hook surface exposes `PreCompact`, `PostCompact`, and `SessionStart`. In this
prototype they can preserve or report controller state and execute a controller-owned
command when invoked. They do not establish that a hook can issue `/clear`, create a fresh
thread, or submit a bootstrap with the required authority. `PreCompact` cannot arm below
the policy threshold. A full hook-only rollover therefore remains unproven.

## Keep

- The exact App Server message projection and unavailable-on-ambiguity behavior.
- The current-context trigger and incompatible-window check.
- Validate-before-create ordering, private registry key, idempotent receipts, and one-shot
  consumption.
- Pointer-only bootstrap and authoritative readback before releasing a held prompt.
- Explicit separation between controller, App Server, and hook-only evidence.

## Discard or defer

- `FakeAppServer` and every filesystem model in this directory after a production adapter
  replaces them.
- Authenticated or UI behavior, real `/clear`, live token claims, global hook installation,
  and production module boundaries; CR-04 owns those observations.

## Sources and limits

The protocol names and shapes were checked against the installed generated schema and the
current `/openai/codex` documentation resolved through Context7. The fake boundary proves
local controller ordering and rejection behavior only. It does not prove that a live Codex
host grants the same session-management authority, that a desktop deep link submits text,
or that provider-side state survives every transport failure.
