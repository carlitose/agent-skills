"""Keep generated session digest pages in the wiki's shared catalog."""

from __future__ import annotations

from pathlib import Path


INDEX_PATH = ("wiki", "index.md")
SESSION_DIRECTORY = ("wiki", "sources")
SESSION_HEADING = "## Session sources"
TIMELINE_HEADING = "## Timeline"
SESSION_LINK_PREFIX = "- [[sources/session-"


class SessionCatalogError(RuntimeError):
    """The shared wiki index cannot be read or safely rewritten."""


def _title(path: Path) -> str:
    """Return the page H1, falling back to its stable filename."""

    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem


def require_session_catalog(wiki_root: Path) -> Path:
    """Return the regular shared index or fail before an ingest can mutate."""

    index = wiki_root.joinpath(*INDEX_PATH)
    if not index.is_file() or index.is_symlink():
        raise SessionCatalogError(f"shared wiki index is unavailable: {index}")
    return index


def session_entries(wiki_root: Path) -> list[str]:
    """Render one deterministic catalog entry per regular session digest."""

    sources = wiki_root.joinpath(*SESSION_DIRECTORY)
    if sources.is_symlink():
        raise SessionCatalogError(f"session source directory is a symlink: {sources}")
    if not sources.is_dir():
        return []
    pages = [
        path
        for path in sorted(sources.glob("session-*.md"), key=lambda item: item.name)
        if path.is_file() and not path.is_symlink()
    ]
    return [f"- [[sources/{path.stem}]] — {_title(path)}" for path in pages]


def render_session_catalog(index_text: str, entries: list[str]) -> str:
    """Replace the generated session section without disturbing other owners."""

    lines = index_text.splitlines()
    retained: list[str] = []
    skipping = False
    for line in lines:
        if line == SESSION_HEADING:
            skipping = True
            continue
        if skipping and line.startswith("## "):
            skipping = False
        if skipping:
            continue
        if line.startswith(SESSION_LINK_PREFIX):
            continue
        retained.append(line)

    while retained and not retained[-1].strip():
        retained.pop()
    if entries:
        section = [SESSION_HEADING, "", *entries, ""]
        try:
            insertion = retained.index(TIMELINE_HEADING)
        except ValueError:
            retained.extend(["", *section])
        else:
            retained[insertion:insertion] = section
    return "\n".join(retained).rstrip() + "\n"


def refresh_session_catalog(wiki_root: Path) -> bool:
    """Refresh the session section and report whether the index changed."""

    index = require_session_catalog(wiki_root)
    before = index.read_text(encoding="utf-8")
    after = render_session_catalog(before, session_entries(wiki_root))
    if after == before:
        return False
    index.write_text(after, encoding="utf-8")
    return True
