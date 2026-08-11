---
ticket_schema: 1
ticket_id: "WD-01"
execution_mode: AFK
blocked_by: []
---

# Make ticket source drift detection line-ending consistent

## Artifact Graph

- Artifact ID: `artifact:wd-01-windows-digest-drift`
- Role: `ticket`
- Parent: [Autopilot Token Economics](../../../specs/autopilot-token-economics-wayfinder.md)

## Type
Task

## Observed Defect
On a CRLF checkout every `resume` fails with a false source-drift error, so the runner is
unusable on Windows. Two digest functions disagree about what a ticket's identity is:

- `ticket_contract.py:246` reads the ticket with `Path.read_text()`, whose universal-newline
  decoding translates CRLF to LF, and `:257` hashes that decoded text. The result becomes
  `Ticket.digest` and is surfaced as the manifest `content_digest` at `ticket_source.py:194`.
  The manifest's stored body accordingly contains no `CR`.
- `ticket_lifecycle.py:34` hashes raw file bytes with `Path.read_bytes()`, which preserves
  CRLF.

The normalization is therefore implicit in text-mode reading rather than deliberate, which is
why the two sides drifted without either looking wrong in isolation.

`assert_ticket_source_state` compares the second against the first. For observed ticket
`TK-01` the ledger recorded `cf71d924dc0571b5d35e477657761b2a89dd45545dd2ccea47b3988a1105bb69`
while the raw-bytes digest of the same untouched file was
`55fdaa410e0c3626f3b2fe98b75f25091120931acb1907fcf3ba2654af2e8dbb`. The files were CRLF
because `ticket-emit` writes in text mode on Windows.

Rewriting the files with LF endings made all nine digests match and unblocked the run, which
confirms line endings are the only difference. That workaround is not a fix.

## What to Build
One consistent notion of ticket source identity, so a pure line-ending difference is not
reported as content drift while any real content change still is.

The canonical digest is the identity the rest of the system already uses: the ledger records
it, the snapshot manifest stores canonicalized content, and CandidateRef binds it. The
lifecycle recheck is the inconsistent side and should compare the same canonical digest
instead of raw bytes. `ticket-emit` should additionally write deterministic LF endings so an
emitted ticket is byte-reproducible across platforms.

## Acceptance Criteria
- [ ] A regression test reproduces the CRLF case and fails before the fix.
- [ ] `resume` succeeds on a CRLF checkout with unmodified ticket files.
- [ ] A real content change is still detected as drift, including whitespace-only edits that
      survive canonicalization.
- [ ] A disposition change is still detected independently of content.
- [ ] `ticket-emit` writes LF endings deterministically on every platform.
- [ ] Existing ledgers whose recorded digest predates the fix are handled explicitly, either
      by remaining valid or by requiring an audited explicit migration. Silent
      reinterpretation of a recorded digest is not acceptable.
- [ ] No change weakens CandidateRef binding, snapshot immutability, or the source
      containment rules.

## Frontier
Ready. Independent of the token-economics measurement work, but discovered by it and
currently blocking any Windows run.

## Step-by-Step Plan
1. Add the failing regression test for a CRLF checkout.
2. Make the lifecycle recheck use the canonical digest that the ledger already records.
3. Make `ticket-emit` write LF deterministically.
4. Decide and implement the compatibility path for pre-existing ledgers.
5. Confirm genuine content and disposition drift are still detected.

## Testing Plan
Fixtures covering a CRLF checkout, an LF checkout, a real content edit, a whitespace-only
edit, a disposition change, and a pre-existing ledger digest. Assert that only the genuine
changes gate.

## Out of Scope
- Normalizing files the runner does not own.
- Relaxing snapshot immutability or CandidateRef binding to make the check pass.
- Repairing the unrelated pre-existing Windows path-separator test failures.
