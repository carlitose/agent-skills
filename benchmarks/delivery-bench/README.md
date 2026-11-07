# delivery-bench (public harness)

Our private benchmark of *how* software is delivered: five arms, chains of requests (1, 3 and 8
in the first measurement), three scenarios, a five-axis profile. The map is
[`docs/specs/delivery-bench-wayfinder.md`](../../docs/specs/delivery-bench-wayfinder.md), the hard
regime (luna medium, complex systems, chains of 12) is
[`docs/specs/delivery-bench-hard-wayfinder.md`](../../docs/specs/delivery-bench-hard-wayfinder.md), and the
contract is [`docs/research/delivery-bench-oracle-contract.md`](../../docs/research/delivery-bench-oracle-contract.md).

Only the harness lives here. Requests, hidden suites, trap catalog and reference solutions live
in the private oracle repository, outside every checkout an arm can read.

- `judge.py` runs a scenario's hidden suite in a no-network container against a delivered
  project mounted read-only, and refuses the record if the project tree changed.
- `example/` is a public toy scenario that shows the formats (`scenario.json`, `hidden/`,
  `reference/`), with `hidden/dbench_checks.py`, the check registry every suite uses.
- `test_judge.py`: `python -B -m unittest test_judge` (offline);
  `DBENCH_LIVE_DOCKER=1` adds the container test on the example.
- `runner.py` hands one arm a scenario's requests in order, judges every delivery with
  `judge.py`, and writes a cell record per arm × scenario × repetition (usage and USD from the
  arm's own sessions, Jev apart, time, exit, timeouts, infrastructure retries, audit). Lots live
  outside Git and bind a human authority file by hash:

  ```
  python -B runner.py init-lot --lot L --lot-id ID --authority A --scenario NAME=PATH ... \
      --arm bare --arm skills-only ... --repetitions 3 --jev-key-file K \
      [--model openai-codex/gpt-6-luna --thinking medium --request-cap 5400 --chain-cap S]
  python -B runner.py prepare-drivers --lot L     # configuration-only driver copies
  # --source CHECKOUT copies from a clean agent-skills checkout and records its commit and tree
  python -B runner.py run-lot --lot L --through 1 --jobs 4
  python -B runner.py status --lot L
  ```

  Model, thinking and time caps belong to the lot (defaults: `gpt-6-sol`, `high`, 3600 s per
  request; `init-lot` refuses a request cap outside 1 s-24 h, the bound of the process capture);
  an authority that names a model binds the lot to it. A scenario sets its chain length
  (`requests`), the judge's `cpus`/`memory`/`pids` and, optionally, the driver's
  `driver_test_command`. Each request records Pi's compactions and their cost apart.
  A cell is extended, never replayed: `--through 3` after `--through 1` delivers requests 2-3.
  `run-lot --rep R --arm A` limits a run to some repetitions and arms (extra repetitions of a
  long chain). `runner.py judge-gated --lot L` judges apart the candidate a driver run left
  behind when it stopped on its semantic gate; it never counts as acceptance.
  Before judging, every request keeps `cells/<cell>/diffs/NN.diff`: that request's own changes
  (from the tree the previous one left), without `TASK.md`, read through a temporary index so the
  arm's repository is untouched. A Docker judge that does not answer is waited for like an outage
  (`judge-wait`); past the last wait the cell stops and the request stays `unjudged`, to be judged,
  not redone, on resume.
  When an attempt ends, before the judge, the runner removes every container, running or stopped,
  that bind-mounts something inside the arm's folder (the judge's own aside) and records them in
  the attempt's `stray_containers` (DBH-44): an agent's own `docker run` no longer outlives it.
  `runner.py amend-suite --lot L --scenario S --reason R` binds a corrected hidden suite to a
  bound lot on the record (old and new digest, reason); only between two `run-lot`, never a seed.
  `init-lot --vague` (DBH-38, an authority with `"variant": "vague"`) hands the Pi arms the short
  requests of each scenario's `requests-vague/` and the tool `ask_user` (`ask_user/index.ts`).
  `simulator.py` answers it with `--simulator-model` (default `gpt-6-sol`, `medium`) in a session
  of its own, from the chain's precise requests, never seeing the arm; the same question about
  the same request gets the same cached answer in every arm; at most 10 questions per attempt;
  an answer naming a hidden file or the canary is replaced. Questions and the simulator's cost
  are recorded apart from the arm's (`ask_user` in the request, `questions` and
  `simulator_cost_usd` in the ledger); a question it cannot answer makes the attempt
  `infra:simulator`. `preflight --lot-free --vague` asks it one real question per arm.
- `profile_report.py --lot L [--through N] [--rep R]` prints the five axes per request and per
  chain (robustness and compass on the final repository, cost and time summed), the driver
  outcomes, the paired acceptance comparison with `bare` (McNemar exact + Holm) with the TBA-03
  rule (provisional winner, arms that need another repetition), compactions per chain (their cost
  is in the chain's Pi USD) and the harness failures, without
  naming any hidden check. `--through N` reads chains of length N: cells brought to N requests.
  `--arm-from ARM=L2` (repeatable) reads that arm's cells from lot `L2` instead, for an arm
  re-measured in its own lot after a fix; the report names the source lot, and the other arms
  keep the version they were measured with.
- `watch.py` follows a lot while it runs and writes nothing. `cell --lot L --cell C` streams that
  cell's Pi sessions (messages, tool calls and results shortened, errors, cost per turn and per
  cell); `lot --lot L` refreshes the cell table and the spend against the authority's `caps.usd`
  (or its last amendment's); `open --lot L [--all] [--rep R]` opens one Windows Terminal window with
  the table and a tab per running cell, and elsewhere (or with `--print`) prints the commands.
- `test_runner.py`, `test_simulator.py`, `test_profile_report.py`, `test_watch.py`: offline, with a fake Pi,
  a fake driver and a fake judge over real Git repositories.


## Superpowers on Pi

`pi-superpowers` uses the same tools and `/goal` as `pi-tools`, plus the upstream Pi bootstrap
and only Superpowers skills. It does not load our mandatory workflow or discovered personal
skills. No companion subagent package is added: upstream's sequential fallback applies.
This measures Superpowers **on Pi**, not Claude Code.

Prepare a reviewed local snapshot of [obra/superpowers](https://github.com/obra/superpowers#pi)
without installing it into personal Pi settings. Pass `--superpowers-root PATH` to both
`preflight --lot-free --arm pi-superpowers` and `init-lot --arm pi-superpowers`; use
`--model openai-codex/gpt-6-luna --thinking medium` for the agreed comparison. Other arms
must not receive `--superpowers-root` unless the same invocation also selects `pi-superpowers`.
The runner does not download, install or update packages.

The snapshot's manifest, version, full content digest (excluding Git bookkeeping), skill
names and path are bound to the lot and every attempt. Missing/changed content refuses the
arm before Pi runs. Preflight requires exactly those skills, the tool profile and no
`ask-skills` routing. The upstream bootstrap is provider context, not JSONL history:
visible skills and an exit code do not prove that the model followed the methodology.
`SUPERPOWERS_DISABLE_TELEMETRY=1` disables the optional visual companion's telemetry.

Use fresh contemporary controls and the same scenarios/repetitions; do not treat historical
Luna or Opus scores as new matched observations. The initial four-arm, four-request measure
and its missing private-scenario gate are in
[the comparison spec](../../docs/specs/delivery-bench-superpowers-luna.md).
`test_superpowers_arm.py` exercises the integration offline; it does not call a model.

## Recover a frozen profile extension

Stop the lot before changing a binding. If an installed extension changed, prepare an
isolated copy of its **original folder**, including its siblings and original line endings.
Keep dependency resolution available outside that frozen folder; do not install or roll
back personal Pi. The replacement entrypoint must retain its original name and folder digest.

```bash
python -B runner.py relocate-extension --lot DIR \
  --source ORIGINAL_ENTRY --snapshot ISOLATED_ENTRY --reason "same-byte isolated recovery"
python -B runner.py run-lot --lot DIR --through 4 --jobs 4
```

The command writes `extension-relocations.json` and audit events through the existing runner.
It never edits `lot.json`, previous attempts, judgments or personal files. The sidecar binds
the original manifest/authority hashes, preserves address history, and replaces only the
physical address in every profile sharing that original entrypoint. All normal content
checks still run before publication and on every later load/attempt. Unknown bindings,
changed content, a different entrypoint name, stale/malformed metadata or active cell locks
refuse the operation. Repeating the same validated relocation is a no-op.

Publication uses the runner's atomic JSON writer. Audit events distinguish `prepared` and
`applied`; an IO failure remains a failure. A failed final audit append does not undo already
published metadata: inspect the sidecar and ledger rather than assuming rollback. Resume
only pending positions; infrastructure failures are not model scores.
`test_extension_relocation.py` covers this operation offline with fake Pi and real Git.
