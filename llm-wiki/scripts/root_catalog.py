"""Bounded ownership for compiler-generated sections in ``wiki/index.md``.

The root catalog has mixed ownership. Human-authored navigation and open work are opaque
bytes; the compiler may replace only the three blocks delimited by exact line-oriented
markers. A catalog with missing, duplicate, malformed, nested, or conflicting markers is
rejected rather than inferred from headings.
"""

from __future__ import annotations

import hashlib
import os
import re
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

PROJECT_SOURCES = "project-sources"
SESSION_SOURCES = "session-sources"
TIMELINE = "timeline"
OWNERS = (PROJECT_SOURCES, SESSION_SOURCES, TIMELINE)
_MARKER_PREFIX = "<!-- llm-wiki:catalog"
_MARKER = re.compile(
    r"<!-- llm-wiki:catalog:(start|end):([a-z][a-z0-9-]*) -->"
)
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class CatalogOwnershipError(ValueError):
    """The root catalog's generated ownership boundaries are not trustworthy."""


@dataclass(frozen=True)
class OwnedSpan:
    """One complete generated block, including both boundary lines."""

    owner: str
    start: int
    end: int


@dataclass(frozen=True)
class CatalogAdoptionSpan:
    """One caller-declared generated region in the unmarked legacy bytes."""

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


def _marker_line(kind: str, owner: str) -> bytes:
    return f"<!-- llm-wiki:catalog:{kind}:{owner} -->\n".encode("ascii")


def _legacy_digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _validate_adoption_spans(
    data: bytes, spans: Sequence[CatalogAdoptionSpan]
) -> tuple[CatalogAdoptionSpan, ...]:
    try:
        normalized = tuple(spans)
    except TypeError as error:
        raise CatalogOwnershipError("catalog adoption spans must be a sequence") from error
    if len(normalized) != len(OWNERS):
        raise CatalogOwnershipError(
            "catalog adoption requires exactly one span for every generated owner"
        )

    previous_end = 0
    for index, (span, expected_owner) in enumerate(zip(normalized, OWNERS)):
        if not isinstance(span, CatalogAdoptionSpan):
            raise CatalogOwnershipError("catalog adoption spans have an invalid shape")
        if span.owner != expected_owner:
            raise CatalogOwnershipError(
                "catalog adoption owners must be complete and ordered: "
                + ", ".join(OWNERS)
            )
        if type(span.start) is not int or type(span.end) is not int:
            raise CatalogOwnershipError("catalog adoption offsets must be integers")
        if span.start < 0 or span.start >= span.end or span.end > len(data):
            raise CatalogOwnershipError(
                f"catalog adoption span is outside the legacy bytes: {span.owner}"
            )
        if index and span.start < previous_end:
            raise CatalogOwnershipError(
                f"catalog adoption spans overlap or are out of order: {span.owner}"
            )
        if span.start and data[span.start - 1 : span.start] not in {b"\n", b"\r"}:
            raise CatalogOwnershipError(
                f"catalog adoption span does not start on a line boundary: {span.owner}"
            )
        if (
            span.start
            and span.start < len(data)
            and data[span.start - 1 : span.start + 1] == b"\r\n"
        ):
            raise CatalogOwnershipError(
                f"catalog adoption span splits a CRLF boundary: {span.owner}"
            )
        if data[span.end - 1 : span.end] not in {b"\n", b"\r"}:
            raise CatalogOwnershipError(
                f"catalog adoption span does not end on a line boundary: {span.owner}"
            )
        if span.end < len(data) and data[span.end - 1 : span.end + 1] == b"\r\n":
            raise CatalogOwnershipError(
                f"catalog adoption span splits a CRLF boundary: {span.owner}"
            )
        try:
            data[span.start : span.end].decode("utf-8", errors="strict")
        except UnicodeError as error:
            raise CatalogOwnershipError(
                f"catalog adoption offset splits UTF-8 text: {span.owner}"
            ) from error
        previous_end = span.end
    return normalized


def _insert_catalog_markers(
    legacy: bytes, spans: Sequence[CatalogAdoptionSpan]
) -> bytes:
    adopted = legacy
    for span in reversed(tuple(spans)):
        adopted = (
            adopted[: span.start]
            + _marker_line("start", span.owner)
            + adopted[span.start : span.end]
            + _marker_line("end", span.owner)
            + adopted[span.end :]
        )
    return adopted


def remove_catalog_markers(adopted: bytes) -> bytes:
    """Remove only the six exact ownership marker lines from a valid catalog."""

    if not isinstance(adopted, bytes):
        raise CatalogOwnershipError("catalog adoption input must be bytes")
    try:
        text = adopted.decode("utf-8", errors="strict")
    except UnicodeError as error:
        raise CatalogOwnershipError("root catalog is not valid UTF-8") from error
    parse_catalog(text)
    kept: list[bytes] = []
    removed = 0
    for line in adopted.splitlines(keepends=True):
        try:
            body = line.rstrip(b"\r\n").decode("ascii")
        except UnicodeError:
            body = ""
        if _MARKER.fullmatch(body):
            removed += 1
        else:
            kept.append(line)
    if removed != len(OWNERS) * 2:
        raise CatalogOwnershipError("root catalog does not contain exactly six marker lines")
    return b"".join(kept)


def adopt_catalog_bytes(
    source: bytes,
    expected_sha256: str,
    spans: Sequence[CatalogAdoptionSpan],
) -> bytes:
    """Adopt one exact legacy catalog without inferring ownership from its content."""

    if not isinstance(source, bytes):
        raise CatalogOwnershipError("catalog adoption input must be bytes")
    if not isinstance(expected_sha256, str) or not _SHA256.fullmatch(expected_sha256):
        raise CatalogOwnershipError(
            "catalog adoption expected SHA-256 must be 64 lowercase hexadecimal characters"
        )
    try:
        text = source.decode("utf-8", errors="strict")
    except UnicodeError as error:
        raise CatalogOwnershipError("root catalog is not valid UTF-8") from error

    already_adopted = _MARKER_PREFIX in text
    legacy = remove_catalog_markers(source) if already_adopted else source
    if _legacy_digest(legacy) != expected_sha256:
        raise CatalogOwnershipError("legacy root catalog SHA-256 differs from expected bytes")
    normalized = _validate_adoption_spans(legacy, spans)
    candidate = _insert_catalog_markers(legacy, normalized)
    try:
        parsed = candidate.decode("utf-8", errors="strict")
    except UnicodeError as error:  # pragma: no cover - spans already prove this invariant
        raise CatalogOwnershipError("adopted root catalog is not valid UTF-8") from error
    parse_catalog(parsed)
    if remove_catalog_markers(candidate) != legacy:
        raise CatalogOwnershipError("catalog adoption marker removal changed legacy bytes")
    if already_adopted and candidate != source:
        raise CatalogOwnershipError("adopted root catalog contradicts the supplied ownership map")
    return candidate


def _read_regular_file(path: Path) -> tuple[bytes, os.stat_result]:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NONBLOCK", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        raise CatalogOwnershipError(f"root catalog is not a regular file: {path}") from error
    try:
        details = os.fstat(descriptor)
        if not stat.S_ISREG(details.st_mode):
            raise CatalogOwnershipError(f"root catalog is not a regular file: {path}")
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            data = handle.read()
        after = os.fstat(descriptor)
        if (details.st_dev, details.st_ino, details.st_size) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
        ):
            raise CatalogOwnershipError("root catalog changed while it was being read")
        return data, details
    finally:
        os.close(descriptor)


def adopt_catalog_file(
    path: Path,
    expected_sha256: str,
    spans: Sequence[CatalogAdoptionSpan],
) -> dict[str, object]:
    """Atomically adopt one regular file after complete in-memory validation."""

    path = Path(path)
    if path.is_symlink():
        raise CatalogOwnershipError(f"root catalog is not a regular file: {path}")
    if path.parent.is_symlink() or not path.parent.is_dir():
        raise CatalogOwnershipError(f"root catalog parent is not a safe directory: {path.parent}")
    normalized = tuple(spans)
    before, details = _read_regular_file(path)
    after = adopt_catalog_bytes(before, expected_sha256, normalized)
    report: dict[str, object] = {
        "schema": 1,
        "status": "unchanged" if after == before else "adopted",
        "path": str(path),
        "legacy_sha256": expected_sha256,
        "adopted_sha256": _legacy_digest(after),
        "spans": [
            {"owner": span.owner, "start": span.start, "end": span.end}
            for span in normalized
        ],
    }
    if after == before:
        return report

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(after)
            handle.flush()
            os.fsync(handle.fileno())
            os.fchmod(handle.fileno(), stat.S_IMODE(details.st_mode))
            os.fsync(handle.fileno())
        current, current_details = _read_regular_file(path)
        if current != before or (
            current_details.st_dev,
            current_details.st_ino,
            stat.S_IMODE(current_details.st_mode),
        ) != (details.st_dev, details.st_ino, stat.S_IMODE(details.st_mode)):
            raise CatalogOwnershipError("root catalog changed before adoption could commit")
        os.replace(temporary, path)
        if os.name != "nt":
            directory = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        observed, observed_details = _read_regular_file(path)
        if observed != after or stat.S_IMODE(observed_details.st_mode) != stat.S_IMODE(
            details.st_mode
        ):
            raise CatalogOwnershipError("adopted root catalog readback differs from intent")
        return report
    finally:
        temporary.unlink(missing_ok=True)


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
