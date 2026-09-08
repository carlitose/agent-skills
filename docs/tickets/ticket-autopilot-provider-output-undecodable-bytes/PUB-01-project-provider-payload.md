---
ticket_schema: 1
ticket_id: "PUB-01"
execution_mode: AFK
blocked_by: []
---

# Ask Azure for the seven fields the runner reads, not the whole object

## Artifact Graph
- Artifact ID: `artifact:pub-01-project-provider-payload`
- Role: `ticket`
- Parent: [ticket-autopilot-provider-output-undecodable-bytes.md](../../specs/ticket-autopilot-provider-output-undecodable-bytes.md)

## Parent Spec
[ticket-autopilot-provider-output-undecodable-bytes.md](../../specs/ticket-autopilot-provider-output-undecodable-bytes.md)

## What to Build

Option D of the parent spec, and only option D. The decode-policy question (A, B, C)
is a human decision and is explicitly out of scope here.

`az repos pr show` returns the full PR object, which embeds
`.repository.project.description`. On a non-UTF-8 console that field's bytes reach
`_decode_data` and raise, after the PR mutation has already landed. The runner never
reads that field. It reads exactly seven, all of them in `_azure_state_receipt` and
`_azure_state`:

```
pullRequestId
sourceRefName
targetRefName
lastMergeSourceCommit.commitId
lastMergeCommit.commitId
description
status
url
```

Add a `--query` projection so only those reach stdout. Measured on PR 24038:

```
full object      : 16 245 bytes, 1 byte > 127  -> UnicodeDecodeError
projected object :  4 200 bytes, 0 bytes > 127 -> parses
```

The dangerous part is not writing the projection. It is that the projection can silently
drift from what the reader consumes: someone adds `document.get("mergeStatus")` to
`_azure_state_receipt`, the projection does not include it, and the field arrives `None`
instead of raising. So the projection must be **derived from a single declared field set**
that both the query and the reader use, and a test must fail if a consumed field is not
projected.

## Acceptance Criteria

- [ ] A single module-level declaration lists the projected fields. The `--query`
      argument is built from it, not hand-written twice.
- [ ] `_azure_view` requests the projection. The five `az ... --output json` call sites
      are reviewed and each either projects or is documented as not needing it
      (`pr list --source-branch` measured clean; `pr policy list` unmeasured).
- [ ] A regression test feeds a recorded full-object payload containing byte `0xf3` in
      `.repository.project.description` and asserts the current code path raises, then
      asserts the projected payload does not. The byte must appear in the test as a byte,
      not as a character, so the test does not depend on the file's own encoding.
- [ ] A drift test asserts that every field `_azure_state_receipt` and `_azure_state`
      read is present in the declared projection. It must fail if a field is added to the
      reader and not to the declaration.
- [ ] `_validate_pr` keeps its byte-exact readback comparison, unchanged. Prove it with
      the existing tests in `test_provider_pr_body.py`, which must stay green.
- [ ] `_decode_data` and `_decode_diagnostic` are not touched. `git` stdout stays strict.
- [ ] Causal proof in both directions: with the projection removed the new test fails;
      with it in place it passes; and the guardian tests pass either way.

## Out of Scope

- Options A, B and C of the parent spec. Choosing between lenient decoding, codepage
  decoding, and field-scoped strictness reopens `WT-02` and needs `grilling` plus a human
  decision. Do not decide it here, and do not decide it implicitly by making the decode
  path lenient "while you are in there".
- The `gh` provider. Unmeasured, therefore untouched.
- Reconciling ledgers already wedged by this fault. Repaired by hand once; if it recurs it
  earns its own ticket.
- Changing the Azure DevOps project description. It is not ours, and depending on it
  staying ASCII is the bug, not the fix.

## Notes

Do not attempt to make `az` emit UTF-8. Measured dead: `az.cmd` runs
`python.exe -IBm azure.cli`, `-I` implies `-E`, and the interpreter ignores
`PYTHONUTF8` and `PYTHONIOENCODING`. All four variants leave the byte at `0xf3`. This is
the same wall that defeated five environment-level workarounds in `PBL-01`.

This ticket reduces the target; it does not close the class. `description` is itself a
projected field, a human can edit a PR body, and an accented reviewer display name would
arrive through the same door. Say so plainly in the PR body rather than claiming the
fault is fixed.
