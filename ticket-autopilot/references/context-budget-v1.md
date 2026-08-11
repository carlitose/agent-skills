# Context budget report v1

`context-budget [root] [--install-root <path>] [--workflow <name>]`
`[--ceiling-config <path>] [--check-ceiling] [--json]`
measures repository-controlled fixed context without credentials, network access, or
mutation. The default workflow is `ticket-autopilot`; `--no-workflow` measures only the
catalogue. The default install root is the current user's `.agents/skills` directory.

The canonical unit is `normalized-utf8-bytes`: strict UTF-8 text after CRLF and lone CR
newlines are normalized to LF. `word_count` fields are diagnostics retained to compare
the earlier investigation; they are not token estimates. Listing entries use the stable
repository-controlled representation `<name>: <description>\n`, excluding any host-owned
formatting or system prompt.

JSON mode uses the normal CLI response envelope (`schema`, `ok`, `command`, and `data`).
`data` is schema 1 with these fields:

- `schema`: report schema, exactly `1`.
- `complete`: false whenever a required listing or workflow source could not be measured.
- `unit`: exactly `normalized-utf8-bytes`.
- `repository` and `install_root`: resolved input paths.
- `workflow`: selected workflow name, or `null` with `--no-workflow`.
- `components`: the consumer-facing fixed totals. `always_on_listing_bytes` counts only
  installed model-visible repository skills; `workflow_static_closure_bytes` counts the
  selected manifest or is `null` when no workflow is selected.
  `variable_leaf_input_bytes` is the largest applicable leaf's declared
  `max_volatile_bytes`; applicable leaves are mutually exclusive model turns, so their
  bounds are maximized rather than summed. `composed_total_bytes` is the arithmetic sum of
  those three components.
- `always_on_listing`: listing totals and inventory. `normalized_bytes` and `word_count`
  cover visible installed skills; `visible_skill_count` is their count.
  `hidden_listing_bytes`, `hidden_word_count`, and `hidden_skill_count` report installed
  entries excluded by `disable-model-invocation: true` rather than dropping them.
  `repository_only_skill_count` covers repository skills absent from the install root.
  `external_installed_skills` names install-root entries outside this repository and does
  not count them. `skills` contains deterministic name-ordered entries. Its `complete`
  field is false and aggregate byte/word fields are `null` after any listing diagnostic,
  so partial discovery cannot look authoritative.
- Each `skills` entry has `name`, `status`, `source`, `normalized_bytes`, and
  `word_count`. `status` is `installed-visible`, `installed-hidden`, `repository-only`,
  or `malformed`; malformed counts are `null`. `source` is `install-root` when actual
  installed metadata was read and `repository` otherwise.
- `workflow_static_closure`: `null` with `--no-workflow`; otherwise it has `workflow`,
  `complete`, aggregate `normalized_bytes`, auxiliary `word_count`, `source_count`,
  `expected_source_count`, and ordered `sources`. Incomplete closure aggregates are `null`.
- Each `sources` entry has a stable `logical_source`, repository-relative `path`,
  `normalized_bytes`, auxiliary `word_count`, and `sha256`, the SHA-256 of the normalized
  bytes.
  Duplicate logical sources fail closed instead of being double-counted.
- `variable_leaf_inputs` lists the selected workflow's applicable leaves and their
  repository-relative declaration paths. Its aggregation is exactly
  `maximum-applicable-leaf-per-turn`; a missing, duplicate, unreadable, or ambiguous
  declaration makes the component incomplete instead of substituting zero.
- `composed_scenarios` reports the fixed prefix plus each applicable leaf bound.
  `worst_case_scenario` is the deterministic maximum and is the source of the composed
  per-turn total.
- `measurement_kind` is `upper-bound`, `observed_consumption` is `false`, and
  `worst_case_assumptions` names the fixed-prefix, full-bound, mutually-exclusive-turn,
  and unobserved-host assumptions. The result is never a token count or an observation of
  a live model context.
- `ceiling` reports whether a versioned ceiling is configured, its byte value and source,
  the measured delta, and one of `informational`, `within`, `exceeded`, or `unavailable`.
  Without a configured ceiling the report is informational. `--check-ceiling` exits with
  status 2 only for `exceeded`; it does not turn missing host data into a runner gate.
- `diagnostics`: objects with `code`, `message`, and `path`. Missing or malformed skill
  front matter and unreadable workflow sources are explicit here, never silent skips.

The report includes aggregate counts, paths, and content hashes only. It does not include
prompt contents, credentials, provider output, chat data, or inferred token conversions.

## Versioned ceiling and deliberate raises

The default ceiling file is
`ticket-autopilot/references/context-budget-ceilings-v1.json`. Its schema is deliberately
small and strict:

```json
{
  "schema": 1,
  "unit": "normalized-utf8-bytes",
  "workflows": {
    "ticket-autopilot": {
      "ceiling_bytes": 0,
      "rationale": "Why this reviewed upper bound is acceptable.",
      "raised_by": "ticket or decision reference"
    }
  }
}
```

The checked-in file contains a positive measured value rather than the illustrative zero.
A content change that increases `composed_total_bytes` above that value is a breach and
fails `--check-ceiling`. A legitimate increase is a separate, reviewable edit to
`ceiling_bytes`, `rationale`, and `raised_by`; changing measured inputs cannot silently
raise the ceiling. Reviewers should compare the component/scenario deltas before accepting
that edit.

This check is an explicit operator/CI command only. It does not add a token budget,
scheduler gate, delivery precondition, or merge-authorization axis to the autopilot ledger.
