"""Bounded vertical writer phases; inherited final quality/retry/freeze owners."""
from pathlib import Path

from behavior_skills import BehaviorController
from chain_controller import ChainGate, _load, _save
from skills_evidence_controller import _CoverageFeedback

REVISION = 'staged-context-v3'


class StagedController(BehaviorController):
    def __init__(self, original, product, store, session, decisions, **options):
        path = Path(store) / 'checkpoint.json'
        if path.exists() and _load(path).get('revision') != REVISION:
            raise ChainGate('distinct staged-context checkpoint required')
        super().__init__(original, product, store, session, decisions, **options)
        self.state.setdefault('revision', REVISION)
        self.state.setdefault('session_epochs', [])
        _save(self.path, self.state)

    def _turn(self, role, ticket, *, readonly=False, **facts):
        if role not in ('builder', 'fix'):
            return super()._turn(role, ticket, readonly=readonly, **facts)
        plan = super()._turn('analysis', ticket, readonly=True, **facts,
            writer_stage='orient-readonly',
            stage_goal='Read code and full public contract. Return clause-to-interface/test checklist and a coherent first vertical implementation plan. Read-only: no edits or build/test commands that mutate project.')
        seed = super()._turn(role, ticket, **facts, writer_stage='vertical-seed', plan=plan,
            stage_goal='Implement/repair the first coherent public behavior with a discovered real test. This is an intermediate step, not final handoff: preserve coherent tested progress even if other clauses remain. Do not withdraw all work solely because the full task is large. No assertion/check weakening.')
        return super()._turn(role, ticket, **facts, writer_stage='complete-contract', plan=plan, prior_seed=seed,
            stage_goal='Complete every public clause and persistent requirement from the checklist. Run targeted behavior tests and required_public_commands. Preserve coherent progress, inspect actual failures, and do not claim stock-suite success proves new behavior. Return exact remaining blocker if any; normal owner freeze/test/review gates follow.')

    def bind_session(self, session, decisions, epoch):
        """Called only by validated lifecycle adapter, not a model or implicit identity swap."""
        self._admit()
        self._verify_public_tickets()
        if not self.state['tickets'] or any(r['status'] != 'completed-local' for r in self.state['tickets'].values()):
            raise ChainGate('session transfer requires completed ticket boundary')
        if self._git('write-tree') != self.state['valid_tree']:
            raise ChainGate('session transfer valid tree changed')
        identity = {'pid': session.pid, 'session_id': session.session_id}
        if epoch['previous'] != self.identity or epoch['next'] != identity or identity == self.identity:
            raise ChainGate('session transfer identity receipt mismatch')
        if not isinstance(decisions, _CoverageFeedback):
            decisions = _CoverageFeedback(decisions, self._record_coverage)
        self.session, self.decisions, self.identity = session, decisions, identity
        self.state['session'] = identity
        self.state['session_epochs'].append(epoch)
        _save(self.path, self.state)
        self._admit()
