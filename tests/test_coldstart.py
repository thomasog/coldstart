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

SCRIPT = Path(__file__).resolve().parent.parent / "plugin/skills/coldstart/scripts/coldstart.py"
spec = importlib.util.spec_from_file_location("coldstart", SCRIPT)
coldstart = importlib.util.module_from_spec(spec)
sys.modules["coldstart"] = coldstart
spec.loader.exec_module(coldstart)

FINISHED_AGENTS = "# Move\n\nDone when moved.\n\n<!-- coldstart 1.1 -->\n"
IMPORTS = "\n".join(coldstart.IMPORTS) + "\n"


class FolderTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def write(self, name, content=""):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def read(self, name):
        return (self.root / name).read_text(encoding="utf-8")

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
        self.assertFalse(report["configured"])
        self.assertEqual(report["files"], ["contract.pdf"])

    def test_reports_code_and_its_scripts(self):
        self.write("package.json", '{"scripts": {"test": "node --test"}}')
        self.write("node_modules/dep/index.js")
        _, report = self.run_cli("scan")
        self.assertEqual(report["kind"], "code")
        self.assertEqual(report["scripts"], {"test": "node --test"})
        self.assertEqual(report["files"], ["package.json"])

    def test_reads_a_manifest_with_a_bom(self):
        (self.root / "package.json").write_bytes(b'\xef\xbb\xbf{"scripts": {"test": "x"}}')
        self.assertEqual(self.run_cli("scan")[1]["scripts"], {"test": "x"})

    def test_survives_an_unreadable_manifest(self):
        (self.root / "package.json").write_bytes(b"\xff\xfe not json")
        self.assertEqual(self.run_cli("scan")[1]["scripts"], {})

    def test_finds_instructions_and_a_configured_folder(self):
        self.write("CLAUDE.md")
        self.write(".ai/HANDOFF.md")
        _, report = self.run_cli("scan")
        self.assertEqual(report["instructions"], ["CLAUDE.md"])
        self.assertTrue(report["configured"])

    def test_truncates_a_huge_folder(self):
        with mock.patch.object(coldstart, "MAX_FILES", 3):
            for n in range(6):
                self.write(f"file{n}.txt")
            _, report = self.run_cli("scan")
        self.assertTrue(report["truncated"])
        self.assertEqual(len(report["files"]), 3)

    def test_never_opens_documents(self):
        self.write("secret.pdf", "private")
        self.write("AGENTS.md", "private")
        self.write(".codex/report.md", "private")
        self.write("package.json", "{}")
        opened = []
        real = Path.read_text

        def spy(path, *args, **kwargs):
            opened.append(path.name)
            return real(path, *args, **kwargs)

        with mock.patch.object(Path, "read_text", spy):
            self.run_cli("scan")
        self.assertEqual(set(opened), {"package.json"})


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
        self.assertEqual(self.read(".claude/CLAUDE.md"), "mine")
        self.assertEqual(report["created"] + report["merged"], [])

    def test_keeps_the_users_settings_and_reports_the_merge(self):
        self.write(".claude/settings.json", '{"plansDirectory": "./mine", "autoMemoryEnabled": true, "permissions": {"deny": ["Read(x)"]}}')
        _, report = self.run_cli("init", "--claude")
        settings = json.loads(self.read(".claude/settings.json"))
        self.assertEqual(report["merged"], [".claude/settings.json"])
        self.assertEqual(settings["plansDirectory"], "./mine")
        self.assertIs(settings["autoMemoryEnabled"], True)
        self.assertIn("Read(x)", settings["permissions"]["deny"])
        self.assertIn("Read(.env)", settings["permissions"]["deny"])

    def test_broken_settings_stop_before_any_write(self):
        self.write(".claude/settings.json", "{broken")
        self.assertEqual(self.run_cli("init", "--claude")[0], 2)
        self.assertFalse((self.root / ".ai").exists())
        self.assertFalse((self.root / ".claude/CLAUDE.md").exists())

    def test_a_non_utf8_gitignore_stops_before_any_write(self):
        (self.root / ".gitignore").write_bytes(b"caf\xe9\n")
        self.assertEqual(self.run_cli("init", "--git")[0], 2)
        self.assertEqual((self.root / ".gitignore").read_bytes(), b"caf\xe9\n")
        self.assertFalse((self.root / ".ai").exists())

    def test_appends_only_missing_gitignore_lines(self):
        self.write(".gitignore", ".env")
        self.run_cli("init", "--git")
        lines = self.read(".gitignore").splitlines()
        self.assertEqual(lines.count(".env"), 1)
        self.assertIn(".ai/scratch/", lines)
        self.assertTrue((self.root / ".git").is_dir())

    def test_stops_without_git_before_any_write(self):
        with mock.patch.object(coldstart.shutil, "which", return_value=None):
            code, report = self.run_cli("init", "--git", "--claude")
        self.assertEqual(code, 2)
        self.assertIn("git is not installed", report["error"])
        self.assertEqual(list(self.root.iterdir()), [])

    def test_dry_run_changes_nothing(self):
        _, report = self.run_cli("init", "--claude", "--git", "--dry-run")
        self.assertIn(".claude/CLAUDE.md", report["created"])
        self.assertEqual(list(self.root.iterdir()), [])


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

    def test_flags_the_real_template_as_unfilled(self):
        self.finished_folder()
        shutil.copy(coldstart.ASSETS / "AGENTS.md", self.root / "AGENTS.md")
        shutil.copy(coldstart.ASSETS / "HANDOFF.md", self.root / ".ai/HANDOFF.md")
        self.assert_problem("unfilled placeholder in AGENTS.md")
        self.assert_problem("unfilled placeholder in .ai/HANDOFF.md")

    def test_accepts_the_memory_template_as_it_is(self):
        self.finished_folder()
        shutil.copy(coldstart.ASSETS / "MEMORY.md", self.root / ".ai/memory/MEMORY.md")
        self.assertEqual(self.run_cli("check")[0], 0)

    def test_flags_absolute_paths(self):
        self.finished_folder()
        self.write("AGENTS.md", FINISHED_AGENTS + "See C:\\Users\\ana\\file\n")
        self.assert_problem("absolute path")

    def test_allows_ordinary_angle_brackets_and_urls(self):
        self.finished_folder()
        extra = "Ana <ana@example.com>, List<String>, Map<String, Int>, <br>, <a href=\"x\">, https://x.com/home/page and `<tag name>`\n"
        self.write("AGENTS.md", FINISHED_AGENTS + extra)
        self.assertEqual(self.run_cli("check"), (0, {"ok": True, "problems": []}))

    def test_flags_a_missing_marker_and_length(self):
        self.finished_folder()
        self.write("AGENTS.md", "line\n" * 130)
        self.assert_problem("no version marker")
        self.assert_problem("over 120 lines")

    def test_flags_files_that_should_have_moved(self):
        self.finished_folder()
        self.write("CLAUDE.md")
        self.assert_problem("move to .ai/archive/")

    def test_flags_a_long_memory_index(self):
        self.finished_folder()
        self.write(".ai/memory/MEMORY.md", "- [x](x.md) - y\n" * 51)
        self.assert_problem("memory index is over 50 entries")

    def test_verifies_the_claude_imports_and_settings(self):
        self.finished_folder()
        self.write(".claude/CLAUDE.md", "@../AGENTS.md\n")
        self.assert_problem("missing import in .claude/CLAUDE.md: @../.ai/HANDOFF.md")
        self.assert_problem("missing: .claude/settings.json")

    def test_ignores_a_claude_folder_without_the_adapter(self):
        self.finished_folder()
        self.write(".claude/notes.txt")
        self.assertEqual(self.run_cli("check")[0], 0)

    def test_passes_a_folder_with_a_complete_adapter(self):
        self.finished_folder()
        self.write(".claude/CLAUDE.md", IMPORTS)
        self.write(".claude/settings.json", "{}")
        self.assertEqual(self.run_cli("check")[0], 0)

    def test_reports_an_undecodable_file_without_changing_it(self):
        self.finished_folder()
        (self.root / "AGENTS.md").write_bytes(b"caf\xe9\n")
        self.assertEqual(self.run_cli("check")[0], 2)
        self.assertEqual((self.root / "AGENTS.md").read_bytes(), b"caf\xe9\n")


class Cli(unittest.TestCase):
    def test_rejects_a_missing_folder(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(coldstart.main(["scan", "no/such/folder"]), 2)
        self.assertIn("error", json.loads(err.getvalue()))


if __name__ == "__main__":
    unittest.main()
