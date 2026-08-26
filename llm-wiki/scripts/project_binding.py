#!/usr/bin/env python3
"""Bind a wiki to the project whose history it compiles.

A wiki is the history of exactly one project, and nothing in the tree records which. This
module holds that binding and resolves it, and it is the only place that knows where the
project lives.

Three facts are kept strictly separate, because conflating them is how a wrong answer gets
presented as a fact:

* whether the configured project root exists;
* whether that project is a Git repository;
* whether one artefact inside it is tracked.

None of the three implies another. A wiki may be committed or ignored, ``docs/`` may be
tracked or not, and the host may not be a repository at all. All four combinations are valid
inputs. Git is one rung of a provenance ladder, never a prerequisite.

Usage:
    python3 project_binding.py <wiki-root> [--json]
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

CONFIG_NAME = "llm-wiki-project.json"
CONFIG_SCHEMA = 1
GIT_MODES = ("auto", "off")
DEFAULT_DOCS_GLOBS = (
    "docs/specs/*.md",
    "docs/tickets/**/*.md",
    "docs/research/*.md",
    "docs/prototypes/**/*.md",
)
DEFAULT_SESSION_PROVIDERS = ("claude-code", "codex")


class BindingError(RuntimeError):
    """The binding is absent, malformed, or points somewhere that is not there."""


def config_path(wiki_root: Path) -> Path:
    """Return the binding file for one wiki root.

    The file sits at the wiki root rather than inside ``wiki/`` or ``raw/`` so the LLM Wiki
    application never sees it: that application watches only ``raw/sources``, ``wiki``,
    ``purpose.md`` and ``schema.md``.
    """

    return wiki_root / CONFIG_NAME


def write_binding(
    wiki_root: Path,
    project_root: Path,
    *,
    docs_globs: tuple[str, ...] = DEFAULT_DOCS_GLOBS,
    git_mode: str = "auto",
    session_providers: tuple[str, ...] = DEFAULT_SESSION_PROVIDERS,
) -> Path:
    """Write the binding for one wiki. Returns the file written."""

    if git_mode not in GIT_MODES:
        raise BindingError(f"git_mode must be one of {GIT_MODES}, got {git_mode!r}")
    document = {
        "schema": CONFIG_SCHEMA,
        "project_root": str(project_root),
        "docs_globs": list(docs_globs),
        "git_mode": git_mode,
        "session_providers": list(session_providers),
    }
    target = config_path(wiki_root)
    target.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return target


def read_binding(wiki_root: Path) -> dict[str, object]:
    """Read and validate the binding without touching the project it names."""

    target = config_path(wiki_root)
    if not target.is_file():
        raise BindingError(f"no wiki binding at {target}")
    try:
        document = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise BindingError(f"{target}: binding is unreadable: {error}") from error
    if not isinstance(document, dict):
        raise BindingError(f"{target}: binding must be an object")
    if document.get("schema") != CONFIG_SCHEMA:
        raise BindingError(f"{target}: binding schema must be {CONFIG_SCHEMA}")
    root = document.get("project_root")
    if not isinstance(root, str) or not root:
        raise BindingError(f"{target}: project_root must be a non-empty string")
    globs = document.get("docs_globs")
    if not isinstance(globs, list) or not globs or not all(
        isinstance(item, str) and item for item in globs
    ):
        raise BindingError(f"{target}: docs_globs must be a non-empty list of strings")
    mode = document.get("git_mode")
    if mode not in GIT_MODES:
        raise BindingError(f"{target}: git_mode must be one of {GIT_MODES}")
    providers = document.get("session_providers")
    if not isinstance(providers, list) or not all(
        isinstance(item, str) and item for item in providers
    ):
        raise BindingError(f"{target}: session_providers must be a list of strings")
    return document


def resolve_project_root(wiki_root: Path) -> Path:
    """Return the project root named by the binding.

    Fails loudly and names the path it tried. It never falls back to the current working
    directory: a silent fallback would make a relocated project look like a project with no
    history rather than a broken binding.
    """

    document = read_binding(wiki_root)
    root = Path(str(document["project_root"]))
    if not root.is_dir():
        raise BindingError(
            f"project_root does not exist: {root} "
            f"(named by {config_path(wiki_root)}); the project may have moved"
        )
    return root


def _git(project_root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(project_root), *arguments],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def is_git_repository(project_root: Path) -> bool:
    """Whether the project is inside a Git work tree.

    Uses ``rev-parse --is-inside-work-tree`` rather than looking for a ``.git`` directory,
    because in a worktree ``.git`` is a file and the common dir lives elsewhere. This says
    nothing about whether any particular file is tracked.
    """

    result = _git(project_root, "rev-parse", "--is-inside-work-tree")
    return result.returncode == 0 and result.stdout.strip() == "true"


def is_tracked(project_root: Path, relative_path: str) -> bool:
    """Whether one artefact is tracked by Git.

    Independent of :func:`is_git_repository`: a repository can hold untracked artefacts, and
    this returns ``False`` both for an untracked file and for a project that is not a
    repository at all. Callers that need to tell those apart must ask both questions.
    """

    if not is_git_repository(project_root):
        return False
    result = _git(project_root, "ls-files", "--error-unmatch", "--", relative_path)
    return result.returncode == 0


def git_enabled(wiki_root: Path) -> bool:
    """Whether Git may be consulted at all for this wiki.

    ``off`` means the operator has taken Git out of the picture; ``auto`` means use it when
    the host is a repository and fall through otherwise.
    """

    document = read_binding(wiki_root)
    if document["git_mode"] == "off":
        return False
    return is_git_repository(resolve_project_root(wiki_root))


def discover_artefacts(wiki_root: Path) -> list[str]:
    """Return the project-relative artefact paths the binding's globs match, sorted."""

    project_root = resolve_project_root(wiki_root)
    document = read_binding(wiki_root)
    found: set[str] = set()
    for pattern in document["docs_globs"]:  # type: ignore[union-attr]
        for path in project_root.glob(str(pattern)):
            if path.is_file():
                found.add(path.relative_to(project_root).as_posix())
    return sorted(found)


def describe(wiki_root: Path) -> dict[str, object]:
    """Return the resolved binding as three separable facts plus the artefact inventory."""

    document = read_binding(wiki_root)
    project_root = resolve_project_root(wiki_root)
    artefacts = discover_artefacts(wiki_root)
    repository = is_git_repository(project_root)
    return {
        "schema": CONFIG_SCHEMA,
        "wiki_root": str(wiki_root),
        "project_root": str(project_root),
        "project_root_exists": True,
        "is_git_repository": repository,
        "git_mode": document["git_mode"],
        "git_enabled": bool(document["git_mode"] == "auto" and repository),
        "docs_globs": document["docs_globs"],
        "session_providers": document["session_providers"],
        "artefact_count": len(artefacts),
        "tracked_artefact_count": (
            sum(1 for item in artefacts if is_tracked(project_root, item))
            if repository
            else None
        ),
    }


def main(argv: list[str]) -> int:
    if not argv or argv[0] in {"-h", "--help"}:
        print(__doc__)
        return 0
    wiki_root = Path(argv[0])
    as_json = "--json" in argv[1:]
    try:
        report = describe(wiki_root)
    except BindingError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    if as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    print(f"wiki        {report['wiki_root']}")
    print(f"project     {report['project_root']}")
    print(f"git repo    {report['is_git_repository']}")
    print(f"git mode    {report['git_mode']} (enabled: {report['git_enabled']})")
    print(f"artefacts   {report['artefact_count']}")
    tracked = report["tracked_artefact_count"]
    print(f"tracked     {'unknown - not a repository' if tracked is None else tracked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
