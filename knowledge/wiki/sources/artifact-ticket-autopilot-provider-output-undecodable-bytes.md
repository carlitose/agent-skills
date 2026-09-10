---
type: source
title: "Provider output carries bytes the runner refuses to read, after the mutation already landed"
identity_key: artifact:ticket-autopilot-provider-output-undecodable-bytes
identity_strength: stable
source_path: docs/specs/ticket-autopilot-provider-output-undecodable-bytes.md
source_digest: sha256:a1966581c1196ba3d59dc167c5d38800b5326ef0abc49577a4fa871bebe45a50
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-09-08
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Provider output carries bytes the runner refuses to read, after the mutation already landed

Compiled from `docs/specs/ticket-autopilot-provider-output-undecodable-bytes.md`. Identity is `artifact:ticket-autopilot-provider-output-undecodable-bytes`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-08** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"decisions":{"headings":[],"status":"not-identified"},"exclusions":{"headings":[],"status":"not-identified"},"goals":{"headings":[],"status":"not-identified"},"invariants":{"headings":[],"status":"not-identified"},"verification":{"headings":[],"status":"not-identified"}},"parts":[{"index":0,"path":"wiki/sources/artifact-ticket-autopilot-provider-output-undecodable-bytes.md","payload_bytes":7222,"payload_sha256":"a1966581c1196ba3d59dc167c5d38800b5326ef0abc49577a4fa871bebe45a50"}],"payload_bytes":7222,"payload_sha256":"a1966581c1196ba3d59dc167c5d38800b5326ef0abc49577a4fa871bebe45a50","schema":1,"source_digest":"sha256:a1966581c1196ba3d59dc167c5d38800b5326ef0abc49577a4fa871bebe45a50","source_identity":"artifact:ticket-autopilot-provider-output-undecodable-bytes","source_kind":"spec"} -->

| Topic | Source sections |
|---|---|
| goals | no matching section identified in the source; complete source retained |
| exclusions | no matching section identified in the source; complete source retained |
| decisions | no matching section identified in the source; complete source retained |
| invariants | no matching section identified in the source; complete source retained |
| verification | no matching section identified in the source; complete source retained |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":7222,"payload_sha256":"a1966581c1196ba3d59dc167c5d38800b5326ef0abc49577a4fa871bebe45a50","schema":1,"source_digest":"sha256:a1966581c1196ba3d59dc167c5d38800b5326ef0abc49577a4fa871bebe45a50","source_identity":"artifact:ticket-autopilot-provider-output-undecodable-bytes"} -->
````markdown
# Provider output carries bytes the runner refuses to read, after the mutation already landed

## Artifact Graph
- Artifact ID: `artifact:ticket-autopilot-provider-output-undecodable-bytes`
- Role: `spec`
- Children: [PUB-01](../tickets/ticket-autopilot-provider-output-undecodable-bytes/done/PUB-01-project-provider-payload.md)

## Type
Decision spec. It records a measured fault, kills one candidate remedy with evidence,
and leaves the policy half of the choice to a human. No production code changes.

## The fault, as observed

Delivering `WCF-01` in `ocr-dotnet-api` on Windows 11:

```
providers.py:1585  _execute_azure    -> az repos pr update ... --output json
providers.py:327   _run
finalizer.py:741   run
git_ops.py:109     stdout=_decode_data(raw_stdout).strip()
git_ops.py:89      return raw.decode("utf-8")
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xf3 in position 7812
```

The byte is not ours. It is field `.repository.project.description` of the JSON that
`az` prints:

```
'Proyecto para los micro servicios de backend que implementan la logica...'
                                                                    ^ 0xf3 = "o" acute, cp1252
```

That is the Azure DevOps *project* description. The runner does not write it, cannot
choose it, and cannot see it coming. Any organisation whose project description is not
pure ASCII breaks PR delivery on a host whose console codepage is not UTF-8, which is
every default-install Windows outside English locales.

## Why this is worse than a crash

The crash happened **after** the provider mutation succeeded. PR 24038 was created,
correct, with a body byte-identical to the one submitted. The ledger recorded nothing:
ticket `verified`, `pr: null`. A real PR was open and the run did not know it.

Retrying cannot help. The second attempt correctly found the existing PR, took the
idempotent `pr update` branch, and died at the same wall, because the undecodable byte
lives in project metadata that every readback carries. The run is not flaky; it is
**wedged**, permanently, on that host and that project.

Measured blast radius across the five `az ... --output json` call sites:

| operation | carries `.repository.project.description` | bytes > 127 |
|---|---|---|
| `pr list --source-branch` | no | 0 |
| `pr show` (full object) | yes | 1 |
| `pr show --query` (projected) | no | 0 |

## The existing policy is per-stream, and the gap is per-caller

`git_ops.py` already split the decision, deliberately and with reasons written down:

- `stdout` decodes strictly through `_decode_data`, because it is "SHAs, branch names,
  remote heads, config values. It feeds digests, equality checks, and
  `assert_cleanup_safe`, which decides whether a worktree may be deleted."
- `stderr` decodes leniently through `_decode_diagnostic`, because it "only ever reaches
  a human or a log."

That reasoning is sound and this spec does not reverse it. `WT-02` chose it on the record
after weighing exactly this trade-off.

The gap is that `SubprocessCommandRunner.run` serves **two different callers** through one
policy. For `git`, the premise holds: stdout is machine-shaped. For the provider CLI, it
does not: stdout is a JSON document embedding arbitrary human prose written by other
people, in whatever encoding the CLI happens to emit. The taxonomy is stream-shaped; the
fault is caller-shaped.

Note the asymmetry that makes provider stdout different from `assert_cleanup_safe`. A
`U+FFFD` in a worktree-deletion guard answers the wrong question **silently** and deletes
work. A `U+FFFD` in the PR-body readback makes the byte-exact comparison in `_validate_pr`
**mismatch loudly**. Same substitution, opposite blast radius. Lenient decoding is not
uniformly unsafe; it is unsafe exactly where a mangled value can still compare equal.

## One candidate remedy is dead, by measurement

"Make `az` emit UTF-8" does not work. `az.cmd` invokes Python in isolated mode:

```
AZ_INSTALLER=MSI ".../python.exe" -IBm azure.cli "$@"
```

`-I` implies `-E`, so the interpreter ignores the environment. Measured, all four
variants, byte unchanged:

```
sin nada          : 0xf3
PYTHONIOENCODING  : 0xf3
PYTHONUTF8=1      : 0xf3
ambas             : 0xf3
```

This is the same root cause that killed five environment-level workarounds during
`PBL-01`. It is recorded here so nobody spends that afternoon again.

## Options that remain

**A. Decode provider stdout leniently.** Route the provider CLI through
`_decode_diagnostic` while `git` keeps `_decode_data`. Cheap, closes the whole class.
Cost: a mangled byte inside a compared field becomes a loud mismatch instead of a loud
decode error. Argued above as acceptable for this caller and unacceptable for
`assert_cleanup_safe`, so the split must be per-caller and must not leak.

**B. Decode with the console codepage.** Lossless for today's byte, since every cp1252
byte maps to a character. Cost: it guesses. Guess wrong and you get mojibake inside a
value that is compared, which is the silent failure mode `WT-02` refused.

**C. Field-scoped strictness.** Decode the payload leniently, then re-derive the fields
that feed equality from the raw bytes strictly. Most faithful to the original reasoning,
most work, and needs a list of which fields are load-bearing.

**D. Ask the provider for less.** Add `--query` so the foreign prose never enters stdout.
Measured on `pr show`: full object 16 245 bytes with one undecodable byte, projected
object 4 200 bytes with none, and the fields the runner needs still present.

D is the cheapest and it is **not sufficient**. It removes today's byte, not the class:
`description` itself is a field the runner must read, a human can edit a PR body, and a
reviewer display name like `Jose` with an accent would arrive through the same door. D
shrinks the target. A, B, or C is what closes it.

## The decision required

Two questions, and only the first is mine to prepare:

1. Adopt D now, as harm reduction, at the five call sites. Mechanical and measurable.
2. Choose between A, B, and C for the class. This reopens ground `WT-02` settled and
   touches how the runner treats values it compares. It belongs to a human, after
   `grilling`, and not as a side effect of unblocking a delivery.

## What must not change

- `_decode_data` stays strict for `git` stdout. `assert_cleanup_safe` keeps its loud
  failure.
- `_validate_pr` keeps its byte-exact readback comparison. `PBL-01` bought that guarantee;
  nothing here may weaken it.
- The ASCII discipline for runner-authored bodies stays. This spec is about text the
  runner did not write.

## Scope
- In: the five `az ... --output json` call sites in `providers.py`; the decode policy for
  provider CLI stdout; a regression test that reproduces the byte.
- Out: changing `git` decode policy; changing `_validate_pr`; the `gh` provider, which has
  not been measured; reconciling ledgers already wedged by this fault.

## Not measured
- Whether `gh` exhibits the same fault. Untested, so unclaimed.
- Whether any other `az` operation embeds project metadata beyond the three in the table.
- Whether the wedged-run reconciliation path deserves its own remedy. Observed once, here,
  and repaired by hand.

````
