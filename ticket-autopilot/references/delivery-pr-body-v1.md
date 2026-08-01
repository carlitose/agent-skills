# Delivery PR-Body Handoff v1

`ticket-autopilot` owns persistence, validation, provider mutation/readback, and lifecycle.
`explain-pr` owns semantic rendering from an already validated verification bundle.

## Render request

After idempotent commit and push, `delivery` returns `render-required` with a request bound
to:

- schema and ticket identity;
- normalized Ticket Envelope facts and digest;
- frozen CandidateRef and artifact generation;
- exact expected PR head, branch, and base;
- changed-path diff facts, the validated-bundle artifact hash, and the completed handoff hash;
- a canonical `request_hash` over every preceding field.

The request is persisted before it is returned. A contradictory request for the same
delivery fails closed.

## Render result

Resume `delivery` with every field below or none of them:

```text
render_request_hash
expected_head_sha
rendered_body
verification_bundle
verification_audit_root
```

The root is the absolute `verification-audit` skill root. The request hash and expected
head must match literally. The canonical verifier validates the bundle against the ticket
CandidateRef and validates the body against the bundle and expected head.

Validated body and bundle content are stored atomically under the run directory by SHA-256.
Missing, partial, stale, corrupt, or contract-invalid artifacts open a durable
`delivery-pr-body` gate.

## Provider completion

The provider receives only the validated body. Its normalized receipt must include the
exact provider, operation, PR ID, branch, base, head, and literal observed body. The runner
then validates the read-back body against the same stored bundle and observed head.

Only this completed receipt can transition the ticket to `pr-open`. Render, local
validation, publication, readback, and revalidation failures remain distinct resumable
delivery phases. Repeating delivery reuses the same content-addressed artifacts and PR.

GitHub updates an existing PR through a REST `PATCH`; body publication must not depend on
the `gh pr edit` GraphQL project-card query. Provider-specific transport does not change
the normalized core receipt.
