---
type: source
title: "Catalog adoption cannot run on Windows: `os.fchmod` does not exist there"
identity_key: artifact:llm-wiki-adoption-windows-fchmod
identity_strength: stable
source_path: docs/specs/llm-wiki-adoption-windows-fchmod.md
source_digest: sha256:b86d800f04696fe8b6ea43d791a7f83f8cb55411b73febfdeabbfe67b090d858
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-09-08
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Catalog adoption cannot run on Windows: `os.fchmod` does not exist there

Compiled from `docs/specs/llm-wiki-adoption-windows-fchmod.md`. Identity is `artifact:llm-wiki-adoption-windows-fchmod`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-08** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"decisions":{"headings":[],"status":"not-identified"},"exclusions":{"headings":[],"status":"not-identified"},"goals":{"headings":[],"status":"not-identified"},"invariants":{"headings":[],"status":"not-identified"},"verification":{"headings":[],"status":"not-identified"}},"parts":[{"index":0,"path":"wiki/sources/artifact-llm-wiki-adoption-windows-fchmod.md","payload_bytes":6213,"payload_sha256":"b86d800f04696fe8b6ea43d791a7f83f8cb55411b73febfdeabbfe67b090d858"}],"payload_bytes":6213,"payload_sha256":"b86d800f04696fe8b6ea43d791a7f83f8cb55411b73febfdeabbfe67b090d858","schema":1,"source_digest":"sha256:b86d800f04696fe8b6ea43d791a7f83f8cb55411b73febfdeabbfe67b090d858","source_identity":"artifact:llm-wiki-adoption-windows-fchmod","source_kind":"spec"} -->

| Topic | Source sections |
|---|---|
| goals | no matching section identified in the source; complete source retained |
| exclusions | no matching section identified in the source; complete source retained |
| decisions | no matching section identified in the source; complete source retained |
| invariants | no matching section identified in the source; complete source retained |
| verification | no matching section identified in the source; complete source retained |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":6213,"payload_sha256":"b86d800f04696fe8b6ea43d791a7f83f8cb55411b73febfdeabbfe67b090d858","schema":1,"source_digest":"sha256:b86d800f04696fe8b6ea43d791a7f83f8cb55411b73febfdeabbfe67b090d858","source_identity":"artifact:llm-wiki-adoption-windows-fchmod"} -->
````markdown
# Catalog adoption cannot run on Windows: `os.fchmod` does not exist there

## Artifact Graph
- Artifact ID: `artifact:llm-wiki-adoption-windows-fchmod`
- Role: `diagnostic`

## Type
Diagnosis with a measured fault

## The fault

`adopt_catalog_file` cannot complete on Windows. Not sometimes: never.

```
File "llm-wiki/scripts/root_catalog.py", line 327, in adopt_catalog_file
    os.fchmod(handle.fileno(), stat.S_IMODE(details.st_mode))
AttributeError: module 'os' has no attribute 'fchmod'
```

Measured on this machine:

```
plataforma: win32 | os.name: nt
tiene fchmod: False
tiene chmod : True
os.chmod in os.supports_fd: False
```

`os.fchmod` is POSIX-only. On Windows it is absent from the module, so the call raises before the
atomic replacement ever happens. `os.chmod` exists but does **not** support a file descriptor
there, which is why a naive swap of one name for the other is not the fix.

## The module's own tests already fail

This is not an exotic call path. The suite that ships with the module fails on Windows today:

```
llm-wiki/tests/test_root_catalog_adoption.py     7 tests, 3 errors
  ERROR test_exact_agent_skills_legacy_fixture_has_the_frozen_digest_and_map
  ERROR test_cli_accepts_only_the_complete_explicit_map_and_replays
  ERROR test_file_adoption_is_atomic_mode_preserving_and_replay_writes_nothing

llm-wiki/tests/test_root_catalog.py              5 tests, 1 error
  ERROR test_tracked_legacy_catalog_requires_adoption_then_yields_a_stable_candidate
```

Four tests, two suites, one line. Every failure is the same `AttributeError`.

Two neighbouring suites are clean on the same machine, which bounds the fault:
`test_ingest_docs` 20 OK, `test_lint_wiki` 27 OK.

## Why it survived

There is no continuous integration in this repository. `WT-07`
(`docs/tickets/windows-text-fidelity/canceled/07-decide-and-introduce-ci.md`) proposed adding it
and was canceled. That ticket wrote its own epitaph:

> This is the gate underneath every other ticket on this map.
> The two regressions it shipped would each have been caught by a single suite run.

Four failing tests, sitting in the repository, invisible. This spec does not reopen that decision;
it records that the prediction held a second time.

## The oversight is local, and provable

Fourteen lines below the failing call, the same function already guards for Windows:

```python
os.replace(temporary, path)
if os.name != "nt":
    directory = os.open(path.parent, os.O_RDONLY)
```

The author knew the platform mattered here. The directory `fsync` is guarded; the `fchmod` is not.
That asymmetry inside one function is what makes this an oversight rather than a POSIX-only design.

`grep -rn fchmod` over `llm-wiki/scripts` and `ticket-autopilot/scripts` returns exactly **one**
line: `root_catalog.py:327`. The blast radius is a single statement.

## The precedent to follow

The repository already has a settled spelling for this, used in twelve places, including
`wiki_io.py:22` in this same package. But `file_lock.py:24` goes further, and its comment states
the reason directly:

```python
# other platform's path, which patching `os.name` itself cannot do without breaking every
# other consumer of that module in the process.
WINDOWS = os.name == "nt"
```

A module-level flag, so a test can drive **either** branch. `test_platform_locks.py:30` and `:44`
do exactly that, and fake the POSIX-only module with `mock.patch.object(..., create=True)`.

That is the pattern this fix must copy, because it is what makes both platforms testable on one
machine.

## Neither platform may be traded for the other

This is a hard requirement, not a preference. The fix must leave the POSIX path byte-identical and
must be proven so, not asserted.

On POSIX, `os.fchmod` must still be called with the same mode, from the same descriptor, at the
same point. On Windows it must be skipped, and nothing else may change.

### The measurement that makes skipping safe

Skipping `fchmod` could simply move the failure to the two later mode assertions. Measured on this
machine before deciding anything:

```
modo del file originale : 0o666
modo del file mkstemp   : 0o666
uguali: True
modo dopo os.replace    : 0o666
il readback passerebbe  : True
```

Windows reports the same mode for both files, so the pre-commit comparison and the final readback
assertion both still hold with the call skipped. Windows has no POSIX mode bits to preserve in the
first place.

## What must not change

- The byte-exact readback after `os.replace`, which raises `adopted root catalog readback differs
  from intent`.
- The pre-commit comparison that raises `root catalog changed before adoption could commit`.
- The `os.fsync` calls on the file itself.
- The mode assertion on POSIX, where `st_mode` is meaningful. The fix must not weaken POSIX to
  make Windows pass; it must skip only what Windows has no concept of.

## Scope

In:

- `root_catalog.py:327` on Windows.
- A test that fails on Windows without the fix and passes with it, and that keeps asserting mode
  preservation where mode exists.
- A test for the **POSIX** branch that runs on Windows too, by patching the module flag and faking
  `os.fchmod` with `create=True`, so the POSIX statement is proven to still be issued with the
  right mode.

Out:

- Continuous integration. That is `WT-07`, canceled by a human decision.
- Any other platform-conditional path in the package.
- The stale-CRLF working-copy problem found in `ocr-dotnet-api` while hitting this fault. Same
  family, different repository, and it needs no code change here.

## Not measured

- Whether `os.chmod(path, ...)` on Windows preserves anything useful. It is not needed by the fix
  and is deliberately not claimed.
- **No run on a real POSIX machine.** The POSIX branch is covered by driving the module flag and
  spying on a faked `os.fchmod`, which proves the statement is issued with the right descriptor
  and mode. It does not prove the kernel behaviour, which is unchanged because the statement is
  unchanged. Whoever has a Linux or macOS box should run the two suites once and say so.
- macOS. The flag is `os.name == "nt"`, so Darwin keeps the POSIX path, but no run on Darwin was
  performed.

````
