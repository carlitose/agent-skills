"""Deterministic source projection: literal text, structural navigation and v1 markers.

Identity and Ticket Envelope parsing remain with ingest_docs. This module has no
filesystem, provider, model or clock dependency.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import html
import json
from pathlib import PurePosixPath
import re

TOPICS = {
    'ticket': {
        'intent': ('What to Build', 'Build intent', 'Intent'),
        'acceptance': ('Acceptance Criteria', 'Acceptance'),
        'testing': ('Testing Plan', 'Testing', 'Tests'),
        'frontier': ('Frontier', 'Frontier / Blocking Edges'),
        'exclusions': ('Out of Scope', 'Exclusions', 'Non-goals'),
    },
    'spec': {
        'goals': ('Goals', 'Goal', 'Destination', 'Goals and non-goals'),
        'exclusions': ('Out of Scope', 'Exclusions', 'Non-goals', 'Goals and non-goals'),
        'decisions': ('Decisions', 'Decision', 'Decisions So Far', 'Decision and evidence'),
        'invariants': ('Invariants', 'Contracts', 'Semantic Invariants', 'Transitions and invariants'),
        'verification': ('Verification', 'Verification Strategy', 'Testing Plan', 'Implementation and verification'),
    },
    'research': {
        'question': ('Question', 'Research Question'),
        'method': ('Method', 'Methodology', 'Research Method'),
        'findings': ('Findings', 'Results'),
        'evidence': ('Evidence', 'Sources', 'Evidence and sources'),
        'limitations': ('Limitations', 'Limits', 'Out of Scope'),
    },
    'prototype': {
        'question': ('Question', 'Prototype frame'),
        'assumptions': ('Assumptions', 'Prototype frame'),
        'results': ('Results', 'Observed Results', 'Observations'),
        'limitations': ('Limitations', 'Limits', 'Out of Scope'),
        'decision': ('Decision', 'Next Step', 'Next Steps', 'Keep, discard, decide'),
    },
    'guide': {
        'purpose': ('Purpose', 'Goal', 'Overview'),
        'prerequisites': ('Prerequisites', 'Requirements', 'Before you begin'),
        'procedure': ('Procedure', 'Steps', 'Usage', 'Step-by-Step Implementation Plan'),
        'limitations': ('Limitations', 'Limits', 'Out of Scope'),
    },
}
MISSING_SECTION = 'no matching section identified in the source; complete source retained'
FENCE = re.compile(r' {0,3}(`{3,}|~{3,})(.*)$')
ATX = re.compile(r' {0,3}(#{1,6})(?:[ \t]+(.*?)|[ \t]*)$')
SETEXT = re.compile(r' {0,3}(=+|-+)[ \t]*$')


class ProjectionError(ValueError):
    """A source cannot be represented under the confirmed projection contract."""


@dataclass(frozen=True)
class Heading:
    title: str
    level: int
    start: int


def visible_lines(text: str):
    """Yield offsets and visible lines; fenced examples are opaque, not headings/links."""
    fence = None
    offset = 0
    for raw in text.splitlines(keepends=True):
        line = raw.rstrip('\r\n')
        visible = line
        if fence is not None:
            if re.fullmatch(r' {0,3}' + re.escape(fence[0]) + '{' + str(len(fence)) + r',}[ \t]*', line):
                fence = None
            visible = ''
        else:
            opening = FENCE.fullmatch(line)
            if opening and not (opening[1][0] == '`' and '`' in opening[2]):
                fence = opening[1]
                visible = ''
        yield offset, visible
        offset += len(raw)


def source_headings(text: str) -> list[Heading]:
    result = []
    previous = None
    envelope = text.startswith('---\n')
    for offset, line in visible_lines(text):
        if envelope:
            if offset and line == '---':
                envelope = False
            continue
        match = ATX.fullmatch(line)
        if match:
            title = re.sub(r'[ \t]+#+[ \t]*$', '', match[2] or '').strip()
            result.append(Heading(title, len(match[1]), offset))
            previous = None
            continue
        underline = SETEXT.fullmatch(line)
        if underline and previous is not None:
            start, title = previous
            result.append(Heading(title.strip(), 1 if underline[1][0] == '=' else 2, start))
            previous = None
        else:
            previous = (offset, line) if line.strip() and not line.startswith(('    ', '\t', '- ', '* ', '> ')) else None
    return result


def source_kind(relative_path: str, text: str, *, is_ticket: bool) -> str:
    if is_ticket:
        return 'ticket'
    # Read only the graph's role; never interpret an envelope or a fenced example.
    graph = False
    for _offset, line in visible_lines(text):
        if line == '## Artifact Graph':
            graph = True
        elif re.match(r'#{1,2} ', line):
            graph = False
        elif graph:
            role = re.fullmatch(r'- Role:\s*`?([a-z-]+)`?\s*', line)
            if role:
                kind = {'wayfinder': 'spec'}.get(role[1], role[1])
                if kind in TOPICS and kind != 'ticket':
                    return kind
    categories = {'specs': 'spec', 'research': 'research', 'prototypes': 'prototype', 'guides': 'guide'}
    parts = PurePosixPath(relative_path).parts
    if len(parts) > 2 and parts[0] == 'docs' and parts[1] in categories:
        return categories[parts[1]]
    raise ProjectionError(f'unresolved source kind for {relative_path}; declare a supported Artifact Graph role or configure a recognized document category')


def _heading_key(value: str) -> str:
    value = re.sub(r'^\d+[.)]\s*', '', value.casefold())
    return ' '.join(re.sub(r'[^\w]+', ' ', value).split())


def coverage_for(kind: str, headings: list[Heading]) -> dict:
    coverage = {}
    for topic, aliases in TOPICS[kind].items():
        indexes = [
            i for i, heading in enumerate(headings)
            if _heading_key(heading.title) in {_heading_key(alias) for alias in aliases}
        ]
        coverage[topic] = {
            'status': 'present' if indexes else 'not-identified',
            'headings': indexes,
        }
    return coverage


def marker(name: str, value: dict) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    encoded = encoded.replace('<', r'\u003c').replace('>', r'\u003e')
    return f'<!-- {name}: {encoded} -->\n'


def literal_source(text: str) -> str:
    """Framing adds a newline outside the declared source byte count."""
    fence = '`' * (max([2, *(len(run) for run in re.findall(r'`+', text))]) + 1)
    return f'{fence}markdown\n{text}\n{fence}\n'


PAGE_BYTES = 32768


def _content(text: str) -> dict:
    raw = text.encode('utf-8')
    return dict(payload_sha256=hashlib.sha256(raw).hexdigest(), payload_bytes=len(raw))


def _payload(text: str, identity: str, digest: str, index: int) -> str:
    record = dict(schema=1, source_identity=identity, source_digest=digest, part_index=index, **_content(text))
    return marker('semantic-payload-v1', record) + literal_source(text)


def _entry(header: str, manifest: dict, headings: list[Heading], payload: str = '') -> str:
    lines = [header, '## Semantic coverage', '', marker('semantic-projection-v1', manifest).rstrip(), '', '| Topic | Source sections |', '|---|---|']
    for topic, item in manifest['coverage'].items():
        names = '; '.join(f'{i}: {html.escape(headings[i].title).replace("|", "&#124;").replace("[", "&#91;").replace("]", "&#93;")}' for i in item['headings'])
        lines.append(f'| {topic} | {names or MISSING_SECTION} |')
    lines += ['', '## Preserved source', '', 'Literal source text; not an agent-authored summary.', '']
    if payload:
        lines.append(payload)
    else:
        lines += [f'- Part {part["index"] + 1}: [[{part["path"][5:-3]}]]' for part in manifest['parts']]
        lines.append('')
    return '\n'.join(lines)


def _part_header(identity: str, digest: str, entry_path: str, index: int) -> str:
    return (f'---\ntype: source-part\nsource_identity: {identity}\nsource_digest: {digest}\n'
            f'source_entry: {entry_path}\n---\n\n# Preserved source — Part {index + 1}\n\n'
            f'Entry and provenance: [[{entry_path[5:-3]}]]\n\n')


def render_projection(header: str, *, text: str, kind: str, identity: str, digest: str, entry_path: str) -> dict[str, str]:
    """Return every bounded page, or fail before callers publish any of them.

    A small source is inline. A large source has a stable manifest entry and only
    external parts; splitting never consumes or trims a source character.
    """
    if not text.strip():
        raise ProjectionError(f'{entry_path}: empty source has no semantic payload')
    headings = source_headings(text)
    manifest = dict(schema=1, source_identity=identity, source_digest=digest, source_kind=kind,
                    coverage=coverage_for(kind, headings), parts=[], **_content(text))
    manifest['parts'] = [dict(index=0, path=entry_path, **_content(text))]
    inline = _entry(header, manifest, headings, _payload(text, identity, digest, 0))
    if len(inline.encode('utf-8')) <= PAGE_BYTES:
        return {entry_path: inline}

    pages = {}
    manifest['parts'] = []
    start = 0
    while start < len(text):
        index = len(manifest['parts'])
        path = f'{entry_path[:-3]}.part-{index:06d}.md'
        prefix = _part_header(identity, digest, entry_path, index)

        def render_to(end):
            return prefix + _payload(text[start:end], identity, digest, index)

        low, high = start, len(text)
        while low < high:
            middle = (low + high + 1) // 2
            if len(render_to(middle).encode('utf-8')) <= PAGE_BYTES:
                low = middle
            else:
                high = middle - 1
        end = low
        if end < len(text):
            end = max((h.start for h in headings if start < h.start <= end), default=end)
        if end <= start:
            raise ProjectionError(f'{entry_path}: source part metadata/framing exceeds {PAGE_BYTES} bytes')
        fragment = text[start:end]
        pages[path] = render_to(end)
        manifest['parts'].append(dict(index=index, path=path, **_content(fragment)))
        start = end
    entry = _entry(header, manifest, headings)
    if len(entry.encode('utf-8')) > PAGE_BYTES:
        raise ProjectionError(f'{entry_path}: required metadata/navigation exceeds {PAGE_BYTES} bytes')
    pages[entry_path] = entry
    return pages


@dataclass(frozen=True)
class Payload:
    record: dict
    text: str


@dataclass(frozen=True)
class ParsedPage:
    manifest: dict | None
    payloads: tuple[Payload, ...]


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ProjectionError(f'duplicate JSON key: {key}')
        result[key] = value
    return result


def _read_marker(line: str, name: str) -> dict:
    prefix = f'<!-- {name}: '
    if not line.startswith(prefix) or not line.endswith(' -->'):
        raise ProjectionError(f'malformed {name} marker')
    try:
        record = json.loads(line[len(prefix):-4], object_pairs_hook=_unique_object)
    except ValueError as error:
        raise ProjectionError(f'malformed {name} JSON: {error}') from error
    if not isinstance(record, dict) or type(record.get('schema')) is not int or record['schema'] != 1:
        raise ProjectionError(f'unsupported {name} schema')
    if marker(name, record).rstrip('\n') != line:
        raise ProjectionError(f'noncanonical {name} JSON')
    return record


def parse_page(text: str) -> ParsedPage:
    """Decode wire framing, not source correctness (owned by semantic-coverage lint).

    Markers inside literal fences are data. A payload's byte count excludes the
    framing newline even when the source has no final newline. Neither whitespace
    nor nested Markdown is stripped from the decoded source.
    """
    manifest = None
    payloads = []
    raw = text.encode('utf-8')
    for offset, line in visible_lines(text):
        if line.startswith('<!-- semantic-projection'):
            if manifest is not None:
                raise ProjectionError('duplicate semantic projection marker')
            manifest = _read_marker(line, 'semantic-projection-v1')
        elif line.startswith('<!-- semantic-payload'):
            record = _read_marker(line, 'semantic-payload-v1')
            count = record.get('payload_bytes')
            if type(count) is not int or count < 0:
                raise ProjectionError('payload_bytes must be a nonnegative integer')
            opening_start = text.find('\n', offset) + 1
            opening_end = text.find('\n', opening_start)
            opening = re.fullmatch(r'(`{3,})markdown', text[opening_start:opening_end])
            if not opening_start or opening_end < 0 or opening is None:
                raise ProjectionError('payload marker must immediately precede a literal source fence')
            start = len(text[:opening_end + 1].encode('utf-8'))
            end = start + count
            closing = b'\n' + opening[1].encode() + b'\n'
            if raw[end:end + len(closing)] != closing:
                raise ProjectionError('payload byte count or closing fence does not match')
            try:
                payload_text = raw[start:end].decode('utf-8', errors='strict')
            except UnicodeError as error:
                raise ProjectionError('payload splits an invalid UTF-8 boundary') from error
            payloads.append(Payload(record, payload_text))
    return ParsedPage(manifest, tuple(payloads))
