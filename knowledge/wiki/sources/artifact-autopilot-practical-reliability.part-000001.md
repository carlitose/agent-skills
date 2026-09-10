---
type: source-part
source_identity: artifact:autopilot-practical-reliability
source_digest: sha256:ebb7330dc5f516a4a6ce7838462e57c94884466744cea2581a3ef3fc40ed2203
source_entry: wiki/sources/artifact-autopilot-practical-reliability.md
---

# Preserved source — Part 2

Entry and provenance: [[sources/artifact-autopilot-practical-reliability]]

<!-- semantic-payload-v1: {"part_index":1,"payload_bytes":4682,"payload_sha256":"04d0d9c33799c3ac52957894e62062d0a65c648872ca93df1b8a7f451873fd36","schema":1,"source_digest":"sha256:ebb7330dc5f516a4a6ce7838462e57c94884466744cea2581a3ef3fc40ed2203","source_identity":"artifact:autopilot-practical-reliability"} -->
```markdown
## Semantic Invariants and External Boundaries
- Protect secrets and user-owned data; do not publish, delete, merge, or delegate through inferred permission.
- Keep implementation evidence bound to the exact candidate and retain separate integration state.
- Preserve literal payload bytes where the existing contract makes them identity-bearing.
- Maintain current Git/provider public behavior except for the specified portable paths, explicit bounded-execution failures, S9's provider-scoped encoding support, S10's portable binding semantics, and S11's native-I/O and exact recovery support. Preserve uncertain-mutation handling.
- Preserve atomic ledger persistence, valid replay, and rejection of invalid transitions.
- Keep the refactor wire-compatible with current CLI/event/schema contracts; compatibility is explicitly required for S6, not permission to add new aliases or migration infrastructure.

## Ticket Plan
| ID | Mode | Blocked by | Frontier | Scope | Outcome |
| --- | --- | --- | --- | --- | --- |
| APM-01 | AFK | — | Ready | S1 | Practical prompt defaults and explicit-user-only delegation |
| APM-02 | AFK | — | Ready | S2 | Portable final-tree receipt paths with real Git regression coverage |
| APM-03 | AFK | APM-02 | Dependency-blocked | S3 | Hermetic fixtures and explicit line-ending behavior |
| APM-04 | AFK | APM-03 | Dependency-blocked | S4 | One local quick/full test entry point with honest results |
| APM-09 | AFK | — | Ready | S9 | Provider-scoped strict JSON decoding with explicit encoding evidence |
| APM-05 | AFK | APM-09 | Dependency-blocked | S5 | Bounded Git/provider subprocesses preserving the provider decoding boundary |
| APM-06 | AFK | APM-04, APM-05 | Dependency-blocked | S6 | One smaller, testable final-tree workflow boundary |
| APM-07 | AFK | APM-01 | Dependency-blocked | S7 | Discoverable operational references and a smaller common prompt |
| APM-08 | AFK | APM-04, APM-05 | Dependency-blocked | S8 | Reproducible local phase/retry report using existing observations |
| APM-10 | AFK | — | Ready in follow-up queue | S10 | Portable wiki binding across computers and exact source checkouts |
| APM-11 | AFK | APM-10 | Dependency-blocked | S11 | Windows long-path delivery and exact pre-provider recovery |

APM-10/APM-11 live in `docs/tickets/wiki-portable-checkouts/` as a separate queued folder run. Do not amend the existing nine-ticket run's immutable source snapshot, add unresolved cross-folder dependency IDs, or start a second mutation in its worktree. Validate and locally commit only the new/updated planning sources before creating the follow-up tracked-source run. Queue creation is not ticket activation, implementation, or integration; the current request does not interrupt APM-01.

AFK means executable inline without an unresolved product decision; it is not subagent or merge authorization. Missing execution environments must be reported honestly. All implementation remains pending after this planning request.

## Verification Strategy
Each ticket owns a causal regression or observable document behavior and its focused checks. Establish the current baseline before comparing results. Re-run the recorded eight-module selection after the Windows fixes; use full-suite checks for runtime/refactor changes and the existing skill graph/context/forward checks for prompt changes. Do not claim POSIX or live-provider verification from Windows mocks. For timing/cancellation tests use disposable local processes and temporary repositories only.

## Alternatives and Non-Goals
- Reject a whole-engine rewrite: start with one vertical boundary and existing adapters.
- Reject another security/approval layer: apply the user's proportionality default.
- Reject default subagents: serial inline composition is the default.
- Reject suppressing failures, removing digest checks, or silently disabling projection.
- No new hosted CI, autonomous merge grant, live provider mutation, installed-Pi update, ad hoc historical ledger repair, or production optimization is authorized by this planning change. S11 specifies only an extension to the existing exact recovery transaction; using it later still requires its actual inputs.

## Next Review
After ticket emission, validate the canonical envelopes, dependency graph, and reciprocal artifact links. Invoke the owned post-batch hook once and preserve its result separately from the planning candidate. Register S10/S11 in a new tracked-source queue, report its ready frontier and wiki result, and leave the existing active run and terminal wiki record untouched. Any tracked wiki output is a separate generated candidate, not part of the planning commit.

```
