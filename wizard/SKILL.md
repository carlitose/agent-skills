---
name: wizard
description: "Author a staged Bash wizard for a manual setup, credential, migration, or cutover procedure that a human will run explicitly. Use when the user asks for a repeatable guided procedure with human-only actions."
argument-hint: "What manual procedure should the human run, which values are sensitive, and where may each value be written?"
disable-model-invocation: true
---

# Wizard

Owns: authoring human-run setup wizards.

A wizard is a Bash script that guides a human through manual actions and records only the
values they explicitly choose to persist. This skill authors and validates that script.
Never run the generated wizard, a copied template, or any live stage. The human runs it
explicitly after reviewing the stage plan and mutation boundaries.

Do not use a wizard for work the agent can safely complete directly, background automation,
or unattended provider changes. Do not turn it into another scheduler or ticket workflow.

## Inputs and stage plan

Read the repository and identify the current configuration, target state, relevant docs,
environment examples, and CI references before asking questions. Then define:

- the ordered stages and the observable completion condition for each stage;
- every value captured, its source, whether it is sensitive, and its approved destination;
- every local file, browser, provider, credential-store, or irreversible action involved;
- the exact actions that remain manual when automation is absent or unauthorized.

Show deterministic stage counts such as `Stage 2/5`. Do not display clocks, rates, duration
predictions, or completion forecasts. The number changes only when the reviewed stage plan
changes.

## Author the script

Copy [template.sh](template.sh) and edit only the section below its `STAGES` marker. Set
`WIZARD_CONFIGURED=1`, set `TOTAL_STAGES` to the exact number of `stage` calls, and keep each
stage focused on one human outcome.

Use the template helpers:

- `stage`, `say`, `step`, `note`, `warn`, `pause`, and `confirm` for the human journey;
- `ask` for non-sensitive single-line input;
- `ask_secret` for sensitive input so terminal echo is disabled;
- `write_env` only for a user-approved local environment destination;
- `open_url` only for a reviewed URL;
- `set_secret` only for a reviewed provider secret name.

Never embed a real credential, token, cookie, personal value, copied secret, or transcript in
the script, examples, tests, logs, command arguments, or handoff. Use fake `example.invalid`
identities and generated in-memory fixture values. Do not print captured secret values.
Unset sensitive shell variables as soon as their final approved operation finishes.

## Mutation and external-action boundary

The script is inert until a human executes it. Local environment writes occur only during
that explicit run and use an idempotent key upsert. Re-running the same value must not add a
duplicate key or change unrelated lines.

Browser opening additionally requires `WIZARD_ALLOW_BROWSER=1`; otherwise show the URL for
manual use. Provider writes additionally require `WIZARD_ALLOW_PROVIDER=1` and an interactive
confirmation immediately before the write. Missing tools, authentication, opt-in, or
confirmation produces a truthful manual follow-up, not an implicit fallback.

Fixture mode always wins over those opt-ins. With `WIZARD_FIXTURE_MODE=1`, browser and
provider helpers must return before command discovery or execution. Fixture stages may write
only to their caller-supplied temporary `ENV_FILE`; they must never persist the generated
sensitive input.

## Validate without running live stages

1. Run `bash -n <wizard>`.
2. Run `shellcheck <wizard>` when `shellcheck` is available.
3. Run only fixture mode in a validated temporary directory, with fake browser and provider
   executables that fail if called.
4. Execute the fixture twice and compare the environment file byte for byte. Confirm there
   is one entry per key and unrelated lines are preserved.
5. Generate the sensitive fixture value in memory. Confirm it is absent from stdout, stderr,
   environment output, sentinels, and retained test artifacts.
6. Statically trace every captured value to its reviewed destination and every external
   action to its opt-in and confirmation gate.

Do not weaken the fixture guard to make a test pass. Do not execute the live wizard during
AFK implementation, review, QA, or verification.

## Return

Return the wizard path, ordered stage list, stage count, value-to-destination map, sensitive
value names without values, local mutation list, external action list, validation results,
and the exact command the human may run. State that browser/provider opt-ins are absent by
default and that execution has not occurred.
