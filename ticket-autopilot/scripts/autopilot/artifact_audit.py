from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

from .ticket_inventory import inventory_tickets


ARTIFACT_AUDIT_SCHEMA = 1
ARTIFACT_ROLES = {"wayfinder", "spec", "ticket", "research"}
_FIELD = re.compile(r"^- (?P<name>Artifact ID|Role|Standalone|Parent):\s*(?P<value>.+?)\s*$")
_LINK_ITEM = re.compile(r"^- \[[^]]+\]\(([^)]+)\)\s*$")
_LINK_VALUE = re.compile(r"^\[[^]]+\]\(([^)]+)\)$")


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] == "`":
        return value[1:-1]
    return value


def _link_target(source: Path, value: str) -> Path | None:
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc or not parsed.path:
        return None
    return (source.parent / unquote(parsed.path)).resolve()


def _inside_managed_root(path: Path, roots: tuple[Path, ...]) -> bool:
    return any(path.is_relative_to(root) for root in roots)


def _has_symlink_component(path: Path, root: Path) -> bool:
    current = root
    for part in path.relative_to(root).parts:
        current /= part
        if current.is_symlink():
            return True
    return False


def _git_changed_paths(root: Path) -> set[str]:
    paths: set[str] = set()
    commands = (
        ("diff", "--name-only", "-z", "HEAD", "--"),
        ("ls-files", "--others", "--exclude-standard", "-z", "--"),
    )
    scopes = ("docs/tickets", "docs/specs", "docs/research")
    for command in commands:
        try:
            result = subprocess.run(
                ["git", "-C", str(root), *command, *scopes],
                check=False,
                capture_output=True,
            )
        except OSError:
            return set()
        if result.returncode != 0:
            continue
        paths.update(
            item.decode("utf-8", "surrogateescape")
            for item in result.stdout.split(b"\0")
            if item
        )
    return paths


def _visible_markdown_lines(text: str) -> list[str]:
    visible: list[str] = []
    fence: str | None = None
    for line in text.splitlines():
        stripped = line.lstrip()
        if fence is not None:
            if stripped.startswith(fence):
                fence = None
            continue
        if stripped.startswith("```"):
            fence = "```"
            continue
        if stripped.startswith("~~~"):
            fence = "~~~"
            continue
        visible.append(line)
    return visible


def _parse_graph(text: str, path: Path, root: Path) -> dict[str, Any] | None:
    lines = _visible_markdown_lines(text)
    try:
        start = lines.index("## Artifact Graph") + 1
    except ValueError:
        return None

    fields: dict[str, list[str]] = {}
    links: dict[str, list[str]] = {"children": [], "produces": [], "related": []}
    malformed_relationships = 0
    collection: str | None = None
    for line in lines[start:]:
        if line.startswith("## "):
            break
        if line in {"### Children", "### Produces", "### Related"}:
            collection = line[4:].lower()
            continue
        field = _FIELD.match(line)
        if field:
            fields.setdefault(
                field.group("name").lower().replace(" ", "_"), []
            ).append(field.group("value"))
            collection = None
            continue
        if collection and line.startswith("- "):
            match = _LINK_ITEM.fullmatch(line)
            if match:
                links[collection].append(match.group(1))
            else:
                malformed_relationships += 1

    node: dict[str, Any] = {
        "id": _unquote(fields.get("artifact_id", [""])[-1]),
        "role": _unquote(fields.get("role", [""])[-1]),
        "path": _relative(path, root),
        **links,
        "_fields": fields,
        "_section_count": lines.count("## Artifact Graph"),
        "_malformed_relationships": malformed_relationships,
    }
    if fields.get("standalone", [""])[-1].lower() == "true":
        node["standalone"] = True
        node["parent"] = None
    else:
        parent = _LINK_VALUE.fullmatch(fields.get("parent", [""])[-1])
        node["standalone"] = False
        node["parent"] = parent.group(1) if parent else None
    return node


def audit_artifacts(root: Path) -> dict[str, Any]:
    """Read and validate the Markdown artifact graph below a repository root."""

    resolved = root.resolve()
    if not resolved.is_dir():
        raise FileNotFoundError(f"artifact audit root does not exist: {resolved}")
    nodes: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, str]] = []
    unreferenced: list[dict[str, str]] = []
    managed_documents: dict[Path, str] = {}
    managed_roots = tuple(
        (resolved / "docs" / folder).resolve()
        for folder in ("tickets", "specs", "research")
    )
    strict_paths = _git_changed_paths(resolved)
    for folder in ("tickets", "specs", "research"):
        directory = resolved / "docs" / folder
        if _has_symlink_component(directory, resolved):
            errors.append(
                {
                    "code": "path-escape",
                    "message": "managed artifact roots may not resolve through a symlink",
                    "path": _relative(directory, resolved),
                }
            )
            continue
        if not directory.is_dir():
            continue
        for path in sorted(directory.rglob("*")):
            if path.is_symlink():
                errors.append(
                    {
                        "code": "path-escape",
                        "message": "managed artifacts may not resolve through a symlink",
                        "path": _relative(path, resolved),
                    }
                )
                continue
            if path.suffix != ".md" or not path.is_file():
                continue
            if _has_symlink_component(path, resolved) or not _inside_managed_root(
                path.resolve(), managed_roots
            ):
                errors.append(
                    {
                        "code": "path-escape",
                        "message": "managed artifact may not resolve through a symlink",
                        "path": _relative(path, resolved),
                    }
                )
                continue
            try:
                node = _parse_graph(path.read_text(encoding="utf-8"), path, resolved)
            except UnicodeDecodeError:
                relative = _relative(path, resolved)
                managed_documents[path.resolve()] = relative
                diagnostic = errors if relative in strict_paths else warnings
                diagnostic.append(
                    {
                        "code": "malformed-markdown",
                        "message": "managed Markdown is not valid UTF-8",
                        "path": relative,
                    }
                )
                continue
            if node is None:
                relative = _relative(path, resolved)
                managed_documents[path.resolve()] = relative
                if relative in strict_paths:
                    errors.append(
                        {
                            "code": "missing-artifact-graph",
                            "message": "new or modified managed Markdown requires an Artifact Graph section",
                            "path": relative,
                        }
                    )
                else:
                    warnings.append(
                        {
                            "code": "legacy-artifact",
                            "message": "managed Markdown has no Artifact Graph section",
                            "path": relative,
                        }
                    )
            else:
                managed_documents[path.resolve()] = node["path"]
                nodes.append(node)

    referenced_paths: set[Path] = set()
    for node in nodes:
        fields = node.pop("_fields")
        section_count = node.pop("_section_count")
        malformed_relationships = node.pop("_malformed_relationships")
        path = node["path"]
        if section_count != 1:
            errors.append(
                {
                    "code": "duplicate-artifact-graph-section",
                    "message": "strict artifact requires exactly one Artifact Graph section",
                    "path": path,
                }
            )
        if malformed_relationships:
            errors.append(
                {
                    "code": "malformed-relationship",
                    "message": "canonical relationship entries must be single Markdown links",
                    "path": path,
                }
            )
        if len(fields.get("artifact_id", [])) != 1 or not node["id"]:
            errors.append(
                {
                    "code": "missing-artifact-id",
                    "message": "strict artifact requires exactly one Artifact ID",
                    "path": path,
                }
            )
        if len(fields.get("role", [])) != 1 or node["role"] not in ARTIFACT_ROLES:
            errors.append(
                {
                    "code": "invalid-role",
                    "message": "Role must be wayfinder, spec, ticket, or research",
                    "path": path,
                }
            )
        standalone = fields.get("standalone", [])
        parents = fields.get("parent", [])
        valid_choice = (
            standalone == ["true"] and not parents
        ) or (
            not standalone and len(parents) == 1 and node["parent"] is not None
        )
        if not valid_choice:
            errors.append(
                {
                    "code": "invalid-root-parent",
                    "message": "declare exactly Standalone: true or one Parent link",
                    "path": path,
                }
            )
        if path.startswith("docs/tickets/") and standalone:
            errors.append(
                {
                    "code": "standalone-ticket",
                    "message": "ticket artifacts may not be standalone",
                    "path": path,
                }
            )
        if (
            path.startswith("docs/tickets/")
            and node["role"] in ARTIFACT_ROLES
            and node["role"] != "ticket"
        ):
            errors.append(
                {
                    "code": "ticket-role-mismatch",
                    "message": "canonical Ticket Envelope sources require Role: ticket",
                    "path": path,
                }
            )
        if node["produces"] and node["role"] != "ticket":
            errors.append(
                {
                    "code": "invalid-produces-owner",
                    "message": "only ticket artifacts may declare Produces",
                    "path": path,
                }
            )
        source = resolved / path
        child_targets = {
            target
            for value in node["children"]
            if (target := _link_target(source, value)) is not None
        }
        produced_targets = {
            target
            for value in node["produces"]
            if (target := _link_target(source, value)) is not None
        }
        if child_targets & produced_targets:
            errors.append(
                {
                    "code": "duplicate-ownership-edge",
                    "message": "one target may not appear in both Children and Produces",
                    "path": path,
                }
            )

    nodes_by_path = {
        (resolved / node["path"]).resolve(): node
        for node in nodes
    }
    nodes_by_id: dict[str, list[dict[str, Any]]] = {}
    for node in nodes:
        if node["id"]:
            nodes_by_id.setdefault(node["id"], []).append(node)
    for artifact_id, matches in sorted(nodes_by_id.items()):
        if len(matches) < 2:
            continue
        paths = sorted(node["path"] for node in matches)
        errors.append(
            {
                "code": "duplicate-artifact-id",
                "message": f"Artifact ID {artifact_id!r} is declared more than once",
                "path": paths[0],
                "paths": paths,
            }
        )
    for node in nodes:
        source = resolved / node["path"]
        references = [
            *([("parent", [node["parent"]])] if node["parent"] else []),
            ("children", node["children"]),
            ("produces", node["produces"]),
            ("related", node["related"]),
        ]
        for relationship, values in references:
            for value in values:
                target = _link_target(source, value)
                if target is None or not _inside_managed_root(target, managed_roots):
                    errors.append(
                        {
                            "code": "path-escape",
                            "message": f"{relationship} link leaves managed artifact roots: {value}",
                            "path": node["path"],
                        }
                    )
                elif target not in nodes_by_path:
                    if target in managed_documents:
                        referenced_paths.add(target)
                    errors.append(
                        {
                            "code": "broken-link",
                            "message": f"{relationship} link has no strict artifact target: {value}",
                            "path": node["path"],
                        }
                    )
                else:
                    referenced_paths.add(target)

    ownership_edges: dict[Path, list[tuple[Path, str]]] = {}
    for owner in nodes:
        owner_path = (resolved / owner["path"]).resolve()
        source = resolved / owner["path"]
        for relationship in ("children", "produces"):
            for value in owner[relationship]:
                target = _link_target(source, value)
                if target in nodes_by_path:
                    ownership_edges.setdefault(target, []).append(
                        (owner_path, relationship)
                    )

    for child in nodes:
        child_path = (resolved / child["path"]).resolve()
        if not child["parent"]:
            continue
        parent_path = _link_target(resolved / child["path"], child["parent"])
        if parent_path not in nodes_by_path:
            continue
        matching = [
            edge
            for edge in ownership_edges.get(child_path, [])
            if edge[0] == parent_path
        ]
        if len(matching) != 1:
            errors.append(
                {
                    "code": "reciprocity-mismatch",
                    "message": "Parent must have exactly one matching Children or Produces edge",
                    "path": child["path"],
                }
            )
        elif (
            child["role"] == "research"
            and nodes_by_path[parent_path]["role"] == "ticket"
            and matching[0][1] != "produces"
        ):
            errors.append(
                {
                    "code": "research-output-not-produced",
                    "message": "ticket-owned research results require a Produces edge",
                    "path": child["path"],
                }
            )

    for target_path, owner_edges in ownership_edges.items():
        target = nodes_by_path[target_path]
        target_parent = (
            _link_target(resolved / target["path"], target["parent"])
            if target["parent"]
            else None
        )
        for owner_path, relationship in owner_edges:
            if target_parent == owner_path:
                continue
            errors.append(
                {
                    "code": "reciprocity-mismatch",
                    "message": f"{relationship} target must point back to its owner",
                    "path": nodes_by_path[owner_path]["path"],
                }
            )

    hierarchy: dict[Path, list[Path]] = {path: [] for path in nodes_by_path}
    for target_path, owner_edges in ownership_edges.items():
        for owner_path, _relationship in owner_edges:
            hierarchy[owner_path].append(target_path)
    visiting: list[Path] = []
    visited: set[Path] = set()
    cycles: set[frozenset[Path]] = set()

    def visit(path: Path) -> None:
        if path in visiting:
            cycles.add(frozenset(visiting[visiting.index(path) :]))
            return
        if path in visited:
            return
        visiting.append(path)
        for target in sorted(hierarchy[path], key=lambda item: item.as_posix()):
            visit(target)
        visiting.pop()
        visited.add(path)

    for path in sorted(hierarchy, key=lambda item: item.as_posix()):
        visit(path)
    for cycle in sorted(
        cycles,
        key=lambda paths: sorted(nodes_by_path[path]["path"] for path in paths),
    ):
        paths = sorted(nodes_by_path[path]["path"] for path in cycle)
        errors.append(
            {
                "code": "hierarchy-cycle",
                "message": "ownership hierarchy cycle: " + ", ".join(paths),
                "path": paths[0],
                "paths": paths,
            }
        )

    ticket_root = resolved / "docs" / "tickets"
    if ticket_root.is_dir() and not _has_symlink_component(ticket_root, resolved):
        inventory = inventory_tickets(ticket_root)
        ticket_by_path = {
            f"docs/tickets/{item['path']}": item
            for item in inventory["tickets"]
        }
        projection_fields = (
            "id",
            "title",
            "disposition",
            "lifecycle",
            "attempt_outcome",
            "mode",
            "blockers",
            "readiness",
            "readiness_causes",
            "stop_reason",
        )
        for node in nodes:
            ticket = ticket_by_path.get(node["path"])
            if ticket is not None:
                node["ticket"] = {
                    field: ticket[field]
                    for field in projection_fields
                }
        for diagnostic in inventory["diagnostics"]:
            path = diagnostic.get("path", diagnostic.get("folder", "."))
            errors.append(
                {
                    "code": diagnostic["code"],
                    "message": diagnostic["message"],
                    "path": f"docs/tickets/{path}".rstrip("/"),
                }
            )

    for path, relative in sorted(
        managed_documents.items(), key=lambda item: item[1]
    ):
        node = nodes_by_path.get(path)
        if (node is not None and node["standalone"]) or path in referenced_paths:
            continue
        unreferenced.append(
            {
                "code": "unreferenced-artifact",
                "message": "managed Markdown is not canonically referenced",
                "path": relative,
            }
        )

    nodes.sort(key=lambda node: (node["id"], node["path"]))
    errors.sort(key=lambda item: (item["path"], item["code"]))
    warnings.sort(key=lambda item: (item["path"], item["code"]))
    return {
        "schema": ARTIFACT_AUDIT_SCHEMA,
        "root": str(resolved),
        "nodes": nodes,
        "errors": errors,
        "warnings": warnings,
        "unreferenced": unreferenced,
        "migration": {
            "automatic_changes": False,
            "required": len(warnings),
            "paths": [item["path"] for item in warnings],
        },
    }


def _cell(value: object) -> str:
    return " ".join(str(value).split())


def render_artifact_audit(result: dict[str, Any]) -> str:
    """Render the versioned audit as deterministic tab-separated text."""

    lines = [
        f"Artifact audit: {result['root']}",
        f"NODES\t{len(result['nodes'])}",
        f"ERRORS\t{len(result['errors'])}",
        f"WARNINGS\t{len(result['warnings'])}",
        f"UNREFERENCED\t{len(result['unreferenced'])}",
        f"MIGRATION_REQUIRED\t{result['migration']['required']}",
        "AUTOMATIC_CHANGES\tfalse",
    ]
    if result["nodes"]:
        lines.extend(("", "ARTIFACT_ID\tROLE\tROOT_OR_PARENT\tPATH"))
        lines.extend(
            "\t".join(
                (
                    _cell(node["id"]),
                    _cell(node["role"]),
                    "standalone" if node["standalone"] else _cell(node["parent"]),
                    _cell(node["path"]),
                )
            )
            for node in result["nodes"]
        )
    for heading, key in (
        ("ERROR DETAILS", "errors"),
        ("WARNING DETAILS", "warnings"),
        ("UNREFERENCED DETAILS", "unreferenced"),
    ):
        if result[key]:
            lines.extend(("", heading))
            lines.extend(
                f"{item['code']}\t{_cell(item['path'])}\t{_cell(item['message'])}"
                for item in result[key]
            )
    return "\n".join(lines) + "\n"
