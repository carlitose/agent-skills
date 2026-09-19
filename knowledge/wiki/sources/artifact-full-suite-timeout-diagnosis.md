---
type: source
title: "Why the full local profile stalls on Windows"
identity_key: artifact:full-suite-timeout-diagnosis
identity_strength: stable
source_path: docs/research/full-suite-timeout-diagnosis.md
source_digest: sha256:cf1c9620c820851bcdceb79d4c2597fd7972e4a01cb8b9fe072aad4c88fba870
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-09-16
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Why the full local profile stalls on Windows

Compiled from `docs/research/full-suite-timeout-diagnosis.md`. Identity is `artifact:full-suite-timeout-diagnosis`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-16** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-windows-text-fidelity-wayfinder]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"evidence":{"headings":[3],"status":"present"},"findings":{"headings":[],"status":"not-identified"},"limitations":{"headings":[],"status":"not-identified"},"method":{"headings":[],"status":"not-identified"},"question":{"headings":[],"status":"not-identified"}},"parts":[{"index":0,"path":"wiki/sources/artifact-full-suite-timeout-diagnosis.md","payload_bytes":4424,"payload_sha256":"cf1c9620c820851bcdceb79d4c2597fd7972e4a01cb8b9fe072aad4c88fba870"}],"payload_bytes":4424,"payload_sha256":"cf1c9620c820851bcdceb79d4c2597fd7972e4a01cb8b9fe072aad4c88fba870","schema":1,"source_digest":"sha256:cf1c9620c820851bcdceb79d4c2597fd7972e4a01cb8b9fe072aad4c88fba870","source_identity":"artifact:full-suite-timeout-diagnosis","source_kind":"research"} -->

| Topic | Source sections |
|---|---|
| question | no matching section identified in the source; complete source retained |
| method | no matching section identified in the source; complete source retained |
| findings | no matching section identified in the source; complete source retained |
| evidence | 3: Evidence |
| limitations | no matching section identified in the source; complete source retained |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":4424,"payload_sha256":"cf1c9620c820851bcdceb79d4c2597fd7972e4a01cb8b9fe072aad4c88fba870","schema":1,"source_digest":"sha256:cf1c9620c820851bcdceb79d4c2597fd7972e4a01cb8b9fe072aad4c88fba870","source_identity":"artifact:full-suite-timeout-diagnosis"} -->
```markdown
# Why the full local profile stalls on Windows

## Artifact Graph

- Artifact ID: `artifact:full-suite-timeout-diagnosis`
- Role: `research`
- Parent: [Windows Text Fidelity at the Provider Boundary](../specs/windows-text-fidelity-wayfinder.md)

## Answer

`npm run test:full` never hung. It ran 95 checks strictly serially through `spawnSync`, gave
one flat `--timeout-seconds` allowance (default `300`) to every check, and printed nothing
while a check was running. Three checks cost far more than that allowance, so each of them
sat silent for five minutes and was then `SIGKILL`ed and reported as
`errored — spawnSync python ETIMEDOUT`, which reads exactly like a hang and is
indistinguishable from a real defect.

The cost is real, not a deadlock. The killed checks finish when they are allowed to:
`test_worktree_gc.py` completed `OK` in **771 s** under load, and `test_cli.py` was still
progressing normally at 899 s with 15 of its 101 cases done. The per-case cost is dominated
by process creation on Windows: one representative case,
`test_cli.CliTests.test_autonomous_first_mutation_gates_if_merge_mode_changes_after_eligibility`,
takes **96 s** and starts **357 child processes** — 250 `_command_supervisor.py` launches,
90 `git rev-parse` calls, and 2 full CLI runs.

A second, independent family of reds was hidden behind those timeouts: every check that
compares working-tree bytes with Git object bytes fails on a normal Windows checkout,
because Git's installer default `core.autocrlf=true` gives the working tree CRLF while the
index keeps LF.

## Evidence

- `scripts/test-local.mjs` (pre-change) — `spawnSync` in a `for` loop over `plan.selected`,
  one `timeout: (options.timeoutSeconds ?? 300) * 1000` for every check, output buffered
  until the child exits.
- Instrumented full run, Windows 11 / Node 24.15.0 / CPython 3.12.10, 22 CPUs:
  `succeeded 81, failed 5, errored 8, skipped 1` in **63.9 min**; `test_cli.py`,
  `test_worktree_gc.py` and `autopilot-forward-matrix` each ended at exactly `300 011 ms`
  with `signal=SIGKILL`; `test_ticket_sources.py` survived at `284 446 ms`, i.e. 5 s under
  the cliff.
- Isolated reruns: `test_worktree_gc.py` → `OK (skipped=1)` at 771 s;
  `test_cli.py` → 15 cases in 899 s, several single cases above 100 s;
  `autopilot-forward-matrix` → still running after 35 min (32 scenarios, each a separate
  `unittest discover` process, several of them heavy `test_cli` integration cases).
- Spawn census for one case (patched `subprocess.Popen`): `357` spawns, `19` distinct
  command shapes, `250 ×` `python -I -S -B .../autopilot/_command_supervisor.py`,
  `45 ×` `git rev-parse --show-toplevel`, `45 ×` `git rev-parse --git-common-dir`.
- Interpreter cost per CLI launch, same machine: `0.61 s` with `-B` (as the tests launch it)
  versus `0.32 s` with a warm bytecode cache, against `0.09 s` of bare interpreter startup.
- `git config --show-origin --get core.autocrlf` → `file:C:/Program Files/Git/etc/gitconfig
  true`, and the repository declares no `.gitattributes`; `README.md` was `35 114` bytes in
  the working tree against `34 485` bytes in the index (629 CRLF pairs). The observing
  checkout has since set `core.autocrlf=false` repository-locally, which is an operator
  configuration, not a repository declaration.
- `os.DirEntry.stat()` on Windows reports `st_dev=0, st_ino=0`, so
  `zero_to_autopilot._read_regular_file` rejected every file it scanned
  (`inventory file changed during scan: README.md`).
- `subprocess.run(..., text=True, input="100644 blob <oid>\tfile.txt\n")` reaches
  `git mktree` as `file.txt\r`, producing a different tree than the one the reconciliation
  proposal names.

## Unknowns

- POSIX wall-clock cost is unobserved; every number here is Windows-only.
- The 250 supervisor launches per case are inherent to the current command-capture design.
  Whether that design can be cheaper without weakening process-tree containment is not
  answered here.
- `autopilot-forward-matrix` has no observed complete serial duration; it was stopped, not
  finished.

## Next Step

Bound and parallelize the profile instead of raising one flat allowance: chunk long
unittest files and the forward matrix into separately bounded invocations, run them across
shard processes with streamed per-check durations, and keep wall-clock-bounded suites
serial. Then repair the byte-fidelity family the timeouts were hiding.

```
