---
ticket_schema: 1
ticket_id: "WFC-01"
execution_mode: AFK
blocked_by: []
---

# Guard the POSIX-only `fchmod` so adoption runs on both platforms

## Artifact Graph
- Artifact ID: `artifact:wfc-01-guard-fchmod`
- Role: `ticket`
- Parent: [llm-wiki-adoption-windows-fchmod.md](../../specs/llm-wiki-adoption-windows-fchmod.md)

## Parent Spec
[llm-wiki-adoption-windows-fchmod.md](../../specs/llm-wiki-adoption-windows-fchmod.md)

## What to Build

`adopt_catalog_file` raises on Windows before it can replace anything:

```
root_catalog.py:327  os.fchmod(handle.fileno(), stat.S_IMODE(details.st_mode))
AttributeError: module 'os' has no attribute 'fchmod'
```

Four tests already fail because of it, in two suites, all with the same error.

### The fix

A module-level flag plus a guard, copying `file_lock.py:24-26`, whose comment already explains why
a flag beats patching `os.name`:

```python
WINDOWS = os.name == "nt"
```

Then the single call at line 327 runs only when the platform has it.

**The POSIX path must come out byte-identical.** Same call, same descriptor, same mode, same
position in the sequence. This ticket fixes Windows; it does not buy Windows with POSIX.

The two later mode assertions stay exactly as they are. They keep working on Windows because both
files report the same mode there, which was measured before choosing this approach:

```
modo del file originale : 0o666
modo del file mkstemp   : 0o666
modo dopo os.replace    : 0o666
```

### The tests

Both branches must be exercised **on whichever machine runs the suite**, following
`test_platform_locks.py:30` and `:44`:

1. **POSIX branch, driven from any platform.** Patch the flag to `False` and fake `os.fchmod` with
   `mock.patch.object(..., create=True)`. Assert it is called once, with the descriptor of the
   temporary file and with `stat.S_IMODE` of the original. This is what proves POSIX was not
   traded away.
2. **Windows branch, driven from any platform.** Patch the flag to `True`. Assert `os.fchmod` is
   never called, the adoption completes, and the byte-exact readback still passes.
3. **Real platform, end to end.** On the machine running the suite, `adopt_catalog_file` completes
   and its report says `adopted`.

## Acceptance Criteria

- [ ] `llm-wiki/tests/test_root_catalog_adoption.py` goes from **3 errors to 0** on Windows, and
      `llm-wiki/tests/test_root_catalog.py` from **1 error to 0**. Before and after counts are
      reported.
- [ ] The POSIX branch test asserts `os.fchmod` is invoked with the temporary file's descriptor and
      `stat.S_IMODE(details.st_mode)`, and it passes on Windows through the faked module.
- [ ] The Windows branch test asserts `os.fchmod` is not invoked, and that the adoption still
      returns `status: adopted` with the readback intact.
- [ ] Causal proof: with the guard removed, the Windows test fails again with the same
      `AttributeError`, and the POSIX branch test **still passes**. Both outcomes are reported.
- [ ] `grep -rn fchmod` over `llm-wiki/scripts` and `ticket-autopilot/scripts` shows the call
      inside the guard and nowhere else.
- [ ] The diff does not touch: the byte-exact readback, the pre-commit comparison, the `os.fsync`
      calls, or the mode assertions. Shown by reading the diff, not asserted.
- [ ] `test_ingest_docs` (20) and `test_lint_wiki` (27) still pass, since they bound the fault.
- [ ] It is stated plainly that **no POSIX machine ran this**, and that the POSIX evidence is the
      spied call plus an unchanged statement.

## Out of Scope

- Continuous integration. That is `WT-07`, canceled by a human decision. This ticket records that
  its prediction held a second time; it does not reopen it.
- Any other platform-conditional path in `llm-wiki` or the runner.
- Using `os.chmod` on Windows to emulate the POSIX behaviour. Windows has no POSIX mode bits, and
  `os.chmod` does not accept a descriptor there. Measured: `os.chmod in os.supports_fd` is `False`.
- The stale-CRLF working copy found in `ocr-dotnet-api` while hitting this fault. Same family,
  different repository, no code change here.

## Notes

Found while executing `WCF-01` in `ocr-dotnet-api`, which cannot proceed until this lands: that
ticket's whole job is one call to `adopt_root_catalog.py`.

The oversight is provable and local. Fourteen lines below the failing call, the same function
already guards for Windows:

```python
os.replace(temporary, path)
if os.name != "nt":
    directory = os.open(path.parent, os.O_RDONLY)
```

The directory `fsync` is guarded, the `fchmod` is not, inside one function. That asymmetry is why
this is an oversight and not a POSIX-only design.
