# Ticket Driver: directed review without product edits or false ambiguity

## Artifact Graph
- Artifact ID: `artifact:ticket-driver-directed-review-boundary`
- Role: `spec`
- Standalone: true

### Children
- [DRB-01 — isolate and interpret directed review](../tickets/ticket-driver-directed-review-boundary/01-isolate-and-interpret-directed-review.md)

## Type and evidence
Bug analysis. The first c3a/c3b benchmark batches (three attempts each) left only one valid result per candidate. Evidence: `tdr05-c3-gate-diagnosis-q1.md` (outside repository, with original immutable receipts). c3a-r1 contains a section-local `No findings.` under a named Python function plus nits in another function; the global parser rightly regards global clean+findings as contradictory, but the directed review lost the section scope. c3a-r3 includes two parseable nit headings and one nit without a path; that third item must stay ambiguous until a reviewer supplies its file. c3b-r1's directed reviewer created a supplementary test in the mutable candidate worktree despite the prompt prohibiting edits; the existing fingerprint gate caught the effect, but the invocation unnecessarily exposed a writable candidate. c3b-r3's `verify.claim_supported` produced an honest uncertain outcome; do not force it to yes.

## Target and invariants
The directed review receives the task and exact high-risk hunks in the prompt, not an open-ended checkout. Invoke only this fresh reviewer from a disposable, distinct working directory, with the same owned Windows process-tree containment and in-process Jev credential isolation. Permit one authored `.ticket-driver/review-directed.md` artifact, copy it to immutable receipts, and detect any other reviewer-created scratch files; continue the original product fingerprint check in case of absolute-path writes. This is operational isolation by cwd, **not an OS sandbox**, ACL guarantee or proof a malicious model cannot write an absolute path. Cleanup of this owned scratch directory follows child termination; do not clean benchmark projects or old receipts.

For directed review only, a standalone `No findings.` under a `##` heading that explicitly names a Python file/function is local to that section and must not contradict explicit findings in another section. A global clean marker in the same review as findings remains `unparsed`; fenced samples and malformed findings remain ambiguous. Require a severity, Python file path and explanation for each issue (optional line when unknown); preserve all explicit blocker/should-fix/nit rows and original order. Do not invent a path or accept `No blockers` as a global clean declaration. Improve the directed-review prompt so the reviewer emits exactly one finding line per issue, with a path and explanation even for missing test coverage, and only one global `No findings.` when no issues anywhere. Do not require JSON or alter CBF-01's global fast-lane semantics. A directed blocker with absent line must be passed to retry prose without a fake `:None` suffix.

## Non-goals and human gates
No changes to `ticket-autopilot`, `bench38` seed/hidden tests, Jev question policy, typed cascade thresholds, independent review claims, or existing c3/c4 receipts. The semantic verify uncertainty c3b-r3 remains a valid gate. Fixing this boundary does not guarantee any future model follows the prompt or any candidate fixes all hidden latent defects. User-authorized TDR-05 aggregate c3/c4 cap remains 30 starts, nine consumed at the old skill identity; post-fix runs need new per-lot labels and technical binding to the installed integrated identity, with no automatic substitution of old attempts.

## Verification
Reproduce RED on the installed source with structural excerpts matching c3a-r1/r3 and a fake reviewer that writes a product file relative to its cwd. GREEN proves section-local parsing, global contradiction gating, pathless ambiguity, artifact-only scratch behavior and no candidate change; verify retry path formatting, c3a/c3b/c4 focused fake tests, c1b/c2 shared parser regressions and mandatory local profile. Hosted exact-head CI and installed sync require their separate proof. Live benchmark is a later distinct TDR-05 phase with recorded spending and sample validity.
