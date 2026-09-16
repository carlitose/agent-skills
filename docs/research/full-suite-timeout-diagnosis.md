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
  true`, and the repository declares no `.gitattributes`; `README.md` is `35 114` bytes in
  the working tree against `34 485` bytes in the index (629 CRLF pairs).
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
