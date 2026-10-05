"""Owned adapter tests use a Python fixture, never the real Pi executable."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
from chain_session import ChainSession, SessionFailure

PEER = Path(__file__).with_name('fake_chain_peer.py')


class PersistentSession(unittest.TestCase):
    def owner(self, *, prefix='spc01-', **options):
        temporary = tempfile.TemporaryDirectory(prefix=prefix)
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        owner = ChainSession([sys.executable, '-B', str(PEER), '--mode', 'rpc'],
                             cwd=root, store=root / 'store', timeout=2, **options)
        self.addCleanup(owner.close)
        return owner

    def test_two_prompts_keep_process_and_session(self):
        owner = self.owner()
        pid = owner.pid
        first = owner.prompt('first request')
        second = owner.prompt('second request')
        self.assertEqual(owner.pid, pid)
        self.assertEqual(owner.session_id, 'fake-main')
        self.assertEqual(owner.launches, 1)
        self.assertEqual(first['text'], 'first request')
        self.assertEqual(second['text'], 'second request')
        self.assertEqual(first['entry_ids'], ['1'])
        self.assertEqual(second['entry_ids'], ['2'])
        self.assertEqual(len(owner.journal['charges']), 2)

    def test_fast_settled_before_acceptance_and_unicode(self):
        owner = self.owner()
        result = owner.prompt('a\u2028b\u2029c')
        self.assertEqual(result['text'], 'a\u2028b\u2029c')
        self.assertEqual(result['disposition'], 'started')

    def test_handled_does_not_wait_for_settled_or_reuse_old_text(self):
        owner = self.owner()
        owner.prompt('old text')
        result = owner.prompt('handled')
        self.assertEqual(result['disposition'], 'handled')
        self.assertIsNone(result['text'])
        self.assertEqual(result['entries'][0]['customType'], 'fixture-receipt')

    def test_queued_is_not_our_completed_turn(self):
        owner = self.owner()
        with self.assertRaises(SessionFailure):
            owner.prompt('queued')
        self.assertFalse(owner.journal['complete'])

    def test_length_malformed_and_crash_do_not_pass(self):
        for value in ['length', 'error', 'aborted', 'malformed', 'crash']:
            with self.subTest(value=value):
                owner = self.owner()
                with self.assertRaises(SessionFailure):
                    owner.prompt(value)
                self.assertFalse(owner.journal['complete'])

    def test_stderr_is_drained_not_parsed(self):
        owner = self.owner()
        self.assertEqual(owner.prompt('stderr')['text'], 'stderr')
        self.assertTrue(owner.stderr_path.stat().st_size)
        self.assertLessEqual(owner.stderr_path.stat().st_size, owner.max_stderr_bytes)

    def test_missing_usage_is_unknown_and_duplicate_entry_is_idempotent(self):
        owner = self.owner()
        owner.prompt('first')
        entry = {'type': 'message', 'id': 'external', 'message': {'role': 'assistant'}}
        owner.observe([entry])
        owner.observe([entry])
        self.assertEqual(owner.journal['charges']['external']['usage'], None)
        self.assertEqual(len(owner.journal['charges']), 2)
        with self.assertRaises(SessionFailure):
            owner.observe([{**entry, 'message': {'role': 'assistant', 'usage': {'input': 99}}}])

    def test_compaction_tool_and_unknown_usage_kind_are_not_lost(self):
        owner = self.owner()
        owner.prompt('compaction')
        self.assertEqual(len(owner.journal['charges']), 4)
        total = sum(c['usage']['totalTokens'] for c in owner.journal['charges'].values())
        self.assertEqual(total, 20)
        owner.sync()
        self.assertEqual(len(owner.journal['charges']), 4)

    def test_journal_and_cursor_persist_together(self):
        owner = self.owner()
        owner.prompt('first')
        saved = json.loads(owner.journal_path.read_text())
        self.assertEqual(saved['cursor'], '1')
        self.assertEqual(set(saved['entry_hashes']), {'1'})
        self.assertEqual(set(saved['charges']), {'1'})
        self.assertTrue(saved['complete'])
        self.assertEqual(saved['session_id'], 'fake-main')

    def test_jev_sentinel_does_not_enter_child_or_journal(self):
        with patch.dict(os.environ, {'TYPESAFE_API_KEY': 'SPC-SENTINEL-NOT-SECRET'}):
            owner = self.owner()
            self.assertEqual(owner.prompt('sentinel')['text'], 'secret=False')
            self.assertNotIn('SPC-SENTINEL', owner.journal_path.read_text())
            self.assertEqual(os.environ['TYPESAFE_API_KEY'], 'SPC-SENTINEL-NOT-SECRET')

    def test_resume_counts_new_launch_without_duplicate_charge(self):
        owner = self.owner(prefix='spc01-\u00e9-')
        owner.prompt('first')
        with self.assertRaises(SessionFailure):
            owner.resume(authorized=True, budget=True)
        self.assertEqual(owner.launches, 1)
        owner.close()
        for options in [{'authorized': False, 'budget': True}, {'authorized': True, 'budget': False}]:
            with self.assertRaises(SessionFailure):
                owner.resume(**options)
        owner.resume(authorized=True, budget=True)
        self.assertEqual(owner.launches, 2)
        self.assertEqual(owner.session_id, 'fake-main')
        self.assertEqual(len(owner.journal['charges']), 1)
        owner.prompt('second')
        self.assertEqual(len(owner.journal['charges']), 2)

    def test_tampered_session_blocks_resume_without_launch(self):
        owner = self.owner()
        owner.prompt('first')
        owner.close()
        Path(owner.journal['session_file']).write_bytes(b'{}\n')
        with self.assertRaises(SessionFailure):
            owner.resume(authorized=True, budget=True)
        self.assertEqual(owner.launches, 1)

    def test_timeout_is_not_termination_or_retry_grant(self):
        owner = self.owner()
        owner.timeout = 0.05
        with self.assertRaises(SessionFailure):
            owner.prompt('slow')
        with self.assertRaises(SessionFailure):
            owner.resume(authorized=True, budget=True)
        self.assertEqual(owner.launches, 1)
        self.assertFalse(owner.journal['complete'])

    def test_output_bound_and_bad_response_fail_closed(self):
        owner = self.owner(max_record_bytes=1024)
        with self.assertRaises(SessionFailure):
            owner.prompt('x' * 900)
        self.assertFalse(owner.journal['complete'])
        owner = self.owner()
        with self.assertRaises(SessionFailure):
            owner.prompt('bad-response')
        self.assertFalse(owner.journal['complete'])

    def test_session_replacement_and_corrupt_journal_do_not_rebind(self):
        owner = self.owner()
        with self.assertRaises(SessionFailure):
            owner.prompt('replace-session')
        self.assertEqual(owner.session_id, 'fake-main')
        self.assertFalse(owner.journal['complete'])
        owner = self.owner()
        owner.prompt('first')
        owner.close()
        owner.journal_path.write_bytes(b'{}\n')
        with self.assertRaises(SessionFailure):
            owner.resume(authorized=True, budget=True)
        self.assertEqual(owner.launches, 1)

    def test_failed_first_turn_cannot_be_blindly_retried(self):
        owner = self.owner()
        with self.assertRaises(SessionFailure):
            owner.prompt('bad-response')
        with self.assertRaises(SessionFailure):
            owner.prompt('second')
        self.assertFalse(owner.journal['complete'])
        self.assertTrue(owner.journal['unknown_usage'])

    def test_live_history_rewrite_cannot_reset_its_prefix_hash(self):
        owner = self.owner()
        owner.prompt('first')
        old_cursor = owner.journal['cursor']
        path = Path(owner.journal['session_file'])
        path.write_bytes(path.read_bytes().replace(b'fake-main', b'FAKE-main'))
        with self.assertRaises(SessionFailure):
            owner.prompt('second')
        self.assertEqual(owner.journal['cursor'], old_cursor)
        self.assertFalse(owner.journal['complete'])

    def test_protocol_receipt_cannot_replace_missing_frame_or_output(self):
        for message in ['unterminated', 'handled-empty']:
            with self.subTest(message=message):
                owner = self.owner()
                with self.assertRaises(SessionFailure):
                    owner.prompt(message)
                self.assertFalse(owner.journal['complete'])

    def test_summary_and_unknown_usage_metadata_are_preserved(self):
        owner = self.owner()
        owner.observe([{'type': 'branch_summary', 'id': 'summary', 'usage': None},
                       {'type': 'usage', 'id': 'unknown', 'kind': 'new-kind', 'usage': None}])
        self.assertIsNone(owner.journal['charges']['summary']['usage'])
        self.assertEqual(owner.journal['charges']['unknown']['operation_kind'], 'new-kind')

    def test_requires_rpc_and_persistent_store_not_print_or_no_session(self):
        temporary = tempfile.TemporaryDirectory(prefix='spc01-invalid-')
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        for flags in [[], ['--mode', 'json'], ['--mode', 'rpc', '--no-session'],
                      ['--mode', 'rpc', '--print'], ['--mode', 'rpc', '--continue']]:
            with self.subTest(flags=flags), self.assertRaises(ValueError):
                ChainSession([sys.executable, '-B', str(PEER), *flags],
                             cwd=root, store=root / 'store')


if __name__ == '__main__':
    unittest.main()
