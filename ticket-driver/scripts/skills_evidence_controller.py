"""Additive skills-oriented evidence lane; historical quality policy is unchanged."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from autopilot.ticket_contract import serialize_ticket_markdown
from chain_controller import ChainController, ChainGate, _load, _save

PROTOCOL = 'skills-evidence-v1'
IMPLEMENTATION = (
    'Use inline implementation, public behavior tests and focused refactoring for this '
    'already-canonical ticket. Add tests exercising the requested new behavior, not only '
    'the old suite. Do not regenerate spec/tickets, delegate, schedule, launch children, '
    'deliver Git changes, alter controller facts or declare acceptance. The caller owns '
    'frozen proofs, formal review and semantic coverage. A rejection reason is only what '
    'was observed: do not invent a diagnosis or use private oracle data.'
)


class _CoverageFeedback:
    """Observe the existing decision capability without replacing its policy or budget."""
    def __init__(self, engine, record):
        self.engine, self.record = engine, record

    @property
    def path(self):
        return self.engine.path

    @property
    def state(self):
        return self.engine.state

    def decide(self, ident, question, state, candidate, **options):
        result = self.engine.decide(ident, question, state, candidate, **options)
        if ident == 'coverage':
            self.record(candidate, result)
        return result


class SkillsEvidenceController(ChainController):
    """Compact public intake and explicit feedback; no test or semantic-proof caching."""
    def __init__(self, original, product, store, session, decisions, **options):
        checkpoint = Path(store) / 'checkpoint.json'
        if checkpoint.exists() and _load(checkpoint).get('protocol') != PROTOCOL:
            raise ChainGate('separate skills evidence checkpoint required')
        observed = _CoverageFeedback(decisions, self._record_coverage)
        super().__init__(original, product, store, session, observed, **options)
        self.state.setdefault('protocol', PROTOCOL)
        self.state.setdefault('public_tickets', {})
        self._verify_public_tickets()
        _save(self.path, self.state)

    def _verify_public_tickets(self):
        for ticket_digest, artifact in self.state['public_tickets'].items():
            path = Path(artifact['path'])
            if (path.parent != self.store or not path.is_file()
                    or hashlib.sha256(path.read_bytes()).hexdigest() != ticket_digest
                    or artifact['sha256'] != ticket_digest):
                raise ChainGate('public ticket artifact missing or changed; reconcile')

    def _public_ticket(self, ticket):
        raw = serialize_ticket_markdown(ticket['envelope'], ticket['body']).encode('utf-8')
        sha = hashlib.sha256(raw).hexdigest()
        if sha != ticket['digest']:
            raise ChainGate('canonical public ticket digest mismatch')
        self._verify_public_tickets()
        if sha not in self.state['public_tickets']:
            path = self.store / ('ticket-' + sha + '.md')
            if path.exists() and path.read_bytes() != raw:
                raise ChainGate('public ticket artifact changed; never overwrite')
            if not path.exists():
                path.write_bytes(raw)
            self.state['public_tickets'][sha] = {'path': str(path), 'sha256': sha}
            _save(self.path, self.state)
        return dict(self.state['public_tickets'][sha])

    def _record_coverage(self, candidate, decision):
        for row in self.state['tickets'].values():
            if row['ticket']['digest'] == candidate['ticket_digest']:
                row['coverage_feedback'] = json.loads(json.dumps({
                    'outcome': decision['outcome'], 'reason': decision['reason'],
                    'binding': decision['binding']}))
                _save(self.path, self.state)
                return
        raise ChainGate('coverage feedback has no owned ticket')

    def _turn(self, role, ticket, *, readonly=False, **facts):
        artifact = self._public_ticket(ticket)
        facts['public_ticket_artifact'] = artifact
        facts['ticket_access'] = 'Read this exact public Markdown artifact when full requirements are needed.'
        if role in ('builder', 'fix'):
            facts['implementation_lane'] = IMPLEMENTATION
        if role == 'fix':
            row = self.state['tickets'][ticket['envelope']['ticket_id']]
            facts['prior_coverage_decision'] = row.get('coverage_feedback')
        # Never rely on session memory alone: the complete immutable ticket stays readable.
        intake = ticket if role == 'builder' else {
            'envelope': ticket['envelope'], 'digest': ticket['digest'], 'body_omitted': True}
        text = super()._turn(role, intake, readonly=readonly, **facts)
        self._verify_public_tickets()
        return text

    def _test_observations(self, receipts):
        if not receipts or any(r['exit_code'] != 0 or r['failure'] for r in receipts):
            return super()._test_observations(receipts)
        rows = [{key: receipt[key] for key in
                 ('candidate_ref', 'argv', 'exit_code', 'failure', 'path', 'sha256')}
                for receipt in receipts]
        observation = {'receipts': rows, 'preview': True, 'successful_output_omitted': True,
                       'complete_output': 'read the exact public receipt path/hash if needed'}
        if len(json.dumps(observation, ensure_ascii=False).encode('utf-8')) > 32768:
            raise ChainGate('public test observation metadata exceeds intake bound')
        return observation
