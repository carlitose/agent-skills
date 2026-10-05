"""Real temp Git/public test processes; model, close and accounting ports are simulated."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import test_chain_controller as f
sys.path.insert(0, str(f.ROOT / 'benchmarks/delivery-bench'))
from staged_behavior import StagedController
from staged_behavior_arm import StagedCell, expanded_skill_turns
from chain_controller import ChainGate


class StagedTests(f.ControllerTests):
    def setUp(self):
        super().setUp()
        (self.home/'facts').rename(self.home/'old-facts')
        self.owner=StagedController(self.original,self.copy,self.home/'facts',self.peer,self.decision,coverage_question=f.Q)
        self.messages=[];prior=self.peer.prompt
        def observe(text):
            self.messages.append(json.loads(text));return prior(text)
        self.peer.prompt=observe

    def test_stage_order_full_contract_and_normal_freeze(self):
        row=self.run_ticket()
        self.assertEqual(row['status'],'completed-local')
        self.assertEqual([m['role'] for m in self.messages],['analysis','builder','builder','review'])
        self.assertEqual([m.get('writer_stage') for m in self.messages],['orient-readonly','vertical-seed','complete-contract',None])
        self.assertTrue(all(m['ticket']['body']==row['ticket']['body'] for m in self.messages))
        self.assertEqual(self.owner.state['valid_tree'],row['candidate']['candidate_tree_oid'])

    def test_orient_mutation_gates_before_writer(self):
        prior=self.peer.prompt
        def bad(text):
            if json.loads(text)['role']=='analysis':(self.copy/'value.py').write_bytes(b'VALUE=9\n')
            return prior(text)
        self.peer.prompt=bad
        with self.assertRaises(ChainGate):self.run_ticket()
        self.assertNotIn('builder',self.peer.calls)

    def test_two_tickets_real_trees_and_receipts_original_unchanged(self):
        first=self.run_ticket();second=self.run_ticket('B',['A'])
        self.assertEqual((first['status'],second['status']),('completed-local','completed-local'))
        self.assertTrue(Path(first['receipts'][0]['path']).is_file())
        self.assertEqual((self.original/'value.py').read_bytes(),b'VALUE = 0\n')
        self.assertEqual(self.peer.calls.count('builder'),4)

    def test_final_failures_three_and_reentry_do_not_reset(self):
        self.peer.bad=True;r=self.run_ticket()
        self.assertEqual((r['status'],r['failures']),('failed',3))
        self.assertEqual(self.peer.calls.count('fix'),4)
        self.assertEqual(self.run_ticket()['failures'],3)
        self.assertEqual(self.run_ticket('B',['A'])['status'],'dependency-blocked')

    def test_unannounced_swap_still_gates(self):
        self.run_ticket();self.peer.session_id='unannounced'
        with self.assertRaises(ChainGate):self.run_ticket('B',['A'])

    def lifecycle_fixture(self):
        class Process:
            def __init__(self,code):self.code=code
            def poll(self):return self.code
        class Native(f.Peer):
            def __init__(self,root,path,sid,code):
                super().__init__(root);self.cwd=root;self.session_id=sid;self.process=Process(code);self.journal_path=path
                self.journal={'closed':code==0,'complete':True,'unknown_usage':[],'charges':{},'argv_digest':'same'}
                path.write_bytes(json.dumps(self.journal).encode())
            def prompt(self,text):
                if not text.startswith('{'):text=text[text.index('{"role":'):]
                result=super().prompt(text);result['session_id']=self.session_id;return result
        class Account:
            def __init__(self,path,authority,state):self.path=path;self.authority_path=authority;self.state=state
            def _check(self):pass
            def reserve(self,kind,upper):self.state['calls'].append({'status':'inflight'});return len(self.state['calls'])
            def settle(self,ident,costs):self.state['calls'][ident-1]['status']='observed'
        before={'authority_sha256':'same','gate':None,'calls':[{'status':'observed'}],'charges':{},'usd_estimate':0,
                'semantic_calls':1,'launches':1,'operator_costs':[{'usd_estimate':1}]}
        old=Native(self.copy,self.home/'old-native.json','fake-shared',0)
        new=Native(self.copy,self.home/'new-native.json','new-context',None)
        cell=object.__new__(StagedCell);cell.project=self.copy;cell.store=self.home/'facts';cell.owner=self.owner;cell.session=old
        cell.budget=Account(self.home/'budget',self.home/'authority',copy.deepcopy(before))
        after=copy.deepcopy(before);after['launches']+=1;after['operator_costs'].append({'usd_estimate':2})
        account=Account(cell.budget.path,cell.budget.authority_path,after)
        mandate=self.home/'mandate.md';mandate.write_bytes(b'human:user staged-context-v3 request lifecycle')
        reference=str(mandate)+'#sha256='+hashlib.sha256(mandate.read_bytes()).hexdigest()
        return cell,new,account,reference

    def test_owned_transfer_retains_tickets_profiles_and_decision_budget(self):
        first=self.run_ticket();cell,new,account,reference=self.lifecycle_fixture();consumed=self.decision.state['budget']
        epoch=cell.begin_ticket_session(new,self.decision,account,actor='human:user',mandate_ref=reference)
        self.assertEqual(epoch['previous']['session_id'],'fake-shared')
        self.assertEqual(epoch['next']['session_id'],'new-context')
        self.assertEqual(self.decision.state['budget'],consumed)
        self.assertEqual(self.owner.state['tickets']['A']['candidate'],first['candidate'])
        with patch('behavior_skills.native_costs',return_value=[]):second=self.run_ticket('B',['A'])
        self.assertEqual(second['status'],'completed-local')
        self.assertIn('coverage_feedback',self.owner.state['tickets']['B'])
        self.assertEqual(self.owner.state['required_commands'],[self.test])
        self.assertEqual(len(self.owner.state['session_epochs']),1)

    def test_live_old_process_and_cost_reset_cannot_transfer(self):
        self.run_ticket();cell,new,account,reference=self.lifecycle_fixture()
        cell.session.process.code=None
        with self.assertRaises(ChainGate):cell.begin_ticket_session(new,self.decision,account,actor='human:user',mandate_ref=reference)
        cell.session.process.code=0;account.state['calls']=[]
        with self.assertRaises(ChainGate):cell.begin_ticket_session(new,self.decision,account,actor='human:user',mandate_ref=reference)
        self.assertEqual(self.owner.identity['session_id'],'fake-shared')

    def test_transfer_requires_completed_boundary_and_hash_bound_human_mandate(self):
        cell,new,account,reference=self.lifecycle_fixture()
        with self.assertRaises(ChainGate):cell.begin_ticket_session(new,self.decision,account,actor='human:user',mandate_ref=reference)
        self.run_ticket()
        with self.assertRaises(ChainGate):cell.begin_ticket_session(new,self.decision,account,actor='model',mandate_ref=reference)
        with self.assertRaises(ChainGate):cell.begin_ticket_session(new,self.decision,account,actor='human:user',mandate_ref=reference+'x')

    def test_actual_journal_field_expansion_observer(self):
        path=self.home/'messages.jsonl';path.write_bytes((json.dumps({'message':{'role':'user','content':[{'type':'text','text':'<skill name="behavior-first">real expanded text'}]}})+'\n').encode())
        class Port:journal={'session_file':str(path)}
        self.assertEqual(expanded_skill_turns(Port()),1)
