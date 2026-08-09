from __future__ import annotations

import json
import subprocess
import tempfile
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
CLI = SCRIPTS / "ticket-autopilot.py"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from autopilot.artifact_audit import audit_artifacts
from autopilot.ticket_contract import serialize_ticket_markdown


def artifact_graph(
    artifact_id: str,
    role: str,
    ownership: str,
    *,
    children: tuple[str, ...] = (),
    produces: tuple[str, ...] = (),
    related: tuple[str, ...] = (),
) -> str:
    lines = [
        "# Artifact",
        "",
        "## Artifact Graph",
        "",
        f"- Artifact ID: `{artifact_id}`",
        f"- Role: `{role}`",
        f"- {ownership}",
    ]
    for heading, links in (
        ("Children", children),
        ("Produces", produces),
        ("Related", related),
    ):
        if links:
            lines.extend(("", f"### {heading}", ""))
            lines.extend(f"- [{Path(link).stem}]({link})" for link in links)
    return "\n".join(lines) + "\n"


def ticket_artifact(
    ticket_id: str,
    graph: str,
    *,
    blockers: tuple[str, ...] = (),
) -> str:
    return serialize_ticket_markdown(
        {
            "ticket_schema": 1,
            "ticket_id": ticket_id,
            "execution_mode": "AFK",
            "blocked_by": list(blockers),
        },
        graph,
    )


class ArtifactAuditTests(unittest.TestCase):
    def test_valid_reciprocal_root_and_child_form_one_graph(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            specs = repo / "docs" / "specs"
            specs.mkdir(parents=True)
            (specs / "map.md").write_text(
                artifact_graph(
                    "artifact:map",
                    "wayfinder",
                    "Standalone: true",
                    children=("./decision.md",),
                ),
                encoding="utf-8",
            )
            (specs / "decision.md").write_text(
                artifact_graph(
                    "artifact:decision",
                    "spec",
                    "Parent: [Map](./map.md)",
                ),
                encoding="utf-8",
            )

            result = audit_artifacts(repo)

        self.assertEqual(1, result["schema"])
        self.assertEqual([], result["errors"])
        self.assertEqual([], result["warnings"])
        self.assertEqual([], result["unreferenced"])
        self.assertEqual(
            ["artifact:decision", "artifact:map"],
            [node["id"] for node in result["nodes"]],
        )

    def test_legacy_markdown_is_warned_and_reported_as_unreferenced(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            specs = repo / "docs" / "specs"
            specs.mkdir(parents=True)
            legacy = specs / "legacy.md"
            legacy.write_text("# Legacy spec\n", encoding="utf-8")

            result = audit_artifacts(repo)

        self.assertEqual([], result["errors"])
        self.assertEqual(
            [
                {
                    "code": "legacy-artifact",
                    "message": "managed Markdown has no Artifact Graph section",
                    "path": "docs/specs/legacy.md",
                }
            ],
            result["warnings"],
        )
        self.assertEqual(
            [
                {
                    "code": "unreferenced-artifact",
                    "message": "managed Markdown is not canonically referenced",
                    "path": "docs/specs/legacy.md",
                }
            ],
            result["unreferenced"],
        )
        self.assertEqual(
            {
                "automatic_changes": False,
                "required": 1,
                "paths": ["docs/specs/legacy.md"],
            },
            result["migration"],
        )

    def test_strict_graph_requires_identity_role_and_one_ownership_choice(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            tickets = repo / "docs" / "tickets"
            tickets.mkdir(parents=True)
            (tickets / "broken.md").write_text(
                ticket_artifact("T-01", """# Broken

## Artifact Graph

- Role: `task`
- Standalone: true
- Parent: [Owner](../../specs/owner.md)
"""),
                encoding="utf-8",
            )

            result = audit_artifacts(repo)

        self.assertEqual(
            [
                "invalid-role",
                "invalid-root-parent",
                "missing-artifact-id",
                "standalone-ticket",
            ],
            sorted(item["code"] for item in result["errors"]),
        )

    def test_canonical_links_must_resolve_inside_managed_roots(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            specs = repo / "docs" / "specs"
            specs.mkdir(parents=True)
            (repo / "outside.md").write_text("# Outside\n", encoding="utf-8")
            (specs / "map.md").write_text(
                artifact_graph(
                    "artifact:map",
                    "wayfinder",
                    "Standalone: true",
                    related=("./missing.md", "../../outside.md"),
                ),
                encoding="utf-8",
            )

            result = audit_artifacts(repo)

        self.assertEqual(
            ["broken-link", "path-escape"],
            sorted(item["code"] for item in result["errors"]),
        )

    def test_duplicate_artifact_ids_are_reported_without_inference(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            specs = repo / "docs" / "specs"
            specs.mkdir(parents=True)
            for name in ("one.md", "two.md"):
                (specs / name).write_text(
                    artifact_graph("artifact:same", "spec", "Standalone: true"),
                    encoding="utf-8",
                )

            result = audit_artifacts(repo)

        duplicate = [
            item for item in result["errors"] if item["code"] == "duplicate-artifact-id"
        ]
        self.assertEqual(1, len(duplicate))
        self.assertEqual(
            ["docs/specs/one.md", "docs/specs/two.md"], duplicate[0]["paths"]
        )

    def test_parent_and_owner_edges_must_be_reciprocal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            specs = repo / "docs" / "specs"
            specs.mkdir(parents=True)
            (specs / "owner.md").write_text(
                artifact_graph("artifact:owner", "spec", "Standalone: true"),
                encoding="utf-8",
            )
            (specs / "child.md").write_text(
                artifact_graph(
                    "artifact:child", "spec", "Parent: [Owner](./owner.md)"
                ),
                encoding="utf-8",
            )

            result = audit_artifacts(repo)

        self.assertEqual(
            ["reciprocity-mismatch"],
            [item["code"] for item in result["errors"]],
        )

    def test_ownership_cycles_are_errors_but_related_cycles_are_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            specs = repo / "docs" / "specs"
            specs.mkdir(parents=True)
            (specs / "one.md").write_text(
                artifact_graph(
                    "artifact:one",
                    "spec",
                    "Parent: [Two](./two.md)",
                    children=("./two.md",),
                    related=("./two.md",),
                ),
                encoding="utf-8",
            )
            (specs / "two.md").write_text(
                artifact_graph(
                    "artifact:two",
                    "spec",
                    "Parent: [One](./one.md)",
                    children=("./one.md",),
                    related=("./one.md",),
                ),
                encoding="utf-8",
            )

            result = audit_artifacts(repo)

        self.assertEqual(
            ["hierarchy-cycle"],
            [item["code"] for item in result["errors"]],
        )

    def test_research_ticket_owns_its_produced_result(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            specs = repo / "docs" / "specs"
            tickets = repo / "docs" / "tickets" / "research"
            research = repo / "docs" / "research"
            specs.mkdir(parents=True)
            tickets.mkdir(parents=True)
            research.mkdir(parents=True)
            (specs / "owner.md").write_text(
                artifact_graph(
                    "artifact:owner",
                    "spec",
                    "Standalone: true",
                    children=("../tickets/research/01.md",),
                ),
                encoding="utf-8",
            )
            (tickets / "01.md").write_text(
                ticket_artifact(
                    "R-01",
                    artifact_graph(
                        "artifact:research-ticket",
                        "ticket",
                        "Parent: [Owner](../../specs/owner.md)",
                        produces=("../../research/result.md",),
                    ),
                ),
                encoding="utf-8",
            )
            (research / "result.md").write_text(
                artifact_graph(
                    "artifact:result",
                    "research",
                    "Parent: [Research ticket](../tickets/research/01.md)",
                ),
                encoding="utf-8",
            )

            result = audit_artifacts(repo)

        self.assertEqual([], result["errors"])

    def test_produces_is_ticket_only_and_may_not_duplicate_children(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            specs = repo / "docs" / "specs"
            specs.mkdir(parents=True)
            (specs / "owner.md").write_text(
                artifact_graph(
                    "artifact:owner",
                    "spec",
                    "Standalone: true",
                    children=("./child.md",),
                    produces=("./child.md",),
                ),
                encoding="utf-8",
            )
            (specs / "child.md").write_text(
                artifact_graph(
                    "artifact:child", "spec", "Parent: [Owner](./owner.md)"
                ),
                encoding="utf-8",
            )

            result = audit_artifacts(repo)

        codes = {item["code"] for item in result["errors"]}
        self.assertIn("invalid-produces-owner", codes)
        self.assertIn("duplicate-ownership-edge", codes)

    def test_ticket_nodes_expose_canceled_dependency_readiness_without_cascade(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            specs = repo / "docs" / "specs"
            group = repo / "docs" / "tickets" / "series"
            canceled = group / "canceled"
            specs.mkdir(parents=True)
            canceled.mkdir(parents=True)
            (specs / "owner.md").write_text(
                artifact_graph(
                    "artifact:owner",
                    "spec",
                    "Standalone: true",
                    children=(
                        "../tickets/series/canceled/01.md",
                        "../tickets/series/02.md",
                    ),
                ),
                encoding="utf-8",
            )
            (canceled / "01.md").write_text(
                ticket_artifact(
                    "01",
                    artifact_graph(
                        "artifact:ticket-01",
                        "ticket",
                        "Parent: [Owner](../../../specs/owner.md)",
                    ),
                ),
                encoding="utf-8",
            )
            (group / "02.md").write_text(
                ticket_artifact(
                    "02",
                    artifact_graph(
                        "artifact:ticket-02",
                        "ticket",
                        "Parent: [Owner](../../specs/owner.md)",
                    ),
                    blockers=("01",),
                ),
                encoding="utf-8",
            )

            result = audit_artifacts(repo)

        tickets = {
            node["id"]: node["ticket"]
            for node in result["nodes"]
            if node["role"] == "ticket"
        }
        self.assertEqual("canceled", tickets["artifact:ticket-01"]["disposition"])
        self.assertEqual("open", tickets["artifact:ticket-02"]["disposition"])
        self.assertEqual("blocked", tickets["artifact:ticket-02"]["readiness"])
        self.assertEqual(
            [{"ticket_id": "01", "reason": "dependency-canceled"}],
            tickets["artifact:ticket-02"]["readiness_causes"],
        )

    def test_symlinked_artifacts_fail_closed_without_mutating_sources(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            specs = repo / "docs" / "specs"
            specs.mkdir(parents=True)
            outside = repo / "outside.md"
            content = artifact_graph(
                "artifact:outside", "spec", "Standalone: true"
            )
            outside.write_text(content, encoding="utf-8")
            escaped = specs / "escaped.md"
            escaped.symlink_to(outside)

            result = audit_artifacts(repo)

            self.assertTrue(escaped.is_symlink())
            self.assertEqual(content, outside.read_text(encoding="utf-8"))

        self.assertEqual([], result["nodes"])
        self.assertEqual(["path-escape"], [item["code"] for item in result["errors"]])

    def test_cli_emits_deterministic_json_and_human_reports_without_a_repo(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            specs = repo / "docs" / "specs"
            specs.mkdir(parents=True)
            (specs / "root.md").write_text(
                artifact_graph("artifact:root", "spec", "Standalone: true"),
                encoding="utf-8",
            )

            json_run = subprocess.run(
                [sys.executable, str(CLI), "artifact-audit", str(repo), "--json"],
                check=False,
                capture_output=True,
                text=True,
            )
            human_runs = [
                subprocess.run(
                    [sys.executable, str(CLI), "artifact-audit", str(repo)],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                for _ in range(2)
            ]

        self.assertEqual(0, json_run.returncode, json_run.stderr)
        payload = json.loads(json_run.stdout)
        self.assertEqual("artifact-audit", payload["command"])
        self.assertEqual(1, payload["data"]["schema"])
        self.assertEqual(0, human_runs[0].returncode, human_runs[0].stderr)
        self.assertEqual(human_runs[0].stdout, human_runs[1].stdout)
        self.assertIn("Artifact audit:", human_runs[0].stdout)
        self.assertIn("ERRORS\t0", human_runs[0].stdout)

    def test_invalid_utf8_is_reported_without_hiding_valid_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            research = repo / "docs" / "research"
            research.mkdir(parents=True)
            (research / "valid.md").write_text(
                artifact_graph("artifact:valid", "research", "Standalone: true"),
                encoding="utf-8",
            )
            (research / "invalid.md").write_bytes(b"\xff\xfe")

            result = audit_artifacts(repo)

        self.assertEqual(["artifact:valid"], [node["id"] for node in result["nodes"]])
        self.assertEqual(
            ["malformed-markdown"], [item["code"] for item in result["warnings"]]
        )

    def test_missing_root_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            missing = Path(temporary) / "missing"
            with self.assertRaises(FileNotFoundError):
                audit_artifacts(missing)

    def test_multiple_parent_links_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            specs = repo / "docs" / "specs"
            specs.mkdir(parents=True)
            for name in ("one.md", "two.md"):
                (specs / name).write_text(
                    artifact_graph(
                        f"artifact:{name}", "spec", "Standalone: true"
                    ),
                    encoding="utf-8",
                )
            (specs / "child.md").write_text(
                artifact_graph(
                    "artifact:child",
                    "spec",
                    "Parent: [One](./one.md) [Two](./two.md)",
                ),
                encoding="utf-8",
            )

            result = audit_artifacts(repo)

        self.assertIn("invalid-root-parent", {item["code"] for item in result["errors"]})

    def test_canonical_reference_keeps_legacy_target_out_of_unreferenced(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            specs = repo / "docs" / "specs"
            specs.mkdir(parents=True)
            (specs / "root.md").write_text(
                artifact_graph(
                    "artifact:root",
                    "spec",
                    "Standalone: true",
                    related=("./legacy.md",),
                ),
                encoding="utf-8",
            )
            (specs / "legacy.md").write_text("# Legacy\n", encoding="utf-8")

            result = audit_artifacts(repo)

        self.assertEqual(["broken-link"], [item["code"] for item in result["errors"]])
        self.assertEqual(["legacy-artifact"], [item["code"] for item in result["warnings"]])
        self.assertEqual([], result["unreferenced"])

    def test_new_managed_markdown_without_graph_is_a_strict_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
            specs = repo / "docs" / "specs"
            specs.mkdir(parents=True)
            new_spec = specs / "new.md"
            new_spec.write_text("# New spec\n", encoding="utf-8")
            before = subprocess.run(
                ["git", "-C", str(repo), "status", "--porcelain"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout

            result = audit_artifacts(repo)

            after = subprocess.run(
                ["git", "-C", str(repo), "status", "--porcelain"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout

        self.assertEqual(before, after)
        self.assertEqual(
            ["missing-artifact-graph"],
            [item["code"] for item in result["errors"]],
        )
        self.assertEqual([], result["warnings"])

    def test_duplicate_graph_sections_and_malformed_relationships_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            specs = repo / "docs" / "specs"
            specs.mkdir(parents=True)
            graph = artifact_graph("artifact:duplicate", "spec", "Standalone: true")
            (specs / "duplicate.md").write_text(
                graph + "\n## Artifact Graph\n",
                encoding="utf-8",
            )
            (specs / "malformed.md").write_text(
                artifact_graph("artifact:malformed", "spec", "Standalone: true")
                + "### Related\n\n- not a Markdown link\n",
                encoding="utf-8",
            )

            result = audit_artifacts(repo)

        self.assertEqual(
            ["duplicate-artifact-graph-section", "malformed-relationship"],
            sorted(item["code"] for item in result["errors"]),
        )

    def test_ticket_envelope_sources_require_graph_role_ticket(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            specs = repo / "docs" / "specs"
            tickets = repo / "docs" / "tickets" / "work"
            specs.mkdir(parents=True)
            tickets.mkdir(parents=True)
            (specs / "owner.md").write_text(
                artifact_graph(
                    "artifact:owner",
                    "spec",
                    "Standalone: true",
                    children=("../tickets/work/01.md",),
                ),
                encoding="utf-8",
            )
            (tickets / "01.md").write_text(
                ticket_artifact(
                    "01",
                    artifact_graph(
                        "artifact:ticket",
                        "spec",
                        "Parent: [Owner](../../specs/owner.md)",
                    ),
                ),
                encoding="utf-8",
            )

            result = audit_artifacts(repo)

        self.assertIn(
            "ticket-role-mismatch", {item["code"] for item in result["errors"]}
        )

    def test_ticket_owned_research_results_require_produces_edge(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            specs = repo / "docs" / "specs"
            tickets = repo / "docs" / "tickets" / "research"
            research = repo / "docs" / "research"
            specs.mkdir(parents=True)
            tickets.mkdir(parents=True)
            research.mkdir(parents=True)
            (specs / "owner.md").write_text(
                artifact_graph(
                    "artifact:owner",
                    "spec",
                    "Standalone: true",
                    children=("../tickets/research/01.md",),
                ),
                encoding="utf-8",
            )
            (tickets / "01.md").write_text(
                ticket_artifact(
                    "01",
                    artifact_graph(
                        "artifact:ticket",
                        "ticket",
                        "Parent: [Owner](../../specs/owner.md)",
                        children=("../../research/result.md",),
                    ),
                ),
                encoding="utf-8",
            )
            (research / "result.md").write_text(
                artifact_graph(
                    "artifact:result",
                    "research",
                    "Parent: [Ticket](../tickets/research/01.md)",
                ),
                encoding="utf-8",
            )

            result = audit_artifacts(repo)

        self.assertIn(
            "research-output-not-produced",
            {item["code"] for item in result["errors"]},
        )

    def test_artifact_graph_examples_inside_fences_are_not_nodes_or_sections(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            specs = repo / "docs" / "specs"
            specs.mkdir(parents=True)
            (specs / "decision.md").write_text(
                artifact_graph("artifact:decision", "spec", "Standalone: true")
                + """
## Example

```markdown
## Artifact Graph

- Artifact ID: `artifact:not-real`
- Role: `ticket`
- Standalone: true
```
""",
                encoding="utf-8",
            )

            result = audit_artifacts(repo)

        self.assertEqual([], result["errors"])
        self.assertEqual(["artifact:decision"], [node["id"] for node in result["nodes"]])

    def test_symlinked_managed_roots_and_subdirectories_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary) / "repo"
            outside = Path(temporary) / "outside"
            specs = repo / "docs" / "specs"
            specs.mkdir(parents=True)
            outside.mkdir()
            (outside / "artifact.md").write_text(
                artifact_graph("artifact:outside", "spec", "Standalone: true"),
                encoding="utf-8",
            )
            (specs / "linked").symlink_to(outside, target_is_directory=True)
            (repo / "docs" / "research").symlink_to(
                outside, target_is_directory=True
            )

            result = audit_artifacts(repo)

        self.assertEqual([], result["nodes"])
        escapes = [item for item in result["errors"] if item["code"] == "path-escape"]
        self.assertEqual(
            ["docs/research", "docs/specs/linked"],
            [item["path"] for item in escapes],
        )


if __name__ == "__main__":
    unittest.main()
