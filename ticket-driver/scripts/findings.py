"""Fast lane for existing code-review prose; absence is uncertainty, not a parse error."""
import re
import shlex
import sys

FINDING = re.compile(r"^\s*\[(blocker|should-fix|nit)\]\s+([^:\n]+):(\d+)\s+-\s+(.+)$", re.I | re.M)
CLEAN = re.compile(r"(?im)^\s*No findings\s*\.?\s*$")
CHECKS = re.compile(r"(?is)^## Automated Checks\s*\n.*?```bash\s*\n(.*?)```", re.M)


def parse_findings(markdown: str) -> dict:
    rows = [dict(severity=m[1].lower(), path=m[2].strip(), line=int(m[3]), text=m[4].strip())
            for m in FINDING.finditer(markdown)]
    if rows:
        return {"state": "parsed", "findings": rows}
    if CLEAN.search(markdown):
        return {"state": "clean", "findings": []}
    return {"state": "unparsed", "findings": []}


def planned_commands(markdown: str) -> list[list[str]]:
    match = CHECKS.search(markdown)
    if not match:
        return []
    commands = []
    for line in match[1].splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if len(line) > 400 or any(symbol in line for symbol in ("|", ";", "&", ">", "<", "`", "$", "\n")):
            raise ValueError("QA plan command is not literal argv")
        argv = shlex.split(line, posix=True)
        if not argv or argv[0] not in ("python", "node", "npm"):
            raise ValueError("QA plan command is not an allowed local test command")
        if argv[0] == "python":
            argv[0] = sys.executable
        commands.append(argv)
        if len(commands) > 4:
            raise ValueError("QA plan has more than four commands")
    return commands
