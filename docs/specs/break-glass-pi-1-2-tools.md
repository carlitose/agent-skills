# Break Glass recovery tools on Pi 1.2.0 and with pi-agent-ide

## Artifact Graph
- Artifact ID: `artifact:break-glass-pi-1-2-tools-spec`
- Role: spec
- Standalone: true
- Amends: [Natural-language Break Glass local repair](pi-break-glass-natural-language-local-repair.md), "Local repair capability"
- Children: [BGT-01 Recovery tools on Pi 1.2.0 and pi-agent-ide](../tickets/break-glass-pi-1-2-tools/done/01-recovery-tools.md)

## Type and evidence
Bug analysis. The user asked whether the newly installed Pi extensions conflict (2026-10-13). A
real Pi 1.2.0 with the user's packages reports these tools:

- built-ins `bash`, `grep`, `find`, `ls` with `sourceInfo.path` `builtin:<name>`. Before Pi 1.2.0
  it was `<builtin:<name>>`. `isCanonicalBuiltin` checks only the old form.
- `read` and `write` from `npm:pi-agent-ide` (origin `package`), and its `edit` with exposure
  `hidden`.

So `selectRecoveryTools` finds no canonical `read` and exposes no tools at all. Even without
pi-agent-ide, the new path form makes every built-in non-canonical. `/break-glass` cannot repair
anything on the user's Pi.

## Goal
1. **Pi 1.2.0 built-ins.** A built-in counts as canonical with either path form, `builtin:<name>`
   or `<builtin:<name>>`. Source `builtin`, scope `temporary` and origin `top-level` stay required.
2. **pi-agent-ide.** A tool with a recovery name (`read`, `bash`, `edit`, `write`) whose
   `sourceInfo.source` is `npm:pi-agent-ide` and origin is `package` also counts. The user chose
   to trust this one package ("fai tutte e 3 le correzioni", 2026-10-13, accepting the proposal
   that named it). Any other extension's same-name tool stays ambiguous, as today.
3. **Hidden tools.** A tool with exposure `hidden` is unavailable: it is neither selected nor
   ambiguous. With pi-agent-ide, the recovery set is `read`, `bash`, `write`, without `edit`.
4. **Wording.** The policy, the block reason and the omission notice name the recovery tools
   instead of "canonical built-in read, bash, edit, and write".

## Non-goals
- A setting for other trusted packages.
- Adding pi-agent-ide's `replace`, `insert` and other tools to the recovery set.
- Changing arming, expiry, prompt binding, revocation or restoration.

## Failure modes
- **A different package named `pi-agent-ide`:** only a package installed from npm under that name
  matches. Pi sets `sourceInfo`, so another extension cannot claim it.
- **Mixed sets:** each name is checked by itself; one built-in and one pi-agent-ide tool can both
  be in the set.

## Verification
- `extensions/break-glass.test.ts`: both path forms are accepted. pi-agent-ide `read` and `write`
  are selected and its hidden `edit` is skipped. Another package's `read` gives no tools.
- `extensions/mandatory-agent-skills.test.ts` keeps passing with the new block reason.
- `npm test` (the quick profile) in CI.

## Gates
- **Attempt:** one PR on `carlitose/agent-skills` with green CI. The agent merges it.
- **Budget:** no spend; targeted local tests, the full suite in CI. **Time:** 4 hours.
  **Maximum attempts:** 2.
- **Installation:** sync of the installed skills and `/reload` only after lot `dbh-vague5` ends
  (a lot must not see an update mid-run).
