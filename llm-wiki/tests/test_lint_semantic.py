"""Corrupt only projection data after real ingest, then observe the public lint."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest

from test_ingest_docs import Fixture, TICKET
from lint_wiki import ERROR, INFO, run_passes


def replace_record(text, name, change):
    prefix = f'<!-- {name}: '
    line = next(line for line in text.split('\n') if line.startswith(prefix))
    record = json.loads(line[len(prefix):-4])
    change(record)
    encoded = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    encoded = encoded.replace('<', r'\u003c').replace('>', r'\u003e')
    return text.replace(line, prefix + encoded + ' -->', 1)


class SemanticCoverageTests(unittest.TestCase):
    def semantic(self, fixture):
        results = {result.name: result for result in run_passes(fixture.wiki)}
        self.assertIn('semantic-coverage', results)
        return results['semantic-coverage']

    def test_current_digest_metadata_and_arbitrary_prose_cannot_pass(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            fixture.run()
            page = fixture.wiki / 'wiki/sources/ticket-family-01.md'
            text = page.read_text(encoding='utf-8')
            page.write_bytes((text.split('## Semantic coverage')[0] + '\nInvented nonempty prose.\n').encode('utf-8'))
            before = fixture.snapshot()
            result = self.semantic(fixture)
            self.assertEqual(ERROR, result.severity)
            self.assertFalse(result.ok)
            self.assertIn('ticket-family-01.md', '\n'.join(result.issues))
            self.assertIn('ingest_docs.py', result.fix)
            self.assertEqual(before, fixture.snapshot(), 'lint must never repair the wiki')
            fixture.run()
            self.assertTrue(self.semantic(fixture).ok)

    def test_manifest_identity_kind_digest_and_coverage_must_match_the_source(self):
        cases = [
            ('identity', lambda m: m.update(source_identity='artifact:invented'), 'source_identity'),
            ('kind', lambda m: m.update(source_kind='guide'), 'source_kind'),
            ('digest', lambda m: m.update(source_digest='sha256:' + '0' * 64), 'source_digest'),
            ('missing topic', lambda m: m['coverage'].pop('intent'), 'coverage'),
            ('false absence', lambda m: m['coverage'].update(intent={'status': 'not-identified', 'headings': []}), 'coverage'),
        ]
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            fixture.ticket.write_bytes(TICKET.format(body='## What to Build\n\nKeep this intention.\n').encode())
            fixture.run()
            page = fixture.wiki / 'wiki/sources/ticket-family-01.md'
            original = page.read_text(encoding='utf-8')
            self.assertTrue(self.semantic(fixture).ok)
            for name, change, diagnostic in cases:
                with self.subTest(defect=name):
                    page.write_bytes(replace_record(original, 'semantic-projection-v1', change).encode())
                    result = self.semantic(fixture)
                    self.assertFalse(result.ok)
                    self.assertIn(diagnostic, '\n'.join(result.issues))
            page.write_bytes(original.encode())
            self.assertTrue(self.semantic(fixture).ok)

    def test_payload_reconstruction_cannot_attest_itself(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            fixture.run()
            page = fixture.wiki / 'wiki/sources/path-docs-research-note-md.md'
            original = page.read_text(encoding='utf-8')
            altered = original.replace('no artifact graph here', 'xx artifact graph here')
            false_source = fixture.weak.read_text(encoding='utf-8').replace('no artifact graph here', 'xx artifact graph here')
            digest = hashlib.sha256(false_source.encode()).hexdigest()
            forged = replace_record(altered, 'semantic-projection-v1', lambda m: (m.update(payload_sha256=digest), m['parts'][0].update(payload_sha256=digest)))
            forged = replace_record(forged, 'semantic-payload-v1', lambda m: m.update(payload_sha256=digest))
            cases = [
                ('altered bytes', altered),
                ('self-consistent forged hashes', forged),
                ('missing payload', original.split('<!-- semantic-payload-v1: ')[0]),
            ]
            for name, text in cases:
                with self.subTest(defect=name):
                    page.write_bytes(text.encode())
                    before = fixture.snapshot()
                    result = self.semantic(fixture)
                    self.assertFalse(result.ok)
                    self.assertIn('payload', '\n'.join(result.issues))
                    self.assertEqual(before, fixture.snapshot())
            page.write_bytes(original.encode())
            self.assertTrue(self.semantic(fixture).ok)

    def test_wire_shape_defects_report_errors_instead_of_passing_or_crashing(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            fixture.weak.write_bytes(b'# Question\n\nA real question.\n')
            fixture.run()
            page = fixture.wiki / 'wiki/sources/path-docs-research-note-md.md'
            original = page.read_text(encoding='utf-8')
            changes = [
                ('extra manifest field', 'semantic-projection-v1', lambda m: m.update(invented=True)),
                ('null part', 'semantic-projection-v1', lambda m: m.update(parts=[None])),
                ('extra part field', 'semantic-projection-v1', lambda m: m['parts'][0].update(invented=True)),
                ('boolean heading index', 'semantic-projection-v1', lambda m: m['coverage']['question'].update(headings=[False])),
                ('extra payload field', 'semantic-payload-v1', lambda m: m.update(invented=True)),
                ('boolean part index', 'semantic-payload-v1', lambda m: m.update(part_index=False)),
                ('wrong schema', 'semantic-projection-v1', lambda m: m.update(schema=True)),
                ('missing size', 'semantic-payload-v1', lambda m: m.pop('payload_bytes')),
                ('empty payload', 'semantic-projection-v1', lambda m: m.update(payload_bytes=0)),
                ('empty inventory', 'semantic-projection-v1', lambda m: m.update(parts=[])),
            ]
            variants = [(name, replace_record(original, marker, change)) for name, marker, change in changes]
            line = next(line for line in original.split('\n') if line.startswith('<!-- semantic-projection-v1: '))
            variants += [('duplicate marker', original + line + '\n'), ('malformed marker', original.replace(line, '<!-- semantic-projection-v1: broken -->'))]
            for name, text in variants:
                with self.subTest(defect=name):
                    page.write_bytes(text.encode())
                    result = self.semantic(fixture)
                    self.assertFalse(result.ok)
                    self.assertIn(page.name, '\n'.join(result.issues))
                    self.assertIn('ingest_docs.py', result.fix)
            page.write_bytes(original.encode())
            self.assertTrue(self.semantic(fixture).ok)

    def test_all_parts_are_declared_once_ordered_owned_and_bounded(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            fixture.ticket.write_bytes(TICKET.format(body='## Testing Plan\n\n' + 'Source 🙂 witness.\n' * 5000).encode())
            fixture.run()
            entry = fixture.wiki / 'wiki/sources/ticket-family-01.md'
            entry_text = entry.read_text(encoding='utf-8')
            parts = sorted(entry.parent.glob('ticket-family-01.part-*.md'))
            self.assertGreater(len(parts), 1)
            original = {p: p.read_bytes() for p in [entry, *parts]}
            first = original[parts[0]].decode()
            payload = first[first.index('<!-- semantic-payload-v1: '):]
            manifest_line = next(line for line in entry_text.split('\n') if line.startswith('<!-- semantic-projection-v1: '))
            extra = entry.parent / 'ticket-family-01.part-999999.md'
            def entry_change(change):
                entry.write_bytes(replace_record(entry_text, 'semantic-projection-v1', change).encode())
            cases = [
                ('oversized entry', lambda: entry.write_bytes((entry_text + 'x' * 32768).encode())),
                ('oversized part', lambda: parts[0].write_bytes((first + 'x' * 32768).encode())),
                ('extra part', lambda: extra.write_bytes(original[parts[0]])),
                ('duplicate descriptor', lambda: entry_change(lambda m: m['parts'].append(m['parts'][0]))),
                ('reordered inventory', lambda: entry_change(lambda m: m['parts'].reverse())),
                ('missing part', lambda: parts[-1].unlink()),
                ('undeclared entry payload', lambda: entry.write_bytes((entry_text + payload).encode())),
                ('duplicate part payload', lambda: parts[0].write_bytes((first + payload).encode())),
                ('manifest on part', lambda: parts[0].write_bytes((first + manifest_line + '\n').encode())),
                ('foreign part metadata', lambda: parts[0].write_bytes(first.replace('source_identity: ticket:family/01', 'source_identity: artifact:foreign').encode())),
                ('wrong part type', lambda: parts[0].write_bytes(first.replace('type: source-part', 'type: source').encode())),
                ('escaping path', lambda: entry_change(lambda m: m['parts'][0].update(path='../outside.md'))),
            ]
            self.assertTrue(self.semantic(fixture).ok)
            for name, corrupt in cases:
                with self.subTest(defect=name):
                    for path, data in original.items():
                        path.write_bytes(data)
                    extra.unlink(missing_ok=True)
                    corrupt()
                    before = fixture.snapshot()
                    result = self.semantic(fixture)
                    self.assertFalse(result.ok)
                    self.assertIn('ticket-family-01', '\n'.join(result.issues))
                    self.assertEqual(before, fixture.snapshot())
            for path, data in original.items():
                path.write_bytes(data)
            extra.unlink(missing_ok=True)
            self.assertTrue(self.semantic(fixture).ok)

    def test_entry_metadata_cannot_hide_a_present_source_but_real_tombstones_are_explicit(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            source = ('# Question\n\n' + 'A preserved witness.\n' * 4000).encode()
            fixture.weak.write_bytes(source)
            fixture.run()
            page = fixture.wiki / 'wiki/sources/path-docs-research-note-md.md'
            original = page.read_text(encoding='utf-8')
            variants = [
                original.replace('source_status: present', 'source_status: missing'),
                original.replace('identity_key: path:docs/research/note.md', 'identity_key: artifact:invented'),
                original.replace('source_path: docs/research/note.md', 'source_path: docs/research/absent.md').replace('source_status: present', 'source_status: missing'),
                'Unrelated prose, with all generated metadata removed.\n',
            ]
            for text in variants:
                with self.subTest(defect=text[:80]):
                    page.write_bytes(text.encode())
                    self.assertFalse(self.semantic(fixture).ok)
            page.write_bytes(original.encode())
            fixture.weak.unlink()
            fixture.run()
            before = fixture.snapshot()
            result = self.semantic(fixture)
            self.assertTrue(result.ok, result.issues)
            self.assertIn('1 unavailable-source tombstone', result.clean_message)
            self.assertEqual(before, fixture.snapshot())
            fixture.weak.write_bytes(source)
            self.assertFalse(self.semantic(fixture).ok, 'a restored source is no longer unavailable')
            fixture.run()
            self.assertTrue(self.semantic(fixture).ok)

    def test_only_absent_binding_is_not_applicable(self):
        from project_binding import config_path
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            fixture.run()
            binding = config_path(fixture.wiki)
            binding.unlink()
            before = fixture.snapshot()
            result = self.semantic(fixture)
            self.assertEqual(INFO, result.severity)
            self.assertIn('not applicable', '\n'.join(result.issues))
            self.assertIn('project_binding.py', result.fix)
            self.assertEqual(before, fixture.snapshot())
            binding.write_bytes(b'{}')
            result = self.semantic(fixture)
            self.assertEqual(ERROR, result.severity)
            self.assertFalse(result.ok)
            self.assertIn('invalid binding', '\n'.join(result.issues))
            self.assertEqual(b'{}', binding.read_bytes())

    def test_visible_navigation_cannot_be_removed_while_markers_stay_valid(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            fixture.ticket.write_bytes(TICKET.format(body='## Testing Plan\n\n' + 'A source witness.\n' * 3000).encode())
            fixture.run()
            page = fixture.wiki / 'wiki/sources/ticket-family-01.md'
            original = page.read_text(encoding='utf-8')
            row = next(line for line in original.split('\n') if line.startswith('| testing |'))
            part_link = next(line for line in original.split('\n') if line.startswith('- Part 1:'))
            variants = [
                original.replace(row, ''),
                original.replace(row, '| testing | Invented section |'),
                original.replace(row, row + '\n' + row),
                original.replace(part_link, ''),
            ]
            for text in variants:
                with self.subTest(defect=variants.index(text)):
                    page.write_bytes(text.encode())
                    result = self.semantic(fixture)
                    self.assertFalse(result.ok)
                    self.assertIn('navigation', '\n'.join(result.issues))
            page.write_bytes(original.encode())
            self.assertTrue(self.semantic(fixture).ok)

    def test_all_kinds_have_a_clean_read_only_full_cli_in_each_supported_host(self):
        from build_timeline import build
        from ingest_docs import ingest
        from project_binding import DEFAULT_DOCS_GLOBS, write_binding
        from test_lint_drift import AUTOPILOT, Fixture as FullFixture, SCRIPTS
        modes = [('git', True, False), ('no-git', False, False), ('ignored-docs', True, True)]
        for name, repository, ignored in modes:
            with self.subTest(host=name), tempfile.TemporaryDirectory() as temporary:
                fixture = FullFixture(Path(temporary), repository=repository, ignore_docs=ignored)
                links = []
                for category, kind, heading in [('research', 'research', 'Question'), ('prototypes', 'prototype', 'Assumptions'), ('guides', 'guide', 'Purpose')]:
                    path = fixture.project / f'docs/{category}/probe.md'
                    path.parent.mkdir(parents=True, exist_ok=True)
                    text = (f'# {kind}\n\n## Artifact Graph\n- Artifact ID: `artifact:{kind}`\n'
                            f'- Role: `{kind}`\n- Parent: [map](../specs/map.md)\n\n'
                            f'{heading}\n' + '=' * len(heading) + '\n\nUnicode 🙂 and unheaded evidence.\n\n'
                            '```markdown\n<!-- semantic-projection-v1: example, not a record -->\n[[not-a-wiki-edge]]\n```\n')
                    path.write_bytes(text.encode())
                    links.append(f'- [{kind}](../{category}/probe.md)')
                source_map = fixture.project / 'docs/specs/map.md'
                source_map.write_bytes(source_map.read_text(encoding='utf-8').replace('\nbody\n', '\n' + '\n'.join(links) + '\n\n## Goals\n\nKeep the evidence.\n').encode())
                write_binding(fixture.wiki, fixture.project, docs_globs=(*DEFAULT_DOCS_GLOBS, 'docs/guides/*.md'))
                ingest(fixture.wiki, AUTOPILOT)
                build(fixture.wiki)
                kinds = set()
                for page in (fixture.wiki / 'wiki/sources').glob('*.md'):
                    prefix = '<!-- semantic-projection-v1: '
                    line = next(line for line in page.read_text(encoding='utf-8').split('\n') if line.startswith(prefix))
                    kinds.add(json.loads(line[len(prefix):-4])['source_kind'])
                self.assertEqual({'ticket', 'spec', 'research', 'prototype', 'guide'}, kinds)
                def snapshot():
                    return {str(p): (p.read_bytes(), p.stat().st_mtime_ns)
                            for root in [fixture.project / 'docs', fixture.wiki]
                            for p in root.rglob('*') if p.is_file()}
                before = snapshot()
                results = fixture.results()
                self.assertEqual(16, len(results))
                self.assertEqual({}, {key: value.issues for key, value in results.items() if value.issues})
                cli = subprocess.run([sys.executable, '-B', str(SCRIPTS / 'lint_wiki.py'), str(fixture.wiki)],
                                     capture_output=True, timeout=90)
                self.assertEqual(0, cli.returncode, cli.stderr.decode('utf-8', errors='replace'))
                self.assertIn(b'OK   semantic-coverage', cli.stdout)
                self.assertEqual(before, snapshot(), 'lint must preserve source/wiki bytes and mtimes')
                self.assertEqual([], ingest(fixture.wiki, AUTOPILOT)['written'])

    def test_source_bytes_inside_unsafe_fences_are_not_a_valid_literal_projection(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            fixture.weak.write_bytes(b'# Question\n\n```\nLiteral example\n```\n')
            fixture.run()
            page = fixture.wiki / 'wiki/sources/path-docs-research-note-md.md'
            original = page.read_text(encoding='utf-8')
            corrupt = original.replace('\n````markdown\n', '\n```markdown\n').replace('\n````\n', '\n```\n')
            self.assertNotEqual(original, corrupt)
            page.write_bytes(corrupt.encode())
            result = self.semantic(fixture)
            self.assertFalse(result.ok)
            self.assertIn('fence', '\n'.join(result.issues))
            page.write_bytes(original.encode())
            self.assertTrue(self.semantic(fixture).ok)

    def test_source_resolution_loop_is_reported_without_a_lint_crash(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            fixture.run()
            original = fixture.weak.read_bytes()
            fixture.weak.unlink()
            try:
                fixture.weak.symlink_to(fixture.weak.name)
            except (OSError, NotImplementedError) as error:
                self.skipTest(f'symlinks unavailable: {error}')
            before = {p: (p.read_bytes(), p.stat().st_mtime_ns)
                      for p in fixture.wiki.rglob('*') if p.is_file()}
            result = self.semantic(fixture)
            self.assertEqual(ERROR, result.severity)
            self.assertFalse(result.ok)
            self.assertIn('path-docs-research-note-md.md', '\n'.join(result.issues))
            self.assertEqual(before, {p: (p.read_bytes(), p.stat().st_mtime_ns)
                                     for p in fixture.wiki.rglob('*') if p.is_file()})
            self.assertTrue(fixture.weak.is_symlink())
            self.assertEqual(fixture.weak.name, str(fixture.weak.readlink()))
            fixture.weak.unlink()
            fixture.weak.write_bytes(original)
            self.assertTrue(self.semantic(fixture).ok)

    def test_invalid_source_paths_report_errors_without_changing_external_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            fixture.run()
            page = fixture.wiki / 'wiki/sources/path-docs-research-note-md.md'
            original = page.read_text(encoding='utf-8')
            outside = Path(temporary) / 'outside.md'
            outside.write_bytes(b'not a configured source')
            before = (outside.read_bytes(), outside.stat().st_mtime_ns)
            for relative in ['../outside.md', '\x00', 'docs\\research\\note.md']:
                with self.subTest(path=repr(relative)):
                    page.write_bytes(original.replace('source_path: docs/research/note.md', 'source_path: ' + relative).encode())
                    result = self.semantic(fixture)
                    self.assertFalse(result.ok)
                    self.assertIn('source_path', '\n'.join(result.issues))
            self.assertEqual(before, (outside.read_bytes(), outside.stat().st_mtime_ns))

    def test_existing_unreadable_sources_never_get_a_tombstone_exemption(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            fixture.run()
            page = fixture.wiki / 'wiki/sources/path-docs-research-note-md.md'
            original = page.read_text(encoding='utf-8')
            fixture.weak.write_bytes(b'\xff')
            for text in [original, original.replace('source_status: present', 'source_status: missing')]:
                with self.subTest(tombstone='source_status: missing' in text):
                    page.write_bytes(text.encode())
                    result = self.semantic(fixture)
                    self.assertFalse(result.ok)
                    self.assertIn('not readable UTF-8', '\n'.join(result.issues))
                    self.assertEqual(b'\xff', fixture.weak.read_bytes())
            fixture.weak.unlink()
            fixture.weak.mkdir()
            result = self.semantic(fixture)
            self.assertFalse(result.ok)
            self.assertIn('not a readable source file', '\n'.join(result.issues))

    def test_a_renamed_entry_cannot_tombstone_an_identity_that_is_still_present(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            fixture.run()
            page = fixture.wiki / 'wiki/sources/path-docs-research-note-md.md'
            text = page.read_text(encoding='utf-8').replace('source_status: present', 'source_status: missing')
            text = text.replace('source_path: docs/research/note.md', 'source_path: docs/research/absent.md')
            page.unlink()
            (page.parent / 'retained-legacy.md').write_bytes(text.encode())
            result = self.semantic(fixture)
            self.assertFalse(result.ok)
            self.assertIn('identity', '\n'.join(result.issues))

    def test_a_symbolic_source_directory_cannot_supply_out_of_wiki_payloads(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            fixture.run()
            sources = fixture.wiki / 'wiki/sources'
            outside = Path(temporary) / 'outside-sources'
            sources.rename(outside)
            before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in outside.glob('*.md')}
            sources.symlink_to(outside, target_is_directory=True)
            try:
                result = self.semantic(fixture)
                self.assertFalse(result.ok)
                self.assertIn('outside', '\n'.join(result.issues))
                self.assertEqual(before, {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in outside.glob('*.md')})
            finally:
                sources.unlink()


if __name__ == '__main__':
    unittest.main()
