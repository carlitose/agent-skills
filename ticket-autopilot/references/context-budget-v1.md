# Context budget report v1

`context-budget [root] [--install-root <path>] [--workflow <name>] [--json]`
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
- `diagnostics`: objects with `code`, `message`, and `path`. Missing or malformed skill
  front matter and unreadable workflow sources are explicit here, never silent skips.

The report includes aggregate counts, paths, and content hashes only. It does not include
prompt contents, credentials, provider output, chat data, or inferred token conversions.
