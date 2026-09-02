"""Keep generated session digest pages in the wiki's shared catalog."""

from __future__ import annotations

from pathlib import Path

from root_catalog import (
    SESSION_SOURCES,
    CatalogOwnershipError,
    parse_catalog,
    update_catalog,
)


INDEX_PATH = ("wiki", "index.md")
SESSION_DIRECTORY = ("wiki", "sources")
SESSION_HEADING = "## Session sources"


class SessionCatalogError(RuntimeError):
    """The shared wiki index cannot be read or safely rewritten."""


def _title(path: Path) -> str:
    """Return the page H1, falling back to its stable filename."""

    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem


def _catalog_text(index: Path) -> str:
    try:
        text = index.read_bytes().decode("utf-8", errors="strict")
        parse_catalog(text)
    except (OSError, UnicodeError, CatalogOwnershipError) as error:
        raise SessionCatalogError(
            f"shared wiki index ownership is invalid: {index}: {error}"
        ) from error
    return text


def require_session_catalog(wiki_root: Path) -> Path:
    """Return a regular, ownership-bounded index or fail before ingest mutation."""

    index = wiki_root.joinpath(*INDEX_PATH)
    if not index.is_file() or index.is_symlink():
        raise SessionCatalogError(f"shared wiki index is unavailable: {index}")
    _catalog_text(index)
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


def render_session_section(entries: list[str]) -> str:
    """Render only the compiler-owned session block content."""

    lines = [SESSION_HEADING, ""]
    if entries:
        lines.extend(entries)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_session_catalog(index_text: str, entries: list[str]) -> str:
    """Replace only the bounded session block, never heading-shaped manual content."""

    try:
        return update_catalog(
            index_text, {SESSION_SOURCES: render_session_section(entries)}
        )
    except CatalogOwnershipError as error:
        raise SessionCatalogError(str(error)) from error


def refresh_session_catalog(wiki_root: Path) -> bool:
    """Refresh the session section and report whether the index changed."""

    index = require_session_catalog(wiki_root)
    before = _catalog_text(index)
    after = render_session_catalog(before, session_entries(wiki_root))
    if after == before:
        return False
    index.write_bytes(after.encode("utf-8"))
    return True
