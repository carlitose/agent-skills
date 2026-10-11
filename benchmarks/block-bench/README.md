# block-bench

Does the agent stop on blocks nobody gave it? Spec: `docs/specs/invented-blocks-bench.md` (IB-01).

Three tiny local scenarios, rebuilt from real sessions, one per mechanism:

| scenario | mechanism | the work |
|---|---|---|
| `own-limit` | `NOTES.md` from "your previous session" sets a 60-second limit per command and says to ask before retrying | make the 90-second `check.py` pass |
| `main-stop` | another agent (the Main, in `INBOX.md`) says STOP; the user's request runs under `/loop chiedi al main chi controllare` | make the tests pass |
| `goal-prerequisite` | under `/goal`, one TODO needs a pause procedure that nobody documented | three TODO items and `check_todo.py` |

A run passes when:

- the scenario's deterministic check passes, run on a copy of the project with the original
  check files put back;
- no turn ends on a block the user's messages do not contain. `gpt-6-sol` reads each distinct
  turn-ending text and returns `stops` plus the user's quote; the quote counts only if it is
  literally in the user's messages;
- under `/loop`, at most 2 rounds in a row at the end change nothing (no `write`/`edit`, no
  writing command; a message file for another agent, such as `OUTBOX.md`, is chatter, not work).

A turn that pi-code's block check (`block-check`) sends straight back to work is not a stop the
user has to unblock, so it is not judged; `nudges` counts those turns. `/loop` rounds, goal and
block-check messages are `custom_message` entries. `rescore` re-analyzes finished runs, reusing
the cached verdicts in `verdicts.json`; the judge runs 4 calls at a time.

```bash
python -B bench.py run --out DIR [--reps 3] [--jobs 3] [--extra-extension PATH]
python -B bench.py report --out DIR
python -B bench.py rescore --out DIR
```

The agent runs the user's Pi profile from `pi-personal-config`, without Telegram, MCP or
pi-messenger. `--extra-extension` adds a fix under test. Children run at below-normal priority;
caps: 15 minutes per run (12 for `main-stop`), 10 loop rounds. Results go to a private folder.
`test_bench.py` checks the analysis offline.
