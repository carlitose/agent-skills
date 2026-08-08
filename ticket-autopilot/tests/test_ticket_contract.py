from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_ROOT.parent
SCRIPTS = SKILL_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from autopilot.ticket_contract import (  # noqa: E402
    ContractError,
    migrate_ticket_text,
    normalize_ticket_envelope,
    parse_ticket_folder,
    parse_ticket_markdown,
    serialize_ticket_markdown,
)


VALID_ENVELOPE = {
    "ticket_schema": 1,
    "ticket_id": "06",
    "execution_mode": "AFK",
    "blocked_by": ["04", "05"],
}


class TicketContractTests(unittest.TestCase):
    def test_folder_layout_is_the_administrative_disposition_source(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            for directory in ("hold", "canceled", "done"):
                (folder / directory).mkdir()
            documents = {
                folder / "01.md": dict(VALID_ENVELOPE, ticket_id="01", blocked_by=[]),
                folder / "hold" / "02.md": dict(
                    VALID_ENVELOPE, ticket_id="02", blocked_by=[]
                ),
                folder / "canceled" / "03.md": dict(
                    VALID_ENVELOPE, ticket_id="03", blocked_by=[]
                ),
                folder / "done" / "04.md": dict(
                    VALID_ENVELOPE, ticket_id="04", blocked_by=[]
                ),
            }
            for path, envelope in documents.items():
                path.write_text(
                    serialize_ticket_markdown(envelope, f"# {envelope['ticket_id']}\n"),
                    encoding="utf-8",
                )

            graph = parse_ticket_folder(folder)

        self.assertEqual(
            {"01": "open", "02": "on-hold", "03": "canceled", "04": "completed"},
            graph.dispositions,
        )
        self.assertEqual(frozenset({"04"}), graph.completed_ids)

    def test_normalization_is_strict_and_deterministic(self) -> None:
        normalized = normalize_ticket_envelope(
            {
                "blocked_by": ["04", "05"],
                "execution_mode": "afk",
                "ticket_id": "06",
                "ticket_schema": "1",
            }
        )

        self.assertEqual(VALID_ENVELOPE, normalized)
        self.assertEqual(
            ["ticket_schema", "ticket_id", "execution_mode", "blocked_by"],
            list(normalized),
        )

    def test_serialization_round_trips_without_reordering_dependencies(self) -> None:
        markdown = serialize_ticket_markdown(
            VALID_ENVELOPE,
            "# Simplify skill graph\n\nKeep this body byte-stable.\n",
        )

        self.assertEqual(
            (
                "---\n"
                "ticket_schema: 1\n"
                'ticket_id: "06"\n'
                "execution_mode: AFK\n"
                "blocked_by:\n"
                '  - "04"\n'
                '  - "05"\n'
                "---\n\n"
                "# Simplify skill graph\n\n"
                "Keep this body byte-stable.\n"
            ),
            markdown,
        )
        parsed = parse_ticket_markdown(markdown)
        self.assertEqual(VALID_ENVELOPE, parsed.envelope)
        self.assertEqual(
            "# Simplify skill graph\n\nKeep this body byte-stable.\n",
            parsed.body,
        )
        self.assertEqual(markdown, serialize_ticket_markdown(parsed.envelope, parsed.body))

    def test_parser_requires_exactly_one_lf_blank_separator(self) -> None:
        canonical = serialize_ticket_markdown(VALID_ENVELOPE, "# LF separator\n")
        missing = canonical.replace("---\n\n# LF", "---\n# LF", 1)
        extra = canonical.replace("---\n\n# LF", "---\n\n\n# LF", 1)

        with self.assertRaisesRegex(ContractError, "exactly one blank line"):
            parse_ticket_markdown(missing)
        with self.assertRaisesRegex(ContractError, "exactly one blank line"):
            parse_ticket_markdown(extra)
        self.assertEqual(
            canonical,
            serialize_ticket_markdown(
                parse_ticket_markdown(canonical).envelope,
                parse_ticket_markdown(canonical).body,
            ),
        )

    def test_parser_requires_exactly_one_crlf_blank_separator(self) -> None:
        canonical = serialize_ticket_markdown(
            VALID_ENVELOPE,
            "# CRLF separator\n",
        ).replace("\n", "\r\n")
        missing = canonical.replace("---\r\n\r\n# CRLF", "---\r\n# CRLF", 1)
        extra = canonical.replace(
            "---\r\n\r\n# CRLF",
            "---\r\n\r\n\r\n# CRLF",
            1,
        )

        with self.assertRaisesRegex(ContractError, "exactly one blank line"):
            parse_ticket_markdown(missing)
        with self.assertRaisesRegex(ContractError, "exactly one blank line"):
            parse_ticket_markdown(extra)
        parsed = parse_ticket_markdown(canonical)
        self.assertEqual("# CRLF separator\r\n", parsed.body)

    def test_empty_dependencies_use_inline_list(self) -> None:
        envelope = dict(VALID_ENVELOPE, blocked_by=[])

        markdown = serialize_ticket_markdown(envelope, "# Independent\n")

        self.assertIn("blocked_by: []\n", markdown)
        self.assertEqual(envelope, parse_ticket_markdown(markdown).envelope)

    def test_unknown_or_missing_fields_fail_closed(self) -> None:
        with self.assertRaisesRegex(ContractError, "unknown field"):
            normalize_ticket_envelope(dict(VALID_ENVELOPE, surprise=True))
        incomplete = dict(VALID_ENVELOPE)
        incomplete.pop("execution_mode")
        with self.assertRaisesRegex(ContractError, "missing required field"):
            normalize_ticket_envelope(incomplete)

    def test_identifier_types_fail_closed_to_preserve_leading_zeroes(self) -> None:
        with self.assertRaisesRegex(ContractError, "ticket_schema must be an integer"):
            normalize_ticket_envelope(dict(VALID_ENVELOPE, ticket_schema=True))
        with self.assertRaisesRegex(ContractError, "ticket_id must be text"):
            normalize_ticket_envelope(dict(VALID_ENVELOPE, ticket_id=6))
        with self.assertRaisesRegex(ContractError, "blocker must be text"):
            normalize_ticket_envelope(dict(VALID_ENVELOPE, blocked_by=[4, "05"]))

    def test_legacy_markdown_requires_explicit_migration(self) -> None:
        legacy = "# Legacy\n\n## Execution Mode\n\nAFK\n"

        with self.assertRaisesRegex(ContractError, "front matter"):
            parse_ticket_markdown(legacy)

        with tempfile.TemporaryDirectory() as temporary:
            ticket = Path(temporary) / "07-legacy.md"
            ticket.write_text(legacy, encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "scripts" / "ticket-autopilot.py"),
                    "migrate",
                    str(ticket),
                    "--write",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            migrated = parse_ticket_markdown(ticket.read_text(encoding="utf-8"))
            self.assertEqual("07", migrated.envelope["ticket_id"])

    def test_legacy_migration_requires_execution_mode_section(self) -> None:
        legacy = "# Legacy\n\n## Ticket ID\n\n07\n"

        with self.assertRaisesRegex(
            ContractError, "legacy Execution Mode section is required"
        ):
            migrate_ticket_text(legacy, source="07-legacy.md")

    def test_legacy_blockers_reject_every_unrecognized_nonempty_entry(self) -> None:
        invalid_entries = (
            "Depends on ticket 02",
            "- Depends on ticket 02",
            "-",
            "- None - probably ready",
            "- [02-parser.md](./03-other.md)",
            "- [01-research.md](./01-research.md) — in progress.",
            "- [01-research.md](./01-research.md) — done.",
            "- [01-research.md](./01-research.md) - completed.",
            "- [01-research.md](./01-research.md) — completed",
        )
        for entry in invalid_entries:
            with self.subTest(entry=entry):
                legacy = (
                    "# Legacy\n\n"
                    "## Ticket ID\n\n08\n\n"
                    "## Execution Mode\n\nAFK\n\n"
                    "## Blocked By\n\n"
                    f"{entry}\n"
                )
                with self.assertRaisesRegex(
                    ContractError,
                    r"reviewer\.md: legacy Blocked By line 1: unsupported entry",
                ):
                    migrate_ticket_text(
                        legacy,
                        source="reviewer.md",
                    )

    def test_legacy_duplicate_blocked_by_sections_fail_closed(self) -> None:
        legacy = (
            "# Legacy\n\n"
            "## Ticket ID\n\n08\n\n"
            "## Execution Mode\n\nAFK\n\n"
            "## Blocked By\n\n- 04\n\n"
            "## Blocked By\n\n- 05\n"
        )

        with self.assertRaisesRegex(
            ContractError,
            r"duplicate\.md: duplicate legacy section 'Blocked By'",
        ):
            migrate_ticket_text(legacy, source="duplicate.md")

    def test_legacy_blocker_supported_forms_migrate_deterministically(self) -> None:
        cases = {
            "absent": ("", []),
            "empty": ("## Blocked By\n\n", []),
            "none": ("## Blocked By\n\n- None\n", []),
            "none-explained": (
                "## Blocked By\n\n- None - can start immediately.\n",
                [],
            ),
            "links": (
                "## Blocked By\n\n"
                "- [04-parser.md](./done/04-parser.md)\n"
                "- [05-validator.md](./05-validator.md)\n",
                ["04", "05"],
            ),
            "completed-link": (
                "## Blocked By\n\n"
                "- [01-research-current-pipeline.md]"
                "(./01-research-current-pipeline.md) — completed.\n",
                ["01"],
            ),
            "plain": (
                "## Blocked By\n\n- 04\n- \"05\"\n- `06`\n",
                ["04", "05", "06"],
            ),
        }
        for name, (blocked_section, expected) in cases.items():
            with self.subTest(name=name):
                legacy = (
                    "# Legacy\n\n"
                    "## Ticket ID\n\n08\n\n"
                    "## Execution Mode\n\nAFK\n\n"
                    f"{blocked_section}"
                )
                migrated = migrate_ticket_text(legacy, source=f"{name}.md")
                parsed = parse_ticket_markdown(migrated)
                self.assertEqual(expected, parsed.envelope["blocked_by"])
                self.assertEqual(migrated, serialize_ticket_markdown(
                    parsed.envelope,
                    parsed.body,
                ))

        reference = (
            SKILL_ROOT / "references" / "ticket-envelope-v1.md"
        ).read_text(encoding="utf-8")
        self.assertIn("Explicit legacy migration forms", reference)
        self.assertIn("None - can start immediately.", reference)

    def test_migrated_candidate_is_validated_before_return(self) -> None:
        invalid_cases = {
            "invalid-id": (
                "## Ticket ID\n\nbad id\n\n## Execution Mode\n\nAFK\n",
                "invalid ticket_id",
            ),
            "duplicate-blocker": (
                "## Ticket ID\n\n08\n\n## Execution Mode\n\nAFK\n\n"
                "## Blocked By\n\n- 04\n- 04\n",
                "duplicate blocker",
            ),
            "self-blocker": (
                "## Ticket ID\n\n08\n\n## Execution Mode\n\nAFK\n\n"
                "## Blocked By\n\n- 08\n",
                "ticket cannot block itself",
            ),
        }
        for name, (sections, message) in invalid_cases.items():
            with self.subTest(name=name):
                with self.assertRaisesRegex(
                    ContractError,
                    rf"{re.escape(name)}\.md: {message}",
                ):
                    migrate_ticket_text(
                        f"# Legacy\n\n{sections}",
                        source=f"{name}.md",
                    )

    def test_direct_migrate_recognizes_lf_and_crlf_canonical_front_matter(self) -> None:
        canonical_lf = serialize_ticket_markdown(
            dict(VALID_ENVELOPE, ticket_id="09", blocked_by=[]),
            "# Canonical\n",
        )
        canonical_crlf = canonical_lf.replace("\n", "\r\n")
        for name, canonical in (
            ("lf", canonical_lf),
            ("crlf", canonical_crlf),
        ):
            with self.subTest(name=name), self.assertRaisesRegex(
                ContractError,
                "already uses versioned front matter",
            ):
                migrate_ticket_text(canonical, source=f"{name}.md")

    def test_emit_and_parse_cli_use_normalized_json_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            envelope_path = root / "envelope.json"
            body_path = root / "body.md"
            ticket_path = root / "ticket.md"
            envelope_path.write_text(json.dumps(VALID_ENVELOPE), encoding="utf-8")
            body_path.write_text("# Contract CLI\n", encoding="utf-8")

            emit = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "scripts" / "ticket-autopilot.py"),
                    "ticket-emit",
                    str(envelope_path),
                    str(body_path),
                    "--output",
                    str(ticket_path),
                ],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, emit.returncode, emit.stderr)
            emit_payload = json.loads(emit.stdout)
            self.assertTrue(emit_payload["ok"])
            self.assertEqual(str(ticket_path.resolve()), emit_payload["data"]["output"])

            parse = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "scripts" / "ticket-autopilot.py"),
                    "ticket-parse",
                    str(ticket_path),
                ],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, parse.returncode, parse.stderr)
            payload = json.loads(parse.stdout)
            self.assertTrue(payload["ok"])
            self.assertEqual(
                {"body": "# Contract CLI\n", "envelope": VALID_ENVELOPE},
                payload["data"],
            )

    def test_migrate_skips_valid_lf_and_crlf_tickets_in_mixed_folder(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            lf_ticket = root / "01-lf.md"
            crlf_ticket = root / "02-crlf.md"
            legacy_ticket = root / "03-legacy.md"
            canonical_lf = serialize_ticket_markdown(
                dict(VALID_ENVELOPE, ticket_id="01", blocked_by=[]),
                "# LF\n",
            )
            canonical_crlf = serialize_ticket_markdown(
                dict(VALID_ENVELOPE, ticket_id="02", blocked_by=["01"]),
                "# CRLF\n",
            ).replace("\n", "\r\n")
            lf_ticket.write_text(canonical_lf, encoding="utf-8")
            crlf_ticket.write_bytes(canonical_crlf.encode("utf-8"))
            legacy_ticket.write_text(
                "# Legacy\n\n## Execution Mode\n\nAFK\n",
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "scripts" / "ticket-autopilot.py"),
                    "migrate",
                    str(root),
                    "--write",
                ],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(0, completed.returncode, completed.stderr)
            payload = json.loads(completed.stdout)["data"]
            self.assertEqual(["03-legacy.md"], payload["changed"])
            self.assertEqual(["01-lf.md", "02-crlf.md"], payload["skipped"])
            self.assertEqual(canonical_lf, lf_ticket.read_text(encoding="utf-8"))
            self.assertEqual(canonical_crlf.encode("utf-8"), crlf_ticket.read_bytes())
            self.assertEqual(
                1,
                crlf_ticket.read_text(encoding="utf-8").count("ticket_schema:"),
            )
            self.assertEqual(
                "03",
                parse_ticket_markdown(
                    legacy_ticket.read_text(encoding="utf-8")
                ).envelope["ticket_id"],
            )

    def test_migrate_rejects_invalid_crlf_front_matter_without_prepending(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            ticket = root / "04-invalid.md"
            original = (
                "---\r\n"
                "ticket_schema: 1\r\n"
                'ticket_id: "04"\r\n'
                "execution_mode: AFK\r\n"
                "blocked_by: []\r\n"
                "unknown_field: true\r\n"
                "---\r\n\r\n"
                "# Invalid\r\n"
            ).encode("utf-8")
            ticket.write_bytes(original)

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "scripts" / "ticket-autopilot.py"),
                    "migrate",
                    str(ticket),
                    "--write",
                ],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(2, completed.returncode)
            payload = json.loads(completed.stdout)
            self.assertIn("undeclared key", payload["error"]["message"])
            self.assertEqual(original, ticket.read_bytes())
            self.assertEqual(1, ticket.read_bytes().count(b"ticket_schema:"))

    def test_migrate_rejects_noncanonical_separator_without_rewrite(self) -> None:
        variants = {
            "missing-lf": b"---\nticket_schema: 1\nticket_id: \"04\"\n"
            b"execution_mode: AFK\nblocked_by: []\n---\n# Missing\n",
            "extra-crlf": b"---\r\nticket_schema: 1\r\nticket_id: \"04\"\r\n"
            b"execution_mode: AFK\r\nblocked_by: []\r\n---\r\n\r\n\r\n# Extra\r\n",
        }
        for name, original in variants.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                ticket = root / "04-invalid.md"
                ticket.write_bytes(original)
                completed = subprocess.run(
                    [
                        sys.executable,
                        str(SKILL_ROOT / "scripts" / "ticket-autopilot.py"),
                        "migrate",
                        str(ticket),
                        "--write",
                    ],
                    cwd=root,
                    text=True,
                    capture_output=True,
                    check=False,
                )

                self.assertEqual(2, completed.returncode)
                payload = json.loads(completed.stdout)
                self.assertIn("exactly one blank line", payload["error"]["message"])
                self.assertEqual(original, ticket.read_bytes())
                self.assertEqual(1, ticket.read_bytes().count(b"ticket_schema:"))

    def test_folder_migrate_preflights_all_files_before_any_write(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            valid = root / "01-valid.md"
            invalid = root / "02-invalid.md"
            valid_original = (
                "# Valid legacy\n\n"
                "## Ticket ID\n\n01\n\n"
                "## Execution Mode\n\nAFK\n\n"
                "## Blocked By\n\n- None - can start immediately.\n"
            ).encode("utf-8")
            invalid_original = (
                "# Invalid legacy\n\n"
                "## Ticket ID\n\n02\n\n"
                "## Execution Mode\n\nAFK\n\n"
                "## Blocked By\n\n- waiting for an unspecified thing\n"
            ).encode("utf-8")
            valid.write_bytes(valid_original)
            invalid.write_bytes(invalid_original)

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "scripts" / "ticket-autopilot.py"),
                    "migrate",
                    str(root),
                    "--write",
                ],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(2, completed.returncode)
            payload = json.loads(completed.stdout)
            self.assertIn(
                "02-invalid.md: legacy Blocked By line 1: unsupported entry",
                payload["error"]["message"],
            )
            self.assertEqual(valid_original, valid.read_bytes())
            self.assertEqual(invalid_original, invalid.read_bytes())
            self.assertNotIn(b"ticket_schema:", valid.read_bytes())

    def test_folder_migrate_rejects_invalid_combined_graph_without_writes(self) -> None:
        cases = {
            "missing": (
                {
                    "01-canonical.md": serialize_ticket_markdown(
                        dict(VALID_ENVELOPE, ticket_id="01", blocked_by=[]),
                        "# Canonical\n",
                    ),
                "02-legacy.md": (
                    "# Legacy\n\n## Ticket ID\n\n02\n\n"
                    "## Execution Mode\n\nAFK\n\n"
                    "## Blocked By\n\n- 99\n"
                    ),
                },
                "02-legacy.md: missing dependency '99'",
            ),
            "duplicate": (
                {
                    "01-canonical.md": serialize_ticket_markdown(
                        dict(VALID_ENVELOPE, ticket_id="01", blocked_by=[]),
                        "# Canonical\n",
                    ),
                "02-legacy.md": (
                    "# Legacy\n\n## Ticket ID\n\n01\n\n"
                    "## Execution Mode\n\nAFK\n"
                ),
                },
                "duplicate ticket_id '01'",
            ),
            "cycle": (
                {
                    "01-canonical.md": serialize_ticket_markdown(
                        dict(VALID_ENVELOPE, ticket_id="01", blocked_by=["02"]),
                        "# Canonical\n",
                    ),
                "02-legacy.md": (
                    "# Legacy\n\n## Ticket ID\n\n02\n\n"
                    "## Execution Mode\n\nAFK\n\n"
                    "## Blocked By\n\n- 01\n"
                    ),
                },
                "dependency cycle: 01 -> 02 -> 01",
            ),
        }
        for name, (files, expected) in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                originals = {}
                for filename, text in files.items():
                    path = root / filename
                    path.write_text(text, encoding="utf-8")
                    originals[path] = path.read_bytes()

                completed = subprocess.run(
                    [
                        sys.executable,
                        str(SKILL_ROOT / "scripts" / "ticket-autopilot.py"),
                        "migrate",
                        str(root),
                        "--write",
                    ],
                    cwd=root,
                    text=True,
                    capture_output=True,
                    check=False,
                )

                self.assertEqual(2, completed.returncode)
                payload = json.loads(completed.stdout)
                self.assertIn(expected, payload["error"]["message"])
                self.assertEqual(
                    originals,
                    {path: path.read_bytes() for path in originals},
                )

    def test_single_file_migrate_preflights_all_siblings_but_writes_only_target(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            canonical = root / "01-canonical.md"
            target = root / "02-target.md"
            legacy_sibling = root / "03-legacy-context.md"
            canonical.write_text(
                serialize_ticket_markdown(
                    dict(VALID_ENVELOPE, ticket_id="01", blocked_by=[]),
                    "# Canonical dependency\n",
                ),
                encoding="utf-8",
            )
            target.write_text(
                "# Target\n\n## Ticket ID\n\n02\n\n"
                "## Execution Mode\n\nAFK\n\n"
                "## Blocked By\n\n- 01\n",
                encoding="utf-8",
            )
            legacy_sibling.write_text(
                "# Legacy context\n\n"
                "## Ticket ID\n\n03\n\n"
                "## Execution Mode\n\nAFK\n\n"
                "## Blocked By\n\n- 02\n",
                encoding="utf-8",
            )
            canonical_before = canonical.read_bytes()
            target_before = target.read_bytes()
            sibling_before = legacy_sibling.read_bytes()

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "scripts" / "ticket-autopilot.py"),
                    "migrate",
                    str(target),
                    "--write",
                ],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(0, completed.returncode, completed.stdout)
            payload = json.loads(completed.stdout)["data"]
            self.assertEqual(["02-target.md"], payload["changed"])
            self.assertEqual([], payload["skipped"])
            self.assertEqual(canonical_before, canonical.read_bytes())
            self.assertEqual(sibling_before, legacy_sibling.read_bytes())
            self.assertNotEqual(target_before, target.read_bytes())
            self.assertEqual(
                ["01"],
                parse_ticket_markdown(
                    target.read_text(encoding="utf-8")
                ).envelope["blocked_by"],
            )

    def test_single_file_migrate_rejects_duplicate_sibling_id_without_writes(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            canonical = root / "01-canonical.md"
            target = root / "02-target.md"
            canonical.write_text(
                serialize_ticket_markdown(
                    dict(VALID_ENVELOPE, ticket_id="01", blocked_by=[]),
                    "# Canonical\n",
                ),
                encoding="utf-8",
            )
            target.write_text(
                "# Duplicate\n\n## Ticket ID\n\n01\n\n"
                "## Execution Mode\n\nAFK\n",
                encoding="utf-8",
            )
            originals = {
                canonical: canonical.read_bytes(),
                target: target.read_bytes(),
            }

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "scripts" / "ticket-autopilot.py"),
                    "migrate",
                    str(target),
                    "--write",
                ],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(2, completed.returncode)
            self.assertIn(
                "duplicate ticket_id '01'",
                json.loads(completed.stdout)["error"]["message"],
            )
            self.assertEqual(
                originals,
                {path: path.read_bytes() for path in originals},
            )

    def test_single_file_migrate_rejects_missing_or_cyclic_graph_without_writes(
        self,
    ) -> None:
        cases = {
            "missing": (
                [],
                ["99"],
                "missing dependency '99'",
            ),
            "cycle": (
                ["02"],
                ["01"],
                "dependency cycle: 01 -> 02 -> 01",
            ),
        }
        for name, (canonical_blockers, target_blockers, expected) in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                canonical = root / "01-canonical.md"
                target = root / "02-target.md"
                canonical.write_text(
                    serialize_ticket_markdown(
                        dict(
                            VALID_ENVELOPE,
                            ticket_id="01",
                            blocked_by=canonical_blockers,
                        ),
                        "# Canonical\n",
                    ),
                    encoding="utf-8",
                )
                blocker_lines = "".join(
                    f"- {blocker}\n" for blocker in target_blockers
                )
                target.write_text(
                    "# Target\n\n## Ticket ID\n\n02\n\n"
                    "## Execution Mode\n\nAFK\n\n"
                    f"## Blocked By\n\n{blocker_lines}",
                    encoding="utf-8",
                )
                originals = {
                    canonical: canonical.read_bytes(),
                    target: target.read_bytes(),
                }

                completed = subprocess.run(
                    [
                        sys.executable,
                        str(SKILL_ROOT / "scripts" / "ticket-autopilot.py"),
                        "migrate",
                        str(target),
                        "--write",
                    ],
                    cwd=root,
                    text=True,
                    capture_output=True,
                    check=False,
                )

                self.assertEqual(2, completed.returncode)
                self.assertIn(
                    expected,
                    json.loads(completed.stdout)["error"]["message"],
                )
                self.assertEqual(
                    originals,
                    {path: path.read_bytes() for path in originals},
                )

    def test_single_file_migrate_accepts_exact_completed_link_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            dependency = root / "01-research-current-pipeline.md"
            target = root / "02-prototype.md"
            dependency.write_text(
                serialize_ticket_markdown(
                    dict(VALID_ENVELOPE, ticket_id="01", blocked_by=[]),
                    "# Research\n",
                ),
                encoding="utf-8",
            )
            target.write_text(
                "# Prototype\n\n"
                "## Ticket ID\n\n02\n\n"
                "## Execution Mode\n\nAFK\n\n"
                "## Blocked By\n\n"
                "- [01-research-current-pipeline.md]"
                "(./01-research-current-pipeline.md) — completed.\n",
                encoding="utf-8",
            )
            dependency_before = dependency.read_bytes()

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "scripts" / "ticket-autopilot.py"),
                    "migrate",
                    str(target),
                    "--write",
                ],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(0, completed.returncode, completed.stdout)
            self.assertEqual(dependency_before, dependency.read_bytes())
            self.assertEqual(
                ["01"],
                parse_ticket_markdown(
                    target.read_text(encoding="utf-8")
                ).envelope["blocked_by"],
            )

    def test_folder_migrate_completed_link_preflight_is_atomic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            dependency = root / "01-research-current-pipeline.md"
            valid = root / "02-prototype.md"
            invalid = root / "03-invalid-status.md"
            dependency.write_text(
                serialize_ticket_markdown(
                    dict(VALID_ENVELOPE, ticket_id="01", blocked_by=[]),
                    "# Research\n",
                ),
                encoding="utf-8",
            )
            valid.write_text(
                "# Prototype\n\n"
                "## Ticket ID\n\n02\n\n"
                "## Execution Mode\n\nAFK\n\n"
                "## Blocked By\n\n"
                "- [01-research-current-pipeline.md]"
                "(./01-research-current-pipeline.md) — completed.\n",
                encoding="utf-8",
            )
            invalid.write_text(
                "# Invalid\n\n"
                "## Ticket ID\n\n03\n\n"
                "## Execution Mode\n\nAFK\n\n"
                "## Blocked By\n\n"
                "- [01-research-current-pipeline.md]"
                "(./01-research-current-pipeline.md) — in progress.\n",
                encoding="utf-8",
            )
            originals = {
                path: path.read_bytes()
                for path in (dependency, valid, invalid)
            }

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "scripts" / "ticket-autopilot.py"),
                    "migrate",
                    str(root),
                    "--write",
                ],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(2, completed.returncode)
            self.assertIn(
                "03-invalid-status.md: legacy Blocked By line 1: unsupported entry",
                json.loads(completed.stdout)["error"]["message"],
            )
            self.assertEqual(
                originals,
                {path: path.read_bytes() for path in originals},
            )


if __name__ == "__main__":
    unittest.main()
