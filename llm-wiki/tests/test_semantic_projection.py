"""Source witnesses must survive the real public ingest path, not only metadata."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from test_ingest_docs import Fixture, TICKET


def manifest_from(text):
    prefix = '<!-- semantic-projection-v1: '
    return json.loads(next(line for line in text.splitlines() if line.startswith(prefix))[len(prefix):-4])


def reconstruct(wiki, manifest):
    """Consumer-side witness, independent of the production renderer/parser."""
    chunks = []
    for part in manifest['parts']:
        raw = (wiki / part['path']).read_bytes()
        prefix = b'<!-- semantic-payload-v1: '
        start = raw.index(prefix)
        marker_end = raw.index(b'\n', start)
        payload = json.loads(raw[start + len(prefix):marker_end - 4])
        fence_end = raw.index(b'\n', marker_end + 1)
        fragment = raw[fence_end + 1:fence_end + 1 + payload['payload_bytes']]
        assert hashlib.sha256(fragment).hexdigest() == part['payload_sha256']
        assert len(fragment) == part['payload_bytes']
        chunks.append(fragment)
    return b''.join(chunks)


class SemanticProjectionTests(unittest.TestCase):
    def test_complete_ticket_text_is_visible_without_opening_the_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            source = TICKET.format(body=(
                '## What to Build\nReject blank reasons before changing a ledger.\n\n'
                '## Acceptance Criteria\n- [ ] Record the literal cause.\n\n'
                '## Testing Plan\nProve the unchanged ledger on rejection.\n\n'
                '## Frontier\nWait for exact evidence, not a guessed cause.\n\n'
                '## Out of Scope\nDo not infer historical gate causes.\n'
            ))
            fixture.ticket.write_text(source, encoding='utf-8')
            fixture.run()
            page = fixture.wiki / 'wiki/sources/ticket-family-01.md'
            self.assertIn(source, page.read_text(encoding='utf-8'))

    def test_manifest_binds_research_kind_and_real_section_occurrences(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            source = ('# Evidence note\n\nQuestion\n========\nWhich value survives?\n\n'
                      '## Findings\nA complete source survives.\n\n'
                      '~~~markdown\n## Method\nThis is an example, not a source heading.\n~~~\n\n'
                      '### Findings\nRepeated findings also survive.\n')
            fixture.weak.write_text(source, encoding='utf-8')
            fixture.run()
            text = (fixture.wiki / 'wiki/sources/path-docs-research-note-md.md').read_text(encoding='utf-8')
            prefix = '<!-- semantic-projection-v1: '
            markers = [line for line in text.splitlines() if line.startswith(prefix)]
            self.assertEqual(1, len(markers))
            manifest = json.loads(markers[0][len(prefix):-4])
            self.assertEqual('research', manifest['source_kind'])
            self.assertEqual('path:docs/research/note.md', manifest['source_identity'])
            self.assertEqual(hashlib.sha256(source.encode()).hexdigest(), manifest['payload_sha256'])
            self.assertEqual(len(source.encode()), manifest['payload_bytes'])
            self.assertEqual({'status': 'present', 'headings': [1]}, manifest['coverage']['question'])
            self.assertEqual({'status': 'present', 'headings': [2, 3]}, manifest['coverage']['findings'])
            self.assertEqual({'status': 'not-identified', 'headings': []}, manifest['coverage']['method'])
            self.assertIn('no matching section identified in the source', text)
            self.assertIn(source, text)

    def test_large_unicode_source_is_complete_in_bounded_ordered_pages(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            source = '# A note\n\n## Question\nAn early section.\n\n## Findings\n' + ('Ω😀漢字 `code`\n' * 7000) + 'TAIL WITHOUT NEWLINE'
            fixture.weak.write_text(source, encoding='utf-8')
            fixture.run()
            entry = fixture.wiki / 'wiki/sources/path-docs-research-note-md.md'
            manifest = manifest_from(entry.read_text(encoding='utf-8'))
            for path in (fixture.wiki / 'wiki/sources').glob('*.md'):
                self.assertLessEqual(len(path.read_bytes()), 32768, path.name)
            self.assertGreater(len(manifest['parts']), 1)
            self.assertEqual(list(range(len(manifest['parts']))), [part['index'] for part in manifest['parts']])
            self.assertEqual(source.encode('utf-8'), reconstruct(fixture.wiki, manifest))
            index = (fixture.wiki / 'wiki/index.md').read_text(encoding='utf-8')
            for part in manifest['parts']:
                target = part['path'][5:-3]
                self.assertEqual(1, index.count(f'[[{target}]]'))
                self.assertIn(f'[[{target}', entry.read_text(encoding='utf-8'))

    def test_current_digest_metadata_only_is_upgraded_then_replays_without_writes(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            fixture.run()
            entry = fixture.wiki / 'wiki/sources/ticket-family-01.md'
            entry.write_text(entry.read_text(encoding='utf-8').split('## Semantic coverage')[0], encoding='utf-8')
            report = fixture.run()
            self.assertEqual(1, report['transitions']['changed'])
            self.assertIn('original body', entry.read_text(encoding='utf-8'))
            self.assertEqual([{'identity': 'ticket:family/01', 'event': 'projection-updated'}], report['events'])
            before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in fixture.wiki.rglob('*.md')}
            self.assertEqual([], fixture.run()['written'])
            self.assertEqual(before, {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in before})

    def test_shrinking_a_source_removes_only_its_obsolete_generated_parts(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            fixture.weak.write_text('# Note\n' + 'preserved text\n' * 5000, encoding='utf-8')
            fixture.run()
            entry = fixture.wiki / 'wiki/sources/path-docs-research-note-md.md'
            parts = [fixture.wiki / p['path'] for p in manifest_from(entry.read_text(encoding='utf-8'))['parts']]
            unrelated = entry.with_name(entry.stem + '.part-999999.md')
            unrelated.write_bytes(b'---\ntype: source-part\nsource_identity: someone-else\n---\nKeep this page.\n')
            before = unrelated.read_bytes()
            fixture.weak.write_text('# Note\nA short final source.\n', encoding='utf-8')
            report = fixture.run()
            self.assertTrue(all(not p.exists() for p in parts))
            self.assertEqual(sorted(p.name for p in parts), report['removed'])
            self.assertEqual(before, unrelated.read_bytes())
            self.assertEqual(fixture.weak.read_text(encoding='utf-8').encode(), reconstruct(fixture.wiki, manifest_from(entry.read_text(encoding='utf-8'))))
            self.assertEqual([], fixture.run()['written'])

    def test_literal_source_links_never_become_wiki_graph_edges(self):
        from lint_wiki import extract_wikilinks
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            source = TICKET.format(body='## What to Build\n[[not-a-wiki-page]]\n```markdown\n[[also-literal]]\n```\n')
            fixture.ticket.write_text(source, encoding='utf-8')
            fixture.run()
            text = (fixture.wiki / 'wiki/sources/ticket-family-01.md').read_text(encoding='utf-8')
            self.assertIn(source, text)
            self.assertEqual(['sources/artifact-map'], extract_wikilinks(text))

    def test_empty_or_invalid_utf8_sources_fail_before_any_wiki_write(self):
        from semantic_projection import ProjectionError
        for raw in (b'', b' \t\r\n', b'# Invalid\n\xff\n'):
            with self.subTest(raw=raw), tempfile.TemporaryDirectory() as temporary:
                fixture = Fixture(Path(temporary))
                fixture.weak.write_bytes(raw)
                before = fixture.snapshot()
                with self.assertRaises(ProjectionError):
                    fixture.run()
                self.assertEqual(before, fixture.snapshot())

    def test_wire_parser_reads_payload_but_not_literal_lookalike_markers(self):
        import semantic_projection as codec
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            source = '# Note\n\n<!-- semantic-projection-v1: {"schema":99} -->\n<!-- semantic-payload-v1: fake -->\n```\nexample\n```'
            fixture.weak.write_text(source, encoding='utf-8')
            fixture.run()
            text = (fixture.wiki / 'wiki/sources/path-docs-research-note-md.md').read_text(encoding='utf-8')
            parsed = codec.parse_page(text)
            self.assertEqual(manifest_from(text), parsed.manifest)
            self.assertEqual([source], [payload.text for payload in parsed.payloads])
            self.assertEqual(0, parsed.payloads[0].record['part_index'])
            with self.assertRaises(codec.ProjectionError):
                codec.parse_page(text + '\n<!-- semantic-projection-v1: {"schema":1} -->\n')
            with self.assertRaises(codec.ProjectionError):
                codec.parse_page(text.replace('"schema":1', '"schema":1,"schema":1', 1))

    def test_a_foreign_part_target_is_never_clobbered(self):
        from semantic_projection import ProjectionError
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            fixture.weak.write_text('# Note\n' + 'preserved text\n' * 5000, encoding='utf-8')
            fixture.run()
            entry = fixture.wiki / 'wiki/sources/path-docs-research-note-md.md'
            part = fixture.wiki / manifest_from(entry.read_text(encoding='utf-8'))['parts'][0]['path']
            part.write_bytes(b'---\ntype: source-part\nsource_identity: someone-else\n---\nPrivate authored page.\n')
            before = fixture.snapshot()
            with self.assertRaises(ProjectionError):
                fixture.run()
            self.assertEqual(before, fixture.snapshot())

    def test_every_configured_kind_has_its_own_coverage_without_widening_discovery(self):
        from project_binding import DEFAULT_DOCS_GLOBS, write_binding
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            proto = fixture.project / 'docs/prototypes/trial/NOTES.md'
            proto.parent.mkdir(parents=True)
            proto.write_text('# Trial\n\n## Artifact Graph\n- Artifact ID: `artifact:trial`\n- Role: `prototype`\n\n## Observed Results\nKeep all observations.\n', encoding='utf-8')
            guide = fixture.project / 'docs/guides/setup.md'
            guide.parent.mkdir()
            guide.write_text('# Setup\n\nPurpose\n=======\nGet ready.\n\n## Prerequisites\nUse an existing project.\n\n## Procedure\nFollow the source.\n\n## Limitations\nNo invented result.\n', encoding='utf-8')
            fixture.run()
            guide_page = fixture.wiki / 'wiki/sources/path-docs-guides-setup-md.md'
            self.assertFalse(guide_page.exists())
            write_binding(fixture.wiki, fixture.project, docs_globs=(*DEFAULT_DOCS_GLOBS, 'docs/guides/*.md'))
            fixture.run()
            expected = {
                'ticket-family-01.md': ('ticket', {'intent', 'acceptance', 'testing', 'frontier', 'exclusions'}),
                'artifact-map.md': ('spec', {'goals', 'exclusions', 'decisions', 'invariants', 'verification'}),
                'path-docs-research-note-md.md': ('research', {'question', 'method', 'findings', 'evidence', 'limitations'}),
                'artifact-trial.md': ('prototype', {'question', 'assumptions', 'results', 'limitations', 'decision'}),
                guide_page.name: ('guide', {'purpose', 'prerequisites', 'procedure', 'limitations'}),
            }
            for name, (kind, topics) in expected.items():
                with self.subTest(kind=kind):
                    text = (fixture.wiki / 'wiki/sources' / name).read_text(encoding='utf-8')
                    manifest = manifest_from(text)
                    self.assertEqual(kind, manifest['source_kind'])
                    self.assertEqual(topics, set(manifest['coverage']))
                    self.assertTrue(reconstruct(fixture.wiki, manifest))
            self.assertTrue(all(v['status'] == 'present' for v in manifest_from(guide_page.read_text(encoding='utf-8'))['coverage'].values()))

    def test_large_ticket_move_tombstone_and_restore_preserve_one_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            source = TICKET.format(body='## What to Build\n' + 'Keep this exact source.\n' * 3000)
            fixture.ticket.write_text(source, encoding='utf-8')
            fixture.run()
            entry = fixture.wiki / 'wiki/sources/ticket-family-01.md'
            manifest = manifest_from(entry.read_text(encoding='utf-8'))
            parts = [fixture.wiki / p['path'] for p in manifest['parts']]
            before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in parts}
            done = fixture.ticket.parent / 'done' / fixture.ticket.name
            done.parent.mkdir()
            fixture.ticket.rename(done)
            self.assertEqual([entry.name], fixture.run()['written'])
            self.assertEqual(before, {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in parts})
            done.unlink()
            fixture.run()
            self.assertIn('source_status: missing', entry.read_text(encoding='utf-8'))
            self.assertEqual(source.encode(), reconstruct(fixture.wiki, manifest))
            self.assertEqual([], fixture.run()['written'])
            done.write_text(source, encoding='utf-8')
            fixture.run()
            self.assertIn('source_status: present', entry.read_text(encoding='utf-8'))
            self.assertEqual(source.encode(), reconstruct(fixture.wiki, manifest))
            parts[0].unlink()
            self.assertEqual([parts[0].name], fixture.run()['written'])
            self.assertEqual(source.encode(), reconstruct(fixture.wiki, manifest))

    def test_size_and_unknown_kind_failures_do_not_publish_a_partial_corpus(self):
        from project_binding import DEFAULT_DOCS_GLOBS, write_binding
        from semantic_projection import ProjectionError
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            fixture.weak.write_text('# ' + 'oversized title ' * 3000, encoding='utf-8')
            before = fixture.snapshot()
            with self.assertRaisesRegex(ProjectionError, 'metadata/navigation'):
                fixture.run(dry_run=True)
            with self.assertRaisesRegex(ProjectionError, 'metadata/navigation'):
                fixture.run()
            self.assertEqual(before, fixture.snapshot())
            fixture.weak.write_text('# Normal note\n', encoding='utf-8')
            other = fixture.project / 'docs/unknown.md'
            other.write_text('# Unknown category\n', encoding='utf-8')
            write_binding(fixture.wiki, fixture.project, docs_globs=(*DEFAULT_DOCS_GLOBS, 'docs/unknown.md'))
            with self.assertRaisesRegex(ProjectionError, 'unresolved source kind'):
                fixture.run()
            self.assertEqual(before, fixture.snapshot())

    def test_unreadable_utf8_is_a_reported_drift_error_not_a_lint_crash(self):
        from lint_wiki import run_passes
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            fixture.run()
            fixture.weak.write_bytes(b'# Changed\n\xff\n')
            stale = next(item for item in run_passes(fixture.wiki) if item.name == 'stale-page')
            self.assertTrue(stale.issues)
            self.assertIn('source is not readable UTF-8', '\n'.join(stale.issues))

    def test_tombstone_rejects_a_symlink_before_any_wiki_or_target_write(self):
        from semantic_projection import ProjectionError
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            fixture.run()
            entry = fixture.wiki / 'wiki/sources/path-docs-research-note-md.md'
            outside = fixture.root / 'outside-wiki.md'
            entry.rename(outside)
            try:
                entry.symlink_to(outside)
            except OSError as error:
                self.skipTest(f'symlink creation unavailable: {error}')
            fixture.weak.unlink()
            before = fixture.snapshot()
            target_before = outside.read_bytes()
            with self.assertRaisesRegex(ProjectionError, 'not a regular file'):
                fixture.run()
            self.assertEqual(target_before, outside.read_bytes())
            self.assertEqual(before, fixture.snapshot())
            self.assertTrue(entry.is_symlink())


if __name__ == '__main__':
    unittest.main()
