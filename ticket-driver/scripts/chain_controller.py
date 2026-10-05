"""Opt-in local chain boundary. Not a folder scheduler or a release authority."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import time

from autopilot.candidate_contract import semantic_candidate
from autopilot.command_capture import CaptureFailure, capture_command
from autopilot.ticket_contract import parse_ticket_markdown, normalize_ticket_envelope, serialize_ticket_markdown
from arbiter import classify, Unavailable, isolated_key
from cascade import _judge_answer
from findings import parse_findings
from function_diff import changed_functions


class ChainGate(RuntimeError):
    pass


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':')).encode()).hexdigest()


def _save(path, value):
    raw = (json.dumps({'body': value, 'sha256': digest(value)}, ensure_ascii=False) + '\n').encode()
    pending = path.with_suffix('.pending')
    with pending.open('wb') as stream:
        stream.write(raw)
        stream.flush()
        __import__('os').fsync(stream.fileno())
    pending.replace(path)


def _load(path):
    try:
        wrapper = json.loads(path.read_text(encoding='utf-8'))
        if wrapper['sha256'] != digest(wrapper['body']):
            raise ValueError()
        return wrapper['body']
    except (OSError, KeyError, TypeError, ValueError):
        raise ChainGate('checkpoint incomplete or changed') from None


class DecisionEngine:
    """Trusted caller supplies separate recipient permissions and observed transport ports."""
    def __init__(self, path, policy, *, permits, budget, jev=None, judge=None, sleep=time.sleep):
        if type(budget) is not int or budget < 0:
            raise ChainGate('explicit nonnegative call budget required')
        self.path, self.policy = Path(path), dict(policy)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        expected = {'noul_low': .2, 'noul_high': .8, 'choice_min_confidence': .75,
                    'risk_score_high': 2.5, 'max_attempts': 3}
        if any(self.policy.get(k) != v for k, v in expected.items()):
            raise ChainGate('unconfirmed thresholds/retry policy')
        self.permits, self.jev, self.judge, self.sleep = permits, jev, judge, sleep
        self.state = _load(self.path) if self.path.exists() else {
            'policy_digest': digest(self.policy), 'budget': budget, 'calls': [], 'decisions': {}}
        if self.state['policy_digest'] != digest(self.policy):
            raise ChainGate('decision policy drift')
        _save(self.path, self.state)

    def _call(self, kind, request, port):
        if self.state['budget'] <= 0:
            raise ChainGate('global external-call budget exhausted')
        self.state['budget'] -= 1
        row = {'kind': kind, 'binding': request['binding'], 'usage': None, 'status': 'inflight'}
        self.state['calls'].append(row)
        _save(self.path, self.state)
        try:
            delivered = json.loads(json.dumps(request))
            response = port(delivered)
            if isinstance(response, dict):
                row['usage'] = response.get('usage')
            row['status'] = 'returned'
            return response if digest(delivered) == digest(request) else None
        except Exception:
            row['status'] = 'unavailable'
            return None
        finally:
            _save(self.path, self.state)

    def decide(self, ident, question, state, candidate, *, sufficient=True, risk=False):
        if _load(self.path) != self.state:
            raise ChainGate('decision checkpoint drift')
        candidate = semantic_candidate(candidate).as_dict()
        key = digest({'candidate': candidate, 'question_id': ident})
        binding = {'candidate_ref': candidate, 'question_id': ident,
                   'question_digest': digest(question), 'state_digest': digest(state),
                   'contract_digest': digest(self.policy), 'call_id': key}
        previous = self.state['decisions'].get(key)
        if previous:
            if previous['binding'] != binding:
                if question['type'] == 'noul' and previous['outcome'] == 'no':
                    return {**previous, 'reason': 'decided negative on same candidate; not bypassable'}
                return {'outcome': 'uncertain', 'reason': 'binding changed; reconcile', 'binding': binding}
            return previous
        # Persist reservation before any external side effect; interrupted calls never replay.
        result = {'outcome': 'uncertain', 'reason': 'inflight/unavailable', 'binding': binding}
        self.state['decisions'][key] = result
        _save(self.path, self.state)
        request = {'binding': binding, 'question_id': ident, 'question': question, 'state': state}
        request_bytes = len(json.dumps(request, ensure_ascii=False).encode())
        data_bound = request_bytes <= 65536
        if sufficient and data_bound and self.jev and self.permits('jev', binding) is True:
            for attempt in range(3):
                reply = self._call('jev', request, self.jev)
                if isinstance(reply, dict) and reply.get('http_status', 200) in (429, 529):
                    if attempt < 2:
                        self.sleep(min(.25 * 2**attempt, 1))
                        continue
                try:
                    if not isinstance(reply, dict) or reply.get('http_status', 200) != 200:
                        raise Unavailable('unavailable')
                    answer = reply['answers'][ident]
                    if answer.get('type') != question['type']:
                        raise Unavailable('type mismatch')
                    result['outcome'] = classify(answer, self.policy)['outcome']
                    result['reason'] = 'jev observed'
                except (Unavailable, KeyError, TypeError, ValueError):
                    result['reason'] = 'jev unavailable/malformed'
                break
        else:
            result['reason'] = (f'semantic-input-bound: {request_bytes} bytes > 65536'
                                if not data_bound else 'insufficient/bound/forbidden/unavailable')
        if (result['outcome'] == 'uncertain' and not risk and sufficient and data_bound
                and self.judge and self.permits('judge', binding) is True):
            reply = self._call('judge', request, self.judge)
            if (isinstance(reply, dict) and all(reply.get(k) == v for k, v in binding.items())
                    and reply.get('stopReason') == 'stop' and isinstance(reply.get('text'), str)):
                result['outcome'] = _judge_answer(question, reply['text'])
                result['reason'] = 'judge observed' if result['outcome'] != 'uncertain' else 'judge uncertain'
            else:
                result['reason'] = 'judge invalid/unavailable'
        _save(self.path, self.state)
        return result


class ChainController:
    """Run one explicit canonical ticket at a time in a caller-owned copy."""
    def __init__(self, original, worktree, store, session, decisions, *, coverage_question,
                 risk_question=None, test_timeout=600, max_output_bytes=8388608):
        self.original, self.root, self.store = map(lambda p: Path(p).resolve(), (original, worktree, store))
        if self.root == self.original or self.original in self.root.parents:
            raise ChainGate('separate owned copy required')
        if Path(self._git('rev-parse', '--show-toplevel')).resolve() != self.root:
            raise ChainGate('worktree root required')
        self.store.mkdir(parents=True, exist_ok=True)
        if self.store == self.root or self.root in self.store.parents:
            gitdir = Path(self._git('rev-parse', '--absolute-git-dir'))
            if gitdir not in self.store.parents:
                raise ChainGate('facts must be outside product tree or inside owned git dir')
        self.path = self.store / 'checkpoint.json'
        self.session, self.decisions, self.coverage_question = session, decisions, coverage_question
        self.risk_question, self.test_timeout, self.max_output_bytes = risk_question, test_timeout, max_output_bytes
        self.base = self._git('rev-parse', 'HEAD')
        self.identity = {'pid': session.pid, 'session_id': session.session_id}
        self.state = _load(self.path) if self.path.exists() else {'base': self.base,
            'valid_tree': self._git('write-tree'), 'tickets': {}, 'expected': self._fingerprint(),
            'original': self._fingerprint(self.original), 'inflight': None, 'gate': None, 'session': self.identity}
        self._admit()
        _save(self.path, self.state)

    def _git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.root), *args]).decode('utf-8').strip()

    def _files(self, root=None):
        root = root or self.root
        raw = subprocess.check_output(['git', '-C', str(root), 'ls-files', '-z', '--cached', '--others', '--exclude-standard'])
        return sorted(set(x.decode('utf-8') for x in raw.split(b'\0') if x))

    def _cache(self, name, root=None):
        root = root or self.root
        parts = Path(name).parts
        return any(part in {'__pycache__', '.pytest_cache', '.ruff_cache', '.mypy_cache'}
                   and root.joinpath(*parts[:i+1]).is_dir() for i, part in enumerate(parts))

    def _fingerprint(self, root=None):
        root = root or self.root
        # Only real tool cache directories are excluded, never similarly named files.
        values = {}
        for name in self._files(root):
            path = root / name
            if self._cache(name, root):
                continue
            values[name] = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        return digest(values)

    def _admit(self):
        if self.decisions.state['budget'] <= 0:
            raise ChainGate('global external-call budget exhausted')
        if self.state['gate'] or self.state['inflight']:
            raise ChainGate('unreconciled global state')
        if self.state['session'] != self.identity or self.identity != {
                'pid': self.session.pid, 'session_id': self.session.session_id}:
            raise ChainGate('session resource changed; reconcile death/checkpoint/permit/budget')
        if self._git('rev-parse', 'HEAD') != self.state['base']:
            raise ChainGate('base drift; preserve/reconcile')
        if self._fingerprint() != self.state['expected'] or self._fingerprint(self.original) != self.state['original']:
            raise ChainGate('product/original mutation; preserve/reconcile')
        if self.path.exists() and _load(self.path) != self.state:
            raise ChainGate('controller checkpoint changed')

    def _turn(self, role, ticket, *, readonly=False, **facts):
        before = self._fingerprint()
        self.state['inflight'] = {'role': role, 'ticket': ticket['envelope']['ticket_id']}
        _save(self.path, self.state)
        result = self.session.prompt(json.dumps({'role': role, 'ticket': ticket, **facts}, ensure_ascii=False))
        after = self._fingerprint()
        if result.get('pid') != self.identity['pid'] or result.get('session_id') != self.identity['session_id']:
            self.state['gate'] = 'session changed during turn'
            _save(self.path, self.state)
            raise ChainGate(self.state['gate'])
        if self._fingerprint(self.original) != self.state['original'] or (readonly and after != before):
            self.state['gate'] = 'read-only/original mutation'
            _save(self.path, self.state)
            raise ChainGate(self.state['gate'])
        self.state['inflight'] = None
        self.state['expected'] = after
        _save(self.path, self.state)
        return result.get('text') or ''

    def _freeze(self, ticket, paths, directories=()):
        def allowed(name):
            return name in paths or any(folder == '.' or name.startswith(folder.rstrip('/') + '/')
                                        for folder in directories)
        unexpected = {n for n in self._git('diff', '--name-only', self.state['valid_tree']).splitlines()
                      if not self._cache(n) and not allowed(n)}
        untracked = {n for n in self._git('ls-files', '--others', '--exclude-standard').splitlines()
                     if not self._cache(n) and not allowed(n)}
        if unexpected or untracked:
            raise ChainGate('unclassified mutation outside ticket scope')
        self._git('add', '-A', '--', *paths)
        return semantic_candidate({'contract_version': 2, 'base_tree_oid': self.state['valid_tree'],
            'candidate_tree_oid': self._git('write-tree'), 'ticket_digest': ticket['digest']}).as_dict()

    def _tests(self, commands, cf, row):
        receipts = []
        before = self._fingerprint()
        for argv in commands:
            started = time.monotonic()
            try:
                with isolated_key():
                    out, err, code = capture_command(list(argv), cwd=self.root,
                        timeout_seconds=self.test_timeout, max_output_bytes=self.max_output_bytes)
                failure, capture_started, cleanup_issues = None, True, 0
            except CaptureFailure as error:
                out, err, code, failure = b'', error.stderr, None, error.reason
                capture_started, cleanup_issues = error.started, len(error.cleanup_issues)
            record = {'candidate_ref': cf, 'argv': argv, 'exit_code': code, 'failure': failure,
                'stdout': out.decode('utf-8', errors='replace'), 'stderr': err.decode('utf-8', errors='replace'),
                'capture_started': capture_started, 'cleanup_issues': cleanup_issues,
                'elapsed_seconds': time.monotonic() - started}
            path = self.store / ('test-' + str(len(list(self.store.glob('test-*.json')))) + '.json')
            path.write_bytes((json.dumps(record, ensure_ascii=False) + '\n').encode())
            receipts.append({'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), **record})
        if before != self._fingerprint():
            raise ChainGate('tests mutated product; evidence stale')
        row['receipts'] = receipts
        return bool(receipts) and all(r['exit_code'] == 0 and not r['failure'] for r in receipts)

    def _test_observations(self, receipts):
        """Bounded public previews; complete attributed receipts remain in the owned store."""
        preview_bytes = 8192
        while True:
            rows = []
            for receipt in receipts:
                record = {key: receipt[key] for key in
                          ('candidate_ref', 'argv', 'exit_code', 'failure', 'path', 'sha256')}
                for stream in ('stdout', 'stderr'):
                    raw = receipt[stream].encode('utf-8')
                    record[stream] = raw[-preview_bytes:].decode('utf-8', errors='replace')
                    record[stream + '_truncated'] = len(raw) > preview_bytes
                rows.append(record)
            observation = {'receipts': rows, 'preview': True,
                           'complete_output': 'read the exact public receipt path/hash if needed'}
            if len(json.dumps(observation, ensure_ascii=False).encode()) <= 32768:
                return observation
            if preview_bytes == 1:
                raise ChainGate('public test observation metadata exceeds intake bound')
            preview_bytes = max(1, preview_bytes // 2)

    def _gate(self, row, kind, reason, *, human=False):
        row.update(status='human-gated' if human else 'infrastructure-gated',
                   failure_kind=kind, failure_reason=reason)
        self.state['gate'] = self.state['gate'] or reason
        _save(self.path, self.state)

    def _candidate_diff(self, cf, row):
        raw = subprocess.check_output(['git', '-C', str(self.root), 'diff', '--no-ext-diff',
                                       '--no-color', cf['base_tree_oid'], cf['candidate_tree_oid']])
        path = self.store / ('diff-' + digest(cf) + '.patch')
        if path.exists() and path.read_bytes() != raw:
            raise ChainGate('frozen diff artifact changed')
        if not path.exists():
            path.write_bytes(raw)
        row['diff_artifact'] = {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(),
                                'candidate_ref': cf}
        try:
            return raw.decode('utf-8')
        except UnicodeDecodeError:
            self._gate(row, 'diff-encoding', 'frozen diff is not UTF-8; raw evidence preserved')
            return None

    def _attempt(self, ticket, paths, directories, commands, row):
        self._turn('builder' if row['failures'] == 0 else 'fix', ticket,
                   failures=row['failures'], prior_findings=row.get('findings'),
                   prior_review_prose=row.get('review_prose'), allowed_paths=paths,
                   test_observations=self._test_observations(row.get('receipts', [])))
        cf = self._freeze(ticket, paths, directories)
        row['candidate'] = cf
        passed = self._tests(commands, cf, row)
        if any(r['failure'] and (r['failure'] != 'timeout' or not r['capture_started']
                                 or r['cleanup_issues']) for r in row['receipts']):
            self._gate(row, 'test-capture', 'public test process/capture unresolved; receipt preserved')
            return 'gated'
        selected, unsupported = changed_functions(self.root, semantic_candidate(cf))
        high = []
        for function in selected:
            outcome = 'uncertain'
            if self.risk_question:
                outcome = self.decisions.decide('risk:' + function['path'] + ':' + function['function'],
                    self.risk_question, function, cf, risk=True)['outcome']
            if outcome == 'uncertain' or not isinstance(outcome, (float, int)) or outcome >= 2.5:
                high.append(function)
        prose = self._turn('review', ticket, readonly=True, candidate=cf,
            directed=high, unsupported=unsupported, global_scope_required=True,
            test_observations=self._test_observations(row['receipts']))
        row['review_prose'] = prose
        row['findings'] = parse_findings(prose, any_extension=True)
        # Known public failure needs the normal fix path, not review-format clarification.
        # With green tests, an unresolved review remains a gate; never relabel its prose.
        if row['findings']['state'] == 'unparsed' and passed:
            self._gate(row, 'review-format', 'review format unresolved; original prose preserved', human=True)
            return 'gated'
        # Parsed findings are model claims, not observed acceptance failures.
        # Explicit blockers remain a veto; other findings enter semantic adjudication.
        review_allows_decision = not any(f['severity'] == 'blocker'
                                        for f in row['findings']['findings'])
        eligible = passed and review_allows_decision
        diff = self._candidate_diff(cf, row)
        if diff is None:
            return 'gated'
        decision = self.decisions.decide('coverage', self.coverage_question,
            {'ticket': ticket, 'candidate': cf,
             'test_observations': self._test_observations(row['receipts']),
             'review': prose, 'diff': diff}, cf, sufficient=eligible)
        if self._fingerprint() != self.state['expected']:
            raise ChainGate('decision callback mutated candidate')
        if eligible and decision['outcome'] == 'yes':
            row['status'] = 'completed-local'
            self.state['valid_tree'] = cf['candidate_tree_oid']
            _save(self.path, self.state)
            return 'completed'
        if decision['outcome'] == 'uncertain' and eligible:
            self._turn('analysis', ticket, readonly=True, decision=decision)
            self._gate(row, 'coverage-uncertain', decision['reason'], human=True)
            return 'gated'
        return 'quality-failure'

    def _restore(self, row):
        # Snapshot every product file before touching ONLY the owned copy.
        archive = self.store / ('failed-' + digest(row['ticket'])[:16])
        archive.mkdir(exist_ok=True)
        names = self._files()
        for name in names:
            src = self.root / name
            if src.is_file():
                dst = archive / name
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(src.read_bytes())
        row['archive'] = str(archive)
        wanted = set(self._git('ls-tree', '-r', '--name-only', self.state['valid_tree']).splitlines())
        self._git('restore', '--source=' + self.state['valid_tree'], '--staged', '--worktree', '--', *sorted(wanted))
        for name in set(names) - wanted:
            path = self.root / name
            if path.is_file():
                path.unlink()
            self._git('rm', '--cached', '--ignore-unmatch', '--', name)
        self.state['expected'] = self._fingerprint()
        _save(self.path, self.state)

    def run_ticket(self, markdown, paths, commands):
        self._admit()
        parsed = parse_ticket_markdown(markdown)
        envelope = normalize_ticket_envelope(parsed.envelope)
        if serialize_ticket_markdown(envelope, parsed.body) != markdown:
            raise ChainGate('canonical ticket serialization required')
        ident = envelope['ticket_id']
        ticket = {'envelope': envelope, 'body': parsed.body,
                  'digest': hashlib.sha256(markdown.encode('utf-8')).hexdigest()}
        row = self.state['tickets'].get(ident)
        if row and row['ticket'] != ticket:
            raise ChainGate('ticket body/envelope changed; reconcile')
        if row and row['status'] in ('completed-local', 'failed'):
            return row
        if any(self.state['tickets'].get(dep, {}).get('status') != 'completed-local' for dep in envelope['blocked_by']):
            return {'status': 'dependency-blocked', 'ticket': ticket}
        if not paths or not commands or any(Path(p).is_absolute() or '..' in Path(p).parts or p.startswith('.git') for p in paths):
            raise ChainGate('literal owned scope and process test commands required')
        paths = [Path(p).as_posix() for p in paths]
        directories = [p for p in paths if (self.root / p).is_dir()]
        if any(not (self.root / p).resolve().is_relative_to(self.root) for p in paths):
            raise ChainGate('scope escapes owned copy')
        failed = [r for r in self.state['tickets'].values() if r['status'] == 'failed' and not r.get('restored')]
        for prior in failed:
            self._restore(prior)
            prior['restored'] = True
        row = row or {'ticket': ticket, 'failures': 0, 'status': 'pending', 'archive': None}
        self.state['tickets'][ident] = row
        while row['failures'] < 3:
            try:
                outcome = self._attempt(ticket, paths, directories, commands, row)
            except Exception as error:
                # Preserve the original exception for the caller, but never persist its secret-bearing text.
                self._gate(row, 'controller-exception', 'controller operation unavailable: ' + type(error).__name__)
                raise
            if outcome != 'quality-failure':
                return row
            row['failures'] += 1
            row['status'] = 'failed' if row['failures'] == 3 else 'fix-required'
            if row['status'] == 'failed':
                archive = self.store / ('failed-' + digest(ticket)[:16])
                archive.mkdir(exist_ok=True)
                for name in self._files():
                    src = self.root / name
                    if src.is_file():
                        dst = archive / name
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        dst.write_bytes(src.read_bytes())
                row['archive'] = str(archive)
            _save(self.path, self.state)
        return row
