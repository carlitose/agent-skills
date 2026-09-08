"""Focused local probes; never a production-policy approval."""
import tempfile
import unittest
from pathlib import Path

from fixtures import FIXTURES, QUESTIONS
from prototype import Experiment, VARIANTS, bounded, compare, digest, production, sections


class ComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = compare()
        cls.variants = cls.result["variants"]

    def test_same_corpus_covers_every_kind_and_two_canonical_tickets(self):
        expected = {f["path"] for f in FIXTURES}
        self.assertEqual({"ticket", "spec", "research", "prototype", "guide"},
                         {f["kind"] for f in FIXTURES})
        for variant in VARIANTS:
            rows = self.variants[variant]["measurements"]
            self.assertEqual(expected, {r["source"] for r in rows})
            self.assertEqual(2, sum(r["compiler_kind"] == "ticket" for r in rows))
            self.assertEqual(["path:docs/guides/context.md"],
                             [r["identity"] for r in rows if r["weak_identity"]])

    def test_metadata_control_fails_query_utility_while_preservation_covers_source_facts(self):
        for variant in VARIANTS:
            for row in self.variants[variant]["measurements"]:
                with self.subTest(variant=variant, source=row["source"]):
                    self.assertEqual(set(QUESTIONS), set(row["questions"]))
                    if variant == "metadata-control":
                        self.assertNotIn("answerable", row["questions"].values())
                    if variant in {"preserve", "layered"}:
                        self.assertNotIn("missing-from-page", row["questions"].values())
                        self.assertTrue(row["literal_fidelity"])
        bounded_rows = {r["source"]: r for r in self.variants["bounded"]["measurements"]}
        self.assertEqual("missing-from-page", bounded_rows[FIXTURES[0]["path"]]["questions"]["exclusions"])
        self.assertEqual("missing-from-page", bounded_rows["docs/guides/context.md"]["questions"]["intent"])
        # Missing source information is not counted as successfully recovered.
        self.assertEqual("absent-in-source", bounded_rows["docs/research/forward.md"]["questions"]["acceptance"])

    def test_replay_is_deterministic_and_unchanged_ingest_writes_zero(self):
        for data in self.variants.values():
            self.assertTrue(data["fresh_directory_deterministic"])
            self.assertTrue(data["unchanged_mtimes"])
            self.assertEqual(6, data["replay"]["transitions"]["unchanged"])
            self.assertEqual([], data["replay"]["written_source_pages"])
            self.assertEqual(0, data["replay"]["summary_bytes_written"])
            self.assertEqual(0, data["replay"]["changed_file_bytes"])
            self.assertEqual(0, data["final_replay"]["changed_file_bytes"])

    def test_semantic_edit_exposes_the_bounded_tail_blind_spot(self):
        for variant, data in self.variants.items():
            edit = data["semantic_edit"]
            self.assertEqual(1, edit["transitions"]["changed"])
            self.assertTrue(edit["digest_changed"])
            self.assertEqual(variant in {"preserve", "layered"}, edit["new_fact_visible"])
            self.assertEqual(variant in {"preserve", "layered"}, edit["semantic_body_changed"])
        self.assertTrue(self.variants["layered"]["semantic_edit"]["authored_summary_stale"])

    def test_move_and_tombstone_keep_identity_and_graph(self):
        for data in self.variants.values():
            self.assertEqual(6, data["first"]["transitions"]["new"])
            self.assertEqual(1, data["disposition_move"]["transitions"]["moved"])
            self.assertEqual(0, data["disposition_move"]["transitions"]["new"])
            self.assertTrue(data["disposition_move"]["same_page_name"])
            self.assertTrue(data["disposition_move"]["parent_link_preserved"])
            self.assertEqual(1, data["missing_source"]["transitions"]["missing"])
            self.assertTrue(data["missing_source"]["tombstone_retained"])
            self.assertEqual([], data["broken_wikilinks"])
            page = data["pages"]["wiki/sources/ticket-family-fx-02.md"]
            self.assertIn("Blocked by: [[sources/ticket-family-fx-01]]", page)
            self.assertIn("Parent source: [[sources/artifact-fixture-map]]", page)
            parent = data["pages"]["wiki/sources/artifact-fixture-map.md"]
            self.assertIn("Child source: [[sources/ticket-family-fx-01]]", parent)

    def test_authored_layer_has_no_automatic_audit_or_complete_summary_claim(self):
        data = self.variants["layered"]
        summary = data["pages"]["wiki/synthesis/ticket-family-fx-01-summary.md"]
        self.assertIn("Freshness: digest-match; audit: unreviewed", summary)
        self.assertIn("A matching digest does not prove semantic correctness", summary)
        first = data["measurements"][0]
        self.assertIn("missing-from-page", first["summary_questions"].values())
        self.assertGreater(data["total_generated"]["bytes"],
                           self.variants["preserve"]["total_generated"]["bytes"])


class BoundaryTests(unittest.TestCase):
    def test_empty_duplicate_and_fenced_sections_are_not_guessed(self):
        text = "## Acceptance Criteria\n\n## Testing Plan\nfirst\n## Testing Plan\nsecond\n```md\n## Evidence\nfake\n```\n"
        parsed = sections(text)
        self.assertEqual(2, len(parsed["testing plan"]))
        self.assertNotIn("evidence", parsed)
        rendered = bounded(text)
        self.assertIn("### acceptance\nUNAVAILABLE", rendered)
        self.assertIn("### evidence\nUNAVAILABLE", rendered)
        self.assertIn("first", rendered)
        self.assertIn("second", rendered)

    def test_normalized_digest_crosses_the_real_source_reader(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.md"
            text = "# Café\n\nLiteral source.\n"
            path.write_bytes(text.encode("utf-8"))
            expected = production.source_digest(path)
            path.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))
            self.assertEqual(expected, production.source_digest(path))
            self.assertEqual(digest(text), expected)

    def test_malformed_ticket_fails_canonical_parser_without_wiki_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            experiment = Experiment(Path(directory), "preserve")
            experiment.run()
            before = experiment.pages()
            experiment.put(FIXTURES[0]["path"], FIXTURES[0]["text"].replace("ticket_schema: 1", "ticket_schema: 99"))
            with self.assertRaises(production.TicketParserError):
                experiment.run()
            self.assertEqual(before, experiment.pages())

    def test_weak_identity_move_is_explicitly_a_new_page_and_tombstone(self):
        with tempfile.TemporaryDirectory() as directory:
            experiment = Experiment(Path(directory), "layered")
            experiment.run()
            old_identity = "path:docs/guides/context.md"
            (experiment.project / "docs/guides/context.md").rename(experiment.project / "docs/guides/moved.md")
            result = experiment.run()
            self.assertEqual(1, result["transitions"]["new"])
            self.assertEqual(1, result["transitions"]["missing"])
            self.assertEqual("missing", production.read_page_front_matter(experiment.page_path(old_identity))["source_status"])
            new_page = experiment.page_path("path:docs/guides/moved.md")
            self.assertTrue(new_page.is_file())
            summary = experiment.wiki / "wiki/synthesis/path-docs-guides-moved-md-summary.md"
            self.assertIn("Freshness: unavailable", summary.read_text(encoding="utf-8"))
            self.assertEqual(0, experiment.run()["changed_file_bytes"])


if __name__ == "__main__":
    unittest.main()
