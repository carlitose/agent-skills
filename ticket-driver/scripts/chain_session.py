"""One persistent RPC resource for a chain; observations are not quality approval."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import queue
import subprocess
import threading
import time


class SessionFailure(RuntimeError):
    """The caller must reconcile; this exception never grants another launch."""


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def _prefix(path, size):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        remaining = size
        while remaining:
            chunk = stream.read(min(remaining, 65536))
            if not chunk:
                raise SessionFailure('session file shortened')
            digest.update(chunk)
            remaining -= len(chunk)
    return digest.hexdigest()


class ChainSession:
    """Caller supplies its authorized executable/config; no implicit Pi/model selection."""
    def __init__(self, argv, *, cwd, store, timeout=600, max_record_bytes=8388608,
                 max_stderr_bytes=32768):
        argv = list(argv)
        forbidden = {'--no-session', '-p', '--print', '-c', '--continue', '-r', '--resume',
                     '--session', '--session-id', '--session-dir', '--fork', '--api-key'}
        if ('--mode' not in argv or argv.index('--mode') + 1 >= len(argv)
                or argv[argv.index('--mode') + 1] != 'rpc' or forbidden.intersection(argv)):
            raise ValueError('explicit RPC with an owner-controlled persistent store required')
        if timeout <= 0 or max_record_bytes <= 0 or max_stderr_bytes < 0:
            raise ValueError('positive deadline/record bound required')
        self.argv, self.cwd, self.store = argv, Path(cwd).resolve(), Path(store).resolve()
        self.timeout, self.max_record_bytes = timeout, max_record_bytes
        self.max_stderr_bytes = max_stderr_bytes
        self.store.mkdir(parents=True, exist_ok=True)
        self.journal_path = self.store / 'chain-observations.json'
        self.stderr_path = self.store / 'chain-stderr.log'
        if self.journal_path.exists():
            raise SessionFailure('existing journal requires explicit recovery, never overwrite')
        self.journal = {'session_id': None, 'session_file': None, 'launches': 0, 'cursor': None,
                        'entry_hashes': {}, 'charges': {}, 'complete': False, 'closed': False,
                        'cwd': str(self.cwd), 'argv_digest': _digest(argv), 'file_size': 0,
                        'file_prefix_sha256': None}
        self._operation = threading.Lock()
        self._sequence = 0
        try:
            self._start()
            self._state(bind=True)
            self.sync()
            self.journal['complete'] = True
            self._save()
        except BaseException:
            self.close()
            raise

    @property
    def pid(self):
        return self.process.pid

    @property
    def launches(self):
        return self.journal['launches']

    @property
    def session_id(self):
        return self.journal['session_id']

    def _save(self):
        raw = (json.dumps(self.journal, sort_keys=True, ensure_ascii=False) + '\n').encode()
        pending = self.journal_path.with_suffix('.pending')
        with pending.open('wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        pending.replace(self.journal_path)

    def _start(self, session_file=None):
        if hasattr(self, 'process') and self.process.poll() is None:
            raise SessionFailure('previous process still alive')
        self._records = queue.Queue()
        self._buffer_lock = threading.Lock()
        self._buffered = 0
        self._reader_failure = None
        argv = [*self.argv, '--session-dir', str(self.store)]
        if session_file:
            argv += ['--session', session_file]
        env = os.environ.copy()
        env.pop('TYPESAFE_API_KEY', None)
        self.process = subprocess.Popen(argv, cwd=self.cwd, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        self.journal['launches'] += 1
        self.journal['closed'] = False
        self._save()

        def stdout():
            try:
                while raw := self.process.stdout.readline(self.max_record_bytes + 1):
                    with self._buffer_lock:
                        if len(raw) > self.max_record_bytes or self._buffered + len(raw) > 2 * self.max_record_bytes:
                            self._reader_failure = 'RPC output bound exceeded'
                        elif not self._reader_failure:
                            self._buffered += len(raw)
                            self._records.put(raw)
                self._records.put(None)
            except (OSError, ValueError):
                self._reader_failure = 'RPC reader failed'
                self._records.put(None)

        def stderr():
            written = self.stderr_path.stat().st_size if self.stderr_path.exists() else 0
            with self.stderr_path.open('ab') as stream:
                while raw := self.process.stderr.read(4096):
                    chunk = raw[:max(0, self.max_stderr_bytes - written)]
                    stream.write(chunk)
                    stream.flush()
                    written += len(chunk)
        self._readers = [threading.Thread(target=stdout, daemon=True),
                         threading.Thread(target=stderr, daemon=True)]
        for reader in self._readers:
            reader.start()

    def _next(self, deadline):
        if time.monotonic() >= deadline:
            raise SessionFailure('RPC deadline; process termination unknown')
        if self._reader_failure:
            raise SessionFailure(self._reader_failure)
        try:
            raw = self._records.get(timeout=max(0.001, deadline - time.monotonic()))
        except queue.Empty:
            raise SessionFailure('RPC deadline; process termination unknown') from None
        if raw is None:
            raise SessionFailure('RPC process exited before completion')
        with self._buffer_lock:
            self._buffered -= len(raw)
        if not raw.endswith(b'\n'):
            raise SessionFailure('unterminated RPC record')
        try:
            record = json.loads(raw)
            if not isinstance(record, dict):
                raise ValueError()
        except (ValueError, UnicodeError):
            raise SessionFailure('malformed RPC record') from None
        if record.get('type') in ('extension_error', 'extension_ui_request'):
            raise SessionFailure('extension error or unresolved UI interaction')
        return record

    def _request(self, kind, *, wait_run=False, **payload):
        self._sequence += 1
        ident = f'{self.launches}-{self._sequence}'
        raw = (json.dumps({'id': ident, 'type': kind, **payload}, ensure_ascii=False) + '\n').encode()
        if len(raw) > self.max_record_bytes:
            raise SessionFailure('RPC input bound exceeded')
        deadline = time.monotonic() + self.timeout
        finished, write_error = threading.Event(), []
        def send():
            try:
                self.process.stdin.write(raw)
                self.process.stdin.flush()
            except (OSError, ValueError) as error:
                write_error.append(type(error).__name__)
            finally:
                finished.set()
        writer = threading.Thread(target=send, daemon=True)
        self._writer = writer
        writer.start()
        if not finished.wait(self.timeout) or write_error:
            raise SessionFailure('RPC write failed or deadline; termination unknown')
        response, settled, messages = None, False, []
        while True:
            record = self._next(deadline)
            if record.get('type') == 'agent_settled':
                settled = True
            elif record.get('type') == 'message_end' and record.get('message', {}).get('role') == 'assistant':
                messages.append(record['message'])
            elif record.get('type') == 'response':
                if record.get('id') != ident or record.get('command') != kind or not record.get('success'):
                    raise SessionFailure('uncorrelated or failed RPC response')
                response = record.get('data', {})
                if not isinstance(response, dict):
                    raise SessionFailure('invalid RPC response data')
            if response is not None:
                disposition = response.get('disposition') if wait_run else None
                if wait_run and disposition not in ('started', 'handled'):
                    raise SessionFailure('prompt not started/handled; queued work not attributable')
                if not wait_run or disposition == 'handled' or settled:
                    return response, messages

    def _state(self, *, bind=False, require_idle=True):
        state, _ = self._request('get_state')
        sid, filename = state.get('sessionId'), state.get('sessionFile')
        if not isinstance(sid, str) or not sid or not isinstance(filename, str) or not filename:
            raise SessionFailure('missing persistent session identity')
        filename = str(Path(filename).resolve())
        if not Path(filename).is_relative_to(self.store):
            raise SessionFailure('session file outside owned store')
        if bind:
            self.journal.update(session_id=sid, session_file=filename)
        elif sid != self.session_id or filename != self.journal['session_file']:
            raise SessionFailure('unexpected session replacement')
        known_prefix = self.journal['file_prefix_sha256']
        if known_prefix is not None:
            try:
                current_prefix = _prefix(Path(filename), self.journal['file_size'])
            except OSError:
                raise SessionFailure('observed session file unavailable') from None
            if current_prefix != known_prefix:
                raise SessionFailure('observed session history changed')
        if require_idle and (state.get('isStreaming') is not False or state.get('isCompacting') is not False
                or state.get('pendingMessageCount') != 0):
            raise SessionFailure('session not demonstrably idle')
        return state

    def observe(self, entries):
        """Native finalized entries only; partial streaming updates never add charges."""
        judges = self.journal.setdefault('judge_receipts', {})
        for entry in entries:
            ident = entry.get('id')
            if not isinstance(ident, str) or not ident:
                raise SessionFailure('entry without stable ID')
            digest = _digest(entry)
            previous = self.journal['entry_hashes'].get(ident)
            if previous is not None and previous != digest:
                raise SessionFailure('persisted entry identity changed')
            self.journal['entry_hashes'][ident] = digest
            message = entry.get('message', {})
            kind = entry.get('type')
            if kind in ('usage', 'compaction', 'branch_summary'):
                usage = entry.get('usage')
            elif kind == 'message' and (message.get('role') == 'assistant' or 'usage' in message):
                usage = message.get('usage')
            elif kind == 'custom' and entry.get('customType') == 'chain-judge-result':
                data = entry.get('data')
                if not isinstance(data, dict) or not isinstance(data.get('call_id'), str) or not data['call_id']:
                    raise SessionFailure('judge receipt without call identity')
                call_id = data['call_id']
                if call_id in judges and judges[call_id] != entry:
                    raise SessionFailure('duplicate or changed judge receipt')
                judges[call_id] = entry
                self.journal['charges'][ident] = {'kind': 'judge', 'usage': data.get('usage'),
                    'call_id': call_id, 'provider': data.get('model', {}).get('provider'),
                    'model': data.get('model', {}).get('id')}
                continue
            else:
                continue
            self.journal['charges'][ident] = {'kind': kind, 'usage': usage,
                'operation_kind': entry.get('kind'),
                'provider': entry.get('provider', message.get('provider')),
                'model': entry.get('model', message.get('model')),
                'response_model': entry.get('responseModel', message.get('responseModel'))}
        # Resolve explicit aliases only after observing the whole append-order page. A
        # missing/ambiguous native identity is not proof of billing equivalence or zero.
        alias_owners = {}
        for entry in judges.values():
            data, ident = entry['data'], entry['id']
            aliases = data.get('native_usage_ids', [])
            if aliases:
                if (not isinstance(aliases, list) or len(aliases) != 1
                        or not isinstance(aliases[0], str) or aliases[0] == ident):
                    raise SessionFailure('ambiguous judge usage alias')
                if aliases[0] in alias_owners and alias_owners[aliases[0]] != data['call_id']:
                    raise SessionFailure('native judge usage alias reused by another call')
                alias_owners[aliases[0]] = data['call_id']
                native = self.journal['charges'].get(aliases[0])
                if (native is None or native['kind'] == 'judge' or native['usage'] is None
                        or native['usage'] != data.get('usage')):
                    raise SessionFailure('judge native usage alias not observed/equal')
                self.journal['charges'].pop(ident, None)

    def sync(self):
        self._state(require_idle=False)
        options = {'since': self.journal['cursor']} if self.journal['cursor'] else {}
        data, _ = self._request('get_entries', **options)
        entries = data.get('entries')
        if not isinstance(entries, list):
            raise SessionFailure('missing entries')
        self.observe(entries)
        if entries:
            self.journal['cursor'] = entries[-1]['id']
        path = Path(self.journal['session_file'])
        if path.exists():
            self.journal['file_size'] = path.stat().st_size
            self.journal['file_prefix_sha256'] = _prefix(path, self.journal['file_size'])
        self._save()
        return entries

    def prompt(self, message):
        if not self._operation.acquire(blocking=False):
            raise SessionFailure('only one prompt can be active')
        try:
            if not self.journal['complete']:
                raise SessionFailure('unreconciled previous operation')
            self._state()
            self.journal['complete'] = False
            self._save()
            response, messages = self._request('prompt', message=message, wait_run=True)
            self._state()
            entries = self.sync()
            if response['disposition'] == 'handled' and not entries:
                raise SessionFailure('handled command without specific output entry')
            final = messages[-1] if messages else None
            if response['disposition'] == 'started' and (final is None or final.get('stopReason') != 'stop'):
                raise SessionFailure('no finalized successful assistant output')
            text = ''.join(p['text'] for p in final.get('content', []) if p.get('type') == 'text') if final else None
            self.journal['complete'] = True
            self._save()
            return {'disposition': response['disposition'], 'text': text, 'entries': entries,
                    'entry_ids': [e['id'] for e in entries], 'session_id': self.session_id, 'pid': self.pid}
        except (SessionFailure, OSError, ValueError):
            self.journal['complete'] = False
            self.journal.setdefault('unknown_usage', []).append({'launch': self.launches,
                'operation': self._sequence, 'reason': 'unfinished or unreported operation'})
            try:
                self.sync()
            except (SessionFailure, OSError, ValueError):
                pass
            self._save()
            raise
        finally:
            self._operation.release()

    def resume(self, *, authorized=False, budget=False):
        if self.process.poll() is None or not authorized or not budget or not self.journal['complete']:
            raise SessionFailure('resume not admissible')
        try:
            if json.loads(self.journal_path.read_text(encoding='utf-8')) != self.journal:
                raise SessionFailure('checkpoint journal changed')
        except ValueError:
            raise SessionFailure('invalid checkpoint journal') from None
        path = Path(self.journal['session_file'])
        size = self.journal['file_size']
        if not path.exists() or _prefix(path, size) != self.journal['file_prefix_sha256']:
            raise SessionFailure('checkpoint session file changed')
        self.close()
        self._start(self.journal['session_file'])
        try:
            self._state()
            self.sync()
        except BaseException:
            self.journal['complete'] = False
            self._save()
            self.close()
            raise

    def close(self):
        if not hasattr(self, 'process'):
            return
        if getattr(self, '_writer', None) and self._writer.is_alive():
            self.process.kill()
            self.process.wait(timeout=5)
            self._writer.join(timeout=5)
            self.journal['complete'] = False
        if not self.process.stdin.closed:
            try:
                self.process.stdin.close()
            except OSError:
                self.journal['complete'] = False
        try:
            self.process.wait(timeout=min(self.timeout, 5))
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=5)
            self.journal['complete'] = False
        for reader in getattr(self, '_readers', []):
            reader.join(timeout=5)
        self.process.stdout.close()
        self.process.stderr.close()
        self.journal['closed'] = True
        self._save()
