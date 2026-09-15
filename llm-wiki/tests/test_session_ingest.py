from __future__ import annotations

import hashlib
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import session_discovery  # noqa: E402
from project_binding import write_binding  # noqa: E402
from scaffold import scaffold  # noqa: E402
from session_catalog import SessionCatalogError  # noqa: E402
from session_ingest import (  # noqa: E402
    MAX_DIGEST_WORDS,
    MIN_DIGEST_WORDS,
    TICKET_REFERENCE,
    _session_id,
    _text_of,
    digest_document,
    extract,
    ingest,
    pointer_document,
    word_count,
)

def claude_record(text: str, stamp: str, kind: str = "assistant") -> str:
    return json.dumps({"type": kind, "timestamp": stamp, "message": {"content": text}})


def codex_record(text: str, stamp: str, kind: str = "event_msg") -> str:
    return json.dumps({"type": kind, "timestamp": stamp, "payload": {"text": text}})


def nested_content_record(blocks: list, stamp: str, role: str = "user") -> str:
    """A turn whose ``content`` is a list of blocks, which is the shape Pi writes."""

    return json.dumps(
        {
            "type": "message",
            "timestamp": stamp,
            "message": {"role": role, "content": blocks, "timestamp": stamp},
        }
    )


def pi_records(cwd: str, session_id: str, texts: list[str], compactions: int = 0) -> list[str]:
    """The record sequence Pi writes: a ``session`` header, turns, and ``compaction`` markers."""

    lines = [
        json.dumps(
            {
                "type": "session",
                "version": 3,
                "id": session_id,
                "timestamp": "2026-09-07T09:04:49.036Z",
                "cwd": cwd,
            }
        )
    ]
    for index, text in enumerate(texts):
        lines.append(
            nested_content_record(
                [{"type": "text", "text": text}], f"2026-09-07T10:0{index}:00Z"
            )
        )
    for index in range(compactions):
        lines.append(
            json.dumps({"type": "compaction", "timestamp": f"2026-09-07T11:0{index}:00Z"})
        )
    return lines


def write_transcript(path: Path, lines: list[str]) -> Path:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


class TicketReferenceRuleTests(unittest.TestCase):
    def test_a_glob_from_this_project_history_is_not_a_ticket(self) -> None:
        """The false positive that a one-digit rule actually produced.

        This repository's own transcript contains the instruction
        "vai avanti con AG-0* con /ticket-autopilot". A loose rule read ``AG-0`` out of it and
        invented a ticket that has never existed.
        """

        text = "vai avanti con AG-0* con /ticket-autopilot"
        self.assertEqual([], TICKET_REFERENCE.findall(text))

    def test_a_bare_number_is_prose_and_a_prefixed_identifier_is_not(self) -> None:
        text = "step 01 failed, so WT-01 and AG-04 were reopened; see item 7 and TK-3"
        self.assertEqual(["WT-01", "AG-04"], TICKET_REFERENCE.findall(text))

    def test_the_repository_identifier_forms_all_match(self) -> None:
        for identifier in ("WT-01", "TK-09", "AG-04", "LW-11", "CR-02", "WD-01", "IS-01"):
            with self.subTest(identifier=identifier):
                self.assertEqual([identifier], TICKET_REFERENCE.findall(identifier))


class ExtractionTests(unittest.TestCase):
    def test_dated_mentions_carry_the_earliest_and_latest_day(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            transcript = write_transcript(
                Path(temporary) / "s.jsonl",
                [
                    claude_record("start on WT-01", "2026-08-11T09:00:00Z"),
                    claude_record("WT-01 again, and AG-04", "2026-08-13T10:00:00Z"),
                    claude_record("WT-01 once more", "2026-08-12T10:00:00Z"),
                ],
            )
            facts = extract(transcript, "claude-code")

        mentions = facts.dated_mentions()
        self.assertEqual({"earliest": "2026-08-11", "latest": "2026-08-13"}, mentions["WT-01"])
        self.assertEqual({"earliest": "2026-08-13", "latest": "2026-08-13"}, mentions["AG-04"])
        self.assertEqual("2026-08-11 to 2026-08-13", facts.span)

    def test_a_compacted_codex_session_is_counted(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            transcript = write_transcript(
                Path(temporary) / "rollout-a-00000000-0000-0000-0000-000000000000.jsonl",
                [
                    codex_record("work on LW-08", "2026-08-20T09:00:00Z"),
                    json.dumps({"type": "compacted", "timestamp": "2026-08-20T09:30:00Z"}),
                    codex_record("more on LW-08", "2026-08-20T10:00:00Z"),
                ],
            )
            facts = extract(transcript, "codex")

        self.assertEqual(1, facts.compacted_records)
        self.assertIn("compacted 1 time", digest_document(facts))
        self.assertIn("incomplete by construction", digest_document(facts))

    def test_a_large_transcript_is_never_read_whole(self) -> None:
        """Streaming is the point: the real stores are ~50 MB."""

        with tempfile.TemporaryDirectory() as temporary:
            lines = [
                claude_record(f"line {index} about WT-01", "2026-08-11T09:00:00Z")
                for index in range(4000)
            ]
            transcript = write_transcript(Path(temporary) / "big.jsonl", lines)
            facts = extract(transcript, "claude-code")

        self.assertEqual(4000, facts.record_count)
        self.assertGreater(facts.size_bytes, 200_000)


class DocumentTests(unittest.TestCase):
    def _facts(self, tickets: int, files: int) -> object:
        with tempfile.TemporaryDirectory() as temporary:
            lines = []
            for index in range(tickets):
                lines.append(
                    claude_record(f"work on ZZ-{index:02d}", "2026-08-11T09:00:00Z")
                )
            for index in range(files):
                lines.append(
                    claude_record(
                        f"edited docs/specs/file{index}.md and decided to keep it",
                        "2026-08-11T09:00:00Z",
                    )
                )
            transcript = write_transcript(Path(temporary) / "s.jsonl", lines)
            return extract(transcript, "claude-code")

    def test_the_digest_stays_inside_its_word_band_at_both_extremes(self) -> None:
        for tickets, files in ((0, 0), (1, 1), (40, 40), (100, 40)):
            with self.subTest(tickets=tickets, files=files):
                document = digest_document(self._facts(tickets, files))
                count = word_count(document)
                self.assertLessEqual(count, MAX_DIGEST_WORDS, document[:200])
                self.assertGreaterEqual(count, MIN_DIGEST_WORDS - 60)

    def test_a_trimmed_list_says_so_rather_than_truncating_silently(self) -> None:
        document = digest_document(self._facts(100, 40))
        self.assertIn("trimmed", document)
        self.assertIn("ZZ-99", document, "complete ticket metadata must survive compaction")
        self.assertNotIn("What the transcript is made of", document)

    def test_the_digest_attributes_claims_to_the_session(self) -> None:
        document = digest_document(self._facts(2, 2))
        self.assertIn("none of it is asserted as project truth", document)

    def test_the_pointer_carries_no_transcript_content(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            secret = "a-very-distinctive-string-from-the-transcript"
            transcript = write_transcript(
                Path(temporary) / "s.jsonl",
                [claude_record(secret, "2026-08-11T09:00:00Z")],
            )
            facts = extract(transcript, "claude-code")
            pointer = pointer_document(facts)

        self.assertNotIn(secret, pointer)
        for field in ("kind: ref", "external_path:", "size_bytes:", "record_count:"):
            self.assertIn(field, pointer)


class StalenessTests(unittest.TestCase):
    def test_a_missing_shared_index_fails_before_writing_session_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            transcript = write_transcript(
                root / "s.jsonl", [claude_record("WT-01", "2026-08-11T09:00:00Z")]
            )
            wiki = root / "wiki"

            import session_ingest

            with patch.object(
                session_ingest, "claude_transcripts", return_value=[transcript]
            ), patch.object(
                session_ingest, "codex_transcripts", return_value=([], [])
            ), self.assertRaises(SessionCatalogError):
                session_ingest.ingest(root, wiki)

            self.assertFalse(wiki.exists())

    def test_an_unchanged_session_is_skipped_and_an_appended_one_is_rewritten(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            store = root / "store"
            store.mkdir()
            transcript = write_transcript(
                store / "s.jsonl", [claude_record("WT-01", "2026-08-11T09:00:00Z")]
            )
            wiki = root / "wiki"
            scaffold(wiki, "Session test")

            import session_ingest

            with patch.object(
                session_ingest, "claude_transcripts", return_value=[transcript]
            ), patch.object(
                session_ingest, "codex_transcripts", return_value=([], [])
            ):
                first = session_ingest.ingest(root, wiki)
                second = session_ingest.ingest(root, wiki)
                with transcript.open("a", encoding="utf-8") as handle:
                    handle.write(claude_record("WT-01 again", "2026-08-12T09:00:00Z") + "\n")
                third = session_ingest.ingest(root, wiki)

        self.assertEqual(1, len(first["written"]))
        self.assertTrue(first["catalog_updated"])
        self.assertEqual([], second["written"], "an unchanged session must write nothing")
        self.assertFalse(second["catalog_updated"])
        self.assertEqual(1, len(second["skipped"]))
        self.assertEqual(1, len(third["written"]), "an appended session must be rebuilt")
        self.assertFalse(third["catalog_updated"], "the stable catalog link needs no rewrite")


class StoreBoundaryTests(unittest.TestCase):
    def test_both_providers_are_ingested_without_copying_transcript_content(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            wiki = root / "wiki"
            scaffold(wiki, "Store boundary test")
            payload = "x" * 2000
            claude = write_transcript(
                root / "claude.jsonl",
                [
                    claude_record(f"WT-01 {payload}", "2026-08-11T09:00:00Z")
                    for _index in range(1000)
                ],
            )
            codex = write_transcript(
                root / "rollout-a-00000000-0000-0000-0000-000000000000.jsonl",
                [
                    codex_record(f"LW-08 {payload}", "2026-08-20T09:00:00Z")
                    for _index in range(1000)
                ],
            )

            import session_ingest

            with patch.object(
                session_ingest, "claude_transcripts", return_value=[claude]
            ), patch.object(
                session_ingest, "codex_transcripts", return_value=([codex], [])
            ):
                report = ingest(project, wiki)
            wiki_bytes = sum(
                path.stat().st_size for path in wiki.rglob("*") if path.is_file()
            )

        self.assertEqual(1, report["claude"])
        self.assertEqual(1, report["codex"])
        self.assertEqual(0, report["unresolved_codex"])
        self.assertTrue(report["catalog_updated"])
        self.assertGreater(report["transcript_bytes"], 1_000_000)
        self.assertLess(
            wiki_bytes,
            report["transcript_bytes"] // 100,
            "the wiki must stay orders of magnitude smaller than the transcripts",
        )

    def test_no_invented_ticket_reaches_the_mention_data(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            transcript = write_transcript(
                root / "session.jsonl",
                [
                    claude_record(
                        "vai avanti con AG-0*; il ticket reale è WT-01",
                        "2026-08-11T09:00:00Z",
                    )
                ],
            )

            import session_ingest

            with patch.object(
                session_ingest, "claude_transcripts", return_value=[transcript]
            ), patch.object(
                session_ingest, "codex_transcripts", return_value=([], [])
            ):
                report = ingest(root / "project", root / "wiki", dry_run=True)
        tickets = {
            ticket
            for mentions in report["dated_ticket_mentions"].values()
            for ticket in mentions
        }
        self.assertNotIn("AG-0", tickets)
        self.assertIn("WT-01", tickets)
        for ticket in tickets:
            self.assertRegex(ticket, r"^[A-Z]{2,6}-\d{2,4}$")


class PiProviderTests(unittest.TestCase):
    """Pi's vocabulary differs from Codex's, and reading it with Codex's words yields silence."""

    def _transcript(self, root: Path, project: Path, compactions: int = 0) -> Path:
        return write_transcript(
            root / "2026-09-07T09-04-49-036Z_01a07b1c-ef8c-73cd-9f7c-0baef19f02c4.jsonl",
            pi_records(
                str(project),
                "01a07b1c-ef8c-73cd-9f7c-0baef19f02c4",
                [
                    "We decided to keep docs/specs/one.md as the source of truth for WT-01.",
                    "Then docs/tickets/two.md was split.",
                ],
                compactions=compactions,
            ),
        )

    def test_the_session_id_is_the_identifier_after_the_timestamp(self) -> None:
        path = Path("2026-09-07T09-04-49-036Z_01a07b1c-ef8c-73cd-9f7c-0baef19f02c4.jsonl")
        self.assertEqual("01a07b1c-ef8c-73cd-9f7c-0baef19f02c4", _session_id(path, "pi"))

    def test_a_pi_transcript_yields_its_cwd_and_its_prose(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            facts = extract(self._transcript(root, project), "pi")

        self.assertEqual(str(project), facts.cwd)
        self.assertEqual({"docs/specs/one.md", "docs/tickets/two.md"}, facts.files_touched)
        self.assertEqual({"WT-01": ["2026-09-07"]}, facts.ticket_mentions)
        self.assertEqual(1, len(facts.decision_lines))

    def test_compaction_is_counted_under_pis_own_spelling(self) -> None:
        """Codex says ``compacted`` and Pi says ``compaction``.

        Counting only Codex's word would mark a truncated transcript ``complete``, which claims
        the digest is missing nothing when the provider already threw detail away.
        """

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            facts = extract(self._transcript(root, project, compactions=2), "pi")

        self.assertEqual(2, facts.compacted_records)
        self.assertIn("source_status: compacted", digest_document(facts))

    def test_a_bound_wiki_compiles_the_providers_its_binding_names(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            wiki = root / "wiki"
            scaffold(wiki, "Provider dispatch test")
            write_binding(wiki, project, session_providers=("pi",))
            transcript = self._transcript(root, project)

            import session_ingest

            with patch.object(
                session_ingest, "pi_transcripts", return_value=([transcript], [])
            ):
                report = ingest(project, wiki)

            digest = wiki / "wiki" / "sources" / (
                "session-pi-01a07b1c-ef8c-73cd-9f7c-0baef19f02c4.md"
            )
            pointer = wiki / "raw" / "refs" / (
                "pi-01a07b1c-ef8c-73cd-9f7c-0baef19f02c4.md"
            )
            digest_text = digest.read_text(encoding="utf-8")
            pointer_text = pointer.read_text(encoding="utf-8")

        self.assertEqual(["pi"], report["providers"])
        self.assertEqual(1, report["pi"])
        self.assertNotIn("claude", report)
        self.assertNotIn("codex", report)
        self.assertIn("provider: pi", pointer_text)
        self.assertIn("tickets_touched: [WT-01]", digest_text)
        self.assertIn("docs/specs/one.md", digest_text)

    def test_an_unknown_provider_in_the_binding_names_the_offending_value(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            wiki = root / "wiki"
            scaffold(wiki, "Unknown provider test")
            write_binding(wiki, project, session_providers=("claude-code", "cladue-code"))
            with self.assertRaises(session_discovery.DiscoveryError) as raised:
                ingest(project, wiki, dry_run=True)
        self.assertIn("cladue-code", str(raised.exception))

    def test_a_second_run_over_unchanged_transcripts_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            wiki = root / "wiki"
            scaffold(wiki, "Idempotence test")
            write_binding(wiki, project, session_providers=("pi",))
            transcript = self._transcript(root, project)

            import session_ingest

            with patch.object(
                session_ingest, "pi_transcripts", return_value=([transcript], [])
            ):
                first = ingest(project, wiki)
                second = ingest(project, wiki)

        self.assertEqual(1, len(first["written"]))
        self.assertEqual([], second["written"])
        self.assertEqual(1, len(second["skipped"]))


class ProviderOutputStabilityTests(unittest.TestCase):
    """Adding a third provider must not move one byte of the two that already worked.

    The goldens cover the pointer **and** the digest, because a provider set threaded through
    discovery could change either. The one line that legitimately varies between runs, the
    external path of a temporary fixture, is redacted rather than asserted.
    """

    def test_claude_and_codex_documents_are_byte_identical_to_their_goldens(self) -> None:
        expected = {
            "claude-code": "16dfd8a89ef561e4bf764e1b38c6416951fcc7fa89061c90a6cc934bafe03848",
            "codex": "ee718a109d0972dcc7aabbaa35749c65f2b12ae2d881e49b034428392cbabc7d",
        }
        digests = {}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            transcripts = {
                "claude-code": write_transcript(
                    root / "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee.jsonl",
                    [
                        claude_record(
                            "Decided to keep docs/specs/one.md as the source of truth for WT-01.",
                            "2026-01-02T10:00:00Z",
                        )
                    ],
                ),
                "codex": write_transcript(
                    root / "rollout-2026-01-03T09-00-00-11111111-2222-3333-4444-555555555555.jsonl",
                    [
                        codex_record(
                            "We chose to split docs/tickets/two.md for LW-08.",
                            "2026-01-03T09:00:00Z",
                        )
                    ],
                ),
            }
            for provider, path in transcripts.items():
                facts = extract(path, provider)
                pointer = re.sub(
                    r"(?m)^external_path: .*$",
                    "external_path: <redacted>",
                    pointer_document(facts),
                )
                combined = pointer + digest_document(facts)
                digests[provider] = hashlib.sha256(
                    combined.encode("utf-8")
                ).hexdigest()

        self.assertEqual(expected, digests)


class NestedMessageContentTests(unittest.TestCase):
    """A turn can wrap its text one level deeper than the reader used to look.

    Measured before this rule existed: a real 174-record transcript of that shape yielded
    text from **zero** records. The digest would have reported no files, no decisions and no
    ticket mentions — indistinguishable from a session that did nothing, and stated with the
    same confidence.
    """

    def test_a_nested_content_list_yields_its_text(self) -> None:
        record = json.loads(
            nested_content_record([{"type": "text", "text": "one"}], "2026-01-02T10:00:00Z")
        )
        self.assertEqual("one", _text_of(record))

    def test_every_block_of_a_turn_contributes_in_order(self) -> None:
        record = json.loads(
            nested_content_record(
                [
                    {"type": "text", "text": "first"},
                    {"type": "text", "text": "second"},
                ],
                "2026-01-02T10:00:00Z",
            )
        )
        self.assertEqual("first\nsecond", _text_of(record))

    def test_a_mixed_list_of_strings_and_blocks_is_read(self) -> None:
        record = json.loads(
            nested_content_record(["bare", {"type": "text", "text": "block"}], "2026-01-02T10:00:00Z")
        )
        self.assertEqual("bare\nblock", _text_of(record))

    def test_a_block_without_text_contributes_nothing_and_raises_nothing(self) -> None:
        record = json.loads(
            nested_content_record(
                [
                    {"type": "image", "source": {"data": "…"}},
                    {"type": "tool_use", "input": {"path": "docs/specs/one.md"}},
                    {"type": "text", "text": "kept"},
                ],
                "2026-01-02T10:00:00Z",
            )
        )
        self.assertEqual("kept", _text_of(record))

    def test_a_dict_whose_content_is_a_string_keeps_its_behaviour(self) -> None:
        record = json.loads(claude_record("plain", "2026-01-02T10:00:00Z"))
        self.assertEqual("plain", _text_of(record))

    def test_the_walk_stops_one_level_down(self) -> None:
        """A block that itself holds a list is an attachment shape, not prose.

        Descending further would start decoding payloads and inventing text; the bound is
        deliberate, so it is pinned here rather than left to be discovered later.
        """

        record = json.loads(
            nested_content_record([{"content": [{"text": "buried"}]}], "2026-01-02T10:00:00Z")
        )
        self.assertEqual("", _text_of(record))

    def test_a_transcript_of_that_shape_carries_its_facts(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            transcript = write_transcript(
                Path(raw) / "2026-01-02T10-00-00-000Z_aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee.jsonl",
                [
                    nested_content_record(
                        [
                            {
                                "type": "text",
                                "text": (
                                    "We decided to keep docs/specs/one.md as the source of "
                                    "truth for WT-01."
                                ),
                            }
                        ],
                        "2026-01-02T10:00:00Z",
                    ),
                    nested_content_record(
                        [{"type": "text", "text": "Then docs/tickets/two.md was split."}],
                        "2026-01-02T11:00:00Z",
                    ),
                ],
            )
            facts = extract(transcript, "claude-code")
            extracted = "\n".join(
                _text_of(json.loads(line))
                for line in transcript.read_text(encoding="utf-8").splitlines()
            )

        self.assertEqual(106, len(extracted))
        self.assertEqual({"docs/specs/one.md", "docs/tickets/two.md"}, facts.files_touched)
        self.assertEqual({"WT-01": ["2026-01-02"]}, facts.ticket_mentions)
        self.assertEqual(1, len(facts.decision_lines))

    def test_a_payload_wrapped_turn_is_read_at_the_same_depth(self) -> None:
        """The payload branch was list-blind in exactly the same way.

        Codex wraps its turn as ``{"payload": {"message": …}}``. Leaving that branch on the
        old string-only rule would have kept the defect this ticket removes alive three lines
        below the fix, waiting for the first provider that wraps blocks there.
        """

        record = {
            "type": "event_msg",
            "timestamp": "2026-01-02T10:00:00Z",
            "payload": {
                "message": [
                    {"type": "text", "text": "wrapped"},
                    {"type": "image", "source": {"data": "…"}},
                    "bare",
                ]
            },
        }
        self.assertEqual("wrapped\nbare", _text_of(record))

    def test_a_payload_string_still_reads_as_one_piece(self) -> None:
        record = json.loads(codex_record("plain", "2026-01-02T10:00:00Z"))
        self.assertEqual("plain", _text_of(record))

    def test_the_supported_providers_digest_exactly_as_before(self) -> None:
        """The change is provider-neutral, so these two bytes must not move.

        The digests are pinned by hash rather than described, because "unchanged" asserted in
        prose is not an assertion.
        """

        expected = {
            "claude-code": "ef6386d25640900d4b0a9c7615e70fbc22c1eac0bd35638abc1c995bc49c4465",
            "codex": "55506ef93fb89cc40d76034a1c2f745bbc2fb4d344a35e8f7e664052c4476ca1",
        }
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            transcripts = {
                "claude-code": write_transcript(
                    root / "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee.jsonl",
                    [
                        claude_record(
                            "Decided to keep docs/specs/one.md as the source of truth for WT-01.",
                            "2026-01-02T10:00:00Z",
                        ),
                        claude_record(
                            "Then we chose to split docs/tickets/two.md into two slices.",
                            "2026-01-02T11:00:00Z",
                        ),
                    ],
                ),
                "codex": write_transcript(
                    root / "rollout-2026-01-03T09-00-00-11111111-2222-3333-4444-555555555555.jsonl",
                    [
                        codex_record(
                            "We decided to rewrite docs/specs/three.md before AG-04 lands.",
                            "2026-01-03T09:00:00Z",
                        )
                    ],
                ),
            }
            for provider, transcript in transcripts.items():
                with self.subTest(provider=provider):
                    document = digest_document(extract(transcript, provider))
                    digest = hashlib.sha256(document.encode("utf-8")).hexdigest()
                    self.assertEqual(expected[provider], digest)


if __name__ == "__main__":
    unittest.main()
