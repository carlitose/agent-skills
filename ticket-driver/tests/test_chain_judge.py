"""Real owned RPC/bridge/parser with synthetic completion, never a live SDK/provider."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'ticket-driver/scripts'), str(ROOT / 'ticket-autopilot/scripts')]
from chain_controller import DecisionEngine, ChainGate, digest
from chain_judge import ChainJudge
from chain_session import ChainSession, SessionFailure

Q = {'type': 'noul', 'instructions': 'Is evidence sufficient?',
     'criteria': {'true': 'covered', 'false': 'missing'}}
CFG = {'noul_low': .2, 'noul_high': .8, 'choice_min_confidence': .75, 'risk_score_high': 2.5, 'max_attempts': 3}
CF = {'contract_version': 2, 'base_tree_oid': 'a'*40, 'candidate_tree_oid': 'b'*40, 'ticket_digest': 'c'*64}
MODEL = {'provider': 'fixture', 'id': 'exact'}


class JudgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='spc03-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def owner(self):
        owner = ChainSession(['node', str(Path(__file__).with_name('fake_chain_judge.mjs')), '--mode', 'rpc'],
            cwd=self.root, store=self.root/'store', timeout=5)
        self.addCleanup(owner.close)
        return owner

    def port(self, owner, **options):
        return ChainJudge(owner, CFG, model=MODEL, grant=options.get('grant', lambda b:
            {'authorized': True, 'budget_calls': 1, 'max_tokens': 128}))

    def request(self, state, ident='q', question=Q):
        return {'binding': {'call_id': digest({'candidate': CF, 'question_id': ident}),
            'candidate_ref': CF, 'question_id': ident, 'question_digest': digest(question),
            'state_digest': digest(state), 'contract_digest': digest(CFG)},
            'question_id': ident, 'question': question, 'state': state}

    def engine(self, port, name='decision', **options):
        return DecisionEngine(self.root/(name+'.json'), CFG, permits=lambda k,b: True, budget=10,
            judge=port, **options)

    def test_handled_native_receipt_and_ordinal_events_not_builder_text(self):
        owner = self.owner()
        port = self.port(owner)
        request = self.request({'evidence': 'Unicode é\u2028b\u2029c\tcontrol', 'number': 1.0})
        # Native byte framing and canonical Python bytes survive control/Unicode JSON.
        result = port(request)
        self.assertEqual(result['text'], 'Answer: yes')
        self.assertEqual(result['usage']['totalTokens'], 5)
        self.assertEqual(owner.launches, 1)
        self.assertEqual(len(owner.journal['judge_receipts']), 1)
        self.assertEqual(len(owner.journal['charges']), 1)
        self.assertEqual(json.loads(owner.journal_path.read_text(encoding='utf-8'))['cursor'], '2')
        owner.sync()
        self.assertEqual(len(owner.journal['charges']), 1)
        with self.assertRaises(SessionFailure):
            port(request)
        self.assertEqual(owner.launches, 1)

    def test_controller_parser_reuses_decision_not_completion(self):
        owner = self.owner()
        engine = self.engine(self.port(owner))
        first = engine.decide('q', Q, {'evidence': 1.0}, CF)
        self.assertEqual(first['outcome'], 'yes')
        self.assertEqual(engine.decide('q', Q, {'evidence': 1.0}, CF), first)
        self.assertEqual(len(engine.state['calls']), 1)
        self.assertEqual(engine.state['calls'][0]['usage']['totalTokens'], 5)
        self.assertEqual(len(owner.journal['charges']), 1)

    def test_stop_tool_malformed_and_exception_do_not_decide_and_usage_retained(self):
        owner = self.owner()
        engine = self.engine(self.port(owner))
        states = [{'stop': 'length'}, {'stop': 'error'}, {'stop': 'aborted'}, {'tool': True},
                  {'answer': 'Answer: yes\nAnswer: yes'}, {'answer': 'Answer: yes\nMore text'}, {'exception': True}]
        for i,state in enumerate(states):
            self.assertEqual(engine.decide(str(i), Q, state, CF)['outcome'], 'uncertain')
        for row in engine.state['calls'][:-1]:
            self.assertEqual(row['usage']['totalTokens'], 5)
        self.assertIsNone(engine.state['calls'][-1]['usage'])
        self.assertNotIn('FIXTURE SECRET', owner.journal_path.read_text(encoding='utf-8'))
        self.assertEqual(len(owner.journal['charges']), len(states))

    def test_choice_and_absent_usage_retain_canonical_parser_and_unknown(self):
        owner = self.owner()
        engine = self.engine(self.port(owner))
        choice = {'type': 'choice', 'instructions': 'Choose', 'criteria': {'a': 'first', 'b': 'second'}}
        result = engine.decide('choice', choice, {'answer': 'Answer: b', 'no_usage': True}, CF)
        self.assertEqual(result['outcome'], 'b')
        self.assertIsNone(engine.state['calls'][0]['usage'])
        self.assertIsNone(next(iter(owner.journal['charges'].values()))['usage'])

    def test_negative_jev_never_invokes_native_judge(self):
        owner = self.owner()
        engine = self.engine(self.port(owner), jev=lambda req:
            {'answers': {'q': {'type': 'noul', 'noul': 0}}})
        self.assertEqual(engine.decide('q', Q, {}, CF)['outcome'], 'no')
        self.assertFalse(owner.journal.get('judge_receipts'))

    def test_forbidden_budget_binding_fail_before_command(self):
        class NoPrompt:
            def prompt(self, value):
                raise AssertionError('no effect permitted')
        request = self.request({})
        for authority in [{'authorized': False, 'budget_calls': 1, 'max_tokens': 128},
                          {'authorized': True, 'budget_calls': 0, 'max_tokens': 128}]:
            with self.assertRaises(ChainGate):
                self.port(NoPrompt(), grant=lambda b: authority)(request)
        request['state'] = {'changed': True}
        with self.assertRaises(ChainGate):
            self.port(NoPrompt())(request)

    def test_wrong_handled_or_receipt_binding_is_not_approval(self):
        class WrongPeer:
            def __init__(self, disposition):
                self.disposition = disposition
            def prompt(self, message):
                payload = json.loads(message.split(' ', 1)[1])
                return {'disposition': self.disposition, 'entries': [{'type': 'custom', 'id': '1',
                    'customType': 'chain-judge-result', 'data': {**payload['binding'],
                    'model': MODEL, 'request_digest': 'wrong', 'text': 'Answer: yes',
                    'stopReason': 'stop', 'valid': True}}]}
        for disposition in ['started', 'handled']:
            with self.assertRaises(ChainGate):
                self.port(WrongPeer(disposition))(self.request({}))

    def test_nested_usage_deduplicates_only_observed_native_identity(self):
        owner = self.owner()
        native = {'type': 'usage', 'id': 'native', 'kind': 'nested', 'usage': {'totalTokens': 5}}
        custom = {'type': 'custom', 'id': 'custom', 'customType': 'chain-judge-result',
                  'data': {'call_id': 'x', 'model': MODEL, 'usage': {'totalTokens': 5}, 'native_usage_ids': ['native']}}
        owner.observe([custom, native])
        self.assertEqual(list(owner.journal['charges']), ['native'])
        self.assertEqual(owner.journal['judge_receipts']['x']['data']['usage']['totalTokens'], 5)
        owner.observe([custom, native])
        self.assertEqual(len(owner.journal['charges']), 1)
        with self.assertRaises(SessionFailure):
            owner.observe([{**custom, 'id': 'duplicate'}])

    def test_two_call_ids_cannot_share_one_native_charge(self):
        owner = self.owner()
        native = {'type': 'usage', 'id': 'native', 'usage': {'totalTokens': 5}}
        first = {'type': 'custom', 'id': 'one', 'customType': 'chain-judge-result',
            'data': {'call_id': 'x', 'model': MODEL, 'usage': {'totalTokens': 5}, 'native_usage_ids': ['native']}}
        second = {**first, 'id': 'two', 'data': {**first['data'], 'call_id': 'y'}}
        owner.observe([native, first])
        with self.assertRaises(SessionFailure):
            owner.observe([second])
        self.assertEqual(owner.journal['charges']['two']['usage']['totalTokens'], 5)

    def test_missing_or_mismatched_native_link_never_silently_discards_usage(self):
        owner = self.owner()
        custom = {'type': 'custom', 'id': 'custom', 'customType': 'chain-judge-result',
            'data': {'call_id': 'x', 'model': MODEL, 'usage': {'totalTokens': 5}, 'native_usage_ids': ['missing']}}
        with self.assertRaises(SessionFailure):
            owner.observe([custom])
        self.assertEqual(owner.journal['charges']['custom']['usage']['totalTokens'], 5)


if __name__ == '__main__':
    unittest.main()
