---
type: source
title: "Pi Messenger between live Pi sessions on Windows"
identity_key: artifact:pi-multi-session-messenger-live
identity_strength: stable
source_path: docs/research/pi-multi-session-messenger-live.md
source_digest: sha256:acc28083f116336205427a7dc9c3a9181f9f527bd4f604a6ddc45a88a8c45421
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-10-05
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Pi Messenger between live Pi sessions on Windows

Compiled from `docs/research/pi-multi-session-messenger-live.md`. Identity is `artifact:pi-multi-session-messenger-live`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-05** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/ticket-pi-multi-session-wayfinder-pms-01]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"evidence":{"headings":[3],"status":"present"},"findings":{"headings":[],"status":"not-identified"},"limitations":{"headings":[],"status":"not-identified"},"method":{"headings":[],"status":"not-identified"},"question":{"headings":[],"status":"not-identified"}},"parts":[{"index":0,"path":"wiki/sources/artifact-pi-multi-session-messenger-live.md","payload_bytes":2631,"payload_sha256":"acc28083f116336205427a7dc9c3a9181f9f527bd4f604a6ddc45a88a8c45421"}],"payload_bytes":2631,"payload_sha256":"acc28083f116336205427a7dc9c3a9181f9f527bd4f604a6ddc45a88a8c45421","schema":1,"source_digest":"sha256:acc28083f116336205427a7dc9c3a9181f9f527bd4f604a6ddc45a88a8c45421","source_identity":"artifact:pi-multi-session-messenger-live","source_kind":"research"} -->

| Topic | Source sections |
|---|---|
| question | no matching section identified in the source; complete source retained |
| method | no matching section identified in the source; complete source retained |
| findings | no matching section identified in the source; complete source retained |
| evidence | 3: Evidence |
| limitations | no matching section identified in the source; complete source retained |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2631,"payload_sha256":"acc28083f116336205427a7dc9c3a9181f9f527bd4f604a6ddc45a88a8c45421","schema":1,"source_digest":"sha256:acc28083f116336205427a7dc9c3a9181f9f527bd4f604a6ddc45a88a8c45421","source_identity":"artifact:pi-multi-session-messenger-live"} -->
```markdown
# Pi Messenger between live Pi sessions on Windows

## Artifact Graph
- Artifact ID: `artifact:pi-multi-session-messenger-live`
- Role: `research`
- Parent: [PMS-01 live two-session check](../tickets/pi-multi-session-wayfinder/01-live-two-session-check.md)

## Answer

On this native Windows host, with `pi-messenger@0.15.2` and three live Pi sessions opened by the
human (2026-10-05, all in the agent-skills main checkout), messages, wake-up, `leave` and dead-session
cleanup work. Reservations work only for the literal path string that was reserved: the same file
written through its absolute path was not blocked. Messages are therefore usable for announcements;
reservations cannot protect files between sessions, least of all across worktrees.

## Evidence

Sessions: NiceIce (this operator session), NiceUnion and VividNova, model `claude-opus-5-5`.

| Check | Result |
|---|---|
| `join`, `list` | Observed: all three listed with project `agent-skills`, branch `main`. |
| `send` NiceIce → NiceUnion | Observed: NiceUnion woke without polling and replied; the reply woke NiceIce with sender name, both in under a minute. |
| `reserve "pms01-probe.txt"` by NiceIce, `write` by VividNova on the same relative path | Observed: blocked, message names NiceIce, branch and reason. |
| Same file through `C:/Users/CGS03/Projects/agent-skills/pms01-probe.txt` | Observed: **not blocked**, the file was written. |
| `release`, then `write` again | Observed: succeeded. |
| `reserve` then `leave` by VividNova | Observed: reservation released and registration removed within 4 s; feed records `release` and `leave`. |
| NiceUnion `reserve "pms01-crash.txt"`, then terminal window closed with X | Observed: within about a minute the process was dead, the registration gone and a `write` of that path from NiceIce was not blocked; the feed has no `leave` event. Exact latency not measured. |
| Same file across two worktrees | Not run; inferred from the absolute-path bypass and `lib.ts` `pathMatchesReservation` (literal string match). |

Side effect observed: Messenger writes `.pi/messenger/feed.jsonl` inside the repository working tree,
and `.gitignore` does not exclude `.pi/`.

## Unknowns

- Behavior with sessions in different repositories, and with `scopeToFolder`, was not tested.
- Messages are not authenticated (any local writer of the inbox can forge one); not tested here.

## Next Step

PMS-03: confirm the protocol with the human. Use Messenger only to announce (claim, done, merged,
blocked); use the pushed-branch claim from PMS-02; do not rely on reservations; decide whether to
ignore `.pi/` in the repository.

```
