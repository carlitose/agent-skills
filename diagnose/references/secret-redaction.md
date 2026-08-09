# Secret-redaction boundary

This is the evidence-safety contract for `diagnose`. It applies before evidence leaves
its source boundary: before a command is displayed, output is quoted, an artifact is
captured, or evidence is passed to another worker or durable report.

## Invariant

Replace credentials, tokens, cookies, authorization headers, private keys, connection
credentials, and secret-bearing argument values with the exact marker `<REDACTED>`.
Construct runnable feedback loops with an environment-variable reference such as
`$DIAGNOSE_API_TOKEN`; never interpolate its value into the displayed command or capture.

Preserve the smallest useful non-secret signal: status and error codes, timestamps when
causal, request or trace IDs, module/function anchors, safe flags, and the few surrounding
lines needed to interpret them. Do not retain a whole artifact merely because one line is
useful.

## Synthetic fixtures

These shapes are deliberately synthetic; placeholders are not credentials.

| Surface | Unsafe shape | Safe displayed or captured shape |
| --- | --- | --- |
| command | `curl -H "Authorization: Bearer <SECRET>" --token <SECRET> https://api.example.test/check` | `curl -H "Authorization: Bearer <REDACTED>" --token <REDACTED> https://api.example.test/check` |
| output | `status=401 request_id=req_fixture auth=<SECRET>` | `status=401 request_id=req_fixture auth=<REDACTED>` |
| artifact | A request archive containing headers, cookies, bodies, and the failing status line | `status=401 request_id=req_fixture` plus `<REDACTED auth headers; non-signal lines omitted>` |

Before durable capture, inspect both the selected lines and surrounding metadata: file
names, command arguments, URLs, environment dumps, and archive headers can carry secrets
even when the main payload looks safe.

## Evidence-loss gate

If the sanitized evidence cannot distinguish the remaining hypotheses, do not weaken the
redaction rule. Stop the diagnosis at that boundary, identify the missing signal, and ask
for a user-produced redacted artifact or separately authorized temporary instrumentation
that emits only the required safe fields. Never request a raw secret, credential-bearing
command, or unredacted artifact.
