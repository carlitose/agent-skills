"""Fast lane for existing code-review prose; absence is uncertainty, not a parse error."""
import re
import shlex
import sys

SEVERITY = re.compile(r"^(?:#{1,6}\s+|[-*]\s+)?(?:\*\*)?\[?(blocker|should-fix|nit)\]?\s+(.+)$", re.I)
MARKER = re.compile(r"^(?:#{1,6}\s+|[-*]\s+)?(?:\*\*)?(?:\[(?:blocker|should-fix|nit)\]|(?:blocker|should-fix|nit)\b)", re.I)
PATH = re.compile(r"(?<![\w/])((?:[\w.-]+/)*[\w.-]+\.py)(?::([1-9]\d*))?")
EXPLANATION = re.compile(r"\s+(?:-|\u2014|\u2013)\s+")
CLEAN = re.compile(r"No findings\s*\.?", re.I)
CHECKS = re.compile(r"(?is)^## Automated Checks\s*\n.*?```bash\s*\n(.*?)```", re.M)


def parse_findings(markdown: str) -> dict:
    """Parse explicit prose markers; unknown or contradictory review lines remain a gate."""
    rows = []
    uncertain = False
    clean = False
    fence = None
    for line in markdown.splitlines():
        stripped = line.lstrip()
        if stripped.startswith(("```", "~~~")):
            marker = stripped[:3]
            fence = None if fence == marker else marker if fence is None else fence
            continue
        if fence is not None or line.startswith(("    ", "\t")):
            continue
        if CLEAN.fullmatch(stripped):
            clean = True
            continue
        match = SEVERITY.match(stripped)
        if not match:
            uncertain |= bool(MARKER.match(stripped))
            continue
        parts = EXPLANATION.split(match[2], maxsplit=1)
        location = PATH.search(parts[0]) if len(parts) == 2 else None
        text = parts[1].strip(" *") if len(parts) == 2 else ""
        if not location or not text:
            uncertain = True
            continue
        rows.append({"severity": match[1].lower(), "path": location[1],
                     "line": int(location[2]) if location[2] else None, "text": text})
    if uncertain or (clean and rows):
        return {"state": "unparsed", "findings": rows}
    if rows:
        return {"state": "parsed", "findings": rows}
    return {"state": "clean" if clean else "unparsed", "findings": []}


def parse_directed_findings(markdown: str) -> dict:
    """Ignore a clean line local to a named function, not a global clean claim."""
    lines = []
    named_function = False
    fence = None
    for line in markdown.splitlines():
        stripped = line.lstrip()
        if stripped.startswith(("```", "~~~")):
            marker = stripped[:3]
            fence = None if fence == marker else marker if fence is None else fence
        elif fence is None:
            if stripped.startswith("## "):
                named_function = bool(PATH.search(stripped))
            if named_function and CLEAN.fullmatch(stripped):
                continue
        lines.append(line)
    return parse_findings("\n".join(lines))


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
