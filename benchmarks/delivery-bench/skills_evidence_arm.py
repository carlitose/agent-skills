"""Separately named cell adapter: same transport, accounting and inherited request boundary."""
from pathlib import Path

from persistent_arm import BudgetedSession, PersistentCell
from skills_evidence_controller import SkillsEvidenceController


class SkillsEvidenceCell(PersistentCell):
    def __init__(self, original, project, store, session, decisions, budget, *, coverage_question,
                 risk_question=None, test_timeout=600):
        self.project, self.store = Path(project), Path(store)
        self.session, self.budget = session, budget
        self.owner = SkillsEvidenceController(
            original, project, store, BudgetedSession(session, budget), decisions,
            coverage_question=coverage_question, risk_question=risk_question, test_timeout=test_timeout)
