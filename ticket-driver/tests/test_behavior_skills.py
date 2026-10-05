"""New variant contract tests: actual Git/processes, substituted AI ports."""
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import test_chain_controller as fixtures
sys.path.insert(0, str(fixtures.ROOT / 'benchmarks/delivery-bench'))
from behavior_skills import BehaviorController, BehaviorCell, SkillBudgetedSession, declared_checks
from chain_controller import ChainGate


class BehaviorTests(fixtures.ControllerTests):
    def setUp(self):
        super().setUp()
        (self.home / 'facts').rename(self.home / 'old-facts')
        self.owner = BehaviorController(self.original, self.copy, self.home / 'facts', self.peer,
                                        self.decision, coverage_question=fixtures.Q)
        self.messages = []
        prompt = self.peer.prompt
        def observe(message):
            self.messages.append(json.loads(message))
            return prompt(message)
        self.peer.prompt = observe

    def test_full_contract_and_required_profile_reach_review_and_fix(self):
        self.decision.jev = lambda r: {'answers': {r['question_id']: {'type': 'noul', 'noul': 0}}, 'usage': {}}
        row = self.run_ticket()
        self.assertEqual((row['status'], row['failures']), ('failed', 3))
        for m in self.messages:
            self.assertEqual(m['ticket']['body'], row['ticket']['body'])
            self.assertEqual(m['required_public_commands'], [self.test])
        fix = next(m for m in self.messages if m['role'] == 'fix')
        self.assertEqual(fix['prior_coverage_decision']['outcome'], 'no')

    def test_owned_profile_drift_gates_even_on_completed_reentry(self):
        self.run_ticket()
        with self.assertRaises(ChainGate):
            self.owner.run_ticket(self.ticket(), ['value.py'], [['echo', 'not the profile']])

    def test_body_drift_does_not_mutate_cumulative_profile(self):
        self.run_ticket()
        before = list(self.owner.state['required_commands'])
        changed = self.ticket().replace('VALUE=1.', 'VALUE=1. python dev.py lint')
        with self.assertRaises(ChainGate):
            self.owner.run_ticket(changed, ['value.py'], [self.test])
        self.assertEqual(self.owner.state['required_commands'], before)

    def test_missing_dependencies_do_not_admit_new_checks(self):
        ticket = self.ticket('B', ['A']).replace('VALUE=1.', 'VALUE=1. python dev.py lint')
        row = self.owner.run_ticket(ticket, ['value.py'], [self.test])
        self.assertEqual(row['status'], 'dependency-blocked')
        self.assertEqual(self.owner.state['required_commands'], [])

    def test_cumulative_lint_executes_and_failure_cannot_be_approved(self):
        # Public fixture's executable is deliberately failing lint; stock test still passes.
        (self.copy / 'dev.py').write_bytes(b'import sys\nprint("lint failure")\nsys.exit(1 if sys.argv[-1] == "lint" else 0)\n')
        # This is an admitted fixture addition before first turn, not unexplained external drift.
        self.owner.state['expected'] = self.owner._fingerprint()
        from chain_controller import _save
        _save(self.owner.path, self.owner.state)
        body = self.ticket().replace('VALUE=1.', 'VALUE=1. `python dev.py lint` must pass.')
        row = self.owner.run_ticket(body, ['value.py', 'dev.py'], [self.test])
        self.assertEqual((row['status'], row['failures']), ('failed', 3))
        self.assertEqual([r['exit_code'] for r in row['receipts']], [0, 1])
        self.assertEqual(row['coverage_feedback']['outcome'], 'uncertain')
        resumed = BehaviorController(self.original, self.copy, self.home / 'facts', self.peer,
                                      self.decision, coverage_question=fixtures.Q)
        self.assertEqual(resumed.state['required_commands'][-1], [self.test[0], 'dev.py', 'lint'])

    def test_failed_previews_keep_diagnostic_tail_and_complete_source(self):
        row = self.run_ticket();receipt=row['receipts'][0]
        record={**receipt,'exit_code':1,'stderr':'x'*20000+'LAST_DIAGNOSTIC'}
        output=self.owner._test_observations([record])['receipts'][0]
        self.assertLessEqual(len(output['stderr'].encode()), 2048)
        self.assertTrue(output['stderr'].endswith('LAST_DIAGNOSTIC'))
        self.assertTrue(output['stderr_truncated'])
        self.assertEqual(record['stderr'], 'x'*20000+'LAST_DIAGNOSTIC')
        self.assertTrue(Path(output['path']).is_file())
        unicode_record={**record,'stderr':'☃'*2000+'LAST'}
        unicode_output=self.owner._test_observations([unicode_record])['receipts'][0]
        self.assertLessEqual(len(unicode_output['stderr'].encode()), 2048)
        self.assertTrue(unicode_output['stderr'].endswith('LAST'))

    def test_legacy_checkpoint_is_not_silently_reused(self):
        with self.assertRaises(ChainGate):
            BehaviorController(self.original, self.copy, self.home / 'old-facts', self.peer,
                               self.decision, coverage_question=fixtures.Q)


class SkillPortTests(unittest.TestCase):
    def test_explicit_skill_prefix_and_same_budget_settlement(self):
        class Native:
            def __init__(self): self.messages=[]
            def prompt(self, text): self.messages.append(text);return {'text':'fixture'}
        class Account:
            state={'charges':{}}
            def __init__(self):self.reserves=[];self.settles=[]
            def reserve(self, kind, upper):self.reserves.append((kind,upper));return len(self.reserves)
            def settle(self, ident, costs):self.settles.append((ident,costs))
        native=Native();account=Account();port=SkillBudgetedSession(native,account)
        with patch('behavior_skills.native_costs',return_value=[]):
            port.prompt(json.dumps({'role':'builder'}));port.prompt(json.dumps({'role':'review'}));port.prompt(json.dumps({'role':'fix'}))
        self.assertTrue(native.messages[0].startswith('/skill:behavior-first '))
        self.assertFalse(native.messages[1].startswith('/skill:'))
        self.assertTrue(native.messages[2].startswith('/skill:behavior-first '))
        self.assertEqual(account.reserves,[('pi',25)]*3)
        self.assertEqual([i for i,cost in account.settles],[1,2,3])
        with self.assertRaises(ChainGate):port.prompt(json.dumps({'role':'unknown'}))

    def test_only_public_literal_conventions_extend_owned_profile(self):
        commands=[['python','dev.py','test']]
        self.assertEqual(declared_checks('`python dev.py lint` and `python dev.py c89`',commands),
                         commands+[['python','dev.py','lint'],['python','dev.py','c89']])
        self.assertEqual(commands,[['python','dev.py','test']])
        self.assertEqual(declared_checks('mypy; shell arbitrary',commands),commands)
        with self.assertRaises(ChainGate):declared_checks('python dev.py lint',[])
