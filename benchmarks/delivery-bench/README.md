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
