# Gate readiness and existing authority

Load for an environment-stage blocker, stale technical binding, or uncertainty about whether
a gate requires a new human decision. [Ticket Autopilot](../SKILL.md) owns scheduling and transitions; this
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

## Mandate, technical binding, and operator store

| Concept | What it establishes | What it does not establish |
| --- | --- | --- |
| **Human mandate** | The original affirmative instruction, actor, covered actions/targets, limits, expiry/revocation and budget. | Provider credentials, readiness, passing checks or permission outside that scope. |
| **Technical binding** | How a covered operation is attached to its current resource, candidate or exact provider observation. | A new mandate, extra budget or permission to change a human-imposed identity limit. |
| **Operator store** | Persisted operational state, bindings, provenance and consumption through its owning contract. | Human consent merely because a record exists, a reference is nonempty, or a write succeeds. |

A user-imposed exact head or path is a mandate limit, not an expiring implementation detail.
Conversely, a broad valid mandate is not consumed merely because its derived resource binding
needs renewal. Provider access remains a separate prerequisite. Missing/corrupt store state is
not proof that consent expired, nor permission to reconstruct unknown revocation history.

### Renew only the technical binding

1. Read the original mandate and its current validity. Identify whether the stale item is a
   derived binding or a human-imposed limit. If that distinction is unresolved, ask only the
   missing scope question; do not repeatedly ask for the same already-valid consent.
2. Prove the replacement stays within the same covered action/target and remaining budget.
   Check current candidate coherence and resource identity. Preserve all attempts, failures,
   cumulative consumption, original evidence identities and outstanding gates; renewal never
   resets them or turns old observations into current passes.
3. For a covered technical renewal, use the existing owning API with the original actor and
   authority reference, retaining parent provenance and new binding readback. Do not request
   duplicate human consent. This instruction does not invent an API or authorize raw edits to
   an operator store or ledger.
4. On changed scope, expiry, revocation, a human-imposed identity mismatch or exhausted budget,
   stop at that boundary and obtain only the genuinely missing decision. Missing credentials
   or an unavailable renewal API remain technical input/capability blockers; repeated consent
   does not repair them. Unknown authority state stays blocked.

Completion criterion: the mandate remains attributable and valid, the renewed binding and
readback stay within its limits and budget, and every prior attempt/gate remains accounted for.
Otherwise report the exact authority or technical gap without silently broadening permission.
This is an operator procedure, not an automatic resolver or evidence that a renewal occurred.

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
4. **Use the existing public transition in the selected lane.** In the Autopilot lane,
   only while the user allows it, consult `approve --help`; when the preceding checks
   succeed, the gate form is:

   ```bash
   "$TICKET_AUTOPILOT_PYTHON" -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
     approve "$RUN" "$GATE_ID" --repo "$REPOSITORY" \
     --actor "$ORIGINAL_ACTOR" --evidence "$ORIGINAL_AUTHORITY_REFERENCE"
   ```

   The actor/reference arguments record the applicable human authority; they do not
   demand a duplicate conversational prompt. This is an operator-attested use of the
   existing contract, not an automatic resolver. The API's nonempty-reference check does
   not itself validate the reference's meaning. Other gate kinds retain their own
   procedures. Completion: normal readback shows reentry or a remaining explicit gate;
   preserve rejection details instead of editing the ledger.

   In skills-only, use the resource or verification contract's supported caller operation;
   do not create/resume a runner or invent ledger state to renew a binding. If that operation
   is unavailable, report a technical capability gap, not a demand for identical consent.
5. **Resume evidence collection, not claims.** Reentry returns to the recorded stage. It
   is not a review, QA, verification, provider or merge pass. Retain unrelated gates and
   the normal quality budget. Implementation, recovery, quality, merge, wiki and Pi
   boundaries remain separate. Completion: report the current phase, observed checks and
   remaining evidence; never call an unresolved or merely resumed ticket complete.

A `pre-qa-coherence-v1` blocked receipt is not an approvable gate. Follow the
[pre-QA coherence recovery](pre-qa-coherence.md): preserve the diagnostic and rebuild from the
fresh target through normal candidate quality. Gate approval, merge authority, or an environment
readiness label cannot convert an incoherent candidate into a passing one.

This procedure does not mechanically certify stop evidence or wake a stopped model. Those
require the separately designed runner assessment and host continuation work; no such
capability follows from the readiness labels.
