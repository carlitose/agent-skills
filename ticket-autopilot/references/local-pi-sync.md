# Exact integrated local Pi synchronization

Load only for this operational branch. [Ticket Autopilot](../SKILL.md) owns scheduling; this
reference owns this branch's operator procedure. CLI `<command> --help` remains the syntax
authority.

## Contract

`sync-local-pi <run> --repo <repository> --ticket <id> --checkout <absolute-persistent-path>
--agents-root <absolute-skill-root> --pi-settings <absolute-settings> --actor <identity> --evidence
<durable-ref>` accepts only a durably integrated ticket, binds its exact head/tree, and persists one
local transaction intent. It materializes a clean persistent checkout, replaces only package- or
prior-manifest-owned skills, invokes `pi install` and `pi list` through the platform-specific installed-Pi launcher,
and retains `skills: []` on exactly one local package. Pi may store the local source relative to its
settings root: preserve that spelling but require its resolved identity and the package row—not the
indented installed path—to equal the approved checkout. First adoption and package-source
replacement require their explicit flags. An owned-manifest source change additionally requires
`--migrate-owned-source-from <exact-old-root>`; it uses a distinct deterministic successor state and
preserves ordinary failed history literally. Owned digest drift remains blocked unless repeated
`--replace-drifted-owned <name>=<observed-sha256>` inputs exactly equal the complete observed drift
set; this destructive authority is valid only during that source migration. Replay re-observes
without a second install; wrong trees, dirty or unsafe paths, command/readback failure, and package
contradictions fail closed and recover owned local state. It never updates the Pi binary or an
active session; report that `/reload` is required. Sync authority grants no merge, provider, wiki,
bootstrap, cleanup, or unrelated future sync.

## Operator procedure

## Exact integrated local Pi synchronization

After an `agent-skills` ticket is durably `integrated`, a separate actor/evidence-bound
command can refresh the local cross-agent skills and Pi package from that exact PR head:

```bash
python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  sync-local-pi my-run --repo /absolute/path/to/agent-skills \
  --ticket MY-01 \
  --checkout "$HOME/.pi/agent/local/agent-skills" \
  --agents-root "$HOME/.agents/skills" \
  --pi-settings "$HOME/.pi/agent/settings.json" \
  --actor "alice@example.com" --evidence "decision://change-123/pi-sync" \
  --adopt-existing-owned --replace-package-source
```

The command first binds the integrated head/tree and persists an immutable intent. Under one
local-sync lock it materializes a persistent clean checkout, atomically replaces only skill
roots proved by the package or prior ownership manifest, preserves external skills, invokes
`pi install` and `pi list` through the platform-specific installed-Pi launcher, and retains
`skills: []` on the single local package because `~/.agents/skills` remains canonical. Pi may persist an absolute
install argument as a source relative to its settings root; the transaction preserves that
spelling but requires its resolved identity and the `pi list` package row to equal the approved
checkout exactly. It never treats the indented installed-path display as package evidence.
Exact replay re-observes without a second install. Wrong trees, dirty paths, symlinks, special
files, package contradictions, command failure, or readback failure stop and recover without a
success receipt. It never invokes a Pi self-update command.

POSIX retains the normal `zsh -lic` wrapper. Windows supports the standard npm `pi.cmd`
selected on PATH for `@earendil-works/pi-coding-agent`: the launcher and installed `bin.pi`
must agree. The adapter runs its entry point through adjacent `node.exe`, otherwise native
Node on PATH, with literal argv and child-only `PI_CODING_AGENT_DIR`. It does not execute
cmd.exe, interpolate paths or install a missing dependency. Unsupported/custom launchers,
missing executables, contradictory metadata and invalid UTF-8 output fail through the
existing recovery path. Native output is captured as bytes and decoded on the caller thread
so Windows reader-thread failures cannot masquerade as success. Git path readback is UTF-8;
Git symlink modes under owned skills remain rejected even when Windows materializes them
as ordinary files. No persisted transaction schema or historical receipt is rewritten.

Implementation, verification, PR-open, and merge attempts do not qualify. A sync failure is
post-integration local state and cannot rewrite Git integration. Existing Pi sessions still
require `/reload`; the command does not claim or control an interactive reload. Its authority
grants no merge, provider, wiki-sync, bootstrap, cleanup, or future unrelated sync.
