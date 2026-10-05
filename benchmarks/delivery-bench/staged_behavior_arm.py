"""Caller-owned request lifecycle; no scheduler, delegation or budget reset."""
import hashlib
import json
from pathlib import Path

from behavior_skills import BehaviorCell, SkillBudgetedSession
from chain_controller import ChainGate, _save
from staged_behavior import StagedController
from persistent_arm import native_costs


def verified_ref(reference):
    try:
        name, expected = reference.rsplit('#sha256=', 1)
        path = Path(name)
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError()
        return path
    except (OSError, ValueError, AttributeError):
        raise ChainGate('hash-bound lifecycle mandate required') from None


def expanded_skill_turns(session):
    """Use the actual documented client journal field, not an invented attribute."""
    turns = 0
    for line in Path(session.journal['session_file']).read_text(encoding='utf-8').splitlines():
        message = json.loads(line).get('message', {})
        content = message.get('content', [])
        content = [{'type': 'text', 'text': content}] if isinstance(content, str) else content
        if message.get('role') == 'user':
            text = '\n'.join(p.get('text', '') for p in content if p.get('type') == 'text')
            turns += text.startswith('<skill name="behavior-first"')
    return turns


class StagedCell(BehaviorCell):
    def __init__(self, original, project, store, session, decisions, budget, *, coverage_question,
                 risk_question=None, test_timeout=600):
        self.project, self.store = Path(project), Path(store)
        self.session, self.budget = session, budget
        self.owner = StagedController(original, project, store, SkillBudgetedSession(session, budget), decisions,
            coverage_question=coverage_question, risk_question=risk_question, test_timeout=test_timeout)

    def begin_ticket_session(self, session, decisions, budget, *, actor, mandate_ref):
        self.owner._admit()
        if actor != 'human:user':
            raise ChainGate('covered human lifecycle authority required')
        mandate = verified_ref(mandate_ref).read_text(encoding='utf-8')
        if 'human:user' not in mandate or 'staged-context-v3' not in mandate:
            raise ChainGate('lifecycle not covered by supplied mandate')
        old = self.session
        if old.process.poll() != 0 or not old.journal['closed'] or not old.journal['complete'] or old.journal.get('unknown_usage'):
            raise ChainGate('previous native death/journal/usage unresolved')
        old_ref = str(old.journal_path) + '#sha256=' + hashlib.sha256(old.journal_path.read_bytes()).hexdigest()
        if json.loads(old.journal_path.read_bytes()) != old.journal:
            raise ChainGate('previous journal changed')
        if session.process.poll() is not None or session.cwd != old.cwd or session.journal['argv_digest'] != old.journal['argv_digest']:
            raise ChainGate('new native not alive or cwd/argv changed')
        budget._check()
        before, after = self.budget.state, budget.state
        if native_costs(old, before['charges']):
            raise ChainGate('previous closing native usage not settled')
        if (budget.path != self.budget.path or budget.authority_path != self.budget.authority_path
                or after['authority_sha256'] != before['authority_sha256'] or before['gate'] or after['gate']
                or after['calls'] != before['calls'] or any(c['status'] != 'observed' for c in after['calls'])
                or after['charges'] != before['charges'] or after['usd_estimate'] != before['usd_estimate']
                or after['semantic_calls'] != before['semantic_calls'] or after['launches'] != before['launches'] + 1
                or after['operator_costs'][:len(before['operator_costs'])] != before['operator_costs']):
            raise ChainGate('lifecycle financial/call provenance changed or unresolved')
        if decisions.path != self.owner.decisions.path or decisions.state != self.owner.decisions.state:
            raise ChainGate('decision accounting cannot reset across requests')
        epoch = {'previous': self.owner.identity.copy(), 'next': {'pid': session.pid, 'session_id': session.session_id},
                 'previous_journal_ref': old_ref, 'mandate_ref': mandate_ref, 'actor': actor,
                 'consumed_launches': after['launches'], 'semantic_calls': after['semantic_calls'],
                 'valid_tree': self.owner.state['valid_tree'], 'native_context': 'fresh-request'}
        self.owner.bind_session(SkillBudgetedSession(session, budget), decisions, epoch)
        self.session, self.budget = session, budget
        _save(self.store / ('epoch-' + str(len(self.owner.state['session_epochs'])) + '.json'), epoch)
        return epoch
