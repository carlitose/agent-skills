# Public failure has priority over review-format uncertainty

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-test-failure-priority`
- Role: `spec`
- Standalone: true

### Children
- [SPB-12](../tickets/solo-pi-jev-luna-pilot/12-fix-test-review-priority.md)

## Observed cause / mandate
SPB-11 real cell r4: public test exit2 with concrete TypeScript compilation failures; review
includes valid blocker and a directory-only `tests` finding, therefore state unparsed. Current
controller gates review-format before treating known failed tests as a quality failure: no fix
turn, failures0. This prevents evaluating repair behavior, not a missing human decision.
Covered by current explicit arm fix/retest mandate, original cumulative financial budget.

## Minimal contract change
Only unresolved-format + tests-passed continues to be a human gate. Known completed failed
public tests continue the ordinary bounded quality-failure/fix path even if review unparsed.
Capture/cleanup uncertainty and readonly mutation gates retain priority. Keep original prose,
partial findings and exact bound receipt; never relabel review clean or adjudicate test failure
with Jev/judge. No hidden feedback, auto-approval or quality cap changes.
Review role must request concrete relative file:line markers (directory-wide missing-test
finding anchors nearest existing file); no parser changes or synthetic findings. Normalization
is instruction clarity only; genuinely unparsed green-test review remains a gate.

## Causal validation
Same actual Git/test fixture: bad public code plus directory finding => failed3 with ordinary
fix turns and no external coverage calls; green code plus same malformed format => gate0.
Changed controller/repair shards and current frozen selected contrast; prior Budget unchanged,
no model calls in local tests. New live cell uses full prior account and distinct source;
valid model failures remain results, not grounds for repeated score hunting.
