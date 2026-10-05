"""No skill may tell the agent to run a user-invoked skill by itself.

A skill with ``disable-model-invocation: true`` is hidden from the model: only the human can
start it. An instruction in another skill such as "then use the handoff skill" can never work.
The guard reads each sentence that names a user-invoked skill and flags it when the sentence
asks for it (use, run, invoke, load, call, follow, hand off or route to), unless the sentence
asks the human to run it or negates the use.
"""

from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
HIDDEN = re.compile(r"(?m)^disable-model-invocation:\s*true\s*$")
INVOKE = re.compile(
    r"\b(use|run|invoke|load|call|follow|hand(?:s)? off to|route(?:s)? to)\b", re.IGNORECASE
)
ALLOWED = re.compile(
    r"\b(ask|tell|let)s? the (user|human)\b|\bthe (user|human) (runs?|types?)\b|\bnot\b|\bnever\b",
    re.IGNORECASE,
)
SENTENCE = re.compile(r"(?<=[.!?])\s+")


def user_invoked_skills(root: Path) -> set[str]:
    return {
        skill.parent.name
        for skill in root.glob("*/SKILL.md")
        if HIDDEN.search(skill.read_text(encoding="utf-8").split("\n---", 1)[0])
    }


def instruction_files(root: Path) -> list[Path]:
    return sorted([*root.glob("*/SKILL.md"), *root.glob("*/references/*.md")])


def violations(root: Path) -> list[str]:
    hidden = user_invoked_skills(root)
    found = []
    for path in instruction_files(root):
        owner = path.relative_to(root).parts[0]
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for sentence in SENTENCE.split(line):
                for name in sorted(hidden - {owner}):
                    pattern = rf"\(\.\./{re.escape(name)}/SKILL\.md\)|`/?{re.escape(name)}`"
                    if (
                        re.search(pattern, sentence)
                        and INVOKE.search(sentence)
                        and not ALLOWED.search(sentence)
                    ):
                        found.append(f"{path.relative_to(root).as_posix()}:{number}: {name}")
    return found


class UserInvokedSkillGuardTests(unittest.TestCase):
    def test_repository_skills_never_call_a_user_invoked_skill(self) -> None:
        self.assertIn("handoff", user_invoked_skills(REPO_ROOT))
        self.assertEqual([], violations(REPO_ROOT))

    def test_guard_flags_an_instruction_and_allows_human_or_negated_mentions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name, front in (("handoff", "disable-model-invocation: true\n"), ("caller", "")):
                (root / name).mkdir()
                (root / name / "SKILL.md").write_bytes(
                    f"---\nname: {name}\n{front}---\n".encode()
                )
            caller = root / "caller" / "SKILL.md"
            caller.write_bytes(
                b"---\nname: caller\n---\n"
                b"Then use the [handoff](../handoff/SKILL.md) skill.\n"
                b"Ask the user to run `/handoff` when they want a transfer.\n"
                b"Do not use the [handoff](../handoff/SKILL.md) skill as a context channel.\n"
                b"The [handoff](../handoff/SKILL.md) skill bridges human sessions.\n"
                b"Done. Finally, run `handoff` for the next session.\n"
            )

            self.assertEqual(
                ["caller/SKILL.md:4: handoff", "caller/SKILL.md:8: handoff"],
                violations(root),
            )


if __name__ == "__main__":
    unittest.main()
