from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
from autopilot.kernel import Kernel
from autopilot.ledger import AtomicLedger
from autopilot.local_report import build_report, compare_reports, main
from autopilot.ticket_contract import parse_ticket_folder


CONTEXT = {'workload': 'controlled-v1:one-ticket', 'environment': 'Windows/Python3.12/Git2/test-host', 'protocol': 'serial; explicit leaf seconds; no provider', 'wall_time_unit': 'seconds'}


def status():
    return {'run_id': 'sample', 'tickets': {'T1': {'quality_failures': 2}},
            'budget_config': {'max_quality_failures': 3}}


def leaf(stage, seconds):
    return {'event': 'leaf-result-recorded', 'ticket_id': 'T1',
            'details': {'stage': stage, 'wall_time': seconds, 'complete': True}}


def phase(report, stage):
    return next(row for row in report['tickets']['T1']['phases'] if row['stage'] == stage)


class LocalReportTests(unittest.TestCase):
    def test_zero_is_recorded_but_missing_is_unavailable(self):
        report = build_report(status(), [leaf('review', 0)])
        self.assertEqual(0, phase(report, 'review')['duration']['value'])
        self.assertEqual('recorded', phase(report, 'review')['duration']['availability'])
        self.assertIsNone(phase(report, 'qa-plan')['duration']['value'])
        self.assertEqual('unspecified', phase(report, 'review')['duration']['unit'])
        self.assertEqual([], report['slowest_observed'])
        self.assertIsNone(report['session_time']['value'])
        self.assertIsNone(report['model_tokens']['value'])

    def test_partial_invalid_and_fractional_observations(self):
        events = [leaf('review', value) for value in [1.5, None, True, -1, float('nan')]]
        before = copy.deepcopy(events)
        report = build_report(status(), events)
        duration = phase(report, 'review')['duration']
        self.assertEqual(1.5, duration['value'])
        self.assertEqual('partial', duration['availability'])
        self.assertEqual(1, duration['observations'])
        self.assertEqual(4, duration['missing'])
        self.assertEqual(before, events)

    def test_large_integer_seconds_do_not_require_float_conversion(self):
        value = 10 ** 400
        self.assertEqual(value, phase(build_report(status(), [leaf('review', value)]), 'review')['duration']['value'])

    def test_comparison_rejects_different_recorded_check_environments(self):
        checks = {'schema': 1, 'records': [], 'platform': 'win32', 'mode': 'quick'}
        left = build_report(status(), [], context=CONTEXT, checks=checks)
        right = build_report(status(), [], context=CONTEXT, checks={**checks, 'platform': 'linux'})
        self.assertEqual('incomparable', compare_reports(left, right)['status'])
        with self.assertRaises(ValueError):
            build_report(status(), [], context={**CONTEXT, 'prompt': 'not accepted'})

    def test_slowest_order_is_stable_and_excludes_unavailable(self):
        events = [leaf('verify', 8), leaf('review', 4), leaf('qa-plan', 8), leaf('review', 2)]
        report = build_report(status(), events, context=CONTEXT)
        self.assertEqual(['qa-plan', 'verify', 'review'], [x['stage'] for x in report['slowest_observed']])
        self.assertEqual([8, 8, 6], [x['recorded_wall_time'] for x in report['slowest_observed']])
        self.assertEqual(report, build_report(status(), list(reversed(events)), context=CONTEXT))

    def test_retry_requests_are_not_leaf_continuations_or_terminal_failures(self):
        events = [leaf('review', 2), leaf('review', 3),
                  {'event': 'quality-failed', 'ticket_id': 'T1', 'details': {'stage': 'review', 'failures': 1}},
                  {'event': 'final-tree-quality-stage-failed', 'ticket_id': 'T1', 'details': {'stage': 'review', 'failures': 3}}]
        report = build_report(status(), events)
        row = phase(report, 'review')
        self.assertEqual(2, row['leaf_observations'])
        self.assertEqual(1, row['retry_requests']['value'])
        self.assertEqual(2, report['tickets']['T1']['quality_failures']['value'])
        self.assertIsNone(phase(build_report(status(), None), 'review')['retry_requests']['value'])

    def test_unknown_retry_threshold_remains_unavailable(self):
        data = status()
        data['budget_config'] = {}
        events = [{'event': 'quality-failed', 'ticket_id': 'T1', 'details': {'stage': 'review', 'failures': 1}}]
        self.assertIsNone(phase(build_report(data, events), 'review')['retry_requests']['value'])

    def test_checks_report_exports_only_existing_counts_and_environment(self):
        checks = {'schema': 1, 'mode': 'quick', 'platform': 'win32', 'python_version': '3.12',
                  'records': [{'id': 'test-one', 'status': 'succeeded', 'command': ['credential-secret'], 'stdout_log': 'private-log'}]}
        data = status()
        data['prompt'] = 'prompt-secret'
        data['tickets']['T1']['delivery'] = {'body': 'provider-secret'}
        report = build_report(data, [leaf('review', 2)], checks=checks)
        self.assertEqual(1, report['checks']['counts']['succeeded'])
        self.assertIsNone(report['checks']['duration']['value'])
        text = json.dumps(report)
        for secret in ['credential-secret', 'private-log', 'prompt-secret', 'provider-secret']:
            self.assertNotIn(secret, text)
        self.assertEqual('check invocations', report['checks']['count_unit'])

    def test_controlled_comparison_and_unknown_or_incomparable_context(self):
        left = build_report(status(), [leaf('review', 2)], context=CONTEXT)
        right = build_report(status(), [leaf('review', 5)], context=CONTEXT)
        comparison = compare_reports(left, right)
        self.assertEqual('declared-comparable', comparison['status'])
        row = next(x for x in comparison['phase_deltas'] if x['stage'] == 'review')
        self.assertEqual(3, row['recorded_wall_time_delta'])
        self.assertEqual('seconds', row['unit'])
        row = next(x for x in comparison['phase_deltas'] if x['stage'] == 'qa-plan')
        self.assertIsNone(row['recorded_wall_time_delta'])
        self.assertEqual('unavailable', compare_reports(left, build_report(status(), []))['status'])
        unknown_unit = build_report(status(), [], context={**CONTEXT, 'wall_time_unit': 'unspecified'})
        self.assertEqual('unavailable', compare_reports(unknown_unit, unknown_unit)['status'])
        changed = build_report(status(), [], context={**CONTEXT, 'environment': 'different-host'})
        self.assertEqual('incomparable', compare_reports(left, changed)['status'])
        self.assertNotIn('speedup', comparison)

    def test_partial_durations_are_not_compared_as_complete_totals(self):
        left = build_report(status(), [leaf('review', 2), leaf('review', None)], context=CONTEXT)
        right = build_report(status(), [leaf('review', 4)], context=CONTEXT)
        row = next(x for x in compare_reports(left, right)['phase_deltas'] if x['stage'] == 'review')
        self.assertIsNone(row['recorded_wall_time_delta'])

    def test_cli_loads_real_ledger_without_save_event_or_provider(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'ledger.json'
            graph = parse_ticket_folder(Path(__file__).parent / 'fixtures/happy')
            kernel = Kernel.new('local-report-test', graph, provider='github')
            store = AtomicLedger(path)
            store.save(kernel.ledger)
            before = path.read_bytes()
            output = io.StringIO()
            with mock.patch.object(AtomicLedger, 'save', side_effect=AssertionError('save')), \
                 mock.patch.object(Kernel, '_event', side_effect=AssertionError('event')), \
                 mock.patch('autopilot.providers.ProviderExecutor', side_effect=AssertionError('provider')), \
                 mock.patch.object(subprocess, 'run', side_effect=AssertionError('subprocess')), \
                 redirect_stdout(output):
                self.assertEqual(0, main([str(path)]))
            self.assertEqual(before, path.read_bytes())
            result = json.loads(output.getvalue())
            self.assertEqual('local-report-test', result['report']['run_id'])
            self.assertEqual([], result['report']['slowest_observed'])
            self.assertIsNone(result['comparison'])

    def test_cli_comparison_reads_context_and_checks_without_changing_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            graph = parse_ticket_folder(Path(__file__).parent / 'fixtures/happy')
            ledgers = [root / 'left.json', root / 'right.json']
            for index, path in enumerate(ledgers):
                AtomicLedger(path).save(Kernel.new('sample-' + str(index), graph, provider='github').ledger)
            context = root / 'context.json'
            context.write_text(json.dumps(CONTEXT), encoding='utf-8')
            checks = root / 'checks.json'
            checks.write_text(json.dumps({'schema': 1, 'records': [{'status': 'succeeded', 'command': ['hidden-argv']}]}), encoding='utf-8')
            inputs = {path: path.read_bytes() for path in [*ledgers, context, checks]}
            output = io.StringIO()
            with redirect_stdout(output):
                result = main([str(ledgers[0]), '--context', str(context), '--checks', str(checks),
                               '--compare-ledger', str(ledgers[1]), '--compare-context', str(context), '--compare-checks', str(checks)])
            self.assertEqual(0, result)
            data = json.loads(output.getvalue())
            self.assertEqual('declared-comparable', data['comparison']['status'])
            self.assertEqual(1, data['report']['checks']['counts']['succeeded'])
            self.assertNotIn('hidden-argv', output.getvalue())
            self.assertEqual(inputs, {path: path.read_bytes() for path in inputs})

    def test_cli_rejects_invalid_input_without_echoing_contents(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'bad.json'
            path.write_text('{"secret": "do-not-echo"}', encoding='utf-8')
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(2, main([str(path)]))
            self.assertNotIn('do-not-echo', output.getvalue())
            self.assertEqual('input-unavailable-or-invalid', json.loads(output.getvalue())['error'])


if __name__ == '__main__':
    unittest.main()
