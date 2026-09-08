---
ticket_schema: 1
ticket_id: "APM-09"
execution_mode: AFK
blocked_by: []
---

# Decode localized Azure CLI JSON without weakening strict Git data

## Artifact Graph
- Artifact ID: `artifact:autopilot-practical-reliability-apm-09`
- Role: `ticket`
- Parent: [Practical Reliability for Ticket Autopilot](../../specs/autopilot-practical-reliability.md)

## Parent Spec
[Practical Reliability for Ticket Autopilot](../../specs/autopilot-practical-reliability.md) — S9 — Localized Azure CLI JSON Decoding.

## What to Build
Distinguish Azure CLI JSON stdout from Git stdout at the existing command/provider boundary. Decode provider bytes strictly using an established producer encoding before JSON parsing, preserving exact human text as well as structural fields. Keep Git's current strict UTF-8 and stderr's diagnostic policies intact.

S9 owns the evidence, policy constraints, and alternatives. The shared-runner failure and installed MSI Python's captured cp1252 stdout were reproduced locally; the original authenticated PR response was reported by the user, not reproduced. This extends the Windows text-fidelity family without reopening WT-02/WT-03. The proposed UTF-8-first/ANSI fallback is not automatically correct: CPython rejects undefined cp1252 bytes, and successful JSON parsing or byte round trips do not identify the intended encoding.

## Acceptance Criteria
- [ ] A raw-byte regression reaches the actual runner and provider JSON boundary: the supported cp1252 response containing byte `0xF3` yields the intended accented text, character-identical, without replacement or normalization. Existing UTF-8 provider JSON remains correct under its supported producer profile.
- [ ] Encoding selection is provider-scoped and justified by an explicit supported producer profile, reliable signal/configuration, or demonstrated producer-side UTF-8 behavior. Unknown/unsupported encoding is actionable failure; neither hard-coded cp1252 for all Windows commands nor trial parsing alone selects a codec.
- [ ] Valid UTF-8 Git output and cleanup inputs retain their behavior; invalid Git data still fails strictly. Stderr diagnostics remain readable under the existing policy, and other providers do not silently acquire an encoding fallback.
- [ ] Tests cover another configured Windows code page, non-ASCII text/paths, undefined bytes such as cp1252 `0x81`, and byte sequences valid in two codecs but representing different text. Assertions check intended characters, not merely absence of U+FFFD.
- [ ] Truncated/malformed JSON and nonzero exits preserve useful diagnostics. A decoding/parsing failure after a simulated accepted PR creation remains an uncertain outcome; existing readback/reconciliation precedes another creation attempt, and the test proves no blind duplicate mutation.
- [ ] Document supported producer/version/platform assumptions and unavailable boundaries. Do not rely on `PYTHON*` overrides ignored by the MSI `-I` launcher or alter global console/Python settings. No real Azure mutation is required for automated acceptance.
- [ ] APM-05 can reuse the resulting strict provider-decoding boundary without duplicating codec selection in its timeout/output-limit implementation.

## Frontier
Ready. No dependency or unresolved product decision. Establish the supported producer encoding as an engineering checkpoint; if the actual producer contract cannot be established, report that exact limitation rather than claiming a safe fallback.

Execute inline. AFK does not authorize subagents; explicit user request is required. This ticket does not itself grant provider publication or merge authority.

## Step-by-Step Implementation Plan
1. Read S9 and the Windows text-fidelity decision context; trace `_run_captured`, `SubprocessCommandRunner`, provider JSON parsing, and PR-create failure/readback. Completion: a sanitized raw-byte test reproduces the current failure and names the affected boundary without a live mutation.
2. Establish the supported Azure stdout encoding mechanism and distinguish it from Git data. Completion: tests identify the intended text for UTF-8, established cp1252, another supported code page, and ambiguous inputs; unsupported cases have explicit failure behavior.
3. Implement the smallest provider-scoped strict-decoding change and connect failures to existing diagnostics/uncertain-mutation handling. Completion: the regression passes without weakening Git/stderr contracts, and simulated accepted creation is not blindly retried.
4. Run focused UTF-8, command-runner, provider, cleanup, and relevant delivery/readback regressions. Completion: record actual results, document supported producer assumptions and missing live/platform evidence, and leave a single decoding boundary for APM-05.

## Testing Plan
- Use disposable child processes that emit raw byte fixtures; a fake returning already-decoded strings does not exercise this bug.
- Use sanitized JSON prose and exact expected Unicode values. Include ambiguous valid encodings, undefined bytes, malformed/truncated JSON, and a nonzero exit with diagnostics.
- Exercise the provider orchestration with an accepted-create/failed-response simulation and subsequent readback. This is integration evidence, not a real Azure PR observation.
- Retain the strict Git/cleanup and lenient stderr regression suite. An installed MSI launcher probe is separate from an authenticated provider operation; report unavailable platforms rather than inventing coverage.

These are planned acceptance checks. Only the scoped baseline/probes described in S9 have run; the fix is not implemented.

## Out of Scope
- Global `errors="replace"`/`ignore`, automatic charset guessing, a general codec framework, or weakening byte/text identity checks.
- Fixing CMD's reinterpretation of Markdown separators or adding Azure expected-head merge support.
- Command timeouts/cancellation/output limits, owned by APM-05, which depends on this ticket.
- CLI upgrades, global environment/console changes, reopening WT-02/WT-03, raw customer-data fixtures, or a live provider mutation merely to prove the local fix.
