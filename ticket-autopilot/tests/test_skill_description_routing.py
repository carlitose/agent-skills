"""Skill descriptions must not collide, and confusable asks must reach the owning skill.

Pi lists every model-invocable skill by name and description, and the model picks one from that
list. Two near-identical descriptions make the pick a coin toss; a description without the words
a user says loses to a broader one. On 2026-11-13 this proxy ranked
`improve-codebase-architecture` first for "find refactoring opportunities", although
`codebase-improver` owns that trigger, and ranked the full-repository workflow first for a
bounded "deepen the modules in this package".

This is a lexical proxy for that choice: stemmed TF-IDF over name and description, ported from
the deterministic Tier-2 routing check of addyosmani/agent-skills (`scripts/run-evals.js`, MIT).
It cannot judge meaning. A failure usually means fix the description, not the case.
"""

from __future__ import annotations

import math
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
COLLISION_LIMIT = 0.5  # upstream's warning level: above it two descriptions read as one

# (user ask, skill that must win, confusable skill that must rank below it)
ROUTING = (
    ("audit the whole repository and reduce technical debt across the codebase",
     "codebase-improver", "improve-codebase-architecture"),
    ("find refactoring opportunities and make this more testable",
     "codebase-improver", "improve-codebase-architecture"),
    ("survey the payments module for architectural friction and write a refactor RFC",
     "improve-codebase-architecture", "codebase-improver"),
    ("suggest how to deepen the modules in this package",
     "improve-codebase-architecture", "codebase-improver"),
    ("review this pull request for regressions", "code-review", "qa-test-plan"),
    ("plan QA for this diff", "qa-test-plan", "code-review"),
    ("find the root cause of this bug", "diagnose", "triangulate-diagnosis"),
    ("cross-check this hard bug with independent diagnostic workers",
     "triangulate-diagnosis", "diagnose"),
    ("simplify this diff without changing behavior", "code-simplification", "code-review"),
    ("put this ticket on hold", "change-status-ticket", "execute-ticket"),
    ("break this spec into tickets", "to-tickets", "to-spec"),
    ("write a spec for this feature", "to-spec", "to-tickets"),
    ("execute this ticket", "execute-ticket", "ticket-autopilot"),
    ("drive the ticket folder AFK", "ticket-autopilot", "execute-ticket"),
)

STOP = frozenset((
    "a", "an", "and", "any", "are", "as", "at", "be", "before", "by", "for", "from", "in", "into",
    "is", "it", "its", "my", "need", "needs", "of", "on", "or", "our", "so", "that", "the", "them",
    "this", "to", "use", "want", "we", "when", "with", "you", "your", "help", "me", "i",
))
ALIASES = {
    "doc": "document", "docs": "document", "config": "configuration", "configs": "configuration",
    "auth": "authenticate", "authentication": "authenticate", "repo": "repository",
    "repos": "repository", "dep": "dependency", "deps": "dependency",
}


def stem(token: str) -> str:
    """Light suffix stripping, not a real stemmer; same rules as upstream."""
    if len(token) > 10 and re.search(r"ifications?$", token):
        token = re.sub(r"ications?$", "i", token)
    for suffix in ("ally", "ing", "ations", "ation", "ed", "es", "al"):
        if len(token) > len(suffix) + 3 and token.endswith(suffix):
            token = token[: -len(suffix)]
            break
    if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
        token = token[:-1]
    if len(token) > 4 and token.endswith("e"):
        token = token[:-1]
    if len(token) > 4 and token[-1] == token[-2] and token[-1] not in "aeiou":
        token = token[:-1]
    if len(token) > 3 and token.endswith("y"):
        token = token[:-1] + "i"
    return token


def tokenize(text: str) -> list[str]:
    words = re.split(r"[\s-]+", re.sub(r"[^a-z0-9\s-]", " ", text.lower()))
    return [stem(ALIASES.get(word, word)) for word in words if len(word) > 2 and word not in STOP]


def counts(tokens: list[str]) -> dict[str, int]:
    found: dict[str, int] = {}
    for token in tokens:
        found[token] = found.get(token, 0) + 1
    return found


def model_invocable(root: Path) -> dict[str, str]:
    """Name to description for every skill the model can see and select."""
    skills = {}
    for path in sorted(root.glob("*/SKILL.md")):
        front = path.read_text(encoding="utf-8").replace("\r\n", "\n").split("\n---", 1)[0]
        if re.search(r"(?m)^disable-model-invocation:\s*true\s*$", front):
            continue
        name = re.search(r"(?m)^name:\s*(.+)$", front)
        description = re.search(r"(?m)^description:\s*(.+)$", front)
        if name and description:
            skills[name[1].strip().strip("\"'")] = description[1].strip().strip("\"'")
    return skills


class Router:
    def __init__(self, skills: dict[str, str]) -> None:
        documents = {}
        for name, description in skills.items():
            name_tokens = tokenize(name.replace("-", " "))
            documents[name] = counts(name_tokens + name_tokens + tokenize(description))
        frequency: dict[str, int] = {}
        for document in documents.values():
            for term in document:
                frequency[term] = frequency.get(term, 0) + 1
        self._idf = {term: math.log(1 + len(documents) / (1 + df)) for term, df in frequency.items()}
        self._unseen = math.log(1 + len(documents))
        self.vectors = {name: self.vector(document) for name, document in documents.items()}

    def vector(self, document: dict[str, int]) -> dict[str, float]:
        return {term: f * self._idf.get(term, self._unseen) for term, f in document.items()}

    def rank(self, prompt: str) -> list[tuple[float, str]]:
        query = self.vector(counts(tokenize(prompt)))
        return sorted(((cosine(query, vector), name) for name, vector in self.vectors.items()), reverse=True)


def cosine(left: dict[str, float], right: dict[str, float]) -> float:
    dot = sum(weight * right.get(term, 0.0) for term, weight in left.items())
    norms = math.sqrt(sum(w * w for w in left.values())) * math.sqrt(sum(w * w for w in right.values()))
    return dot / norms if norms else 0.0


class SkillDescriptionRoutingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.skills = model_invocable(REPO_ROOT)
        self.router = Router(self.skills)

    def test_catalog_excludes_user_invoked_skills(self) -> None:
        self.assertIn("codebase-improver", self.skills)
        self.assertNotIn("retro", self.skills)

    def test_no_two_descriptions_collide(self) -> None:
        names = sorted(self.router.vectors)
        for index, left in enumerate(names):
            for right in names[index + 1:]:
                similarity = cosine(self.router.vectors[left], self.router.vectors[right])
                with self.subTest(pair=f"{left} <> {right}"):
                    self.assertLess(similarity, COLLISION_LIMIT)

    def test_confusable_asks_reach_their_owner(self) -> None:
        for prompt, owner, rival in ROUTING:
            with self.subTest(prompt=prompt):
                ranking = self.router.rank(prompt)
                order = [name for _, name in ranking]
                scores = {name: score for score, name in ranking}
                self.assertGreater(scores[owner], 0.0)
                self.assertLess(order.index(owner), order.index(rival), ranking[:3])
                self.assertLess(order.index(owner), 3, ranking[:3])

    def test_router_prefers_the_description_sharing_the_prompt_terms(self) -> None:
        router = Router({"alpha": "Plan causal QA checks", "beta": "Review a diff for regressions"})
        self.assertEqual("beta", router.rank("review this diff for regressions")[0][1])


if __name__ == "__main__":
    unittest.main()
