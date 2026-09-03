# Final-Tree Observation, Parity, and Rollback Evidence

## Artifact Graph
- Artifact ID: `artifact:delivery-revalidation-observation-parity-result`
- Role: `research`
- Standalone: true

## Status and Claim Ceiling

FTV-04 controlled evidence passes for the production observer, enabled transaction, scheduler,
ledger, provider-head binding, and terminal-proof contracts delivered through FTV-03. This is a
logical correctness result, not a wall-time, token, provider-savings, or universal performance
claim. The frozen matrix uses disposable repositories and deterministic provider fakes; those
checks are labeled simulated and grant no provider or merge authority. The retained FTV-03
provider observation is live readback from its already completed delivery, but this harness
performs no provider mutation.

The result is an enablement prerequisite only. It does not itself change the default, complete
FTV-05, authorize integration, apply the wiki, synchronize local Pi, clean a checkout, update Pi,
or reload an active session.

## Exact Retained Inputs and Report

Run-relative paths are under
`.git/ticket-autopilot/runs/delivery-revalidation-final-tree-validation-20260902/artifacts/`.

| Artifact | Exact path | SHA-256 |
|---|---|---|
| Controlled FTV-03 fixture | `ftv-04-forward-fixture-bc623532801cfd8e8b7c2276df06505ee25fa58c8f6914b1f8763e7aca67b599.json` | `bc623532801cfd8e8b7c2276df06505ee25fa58c8f6914b1f8763e7aca67b599` |
| Normalized parity/matrix/rollback report | `ftv-04-forward-report-8ebf78be5cbd674925d490715066f36dd95a6803f2f01868355d673521a72502.json` | `8ebf78be5cbd674925d490715066f36dd95a6803f2f01868355d673521a72502` |
| Fresh FTV-03 D-focused checks | `ftv-03-delivery-focused-f2b2.log` | `9c25e51cc55abd9176d369b8751808ef46f1d558da150d0d10018283ebc56d0a` |
| Fresh FTV-03 D full suite | `ftv-03-delivery-full-suite-f2b2.log` | `a8432e540b7b554f3270f7d965394f5d0d2633667855c00e382e55d9f2b7fb6b` |
| Fresh FTV-03 D extension suite | `ftv-03-delivery-extension-f2b2.log` | `9b993932741c05ea3fb26b51fb32d8b0665bab61efe86b77878f969a3ab6d9f2` |
| Fresh FTV-03 D context/static result | `ftv-03-delivery-context-static-f2b2.log` | `273a5e3dded02003d86e1b7e3b1fb72809351cf864ca3bd3f65166cb66c3ae1e` |
| Final D verification bundle | `ftv-03-delivery-verification-bundle.json` | `0d3325d043adf98d8fa720b6742858b43dd0d8137e3882566439592ac609a3af` |

Two complete harness runs produced byte-identical normalized report bytes and the same report hash.
The report contains logical labels and counts only; scratch paths and command runtimes are absent.

## Controlled Observation-to-Delivery Identity

The source trace is FTV-03:

- base tree: `a1fe170565c64d0d6ae3067da80e75367414a053`;
- implementation tree `I`: `e995c74ad05645474b9475b3fa6489d57f7e4a00`;
- authoritative delivery tree `D`: `f2b2de06345ea1b644f32293aaf478e1e35af474`;
- provider head: `b0a981687aee72747c049345e9ef92f47239f15d`;
- terminal merge commit: `96494d36732466a772548c93b6dafaa8bba342b9`;
- observation manifest digest: `50f96273065a3b40b1da6edffcbf5c51d3a07619dac09aac1de80ea7060d7d2b`;
- observation digest: `c6ea95d583200827960f081ba32db64982dc5fff3ebff4ffe93eeaac76c41cb4`;
- effect digest: `5065bfb86bc1c00dee222bcf58484b8685fad321c3663b26042561420c3507d1`;
- receipt SHA-256: `2bc583433b2639528e273e5f193abb41cdd8c75869b2a77c9dedf0968324f709`;
- link-closure digest: `c4c3fef3bb230b5dac28a8fd42a7e6c60b9550da8d958ff001e622ae6c2f0876`.

The production observer planned exactly four effects and exact `D`. Comparing that manifest with
the authoritative tracked delivery returned `parity` with no discrepancy. Observe and enabled
manifests had identical implementation/delivery CandidateRefs, ticket identity, receipt, link
closure, effects, raw no-renames diff, and negative proof. The enabled transaction reached the
same `D`, bound all three checkpoints, and exact final replay returned `already-applied`.

The D-bound Verification Record, rendered body, provider readback, provider head, and terminal
proof all bind the same CandidateRef and tree. Fresh `main` reachability contains the exact provider
head, and the terminal tree equals `D`. The provider body SHA-256 is
`27a78a963689cf89665e62450a33abd00265f32ecaad2b52e34ca5f03e65231d`;
the provider-observation digest is
`cbdb7d7801ba0ed1a40643b63c5a6f1e28c40334b71033a6e130a6a33a74c7e1`;
the terminal-proof digest is
`2a2edafd961d00fa64689c2e98525aee9760e380915bf25dcde0fe09aeda02d5`.

## Frozen Logical Matrix

The retained harness ran five command groups comprising 29 logical tests. All outcome classes
passed:

- narrow positive and exact observer/authoritative parity;
- recoverable transaction checkpoints and exact replay;
- full-path preflight fallbacks;
- extra-path/blob/mode/receipt/link, stale-identity, reconciliation, provider, and other
  fail-closed classifier/parity blockers;
- historical ledgers with no reconstructed projection configuration;
- same-`D` final-stage failure and semantic-drift restart;
- provider-head and fresh terminal lineage;
- all adjacent authority-separation checks.

The broader retained D evidence independently records 120 focused checks, 747 Ticket Autopilot
checks with one platform-only skip, six mandatory-extension checks, 14 context/token-reduction
checks, compilation, diff validation, and clean exact tree identity. These are logical counts, not
cost or speed measurements.

## Rollback Result

A new `off` selection rejects a new projection with the explicit `mode` exclusion. In the same
controlled trace, an already persisted version-1 enabled intent remains authoritative after that
selection, completes exact `D`, binds `projected-not-integrated`, and returns `already-applied` on
final replay. The later default therefore neither deletes nor rewrites in-flight state. Any
contradiction still blocks under the recorded transaction contract.

Historical ledgers with absent projection configuration remain absent and use the established full
path. Switching a default changes only new-run configuration; it grants no authority to infer a
manifest or quality checkpoint for historical state.

## Limits Carried into FTV-05

- The matrix does not establish a speedup or lower token consumption.
- Deterministic fake-provider checks are simulated and non-authoritative.
- The live FTV-03 provider readback establishes only that exact completed head/body lineage.
- The controlled context upper bound remains `178,255` bytes against the unchanged `176,903`
  ceiling, an explicit `1,352`-byte excess rather than observed runtime consumption.
- The historical FTV ledger's missing projection configuration, terminal wiki `broken-binding`,
  failed local Pi drift check, and separate cleanup/reload gates remain literal.
- FTV-05 must validate the exact integrated FTV-04 completion handoff before changing the default.
