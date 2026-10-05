"""Grounded skill-enabled candidate; same inherited semantic/process/budget vetoes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from autopilot.ticket_contract import parse_ticket_markdown, serialize_ticket_markdown
from chain_controller import ChainController, ChainGate, _load, _save
from skills_evidence_controller import SkillsEvidenceController
from persistent_arm import BudgetedSession, PersistentCell, ROLE_INSTRUCTIONS, native_costs

VARIANT = 'behavior-skills-v2'
SKILL = 'behavior-first'


def declared_checks(body, commands):
    """Literal public corpus conventions only; never interpret arbitrary model commands."""
    if not commands or not all(isinstance(c, (list, tuple)) and c for c in commands):
        raise ChainGate('owned base test profile required')
    required = [list(c) for c in commands]
    for action in ('lint', 'c89'):
        if 'python dev.py ' + action in body:
            argv = [commands[0][0], 'dev.py', action]
            if argv not in required:
                required.append(argv)
    return required


class SkillBudgetedSession(BudgetedSession):
    def prompt(self, message):
        role = json.loads(message).get('role')
        if role not in ROLE_INSTRUCTIONS:
            raise ChainGate('caller supplied unknown role')
        prefix = '/skill:' + SKILL + ' ' if role in ('builder', 'fix') else ''
        reservation = self.budget.reserve('pi', self.reservation_usd)
        try:
            return self.session.prompt(prefix + ROLE_INSTRUCTIONS[role] + '\n' + message)
        finally:
            self.budget.settle(reservation, native_costs(self.session, self.budget.state['charges']))


class BehaviorController(SkillsEvidenceController):
    def __init__(self, original, product, store, session, decisions, **options):
        checkpoint = Path(store) / 'checkpoint.json'
        if checkpoint.exists() and _load(checkpoint).get('variant') != VARIANT:
            raise ChainGate('separate behavior-skills checkpoint required')
        super().__init__(original, product, store, session, decisions, **options)
        self.state.setdefault('variant', VARIANT)
        self.state.setdefault('base_commands', None)
        self.state.setdefault('required_commands', [])
        _save(self.path, self.state)

    def run_ticket(self, markdown, paths, commands):
        self._admit()
        parsed = parse_ticket_markdown(markdown)
        if serialize_ticket_markdown(parsed.envelope, parsed.body) != markdown:
            raise ChainGate('canonical ticket serialization required')
        row = self.state['tickets'].get(parsed.envelope['ticket_id'])
        if row and row['ticket']['digest'] != hashlib.sha256(markdown.encode()).hexdigest():
            raise ChainGate('ticket changed; reconcile before profile mutation')
        base = [list(c) for c in commands]
        if self.state['base_commands'] is not None and base != self.state['base_commands']:
            raise ChainGate('owned base test profile changed; reconcile')
        if row and row['status'] in ('completed-local', 'failed'):
            return super().run_ticket(markdown, paths, self.state['required_commands'])
        if any(self.state['tickets'].get(dep, {}).get('status') != 'completed-local'
               for dep in parsed.envelope['blocked_by']):
            return super().run_ticket(markdown, paths, commands)
        required = declared_checks(parsed.body, commands)
        self.state['base_commands'] = base
        for argv in required:
            if argv not in self.state['required_commands']:
                self.state['required_commands'].append(argv)
        _save(self.path, self.state)
        return super().run_ticket(markdown, paths, self.state['required_commands'])

    def _turn(self, role, ticket, *, readonly=False, **facts):
        artifact = self._public_ticket(ticket)
        facts['public_ticket_artifact'] = artifact
        facts['required_public_commands'] = self.state['required_commands']
        facts['behavior_rule'] = ('Implement/test every public clause; stock-suite success alone is insufficient. '
                                 'No private data, skipped mandatory checks or invented rejection diagnosis.')
        if role == 'fix':
            facts['prior_coverage_decision'] = self.state['tickets'][ticket['envelope']['ticket_id']].get('coverage_feedback')
        # Full requirements are explicit each turn; optional artifact reads cannot lose the contract.
        text = ChainController._turn(self, role, ticket, readonly=readonly, **facts)
        self._verify_public_tickets()
        return text

    def _test_observations(self, receipts):
        observed = super()._test_observations(receipts)
        for row in observed['receipts']:
            for stream in ('stdout', 'stderr'):
                if stream not in row:
                    continue
                raw = row[stream].encode('utf-8')
                row[stream] = raw[-2048:].decode('utf-8', errors='ignore')
                row[stream + '_truncated'] = row[stream + '_truncated'] or len(raw) > 2048
        return observed


class BehaviorCell(PersistentCell):
    def __init__(self, original, project, store, session, decisions, budget, *, coverage_question,
                 risk_question=None, test_timeout=600):
        self.project, self.store = Path(project), Path(store)
        self.session, self.budget = session, budget
        self.owner = BehaviorController(original, project, store, SkillBudgetedSession(session, budget), decisions,
            coverage_question=coverage_question, risk_question=risk_question, test_timeout=test_timeout)
