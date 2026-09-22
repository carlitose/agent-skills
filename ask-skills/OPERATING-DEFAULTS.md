## Practical operating defaults

| Default | Behavior |
| --- | --- |
| Proportionate security | Keep security simple and proportionate to the actual risk. Do not add advanced security protocols, new approval layers, or extra procedures unless explicitly requested. |
| Explicit delegation only | Work serially inline with one agent. Create or use subagents only on an explicit user request, within the requested scope. |
| One session per ticket | Treat the ticket's completion document as the cut point and start the next ticket in a new session. A session of 4 638 calls paid 0.176 $ per call where short sessions stay under 0.10 $: a long session pays its whole prefix again on every turn. |
| Batch independent calls | Calls whose inputs do not depend on each other belong in one block. Measured: 16 859 of 17 315 tool turns carried exactly one call, so almost every result cost a full model turn. |
| Check the platform before a shell | Resolve the binary and the platform first (`shutil.which`, `os.name`), and make PowerShell exit through an explicit `$LASTEXITCODE` instead of letting `cmd.exe` decide. Measured: 523 bash results were errors, mostly mixed `\`/`/` paths and exit codes read through the wrong shell. |

AFK, task size, broad research, tool availability, generic host permission, and silence are not delegation requests. Quoted, example, or negated delegation text is not a request. Do not solicit delegation approval merely to complete routine work inline.

Inline skill composition is not delegation; shared-context review is not independent. When requested isolation is unavailable, report the limit rather than simulate independence.

The three numbers above are measurements of this operator's own session logs on 2026-09-22, not
estimates. They are defaults, not prohibitions: a dependent call still waits for its input, and a
ticket that genuinely continues earlier work still continues in place.

Preserve essential secret protection, data integrity, authorization for destructive or external actions, and higher-priority mandatory instructions. Report a genuine conflict rather than bypass it. These defaults neither remove existing runtime protections nor grant merge, publication, cleanup, installation, or reload authority.
