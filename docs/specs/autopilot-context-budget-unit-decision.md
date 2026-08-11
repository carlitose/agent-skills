# Autopilot context budget unit

## Status

Accepted on 2026-08-11. Authority: explicit user confirmation for ticket `TK-01`.

## Type

Decision spec

## Artifact Graph

- Artifact ID: `artifact:autopilot-context-budget-unit-decision`
- Role: `spec`
- Parent: [Autopilot Token Economics](autopilot-token-economics-wayfinder.md)

## Context

Autopilot needs a regression budget that is deterministic, provider-free, cheap to run,
and comparable between repository revisions. A model tokenizer alone cannot satisfy that
contract: remote token-count APIs add credentials, network dependency, latency, and data
exposure, while local model-specific tokenizers change the meaning of the number when the
host or model changes.

The local budget also cannot describe the whole live context. Chat history can be the
largest consumer, and hosts may add system instructions, tool definitions, compaction, or
other surfaces the repository cannot inspect. The decision therefore separates an
enforceable repository-controlled byte budget from host-reported live context tokens.

## Decision

### Deterministic unit

The canonical local unit is the number of UTF-8 bytes after platform newlines are
normalized to LF.

For every counted text surface:

1. accept Unicode text or decode bytes as strict UTF-8;
2. replace CRLF and lone CR with LF;
3. encode the normalized text as strict UTF-8;
4. count the resulting octets.

Invalid UTF-8 is an error. Replacement characters, locale-dependent decoding, native line
endings, token approximations, and inferred conversions are forbidden. The resulting value
is a byte budget, not an estimate of model tokens, price, latency, or cache usage.

### Counted components

Reports keep these components separate and also expose a composed total:

- `always_on_listing_bytes`: repository-controlled model-visible skill or capability
  listing text that is present before a workflow is selected;
- `workflow_static_closure_bytes`: the selected workflow's fixed instructions and required
  references, with each logical source counted once in a deterministic manifest;
- `variable_leaf_input_bytes`: the declared maximum normalized-byte intake for the
  applicable leaf inputs, reported by leaf and input class;
- `composed_total_bytes`: the arithmetic sum of the selected fixed components and the
  applicable variable bounds, without a guessed token conversion.

Fixed instructions and variable leaf inputs must never be collapsed into one unexplained
number. `TK-02` owns the exact fixed-surface inventory and report schema, `TK-03` owns the
per-leaf input bounds, and `TK-04` owns concrete composed ceilings and the scenarios to
which they apply.

The deterministic layer excludes chat history, model output, hidden host/system prompts,
host-owned tool schemas, content a leaf does not load, binary files, digest-addressed
evidence that remains out of context, cache accounting, and any provider billing data.
Exclusion means “not locally enforceable,” not “free.”

### Live observation layer

Live context is recorded only from an explicit host-reported value and retains the host's
native token unit. It includes chat history and every other surface the host includes in
that value. It is never derived from the deterministic byte total.

When a host supplies categories, the observation may retain aggregate category totals.
Claude Code can expose a context-category breakdown through `/context`. The documented
Codex status surface exposes overall context/token usage but no equivalent category
breakdown; that case must say `breakdown: unavailable` rather than inventing categories.
`TK-09` owns the version-bound observation mechanics.

### Execution and latency policy

Deterministic measurement runs only on explicit operator request or in CI. It must not run
synchronously on every model call. Live host values are sampled only at ticket boundaries,
not continuously and not once per model interaction.

A pull-request check reports every component and delta. It fails only when an explicit,
versioned ceiling for the applicable scenario is exceeded. In the absence of such a
ceiling, the delta is informational. `TK-04` owns the ceiling values and deliberate raise
procedure.

### Reporting stability

Two local reports are comparable only when they use the same unit contract and compatible
report schema. A stable report:

- identifies this unit and its version;
- uses repository-relative logical component identifiers in deterministic order;
- counts normalized content only, never absolute paths, timestamps, locale output, or
  platform newline bytes;
- records separate component values before computing the total;
- identifies the source revision or tree and measurement implementation version so a delta
  is attributable;
- represents unavailable inputs explicitly instead of substituting zero.

A component rename or inventory change is visible metadata, not silently folded into a
numeric delta. Byte deltas may be compared across commits; byte totals must not be compared
as though they were model-token deltas.

## Data and privacy boundary

Persist only aggregate counts and the minimum technical metadata needed to reproduce and
compare them: schema/unit versions, logical component identifiers, source revision, host
and model labels when supplied, boundary kind, and availability state.

Do not persist prompts, messages, file contents, transcripts, chat/session IDs, handoff
contents, or credentials in measurement records. Do not upload a report or any source data
unless the user invokes a separate explicit submission operation. Local session-log parsing
is not required by this decision.

## Rejected alternatives

- **Remote exact-tokenizer API:** rejected because it requires provider credentials and a
  network call, adds latency and failure modes, may expose text, and is not provider-free.
- **Model-specific local tokenizer:** rejected as the canonical unit because results change
  with tokenizer/model selection and cannot compare Codex and Claude Code consistently.
- **Word or character count:** rejected because language, whitespace, and Unicode encoding
  make the unit too weak or ambiguous for an enforceable byte intake bound.
- **Guessed byte-to-token or word-to-token formula:** rejected because it turns a stable
  measurement into an unverified model-specific estimate.
- **Measure every model call:** rejected because it adds latency to the entire workflow and
  duplicates work; explicit/CI measurement and boundary sampling provide the required
  signals.
- **Use only the local budget:** rejected because it hides chat history and host-owned
  context, often the dominant live cost.
- **Use only host-reported tokens:** rejected because availability and category detail vary
  by host and version, so it cannot provide a provider-free regression gate.

## Consequences

The repository can enforce deterministic growth without claiming knowledge it does not
have. A local regression report remains fast, offline, reproducible, and safe to compare.
The live observation remains honest about chat history and host-owned context, but cannot
gate CI when the host does not expose it.

There are intentionally two units in reports: normalized UTF-8 bytes for enforceable local
budgets and host-reported tokens for observed live context. They may be displayed together
only when clearly labeled and must never be added, converted, or ranked as equivalent.

## Verification strategy

`TK-02` should provide unit fixtures covering LF, CRLF, lone CR, ASCII, multibyte Unicode,
invalid UTF-8, deterministic manifest ordering, and duplicate logical sources. Repository
integration evidence should prove identical content yields identical component counts on
Windows and non-Windows environments.

`TK-04` should prove that all deltas are reported, that an absent ceiling remains
informational, and that only an explicit exceeded ceiling fails. `TK-09` should prove the
host boundary separately, including a Codex observation with unavailable breakdown and a
Claude Code observation only when the host actually supplies categories.

No runtime behavior or measurement command is implemented by this decision spec.

## Unresolved implementation questions

- The exact versioned JSON field layout and fixed-component discovery rules belong to
  `TK-02`.
- Per-leaf input classes and bound values belong to `TK-03`.
- Concrete ceilings and the deliberate raise workflow belong to `TK-04`.
- Host adapters, exact ticket boundary events, and live observation storage mechanics
  belong to `TK-09`.

None of these questions may redefine the canonical byte unit or infer a token conversion.
