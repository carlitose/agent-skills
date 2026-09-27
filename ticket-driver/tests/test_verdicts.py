"""The fresh judge's verdict comes from the question registry and only from its final line."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
sys.path.insert(0, str(HERE.parents[1] / "ticket-autopilot" / "scripts"))
from arbiter import questions  # noqa: E402
from cascade import _judge_answer, render_verdicts, verdicts  # noqa: E402

REGISTRY, _ = questions(HERE.parent)
ESCALATING = ("review.findings_block", "review.scope_complete", "qa.evidence_class",
              "verify.claim_supported", "retry.recoverable")


class VerdictVocabularyTests(unittest.TestCase):
    def test_every_escalating_question_lists_each_allowed_answer_and_its_criterion(self):
        for ident in ESCALATING:
            with self.subTest(question=ident):
                question = REGISTRY[ident]
                rendered = render_verdicts(question)
                values = ["yes", "no"] if question["type"] == "noul" else list(question["criteria"])
                self.assertEqual(sorted(verdicts(question)), sorted(values))
                for value in [*values, "undetermined"]:
                    self.assertIn(f"`Answer: {value}`", rendered)
                for criterion in question["criteria"].values():
                    self.assertIn(criterion, rendered)

    def test_noul_answers_follow_the_arbiter_outcome_names(self):
        self.assertEqual(verdicts(REGISTRY["review.findings_block"]), {"yes": "yes", "no": "no"})
        self.assertIn("Concrete correctness", render_verdicts(REGISTRY["review.findings_block"]).split("`Answer: no`")[0])

    def test_score_questions_are_never_decided_by_prose(self):
        self.assertEqual(verdicts(REGISTRY["risk.semantic_change"]), {})
        self.assertEqual(_judge_answer(REGISTRY["risk.semantic_change"], "Answer: 3\n"), "uncertain")


class FinalAnswerParsingTests(unittest.TestCase):
    def answer(self, ident, text):
        return _judge_answer(REGISTRY[ident], text)

    def test_single_final_answer_line_decides(self):
        self.assertEqual(self.answer("qa.evidence_class", "Mixed binaries.\n\nAnswer: integration\n"), "integration")
        self.assertEqual(self.answer("qa.evidence_class", "Answer: unknown"), "unknown")
        self.assertEqual(self.answer("retry.recoverable", "Answer: environment-failure."), "environment-failure")
        self.assertEqual(self.answer("review.scope_complete", "Prose.\n**Answer: No**  \n"), "no")
        self.assertEqual(self.answer("verify.claim_supported", "Prose.\n`Answer: yes`\n"), "yes")

    def test_every_other_ending_fails_closed(self):
        cases = {
            "no answer line": "No findings.\nThis blocks integration.\n",
            "quoted sentence only": 'The review says "No findings."\n',
            "answer not last": "Answer: no\nBut I am unsure.\n",
            "two answer lines": "Answer: no\nAnswer: no\n",
            "undetermined": "The state does not decide.\nAnswer: undetermined\n",
            "value not allowed": "Answer: maybe\n",
            "other question's value": "Answer: integration\n",
            "unavailable judge": "judge unavailable",
            "empty": "",
        }
        for label, text in cases.items():
            with self.subTest(label):
                self.assertEqual(self.answer("review.findings_block", text), "uncertain")

    def test_answer_mentioned_inside_a_sentence_is_not_a_verdict_line(self):
        self.assertEqual(self.answer("review.findings_block", "I would write Answer: no here.\n"), "uncertain")


class ObservedTestSourcesTests(unittest.TestCase):
    def test_changed_tests_come_first_docs_are_not_tests_and_the_budget_truncates(self):
        from driver import observed_test_sources
        with tempfile.TemporaryDirectory(prefix="tdr-sources-") as temp:
            root = Path(temp)
            files = {"docs/specs/tests-plan.md": "plan", "src/app.ts": "code", "src/app.test.ts": "t" * 60,
                     "tests/test_rec.c": "unit", "tests/test_cli.sh": "cli", "pkg/foo_test.go": "go"}
            for name, text in files.items():
                (root / name).parent.mkdir(parents=True, exist_ok=True)
                (root / name).write_text(text, encoding="utf-8")
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
            sources = observed_test_sources(root, ["src/app.ts", "tests/test_cli.sh"], budget=60)
        self.assertEqual([s["path"] for s in sources],
                         ["tests/test_cli.sh", "pkg/foo_test.go", "src/app.test.ts"])
        self.assertEqual([s["truncated"] for s in sources], [False, False, True])
        self.assertEqual(sum(len(s["content"]) for s in sources), 60)


if __name__ == "__main__":
    unittest.main()
