# Jev request shadow: log whether each user request is precise or vague

## Artifact Graph
- Artifact ID: `artifact:jev-request-shadow-spec`
- Role: spec
- Standalone: true
- Children: [JRS-01 Shadow extension](../tickets/jev-request-shadow/done/01-shadow-extension.md)

## Type and evidence
Feature, observation only. The user proposed using Jev to decide how to start each request
(2026-10-14) and chose the shadow mode ("1", answering "Sì, in osservazione").

An offline check on 2026-10-14 (`$TEMP/jevroute/`, about $0.0016 of Jev input) found:
- Jev's Noul "precise enough to implement and check without asking" separates the 36 precise and
  12 vague delivery-bench-hard requests at 0.4. A length rule does too, so that set is too easy.
- On 10 real short messages with one line of context, 7 of 10 were right. All 4 vague ones were
  right; 3 of 6 clear short follow-ups scored vague.
- Benchmarks give a solid signal only for vague requests (pi-full with grilling 12/36, bare
  `/goal` 7/36). Per-request choice between pi-tools and `/goal` is noise, so only "ask first or
  implement" is worth routing.

Real traffic is needed before Jev decides anything. Routing rules left to the model's judgment do
not fire reliably; a typed classifier would decide every time.

## Goal
1. A new extension `extensions/jev-request-shadow.ts`, listed in `package.json` `pi.extensions`.
   It never changes the input, the prompt or the tools.
2. Off by default. `/jev-shadow on`, `/jev-shadow off`, `/jev-shadow status`; the state lives in
   `<agent-dir>/agent-skills/jev-request-shadow.json`.
3. When on, for each user input from `interactive` or `rpc` (not `extension`), after stripping a
   leading `/skill:ask-skills `, skip blanks and anything else starting with `/` or `!`. Otherwise
   send one Jev request without waiting for it:
   - `POST https://api.typesafe.ai/v1/systemone`, model `jev-latest`;
   - state `{ context, request }`: `context` is the tail (1,500 characters) of the text of the
     last assistant message on the current branch, `request` the user text (first 4,000
     characters);
   - one Noul question, `request_precise`, with the wording of the offline check.
4. The key is `TYPESAFE_API_KEY` from the environment; on Windows, if absent, the user-level
   variable (`HKCU\Environment`). No key: nothing is sent and `status` says so.
5. Each answer or failure appends one JSON line to
   `<agent-dir>/agent-skills/jev-request-shadow.jsonl`: time, session id and file, request and
   context lengths, Noul, verdict (`precise` at ≥ 0.4, else `vague`), input tokens and latency,
   or a short error (`timeout`, `http <code>`, `invalid`). The message text is never written.
6. 8-second timeout, no retry. Any failure is logged and swallowed; it never reaches the turn.
7. `/jev-shadow report` summarizes the log: requests, precise and vague, errors, input tokens and
   estimated cost at $0.042 per million input tokens.

## Non-goals
- Acting on the verdict (routing to grilling, choosing an arm). A later spec decides that from the
  log.
- Questions other than precise or vague; pi-advisor.
- Loading it from the pi-personal-config bundle, which lists its extensions one by one.

## Failure modes
- A slow or failing Jev delays or breaks a turn: fire-and-forget with a timeout; the handler
  returns before the request ends.
- Private text leaks to disk: the log holds lengths and numbers only.
- Sending text without consent: off by default, on only by the user's command.

## Gates
- Attempt: the work up to merge, local sync and `/jev-shadow on` on this computer.
- Budget, time and maximum attempts: not set. Jev costs about $0.00004 per request.
- Approvals: the user agreed to send each request and the assistant's previous message tail to
  TypeSafe in shadow mode ("1", 2026-10-14). Merge and local sync follow the usual practice.
- Exact version: none.
- Existing blocks: none. Searched `package.json`, `extensions/`, `docs/specs/`.

## Verification
- Unit tests with a fake fetch: off sends nothing; on sends one request with the stripped text
  and the context tail; commands, `!`, blanks and extension input send nothing; a failure or
  timeout is logged and does not throw; the log has no message text; `report` counts lines.
- After local sync and reload: `/jev-shadow on`, one real request, one log line.
