# Terminal-Bench 4.0 — Pi y dos candidatos con Opus 5.5

## Artifact Graph
- Artifact ID: `artifact:terminal-bench-4-opus55`
- Role: `spec`
- Standalone: true

### Children
- [TBF-01](../tickets/terminal-bench-4-opus55/01-freeze-dataset-model-and-runtime.md)
- [TBF-02](../tickets/terminal-bench-4-opus55/02-bridge-four-arms-to-harbor.md)
- [TBF-03](../tickets/terminal-bench-4-opus55/03-run-the-authorized-pilot.md)
- [TBF-04](../tickets/terminal-bench-4-opus55/04-report-the-full-benchmark.md)

## Type and status
Decision and evaluation specification. **Preparation only**: no public-benchmark attempt has been launched. The earlier three-arm draft on branch `research/public-benchmark-frontier` at `5392e997` is historical research, not an integrated ticket source or authorization for the revised experiment.

## Decision and objective
Compare **Pi bare, Pi skills-only, ticket-driver c1a and ticket-driver c3a** on the exact same Terminal-Bench 4.0 tasks using Anthropic Claude Opus 5.5. First run a 3-task, one-attempt-per-arm pilot (12 starts), then assess whether the full dataset is feasible before authorizing any full-run lot. For the full benchmark, the user chose **three attempts per task per arm**, to match the intended public-index method. Measure completed and failed attempts, verified task result, model usage and cost, active time, code/test deltas where applicable, and task coverage. A valid harness run is not the same as a passing task. No publication to a leaderboard is authorized.

Official model documentation at `https://platform.claude.com/docs/en/docs/about-claude/models/overview` lists API ID **`claude-opus-5-5`**, base prices **$4/input MTok and $20/output MTok**. Account-specific availability is still unverified. The benchmark's official site (`https://www.tbench.ai/`) shows Terminal-Bench 4.0; the exact immutable Harbor Hub dataset ref and task manifest **have not been verified**. Do not assume the old draft's `@4.0.0` spelling or its 66-task count without registry readback. Harbor's official `BaseAgent` contract executes the agent loop outside the task container through `environment.exec`; an example in the repository documentation is not proof that Pi's tool calls are sandboxed.

## Authorization and budgets
- **Pilot lot only:** the user explicitly authorized 3 fixed tasks × 4 arms = **12 starts**, including c1a/c3a only for this batch, with a **cumulative $250 maximum**, including every failed or gated start and any applicable benchmark usage. No automatic retry and no replacement of a failed start. This is a scoped exception to the ongoing skills-only suspension; it does not authorize the old ticket-autopilot runner or a later ticket-driver lot.
- **Entire project ceiling:** the user selected **$1,000 cumulative**, including the pilot and failures. This is a spending ceiling, **not permission to launch full-benchmark lots**. Each full-run lot requires its own explicit authorization after pilot evidence and a cost projection. Stop before a start that cannot stay within the remaining authorized budget; do not silently change models, arms, task selection or attempt count.
- The user selected **local Docker** and allowed starting its daemon for preparation. At discovery, Docker CLI 29.5.2 was installed but the Linux engine did not respond; Harbor was not installed. Package installation and runtime changes must be scoped to the isolated benchmark setup, not to unrelated Pi installs. No model request, Docker start, Harbor install or benchmark run has occurred yet.
- No secret values in specs, tickets, logs or task containers. Verify the actual process environment inherited by external agents and child Pi leaves before any live request. Any Jev-dependent c3a path must have a legitimate project-specific permission and keep its key only in the driver, not in Pi leaves or the container; if that binding is absent, stop rather than substituting a different c3a.

## Invariants and fairness
1. Freeze one versioned Harbor dataset manifest, three pilot task identities, task environment, exact Opus model ID, provider, thinking setting and agent tool exposure before the first live start. All four arms receive the same task text, limits and number of attempts. Distinguish the benchmark's public score from a locally reproduced result with a different harness.
2. Pi's actual file and shell operations must target only the task sandbox through Harbor's environment, never the host checkout. The host holds model credentials; the task container cannot read them. The same permitted task capabilities must be observable for every arm. Any unavoidable degradation is recorded before a run; do not count a degraded arm as equivalent.
3. c1a/c3a require a faithful normalized-ticket and Git boundary. Prove that ordinary Terminal-Bench tasks can be adapted without changing the task contract or granting extra context. If they cannot, stop and report incompatibility rather than generating artificial success or silently dropping hard tasks.
4. Fix the attempt ledger before spending: stable task/arm/attempt identities; distinguish `started`, `gated`, `failed`, `valid` and task pass/fail. Reserve against remaining budget and reconcile model cost from original usage. Unknown cost is not zero. Stop on an ambiguous outcome; never silently retry. Pilot results remain pilot results and are not retroactively promoted into full-run replicates after changing any binding.
5. Prefer three fixed CPU-compatible tasks for the pilot; enumerate every task requiring unavailable GPU and report exclusions. Do not replace a missing task without recording the change. Report incomplete coverage, rather than comparing a partial run as if it were the full benchmark.
6. The full-run plan is three independent attempts per task per arm on the frozen dataset. Before each authorized lot, compare the observed pilot cost with remaining $1,000; if it will not cover the intended set, seek a new human decision or report a partial benchmark honestly. No automatic continuation after the pilot.

## Slices and verification
- **TBF-01:** resolve the exact registry ref and task count, prove Docker runtime, inspect model accessibility without generating a paid completion, and freeze the pilot manifest. If a technical probe requires paid API usage, charge it to the authorized pilot only after attributable cost accounting is ready. Record source versions and credential-handling plan.
- **TBF-02:** implement one Harbor-to-Pi adapter and four bounded arm variants; demonstrate in a local no-paid smoke that tool calls remain in the sandbox, return trajectories and support billing receipts. A live `hello-world` call counts against the authorized pilot only if explicitly included in its twelve starts; otherwise use a no-model test. Fail closed on parity loss or leaked credentials.
- **TBF-03:** after TBF-01/02 and authority readback, launch at most the 12 authorized attempts under the $250 pilot cap. Record each result, spend and stop, and determine whether the full benchmark is feasible. No implicit rerun of a gated task.
- **TBF-04:** request a *new* exact full-run lot authorization; run only within the cumulative $1,000 ceiling and reduce the observed data to task success, coverage, active time and model costs. If pilot evidence shows the cap cannot cover the full design, stop for a human budget/scope decision. Publish results only to a local report; no leaderboard publication.

Evidence levels remain separate: offline adapter tests, local no-model smoke, live pilot and authorized full run. Each claim cites the matching immutable run and dataset identity. The completion of a documentation or adapter ticket does not imply that a paid benchmark ran.
