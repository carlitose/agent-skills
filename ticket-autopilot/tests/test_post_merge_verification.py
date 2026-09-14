from __future__ import annotations

import copy
import hashlib
import io
import json
from contextlib import redirect_stdout
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))

from autopilot import post_merge_verification as pmv
from autopilot.cli import main as cli_main
from autopilot.verification_checkpoint import load_verification_adapters
from autopilot.kernel import CandidateRef, Kernel, TransitionError
from autopilot.ledger import AtomicLedger, LedgerError
from autopilot.ticket_source import inspect_ticket_source, persist_ticket_snapshot
from autopilot.leaf_protocol import LEAF_PHASE_CONTRACTS

if __package__:
    from .test_kernel import ticket_text, record_review_handoff, _terminal_proof
    from .git_test_support import GitIsolatedTestCase
else:
    from test_kernel import ticket_text, record_review_handoff, _terminal_proof
    from git_test_support import GitIsolatedTestCase


class PostMergeVerificationTests(GitIsolatedTestCase):
    def setUp(self):
        super().setUp()
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.repo = Path(temporary.name).resolve()
        self.git('init', '-b', 'main')
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        folder = self.repo / 'docs/tickets/test'
        folder.mkdir(parents=True)
        for ident, blockers, mode in [('01', (), 'AFK'), ('02', ('01',), 'HITL'), ('03', ('01',), 'AFK')]:
            text = ticket_text(ident, blockers, mode) + '\n## Acceptance Criteria\n- [ ] The fixture source is verified.\n'
            (folder / (ident + '.md')).write_text(text, encoding='utf-8')
        (self.repo / 'worker.py').write_text('VALUE = 1\n', encoding='utf-8')
        self.git('add', '.'); self.git('commit', '-m', 'fixture baseline')
        old_head = self.git('rev-parse', 'HEAD')
        old_tree = self.git('rev-parse', 'HEAD^{tree}')
        source = inspect_ticket_source(self.repo, folder, base_ref='HEAD')
        self.run_dir = self.repo / '.git/ticket-autopilot/runs/test'
        manifest = persist_ticket_snapshot(self.run_dir, source)
        self.kernel = Kernel.new('test', source.graph, provider='github',
            repo=str(self.repo), worktree=str(self.repo), base_sha=old_head,
            source_mode=source.source_mode, snapshot_manifest_digest=source.manifest_digest,
            snapshot_manifest_path=str(manifest), source_folder_identity=source.folder_identity)
        old = CandidateRef(old_tree, old_tree, source.graph.tickets['01'].digest)
        self.kernel.activate('01', old)
        for stage in ('implement', 'simplify', 'review', 'qa-plan', 'qa-execute', 'verify', 'finalize'):
            if stage in ('review', 'qa-plan', 'qa-execute', 'verify'):
                record_review_handoff(self.kernel, '01', old, stage=stage)
            self.kernel.record_stage('01', stage, 'pass', old)
        self.kernel.record_pr('01', provider='github', pr_id='1', head_sha=old_head,
            base_branch='main', base_sha=old_head)
        # Synthetic pre-existing integration history; never an observation of a live provider.
        observation = {'schema': 1, 'provider': 'github', 'operation': 'get-pr-state',
            'evidence_class': 'live', 'observed': True, 'pr_id': '1',
            'head_sha': old_head, 'merge_commit_sha': old_head, 'state': 'merged'}
        proof = _terminal_proof(self.kernel, '01', observation, provenance='external-readback')
        proof.update(terminal_sha=old_head, terminal_tree_oid=old_tree,
            merge_commit_sha=old_head, reachable_sha=old_head)
        self.kernel.record_external_integration('01', actor='fixture', head_sha=old_head,
            evidence='fixture://preexisting-integration', provider_observation=observation,
            terminal_proof=proof)
        start = self.kernel.human_gated_ids()[0]
        self.kernel.approve_gate(start, actor='fixture-human', evidence='fixture://start-only')
        (self.repo / 'worker.py').write_text('VALUE = 2\n', encoding='utf-8')
        self.git('add', 'worker.py'); self.git('commit', '-m', 'changed merged source')
        self.gate_id = self.kernel.open_gate('02', category='post-merge-verification', scope='ticket',
            reason='Fresh source verification required', details={
                'schema': 1, 'source_head': self.git('rev-parse', 'HEAD'),
                'source_tree': self.git('rev-parse', 'HEAD^{tree}'),
                'historical_candidate_ref': old.as_dict(), 'human_canary_approval': False,
                'required_stages': ['candidate-invalidation-or-rebind', 'review', 'qa-plan', 'qa-execute', 'verify'],
            })
        self.store = AtomicLedger(self.run_dir / 'ledger.json')
        self.store.save(self.kernel.ledger)

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], stderr=subprocess.PIPE).decode('utf-8').strip()

    def bind(self):
        return pmv.bind_source(self.kernel.ledger, self.gate_id, self.repo)

    def test_real_null_candidate_dead_end_has_gate_scoped_binding(self):
        before = copy.deepcopy(self.kernel.ledger)
        with self.assertRaises(TransitionError):
            self.kernel.activate('02', CandidateRef('base', 'tree', 'digest'))
        session = self.bind()
        self.kernel.record_post_merge_session(self.gate_id, session)
        self.store.save(self.kernel.ledger)
        restored = self.store.load()
        self.assertEqual(before['tickets'], restored['tickets'])
        self.assertEqual('open', restored['gates'][self.gate_id]['state'])
        self.assertEqual('01', session['ticket_id'])
        self.assertEqual(self.git('rev-parse', 'HEAD^{tree}'), session['candidate_ref']['candidate_tree_oid'])
        self.assertEqual(['worker.py'], session['files_expected'])
        self.assertEqual('implement', pmv.session_context(restored, self.gate_id)['stage'])
        self.assertIsNone(restored['tickets']['02']['candidate_ref'])

    def test_human_approval_cannot_skip_post_merge_quality(self):
        before = copy.deepcopy(self.kernel.ledger)
        with self.assertRaisesRegex(TransitionError, 'post-merge'):
            self.kernel.approve_gate(self.gate_id, actor='human', evidence='decision://approve')
        self.assertEqual(before, self.kernel.ledger)

    def test_dirty_source_is_rejected_without_mutation(self):
        before = copy.deepcopy(self.kernel.ledger)
        (self.repo / 'worker.py').write_text('VALUE = 3\n', encoding='utf-8')
        with self.assertRaisesRegex(pmv.PostMergeVerificationError, 'clean'):
            self.bind()
        self.assertEqual(before, self.kernel.ledger)

    def test_session_binding_replay_preserves_history_and_budget(self):
        session = self.bind()
        self.kernel.record_post_merge_session(self.gate_id, session)
        before = copy.deepcopy(self.kernel.ledger)
        self.kernel.record_post_merge_session(self.gate_id, self.bind())
        self.assertEqual(before, self.kernel.ledger)

    def command(self, action, *, payload=None, expected=0):
        args = ['post-merge-verify', 'test', '--repo', str(self.repo),
                '--gate', self.gate_id, '--action', action]
        if action == 'bind':
            args += ['--source-worktree', str(self.repo)]
        if payload is not None:
            path = self.run_dir / 'request.json'
            path.write_text(json.dumps(payload), encoding='utf-8')
            args += ['--input', str(path)]
        output = io.StringIO()
        with mock.patch('autopilot.cli._provider', side_effect=AssertionError('provider forbidden')):
            with redirect_stdout(output):
                code = cli_main(args)
        result = json.loads(output.getvalue())
        self.assertEqual(expected, code, result)
        return result.get('data', result)

    def current_session(self):
        return self.store.load()['gates'][self.gate_id]['details'][pmv.SESSION_KEY]

    def leaf(self, session, stage, *, complete=True, bundle=None):
        files = session['files_expected']
        phases = list(LEAF_PHASE_CONTRACTS[stage])
        leaf = {'schema': 3, 'complete': complete, 'candidate_ref': session['candidate_ref'],
            'stage': stage, 'phase_contract': phases,
            'scope': {'files_expected': files, 'files_inspected': files if complete else [],
                      'files_remaining': [] if complete else files},
            'phases_remaining': [] if complete else phases[1:],
            'commands_run': ['fixture:read-source'], 'findings': [],
            'progress_phase': phases[-1] if complete else phases[0],
            'stop_reason': None if complete else 'interrupted',
            'execution': {'mode': 'inline', 'isolation': 'shared-context', 'parallel': False, 'authority_ref': None}}
        if stage in {'qa-plan', 'qa-execute', 'verify'}:
            evidence = self.run_dir / (stage + '.txt')
            self.assertEqual('VALUE = 2\n', (self.repo / 'worker.py').read_text(encoding='utf-8'))
            evidence.write_text('Fixture observed source VALUE = 2\n', encoding='utf-8')
            item = {'id': 'fixture:' + stage, 'artifact': str(evidence),
                'sha256': hashlib.sha256(evidence.read_bytes()).hexdigest(),
                'result': 'planned' if stage == 'qa-plan' else 'pass', 'candidate_ref': session['candidate_ref']}
            if bundle is not None:
                item.update(id='post-merge:bundle', artifact='post-merge-bundle://' + pmv.digest(bundle),
                            sha256=pmv.digest(bundle), result='pass')
            leaf['quality'] = {'schema': 1, 'causal_scope': ['source-fixture'],
                'evidence': [item], 'limitations': ['Synthetic local quality inputs, not live evidence.']}
        return leaf

    def bundle(self, session):
        ref = session['candidate_ref']
        stages = [{'id': 'stage-' + name, 'stage': name, 'result': 'pass', 'candidate_ref': ref,
            'artifact': pmv.stage_artifact(session, name), 'evidence_ids': ['unit-source'],
            'invariant_ids': ['source-only'], 'boundary_delta_ids': [], 'gate_ids': [],
            'provider_record_ids': [], 'limitations': ['post-merge isolation: shared-context']}
            for name in pmv.STAGES]
        bundle = {'contract_version': 2, 'artifact_type': 'verification-bundle',
            'ticket_id': session['ticket_id'], 'ticket_envelope_ref': session['ticket_envelope_ref'],
            'candidate_ref': ref, 'stage_results': stages,
            'evidence': [{'id': 'unit-source', 'candidate_ref': ref, 'class': 'unit',
                'environment': 'Disposable source fixture', 'environment_scope': 'local',
                'boundary_scope': 'internal', 'result': 'pass', 'critical': True,
                'supports_claim': 'deployable-for-test', 'causal_coverage': 'complete',
                'injection_point': 'fixture source', 'observed_segment': 'read fixture source',
                'artifact': str(self.run_dir / 'qa-execute.txt'), 'limitations': ['No live behavior.']}],
            'invariants': [{'id': 'source-only', 'candidate_ref': ref,
                'description': 'Only the fixture source is assessed.', 'status': 'preserved',
                'impact': 'high', 'evidence_ids': ['unit-source'], 'authorization_ref': None}],
            'external_boundary_delta': [],
            'gates': [{'id': 'canary', 'candidate_ref': ref, 'scope': 'ticket', 'kind': 'human',
                'critical': True, 'status': 'open', 'owner': 'operator',
                'required_evidence': 'Separate live canary authority'}],
            'provider_records': [],
            'claims': [{'id': item['id'], 'candidate_ref': ref, 'text': item['text'],
                'kind': 'behavior', 'criticality': 'high', 'environment_scope': 'local',
                'boundary_scope': 'internal',
                'causal_chain': [{'step': 'read fixture source', 'controller': 'codebase', 'observed': True}],
                'uncovered_segments': [], 'status': 'supported', 'requested_claim': 'deployable-for-test',
                'evidence_ids': ['unit-source'], 'gate_ids': []} for item in session['criteria']],
            'verification': {'candidate_ref': ref, 'implementation_status': 'complete',
                'max_claim': 'deployable-for-test', 'release_status': 'blocked', 'final_disposition': 'release-blocked',
                'evidence_ids': ['unit-source'], 'invariant_ids': ['source-only'], 'boundary_delta_ids': [],
                'gate_ids': ['canary'], 'provider_record_ids': [],
                'claim_ids': [item['id'] for item in session['criteria']],
                'blocking_gaps': ['Live canary is separately gated.'],
                'forbidden_claims': ['production readiness'], 'requested_operation': 'report'}}
        validate, reduce = load_verification_adapters(SCRIPTS.parents[1] / 'verification-audit', current_candidate=ref)
        bundle['verification'].update(reduce(bundle))
        validate(bundle)
        return bundle

    def advance_to_audit(self):
        self.command('bind')
        for stage in pmv.STAGES[:-1]:
            session = self.current_session()
            self.command('leaf', payload={'leaf_result': self.leaf(session, stage), 'tool_calls': 1, 'wall_time': 1})
        session = self.current_session()
        bundle = self.bundle(session)
        self.command('leaf', payload={'leaf_result': self.leaf(session, 'verify', bundle=bundle),
                                     'tool_calls': 1, 'wall_time': 1})
        return bundle

    def test_public_complete_flow_keeps_live_gate_and_supports_restart_replay(self):
        before = copy.deepcopy(self.kernel.ledger['tickets']['01'])
        other_gate = self.kernel.open_gate('03', category='human', scope='ticket',
            reason='Separate live authority remains required')
        self.store.save(self.kernel.ledger)
        other_before = copy.deepcopy(self.kernel.ledger['gates'][other_gate])
        bundle = self.advance_to_audit()
        pending = self.store.load()
        self.assertEqual('open', pending['gates'][self.gate_id]['state'])
        self.assertIsNone(pending['tickets']['02']['candidate_ref'])
        # A crash after the audit save must leave a resumable, still-open condition.
        with mock.patch('autopilot.cli.Kernel.approve_gate',
                        side_effect=TransitionError('interrupted after audit persistence')):
            self.command('complete', payload=bundle, expected=2)
        pending = self.store.load()
        self.assertEqual('open', pending['gates'][self.gate_id]['state'])
        receipt = pending['gates'][self.gate_id]['details'][pmv.SESSION_KEY]['audit']
        self.assertIsNotNone(receipt)
        raw = self.store.path.read_bytes()
        evidence_path = self.run_dir / 'qa-execute.txt'
        original = evidence_path.read_bytes()
        evidence_path.write_text('Changed after audit persistence', encoding='utf-8')
        self.command('complete', payload=bundle, expected=2)
        output = io.StringIO()
        with redirect_stdout(output):
            code = cli_main(['approve', 'test', self.gate_id, '--repo', str(self.repo),
                '--actor', 'verification-audit', '--evidence', 'post-merge-audit://' + receipt['digest']])
        self.assertEqual('open', self.store.load()['gates'][self.gate_id]['state'])
        self.assertEqual(2, code, output.getvalue())
        self.assertIn('post-merge-verify', output.getvalue())
        self.assertEqual(raw, self.store.path.read_bytes())
        evidence_path.write_bytes(original)
        result = self.command('complete', payload=bundle)
        completed = self.store.load()
        self.assertEqual('verified', result['state'])
        self.assertEqual('passed', completed['gates'][self.gate_id]['state'])
        self.assertEqual('pending', completed['tickets']['02']['state'])
        self.assertIsNone(completed['tickets']['02']['candidate_ref'])
        self.assertEqual(before, completed['tickets']['01'])
        self.assertEqual(other_before, completed['gates'][other_gate])
        self.assertEqual('blocked', self.current_session()['audit']['reduction']['release_status'])
        raw = self.store.path.read_bytes()
        self.command('status')
        self.command('complete', payload=bundle)
        self.assertEqual(raw, self.store.path.read_bytes())

    def test_out_of_order_old_candidate_and_false_isolation_are_rejected(self):
        session = self.bind()
        before = copy.deepcopy(session)
        with self.assertRaises(ValueError):
            pmv.append_leaf(self.kernel.ledger, session, self.leaf(session, 'review'))
        stale = self.leaf(session, 'implement')
        stale['candidate_ref'] = self.kernel.ledger['tickets']['01']['candidate_ref']
        with self.assertRaises(ValueError):
            pmv.append_leaf(self.kernel.ledger, session, stale)
        dishonest = self.leaf(session, 'implement')
        dishonest['execution']['isolation'] = 'independent'
        with self.assertRaises(ValueError):
            pmv.append_leaf(self.kernel.ledger, session, dishonest)
        self.assertEqual(before, session)

    def test_partial_continuation_and_duplicate_do_not_reset_budget(self):
        session = self.bind()
        partial = self.leaf(session, 'implement', complete=False)
        session = pmv.append_leaf(self.kernel.ledger, session, partial, tool_calls=2, wall_time=3)
        repeat = pmv.append_leaf(self.kernel.ledger, session, partial, tool_calls=2, wall_time=3)
        self.assertEqual(session, repeat)
        self.assertEqual(1, pmv.replay_entries(self.kernel.ledger, repeat)[0]['interactions_consumed'])
        complete = self.leaf(session, 'implement')
        session = pmv.append_leaf(self.kernel.ledger, session, complete, tool_calls=1, wall_time=1)
        budget, _, stage = pmv.replay_entries(self.kernel.ledger, session)
        self.assertEqual(2, budget['interactions_consumed'])
        self.assertEqual('simplify', stage)
        with self.assertRaises(ValueError):
            pmv.append_leaf(self.kernel.ledger, session, complete, tool_calls=True, wall_time=1)

    def test_wrong_source_tree_pause_and_normalized_input_tampering_fail(self):
        ledger = copy.deepcopy(self.kernel.ledger)
        ledger['gates'][self.gate_id]['details']['source_tree'] = 'f' * 40
        with self.assertRaisesRegex(ValueError, 'head/tree'):
            pmv.bind_source(ledger, self.gate_id, self.repo)
        ledger = copy.deepcopy(self.kernel.ledger)
        ledger['pause'] = {'reason': 'fixture pause'}
        with self.assertRaisesRegex(ValueError, 'paused'):
            pmv.bind_source(ledger, self.gate_id, self.repo)
        for disposition in ('on-hold', 'canceled'):
            with self.subTest(disposition=disposition):
                ledger = copy.deepcopy(self.kernel.ledger)
                ledger['tickets']['02']['disposition'] = disposition
                with self.assertRaisesRegex(ValueError, 'open, unstarted'):
                    pmv.bind_source(ledger, self.gate_id, self.repo)
        session = self.bind()
        session['normalized_ticket']['body'] = '## Acceptance Criteria\n- [ ] Weaker criterion\n'
        session['criteria'] = [{'id': 'criterion-1', 'text': 'Weaker criterion'}]
        with self.assertRaisesRegex(ValueError, 'normalized input'):
            pmv.validate_session(self.kernel.ledger, self.gate_id, session)

    def test_canonical_audit_cannot_substitute_a_different_review_or_scope(self):
        bundle = self.advance_to_audit()
        raw = self.store.path.read_bytes()
        forged = copy.deepcopy(bundle)
        forged['stage_results'][2]['artifact'] = 'historical://different-review'
        self.command('complete', payload=forged, expected=2)
        self.assertEqual(raw, self.store.path.read_bytes())
        forged = copy.deepcopy(bundle)
        forged['claims'][0]['text'] = 'A weaker assertion'
        self.command('complete', payload=forged, expected=2)
        self.assertEqual(raw, self.store.path.read_bytes())
        (self.run_dir / 'qa-execute.txt').write_text('changed', encoding='utf-8')
        self.command('complete', payload=bundle, expected=2)
        self.assertEqual(raw, self.store.path.read_bytes())

    def test_reserved_budget_stops_work_without_changing_the_session(self):
        ledger = copy.deepcopy(self.kernel.ledger)
        ledger['max_leaf_interactions'] = 4
        session = pmv.bind_source(ledger, self.gate_id, self.repo)
        for stage in ('implement', 'simplify'):
            session = pmv.append_leaf(ledger, session, self.leaf(session, stage))
        before = copy.deepcopy(session)
        with self.assertRaisesRegex(ValueError, 'budget|reserved'):
            pmv.append_leaf(ledger, session, self.leaf(session, 'review'))
        self.assertEqual(before, session)
        self.assertEqual(2, pmv.replay_entries(ledger, session)[0]['interactions_consumed'])

    def test_replacement_refs_and_cross_repository_source_fail_before_binding(self):
        before = copy.deepcopy(self.kernel.ledger)
        with tempfile.TemporaryDirectory() as other:
            subprocess.run(['git', 'init', other], check=True, capture_output=True)
            with self.assertRaisesRegex(ValueError, 'different repository'):
                pmv.bind_source(self.kernel.ledger, self.gate_id, Path(other))
        self.git('replace', 'HEAD', 'HEAD~1')
        with self.assertRaisesRegex(ValueError, 'replacement'):
            self.bind()
        self.assertEqual(before, self.kernel.ledger)

    def test_missing_or_ambiguous_parent_and_malformed_oid_fail_closed(self):
        ledger = copy.deepcopy(self.kernel.ledger)
        ledger['tickets']['02']['blocked_by'] = []
        with self.assertRaisesRegex(ValueError, 'missing or ambiguous'):
            pmv.gate_scope(ledger, self.gate_id)
        ledger = copy.deepcopy(self.kernel.ledger)
        ledger['tickets']['03']['candidate_ref'] = ledger['tickets']['01']['candidate_ref']
        ledger['tickets']['02']['blocked_by'].append('03')
        with self.assertRaisesRegex(ValueError, 'missing or ambiguous'):
            pmv.gate_scope(ledger, self.gate_id)
        ledger = copy.deepcopy(self.kernel.ledger)
        ledger['gates'][self.gate_id]['details']['historical_candidate_ref']['base_tree_oid'] = '--output=forbidden'
        with self.assertRaisesRegex(ValueError, 'full Git object IDs'):
            pmv.gate_scope(ledger, self.gate_id)

    def test_frozen_binding_and_forged_persisted_transition_are_rejected(self):
        session = self.bind()
        self.kernel.record_post_merge_session(self.gate_id, session)
        self.store.save(self.kernel.ledger)
        raw = self.store.path.read_bytes()
        updated = copy.deepcopy(session)
        updated['files_expected'] = ['extra.py', 'worker.py']
        with self.assertRaisesRegex(TransitionError, 'frozen binding'):
            self.kernel.record_post_merge_session(self.gate_id, updated)
        forged = Kernel(self.store.load())
        forged.ledger['gates'][self.gate_id]['details'][pmv.SESSION_KEY] = updated
        forged._event('post-merge-verification-recorded', '02', gate_id=self.gate_id,
                      session_digest=pmv.digest(updated))
        with self.assertRaises(LedgerError):
            self.store.save(forged.ledger)
        self.assertEqual(raw, self.store.path.read_bytes())


if __name__ == '__main__':
    unittest.main()
