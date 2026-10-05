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
