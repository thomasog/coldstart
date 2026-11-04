import contextlib
import importlib.util
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parent.parent / "skills/coldstart/scripts/coldstart.py"
spec = importlib.util.spec_from_file_location("coldstart", SCRIPT)
coldstart = importlib.util.module_from_spec(spec)
sys.modules["coldstart"] = coldstart
spec.loader.exec_module(coldstart)

FINISHED_AGENTS = "# Move\n\nDone when moved.\n\n<!-- coldstart 1.0 -->\n"


class FolderTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def write(self, name, content=""):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def run_cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = coldstart.main([args[0], str(self.root), *args[1:]])
        return code, json.loads(out.getvalue() or err.getvalue())

    def finished_folder(self):
        self.write("AGENTS.md", FINISHED_AGENTS)
        self.write(".ai/HANDOFF.md", "# Handoff\n")
        self.write(".ai/memory/MEMORY.md", "# Memory\n\n`<one line>`\n")


class Scan(FolderTest):
    def test_reports_a_personal_folder(self):
        self.write("contract.pdf")
        code, report = self.run_cli("scan")
        self.assertEqual(code, 0)
        self.assertEqual(report["kind"], "personal")
        self.assertEqual(report["layout"], "none")
        self.assertEqual(report["files"], ["contract.pdf"])

    def test_reports_code_and_its_scripts(self):
        self.write("package.json", '{"scripts": {"test": "node --test"}}')
        self.write("node_modules/dep/index.js")
        _, report = self.run_cli("scan")
        self.assertEqual(report["kind"], "code")
        self.assertEqual(report["scripts"], {"test": "node --test"})
        self.assertEqual(report["files"], ["package.json"])

    def test_finds_instructions_and_the_earlier_layout(self):
        self.write("CLAUDE.md")
        self.write(".agents/HANDOFF.md")
        _, report = self.run_cli("scan")
        self.assertEqual(report["instructions"], ["CLAUDE.md"])
        self.assertEqual(report["layout"], "old")

    def test_reads_the_version_marker(self):
        self.write("AGENTS.md", FINISHED_AGENTS)
        self.assertEqual(self.run_cli("scan")[1]["version"], "1.0")

    def test_never_opens_documents(self):
        self.write("secret.pdf", "private")
        self.write(".codex/report.md", "private")
        self.write("package.json", "{}")
        self.write("AGENTS.md", FINISHED_AGENTS)
        opened = []
        real = Path.read_text

        def spy(path, *args, **kwargs):
            opened.append(path.name)
            return real(path, *args, **kwargs)

        with mock.patch.object(Path, "read_text", spy):
            self.run_cli("scan")
        self.assertEqual(set(opened), {"package.json", "AGENTS.md"})


class Init(FolderTest):
    def test_creates_only_the_state_folder_by_default(self):
        self.run_cli("init")
        self.assertTrue((self.root / ".ai/memory").is_dir())
        self.assertFalse((self.root / ".claude").exists())
        self.assertFalse((self.root / ".gitignore").exists())

    def test_adds_the_claude_adapter(self):
        self.run_cli("init", "--claude")
        for target in coldstart.ADAPTER.values():
            self.assertTrue((self.root / target).is_file(), target)

    def test_never_overwrites_and_can_repeat(self):
        self.write(".claude/CLAUDE.md", "mine")
        self.run_cli("init", "--claude")
        _, report = self.run_cli("init", "--claude")
        self.assertEqual((self.root / ".claude/CLAUDE.md").read_text(encoding="utf-8"), "mine")
        self.assertEqual(report["created"], [])

    def test_merges_existing_settings(self):
        self.write(".claude/settings.json", '{"model": "opus", "permissions": {"deny": ["Read(x)"]}}')
        self.run_cli("init", "--claude")
        settings = json.loads((self.root / ".claude/settings.json").read_text(encoding="utf-8"))
        self.assertEqual(settings["model"], "opus")
        self.assertEqual(settings["plansDirectory"], "./.ai/plans")
        self.assertIn("Read(x)", settings["permissions"]["deny"])
        self.assertIn("Read(.env)", settings["permissions"]["deny"])

    def test_appends_only_missing_gitignore_lines(self):
        self.write(".gitignore", ".env\n")
        self.run_cli("init", "--git")
        lines = (self.root / ".gitignore").read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines.count(".env"), 1)
        self.assertIn(".ai/scratch/", lines)
        self.assertTrue((self.root / ".git").is_dir())

    def test_dry_run_changes_nothing(self):
        _, report = self.run_cli("init", "--claude", "--git", "--dry-run")
        self.assertIn(".ai/memory/", report["created"])
        self.assertEqual(list(self.root.iterdir()), [])


class Upgrade(FolderTest):
    def old_folder(self):
        self.write("AGENTS.md", "Read `.agents/HANDOFF.md`. Skills: `.agents/skills/`.\n")
        self.write(".agents/HANDOFF.md", "See `.agents/memory/MEMORY.md`.\n")
        self.write(".agents/memory/MEMORY.md", "# Memory\n")
        self.write(".agents/skills/demo/SKILL.md", "demo\n")
        self.write(".claude/CLAUDE.md", "@../.agents/HANDOFF.md\n")

    def test_moves_state_and_keeps_skills(self):
        self.old_folder()
        code, report = self.run_cli("upgrade")
        self.assertEqual(code, 0)
        self.assertEqual(report["moved"], ["HANDOFF.md", "memory"])
        self.assertTrue((self.root / ".ai/memory/MEMORY.md").is_file())
        self.assertTrue((self.root / ".agents/skills/demo/SKILL.md").is_file())
        self.assertFalse((self.root / ".agents/HANDOFF.md").exists())

    def test_rewrites_paths_but_not_skills(self):
        self.old_folder()
        self.run_cli("upgrade")
        agents = (self.root / "AGENTS.md").read_text(encoding="utf-8")
        self.assertEqual(agents, "Read `.ai/HANDOFF.md`. Skills: `.agents/skills/`.\n")
        self.assertIn(".ai/memory/", (self.root / ".ai/HANDOFF.md").read_text(encoding="utf-8"))
        self.assertIn("../.ai/", (self.root / ".claude/CLAUDE.md").read_text(encoding="utf-8"))

    def test_removes_an_emptied_folder(self):
        self.write(".agents/HANDOFF.md")
        self.run_cli("upgrade")
        self.assertFalse((self.root / ".agents").exists())

    def test_dry_run_changes_nothing(self):
        self.old_folder()
        _, report = self.run_cli("upgrade", "--dry-run")
        self.assertIn(".ai/HANDOFF.md", report["rewritten"])
        self.assertTrue((self.root / ".agents/HANDOFF.md").is_file())
        self.assertFalse((self.root / ".ai").exists())

    def test_refuses_without_the_earlier_layout(self):
        self.assertEqual(self.run_cli("upgrade")[0], 2)

    def test_refuses_to_overwrite_existing_state(self):
        self.old_folder()
        self.write(".ai/HANDOFF.md", "newer")
        code, report = self.run_cli("upgrade")
        self.assertEqual(code, 2)
        self.assertIn("HANDOFF.md", report["error"])


class Check(FolderTest):
    def test_passes_a_finished_folder(self):
        self.finished_folder()
        self.assertEqual(self.run_cli("check"), (0, {"ok": True, "problems": []}))

    def assert_problem(self, fragment):
        code, report = self.run_cli("check")
        self.assertEqual(code, 1)
        self.assertTrue(any(fragment in problem for problem in report["problems"]), report)

    def test_flags_missing_files(self):
        self.assert_problem("missing: AGENTS.md")

    def test_flags_unfilled_placeholders(self):
        self.finished_folder()
        self.write(".ai/HANDOFF.md", "<The concrete next step.>\n")
        self.assert_problem("unfilled placeholder in .ai/HANDOFF.md")

    def test_flags_absolute_paths(self):
        self.finished_folder()
        self.write("AGENTS.md", FINISHED_AGENTS + "See C:\\Users\\ana\\file\n")
        self.assert_problem("absolute path")

    def test_allows_urls_and_code_spans(self):
        self.finished_folder()
        self.write("AGENTS.md", FINISHED_AGENTS + "https://example.com and `<tag>`\n")
        self.assertEqual(self.run_cli("check")[0], 0)

    def test_flags_old_references_but_not_skills(self):
        self.finished_folder()
        self.write("AGENTS.md", FINISHED_AGENTS + "`.agents/skills/` stays\n")
        self.assertEqual(self.run_cli("check")[0], 0)
        self.write("AGENTS.md", FINISHED_AGENTS + "`.agents/memory/`\n")
        self.assert_problem("reference to .agents/")

    def test_flags_a_missing_marker_and_length(self):
        self.finished_folder()
        self.write("AGENTS.md", "line\n" * 130)
        self.assert_problem("no version marker")
        self.assert_problem("over 120 lines")

    def test_flags_files_that_should_have_moved(self):
        self.finished_folder()
        self.write("CLAUDE.md")
        self.assert_problem("should have moved")

    def test_flags_an_incomplete_adapter(self):
        self.finished_folder()
        self.write(".claude/CLAUDE.md", "@../AGENTS.md\n")
        self.assert_problem("missing: .claude/settings.json")


class Cli(unittest.TestCase):
    def test_rejects_a_missing_folder(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(coldstart.main(["scan", "no/such/folder"]), 2)
        self.assertIn("error", json.loads(err.getvalue()))


if __name__ == "__main__":
    unittest.main()
