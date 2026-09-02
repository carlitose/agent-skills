"""Bounded ownership for compiler-generated sections in ``wiki/index.md``.

The root catalog has mixed ownership. Human-authored navigation and open work are opaque
bytes; the compiler may replace only the three blocks delimited by exact line-oriented
markers. A catalog with missing, duplicate, malformed, nested, or conflicting markers is
rejected rather than inferred from headings.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping

PROJECT_SOURCES = "project-sources"
SESSION_SOURCES = "session-sources"
TIMELINE = "timeline"
OWNERS = (PROJECT_SOURCES, SESSION_SOURCES, TIMELINE)
_MARKER_PREFIX = "<!-- llm-wiki:catalog"
_MARKER = re.compile(
    r"<!-- llm-wiki:catalog:(start|end):([a-z][a-z0-9-]*) -->"
)


class CatalogOwnershipError(ValueError):
    """The root catalog's generated ownership boundaries are not trustworthy."""


@dataclass(frozen=True)
class OwnedSpan:
    """One complete generated block, including both boundary lines."""

    owner: str
    start: int
    end: int


def _line_body(line: str) -> str:
    return line.rstrip("\r\n")


def parse_catalog(text: str) -> dict[str, OwnedSpan]:
    """Return all exact generated spans or reject the complete catalog.

    Offsets are over the original decoded string. Newline spelling therefore remains part
    of every non-owned span and survives replacement byte-for-byte after UTF-8 encoding.
    """

    spans: dict[str, OwnedSpan] = {}
    opened: tuple[str, int] | None = None
    offset = 0
    for line in text.splitlines(keepends=True):
        body = _line_body(line)
        if _MARKER_PREFIX not in body:
            offset += len(line)
            continue
        match = _MARKER.fullmatch(body)
        if match is None:
            raise CatalogOwnershipError(
                f"root catalog contains a malformed ownership boundary at offset {offset}"
            )
        kind, owner = match.groups()
        if owner not in OWNERS:
            raise CatalogOwnershipError(
                f"root catalog contains an unknown generated owner: {owner}"
            )
        if kind == "start":
            if opened is not None:
                raise CatalogOwnershipError(
                    f"root catalog contains nested generated boundaries: "
                    f"{opened[0]} then {owner}"
                )
            if owner in spans:
                raise CatalogOwnershipError(
                    f"root catalog duplicates generated owner: {owner}"
                )
            opened = (owner, offset)
        else:
            if opened is None:
                raise CatalogOwnershipError(
                    f"root catalog closes generated owner without a start: {owner}"
                )
            if opened[0] != owner:
                raise CatalogOwnershipError(
                    f"root catalog has conflicting generated boundaries: "
                    f"{opened[0]} closed by {owner}"
                )
            spans[owner] = OwnedSpan(owner, opened[1], offset + len(line))
            opened = None
        offset += len(line)
    if opened is not None:
        raise CatalogOwnershipError(
            f"root catalog is missing the end boundary for generated owner: {opened[0]}"
        )
    missing = [owner for owner in OWNERS if owner not in spans]
    if missing:
        raise CatalogOwnershipError(
            "root catalog is missing generated ownership boundaries: " + ", ".join(missing)
        )
    return spans


def _canonical_content(content: str) -> str:
    if not isinstance(content, str):
        raise CatalogOwnershipError("generated catalog content must be text")
    if _MARKER_PREFIX in content:
        raise CatalogOwnershipError("generated catalog content contains an ownership marker")
    normalized = content.replace("\r\n", "\n").replace("\r", "\n")
    if normalized and not normalized.endswith("\n"):
        normalized += "\n"
    return normalized


def catalog_block(owner: str, content: str) -> str:
    """Render one canonical generated block."""

    if owner not in OWNERS:
        raise CatalogOwnershipError(f"unknown generated catalog owner: {owner}")
    return (
        f"<!-- llm-wiki:catalog:start:{owner} -->\n"
        f"{_canonical_content(content)}"
        f"<!-- llm-wiki:catalog:end:{owner} -->\n"
    )


def update_catalog(text: str, replacements: Mapping[str, str]) -> str:
    """Replace selected owned blocks while preserving every other character exactly."""

    unknown = sorted(set(replacements) - set(OWNERS))
    if unknown:
        raise CatalogOwnershipError(
            "replacement names unknown generated owners: " + ", ".join(unknown)
        )
    spans = parse_catalog(text)
    updated = text
    for owner in sorted(replacements, key=lambda item: spans[item].start, reverse=True):
        span = spans[owner]
        updated = (
            updated[: span.start]
            + catalog_block(owner, replacements[owner])
            + updated[span.end :]
        )
    return updated


def render_timeline_section(*, present: bool) -> str:
    """Render the generated timeline navigation, including its stable anchor."""

    lines = ["## Timeline", ""]
    if present:
        lines.extend(
            [
                "- [[timeline/index]] — when each artefact happened, and how each date is known",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def initialize_catalog(prefix: str = "# Index\n\n") -> str:
    """Create a minimal mixed-ownership catalog when no index exists yet."""

    if _MARKER_PREFIX in prefix:
        raise CatalogOwnershipError("catalog prefix must not contain ownership markers")
    if prefix and not prefix.endswith(("\n", "\r")):
        prefix += "\n"
    text = prefix + "".join(catalog_block(owner, "") for owner in OWNERS)
    parse_catalog(text)
    return text
