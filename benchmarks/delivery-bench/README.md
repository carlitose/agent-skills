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
  `runner.py amend-suite --lot L --scenario S --reason R` binds a corrected hidden suite to a
  bound lot on the record (old and new digest, reason); only between two `run-lot`, never a seed.
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
- `test_runner.py`, `test_profile_report.py`, `test_watch.py`: offline, with a fake Pi, a fake driver and a fake
  judge over real Git repositories.
