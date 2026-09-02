from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path


CANONICAL_BODY_ENCODING = "utf-8-lf-v1"


class PrBodyArtifactError(RuntimeError):
    """A PR-body artifact is not the exact canonical or proven legacy value."""


def canonical_markdown(content: str) -> tuple[str, bytes]:
    """Return the sole accepted PR-body representation: UTF-8 with LF endings."""

    canonical = content.replace("\r\n", "\n").replace("\r", "\n")
    try:
        encoded = canonical.encode("utf-8")
    except UnicodeEncodeError as error:
        raise PrBodyArtifactError("PR-body is not valid Unicode text") from error
    return canonical, encoded


def _digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def persist_pr_body(path: Path, content: bytes) -> None:
    """Persist exact bytes atomically without host newline translation."""

    content_sha256 = _digest(content)
    if path.exists():
        try:
            existing = path.read_bytes()
        except OSError as error:
            raise PrBodyArtifactError(f"PR-body artifact is unreadable: {error}") from error
        if existing != content:
            raise PrBodyArtifactError(
                "content-addressed PR-body artifact is contradictory"
            )
        if path.name != f"{content_sha256}.md":
            raise PrBodyArtifactError(
                "content-addressed PR-body path does not match its exact bytes"
            )
        return

    if path.name != f"{content_sha256}.md":
        raise PrBodyArtifactError(
            "content-addressed PR-body path does not match its exact bytes"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, raw_temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(raw_temporary)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        if os.name != "nt":
            directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
            directory = os.open(path.parent, directory_flags)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
    except OSError as error:
        raise PrBodyArtifactError(f"PR-body artifact cannot be persisted: {error}") from error
    finally:
        temporary.unlink(missing_ok=True)


def read_pr_body(
    path: Path,
    *,
    recorded_sha256: str,
    encoding: str | None,
) -> str:
    """Read canonical bytes or one exactly reversible legacy Windows expansion."""

    try:
        raw = path.read_bytes()
    except OSError as error:
        raise PrBodyArtifactError(f"PR-body artifact is unreadable: {error}") from error

    if encoding == CANONICAL_BODY_ENCODING:
        accepted = raw if _digest(raw) == recorded_sha256 else None
    elif encoding is None:
        accepted = None
        if _digest(raw) == recorded_sha256:
            accepted = raw
        elif b"\r\n" in raw:
            reconstructed = raw.replace(b"\r\n", b"\n")
            if _digest(reconstructed) == recorded_sha256:
                accepted = reconstructed
    else:
        raise PrBodyArtifactError("PR-body artifact encoding is unsupported")

    if accepted is None:
        raise PrBodyArtifactError("persisted PR-body hash is invalid")
    try:
        text = accepted.decode("utf-8")
    except UnicodeDecodeError as error:
        raise PrBodyArtifactError("persisted PR-body is not valid UTF-8") from error
    canonical, canonical_bytes = canonical_markdown(text)
    if encoding == CANONICAL_BODY_ENCODING:
        if canonical_bytes != accepted:
            raise PrBodyArtifactError("canonical PR-body artifact contains non-LF endings")
        return canonical
    if accepted == raw and canonical_bytes != accepted:
        raise PrBodyArtifactError(
            "legacy PR-body artifact has unproven non-canonical endings"
        )
    return canonical
