# delivery-bench (public harness)

Our private benchmark of *how* software is delivered: five arms, chains of 1, 3 and 8 requests,
three scenarios, a five-axis profile. The map is
[`docs/specs/delivery-bench-wayfinder.md`](../../docs/specs/delivery-bench-wayfinder.md) and the
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
      --arm bare --arm skills-only ... --repetitions 3 --jev-key-file K
  python -B runner.py prepare-drivers --lot L     # configuration-only driver copies
  python -B runner.py run-lot --lot L --through 1 --jobs 4
  python -B runner.py status --lot L
  ```

  A cell is extended, never replayed: `--through 3` after `--through 1` delivers requests 2-3.
  `run-lot --rep R --arm A` limits a run to some repetitions and arms (extra repetitions of a
  long chain). `runner.py judge-gated --lot L` judges apart the candidate a driver run left
  behind when it stopped on its semantic gate; it never counts as acceptance.
- `profile_report.py --lot L [--through N] [--rep R]` prints the five axes per request and per
  chain (robustness and compass on the final repository, cost and time summed), the driver
  outcomes, the paired acceptance comparison with `bare` (McNemar exact + Holm) with the TBA-03
  rule (provisional winner, arms that need another repetition) and the harness failures, without
  naming any hidden check. `--through N` reads chains of length N: cells brought to N requests.
- `test_runner.py`, `test_profile_report.py`: offline, with a fake Pi, a fake driver and a fake
  judge over real Git repositories.
