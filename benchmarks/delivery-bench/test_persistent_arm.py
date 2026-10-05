"""Causal local boundaries only; no Pi/provider/secret access."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(Path(__file__).parent), str(ROOT/'ticket-driver/scripts'), str(ROOT/'ticket-autopilot/scripts')]
from persistent_arm import Budget, BudgetedSession, PersistentCell, clone_product, make_decisions, snapshot_tree, validate_argv
from chain_controller import ChainGate


class ArmBoundaryTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory(prefix='spb01-')
        self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)
        self.authority={'schema':1,'authority_type':'benchmark-only','authorized_by':'human:user',
            'budget':{'currency':'EUR','ceiling':10,'usd_per_eur':1.1},
            'model':{'provider':'fixture','id':'exact','thinking':'medium'},
            'permissions':{'pi':True,'jev':True,'judge':True},
            'scope':{'arms':['bare','pi-jev-persistent'],'scenarios':['fixture'],'length':4,'repetitions':1},
            'limits':{'max_pi_launches':2,'max_semantic_calls':3}}
        self.path=self.root/'authority.json'
        self.path.write_bytes(json.dumps(self.authority).encode())
        self.budget=Budget(self.path,self.root/'budget.json')
        # This fixture contains no paid operator. Never use this synthetic observation for live admission.
        self.budget.observe_operator_cost(0.0,'fixture:no-paid-operator')

    def test_budget_cumulative_reservation_and_no_duplicate_source(self):
        reservation=self.budget.reserve('pi',2)
        usage={'source':'native:s1:e1','usage':{'totalTokens':2},'usd_estimate':.5}
        self.budget.settle(reservation,[usage])
        reservation=self.budget.reserve('judge',2)
        self.budget.settle(reservation,[usage])
        self.assertEqual(self.budget.state['usd_estimate'],.5)
        reopened=Budget(self.path,self.root/'budget.json')
        self.assertEqual(reopened.state,self.budget.state)
        with self.assertRaises(ChainGate):
            reopened.reserve('pi',11)

    def test_unknown_cost_preserved_and_stops_new_spend(self):
        reservation=self.budget.reserve('pi',2)
        with self.assertRaises(ChainGate):
            self.budget.settle(reservation,[{'source':'native:s1:e1','usage':None,'usd_estimate':None}])
        self.assertTrue(self.budget.state['gate'])
        self.assertEqual(self.budget.state['calls'][0]['status'],'unknown')
        with self.assertRaises(ChainGate):
            self.budget.reserve('judge',1)
        self.assertEqual(self.budget.state['charges']['native:s1:e1']['usage'],None)

    def test_inflight_or_changed_authority_never_replays(self):
        self.budget.reserve('pi',1)
        with self.assertRaises(ChainGate):
            Budget(self.path,self.root/'budget.json').reserve('pi',1)
        self.path.write_bytes(b'{}')
        with self.assertRaises(ChainGate):
            Budget(self.path,self.root/'budget.json')

    def test_session_wrapper_keeps_identity_roles_and_observes_final_usage(self):
        class Peer:
            pid=123
            session_id='one-session'
            journal={'charges':{}}
            def prompt(self,message):
                self.message=message
                self.journal['charges']['e1']={'usage':{'cost':{'total':.01},'totalTokens':3}}
                return {'pid':self.pid,'session_id':self.session_id,'text':'No findings.'}
        peer=Peer()
        wrapper=BudgetedSession(peer,self.budget,reservation_usd=2)
        result=wrapper.prompt(json.dumps({'role':'review','ticket':{'body':'task'}}))
        self.assertEqual((result['pid'],result['session_id']),(123,'one-session'))
        self.assertIn('findings',peer.message)
        self.assertIn('read-only',peer.message.lower())
        self.assertEqual(self.budget.state['usd_estimate'],.01)

    def test_launch_requires_pi_permission_and_no_inflight_reservation(self):
        from unittest.mock import patch
        good=['node','pi.js','--mode','rpc','--provider','fixture','--model','exact','--thinking','medium']
        self.budget.reserve('judge',1)
        with patch('persistent_arm.ChainSession') as launch, self.assertRaises(ChainGate):
            self.budget.launch(good,cwd=self.root,store=self.root/'session')
        launch.assert_not_called()

    def test_argv_model_mode_bound_to_grant(self):
        good=['node','pi.js','--mode','rpc','--provider','fixture','--model','exact','--thinking','medium']
        validate_argv(good,self.authority)
        with self.assertRaises(ChainGate):
            validate_argv([*good[:-1],'high'],self.authority)
        with self.assertRaises(ChainGate):
            validate_argv([*good,'--api-key','forbidden'],self.authority)

    def test_two_cell_requests_reuse_one_resource_and_snapshot_valid_trees(self):
        import subprocess
        self.authority['budget']['ceiling']=100
        self.path.write_bytes(json.dumps(self.authority).encode())
        budget=Budget(self.path,self.root/'cell-budget.json')
        budget.observe_operator_cost(0.0,'fixture:no-paid-operator')
        original=self.root/'original'; original.mkdir()
        def git(where,*args):
            return subprocess.check_output(['git','-C',str(where),*args]).decode().strip()
        git(original,'init','-q'); git(original,'config','core.autocrlf','false')
        git(original,'config','user.name','fixture'); git(original,'config','user.email','fixture@local')
        (original/'value.py').write_bytes(b'VALUE=0\n')
        git(original,'add','.'); git(original,'commit','-qm','seed')
        project=self.root/'project'
        clone_product(original,project)
        class Peer:
            pid=100; session_id='same'; launches=1; gated=False
            journal={'charges':{}}
            def prompt(inner,message):
                role=json.loads(message.split('\n',1)[1])['role']
                if role in ('builder','fix'):
                    (project/'value.py').write_bytes(b'VALUE=1\n')
                    if inner.gated:
                        (project/'candidate-only.txt').write_bytes(b'not delivered\n')
                ident=str(len(inner.journal['charges'])+1)
                inner.journal['charges'][ident]={'usage':{'totalTokens':2,'cost':{'total':.01}}}
                return {'pid':inner.pid,'session_id':inner.session_id,
                        'text':'No findings.' if role=='review' else 'Implemented.'}
        peer=Peer()
        cfg={'noul_low':.2,'noul_high':.8,'choice_min_confidence':.75,'risk_score_high':2.5,'max_attempts':3}
        def ask(state,selected,policy):
            self.assertIn('diff',state)
            self.assertEqual(policy['max_attempts'],1)
            return {key:{'type':'noul','noul':.5 if peer.gated else 1} for key in selected},{'input_tokens':3,'output_tokens':0}
        decisions=make_decisions(peer,budget,self.root/'decisions.json',cfg,jev_ask=ask)
        q={'type':'noul','instructions':'Coverage?','criteria':{'true':'yes','false':'no'}}
        cell=PersistentCell(original,project,self.root/'facts',peer,decisions,budget,coverage_question=q)
        command=[sys.executable,'-B','-c','from value import VALUE; assert VALUE==1']
        first=cell.request('T1','# Fixture\n\nImplement VALUE=1.\n',[command])
        second=cell.request('T2','# Fixture\n\nPreserve VALUE=1.\n',[command],dependencies=['T1'])
        self.assertEqual((first['status'],second['status']),('completed-local','completed-local'))
        self.assertEqual(first['cost_report']['operator_estimate_usd'],0.0)  # synthetic fixture only
        self.assertEqual(first['cost_report']['combined_estimate_usd'],first['budget_estimated_usd'])
        self.assertGreater(second['cost_report']['combined_estimate_usd'],first['cost_report']['combined_estimate_usd'])
        self.assertIsNone(second['cost_report']['invoice_total_usd'])
        self.assertEqual((first['pid'],second['pid']),(100,100))
        self.assertEqual((first['session_id'],second['session_id']),('same','same'))
        self.assertEqual((Path(first['snapshot'])/'value.py').read_bytes(),b'VALUE=1\n')
        self.assertEqual((original/'value.py').read_bytes(),b'VALUE=0\n')
        self.assertEqual(budget.state['semantic_calls'],2)
        peer.gated=True
        decisions.judge=None  # this negative case has no configured semantic completion port
        gated=cell.request('T3','# Fixture\n\nCandidate with uncertain coverage.\n',[command])
        self.assertEqual(gated['status'],'human-gated')
        self.assertNotEqual(gated['candidate_ref']['candidate_tree_oid'],gated['delivered_tree'])
        self.assertFalse((Path(gated['snapshot'])/'candidate-only.txt').exists())
        self.assertTrue((project/'candidate-only.txt').exists())

    def test_interrupted_turn_cannot_hide_unknown_cost_behind_partial_native_usage(self):
        class Peer:
            pid=123; session_id='partial'
            journal={'charges':{},'unknown_usage':[]}
            def prompt(inner,message):
                inner.journal['charges']['partial-entry']={'usage':{'cost':{'total':0}}}
                inner.journal['unknown_usage'].append({'launch':1,'operation':6,
                    'reason':'unfinished or unreported operation'})
                raise RuntimeError('fake interrupted transport')
        wrapper=BudgetedSession(Peer(),self.budget,reservation_usd=2)
        with self.assertRaises(RuntimeError):
            wrapper.prompt(json.dumps({'role':'builder','ticket':{'body':'task'}}))
        self.assertEqual(self.budget.state['calls'][0]['status'],'unknown')
        self.assertTrue(self.budget.state['gate'])
        with self.assertRaises(ChainGate):
            self.budget.reserve('pi',1)

    def test_jev_unavailable_retains_safe_cause_and_unknown_consumption(self):
        from arbiter import Unavailable
        class Peer:
            pass
        def ask(state,selected,policy):
            raise Unavailable('HTTP 403')
        cfg={'noul_low':.2,'noul_high':.8,'choice_min_confidence':.75,'risk_score_high':2.5,'max_attempts':3}
        engine=make_decisions(Peer(),self.budget,self.root/'decisions.json',cfg,jev_ask=ask)
        cf={'contract_version':2,'base_tree_oid':'a'*40,'candidate_tree_oid':'b'*40,'ticket_digest':'c'*64}
        q={'type':'noul','instructions':'Coverage?','criteria':{'true':'yes','false':'no'}}
        self.assertEqual(engine.decide('q',q,{},cf)['outcome'],'uncertain')
        self.assertEqual(self.budget.state['calls'][0]['failure'],'HTTP 403')
        self.assertEqual(self.budget.state['calls'][0]['status'],'unknown')
        self.assertTrue(self.budget.state['gate'])
        self.assertEqual(self.budget.state['semantic_calls'],1)

    def test_snapshot_uses_actual_git_tree_without_touching_source(self):
        import subprocess
        source=self.root/'source';source.mkdir()
        def git(*args):
            return subprocess.check_output(['git','-C',str(source),*args]).decode().strip()
        git('init','-q');git('config','user.name','fixture');git('config','user.email','fixture@local')
        (source/'value.py').write_bytes(b'VALUE=1\n')
        git('add','.');git('commit','-qm','seed')
        tree=git('write-tree')
        (source/'value.py').write_bytes(b'VALUE=9\n')
        target=self.root/'snapshot'
        snapshot_tree(source,tree,target)
        self.assertEqual((target/'value.py').read_bytes(),b'VALUE=1\n')
        self.assertEqual((source/'value.py').read_bytes(),b'VALUE=9\n')
        with self.assertRaises(ChainGate):
            snapshot_tree(source,tree,target)


if __name__=='__main__':
    unittest.main()
