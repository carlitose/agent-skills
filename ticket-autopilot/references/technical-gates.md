# Gate readiness and existing authority

Load for an environment-stage blocker or uncertainty about whether a gate requires a new
human decision. [Ticket Autopilot](../SKILL.md) owns scheduling and transitions; this
reference owns interpretation and the scoped operator procedure.

## Interpret status without granting permission

For an otherwise eligible gated ticket, schema-2 status uses its applicable open ticket
and run gates:

| Readiness | Meaning |
| --- | --- |
| `human-gated` | An explicitly classified human gate is open; human takes precedence in a mixed set. |
| `environment-gated` | All applicable open gates are classified `environment`. |
| `gated` | Other, mixed non-human or unavailable classification; inspect the actual records. |

These are persisted classifications, not proof of recoverability. An environment reason
can still describe missing credentials, an unresolved decision or required evidence.
Never infer permission or a restored prerequisite from a label or reason string.

`open_gates` and `open_gate_records` retain every category in persisted order. The Python
`open_gate_ids()` accessor returns that complete set; `human_gated_ids()` returns only
open human-category gates. Its former all-gates behavior is intentionally corrected, not
retained as an alias. Closed gates do not affect classification. Status reads neither
rewrite legacy reasons nor resolve gates, reset budgets, activate tickets or pass stages.
Administrative barriers, dependencies and actual scheduling restrictions still apply.

## Continue within the existing request

Incomplete implementation or unattempted checks are work, not evidence of an unavailable
environment. Continue authorized prerequisite investigation and unrelated ready AFK work
while a ticket remains gated. Use the bounded declared check plan; do not require every
imaginable alternative or turn missing release evidence into a release pass.

Before resolving an `environment` / `stage` / `ticket` gate:

1. **Identify the current blocker.** Read status and the exact gate, run, ticket, stage and
   CandidateRef. Distinguish an ordinary unfinished action from a demonstrated obstacle
   or an actual missing decision. Record the minimal redacted observation and any declared
   alternative still to try. Completion: the cause and remaining work are explicit; a
   generic historical reason has not been rewritten or guessed.
2. **Read the original authority.** Inspect the durable implementation or recovery
   instruction, its actor and scope. Reuse it only when it covers this action and remains
   valid, including any explicit candidate binding. A stop, changed request, missing
   decision or expanded scope requires its own resolution. A merge grant alone supplies
   none of this authority. Completion: the original reference supports the requested
   reentry without inventing a new human message or substituting a different grant.
3. **Establish recovery.** Perform only the already-authorized bounded prerequisite work.
   Preserve its actual outcome. Do not resolve the gate while its cause remains unknown
   or unresolved. Missing credentials, live-action approval or explicitly required
   independent evidence are not supplied by local substitutes. If the candidate changed,
   use normal candidate refresh/recovery and fresh quality rather than stale evidence.
   Completion: prerequisite restoration and current scope are supported by observations,
   or the exact remaining boundary is reported and the gate stays open.
4. **Use the existing public transition.** Consult `approve --help`; when the preceding
   checks succeed, the gate form is:

   ```bash
   python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
     approve "$RUN" "$GATE_ID" --repo "$REPOSITORY" \
     --actor "$ORIGINAL_ACTOR" --evidence "$ORIGINAL_AUTHORITY_REFERENCE"
   ```

   The actor/reference arguments record the applicable human authority; they do not
   demand a duplicate conversational prompt. This is an operator-attested use of the
   existing contract, not an automatic resolver. The API's nonempty-reference check does
   not itself validate the reference's meaning. Other gate kinds retain their own
   procedures. Completion: normal readback shows reentry or a remaining explicit gate;
   preserve rejection details instead of editing the ledger.
5. **Resume evidence collection, not claims.** Reentry returns to the recorded stage. It
   is not a review, QA, verification, provider or merge pass. Retain unrelated gates and
   the normal quality budget. Implementation, recovery, quality, merge, wiki and Pi
   boundaries remain separate. Completion: report the current phase, observed checks and
   remaining evidence; never call an unresolved or merely resumed ticket complete.

This procedure does not mechanically certify stop evidence or wake a stopped model. Those
require the separately designed runner assessment and host continuation work; no such
capability follows from the readiness labels.
