import contextlib
import importlib.util
import io
import json
import re
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

FINISHED_AGENTS = "# Move\n\nStart by reading `.ai/HANDOFF.md`.\n"
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
    def test_lists_names_and_skips_dependencies(self):
        self.write("contract.pdf")
        self.write("node_modules/dep/index.js")
        code, report = self.run_cli("scan")
        self.assertEqual(code, 0)
        self.assertFalse(report["configured"])
        self.assertEqual(report["files"], ["contract.pdf"])

    def test_finds_instructions_and_a_configured_folder(self):
        self.write("CLAUDE.md")
        self.finished_folder()
        _, report = self.run_cli("scan")
        self.assertEqual(report["instructions"], ["AGENTS.md", "CLAUDE.md"])
        self.assertTrue(report["configured"])

    def test_a_partial_folder_is_not_configured(self):
        self.write(".ai/HANDOFF.md")
        self.assertFalse(self.run_cli("scan")[1]["configured"])

    def test_names_executable_config_but_not_the_codex_folder(self):
        self.write(".mcp.json")
        self.write(".codex/report.md")
        self.assertEqual(self.run_cli("scan")[1]["instructions"], [".mcp.json"])

    def test_finds_the_repository_above_a_subfolder(self):
        (self.root / ".git").mkdir()
        subfolder = self.root / "packages/foo"
        subfolder.mkdir(parents=True)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            coldstart.main(["scan", str(subfolder)])
        self.assertEqual(json.loads(out.getvalue())["git"], str(self.root.resolve()))

    def test_finds_rules_under_the_agents_folder(self):
        self.write(".agents/rules/style.md")
        self.assertEqual(self.run_cli("scan")[1]["instructions"], [".agents/rules"])

    def test_truncates_a_huge_folder(self):
        with mock.patch.object(coldstart, "MAX_FILES", 3):
            for n in range(6):
                self.write(f"file{n}.txt")
            _, report = self.run_cli("scan")
        self.assertTrue(report["truncated"])
        self.assertEqual(len(report["files"]), 3)

    def test_one_big_folder_leaves_room_for_the_rest(self):
        with mock.patch.object(coldstart, "MAX_PER_FOLDER", 2):
            for n in range(5):
                self.write(f"Photos/img{n}.jpg")
            self.write("contract.pdf")
            self.write("deep/notes/todo.txt")
            _, report = self.run_cli("scan")
        self.assertEqual(report["files"], ["contract.pdf", "Photos/img0.jpg", "Photos/img1.jpg", "Photos/ (+3 more files)", "deep/notes/todo.txt"])

    def test_names_cursor_and_vscode_config_that_runs(self):
        self.write(".cursor/hooks.json")
        self.write(".vscode/mcp.json")
        self.assertEqual(self.run_cli("scan")[1]["instructions"], [".cursor/hooks.json", ".vscode/mcp.json"])

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
        self.assertEqual(opened, [])


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
        self.assertFalse((self.root / ".claude/agents").exists())
        self.assertNotIn("advisorModel", json.loads(self.read(".claude/settings.json")))

    def test_routing_adds_the_helpers_and_the_advisor_and_can_repeat(self):
        self.finished_folder()
        self.run_cli("init", "--routing")
        for target in (*coldstart.ADAPTER.values(), *coldstart.ROUTING.values()):
            self.assertTrue((self.root / target).is_file(), target)
        self.assertEqual(json.loads(self.read(".claude/settings.json"))["advisorModel"], "opus")
        _, report = self.run_cli("init", "--routing")
        self.assertEqual(report["created"] + report["merged"], [])
        self.assertEqual(self.run_cli("check")[0], 0)

    def test_routing_keeps_the_advisor_the_user_chose(self):
        self.write(".claude/settings.json", '{"advisorModel": "fable"}')
        self.run_cli("init", "--routing")
        self.assertEqual(json.loads(self.read(".claude/settings.json"))["advisorModel"], "fable")

    def test_every_helper_sets_its_model_and_effort(self):
        for asset in coldstart.ROUTING:
            frontmatter = (coldstart.ASSETS / asset).read_text(encoding="utf-8").split("---")[1]
            self.assertRegex(frontmatter, r"(?m)^model: (haiku|sonnet)$", asset)
            self.assertRegex(frontmatter, r"(?m)^effort: \w+$", asset)

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

    def test_a_list_of_the_wrong_shape_stops_before_any_write(self):
        self.write(".claude/settings.json", '{"permissions": {"deny": null}}')
        code, report = self.run_cli("init", "--claude")
        self.assertEqual(code, 2)
        self.assertIn("error", report)
        self.assertFalse((self.root / ".ai").exists())

    def test_keeps_non_ascii_settings_readable(self):
        self.write(".claude/settings.json", '{"plansDirectory": "./planos-açaí"}')
        self.run_cli("init", "--claude")
        self.assertIn("açaí", self.read(".claude/settings.json"))

    def test_the_settings_template_holds_nothing_that_runs(self):
        settings = json.loads((coldstart.ASSETS / "settings.json").read_text(encoding="utf-8"))
        self.assertEqual(set(settings), {"plansDirectory", "autoMemoryEnabled", "permissions"})

    def test_a_non_utf8_gitignore_stops_before_any_write(self):
        (self.root / ".gitignore").write_bytes(b"caf\xe9\n")
        self.assertEqual(self.run_cli("init", "--gitignore")[0], 2)
        self.assertEqual((self.root / ".gitignore").read_bytes(), b"caf\xe9\n")
        self.assertFalse((self.root / ".ai").exists())

    def test_adds_only_missing_gitignore_lines_and_no_repository(self):
        self.write(".gitignore", ".env")
        self.run_cli("init", "--gitignore")
        lines = self.read(".gitignore").splitlines()
        self.assertEqual(lines.count(".env"), 1)
        self.assertIn(".ai/scratch/", lines)
        self.assertFalse((self.root / ".git").exists())

    def test_a_negation_the_user_has_still_wins(self):
        self.write(".gitignore", ".env*\n!.env.example\n")
        self.run_cli("init", "--gitignore")
        self.assertEqual(self.read(".gitignore").splitlines()[-1], "!.env.example")

    def test_refuses_the_home_folder_and_any_folder_above_it(self):
        for home in (self.root, self.root / "users/me"):
            with mock.patch.object(coldstart.Path, "home", return_value=home):
                code, report = self.run_cli("init", "--claude")
            self.assertEqual(code, 2)
            self.assertIn("home folder", report["error"])
            self.assertEqual(list(self.root.iterdir()), [])

    def test_keeps_the_line_endings_and_bom_of_a_merged_file(self):
        (self.root / ".gitignore").write_bytes(b"\xef\xbb\xbfdist/\r\n")
        self.run_cli("init", "--gitignore")
        content = (self.root / ".gitignore").read_bytes()
        self.assertTrue(content.startswith(b"\xef\xbb\xbf"))
        self.assertNotIn(b"\n", content.replace(b"\r\n", b""))
        self.assertIn(b".ai/scratch/\r\n", content)

    def test_the_real_adapter_passes_check(self):
        self.finished_folder()
        self.run_cli("init", "--claude", "--gitignore")
        self.assertEqual(self.run_cli("check"), (0, {"ok": True, "problems": []}))
        self.assertFalse((self.root / ".claude/agents/advisor.md").exists())

    def test_the_agents_template_stays_small(self):
        self.assertLessEqual(len((coldstart.ASSETS / "AGENTS.md").read_text(encoding="utf-8").splitlines()), 25)

    def test_refuses_a_link_that_leads_outside(self):
        outside = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, outside, ignore_errors=True)
        try:
            (self.root / ".claude").symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest("this system can't create links")
        code, report = self.run_cli("init", "--claude")
        self.assertEqual(code, 2)
        self.assertIn("leads outside", report["error"])
        self.assertEqual(list(outside.iterdir()), [])


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

    def test_flags_paths_from_this_machine_however_they_are_written(self):
        if len(Path.home().parts) <= 2:
            self.skipTest("a home this short is ignored on purpose")
        home = Path.home().as_posix().split(":")[-1]
        for path in (str(Path.home()), str(Path.home()).lower(), f"/c{home}", f"/mnt/c{home}"):
            self.finished_folder()
            self.write("AGENTS.md", FINISHED_AGENTS + f"See {path}/file\n")
            self.assert_problem("path from this machine")

    def test_allows_paths_that_belong_to_the_project(self):
        self.finished_folder()
        self.write("AGENTS.md", FINISHED_AGENTS + "WORKDIR /srv/node/app, GET /Users/:id, https://x.com/home/page\n")
        self.assertEqual(self.run_cli("check")[0], 0)

    def test_allows_ordinary_angle_brackets_and_urls(self):
        self.finished_folder()
        extra = "Ana <ana@example.com>, List<String>, Map<String, Int>, <br>, <a href=\"x\">, https://x.com/home/page and `<tag name>`\n"
        self.write("AGENTS.md", FINISHED_AGENTS + extra)
        self.assertEqual(self.run_cli("check"), (0, {"ok": True, "problems": []}))

    def test_flags_a_translated_placeholder(self):
        self.finished_folder()
        self.write("AGENTS.md", FINISHED_AGENTS + "<Área de atuação>\n")
        self.assert_problem("unfilled placeholder")

    def test_flags_a_missing_pointer_and_length(self):
        self.finished_folder()
        self.write("AGENTS.md", "line\n" * 130)
        self.assert_problem("does not point to .ai/HANDOFF.md")
        self.assert_problem("over 120 lines")

    def test_flags_an_override_that_shadows_agents_md(self):
        self.finished_folder()
        self.write("AGENTS.override.md")
        self.assert_problem("move to .ai/archive/: AGENTS.override.md")

    def test_flags_a_long_memory(self):
        self.finished_folder()
        self.write(".ai/memory/MEMORY.md", "- 2026-11-05 fact (me)\n" * 51)
        self.assert_problem("MEMORY.md is over 50 entries")

    def full_adapter(self):
        self.finished_folder()
        for target in coldstart.ADAPTER.values():
            self.write(target, "{}")
        self.write(".claude/CLAUDE.md", IMPORTS)

    def test_passes_a_folder_with_a_complete_adapter(self):
        self.full_adapter()
        self.assertEqual(self.run_cli("check")[0], 0)

    def test_verifies_the_adapter_it_finds(self):
        self.full_adapter()
        self.write(".claude/CLAUDE.md", "@../AGENTS.md\n")
        (self.root / ".claude/settings.json").unlink()
        self.write("CLAUDE.md")
        self.assert_problem("missing import in .claude/CLAUDE.md: @../.ai/HANDOFF.md")
        self.assert_problem("missing: .claude/settings.json")
        self.assert_problem("move to .ai/archive/: CLAUDE.md")

    def test_finds_the_adapter_and_ignores_trailing_spaces(self):
        self.finished_folder()
        self.write(".claude/settings.json", "{}")
        self.write(".claude/CLAUDE.md", "@../AGENTS.md  \n@../.ai/HANDOFF.md\n@../.ai/memory/MEMORY.md\r\n")
        self.assertEqual(self.run_cli("check")[0], 0)
        (self.root / ".claude/settings.json").unlink()
        self.assert_problem("missing: .claude/settings.json")

    def test_a_longer_home_name_is_not_this_machine(self):
        if len(Path.home().parts) <= 2:
            self.skipTest("a home this short is ignored on purpose")
        self.finished_folder()
        self.write("AGENTS.md", FINISHED_AGENTS + f"See {Path.home().as_posix()}x/file\n")
        self.assertEqual(self.run_cli("check")[0], 0)

    def test_leaves_a_teammates_claude_files_alone(self):
        self.finished_folder()
        self.write("CLAUDE.md")
        self.write(".claude/CLAUDE.md", "their notes\n")
        self.assertEqual(self.run_cli("check")[0], 0)

    def test_reports_an_undecodable_file_without_changing_it(self):
        self.finished_folder()
        (self.root / "AGENTS.md").write_bytes(b"caf\xe9\n")
        self.assertEqual(self.run_cli("check")[0], 2)
        self.assertEqual((self.root / "AGENTS.md").read_bytes(), b"caf\xe9\n")


class Release(unittest.TestCase):
    def test_every_version_matches(self):
        repo = SCRIPT.parents[4]
        plugin = json.loads((repo / "plugin/.claude-plugin/plugin.json").read_text(encoding="utf-8"))["version"]
        skill = re.search(r'version: "(.+)"', (repo / "plugin/skills/coldstart/SKILL.md").read_text(encoding="utf-8")).group(1)
        changelog = re.search(r"^## (\S+)", (repo / "CHANGELOG.md").read_text(encoding="utf-8"), re.M).group(1)
        self.assertEqual({plugin, skill, changelog}, {plugin})


class Cli(unittest.TestCase):
    def test_rejects_a_missing_folder(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(coldstart.main(["scan", "no/such/folder"]), 2)
        self.assertIn("error", json.loads(err.getvalue()))


if __name__ == "__main__":
    unittest.main()
