from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence


CONTEXT_BUDGET_SCHEMA = 1
CONTEXT_BUDGET_UNIT = "normalized-utf8-bytes"
DEFAULT_WORKFLOW = "ticket-autopilot"
WORKFLOW_MANIFESTS: dict[str, tuple[str, ...]] = {
    DEFAULT_WORKFLOW: (
        "ticket-autopilot/SKILL.md",
        "execute-ticket/SKILL.md",
        "code-simplification/SKILL.md",
        "code-review/SKILL.md",
        "qa-test-plan/SKILL.md",
        "verification-audit/SKILL.md",
        "explain-pr/SKILL.md",
        "ticket-autopilot/references/ticket-envelope-v1.md",
        "ticket-autopilot/references/delivery-pr-body-v1.md",
        "ticket-autopilot/references/merge-critical-path-v1.md",
        "verification-audit/references/verification-record.md",
    )
}
_FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---(?:\n|\Z)", re.DOTALL)
_FIELD = re.compile(r"^(?P<key>[A-Za-z0-9_-]+):\s*(?P<value>.*)$")


class ContextBudgetError(ValueError):
    pass


def normalized_text(value: str | bytes) -> str:
    text = value.decode("utf-8", errors="strict") if isinstance(value, bytes) else value
    return text.replace("\r\n", "\n").replace("\r", "\n")


def normalized_bytes(value: str | bytes) -> int:
    return len(normalized_text(value).encode("utf-8", errors="strict"))


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] == '"':
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError as error:
            raise ContextBudgetError(f"invalid quoted front matter value: {value}") from error
        if not isinstance(decoded, str):
            raise ContextBudgetError(f"front matter value is not text: {value}")
        return decoded
    if len(value) >= 2 and value[0] == value[-1] == "'":
        return value[1:-1].replace("''", "'")
    return value


def _front_matter(value: bytes, *, source: str) -> dict[str, str]:
    text = normalized_text(value)
    match = _FRONT_MATTER.match(text)
    if match is None:
        raise ContextBudgetError(f"{source}: missing or unterminated front matter")
    fields: dict[str, str] = {}
    for number, line in enumerate(match.group(1).splitlines(), start=2):
        if not line.strip():
            continue
        if line.startswith((" ", "\t")):
            raise ContextBudgetError(
                f"{source}:{number}: multiline front matter is unsupported"
            )
        field = _FIELD.fullmatch(line)
        if field is None:
            raise ContextBudgetError(f"{source}:{number}: malformed front matter field")
        key = field.group("key")
        if key in fields:
            raise ContextBudgetError(f"{source}:{number}: duplicate field {key!r}")
        fields[key] = _unquote(field.group("value").strip())
    name = fields.get("name", "")
    description = fields.get("description", "")
    if not name or not description:
        raise ContextBudgetError(f"{source}: name and description are required")
    hidden = fields.get("disable-model-invocation", "false")
    if hidden not in {"true", "false"}:
        raise ContextBudgetError(
            f"{source}: disable-model-invocation must be true or false"
        )
    return {
        "name": name,
        "description": description,
        "hidden": hidden,
    }


def _word_count(text: str) -> int:
    return len(re.findall(r"\S+", text))


def _listing_text(name: str, description: str) -> str:
    return f"{name}: {description}\n"


def _diagnostic(code: str, message: str, path: str) -> dict[str, str]:
    return {"code": code, "message": message, "path": path}


def _repository_skills(repo: Path) -> dict[str, Path]:
    return {
        folder.name: skill
        for folder in sorted(repo.iterdir(), key=lambda item: item.name)
        if folder.is_dir() and (skill := folder / "SKILL.md").is_file()
    }


def _measure_listing(
    repo: Path, install_root: Path, diagnostics: list[dict[str, str]]
) -> dict[str, Any]:
    diagnostic_count = len(diagnostics)
    repository_skills = _repository_skills(repo)
    skills: list[dict[str, Any]] = []
    visible_bytes = 0
    visible_words = 0
    hidden_bytes = 0
    hidden_words = 0
    visible_count = 0
    hidden_count = 0
    repository_only_count = 0
    for directory_name, repository_path in repository_skills.items():
        installed_path = install_root / directory_name / "SKILL.md"
        installed = installed_path.is_file()
        source_path = installed_path if installed else repository_path
        display_path = (
            f"install-root/{directory_name}/SKILL.md"
            if installed
            else f"repository/{directory_name}/SKILL.md"
        )
        try:
            matter = _front_matter(source_path.read_bytes(), source=display_path)
            if matter["name"] != directory_name:
                raise ContextBudgetError(
                    f"{display_path}: name {matter['name']!r} differs from directory"
                )
        except (ContextBudgetError, UnicodeDecodeError, OSError) as error:
            diagnostics.append(
                _diagnostic("malformed-front-matter", str(error), display_path)
            )
            skills.append(
                {
                    "name": directory_name,
                    "status": "malformed",
                    "source": "install-root" if installed else "repository",
                    "normalized_bytes": None,
                    "word_count": None,
                }
            )
            continue
        listing_text = _listing_text(matter["name"], matter["description"])
        byte_count = normalized_bytes(listing_text)
        word_count = _word_count(listing_text)
        if not installed:
            status = "repository-only"
            repository_only_count += 1
        elif matter["hidden"] == "true":
            status = "installed-hidden"
            hidden_count += 1
            hidden_bytes += byte_count
            hidden_words += word_count
        else:
            status = "installed-visible"
            visible_count += 1
            visible_bytes += byte_count
            visible_words += word_count
        skills.append(
            {
                "name": matter["name"],
                "status": status,
                "source": "install-root" if installed else "repository",
                "normalized_bytes": byte_count,
                "word_count": word_count,
            }
        )
    external_installed = []
    if install_root.is_dir():
        external_installed = sorted(
            folder.name
            for folder in install_root.iterdir()
            if folder.is_dir()
            and (folder / "SKILL.md").is_file()
            and folder.name not in repository_skills
        )
    else:
        diagnostics.append(
            _diagnostic(
                "missing-install-root",
                f"install root does not exist: {install_root}",
                "install-root",
            )
        )
    complete = len(diagnostics) == diagnostic_count
    return {
        "complete": complete,
        "normalized_bytes": visible_bytes if complete else None,
        "word_count": visible_words if complete else None,
        "visible_skill_count": visible_count,
        "hidden_listing_bytes": hidden_bytes if complete else None,
        "hidden_word_count": hidden_words if complete else None,
        "hidden_skill_count": hidden_count,
        "repository_only_skill_count": repository_only_count,
        "external_installed_skills": external_installed,
        "skills": skills,
    }


def _measure_workflow(
    repo: Path,
    workflow: str | None,
    manifests: Mapping[str, Sequence[str]],
    diagnostics: list[dict[str, str]],
) -> dict[str, Any] | None:
    if workflow is None:
        return None
    if workflow not in manifests:
        raise ContextBudgetError(f"unknown workflow {workflow!r}")
    manifest = tuple(manifests[workflow])
    if len(set(manifest)) != len(manifest):
        raise ContextBudgetError(f"workflow {workflow!r} has a duplicate logical source")
    diagnostic_count = len(diagnostics)
    sources: list[dict[str, Any]] = []
    for relative in manifest:
        path = repo / Path(relative)
        try:
            raw = path.read_bytes()
            text = normalized_text(raw)
        except (UnicodeDecodeError, OSError) as error:
            diagnostics.append(
                _diagnostic("unreadable-workflow-source", str(error), relative)
            )
            continue
        encoded = text.encode("utf-8", errors="strict")
        sources.append(
            {
                "logical_source": relative,
                "path": relative,
                "normalized_bytes": len(encoded),
                "word_count": _word_count(text),
                "sha256": hashlib.sha256(encoded).hexdigest(),
            }
        )
    complete = len(diagnostics) == diagnostic_count
    return {
        "workflow": workflow,
        "complete": complete,
        "normalized_bytes": (
            sum(item["normalized_bytes"] for item in sources) if complete else None
        ),
        "word_count": sum(item["word_count"] for item in sources) if complete else None,
        "source_count": len(sources),
        "expected_source_count": len(manifest),
        "sources": sources,
    }


def measure_context_budget(
    repo: Path,
    *,
    install_root: Path,
    workflow: str | None = DEFAULT_WORKFLOW,
    workflow_manifests: Mapping[str, Sequence[str]] = WORKFLOW_MANIFESTS,
) -> dict[str, Any]:
    resolved_repo = repo.resolve()
    resolved_install = install_root.resolve()
    if not resolved_repo.is_dir():
        raise ContextBudgetError(f"repository root does not exist: {resolved_repo}")
    diagnostics: list[dict[str, str]] = []
    listing = _measure_listing(resolved_repo, resolved_install, diagnostics)
    closure = _measure_workflow(
        resolved_repo, workflow, workflow_manifests, diagnostics
    )
    complete = listing["complete"] and (
        closure is None or closure["complete"]
    )
    return {
        "schema": CONTEXT_BUDGET_SCHEMA,
        "complete": complete,
        "unit": CONTEXT_BUDGET_UNIT,
        "repository": str(resolved_repo),
        "install_root": str(resolved_install),
        "workflow": workflow,
        "components": {
            "always_on_listing_bytes": listing["normalized_bytes"],
            "workflow_static_closure_bytes": (
                closure["normalized_bytes"] if closure is not None else None
            ),
        },
        "always_on_listing": listing,
        "workflow_static_closure": closure,
        "diagnostics": diagnostics,
    }


def render_context_budget(report: Mapping[str, Any]) -> str:
    listing = report["always_on_listing"]
    closure = report["workflow_static_closure"]
    lines = [
        f"UNIT\t{report['unit']}",
        (
            "ALWAYS_ON_LISTING"
            f"\t{listing['normalized_bytes'] if listing['complete'] else '-'}"
            f"\tcomplete={str(listing['complete']).lower()}"
            f"\tvisible={listing['visible_skill_count']}"
            f"\thidden={listing['hidden_skill_count']}"
            f"\trepository-only={listing['repository_only_skill_count']}"
        ),
    ]
    for skill in listing["skills"]:
        lines.append(
            "SKILL"
            f"\t{skill['status']}"
            f"\t{skill['name']}"
            f"\t{skill['normalized_bytes'] if skill['normalized_bytes'] is not None else '-'}"
        )
    if closure is not None:
        lines.append(
            "WORKFLOW_STATIC_CLOSURE"
            f"\t{closure['workflow']}"
            f"\t{closure['normalized_bytes'] if closure['complete'] else '-'}"
            f"\tcomplete={str(closure['complete']).lower()}"
            f"\tsources={closure['source_count']}"
        )
        for source in closure["sources"]:
            lines.append(
                "SOURCE"
                f"\t{source['normalized_bytes']}"
                f"\t{source['path']}"
                f"\t{source['sha256']}"
            )
    for diagnostic in report["diagnostics"]:
        lines.append(
            "DIAGNOSTIC"
            f"\t{diagnostic['code']}"
            f"\t{diagnostic['path']}"
            f"\t{diagnostic['message']}"
        )
    return "\n".join(lines) + "\n"
