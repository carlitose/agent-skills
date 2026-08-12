---
ticket_schema: 1
ticket_id: "WT-01"
execution_mode: AFK
blocked_by: []
---

# Make the PR body round trip character-identical through the provider

## Artifact Graph
- Artifact ID: `artifact:wt-01-body-round-trip-fidelity`
- Role: `ticket`
- Parent: [windows-text-fidelity-wayfinder.md](../../specs/windows-text-fidelity-wayfinder.md)

## Parent Spec
[windows-text-fidelity-wayfinder.md](../../specs/windows-text-fidelity-wayfinder.md)

## What to Build
A PR body published through `az repos pr create` / `update` must read back **literally
equal** to the validated body. `finalizer.py:1103` compares with `!=`, so any lossy step in
the round trip opens a `delivery-pr-body` gate at `readback-validation`.

PR #78 correctly identified that `--description` is `nargs='+'` and must receive one
argument per line, but expanded it with `body.splitlines()`, which discards the body's
trailing newline. Instrumented at the failure site on CandidateRef `acd881c`:

```
expected len=419  tail='le --> Validate --> Publish --> Readback --> Revalidate\n```\n'
received len=418  tail='dle --> Validate --> Publish --> Readback --> Revalidate\n```'
```

One character. `splitlines()` additionally normalizes CRLF to LF and splits on `\v`, `\f`,
`\x1c`-`\x1e`, `\x85`, `U+2028` and `U+2029`, each of which breaks the same literal
comparison.

The test double hides this. `FakeAzureRunner` in `ticket-autopilot/tests/test_cli.py`
stores `command[command.index("--description") + 1]` — only the **first line**, which is
precisely the production truncation PR #78 set out to fix. The fake therefore models the
broken contract and cannot fail on it.

Two further argument-vector defects follow from the same expansion, reproduced against
`argparse` with `nargs='+'`:

- a body line of exactly `---` is parsed as an option: `unrecognized arguments: ---`;
- an empty body expands to zero arguments: `expected at least one argument`.

## Acceptance Criteria
- [ ] A body ending with a newline survives publish and readback with identical length and
      content.
- [ ] A body containing CRLF, `U+2028`, or a form feed survives unchanged, or is normalized
      once before both publish and comparison so the two cannot disagree.
- [ ] A body containing a line equal to `---` is delivered without an argument-parsing
      error.
- [ ] An empty body does not produce a zero-argument `--description`.
- [ ] `FakeAzureRunner` reconstructs the description from the whole argument vector, so it
      fails when production truncates.
- [ ] `test_azure_external_merge_requires_exact_sha_and_live_observation` and
      `test_autonomous_merge_gates_a_provider_without_atomic_expected_head` are green.

## Frontier
Ready. The remedy is already verified in a scratch clone: replacing `*body.splitlines()`
with `*body.split("\n")` at both call sites (`providers.py:1006` and `:1026`) and joining
the argument vector in the fake turns both tests green, and additionally fixes
`test_azure_external_merge_...`, which is red on base `d306799` with `[WinError 2]`.

## Step-by-Step Implementation Plan
1. Replace `*body.splitlines()` with `*body.split("\n")` at both `providers.py` call sites.
   `split("\n")` is the exact inverse of the `"\n".join()` that `az` documents
   ("Each value sent to this arg will be a new line"), so the round trip is an identity.
   Checkpoint: the two azure tests go green.
2. Guard the empty-body and `---` cases at the same boundary. Checkpoint: the argparse
   repro cases pass.
3. Update `FakeAzureRunner` to join `command[index("--description")+1 : index("--output")]`
   with `"\n"`. Checkpoint: reverting step 1 must make the tests red again — verify this
   explicitly, since a fake that cannot fail is worse than no fake.
4. Add a round-trip property test over the lossy inputs. Checkpoint: it fails against
   `splitlines()`.

## Testing Plan
Automated: the two named `test_cli` integration tests (simulated provider), plus a new unit
test asserting `"\n".join(body.split("\n")) == body` for bodies with a trailing newline,
CRLF, `U+2028`, `\f`, and empty content.

Unavailable boundary: no authenticated Azure DevOps organization is reachable, so real
`az --description` behaviour stays **modelled, never observed**. `FakeAzureRunner` is a
simulated double and no result obtained through it may be reported as live evidence. A
single live delivery with a trailing-newline body remains an open gate.

## Out of Scope
- The `errors` decoding policy, which is `WT-02`.
- The `.strip()` applied to `CommandResult`, which is `WT-05`.
- cmd.exe re-parsing markdown table separators, declared out of scope by PR #78 itself.
- Relaxing the literal comparison at `finalizer.py:1103`; the comparison is correct.
