from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from project_binding import (  # noqa: E402
    BindingError,
    config_path,
    describe,
    discover_artefacts,
    git_enabled,
    is_git_repository,
    is_tracked,
    read_binding,
    resolve_project_root,
    write_binding,
)


def git(cwd: Path, *arguments: str) -> None:
    subprocess.run(
        ["git", "-C", str(cwd), *arguments],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def make_project(root: Path, *, git_init: bool, track_docs: bool) -> Path:
    """Build one of the four tracked/untracked combinations."""

    project = root / "project"
    (project / "docs" / "specs").mkdir(parents=True)
    (project / "docs" / "specs" / "a.md").write_text("# a\n", encoding="utf-8")
    (project / "docs" / "specs" / "b.md").write_text("# b\n", encoding="utf-8")
    if git_init:
        git(project, "init", "--initial-branch=main")
        git(project, "config", "user.email", "test@example.invalid")
        git(project, "config", "user.name", "Test")
        if track_docs:
            git(project, "add", "docs")
            git(project, "commit", "-m", "docs")
        else:
            (project / ".gitignore").write_text("docs/\n", encoding="utf-8")
            git(project, "add", ".gitignore")
            git(project, "commit", "-m", "ignore docs")
    return project


def make_wiki(root: Path, project: Path, *, git_mode: str = "auto") -> Path:
    wiki = root / "wiki-root"
    wiki.mkdir()
    write_binding(wiki, project, git_mode=git_mode)
    return wiki


class ProjectBindingTests(unittest.TestCase):
    def test_binding_round_trips_and_validates_its_own_shape(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = make_project(root, git_init=False, track_docs=False)
            wiki = make_wiki(root, project)

            self.assertTrue(config_path(wiki).is_file())
            document = read_binding(wiki)
            self.assertEqual(1, document["schema"])
            self.assertEqual(str(project), document["project_root"])
            self.assertIn("docs/specs/*.md", document["docs_globs"])

            config_path(wiki).write_text('{"schema": 99}', encoding="utf-8")
            with self.assertRaisesRegex(BindingError, "schema must be 1"):
                read_binding(wiki)

    def test_the_four_tracked_combinations_all_resolve_without_raising(self) -> None:
        """A wiki may be committed or ignored and docs may be tracked or not.

        All four are valid inputs. The point of the test is that none raises and none
        conflates 'not a repository' with 'not tracked'.
        """

        for git_init in (True, False):
            for track_docs in (True, False):
                with self.subTest(git_init=git_init, track_docs=track_docs):
                    with tempfile.TemporaryDirectory() as temporary:
                        root = Path(temporary)
                        project = make_project(
                            root, git_init=git_init, track_docs=track_docs
                        )
                        wiki = make_wiki(root, project)

                        self.assertEqual(project, resolve_project_root(wiki))
                        self.assertEqual(git_init, is_git_repository(project))
                        self.assertEqual(
                            git_init and track_docs,
                            is_tracked(project, "docs/specs/a.md"),
                        )
                        self.assertEqual(
                            ["docs/specs/a.md", "docs/specs/b.md"],
                            discover_artefacts(wiki),
                        )

    def test_untracked_artefact_in_a_repository_is_not_the_same_as_no_repository(
        self,
    ) -> None:
        """The two facts stay separable, which is what the provenance ladder needs."""

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = make_project(root, git_init=True, track_docs=False)
            wiki = make_wiki(root, project)

            self.assertTrue(is_git_repository(project))
            self.assertFalse(is_tracked(project, "docs/specs/a.md"))
            report = describe(wiki)
            self.assertTrue(report["is_git_repository"])
            self.assertEqual(0, report["tracked_artefact_count"])

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = make_project(root, git_init=False, track_docs=False)
            wiki = make_wiki(root, project)

            self.assertFalse(is_git_repository(project))
            self.assertFalse(is_tracked(project, "docs/specs/a.md"))
            report = describe(wiki)
            self.assertFalse(report["is_git_repository"])
            self.assertIsNone(
                report["tracked_artefact_count"],
                "a non-repository must report unknown, not zero",
            )

    def test_resolution_from_a_worktree_matches_the_main_tree(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = make_project(root, git_init=True, track_docs=True)
            linked = root / "linked-worktree"
            git(project, "worktree", "add", str(linked), "-b", "side")
            try:
                wiki_main = make_wiki(root, project)
                wiki_linked = root / "wiki-linked"
                wiki_linked.mkdir()
                write_binding(wiki_linked, linked)

                self.assertTrue(is_git_repository(linked))
                self.assertTrue(is_tracked(linked, "docs/specs/a.md"))
                self.assertEqual(
                    discover_artefacts(wiki_main), discover_artefacts(wiki_linked)
                )
                self.assertEqual(
                    describe(wiki_main)["tracked_artefact_count"],
                    describe(wiki_linked)["tracked_artefact_count"],
                )
            finally:
                git(project, "worktree", "remove", "--force", str(linked))

    def test_a_moved_project_fails_loudly_and_never_falls_back_to_cwd(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = make_project(root, git_init=False, track_docs=False)
            wiki = make_wiki(root, project)
            moved = root / "moved"
            project.rename(moved)

            with self.assertRaises(BindingError) as raised:
                resolve_project_root(wiki)
            message = str(raised.exception)
            self.assertIn(str(project), message, "the attempted path must be named")
            self.assertIn("may have moved", message)

    def test_git_mode_off_takes_git_out_of_the_picture(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = make_project(root, git_init=True, track_docs=True)
            wiki = make_wiki(root, project, git_mode="off")

            self.assertTrue(is_git_repository(project))
            self.assertFalse(git_enabled(wiki))
            self.assertFalse(describe(wiki)["git_enabled"])

    def test_a_missing_binding_names_the_file_it_expected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            wiki = Path(temporary) / "empty"
            wiki.mkdir()
            with self.assertRaisesRegex(BindingError, "no wiki binding at"):
                read_binding(wiki)


if __name__ == "__main__":
    unittest.main()
