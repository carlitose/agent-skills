"""SPB-03 causal repair fixtures: real Git/test processes, substituted model and classifier."""
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
import test_chain_controller as fixtures
from chain_controller import ChainGate, _load
from autopilot.command_capture import CaptureFailure
from findings import parse_findings


class RepairTests(unittest.TestCase):
    setUp = fixtures.ControllerTests.setUp
    git = fixtures.ControllerTests.git
    ticket = fixtures.ControllerTests.ticket
    run_ticket = fixtures.ControllerTests.run_ticket

    def review_prose(self, prose):
        original = self.peer.prompt
        def prompt(message):
            reply = original(message)
            if json.loads(message)['role'] == 'review':
                reply['text'] = prose
            return reply
        self.peer.prompt = prompt

    def test_nonblocking_review_reaches_semantic_yes_without_becoming_clean(self):
        prose = '[should-fix] value.py:1 - Add an optional convenience API not requested by this ticket.'
        self.review_prose(prose)
        observed = []
        original_jev = self.decision.jev
        def jev(request):
            observed.append(request)
            return original_jev(request)
        self.decision.jev = jev
        row = self.run_ticket()
        self.assertEqual((row['status'], row['failures']), ('completed-local', 0))
        self.assertEqual(row['review_prose'], prose)
        self.assertEqual(row['findings']['state'], 'parsed')
        request = next(r for r in observed if r['question_id'] == 'coverage')
        self.assertEqual(request['state']['review'], prose)
        self.assertEqual(request['binding']['candidate_ref'], row['candidate'])
        self.assertIn('+VALUE = 1', request['state']['diff'])
        self.assertEqual(request['state']['test_observations']['receipts'][0]['exit_code'], 0)
        self.assertEqual(row['receipts'][0]['candidate_ref'], row['candidate'])

    def test_nit_is_not_an_automatic_blocker(self):
        self.review_prose('[nit] value.py:1 - Prefer a longer constant name.')
        row = self.run_ticket()
        self.assertEqual((row['status'], row['failures']), ('completed-local', 0))
        self.assertEqual(row['findings']['findings'][0]['severity'], 'nit')

    def test_nonblocker_semantic_no_still_fails_and_blocks_dependents(self):
        prose = '[should-fix] value.py:1 - A required behavior is missing despite green tests.'
        self.review_prose(prose)
        observed = []
        def jev(request):
            observed.append(request)
            return {'answers': {request['question_id']: {'type': 'noul', 'noul': 0}}, 'usage': {}}
        self.decision.jev = jev
        self.decision.judge = lambda request: self.fail('A decided NO cannot be bypassed')
        row = self.run_ticket()
        self.assertEqual((row['status'], row['failures']), ('failed', 3))
        self.assertEqual(row['receipts'][0]['exit_code'], 0)
        self.assertEqual(observed[0]['state']['review'], prose)
        self.assertEqual(self.run_ticket('B', ['A'])['status'], 'dependency-blocked')

    def test_nonblocker_uncertainty_is_gate_not_three_code_failures(self):
        prose = '[should-fix] value.py:1 - The requirement interpretation needs adjudication.'
        self.review_prose(prose)
        self.decision.jev = lambda request: {
            'answers': {request['question_id']: {'type': 'noul', 'noul': .5}}, 'usage': {}}
        row = self.run_ticket()
        self.assertEqual((row['status'], row['failures']), ('human-gated', 0))
        self.assertEqual(row['failure_kind'], 'coverage-uncertain')
        self.assertEqual(row['review_prose'], prose)
        self.assertTrue(_load(self.owner.path)['gate'])

    def test_nonblocker_judge_fallback_can_complete_without_discarding_findings(self):
        prose = '[should-fix] value.py:1 - Optional API deserves consideration.'
        self.review_prose(prose)
        observed = []
        self.decision.jev = lambda request: {
            'answers': {request['question_id']: {'type': 'noul', 'noul': .5}}, 'usage': {}}
        def judge(request):
            observed.append(request)
            return {**request['binding'], 'text': 'Answer: yes', 'stopReason': 'stop', 'usage': {}}
        self.decision.judge = judge
        row = self.run_ticket()
        self.assertEqual((row['status'], row['failures']), ('completed-local', 0))
        self.assertEqual(row['findings']['state'], 'parsed')
        self.assertEqual(observed[0]['state']['review'], prose)
        self.assertEqual(observed[0]['binding']['candidate_ref'], row['candidate'])

    def test_explicit_blocker_cannot_be_overridden_by_semantic_yes(self):
        self.review_prose('[blocker] value.py:1 - Explicit required-acceptance defect.')
        self.decision.jev = lambda request: self.fail('Explicit blocker is a local veto')
        row = self.run_ticket()
        self.assertEqual((row['status'], row['failures']), ('failed', 3))
        self.assertEqual(row['receipts'][0]['exit_code'], 0)
        self.assertEqual(row['findings']['findings'][0]['severity'], 'blocker')

    def test_failed_public_tests_remain_veto_with_nonblocker_review(self):
        self.peer.bad = True
        self.review_prose('[nit] value.py:1 - Optional style change.')
        self.decision.jev = lambda request: self.fail('Failed public tests cannot be approved')
        row = self.run_ticket()
        self.assertEqual((row['status'], row['failures']), ('failed', 3))
        self.assertEqual(row['receipts'][0]['exit_code'], 1)

    def test_failed_tests_with_unparsed_review_reach_fix_not_human_gate(self):
        self.peer.bad = True
        prose = '[blocker] value.py:1 - Public execution fails.\n[should-fix] tests - Add public coverage.'
        self.review_prose(prose)
        self.decision.jev = lambda request: self.fail('Known public failure cannot need external approval')
        row = self.run_ticket()
        self.assertEqual((row['status'], row['failures']), ('failed', 3))
        self.assertEqual(row['review_prose'], prose)
        self.assertEqual(row['findings']['state'], 'unparsed')
        self.assertEqual(row['receipts'][0]['exit_code'], 1)
        self.assertEqual(self.peer.calls, ['builder', 'review', 'fix', 'review', 'fix', 'review'])

    def test_non_python_findings_keep_path_line_severity_and_explanation(self):
        for path in ('src/parser.c', 'src/api.h', 'src/type.js', 'src/type.ts',
                     'src/type.tsx', 'src/type.jsx', 'src/type.mjs', 'test.lua', 'value.py'):
            with self.subTest(path=path):
                parsed = parse_findings(f'[blocker] {path}:12 - Public example is broken.', any_extension=True)
                self.assertEqual(parsed, {'state': 'parsed', 'findings': [
                    {'severity': 'blocker', 'path': path, 'line': 12,
                     'text': 'Public example is broken.'}]})

    def test_unparsed_review_gates_without_consuming_code_failures(self):
        original = self.peer.prompt
        prose = '[blocker] location missing - Preserve this evidence.'
        def prompt(message):
            reply = original(message)
            if json.loads(message)['role'] == 'review':
                reply['text'] = prose
            return reply
        self.peer.prompt = prompt
        row = self.run_ticket()
        self.assertEqual(row['status'], 'human-gated')
        self.assertEqual(row['failure_kind'], 'review-format')
        self.assertEqual(row['failures'], 0)
        self.assertEqual(row['review_prose'], prose)
        self.assertEqual(self.peer.calls, ['builder', 'review'])
        self.assertEqual(self.decision.state['calls'], [])
        self.assertTrue(_load(self.owner.path)['gate'])
        with self.assertRaises(ChainGate):
            self.run_ticket('B')

    def test_fix_receives_failing_public_test_stderr_and_candidate(self):
        original = self.peer.prompt
        seen = []
        self.peer.bad = True
        command = [sys.executable, '-B', '-c',
                   'import sys; from value import VALUE; '
                   'print("NEED VALUE=1", file=sys.stderr) if VALUE!=1 else None; '
                   'sys.exit(0 if VALUE==1 else 1)']
        def prompt(message):
            value = json.loads(message)
            if value['role'] in ('fix', 'review'):
                seen.append(value)
            if value['role'] == 'fix':
                tests = value.get('test_observations', {})
                rows = tests.get('receipts', [])
                if rows and 'NEED VALUE=1' in rows[0].get('stderr', ''):
                    self.peer.bad = False
            return original(message)
        self.peer.prompt = prompt
        row = self.owner.run_ticket(self.ticket(), ['value.py'], [command])
        self.assertEqual(row['status'], 'completed-local')
        fix = next(v for v in seen if v['role'] == 'fix')
        evidence = fix['test_observations']['receipts'][0]
        self.assertEqual(evidence['exit_code'], 1)
        self.assertEqual(evidence['argv'], command)
        self.assertIsNotNone(evidence['candidate_ref'])
        self.assertEqual(hashlib.sha256(Path(evidence['path']).read_bytes()).hexdigest(), evidence['sha256'])
        self.assertTrue(all(v.get('test_observations', {}).get('receipts') for v in seen))

    def test_large_public_output_reaches_coverage_with_full_receipt_preserved(self):
        observed = []
        original_jev = self.decision.jev
        def jev(request):
            observed.append(request)
            return original_jev(request)
        self.decision.jev = jev
        command = [sys.executable, '-B', '-c', 'print("X" * 100000)']
        row = self.owner.run_ticket(self.ticket(), ['value.py'], [command])
        self.assertEqual(row['status'], 'completed-local')
        request = next(r for r in observed if r['question_id'] == 'coverage')
        self.assertLessEqual(len(json.dumps(request, ensure_ascii=False).encode()), 65536)
        tests = request['state']['test_observations']
        self.assertLessEqual(len(json.dumps(tests, ensure_ascii=False).encode()), 32768)
        preview = tests['receipts'][0]
        self.assertTrue(preview['stdout_truncated'])
        self.assertEqual(preview['candidate_ref'], request['binding']['candidate_ref'])
        self.assertEqual(hashlib.sha256(Path(preview['path']).read_bytes()).hexdigest(),
                         preview['sha256'])
        full = json.loads(Path(preview['path']).read_text(encoding='utf-8'))['stdout']
        self.assertGreaterEqual(len(full), 100000)
        self.assertEqual(full, row['receipts'][0]['stdout'])
        self.assertNotIn('receipts', request['state'])

    def test_oversized_diff_stays_gated_with_specific_reason_and_full_artifact(self):
        original_prompt = self.peer.prompt
        def prompt(message):
            reply = original_prompt(message)
            if json.loads(message)['role'] == 'builder':
                (self.copy / 'value.py').write_bytes(b'VALUE = 1\n#' + b'X' * 70000 + b'\n')
            return reply
        self.peer.prompt = prompt
        row = self.run_ticket()
        self.assertEqual((row['status'], row['failures']), ('human-gated', 0))
        self.assertTrue(row['failure_reason'].startswith('semantic-input-bound:'))
        self.assertIn('65536', row['failure_reason'])
        self.assertEqual(self.decision.state['calls'], [])
        self.assertEqual(self.peer.calls, ['builder', 'review', 'analysis'])
        artifact = row['diff_artifact']
        raw = Path(artifact['path']).read_bytes()
        self.assertIn(b'X' * 70000, raw)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), artifact['sha256'])
        self.assertEqual(row['receipts'][0]['exit_code'], 0)

    def test_large_green_output_does_not_override_semantic_no(self):
        self.decision.jev = lambda request: {
            'answers': {request['question_id']: {'type': 'noul', 'noul': 0}}, 'usage': {}}
        self.decision.judge = lambda request: self.fail('A decided NO must not call judge')
        command = [sys.executable, '-B', '-c',
                   'from value import VALUE; assert VALUE == 1; print("X" * 100000)']
        row = self.owner.run_ticket(self.ticket(), ['value.py'], [command])
        self.assertEqual((row['status'], row['failures']), ('failed', 3))
        self.assertEqual(row['receipts'][0]['exit_code'], 0)
        self.assertGreaterEqual(len(row['receipts'][0]['stdout']), 100000)
        self.assertEqual([c['kind'] for c in self.decision.state['calls']], ['jev'])
        self.assertEqual(self.run_ticket('B', ['A'])['status'], 'dependency-blocked')

    def test_public_test_preview_is_bounded_and_declares_truncation(self):
        original = self.peer.prompt
        seen = []
        def prompt(message):
            value = json.loads(message)
            if value['role'] == 'review':
                seen.append(value['test_observations'])
            return original(message)
        self.peer.prompt = prompt
        command = [sys.executable, '-B', '-c', 'print("X" * 65536)']
        self.owner.run_ticket(self.ticket(), ['value.py'], [command])
        self.assertLessEqual(len(json.dumps(seen[0], ensure_ascii=False).encode()), 32768)
        record = seen[0]['receipts'][0]
        self.assertTrue(record['stdout_truncated'])
        output = json.loads(Path(record['path']).read_text(encoding='utf-8'))['stdout']
        self.assertEqual(output[:65536], 'X' * 65536)
        self.assertIn(output[65536:], ('\n', '\r\n'))

    def test_non_utf8_frozen_diff_is_preserved_as_infrastructure_gate(self):
        original = self.peer.prompt
        def prompt(message):
            reply = original(message)
            if json.loads(message)['role'] == 'builder':
                (self.copy / 'raw.txt').write_bytes(b'\xff\n')
            return reply
        self.peer.prompt = prompt
        row = self.owner.run_ticket(self.ticket(), ['.'], [self.test])
        self.assertEqual(row['status'], 'infrastructure-gated')
        self.assertEqual(row['failures'], 0)
        self.assertEqual(row['failure_kind'], 'diff-encoding')
        artifact = row['diff_artifact']
        raw = Path(artifact['path']).read_bytes()
        self.assertIn(b'\xff', raw)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), artifact['sha256'])
        self.assertEqual((self.copy / 'raw.txt').read_bytes(), b'\xff\n')
        self.assertTrue(row['candidate'])
        self.assertTrue(_load(self.owner.path)['gate'])
        self.assertEqual(self.decision.state['calls'], [])

    def test_interrupted_turn_records_gate_and_keeps_inflight_and_partial_copy(self):
        original = self.peer.prompt
        def prompt(message):
            original(message)
            raise RuntimeError('fake sensitive detail not for checkpoint')
        self.peer.prompt = prompt
        with self.assertRaises(RuntimeError):
            self.run_ticket()
        state = _load(self.owner.path)
        self.assertEqual(state['tickets']['A']['status'], 'infrastructure-gated')
        self.assertEqual(state['tickets']['A']['failures'], 0)
        self.assertEqual(state['inflight']['role'], 'builder')
        self.assertTrue(state['gate'])
        self.assertNotIn('fake sensitive detail', self.owner.path.read_text(encoding='utf-8'))
        self.assertEqual((self.copy / 'value.py').read_bytes(), b'VALUE = 1\n')

    def test_capture_launch_failure_is_not_three_code_failures(self):
        with patch('chain_controller.capture_command', side_effect=CaptureFailure('launch', 'fake private message')):
            row = self.run_ticket()
        self.assertEqual(row['status'], 'infrastructure-gated')
        self.assertEqual(row['failure_kind'], 'test-capture')
        self.assertEqual(row['failures'], 0)
        self.assertEqual(row['receipts'][0]['failure'], 'launch')
        self.assertEqual(self.peer.calls, ['builder'])
        self.assertTrue(_load(self.owner.path)['gate'])

    def test_real_failed_tests_still_consume_three_final_failures(self):
        self.peer.bad = True
        row = self.run_ticket()
        self.assertEqual((row['status'], row['failures']), ('failed', 3))
        self.assertEqual(self.run_ticket('B', ['A'])['status'], 'dependency-blocked')


if __name__ == '__main__':
    unittest.main()
