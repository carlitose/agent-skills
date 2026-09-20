from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest
from urllib.parse import parse_qs, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from autopilot.git_ops import CommandResult  # noqa: E402
from autopilot.providers import (  # noqa: E402
    GET_CHECKS_AND_POLICIES, GitHubProvider, ProviderError, ProviderExecutor,
)

HEAD = '1' * 40
PROTECTION_DOC = 'https://docs.github.com/rest/branches/branch-protection#get-branch-protection'


def api_error(message: str, status: int, documentation: str = PROTECTION_DOC) -> CommandResult:
    return CommandResult(json.dumps({'message': message, 'status': str(status),
                                     'documentation_url': documentation}), 'API error', 1)


def protection(*contexts: str) -> dict:
    return {'required_status_checks': {
        'strict': True, 'contexts': list(contexts),
        'checks': [{'context': context, 'app_id': None} for context in contexts],
    }}


def check_run(name='ci', *, app_id=15368, head=HEAD, status='completed', conclusion='success', run_id=101):
    return {'id': run_id, 'name': name, 'app': {'id': app_id}, 'head_sha': head,
            'status': status, 'conclusion': conclusion}


class ReadbackCommands:
    """Controlled external API outcomes; never substitutes provider logic."""

    def __init__(self):
        self.view = {'number': 17, 'headRefOid': HEAD, 'baseRefName': 'main',
                     'mergeStateStatus': 'CLEAN', 'statusCheckRollup': []}
        self.rules = []
        self.protection = api_error('Branch not protected', 404)
        self.check_pages = {}
        self.gh_235 = False
        self.commands = []

    def run(self, command: list[str], *, cwd: Path) -> CommandResult:
        self.commands.append(command)
        if command[:3] == ['gh', 'pr', 'view']:
            value = self.view
        elif command[:2] == ['gh', 'api'] and '/rules/branches/' in command[2]:
            value = self.rules
        elif command[:2] == ['gh', 'api'] and command[2].endswith('/protection'):
            value = self.protection
        elif command[:2] == ['gh', 'api'] and '/check-runs?' in command[2]:
            query = parse_qs(urlsplit(command[2]).query)
            assert query['filter'] == ['latest']
            assert '--paginate' in command
            if self.gh_235:
                assert '--slurp' not in command, 'unknown flag in gh 2.35.0: --slurp'
            value = self.check_pages.get(int(query['app_id'][0]), [{'total_count': 0, 'check_runs': []}])
            if '--slurp' not in command and isinstance(value, list):
                return CommandResult('\n'.join(json.dumps(page) for page in value), '', 0)
        else:
            raise AssertionError(f'unexpected external operation: {command}')
        return value if isinstance(value, CommandResult) else CommandResult(json.dumps(value), '', 0)


class GitHubRequiredChecksTests(unittest.TestCase):
    def setUp(self):
        self.commands = ReadbackCommands()
        self.provider = ProviderExecutor(GitHubProvider(), cwd=Path.cwd(), runner=self.commands)

    def observe(self):
        return self.provider.execute(GET_CHECKS_AND_POLICIES, pr_id='17', expected_head=HEAD)

    def test_missing_classic_required_check_remains_pending(self):
        self.commands.protection = protection('local-profile')
        result = self.observe()
        self.assertEqual(result['checks_and_policies'], [
            {'bucket': 'pending', 'name': 'local-profile', 'state': 'EXPECTED', 'workflow': ''},
        ])
        self.assertEqual(result['active_rules'], [])
        self.assertEqual(result['branch_protection_observation']['status'], 'observed')
        self.assertEqual(result['head_sha'], HEAD)

    def test_same_name_success_does_not_satisfy_required_ruleset_app(self):
        self.commands.rules = [{'type': 'required_status_checks', 'parameters': {
            'required_status_checks': [{'context': 'ci', 'integration_id': 15368}],
        }}]
        self.commands.view['statusCheckRollup'] = [
            {'name': 'ci', 'status': 'COMPLETED', 'conclusion': 'SUCCESS'},
        ]
        # No run from the required app, even though an identically named check passed.
        result = self.observe()
        self.assertEqual([item['bucket'] for item in result['checks_and_policies']], ['pass', 'pending'])
        self.assertEqual(result['checks_and_policies'][1]['state'], 'EXPECTED')

    def test_classic_app_state_is_observed_fresh_for_the_exact_head(self):
        self.commands.protection = protection('ci')
        self.commands.protection['required_status_checks']['checks'][0]['app_id'] = 15368
        self.commands.view['statusCheckRollup'] = [{'name': 'ci', 'conclusion': 'SUCCESS'}]
        for status, conclusion, bucket in [('completed', 'success', 'pass'),
                                           ('in_progress', None, 'pending'),
                                           ('completed', 'failure', 'fail')]:
            with self.subTest(status=status, conclusion=conclusion):
                self.commands.check_pages[15368] = [{'total_count': 1, 'check_runs': [
                    check_run(status=status, conclusion=conclusion),
                ]}]
                result = self.observe()
                self.assertEqual([item['bucket'] for item in result['checks_and_policies']], ['pass', bucket])
        requests = [cmd for cmd in self.commands.commands if '/check-runs?' in cmd[2]]
        self.assertEqual(len(requests), 3)
        self.assertTrue(all('/commits/' + HEAD + '/' in cmd[2] for cmd in requests))

    def test_malformed_classic_policies_fail_closed(self):
        for policy in [[], {'contexts': 'ci', 'checks': []},
                       {'contexts': [None], 'checks': []},
                       {'contexts': [], 'checks': 'ci'},
                       {'contexts': [], 'checks': [{}]},
                       {'contexts': [], 'checks': [{'context': 'ci'}]},
                       {'contexts': [], 'checks': [{'context': 'ci', 'app_id': True}]},
                       {'contexts': [], 'checks': [{'context': 'ci', 'app_id': '15368'}]}]:
            with self.subTest(policy=policy):
                self.commands.protection = {'required_status_checks': policy}
                with self.assertRaises(ProviderError):
                    self.observe()

    def test_sources_union_deduplicates_without_losing_existing_failures_or_queue(self):
        self.commands.protection = protection('shared', 'classic-only')
        self.commands.rules = [{'type': 'merge_queue'}, {'type': 'required_status_checks', 'parameters': {
            'required_status_checks': [{'context': 'shared'}, {'context': 'rules-only'}, {'context': 'shared'}],
        }}]
        self.commands.view['statusCheckRollup'] = [{'name': 'other', 'conclusion': 'FAILURE'}]
        result = self.observe()
        self.assertEqual([item['name'] for item in result['checks_and_policies']],
                         ['other', 'shared', 'classic-only', 'rules-only'])
        self.assertEqual([item['bucket'] for item in result['checks_and_policies']],
                         ['fail', 'pending', 'pending', 'pending'])
        self.assertEqual(result['merge_mode'], 'queue')
        self.assertEqual(len(result['active_rules']), 2)

    def test_absence_and_plan_limitation_are_distinct_and_preserve_rules(self):
        self.commands.rules = [{'type': 'required_status_checks', 'parameters': {
            'required_status_checks': [{'context': 'rules-only'}],
        }}]
        for response, status in [
            (api_error('Branch not protected', 404), 'absent'),
            (api_error('Upgrade to GitHub Pro or make this repository public to enable this feature.', 403),
             'feature-unavailable'),
        ]:
            with self.subTest(status=status):
                self.commands.protection = response
                result = self.observe()
                self.assertEqual(result['branch_protection_observation']['status'], status)
                self.assertEqual(result['checks_and_policies'][0]['bucket'], 'pending')

    def test_ordinary_errors_and_malformed_responses_are_not_absence(self):
        for response in [api_error('Branch not found', 404), api_error('Not Found', 404),
                         api_error('Resource not accessible by integration', 403),
                         api_error('API rate limit exceeded', 403), api_error('rate limited', 429),
                         api_error('server unavailable', 500),
                         api_error('Branch not protected', 404, 'https://example.invalid/not-the-api'),
                         CommandResult('not json', '', 0), CommandResult('', 'network failed', 1), []]:
            with self.subTest(response=response):
                self.commands.protection = response
                with self.assertRaises(ProviderError):
                    self.observe()

    def test_rules_plan_limitation_does_not_hide_classic_requirement(self):
        self.commands.rules = api_error(
            'Upgrade to GitHub Pro or make this repository public to enable this feature.', 403,
            'https://docs.github.com/rest/repos/rules#get-rules-for-a-branch')
        self.commands.protection = protection('classic-only')
        result = self.observe()
        self.assertEqual(result['rules_observation']['status'], 'feature-unavailable')
        self.assertEqual(result['checks_and_policies'][0]['name'], 'classic-only')
        self.assertEqual(result['checks_and_policies'][0]['bucket'], 'pending')

    def test_existing_context_pass_and_unrestricted_app_need_no_app_read(self):
        self.commands.view['statusCheckRollup'] = [{'context': 'ci', 'state': 'SUCCESS'}]
        for app_id in [None, -1]:
            with self.subTest(app_id=app_id):
                self.commands.protection = protection('ci')
                self.commands.protection['required_status_checks']['checks'][0]['app_id'] = app_id
                result = self.observe()
                self.assertEqual(len(result['checks_and_policies']), 1)
                self.assertEqual(result['checks_and_policies'][0]['bucket'], 'pass')
        self.assertFalse(any('/check-runs?' in cmd[2] for cmd in self.commands.commands))

    def test_protected_branch_without_required_checks(self):
        self.commands.protection = {'enforce_admins': {'enabled': True}}
        result = self.observe()
        self.assertEqual(result['checks_and_policies'], [])
        self.assertEqual(result['branch_protection_observation']['status'], 'observed')

    def test_base_is_url_encoded_and_head_drift_stops_before_policy_reads(self):
        self.commands.view['baseRefName'] = 'release/v1'
        self.observe()
        self.assertTrue(any('/branches/release%2Fv1/protection' in cmd[2] for cmd in self.commands.commands))
        self.commands.commands.clear()
        self.commands.view['headRefOid'] = '2' * 40
        with self.assertRaisesRegex(ProviderError, 'different PR head'):
            self.observe()
        self.assertEqual(len(self.commands.commands), 1)

    def require_app(self):
        self.commands.rules = [{'type': 'required_status_checks', 'parameters': {
            'required_status_checks': [{'context': 'ci', 'integration_id': 15368}],
        }}]
        self.commands.view['statusCheckRollup'] = [{'name': 'ci', 'conclusion': 'SUCCESS'}]

    def test_app_checks_are_paginated_and_identical_requirements_share_one_read(self):
        self.require_app()
        self.commands.protection = protection('ci')
        self.commands.protection['required_status_checks']['checks'][0]['app_id'] = 15368
        self.commands.check_pages[15368] = [
            {'total_count': 2, 'check_runs': [check_run(name='prepare')]},
            {'total_count': 2, 'check_runs': [check_run(run_id=102)]},
        ]
        result = self.observe()
        self.assertEqual([item['bucket'] for item in result['checks_and_policies']], ['pass', 'pass'])
        self.assertEqual(len([cmd for cmd in self.commands.commands if '/check-runs?' in cmd[2]]), 1)

    def test_app_queries_preserve_the_existing_gh_235_contract(self):
        self.require_app()
        self.commands.gh_235 = True
        self.commands.check_pages[15368] = [
            {'total_count': 2, 'check_runs': [check_run(name='prepare')]},
            {'total_count': 2, 'check_runs': [check_run(run_id=102)]},
        ]
        result = self.observe()
        self.assertEqual([item['bucket'] for item in result['checks_and_policies']], ['pass', 'pass'])

    def test_app_readback_rejects_foreign_or_malformed_evidence(self):
        self.require_app()
        normal = check_run()
        bad_runs = [dict(normal, head_sha='2' * 40), dict(normal, app={'id': 999}),
                    dict(normal, app=None), dict(normal, app={'id': True}),
                    dict(normal, id=True), dict(normal, id=0), dict(normal, name=None),
                    dict(normal, status='in_progress'), dict(normal, conclusion=None),
                    dict(normal, status='invented'), dict(normal, status=[]), dict(normal, status={})]
        for bad in bad_runs:
            with self.subTest(run=bad):
                self.commands.check_pages[15368] = [{'total_count': 1, 'check_runs': [bad]}]
                with self.assertRaises(ProviderError):
                    self.observe()

    def test_incomplete_duplicate_or_failed_app_pagination_cannot_pass(self):
        self.require_app()
        page = {'total_count': 1, 'check_runs': [check_run()]}
        for pages in [[], {}, [{'total_count': True, 'check_runs': []}],
                      [{'total_count': 2, 'check_runs': [check_run()]}], [page, copy.deepcopy(page)],
                      [page, {'total_count': 2, 'check_runs': []}],
                      [{'total_count': 0, 'check_runs': 'malformed'}],
                      CommandResult(json.dumps(page) + '\n{', '', 0),
                      CommandResult('', 'permission denied', 1)]:
            with self.subTest(pages=pages):
                self.commands.check_pages[15368] = pages
                with self.assertRaises(ProviderError):
                    self.observe()

    def test_ruleset_schema_or_app_identity_errors_cannot_drop_a_requirement(self):
        for parameters in [None, [], {}, {'required_status_checks': None},
                           {'required_status_checks': [{'context': 'ci', 'integration_id': False}]},
                           {'required_status_checks': [{'context': 'ci', 'integration_id': -2}]}]:
            with self.subTest(parameters=parameters):
                self.commands.rules = [{'type': 'required_status_checks', 'parameters': parameters}]
                with self.assertRaises(ProviderError):
                    self.observe()


if __name__ == '__main__':
    unittest.main()
