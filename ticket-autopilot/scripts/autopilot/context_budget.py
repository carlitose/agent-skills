from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence


CONTEXT_BUDGET_SCHEMA = 1
CONTEXT_BUDGET_UNIT = "normalized-utf8-bytes"
DEFAULT_WORKFLOW = "ticket-autopilot"
DEFAULT_CEILING_CONFIG = "ticket-autopilot/references/context-budget-ceilings-v1.json"
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
WORKFLOW_LEAF_SKILLS: dict[str, tuple[str, ...]] = {
    DEFAULT_WORKFLOW: (
        "code-simplification",
        "code-review",
        "qa-test-plan",
        "verification-audit",
    )
}
_FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---(?:\n|\Z)", re.DOTALL)
_FIELD = re.compile(r"^(?P<key>[A-Za-z0-9_-]+):\s*(?P<value>.*)$")
_VOLATILE_BOUND = re.compile(r"`max_volatile_bytes`:\s*`(?P<bytes>[0-9]+)`")


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


def _measure_leaf_inputs(
    repo: Path,
    workflow: str | None,
    workflow_leaf_skills: Mapping[str, Sequence[str]],
    diagnostics: list[dict[str, str]],
) -> dict[str, Any] | None:
    if workflow is None or workflow not in workflow_leaf_skills:
        return None
    leaf_names = tuple(workflow_leaf_skills[workflow])
    if len(set(leaf_names)) != len(leaf_names):
        raise ContextBudgetError(f"workflow {workflow!r} has a duplicate leaf skill")
    diagnostic_count = len(diagnostics)
    leaves: list[dict[str, Any]] = []
    for name in leaf_names:
        relative = f"{name}/SKILL.md"
        path = repo / relative
        try:
            text = normalized_text(path.read_bytes())
            matches = list(_VOLATILE_BOUND.finditer(text))
            if len(matches) != 1:
                raise ContextBudgetError(
                    f"{relative}: expected exactly one max_volatile_bytes declaration"
                )
            bound = int(matches[0].group("bytes"))
            if bound <= 0:
                raise ContextBudgetError(
                    f"{relative}: max_volatile_bytes must be positive"
                )
        except (ContextBudgetError, UnicodeDecodeError, OSError) as error:
            diagnostics.append(
                _diagnostic("unreadable-leaf-bound", str(error), relative)
            )
            continue
        leaves.append(
            {
                "leaf": name,
                "path": relative,
                "max_volatile_bytes": bound,
            }
        )
    complete = len(diagnostics) == diagnostic_count
    return {
        "workflow": workflow,
        "complete": complete,
        "aggregation": "maximum-applicable-leaf-per-turn",
        "normalized_bytes": (
            max((item["max_volatile_bytes"] for item in leaves), default=0)
            if complete
            else None
        ),
        "leaf_count": len(leaves),
        "expected_leaf_count": len(leaf_names),
        "leaves": leaves,
    }


def _read_ceiling_config(
    repo: Path,
    workflow: str | None,
    requested_path: Path | None,
) -> tuple[Path | None, dict[str, Any] | None]:
    if workflow is None:
        return None, None
    path = (
        requested_path.resolve()
        if requested_path is not None
        else repo / DEFAULT_CEILING_CONFIG
    )
    if not path.is_file():
        if requested_path is not None:
            raise ContextBudgetError(f"ceiling config does not exist: {path}")
        return None, None
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError) as error:
        raise ContextBudgetError(f"ceiling config is unreadable: {error}") from error
    if not isinstance(document, dict) or set(document) != {
        "schema",
        "unit",
        "workflows",
    }:
        raise ContextBudgetError("ceiling config must contain schema, unit, and workflows")
    if document["schema"] != 1 or document["unit"] != CONTEXT_BUDGET_UNIT:
        raise ContextBudgetError("ceiling config schema or unit is unsupported")
    workflows = document["workflows"]
    if not isinstance(workflows, dict):
        raise ContextBudgetError("ceiling config workflows must be an object")
    entry = workflows.get(workflow)
    if entry is None:
        return path, None
    if not isinstance(entry, dict) or set(entry) != {
        "ceiling_bytes",
        "rationale",
        "raised_by",
    }:
        raise ContextBudgetError(
            f"ceiling config workflow {workflow!r} has unsupported fields"
        )
    ceiling_bytes = entry["ceiling_bytes"]
    if (
        isinstance(ceiling_bytes, bool)
        or not isinstance(ceiling_bytes, int)
        or ceiling_bytes <= 0
    ):
        raise ContextBudgetError("ceiling_bytes must be a positive integer")
    if not isinstance(entry["rationale"], str) or not entry["rationale"].strip():
        raise ContextBudgetError("ceiling rationale must be non-empty text")
    if not isinstance(entry["raised_by"], str) or not entry["raised_by"].strip():
        raise ContextBudgetError("ceiling raised_by must be non-empty text")
    return path, entry


def _ceiling_result(
    *,
    workflow: str | None,
    total: int | None,
    config_path: Path | None,
    entry: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if entry is None:
        return {
            "configured": False,
            "status": "informational",
            "workflow": workflow,
            "config_path": str(config_path) if config_path is not None else None,
            "ceiling_bytes": None,
            "delta_bytes": None,
            "rationale": None,
            "raised_by": None,
        }
    ceiling_bytes = entry["ceiling_bytes"]
    status = "unavailable" if total is None else (
        "exceeded" if total > ceiling_bytes else "within"
    )
    return {
        "configured": True,
        "status": status,
        "workflow": workflow,
        "config_path": str(config_path),
        "ceiling_bytes": ceiling_bytes,
        "delta_bytes": total - ceiling_bytes if total is not None else None,
        "rationale": entry["rationale"],
        "raised_by": entry["raised_by"],
    }


def measure_context_budget(
    repo: Path,
    *,
    install_root: Path,
    workflow: str | None = DEFAULT_WORKFLOW,
    workflow_manifests: Mapping[str, Sequence[str]] = WORKFLOW_MANIFESTS,
    workflow_leaf_skills: Mapping[str, Sequence[str]] = WORKFLOW_LEAF_SKILLS,
    ceiling_config: Path | None = None,
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
    leaf_inputs = _measure_leaf_inputs(
        resolved_repo, workflow, workflow_leaf_skills, diagnostics
    )
    complete = listing["complete"] and (
        closure is None or closure["complete"]
    ) and (
        leaf_inputs is None or leaf_inputs["complete"]
    )
    listing_bytes = listing["normalized_bytes"]
    closure_bytes = closure["normalized_bytes"] if closure is not None else None
    variable_bytes = (
        leaf_inputs["normalized_bytes"] if leaf_inputs is not None else None
    )
    composed_total = (
        listing_bytes + closure_bytes + variable_bytes
        if (
            listing_bytes is not None
            and closure_bytes is not None
            and variable_bytes is not None
        )
        else None
    )
    scenarios = []
    if composed_total is not None and leaf_inputs is not None:
        fixed_bytes = listing_bytes + closure_bytes
        scenarios = [
            {
                "leaf": item["leaf"],
                "fixed_bytes": fixed_bytes,
                "variable_leaf_input_bytes": item["max_volatile_bytes"],
                "composed_total_bytes": fixed_bytes
                + item["max_volatile_bytes"],
            }
            for item in leaf_inputs["leaves"]
        ]
    worst_case = (
        max(scenarios, key=lambda item: (item["composed_total_bytes"], item["leaf"]))
        if scenarios
        else None
    )
    config_path, ceiling_entry = _read_ceiling_config(
        resolved_repo, workflow, ceiling_config
    )
    ceiling = _ceiling_result(
        workflow=workflow,
        total=composed_total,
        config_path=config_path,
        entry=ceiling_entry,
    )
    return {
        "schema": CONTEXT_BUDGET_SCHEMA,
        "complete": complete,
        "unit": CONTEXT_BUDGET_UNIT,
        "repository": str(resolved_repo),
        "install_root": str(resolved_install),
        "workflow": workflow,
        "measurement_kind": "upper-bound",
        "observed_consumption": False,
        "worst_case_assumptions": [
            "Every repository-controlled visible listing byte is present.",
            "The complete selected workflow static closure is present.",
            "The invoked leaf may consume its full declared volatile-input bound.",
            "A turn invokes one applicable leaf, so mutually exclusive leaf bounds are maximized rather than summed.",
            "Host-owned prompts, chat history, tool schemas, model output, and cache behavior are excluded because local measurement cannot observe them.",
        ],
        "components": {
            "always_on_listing_bytes": listing_bytes,
            "workflow_static_closure_bytes": closure_bytes,
            "variable_leaf_input_bytes": variable_bytes,
            "composed_total_bytes": composed_total,
        },
        "always_on_listing": listing,
        "workflow_static_closure": closure,
        "variable_leaf_inputs": leaf_inputs,
        "composed_scenarios": scenarios,
        "worst_case_scenario": worst_case,
        "ceiling": ceiling,
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
    leaf_inputs = report["variable_leaf_inputs"]
    if leaf_inputs is not None:
        lines.append(
            "VARIABLE_LEAF_INPUT"
            f"\t{leaf_inputs['normalized_bytes'] if leaf_inputs['complete'] else '-'}"
            f"\tcomplete={str(leaf_inputs['complete']).lower()}"
            f"\taggregation={leaf_inputs['aggregation']}"
        )
        for leaf in leaf_inputs["leaves"]:
            lines.append(
                "LEAF_BOUND"
                f"\t{leaf['leaf']}"
                f"\t{leaf['max_volatile_bytes']}"
            )
    lines.append(
        "COMPOSED_TOTAL"
        f"\t{report['components']['composed_total_bytes'] if report['components']['composed_total_bytes'] is not None else '-'}"
        "\tkind=upper-bound"
        "\tobserved-consumption=false"
    )
    ceiling = report["ceiling"]
    lines.append(
        "CEILING"
        f"\t{ceiling['status']}"
        f"\t{ceiling['ceiling_bytes'] if ceiling['ceiling_bytes'] is not None else '-'}"
        f"\tdelta={ceiling['delta_bytes'] if ceiling['delta_bytes'] is not None else '-'}"
    )
    for diagnostic in report["diagnostics"]:
        lines.append(
            "DIAGNOSTIC"
            f"\t{diagnostic['code']}"
            f"\t{diagnostic['path']}"
            f"\t{diagnostic['message']}"
        )
    return "\n".join(lines) + "\n"
