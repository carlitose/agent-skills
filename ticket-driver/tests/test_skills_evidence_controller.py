"""Real Git/test processes; substituted AI ports. Historical gates inherited as contract tests."""
import hashlib
import json
from pathlib import Path
import sys

import test_chain_controller as fixtures
from chain_controller import ChainGate, _save
from skills_evidence_controller import SkillsEvidenceController

sys.path.insert(0, str(fixtures.ROOT / 'benchmarks/delivery-bench'))
from skills_evidence_arm import SkillsEvidenceCell


class SkillsEvidenceTests(fixtures.ControllerTests):
    def setUp(self):
        super().setUp()
        (self.home / 'facts').rename(self.home / 'historical-facts')
        self.owner = SkillsEvidenceController(
            self.original, self.copy, self.home / 'facts', self.peer,
            self.decision, coverage_question=fixtures.Q)
        self.messages = []
        prompt = self.peer.prompt
        def observe(message):
            self.messages.append(json.loads(message))
            return prompt(message)
        self.peer.prompt = observe

    def test_review_has_exact_public_ticket_without_repeated_body(self):
        row = self.run_ticket()
        self.assertEqual(row['status'], 'completed-local')
        builder, review = self.messages
        self.assertEqual(builder['ticket']['body'], row['ticket']['body'])
        self.assertNotIn('body', review['ticket'])
        artifact = review['public_ticket_artifact']
        raw = Path(artifact['path']).read_bytes()
        self.assertEqual(raw, self.ticket().encode())
        self.assertEqual(hashlib.sha256(raw).hexdigest(), artifact['sha256'])
        self.assertEqual(artifact['sha256'], row['candidate']['ticket_digest'])
        self.assertIn('requested new behavior', builder['implementation_lane'])

    def test_green_output_compact_but_full_receipt_preserved(self):
        row = self.run_ticket()
        receipt = row['receipts'][0]
        large = {**receipt, 'stdout': 'x' * 20000, 'stderr': 'y' * 20000}
        observed = self.owner._test_observations([large])
        self.assertNotIn('stdout', observed['receipts'][0])
        self.assertEqual(observed['receipts'][0]['sha256'], receipt['sha256'])
        self.assertEqual(hashlib.sha256(Path(receipt['path']).read_bytes()).hexdigest(), receipt['sha256'])
        self.assertLess(len(json.dumps(observed).encode()), 2048)
        self.assertEqual(large['stdout'], 'x' * 20000)
        failed = {**large, 'exit_code': 1, 'stderr': 'x' * 30000 + 'REQUIRED_DIAGNOSTIC'}
        preview = self.owner._test_observations([failed])
        self.assertTrue(preview['receipts'][0]['stderr'].endswith('REQUIRED_DIAGNOSTIC'))
        self.assertTrue(preview['receipts'][0]['stderr_truncated'])
        self.assertLessEqual(len(json.dumps(preview).encode()), 32768)

    def test_fix_receives_negative_coverage_without_invented_diagnosis(self):
        self.decision.jev = lambda request: {
            'answers': {request['question_id']: {'type': 'noul', 'noul': 0}}, 'usage': {}}
        row = self.run_ticket()
        self.assertEqual((row['status'], row['failures']), ('failed', 3))
        fix = next(m for m in self.messages if m['role'] == 'fix')
        feedback = fix['prior_coverage_decision']
        self.assertEqual(feedback['outcome'], 'no')
        self.assertEqual(feedback['reason'], 'jev observed')
        self.assertEqual(feedback['binding']['candidate_ref'], row['candidate'])
        self.assertNotIn('body', fix['ticket'])
        self.assertNotIn('missing_criteria', feedback)

    def test_public_failure_remains_failure_and_gets_uncertain_feedback(self):
        self.peer.bad = True
        row = self.run_ticket()
        self.assertEqual((row['status'], row['failures']), ('failed', 3))
        fix = next(m for m in self.messages if m['role'] == 'fix')
        self.assertEqual(fix['prior_coverage_decision']['outcome'], 'uncertain')
        self.assertEqual(row['receipts'][0]['exit_code'], 1)
        self.assertTrue(fix['test_observations']['receipts'][0]['stderr'])

    def test_artifact_tamper_missing_and_protocol_reentry_fail_closed(self):
        self.run_ticket()
        artifact = next(iter(self.owner.state['public_tickets'].values()))
        path = Path(artifact['path'])
        raw = path.read_bytes()
        path.write_bytes(b'changed')
        with self.assertRaises(ChainGate):
            SkillsEvidenceController(self.original, self.copy, self.home / 'facts',
                                     self.peer, self.decision, coverage_question=fixtures.Q)
        path.write_bytes(raw)
        resumed = SkillsEvidenceController(self.original, self.copy, self.home / 'facts',
                                           self.peer, self.decision, coverage_question=fixtures.Q)
        self.assertEqual(resumed.run_ticket(self.ticket(), ['value.py'], [self.test])['status'], 'completed-local')
        path.unlink()
        with self.assertRaises(ChainGate):
            resumed.run_ticket(self.ticket('B'), ['value.py'], [self.test])
        with self.assertRaises(ChainGate):
            SkillsEvidenceController(self.original, self.copy, self.home / 'historical-facts',
                                     self.peer, self.decision, coverage_question=fixtures.Q)

    def test_model_mutating_public_ticket_artifact_is_detected(self):
        old = self.peer.prompt
        def mutate(message):
            value = json.loads(message)
            reply = old(message)
            if value['role'] == 'review':
                Path(value['public_ticket_artifact']['path']).write_bytes(b'changed')
            return reply
        self.peer.prompt = mutate
        with self.assertRaises(ChainGate):
            self.run_ticket()

    def test_cell_adapter_uses_same_session_and_accounting_port(self):
        class Account:
            def __init__(self):
                self.reserved = []
                self.settled = []
                self.state = {'charges': {}}
            def reserve(self, kind, usd):
                self.reserved.append((kind, usd))
                return len(self.reserved)
            def settle(self, ident, costs):
                self.settled.append(ident)
        # Only compose the adapter; native usage settlement is the unchanged owner's contract.
        account = Account()
        cell = SkillsEvidenceCell(self.original, self.copy, self.home / 'adapter-facts',
                                  self.peer, self.decision, account, coverage_question=fixtures.Q)
        self.assertIsInstance(cell.owner, SkillsEvidenceController)
        self.assertIs(cell.owner.session.session, self.peer)
        self.assertIs(cell.owner.session.budget, account)
        self.assertEqual(cell.owner.identity, self.owner.identity)

    def test_metadata_bound_never_drops_receipts_to_fit(self):
        row = self.run_ticket()
        receipt = {**row['receipts'][0], 'argv': ['x' * 33000]}
        with self.assertRaises(ChainGate):
            self.owner._test_observations([receipt])
