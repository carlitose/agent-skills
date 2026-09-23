# Ticket Driver: recognize review findings without inventing clean reviews

## Artifact Graph
- Artifact ID: `artifact:ticket-driver-review-findings`
- Role: `spec`
- Standalone: true

### Children
- [CBF-01 — recognize prose findings safely](../tickets/ticket-driver-review-findings/01-recognize-prose-findings-safely.md)

## Type and evidence
Bug analysis. In the authorized c1b benchmark (three live runs, no valid samples), every reviewer wrote a Markdown artifact with actual findings, but `parse_findings` returned `unparsed`: `tdr05-c1b-report-q1.md` (external benchmark evidence). The three preserved reviewer artifacts have a bold `should-fix` path without a line number; a bold `[blocker]` with more than one path, where the primary path has no line; and `### nit path:line` headings. The fast lane accepts only an unadorned `[severity] path:line - explanation` line. Gating an ambiguous review is correct; failing to recognize these explicit findings is avoidable. c2b also had independent gates (retry uncertainty, oversized QA plan); fixing findings does not claim to fix those gates.

## Target and non-goals
Keep reviewer prose and the zero-JSON leaf contract. Parse a bounded, explicit severity marker at the beginning of a Markdown line: `blocker`, `should-fix`, or `nit`, optionally in a heading, bold, or square brackets; require a Python file path and a nonempty explanation separated by a dash. Preserve the primary file path and an integer line when present, otherwise report an absent line (`None`) instead of inventing a location. Canonical `[severity] path:line - explanation` remains accepted. Ignore fenced code examples and non-finding prose. An explicit standalone `No findings.` means clean only when no severity marker appears in the review. If any severity-marked line is malformed or lacks a path/explanation, fail closed as `unparsed` even if another line parses. Multiple explicit findings remain distinct, in source order; `blocker` still triggers the existing retry/stop path. Do not infer findings from arbitrary natural-language text, treat `No blockers` as clean, call Jev, or change the already-consumed c1b benchmark evidence.

Adjust the reviewer prompt to invite the supported finding shape; preserve optional prose and fresh-session review. This is not a requirement for reviewers to emit JSON or a program status. Do not alter `ticket-autopilot`, the Jev policy, the c2 mandates, or the QA-command limit in this slice. An old fenced example or contradictory/malformed severity line must never silently become `clean`.

## Verification and rollout
Add synthetic tests transcribed from the *structure* of all three observed reviews, plus a canonical finding, truly clean review, fence exclusion, missing-path ambiguity, mixed valid/malformed severity, and `No blockers` without findings. Demonstrate RED on the current parser, GREEN after the fix; run c1b, c2 and c3 targeted suites because they share `parse_findings`, then the applicable mandatory quick profile. Existing c1b receipts are historical; no live retry or claim of 3 valid c1b samples from unit tests. Delivery and installed-package sync have their own authorization/readback gates. The next optional live c1b measurement requires a fresh, bounded human mandate.
