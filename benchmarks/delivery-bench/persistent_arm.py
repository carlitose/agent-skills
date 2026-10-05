"""One explicit benchmark cell boundary. No folder scheduler or Git/provider delivery."""
from __future__ import annotations

import hashlib
import io
import json
import math
from pathlib import Path
import subprocess
import tarfile

from chain_controller import ChainController, ChainGate, DecisionEngine, _save, _load, digest
from chain_judge import ChainJudge
from chain_session import ChainSession
from arbiter import ask, Unavailable
from autopilot.ticket_contract import serialize_ticket_markdown


def validate_argv(argv, authority):
    expected = {'--mode': 'rpc', '--provider': authority['model']['provider'],
                '--model': authority['model']['id'], '--thinking': authority['model']['thinking']}
    for flag, value in expected.items():
        if argv.count(flag) != 1 or argv.index(flag) + 1 >= len(argv) or argv[argv.index(flag)+1] != value:
            raise ChainGate('native argv/model/thinking binding mismatch')
    if '--api-key' in argv:
        raise ChainGate('alternate inline credential forbidden')


class Budget:
    """Attributable estimates and reservations, not an invoice or provider-side spending cap."""
    def __init__(self, authority, path):
        self.authority_path, self.path = Path(authority), Path(path)
        try:
            self.authority = json.loads(self.authority_path.read_text(encoding='utf-8'))
            a = self.authority
            if (a['schema'] != 1 or a['authority_type'] != 'benchmark-only' or a['authorized_by'] != 'human:user'
                    or a['budget']['currency'] != 'EUR' or a['budget']['ceiling'] <= 0
                    or a['budget']['usd_per_eur'] <= 0):
                raise ValueError()
        except (OSError, ValueError, KeyError, TypeError):
            raise ChainGate('benchmark mandate/budget missing or invalid') from None
        self.ceiling = float(a['budget']['ceiling']) * float(a['budget']['usd_per_eur'])
        if not math.isfinite(self.ceiling):
            raise ChainGate('finite monetary ceiling required')
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.state = _load(self.path) if self.path.exists() else {
            'authority_sha256': hashlib.sha256(self.authority_path.read_bytes()).hexdigest(),
            'calls': [], 'charges': {}, 'usd_estimate': 0.0, 'launches': 0, 'semantic_calls': 0,
            'operator_costs': [], 'gate': None}
        self._check()
        _save(self.path, self.state)

    def _check(self):
        if hashlib.sha256(self.authority_path.read_bytes()).hexdigest() != self.state['authority_sha256']:
            raise ChainGate('authority drift; preserve original provenance and consumption')
        if self.path.exists() and _load(self.path) != self.state:
            raise ChainGate('budget checkpoint changed')

    def observe_operator_cost(self, usd_estimate, source):
        """Trusted caller supplies an attributable cumulative estimate; never invent a live zero."""
        self._check()
        if (not isinstance(source, str) or not source.strip()
                or (usd_estimate is not None and (type(usd_estimate) not in (int, float)
                    or not math.isfinite(usd_estimate) or usd_estimate < 0))):
            raise ChainGate('operator estimate/source invalid')
        observations = self.state.get('operator_costs', [])
        record = {'source': source, 'usd_estimate': usd_estimate}
        previous = next((r for r in observations if r['source'] == source), None)
        if previous is not None:
            if previous != record:
                raise ChainGate('operator observation identity changed')
            return
        known = [r['usd_estimate'] for r in observations if r['usd_estimate'] is not None]
        if usd_estimate is not None and known and usd_estimate < max(known):
            raise ChainGate('cumulative operator estimate cannot reset')
        self.state.setdefault('operator_costs', []).append(record)
        _save(self.path, self.state)

    def cost_report(self):
        """A combined estimate exists only with complete experimental and operator accounting."""
        observations = self.state.get('operator_costs', [])
        operator = observations[-1]['usd_estimate'] if observations else None
        unknown_experiment = any(r['status'] != 'observed' for r in self.state['calls'])
        experiment = None if unknown_experiment else self.state['usd_estimate']
        combined = None if experiment is None or operator is None else experiment + operator
        return {'experimental_estimate_usd': experiment,
                'priced_experimental_estimate_usd': self.state['usd_estimate'],
                'operator_estimate_usd': operator, 'combined_estimate_usd': combined,
                'remaining_estimate_usd': None if combined is None else self.ceiling - combined,
                'invoice_total_usd': None,
                'unreconciled': (['experimental usage'] if unknown_experiment else [])
                    + (['operator cost'] if operator is None else [])}

    def _financial_headroom(self):
        remaining = self.cost_report()['remaining_estimate_usd']
        if remaining is None:
            raise ChainGate('experimental/operator cost unreconciled; new spending stopped')
        return remaining

    def reserve(self, kind, upper_usd):
        self._check()
        if (self.state['gate'] or any(r['status'] == 'inflight' for r in self.state['calls'])
                or self.authority['permissions'].get(kind) is not True):
            raise ChainGate('budget/recipient/inflight gate')
        if not isinstance(upper_usd, (int, float)) or not math.isfinite(upper_usd) or upper_usd <= 0:
            raise ChainGate('explicit positive in-flight monetary reservation required')
        if upper_usd > self._financial_headroom():
            raise ChainGate('cumulative monetary budget exhausted')
        if kind in ('jev', 'judge'):
            if self.state['semantic_calls'] >= self.authority['limits']['max_semantic_calls']:
                raise ChainGate('semantic call budget exhausted')
            self.state['semantic_calls'] += 1
        ident = len(self.state['calls']) + 1
        self.state['calls'].append({'id': ident, 'kind': kind, 'reserved_usd': upper_usd,
                                    'status': 'inflight', 'sources': []})
        _save(self.path, self.state)
        return ident

    def settle(self, ident, observations):
        self._check()
        row = self.state['calls'][ident-1]
        if row['id'] != ident or row['status'] != 'inflight':
            raise ChainGate('reservation identity/status mismatch')
        unknown = not observations
        for value in observations:
            source = value['source']
            old = self.state['charges'].get(source)
            if old is not None and old != value:
                self.state['gate'] = 'charge identity changed'
                _save(self.path, self.state)
                raise ChainGate(self.state['gate'])
            self.state['charges'][source] = value
            row['sources'].append(source)
            price = value.get('usd_estimate')
            if not isinstance(price, (float, int)) or not math.isfinite(price) or price < 0:
                unknown = True
            elif old is None:
                self.state['usd_estimate'] += price
        row['status'] = 'unknown' if unknown else 'observed'
        if unknown:
            self.state['gate'] = 'unreported cost: reservation retained, new spending stopped'
        elif self.cost_report()['remaining_estimate_usd'] is None:
            self.state['gate'] = 'operator cost unreconciled; native usage preserved, new spending stopped'
        elif self.cost_report()['remaining_estimate_usd'] < 0:
            self.state['gate'] = 'combined observed estimates exceeded mandate ceiling'
        _save(self.path, self.state)
        if self.state['gate']:
            raise ChainGate(self.state['gate'])

    def _launch_limit(self):
        return max([self.authority['limits']['max_pi_launches']] +
                   [b['max_pi_launches'] for b in self.state.get('launch_capacity_bindings', [])])

    def renew_launch_capacity(self, *, actor, mandate_ref):
        """Caller attests a covered mandate; bind one next launch without resetting consumption."""
        self._check()
        if actor != 'human:user' or not isinstance(mandate_ref, str) or not mandate_ref.strip():
            raise ChainGate('explicit human actor and covered mandate reference required')
        if (self.state['gate'] or self.authority['permissions'].get('pi') is not True
                or any(r['status'] == 'inflight' for r in self.state['calls'])):
            raise ChainGate('launch budget/permission/inflight gate')
        if self._financial_headroom() <= 0:
            raise ChainGate('cumulative monetary budget exhausted')
        limit = self._launch_limit()
        bindings = self.state.get('launch_capacity_bindings', [])
        if self.state['launches'] < limit:
            return dict(bindings[-1]) if bindings else {'max_pi_launches': limit}
        binding = {'previous_limit': limit, 'max_pi_launches': self.state['launches'] + 1,
                   'actor': actor, 'mandate_ref': mandate_ref}
        self.state.setdefault('launch_capacity_bindings', []).append(binding)
        _save(self.path, self.state)
        return dict(binding)

    def admit_launch(self, argv):
        """Non-starting preflight shared by callers and the actual launch boundary."""
        self._check()
        if (self.state['gate'] or self.authority['permissions'].get('pi') is not True
                or any(r['status'] == 'inflight' for r in self.state['calls'])):
            raise ChainGate('launch budget/permission/inflight gate')
        validate_argv(argv, self.authority)
        if self._financial_headroom() <= 0:
            raise ChainGate('cumulative monetary budget exhausted')
        limit = self._launch_limit()
        if self.state['launches'] >= limit:
            raise ChainGate(f'native-launch-capacity: consumed {self.state["launches"]}, admitted limit {limit}')

    def launch(self, argv, *, cwd, store, timeout=5400):
        self.admit_launch(argv)
        self.state['launches'] += 1
        _save(self.path, self.state)
        try:
            return ChainSession(argv, cwd=cwd, store=store, timeout=timeout)
        except Exception:
            self.state['gate'] = 'failed native launch; reconcile retained session/process/usage facts'
            _save(self.path, self.state)
            raise


def native_costs(session, seen):
    observations = []
    for ident, value in session.journal['charges'].items():
        key = 'native:' + session.session_id + ':' + ident
        if key in seen:
            continue
        usage = value.get('usage')
        cost = usage.get('cost', {}).get('total') if isinstance(usage, dict) else None
        observations.append({'source': key, 'usage': usage, 'usd_estimate': cost})
    for operation in session.journal.get('unknown_usage', []):
        key = 'unknown-native:' + session.session_id + ':' + digest(operation)
        if key not in seen:
            observations.append({'source': key, 'usage': None, 'usd_estimate': None,
                                 'operation': operation})
    return observations


ROLE_INSTRUCTIONS = {
    'builder': 'Implement the supplied canonical ticket inside allowed_paths. The controller owns spec, '
        'tests, review and delivery. Do not start any runner/scheduler/driver or ask for model-generated '
        'metadata. Read product conventions. Write code and public tests, not hidden/oracle data.',
    'fix': 'Repair only this ticket according to supplied findings/test observations and allowed_paths. '
        'Do not reset failed attempts or change the test criteria. No delivery/runner/scheduler.',
    'review': 'Read-only review of directed/unsupported areas AND the entire ticket scope. Produce '
        'findings before any fix; never edit files or claim independence. If no finding, end with '
        'No findings. Otherwise use [blocker|should-fix|nit] path:line - concrete problem and evidence. '
        'Use a concrete relative file path, not a bare directory label. For directory-wide or missing-test '
        'issues, anchor the finding in the nearest existing file. Keep every finding on its own line. '
        'Ground each finding in the public ticket and product contract; distinguish required defects '
        'from optional improvements. Do not invent extra requirements or count severity as proof.',
    'analysis': 'Read-only shared analysis: explain uncertainty and the human gate. Do not approve, '
        'edit, perform delivery or call a replacement judge/runner.',
}


class BudgetedSession:
    def __init__(self, session, budget, *, reservation_usd=25):
        self.session, self.budget, self.reservation_usd = session, budget, reservation_usd

    @property
    def pid(self):
        return self.session.pid

    @property
    def session_id(self):
        return self.session.session_id

    def prompt(self, message):
        value = json.loads(message)
        if value.get('role') not in ROLE_INSTRUCTIONS:
            raise ChainGate('caller supplied unknown role')
        reservation = self.budget.reserve('pi', self.reservation_usd)
        try:
            return self.session.prompt(ROLE_INSTRUCTIONS[value['role']] + '\n' + message)
        finally:
            self.budget.settle(reservation, native_costs(self.session, self.budget.state['charges']))


def clone_product(original, target):
    """Clone a committed owned seed with LF at checkout, preserving any partial failure."""
    original, target = Path(original).resolve(), Path(target)
    if target.is_symlink():
        raise ChainGate('new separate clone destination required')
    target = target.resolve()
    if target.exists() or original == target or original in target.parents:
        raise ChainGate('new separate clone destination required')
    def git(root, *args):
        return subprocess.check_output(['git', '-c', 'core.autocrlf=false', '-c', 'core.eol=lf',
                                        '-C', str(root), *args], timeout=120).decode('utf-8').strip()
    if Path(git(original, 'rev-parse', '--show-toplevel')).resolve() != original:
        raise ChainGate('owned seed root required')
    if git(original, 'diff', '--name-only', 'HEAD') or git(original, 'ls-files', '--others', '--exclude-standard'):
        raise ChainGate('committed seed required; original never normalized implicitly')
    expected = git(original, 'rev-parse', 'HEAD^{tree}')
    subprocess.run(['git', '-c', 'core.autocrlf=false', '-c', 'core.eol=lf', 'clone', '-q',
                    '--no-hardlinks', str(original), str(target)], check=True, timeout=120)
    git(target, 'config', 'core.autocrlf', 'false')
    git(target, 'config', 'core.eol', 'lf')
    git(target, 'remote', 'remove', 'origin')
    git(target, 'add', '-A')
    if git(target, 'write-tree') != expected:
        raise ChainGate('materialized clone differs from seed; preserve and never launch')
    return expected


def snapshot_tree(project, tree, target):
    """A newly owned immutable product snapshot, never an overwrite or history mutation."""
    project, target = Path(project), Path(target)
    if target.exists():
        raise ChainGate('snapshot destination already exists; never replace evidence')
    raw = subprocess.check_output(['git', '-C', str(project), '-c', 'core.autocrlf=false',
                                   '-c', 'core.eol=lf', 'archive', tree], timeout=120)
    target.mkdir(parents=True)
    try:
        with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
            for member in archive:
                output = target / member.name
                if not output.resolve().is_relative_to(target.resolve()):
                    raise ValueError('archive path outside snapshot')
                if member.isdir():
                    output.mkdir(parents=True, exist_ok=True)
                elif member.isfile():
                    output.parent.mkdir(parents=True, exist_ok=True)
                    output.write_bytes(archive.extractfile(member).read())
                    output.chmod(member.mode & 0o777)
                elif member.issym():
                    if not (output.parent / member.linkname).resolve().is_relative_to(target.resolve()):
                        raise ValueError('archive link outside snapshot')
                    output.parent.mkdir(parents=True, exist_ok=True)
                    output.symlink_to(member.linkname)
                else:
                    raise ValueError('unsupported archive member')
    except Exception:
        raise ChainGate('snapshot extraction failed; preserve partial evidence') from None


def make_decisions(session, budget, path, policy, *, jev_ask=ask):
    """The caller's live recipients, with one debit/observation per transport attempt."""
    contract = dict(policy)
    grant = budget.authority
    model = {key: grant['model'][key] for key in ('provider', 'id')}
    judge = ChainJudge(session, contract, model=model, grant=lambda binding: {
        'authorized': grant['permissions'].get('judge') is True,
        'budget_calls': 1, 'max_tokens': 16384, 'reasoning': grant['model']['thinking']})

    def jev(request):
        reservation = budget.reserve('jev', 1)
        observations = []
        try:
            # DecisionEngine owns max-three retry accounting; ask does one HTTP attempt.
            answers, usage = jev_ask(request['state'], {request['question_id']: request['question']},
                                     {**contract, 'max_attempts': 1})
            observations = [{'source': 'jev:' + request['binding']['call_id'] + ':' + str(reservation),
                'usage': usage, 'usd_estimate': usage['input_tokens'] * 0.042e-6}]
            return {'answers': answers, 'usage': usage}
        except Unavailable as error:
            tag = str(error)
            budget.state['calls'][reservation-1]['failure'] = (
                tag if len(tag) == 8 and tag.startswith('HTTP ') and tag[5:].isdigit()
                else 'jev unavailable')
            _save(budget.path, budget.state)
            raise
        finally:
            budget.settle(reservation, observations)

    def completion(request):
        reservation = budget.reserve('judge', 25)
        try:
            return judge(request)
        finally:
            budget.settle(reservation, native_costs(session, budget.state['charges']))

    return DecisionEngine(path, contract, permits=lambda kind, binding:
        grant['permissions'].get(kind) is True and not budget.state['gate'],
        budget=grant['limits']['max_semantic_calls'], jev=jev, judge=completion)


class PersistentCell:
    """Caller supplies exactly one owned cell, recipients and process-owned test commands."""
    def __init__(self, original, project, store, session, decisions, budget, *, coverage_question,
                 risk_question=None, test_timeout=600):
        self.project, self.store = Path(project), Path(store)
        self.session, self.budget = session, budget
        self.owner = ChainController(original, project, store, BudgetedSession(session, budget), decisions,
            coverage_question=coverage_question, risk_question=risk_question, test_timeout=test_timeout)

    def request(self, ident, body, commands, *, dependencies=()):
        markdown = serialize_ticket_markdown({'ticket_schema': 1, 'ticket_id': ident,
            'execution_mode': 'AFK', 'blocked_by': list(dependencies)}, body)
        row = self.owner.run_ticket(markdown, ['.'], commands)
        snapshot = self.store / 'snapshots' / ident
        # The delivered snapshot is last VALID tree, not an uncertain builder candidate.
        snapshot_tree(self.project, self.owner.state['valid_tree'], snapshot)
        result = {'ticket': ident, 'status': row['status'], 'candidate_ref': row.get('candidate'),
            'delivered_tree': self.owner.state['valid_tree'], 'snapshot': str(snapshot),
            'snapshot_id': digest({'ticket': ident, 'tree': self.owner.state['valid_tree']}),
            'pid': self.session.pid, 'session_id': self.session.session_id,
            'launches': self.session.launches, 'budget_estimated_usd': self.budget.state['usd_estimate'],
            'cost_report': self.budget.cost_report()}
        _save(self.store / ('request-' + ident + '.json'), result)
        return result
