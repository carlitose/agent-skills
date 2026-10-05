"""Controller causal tests: Git and test processes real, Pi/Jev/judge substituted."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'ticket-driver/scripts'), str(ROOT / 'ticket-autopilot/scripts')]
from autopilot.ticket_contract import serialize_ticket_markdown
from chain_controller import ChainController, DecisionEngine, ChainGate

Q = {'type': 'noul', 'instructions': 'Does the observed evidence cover all acceptance criteria?',
     'criteria': {'true': 'all covered', 'false': 'at least one missing'}}
CFG = {'noul_low': .2, 'noul_high': .8, 'choice_min_confidence': .75, 'risk_score_high': 2.5,
       'max_attempts': 3}


class Peer:
    pid = 100
    session_id = 'fake-shared'
    def __init__(self, root):
        self.root, self.calls, self.bad, self.mutate_review = root, [], False, False
    def prompt(self, message):
        value = json.loads(message)
        self.calls.append(value['role'])
        if value['role'] in ('builder', 'fix'):
            (self.root / 'value.py').write_bytes(b'VALUE = 0\n' if self.bad else b'VALUE = 1\n')
        if value['role'] == 'review' and self.mutate_review:
            (self.root / 'value.py').write_bytes(b'VALUE = 9\n')
        text = 'No findings.' if value['role'] == 'review' else 'Written'
        return {'text': text, 'pid': self.pid, 'session_id': 'fake-shared', 'entry_ids': []}


class ControllerTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='spc02-')
        self.addCleanup(temp.cleanup)
        self.home = Path(temp.name)
        self.original, self.copy = self.home / 'original', self.home / 'copy'
        self.original.mkdir()
        self.git(self.original, 'init', '-q')
        self.git(self.original, 'config', 'core.autocrlf', 'false')
        self.git(self.original, 'config', 'user.name', 'fixture')
        self.git(self.original, 'config', 'user.email', 'fixture@local')
        (self.original / 'value.py').write_bytes(b'VALUE = 0\n')
        self.git(self.original, 'add', '.')
        self.git(self.original, 'commit', '-qm', 'fixture')
        self.git(self.home, '-c', 'core.autocrlf=false', '-c', 'core.eol=lf',
                 'clone', '-q', '--no-hardlinks', str(self.original), str(self.copy))
        self.git(self.copy, 'config', 'core.autocrlf', 'false')
        self.peer = Peer(self.copy)
        self.decision = DecisionEngine(self.home / 'decisions.json', CFG,
            permits=lambda kind, binding: True, budget=100,
            jev=lambda request: {'answers': {request['question_id']: {'type': 'noul', 'noul': 1}},
                                 'usage': {'input_tokens': 1, 'output_tokens': 1}}, judge=None)
        self.owner = ChainController(self.original, self.copy, self.home / 'facts', self.peer,
                                     self.decision, coverage_question=Q)
        self.test = [sys.executable, '-B', '-c', 'from value import VALUE; assert VALUE == 1']

    def git(self, cwd, *args):
        return subprocess.check_output(['git', *args], cwd=cwd).decode().strip()

    def ticket(self, ident='A', deps=()):
        return serialize_ticket_markdown({'ticket_schema': 1, 'ticket_id': ident,
            'execution_mode': 'AFK', 'blocked_by': list(deps)}, '# Local fixture\n\nImplement VALUE=1.\n')

    def run_ticket(self, ident='A', deps=()):
        return self.owner.run_ticket(self.ticket(ident, deps), ['value.py'], [self.test])

    def test_explicit_owned_directory_scope_allows_new_product_files(self):
        original_prompt = self.peer.prompt
        def prompt(message):
            result = original_prompt(message)
            if json.loads(message)['role'] == 'builder':
                (self.copy / 'added').mkdir(exist_ok=True)
                (self.copy / 'added/new.py').write_bytes(b'NEW = 1\n')
            return result
        self.peer.prompt = prompt
        row = self.owner.run_ticket(self.ticket(), ['.'], [self.test])
        self.assertEqual(row['status'], 'completed-local')
        self.assertIn('added/new.py', self.git(self.copy, 'ls-tree', '-r', '--name-only', row['candidate']['candidate_tree_oid']))
        self.assertFalse((self.original / 'added').exists())

    def test_file_scope_is_not_widened_by_directory_support(self):
        original_prompt = self.peer.prompt
        def prompt(message):
            result = original_prompt(message)
            if json.loads(message)['role'] == 'builder':
                (self.copy / 'other.py').write_bytes(b'OTHER = 1\n')
            return result
        self.peer.prompt = prompt
        with self.assertRaises(ChainGate):
            self.owner.run_ticket(self.ticket(), ['value.py'], [self.test])
        self.assertEqual((self.copy / 'other.py').read_bytes(), b'OTHER = 1\n')

    def test_coverage_is_bound_to_literal_frozen_product_diff(self):
        observed = []
        original_jev = self.decision.jev
        def jev(request):
            observed.append(request)
            return original_jev(request)
        self.decision.jev = jev
        row = self.run_ticket()
        request = next(r for r in observed if r['question_id'] == 'coverage')
        cf = row['candidate']
        expected = self.git(self.copy, 'diff', '--no-ext-diff', '--no-color',
                            cf['base_tree_oid'], cf['candidate_tree_oid'])
        self.assertEqual(request['state']['diff'].strip(), expected)
        self.assertIn('+VALUE = 1', request['state']['diff'])

    def test_two_tickets_real_trees_and_receipts_original_unchanged(self):
        first = self.run_ticket()
        second = self.run_ticket('B', ['A'])
        self.assertEqual((first['status'], second['status']), ('completed-local', 'completed-local'))
        self.assertEqual(first['candidate']['contract_version'], 2)
        self.assertTrue(Path(first['receipts'][0]['path']).exists())
        self.assertEqual((self.original / 'value.py').read_bytes(), b'VALUE = 0\n')
        self.assertEqual(self.peer.calls.count('builder'), 2)
        self.assertNotIn('commit', self.peer.calls)

    def test_final_failures_three_and_reentry_do_not_reset(self):
        self.peer.bad = True
        result = self.run_ticket()
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['failures'], 3)
        self.assertEqual(self.run_ticket()['failures'], 3)
        self.assertEqual(self.peer.calls.count('fix'), 2)
        self.assertTrue(result['archive'])
        self.assertEqual(self.run_ticket('B', ['A'])['status'], 'dependency-blocked')
        self.peer.bad = False
        self.assertEqual(self.run_ticket('C')['status'], 'completed-local')
        self.assertEqual((self.original / 'value.py').read_bytes(), b'VALUE = 0\n')

    def test_review_mutation_and_external_drift_preserved(self):
        self.peer.mutate_review = True
        with self.assertRaises(ChainGate):
            self.run_ticket()
        self.assertEqual((self.copy / 'value.py').read_bytes(), b'VALUE = 9\n')
        with self.assertRaises(ChainGate):
            self.run_ticket('other')

    def test_green_test_is_not_coverage_and_incomplete_review_not_clean(self):
        self.decision.jev = lambda request: {'answers': {request['question_id']: {'type': 'noul', 'noul': 0}}, 'usage': {}}
        self.assertEqual(self.run_ticket()['status'], 'failed')
        self.assertEqual(self.owner.state['tickets']['A']['failures'], 3)

    def test_checkpoint_tamper_and_global_budget_block(self):
        self.owner.path.write_bytes(b'{}\n')
        with self.assertRaises(ChainGate):
            self.run_ticket()

    def test_decision_negative_no_judge_and_one_uncertain_attempt(self):
        cf = {'contract_version': 2, 'base_tree_oid': 'a'*40, 'candidate_tree_oid': 'b'*40, 'ticket_digest': 'c'*64}
        calls = []
        self.decision.judge = lambda request: calls.append(request) or {**request['binding'], 'text': 'Answer: yes', 'stopReason': 'stop', 'usage': {}}
        self.decision.jev = lambda request: {'answers': {'q': {'type': 'noul', 'noul': 0}}, 'usage': {}}
        self.assertEqual(self.decision.decide('q', Q, {}, cf)['outcome'], 'no')
        self.assertEqual(calls, [])
        self.decision.jev = lambda request: {'answers': {'u': {'type': 'noul', 'noul': .5}}, 'usage': {}}
        self.assertEqual(self.decision.decide('u', Q, {}, cf)['outcome'], 'yes')
        self.assertEqual(self.decision.decide('u', Q, {}, cf)['outcome'], 'yes')
        self.assertEqual(len(calls), 1)

    def test_http_retry_only_429_529_and_binding_mismatch(self):
        cf = {'contract_version': 2, 'base_tree_oid': 'a'*40, 'candidate_tree_oid': 'b'*40, 'ticket_digest': 'c'*64}
        statuses = iter([429, 529, 200])
        self.decision.jev = lambda request: {'http_status': next(statuses), 'answers': {'q': {'type': 'noul', 'noul': 1}}, 'usage': {}}
        self.assertEqual(self.decision.decide('q', Q, {}, cf)['outcome'], 'yes')
        self.assertEqual(len(self.decision.state['calls']), 3)
        self.decision.jev = lambda request: {'http_status': 500, 'usage': {}}
        self.decision.judge = lambda request: {'text': 'Answer: yes', 'stopReason': 'stop', 'usage': {}}
        self.assertEqual(self.decision.decide('x', Q, {}, cf)['outcome'], 'uncertain')
        self.assertEqual(len(self.decision.state['calls']), 5)

    def test_incomplete_review_global_budget_and_session_drift_gate(self):
        original = self.peer.prompt
        def incomplete(message):
            reply = original(message)
            if json.loads(message)['role'] == 'review':
                reply['text'] = 'Looks okay'
            return reply
        self.peer.prompt = incomplete
        row = self.run_ticket()
        self.assertEqual((row['status'], row['failures']), ('human-gated', 0))
        self.assertEqual(row['failure_kind'], 'review-format')
        self.peer.pid = 999
        with self.assertRaises(ChainGate):
            self.run_ticket('other')
        cf = {'contract_version': 2, 'base_tree_oid': 'a'*40, 'candidate_tree_oid': 'b'*40, 'ticket_digest': 'c'*64}
        self.decision.state['budget'] = 0
        from chain_controller import _save
        _save(self.decision.path, self.decision.state)
        with self.assertRaises(ChainGate):
            self.decision.decide('budget', Q, {}, cf)

    def test_checkpoint_reentry_and_risk_uncertainty_does_not_judge(self):
        self.run_ticket()
        reloaded = ChainController(self.original, self.copy, self.home / 'facts', self.peer,
                                   self.decision, coverage_question=Q)
        self.assertEqual(reloaded.run_ticket(self.ticket(), ['value.py'], [self.test])['status'], 'completed-local')
        cf = {'contract_version': 2, 'base_tree_oid': 'a'*40, 'candidate_tree_oid': 'b'*40, 'ticket_digest': 'c'*64}
        calls = []
        self.decision.jev = lambda request: {'http_status': 429, 'usage': {}}
        self.decision.judge = lambda request: calls.append(request)
        self.decision.sleep = lambda delay: None
        start = len(self.decision.state['calls'])
        self.assertEqual(self.decision.decide('risk', Q, {}, cf, risk=True)['outcome'], 'uncertain')
        self.assertEqual(len(self.decision.state['calls']) - start, 3)
        self.assertEqual(calls, [])
        self.owner.state['inflight'] = {'role': 'builder'}
        from chain_controller import _save
        _save(self.owner.path, self.owner.state)
        with self.assertRaises(ChainGate):
            self.owner.run_ticket(self.ticket('crash'), ['value.py'], [self.test])

    def test_insufficient_or_forbidden_data_never_calls_judge(self):
        cf = {'contract_version': 2, 'base_tree_oid': 'a'*40, 'candidate_tree_oid': 'b'*40, 'ticket_digest': 'c'*64}
        self.decision.permits = lambda kind, binding: False
        self.assertEqual(self.decision.decide('q', Q, {}, cf)['outcome'], 'uncertain')
        self.assertEqual(self.decision.state['calls'], [])
        self.decision.permits = lambda kind, binding: True
        self.assertEqual(self.decision.decide('x', Q, {}, cf, sufficient=False)['outcome'], 'uncertain')
        self.assertEqual(self.decision.state['calls'], [])


if __name__ == '__main__':
    unittest.main()
