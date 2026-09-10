---
type: source
title: "Runner-Defect Issue Escalation Prototype"
identity_key: artifact:runner-defect-issue-escalation-prototype
identity_strength: stable
source_path: docs/prototypes/runner-defect-issue-escalation/NOTES.md
source_digest: sha256:57681cbc550889f18d3b0f4ec37ee782a9084994ec97b13faa589f267b2eb725
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-08-29
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Runner-Defect Issue Escalation Prototype

Compiled from `docs/prototypes/runner-defect-issue-escalation/NOTES.md`. Identity is `artifact:runner-defect-issue-escalation-prototype`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-29** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/ticket-ticket-autopilot-runner-defect-issues-rd-02]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"assumptions":{"headings":[2],"status":"present"},"decision":{"headings":[],"status":"not-identified"},"limitations":{"headings":[8],"status":"present"},"question":{"headings":[2],"status":"present"},"results":{"headings":[],"status":"not-identified"}},"parts":[{"index":0,"path":"wiki/sources/artifact-runner-defect-issue-escalation-prototype.md","payload_bytes":6248,"payload_sha256":"57681cbc550889f18d3b0f4ec37ee782a9084994ec97b13faa589f267b2eb725"}],"payload_bytes":6248,"payload_sha256":"57681cbc550889f18d3b0f4ec37ee782a9084994ec97b13faa589f267b2eb725","schema":1,"source_digest":"sha256:57681cbc550889f18d3b0f4ec37ee782a9084994ec97b13faa589f267b2eb725","source_identity":"artifact:runner-defect-issue-escalation-prototype","source_kind":"prototype"} -->

| Topic | Source sections |
|---|---|
| question | 2: Prototype frame |
| assumptions | 2: Prototype frame |
| results | no matching section identified in the source; complete source retained |
| limitations | 8: Limits |
| decision | no matching section identified in the source; complete source retained |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":6248,"payload_sha256":"57681cbc550889f18d3b0f4ec37ee782a9084994ec97b13faa589f267b2eb725","schema":1,"source_digest":"sha256:57681cbc550889f18d3b0f4ec37ee782a9084994ec97b13faa589f267b2eb725","source_identity":"artifact:runner-defect-issue-escalation-prototype"} -->
````markdown
# Runner-Defect Issue Escalation Prototype

## Artifact Graph

- Artifact ID: `artifact:runner-defect-issue-escalation-prototype`
- Role: `prototype`
- Parent: [RD-02 Prototype fingerprinted issue escalation](../../tickets/ticket-autopilot-runner-defect-issues/done/02-prototype-fingerprinted-issue-escalation.md)

The active ticket source is runner-bound by digest. Its reciprocal evidence link lives in the
parent Wayfinder rather than mutating the ticket during execution.

## Prototype frame

- **Question:** Can normalized runner-defect eligibility, a stable fingerprint, an orthogonal
  local sidecar, exact-marker deduplication, and crash replay guarantee at most one fake issue
  without network access or mutation of run state?
- **Branch:** logic. The uncertainty is a validation, persistence, and state-machine contract.
- **Assumption:** a diagnosed producer supplies the exact RD-01 allowlisted record and a
  read-only validated run binding; the fake adapter can distinguish conclusive from
  inconclusive exact-marker absence.
- **Useful result:** deterministic tests reject unsafe inputs before adapter work, preserve the
  protected run projection byte-for-byte, and reduce RD-03 to explicit authority and lifecycle
  choices rather than unresolved mechanics.

This folder is disposable. Production code must not import it.

## Run

```bash
python3 -B -m unittest discover \
  -s docs/prototypes/runner-defect-issue-escalation -p 'test_*.py'

python3 -B docs/prototypes/runner-defect-issue-escalation/runner.py
```

The runner prints a deterministic no-network transcript. Tests use only the Python standard
library, temporary directories, an atomic JSON sidecar, process-local plus OS file locking, and
a stateful fake issue adapter.

## Answer

The model supports the narrow design with a conservative boundary:

- strict shape validation accepts only `runner-defect`, runner-owned symbols, high confidence,
  deterministic reproduction plus source trace, at least one `local-deterministic` evidence
  item, lowercase SHA-256 artifacts, and an applied redaction contract;
- project/candidate failures, expected gates, provider/environment failures, unsupported
  configurations, user/input errors, lower confidence, unknown fields, raw output, secrets,
  absolute paths, volatile identities, Markdown passthrough, authority data, and malformed or
  unbound ledgers stop before search, create, or durable capture;
- sorted-key UTF-8 JSON over the RD-01 projection produces one fingerprint across changed
  symptoms, evidence order, and excluded runtime context, while owner, code, phase, and
  invariant changes split fingerprints;
- one per-fingerprint lock and atomic sidecar serialize equivalent concurrent reports;
- every path searches the exact marker before create, open and closed matches are terminal
  deduplication receipts, and the fake exposes no comment, reopen, label, or close operation;
- reservation, search, dispatch intent, published receipt, deduplication receipt, retryable
  failure, terminal failure, and ambiguous dispatch survive replay;
- a crash before fake dispatch can create once only after a conclusive absent observation; a
  lost response or crash after fake creation recovers by exact search and never sends a second
  create; inconclusive recovery remains `dispatch-ambiguous`;
- final replay returns the exact persisted bytes and performs no adapter call;
- `tickets`, `gates`, `effects`, verification leaves, delivery, PR, merge policy/grant, and
  ledger history remain byte-identical on success, rejection, crash, and replay.

## Keep

- The exact allowlisted diagnostic record and validate-before-fingerprint ordering.
- SHA-256 over the narrow stable projection and exact hidden marker.
- A dedicated issue adapter with only exact search and create capabilities.
- The orthogonal content-addressed sidecar, per-fingerprint lock, atomic write/readback, and
  search-before-create replay protocol.
- Explicit `dispatch-ambiguous` state and conclusive/inconclusive absence distinction.
- Byte-comparison of protected run projections and adapter call-count assertions.

## Discard

- All Python in this directory after RD-03 freezes policy and RD-04 encodes the accepted
  production contract.
- Synthetic provider modes, fixture issue numbers, process-local lock registry, presentation
  wording, and the prototype's temporary directory layout.
- Any assumption that a fake result, AFK mode, merge grant, gate approval, or local filesystem
  access confers issue-write authority.

## RD-03 decisions exposed by the prototype

1. **Grant scope and identity:** per run, per repository, or separately revocable reusable
   authority; actor/evidence binding; whether a grant may outlive the originating run.
2. **Expiry and revocation:** duration, consumption count, revocation event, and behavior for
   an already reserved or ambiguous dispatch.
3. **Claim threshold:** retain the prototype's high-confidence plus deterministic/local-source
   threshold or authorize a narrower alternative; lower confidence is currently rejected.
4. **Closed issues:** keep the prototype's no-op deduplication receipt, or require a separate
   human action for any reopen or follow-up. Automatic reopen/comment is not modeled.
5. **Outbox ownership:** final Git-common path, repository/run binding, retention, garbage
   collection, corrupt-sidecar recovery, and pre-ledger behavior.
6. **Retry semantics:** which search/create failures are terminal, who can declare absence
   conclusive after ambiguous dispatch, and whether manual reconciliation is mandatory.
7. **Presentation contract:** stable title/body fields, labels, and whether evidence digests may
   be externally visible; these are not authority inputs.

## Limits

- No network, provider CLI, credential, GitHub behavior, issue mutation, production import, or
  runner integration is exercised.
- The fake's conclusive absence bit is an explicit oracle. RD-04 must not infer it from one
  empty text search.
- Local atomic replace and locks are exercised on one host, not across distributed filesystems.
- Secret checks prove an allowlisted/minimized boundary and synthetic counterexamples; they do
  not claim arbitrary-text secret detection.

````
