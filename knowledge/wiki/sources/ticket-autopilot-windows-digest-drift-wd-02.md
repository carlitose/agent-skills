---
type: source
title: "Decode provider and Git command output as UTF-8"
identity_key: ticket:autopilot-windows-digest-drift/WD-02
identity_strength: stable
source_path: docs/tickets/autopilot-windows-digest-drift/done/02-fix-windows-provider-decoding.md
source_digest: sha256:9d1c593cd2ca2f429dfce5e1f6359c880c6ef1868e5116d1b59fd42b92b7b44a
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-11
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
run_id: 32822440c9894b5c
---

# Decode provider and Git command output as UTF-8

Compiled from `docs/tickets/autopilot-windows-digest-drift/done/02-fix-windows-provider-decoding.md`. Identity is `ticket:autopilot-windows-digest-drift/WD-02`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-11** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-autopilot-token-economics-wayfinder]]

## Run

Completed under autopilot run `32822440c9894b5c`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[6],"status":"present"},"exclusions":{"headings":[10],"status":"present"},"frontier":{"headings":[7],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[9],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-autopilot-windows-digest-drift-wd-02.md","payload_bytes":3777,"payload_sha256":"9d1c593cd2ca2f429dfce5e1f6359c880c6ef1868e5116d1b59fd42b92b7b44a"}],"payload_bytes":3777,"payload_sha256":"9d1c593cd2ca2f429dfce5e1f6359c880c6ef1868e5116d1b59fd42b92b7b44a","schema":1,"source_digest":"sha256:9d1c593cd2ca2f429dfce5e1f6359c880c6ef1868e5116d1b59fd42b92b7b44a","source_identity":"ticket:autopilot-windows-digest-drift/WD-02","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 6: Acceptance Criteria |
| testing | 9: Testing Plan |
| frontier | 7: Frontier |
| exclusions | 10: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3777,"payload_sha256":"9d1c593cd2ca2f429dfce5e1f6359c880c6ef1868e5116d1b59fd42b92b7b44a","schema":1,"source_digest":"sha256:9d1c593cd2ca2f429dfce5e1f6359c880c6ef1868e5116d1b59fd42b92b7b44a","source_identity":"ticket:autopilot-windows-digest-drift/WD-02"} -->
````markdown
---
ticket_schema: 1
ticket_id: "WD-02"
execution_mode: AFK
blocked_by: []
---

# Decode provider and Git command output as UTF-8

## Artifact Graph

- Artifact ID: `artifact:wd-02-fix-windows-provider-decoding`
- Role: `ticket`
- Parent: [Autopilot Token Economics](../../../specs/autopilot-token-economics-wayfinder.md)

## Type
Defect

## What to Build
`SubprocessCommandRunner.run` in `ticket-autopilot/scripts/autopilot/git_ops.py:41` calls
`subprocess.run(..., text=True)` without an explicit `encoding`. Python then decodes the
child process output with `locale.getencoding()`, which on this Windows machine is
`cp1252`. `gh` emits UTF-8. Any non-ASCII byte in provider output is therefore decoded
into the wrong characters.

The runner must decode provider and Git output as UTF-8 regardless of platform locale.

## Observed failure

Ticket TK-05 in run `7974966ec8d84a35` reached `verified`, delivery pushed
`b5fae4bab9a10e4cf53e6ffb638c16c2b1e4de22` and opened PR #54 with the correct body. The
`create-or-update-pr` readback then failed and opened a `delivery-pr-body` gate at phase
`readback-validation` with `provider receipt body contradicts validated delivery body`.

The PR body contained three em-dashes (U+2014). Measured:

- validated body artifact: 4830 characters, 4942 bytes on disk
- body stored on GitHub, read with an explicit UTF-8 decode: 4830 characters, identical
- same body read back through `SubprocessCommandRunner`: 4836 characters

4836 is exactly 4830 plus two extra characters for each of the three em-dashes, which is
what decoding 4836 UTF-8 bytes as a single-byte codepage produces. The content was never
wrong; only the decode was.

## Second site: the CLI's own JSON output

The same locale assumption applies in the other direction. When
`ticket-autopilot.py` output is redirected to a file on Windows, Python encodes stdout
with the locale codepage, so JSON containing non-ASCII is written as cp1252 and cannot be
read back as UTF-8:

```
UnicodeDecodeError: 'utf-8' codec can't decode byte 0x97 in position 13924
```

`0x97` is the cp1252 encoding of an em-dash. The CLI documents structured JSON as its
interface, so that JSON must be UTF-8 regardless of where it is redirected. Setting
`PYTHONIOENCODING=utf-8` works around it; the CLI should not depend on the caller doing so.

## Acceptance Criteria
- [ ] `SubprocessCommandRunner.run` decodes stdout and stderr as UTF-8 on every platform.
- [ ] The CLI writes its JSON output as UTF-8 regardless of the locale encoding and of
      whether stdout is a terminal or a file.
- [ ] A PR body containing non-ASCII characters survives the delivery readback comparison
      unchanged.
- [ ] A test fails if the runner is constructed without an explicit encoding.
- [ ] The behaviour is verified on Windows, where the locale encoding is not UTF-8.

## Frontier
Ready. No dependency and no decision remains. Related to `WD-01`, which is the
line-ending member of the same family: platform-dependent text handling silently breaking
an equality or digest check.

## Step-by-Step Plan
1. Pass `encoding="utf-8"` (and decide on `errors`) in `SubprocessCommandRunner.run`.
2. Check the other `subprocess.run` call sites in `git_ops.py` for the same omission.
3. Add a test that drives a non-ASCII payload through the runner.

## Testing Plan
A unit test that runs a child process emitting known non-ASCII UTF-8 bytes and asserts the
decoded string is character-identical to the source, plus a delivery-level test that a
non-ASCII PR body passes readback validation.

## Out of Scope
- The line-ending drift in ticket source digests, which is `WD-01`.
- The `.strip()` applied to stdout and stderr in the same method, which is a separate
  latent equality hazard and needs its own decision.

````
