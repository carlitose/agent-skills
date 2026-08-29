# Ticket Autopilot Ledger History Size Diagnostic

## Artifact Graph

- Artifact ID: `artifact:ticket-autopilot-ledger-history-size-diagnostic`
- Role: `spec`
- Standalone: true

### Children

- [Store ledger history as verifiable state deltas](../tickets/ticket-autopilot-ledger-history-size/01-store-history-as-verifiable-state-deltas.md)

## Diagnosis Report - lens: repro-first

### Root cause

Every ledger history event embeds a complete deep copy of the entire current run snapshot.
`Kernel._seal_history()` does this for every event appended by a transaction, while the event
hash includes that full snapshot. As tickets accumulate delivery receipts, PR bodies, leaf
results, and evidence references, each later event repeats all prior state. File growth is
therefore approximately the sum of every historical snapshot: quadratic in state growth rather
than proportional to the actual changes.

### Evidence

- Run `f74e8975ae4d49a5` is 75,768,207 bytes. Its history is 75,405,778 bytes across 477 events;
  the current snapshot is about 327,742 bytes and event metadata without snapshots is about
  148,030 bytes.
- The same run stores about 75,286,400 bytes of snapshot bodies. Content-addressing only exact
  duplicates would not solve the problem: 464 of 477 snapshots are unique and their unique
  bytes still total about 73,233,819.
- Run `fts-selector-integrity-20260829` has one ticket and 48 events, yet its ledger is 988,180
  bytes because history repeats about 934,250 bytes of snapshots while current state is only
  about 39,058 bytes.
- Run `cr-autocompact-removal-20260829` is 11,863,682 bytes with 161 history events. Older runs
  in the same repository reach roughly 18 MB, 59 MB, and 75 MB.
- A status read of the 75 MB ledger takes about 1.45 seconds locally versus about 0.21 seconds
  for the one-ticket ledger.
- `Kernel._seal_history()` deep-copies every ledger field except `history` into each new event;
  `AtomicLedger._validate()` then reloads and validates every copy.

### Feedback loop built

A deterministic fixture can append growing ticket, leaf, and delivery state, serialize both
the existing full-snapshot history and a compact history, and compare byte growth while
replaying every transition to the exact final snapshot and original event hashes.

### Fix location and approach

Keep the first checkpoint snapshot, then encode later event state as deterministic structural
deltas from the previous reconstructed snapshot. Dictionary changes use path-bound set/remove
operations; append-only list growth uses append operations; non-append list changes fail safely
to an explicit replacement. The stored event keeps its existing `previous_hash` and `hash`.
Validation replays the delta, reconstructs the full snapshot, hashes the original virtual event
shape containing that snapshot, and applies the existing transition validator. A changed delta
that changes state therefore cannot match the original event hash.

Support a full-snapshot prefix followed by a compact suffix so existing schema-4 ledgers remain
readable and newly appended events can be compact immediately. Provide an explicit, atomic
compaction command that first validates an existing ledger, replaces historical snapshot bodies
with equivalent deltas, validates the reconstructed original hash chain, and preserves the
current snapshot, event sequence, previous hashes, event hashes, and history head.

### Alternatives ruled out

- Removing history is invalid because it destroys the append-only audit trail.
- Truncating PR bodies or evidence opportunistically changes audit content and does not address
  the repeated-snapshot multiplier.
- Compressing the whole JSON file reduces disk size but forces full decompression and parsing on
  every status/resume and complicates atomic access.
- Content-addressing exact snapshots has little leverage because nearly every snapshot is unique.
- Rehashing a rewritten history would create a new audit chain instead of proving equivalence to
  the original one.

### Confidence: high

Measured byte attribution and the sealing code agree: repeated full snapshots dominate the file,
and event metadata plus current state are two orders of magnitude smaller in the largest run.

## Current Behavior

The append-only audit semantics are correct, but a growing snapshot is copied into every event.
Large histories consume tens of megabytes and make every ledger load, status, resume, and save
parse and validate the repeated state.

This is runner state, not application data and not an OpenRouter-key issue. Provider output and
PR-body material already admitted to the ledger remain governed by existing sanitization rules.

## Target Invariants

- Event sequence, event details, previous hashes, original event hashes, and history head remain
  unchanged by compaction.
- Replaying the compact history reconstructs every exact historical snapshot and the exact final
  persisted state.
- Any semantic patch corruption fails the original event-hash check.
- Existing full-snapshot schema-4 ledgers remain readable without migration.
- A full-history prefix may transition once to a compact suffix; compact history never falls back
  to embedded full snapshots.
- Compaction is explicit and atomic for an existing ledger; failed validation leaves the source
  byte-for-byte unchanged.
- Evidence, PR bodies, approvals, CandidateRefs, gates, and receipts are preserved, not truncated.

## Verification Strategy

- Unit tests for deterministic diff/apply over dictionaries, appended lists, replacements,
  removals, escaped keys, empty patches, and corrupt operations.
- Ledger tests proving legacy full history and compact history reconstruct identical snapshots
  and retain the same original hash chain.
- Migration tests for atomic success, idempotence, corruption rejection, and unchanged source on
  failure.
- Growth regression with an expanding multi-ticket fixture; compact serialization must remain
  proportional to changes and materially below the full-snapshot baseline.
- Complete ticket-autopilot suite and forward-test matrix remain green.

## Non-goals

- Deleting or weakening audit history.
- Automatically rewriting existing user ledgers during ordinary status or resume.
- Changing evidence classification, provider sanitization, or secret-handling policy.
- Optimizing unrelated artifact directories.

