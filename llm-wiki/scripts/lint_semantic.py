"""Read-only semantic-coverage lint for the project-source projection contract."""
from __future__ import annotations

import hashlib
import html
from pathlib import Path, PurePosixPath
import re

from ingest_docs import Artefact, TicketParserError, classify, default_autopilot_root, page_name
from lint_wiki import ERROR, INFO, PassResult, parse_frontmatter
from project_binding import BindingError, config_path, discover_artefacts, resolve_project_root
from semantic_projection import (
    MISSING_SECTION, PAGE_BYTES, ProjectionError, coverage_for, parse_page,
    source_headings, source_kind, visible_lines,
)


def _fields(record, expected: set[str], name: str) -> None:
    if not isinstance(record, dict) or set(record) != expected:
        raise ProjectionError(f'{name} fields do not match projection v1')


def _positive_count(record, field: str) -> None:
    if type(record.get(field)) is not int or record[field] <= 0:
        raise ProjectionError(f'{field} must be a positive integer')


def _check_source_manifest(manifest: dict, source) -> None:
    _fields(manifest, {'schema', 'source_identity', 'source_digest', 'source_kind', 'payload_sha256', 'payload_bytes', 'coverage', 'parts'}, 'manifest')
    _positive_count(manifest, 'payload_bytes')
    coverage = manifest['coverage']
    if not isinstance(coverage, dict):
        raise ProjectionError('coverage must be a topic mapping')
    for item in coverage.values():
        _fields(item, {'status', 'headings'}, 'coverage topic')
        if not isinstance(item['headings'], list) or any(type(i) is not int or i < 0 for i in item['headings']):
            raise ProjectionError('coverage headings must be ordered integer indexes')
    kind = source_kind(source.relative_path, source.source_text, is_ticket=source.kind == 'ticket')
    expected = dict(source_identity=source.identity_key, source_digest=source.digest, source_kind=kind,
                    coverage=coverage_for(kind, source_headings(source.source_text)))
    for field, value in expected.items():
        if manifest.get(field) != value:
            raise ProjectionError(f'{field} does not match the configured source')


def _read_generated(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise ProjectionError(f'generated path is missing or not a regular file: {path.name}')
    raw = path.read_bytes()
    if len(raw) > PAGE_BYTES:
        raise ProjectionError(f'{path.name}: page exceeds {PAGE_BYTES} UTF-8 bytes')
    return raw.decode('utf-8')


def _check_payloads(wiki_root: Path, entry: Path, parsed, source) -> set[str]:
    expected = source.source_text.encode('utf-8')
    if not source.source_text.strip():
        raise ProjectionError('empty source has no semantic payload')
    manifest = parsed.manifest
    if (manifest.get('payload_sha256') != hashlib.sha256(expected).hexdigest()
            or manifest.get('payload_bytes') != len(expected)):
        raise ProjectionError('manifest payload hash/byte count does not match the source')
    parts = manifest.get('parts')
    if not isinstance(parts, list) or not parts:
        raise ProjectionError('missing payload inventory')
    recovered = bytearray()
    declared = set()
    entry_relative = entry.relative_to(wiki_root).as_posix()
    if parsed.payloads and (len(parts) != 1 or not isinstance(parts[0], dict) or parts[0].get('path') != entry_relative):
        raise ProjectionError('undeclared payload on the entry page')
    for index, part in enumerate(parts):
        _fields(part, {'index', 'path', 'payload_sha256', 'payload_bytes'}, 'payload inventory item')
        _positive_count(part, 'payload_bytes')
        expected_path = entry_relative if len(parts) == 1 and part.get('path') == entry_relative else f'{entry_relative[:-3]}.part-{index:06d}.md'
        if part.get('path') != expected_path or type(part.get('index')) is not int or part['index'] != index:
            raise ProjectionError('payload part path/order differs from its identity-based inventory')
        path = wiki_root / expected_path
        if path.is_symlink() or not path.is_file():
            raise ProjectionError(f'payload part is missing or not a regular file: {expected_path}')
        declared.add(expected_path)
        if path == entry:
            page = parsed
        else:
            text = _read_generated(path)
            page = parse_page(text)
            if page.manifest is not None:
                raise ProjectionError(f'part must not contain a manifest: {expected_path}')
            matter = parse_frontmatter(text) or {}
            expected_matter = dict(type='source-part', source_identity=source.identity_key,
                                   source_digest=source.digest, source_entry=entry_relative)
            if 'identity_key' in matter or any(matter.get(key) != value for key, value in expected_matter.items()):
                raise ProjectionError(f'part metadata does not bind its entry/source: {expected_path}')
        if len(page.payloads) != 1:
            raise ProjectionError(f'missing or duplicate payload: {expected_path}')
        payload = page.payloads[0]
        raw = payload.text.encode('utf-8')
        record = payload.record
        _fields(record, {'schema', 'source_identity', 'source_digest', 'part_index', 'payload_sha256', 'payload_bytes'}, 'payload marker')
        if type(record['part_index']) is not int:
            raise ProjectionError('payload part_index must be an integer')
        facts = dict(source_identity=source.identity_key, source_digest=source.digest,
                     part_index=index, payload_sha256=hashlib.sha256(raw).hexdigest(), payload_bytes=len(raw))
        if not raw or any(record.get(key) != value for key, value in facts.items()):
            raise ProjectionError(f'payload fields/hash/bytes mismatch: {expected_path}')
        if part.get('payload_sha256') != facts['payload_sha256'] or part.get('payload_bytes') != len(raw):
            raise ProjectionError(f'payload inventory hash/bytes mismatch: {expected_path}')
        recovered.extend(raw)
    if recovered != expected:
        raise ProjectionError('complete payload reconstruction differs from the configured source')
    extras = {p.relative_to(wiki_root).as_posix() for p in entry.parent.glob(entry.stem + '.part-*.md')} - declared
    if extras:
        raise ProjectionError('undeclared payload part(s): ' + ', '.join(sorted(extras)))
    return declared


def _check_navigation(text: str, manifest: dict, source: Artefact, entry_relative: str) -> None:
    lines = [line for _, line in visible_lines(text)]
    if lines.count('## Semantic coverage') != 1 or lines.count('## Preserved source') != 1:
        raise ProjectionError('missing/duplicate semantic navigation sections')
    start, end = lines.index('## Semantic coverage'), lines.index('## Preserved source')
    rows = []
    for line in lines[start + 1:end]:
        if line.startswith('|'):
            columns = line.split('|')
            if len(columns) != 4 or columns[0] or columns[-1]:
                raise ProjectionError('malformed coverage navigation row')
            rows.append(tuple(html.unescape(value.strip()) for value in columns[1:-1]))
    headings = source_headings(source.source_text)
    expected = {
        topic: '; '.join(f'{i}: {headings[i].title}' for i in item['headings']) or MISSING_SECTION
        for topic, item in manifest['coverage'].items()
    }
    if (rows[:2] != [('Topic', 'Source sections'), ('---', '---')]
            or len(rows) != len(expected) + 2 or dict(rows[2:]) != expected):
        raise ProjectionError('coverage navigation differs from the actual source sections')
    links = [match.groups() for line in lines[end + 1:]
             if (match := re.fullmatch(r'- Part (\d+): \[\[([^\]]+)\]\]', line))]
    expected_links = [(str(part['index'] + 1), part['path'][5:-3])
                      for part in manifest['parts'] if part['path'] != entry_relative]
    if links != expected_links:
        raise ProjectionError('part navigation is missing, duplicated or out of order')


def _source_path(project: Path, relative) -> Path:
    if (not isinstance(relative, str) or not relative or '\\' in relative or '\0' in relative
            or PurePosixPath(relative).is_absolute() or '..' in PurePosixPath(relative).parts
            or PurePosixPath(relative).as_posix() != relative):
        raise ProjectionError('source_path must be a canonical project-relative path')
    path = project / relative
    try:
        within_project = path.resolve().is_relative_to(project.resolve())
    except RuntimeError as error:
        raise ProjectionError(f'source_path cannot be resolved: {error}') from error
    if not within_project:
        raise ProjectionError('source_path resolves outside the configured project')
    return path


def _source_snapshot(project: Path, matched: set[str]):
    """Identify current entries independently of editable generated metadata.

    Failed un-ingested sources stay with the existing un-ingested pass. A page
    referring to a failed source receives that error, never a tombstone exemption.
    """
    by_path: dict[str, Artefact] = {}
    by_name: dict[str, list[Artefact]] = {}
    errors: dict[str, str] = {}
    for relative in sorted(matched):
        try:
            _source_path(project, relative)
            source = classify(project, relative, default_autopilot_root())
            by_path[relative] = source
            by_name.setdefault(page_name(source), []).append(source)
        except (OSError, UnicodeError, ProjectionError, TicketParserError) as error:
            errors[relative] = str(error)
    return by_path, by_name, errors


def _tombstone_parts(wiki_root: Path, entry: Path, matter: dict) -> set[str]:
    retained = set()
    for path in entry.parent.glob(entry.stem + '.part-*.md'):
        if path.is_symlink() or not path.is_file():
            raise ProjectionError(f'tombstone part is not a regular file: {path.name}')
        metadata = parse_frontmatter(path.read_text(encoding='utf-8')) or {}
        if (metadata.get('type') == 'source-part'
                and metadata.get('source_identity') == matter['identity_key']
                and metadata.get('source_entry') == entry.relative_to(wiki_root).as_posix()):
            retained.add(path.relative_to(wiki_root).as_posix())
    return retained


def check_semantic_coverage(wiki_root: Path) -> PassResult:
    result = PassResult(
        'semantic-coverage', severity=ERROR,
        clean_message='Present source pages carry semantic projection v1',
        fix='Correct source/binding/ownership errors first, then run `ingest_docs.py` to regenerate; lint never repairs content.',
    )
    if not config_path(wiki_root).exists() and not config_path(wiki_root).is_symlink():
        result.severity = INFO
        result.issues.append('   not applicable: no project binding')
        result.fix = 'Use `project_binding.py` to bind a project only when project-history compilation is intended.'
        return result
    try:
        project = resolve_project_root(wiki_root)
        matched = set(discover_artefacts(wiki_root))
    except (BindingError, OSError, ValueError, KeyError) as error:
        result.issues.append(f'   {config_path(wiki_root)} — invalid binding: {error}')
        result.fix = 'Correct the existing binding with `project_binding.py`, then rerun lint.'
        return result
    sources = wiki_root / 'wiki/sources'
    try:
        if not sources.resolve().is_relative_to(wiki_root.resolve()):
            raise ProjectionError('wiki/sources resolves outside the wiki root')
    except (OSError, ValueError, RuntimeError) as error:
        result.issues.append(f'   wiki/sources — {error}')
        return result
    by_path, by_name, source_errors = _source_snapshot(project, matched)
    declared = set()
    observed_parts = set()
    checked = tombstones = 0
    for path in sorted(sources.glob('*.md')):
        try:
            if path.is_symlink() or not path.is_file():
                raise ProjectionError('generated source path is not a regular file')
            text = path.read_bytes().decode('utf-8')
            matter = parse_frontmatter(text.replace('\r\n', '\n').replace('\r', '\n')) or {}
            known = by_name.get(path.name, [])
            if not known and (matter.get('type') == 'source-part' or matter.get('source_identity') or re.search(r'\.part-\d{6}$', path.stem)):
                observed_parts.add(path.relative_to(wiki_root).as_posix())
                continue
            if not (known or matter.get('identity_key') or matter.get('source_path')):
                continue
            if len(known) > 1:
                raise ProjectionError('entry name is shared by multiple configured sources')
            relative = matter.get('source_path')
            source_path = _source_path(project, relative)
            if relative in source_errors:
                raise ProjectionError(source_errors[relative])
            source = known[0] if known else by_path.get(relative)
            if source is None:
                if source_path.exists() and not source_path.is_file():
                    raise ProjectionError('source_path exists but is not a readable source file')
                if (matter.get('source_status') != 'missing' or matter.get('type') != 'source'
                        or not isinstance(matter.get('identity_key'), str) or not matter['identity_key']):
                    raise ProjectionError('unavailable source requires an explicit identity-bearing tombstone')
                if any(item.identity_key == matter['identity_key'] for item in by_path.values()):
                    raise ProjectionError('tombstone identity is still present in the configured sources')
                declared.update(_tombstone_parts(wiki_root, path, matter))
                tombstones += 1
                continue
            expected_matter = dict(type='source', identity_key=source.identity_key,
                                   source_path=source.relative_path, source_digest=source.digest,
                                   source_status='present')
            for field, value in expected_matter.items():
                if matter.get(field) != value:
                    raise ProjectionError(f'{field} does not match the present configured source')
            if path.name != page_name(source):
                raise ProjectionError('entry filename does not match the canonical source identity')
            text = _read_generated(path)
            parsed = parse_page(text)
            if parsed.manifest is None:
                raise ProjectionError('missing semantic manifest; legacy metadata or prose is not source coverage')
            _check_source_manifest(parsed.manifest, source)
            declared.update(_check_payloads(wiki_root, path, parsed, source))
            _check_navigation(text, parsed.manifest, source, path.relative_to(wiki_root).as_posix())
            checked += 1
        except (OSError, UnicodeError, ProjectionError, TicketParserError) as error:
            result.issues.append(f'   {path.relative_to(wiki_root).as_posix()} — {error}')
    for relative in sorted(observed_parts - declared):
        result.issues.append(f'   {relative} — undeclared/orphan semantic payload part')
    result.clean_message = (f'Checked {checked} present source page(s); {tombstones} unavailable-source tombstone(s) '
                            'retained without a semantic freshness/coverage claim')
    return result
