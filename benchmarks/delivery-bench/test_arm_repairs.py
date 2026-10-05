"""Owned clone/accounting causal fixtures. No provider, model, secret or hidden oracle access."""
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
import test_persistent_arm as fixtures
import persistent_arm as arm
from chain_controller import ChainGate


class ArmRepairs(unittest.TestCase):
    def setUp(self):
        fixtures.ArmBoundaryTests.setUp(self)
        # Separate unknown-accounting store, not a mutation/reset of the fixture's priced history.
        self.budget = arm.Budget(self.path, self.root/'repair-budget.json')

    def test_covered_launch_renewal_preserves_consumption_and_original_authority(self):
        self.budget.observe_operator_cost(1.0, 'fixture:operator')
        reservation = self.budget.reserve('pi', 1)
        self.budget.settle(reservation, [{'source': 'native:fixture:past', 'usage': {}, 'usd_estimate': .5}])
        argv = ['node', 'pi.js', '--mode', 'rpc', '--provider', 'fixture', '--model', 'exact', '--thinking', 'medium']
        with patch('persistent_arm.ChainSession'):
            self.budget.launch(argv, cwd=self.root, store=self.root/'one')
            self.budget.launch(argv, cwd=self.root, store=self.root/'two')
        before = json.loads(json.dumps(self.budget.state))
        authority = self.path.read_bytes()
        with self.assertRaises(ChainGate):
            self.budget.admit_launch(argv)
        binding = self.budget.renew_launch_capacity(actor='human:user', mandate_ref='fixture:explicit-repair-loop')
        self.assertEqual(binding['max_pi_launches'], 3)
        self.budget.admit_launch(argv)
        for key, value in before.items():
            self.assertEqual(self.budget.state[key], value)
        self.assertEqual(self.path.read_bytes(), authority)
        again = self.budget.renew_launch_capacity(actor='human:user', mandate_ref='fixture:explicit-repair-loop')
        self.assertEqual(again, binding)
        reopened = arm.Budget(self.path, self.root/'repair-budget.json')
        reopened.admit_launch(argv)
        with patch('persistent_arm.ChainSession'):
            reopened.launch(argv, cwd=self.root, store=self.root/'three')
        self.assertEqual(reopened.state['launches'], 3)
        with self.assertRaises(ChainGate):
            reopened.admit_launch(argv)

    def test_exhausted_capacity_is_detected_without_start_or_consumption(self):
        self.budget.observe_operator_cost(1.0, 'fixture:operator')
        argv = ['node', 'pi.js', '--mode', 'rpc', '--provider', 'fixture', '--model', 'exact', '--thinking', 'medium']
        with patch('persistent_arm.ChainSession'):
            for n in range(2):
                self.budget.launch(argv, cwd=self.root, store=self.root/str(n))
        before = json.loads(json.dumps(self.budget.state))
        with patch('persistent_arm.ChainSession') as launch:
            with self.assertRaisesRegex(ChainGate, 'native-launch-capacity: consumed 2, admitted limit 2'):
                self.budget.admit_launch(argv)
            with self.assertRaises(ChainGate):
                self.budget.launch(argv, cwd=self.root, store=self.root/'forbidden')
            launch.assert_not_called()
        self.assertEqual(self.budget.state, before)

    def test_launch_renewal_rejects_invalid_provenance_without_mutation(self):
        self.budget.observe_operator_cost(1.0, 'fixture:operator')
        before = json.loads(json.dumps(self.budget.state))
        for actor, ref in [('assistant', 'fixture:grant'), ('human:user', ''), ('human:user', True)]:
            with self.subTest(actor=actor, ref=ref), self.assertRaises(ChainGate):
                self.budget.renew_launch_capacity(actor=actor, mandate_ref=ref)
        self.assertEqual(self.budget.state, before)

    def test_launch_renewal_does_not_bypass_unknown_exhausted_or_inflight_cost(self):
        grant = {'actor': 'human:user', 'mandate_ref': 'fixture:explicit-repair-loop'}
        with self.assertRaises(ChainGate):
            self.budget.renew_launch_capacity(**grant)
        self.budget.observe_operator_cost(self.budget.ceiling + 1, 'fixture:exhausted')
        with self.assertRaises(ChainGate):
            self.budget.renew_launch_capacity(**grant)
        fresh = arm.Budget(self.path, self.root/'inflight-budget.json')
        fresh.observe_operator_cost(1.0, 'fixture:known')
        fresh.reserve('pi', 1)
        with self.assertRaises(ChainGate):
            fresh.renew_launch_capacity(**grant)
        self.assertNotIn('launch_capacity_bindings', fresh.state)

    def test_launch_renewal_preserves_permission_and_unknown_usage_gates(self):
        denied = dict(self.authority, permissions={'pi': False, 'jev': True, 'judge': True})
        authority = self.root/'denied-authority.json'
        authority.write_bytes(json.dumps(denied).encode())
        budget = arm.Budget(authority, self.root/'denied-budget.json')
        budget.observe_operator_cost(1.0, 'fixture:operator')
        grant = {'actor': 'human:user', 'mandate_ref': 'fixture:explicit-repair-loop'}
        with self.assertRaises(ChainGate):
            budget.renew_launch_capacity(**grant)
        self.budget.observe_operator_cost(1.0, 'fixture:operator')
        reservation = self.budget.reserve('pi', 1)
        with self.assertRaises(ChainGate):
            self.budget.settle(reservation, [{'source': 'native:unknown', 'usage': None, 'usd_estimate': None}])
        before = json.loads(json.dumps(self.budget.state))
        with self.assertRaises(ChainGate):
            self.budget.renew_launch_capacity(**grant)
        self.assertEqual(self.budget.state, before)
        self.assertNotIn('launch_capacity_bindings', self.budget.state)

    def test_consumed_renewal_can_bind_next_launch_but_not_reset_count(self):
        self.budget.observe_operator_cost(1.0, 'fixture:operator')
        argv = ['node', 'pi.js', '--mode', 'rpc', '--provider', 'fixture', '--model', 'exact', '--thinking', 'medium']
        grant = {'actor': 'human:user', 'mandate_ref': 'fixture:explicit-repair-loop'}
        with patch('persistent_arm.ChainSession'):
            for n in range(2):
                self.budget.launch(argv, cwd=self.root, store=self.root/str(n))
            self.budget.renew_launch_capacity(**grant)
            self.budget.launch(argv, cwd=self.root, store=self.root/'third')
        second = self.budget.renew_launch_capacity(**grant)
        self.assertEqual((second['previous_limit'], second['max_pi_launches']), (3, 4))
        self.assertEqual(self.budget.state['launches'], 3)
        self.assertEqual(len(self.budget.state['launch_capacity_bindings']), 2)

    def test_unknown_operator_cost_keeps_total_unknown_and_blocks_new_spend(self):
        report = self.budget.cost_report()
        self.assertIsNone(report['operator_estimate_usd'])
        self.assertIsNone(report['combined_estimate_usd'])
        self.assertIsNone(report['remaining_estimate_usd'])
        with self.assertRaises(ChainGate):
            self.budget.reserve('pi', 1)
        good = ['node', 'pi.js', '--mode', 'rpc', '--provider', 'fixture', '--model', 'exact', '--thinking', 'medium']
        with patch('persistent_arm.ChainSession') as launch, self.assertRaises(ChainGate):
            self.budget.launch(good, cwd=self.root, store=self.root/'sessions')
        launch.assert_not_called()

    def test_operator_cost_is_cumulative_idempotent_and_inclusive(self):
        self.budget.observe_operator_cost(9.0, 'fixture:operator-observation-1')
        self.budget.observe_operator_cost(9.0, 'fixture:operator-observation-1')
        self.assertEqual(len(self.budget.state['operator_costs']), 1)
        reservation = self.budget.reserve('pi', 1)
        self.budget.settle(reservation, [{'source':'native:fixture:one','usage':{},'usd_estimate':1.0}])
        report = self.budget.cost_report()
        self.assertEqual(report['experimental_estimate_usd'], 1.0)
        self.assertEqual(report['operator_estimate_usd'], 9.0)
        self.assertEqual(report['combined_estimate_usd'], 10.0)
        self.assertAlmostEqual(report['remaining_estimate_usd'], 1.0)
        self.assertIsNone(report['invoice_total_usd'])
        with self.assertRaises(ChainGate):
            self.budget.reserve('pi', 2)
        with self.assertRaises(ChainGate):
            self.budget.observe_operator_cost(8.0, 'fixture:reset-forbidden')
        with self.assertRaises(ChainGate):
            self.budget.observe_operator_cost(10.0, 'fixture:operator-observation-1')
        reopened = arm.Budget(self.path, self.root/'repair-budget.json')
        self.assertEqual(reopened.cost_report(), report)

    def test_unknown_operator_observation_is_not_zero_or_a_consumption_reset(self):
        self.budget.observe_operator_cost(1.0, 'fixture:known')
        self.budget.observe_operator_cost(None, 'fixture:interrupted')
        self.assertIsNone(self.budget.cost_report()['combined_estimate_usd'])
        with self.assertRaises(ChainGate):
            self.budget.reserve('jev', 1)
        with self.assertRaises(ChainGate):
            self.budget.observe_operator_cost(0.0, 'fixture:lost-history')
        self.budget.observe_operator_cost(2.0, 'fixture:reconciled')
        self.assertEqual(self.budget.cost_report()['combined_estimate_usd'], 2.0)
        self.assertEqual(len(self.budget.state['operator_costs']), 3)

    def test_invalid_operator_estimates_never_create_a_priced_observation(self):
        for amount, source in [(-1, 'fixture:bad'), (float('nan'), 'fixture:bad'),
                               (float('inf'), 'fixture:bad'), (True, 'fixture:bad'), (0, '')]:
            with self.subTest(amount=amount, source=source), self.assertRaises(ChainGate):
                self.budget.observe_operator_cost(amount, source)
        self.assertEqual(self.budget.state['operator_costs'], [])
        self.assertIsNone(self.budget.cost_report()['combined_estimate_usd'])

    def test_unknown_operator_during_reservation_never_loses_returned_native_usage(self):
        self.budget.observe_operator_cost(0.0, 'fixture:known')
        reservation = self.budget.reserve('pi', 1)
        self.budget.observe_operator_cost(None, 'fixture:operator-interrupted')
        usage = {'source': 'native:fixture:one', 'usage': {}, 'usd_estimate': .5}
        with self.assertRaises(ChainGate):
            self.budget.settle(reservation, [usage])
        self.assertEqual(self.budget.state['calls'][0]['status'], 'observed')
        self.assertEqual(self.budget.state['charges'][usage['source']], usage)
        self.assertEqual(self.budget.cost_report()['experimental_estimate_usd'], .5)
        self.assertIsNone(self.budget.cost_report()['combined_estimate_usd'])
        self.assertEqual(arm.Budget(self.path, self.root/'repair-budget.json').state, self.budget.state)

    def test_owned_clone_is_lf_before_checkout_and_never_overwrites_original(self):
        seed = self.root/'seed'; seed.mkdir()
        def git(where,*args):
            return subprocess.check_output(['git','-C',str(where),*args]).decode().strip()
        git(seed,'init','-q'); git(seed,'config','core.autocrlf','false')
        git(seed,'config','user.name','fixture'); git(seed,'config','user.email','fixture@local')
        raw = b'a\xa7\nb\n'; (seed/'legacy.txt').write_bytes(raw)
        git(seed,'add','-A'); git(seed,'commit','-qm','seed')
        original_tree = git(seed,'write-tree')
        target = self.root/'project'
        # Simulate inherited Windows behavior without changing any host configuration.
        import os
        with patch.dict(os.environ, {'GIT_CONFIG_COUNT':'1','GIT_CONFIG_KEY_0':'core.autocrlf','GIT_CONFIG_VALUE_0':'true'}):
            tree = arm.clone_product(seed,target)
        self.assertEqual(tree,original_tree)
        self.assertEqual((target/'legacy.txt').read_bytes(),raw)
        self.assertEqual((seed/'legacy.txt').read_bytes(),raw)
        self.assertEqual(git(seed,'write-tree'),original_tree)
        with self.assertRaises(ChainGate):
            arm.clone_product(seed,target)
        self.assertEqual((target/'legacy.txt').read_bytes(),raw)


if __name__ == '__main__':
    unittest.main()
