#!/usr/bin/env python3
"""The mechanical half of the coldstart skill.

Standard library only: no network, no prompts. Prints JSON to stdout.
Exit codes: 0 done, 1 problems found, 2 could not run.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"
MANIFESTS = ("package.json", "pyproject.toml", "go.mod", "Cargo.toml")
INSTRUCTIONS = (
    "AGENTS.md", "AGENTS.override.md", "CLAUDE.md", ".claude/CLAUDE.md", ".cursorrules",
    ".cursor/rules", ".clinerules", ".github/copilot-instructions.md", "GEMINI.md",
)
ADAPTER = {
    "CLAUDE.md": ".claude/CLAUDE.md",
    "settings.json": ".claude/settings.json",
    "scout.md": ".claude/agents/scout.md",
    "advisor.md": ".claude/agents/advisor.md",
}
REQUIRED = ("AGENTS.md", ".ai/HANDOFF.md", ".ai/memory/MEMORY.md")
MOVED_OUT = ("CLAUDE.md", "AGENTS.override.md")
IMPORTS = ("@../AGENTS.md", "@../.ai/HANDOFF.md", "@../.ai/memory/MEMORY.md")
SKIPPED_DIRS = {".git", "node_modules", ".venv", "__pycache__", "dist", "build"}
MAX_FILES, MAX_AGENTS_LINES, MAX_MEMORIES = 300, 120, 50

URL = re.compile(r"https?://\S+")
ABSOLUTE_PATH = re.compile(r"\b[A-Za-z]:[\\/]|(?<![\w.])/(?:Users|home)/")
MARKER = re.compile(r"<!-- coldstart \S+ -->")
PLACEHOLDER = re.compile(r"(?<!\w)<[A-Za-z][^<>=\n]* [^<>=\n]*>")
CODE = re.compile(r"```.*?```|`[^`\n]*`", re.S)


class Abort(Exception):
    """A condition that stops the command before it changes anything."""


def text(path):
    return path.read_text(encoding="utf-8-sig")


def tree(root):
    """Relative file names under root, without opening any of them."""
    names = []
    for folder, subfolders, files in os.walk(root):
        subfolders[:] = sorted(set(subfolders) - SKIPPED_DIRS)
        for name in sorted(files):
            names.append((Path(folder) / name).relative_to(root).as_posix())
            if len(names) > MAX_FILES:
                return names
    return names


def package_scripts(root):
    try:
        return json.loads(text(root / "package.json")).get("scripts", {})
    except (OSError, ValueError, AttributeError):
        return {}


def scan(root, args):
    """Report what is in the folder. Opens only package.json, never documents."""
    manifests = [name for name in MANIFESTS if (root / name).exists()]
    files = tree(root)
    return {
        "kind": "code" if manifests or (root / ".git").exists() or (root / "src").is_dir() else "personal",
        "git": (root / ".git").exists(),
        "configured": (root / ".ai/HANDOFF.md").exists(),
        "instructions": [name for name in INSTRUCTIONS if (root / name).exists()],
        "manifests": manifests,
        "scripts": package_scripts(root),
        "files": files[:MAX_FILES],
        "truncated": len(files) > MAX_FILES,
    }


def merged_settings(path):
    """The existing settings plus what the template adds. The user's values win."""
    settings = json.loads(text(path))
    template = json.loads(text(ASSETS / "settings.json"))
    deny = settings.setdefault("permissions", {}).setdefault("deny", [])
    deny += [rule for rule in template["permissions"]["deny"] if rule not in deny]
    for key, value in template.items():
        settings.setdefault(key, value)
    return settings


def gitignore_with_template(path):
    existing = text(path) if path.exists() else ""
    missing = [line for line in text(ASSETS / "gitignore").splitlines() if line not in existing.splitlines()]
    if not missing:
        return None
    return existing + ("\n" if existing and not existing.endswith("\n") else "") + "\n".join(missing) + "\n"


def init(root, args):
    """Create .ai/memory/, and on request the Claude adapter and git. Never overwrites a file."""
    if args.git and not shutil.which("git"):
        raise Abort("git is not installed: run again without --git")
    writes, kept = {}, []
    if args.claude:
        for asset, target in ADAPTER.items():
            if not (root / target).exists():
                writes[target] = text(ASSETS / asset)
            elif asset == "settings.json" and json.loads(text(root / target)) != merged_settings(root / target):
                writes[target] = json.dumps(merged_settings(root / target), indent=2) + "\n"
            else:
                kept.append(target)
    if args.git:
        gitignore = gitignore_with_template(root / ".gitignore")
        if gitignore:
            writes[".gitignore"] = gitignore
    created = [name for name in writes if not (root / name).exists()]
    if not args.dry_run:
        (root / ".ai/memory").mkdir(parents=True, exist_ok=True)
        for name, content in writes.items():
            (root / name).parent.mkdir(parents=True, exist_ok=True)
            (root / name).write_text(content, encoding="utf-8", newline="\n")
        if args.git and not (root / ".git").exists():
            subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)
    return {"created": created, "merged": [n for n in writes if n not in created], "kept": kept, "dry_run": args.dry_run}


def check(root, args):
    """List what is missing or wrong in a finished folder."""
    problems = [f"missing: {name}" for name in REQUIRED if not (root / name).is_file()]
    problems += [f"move to .ai/archive/: {name}" for name in MOVED_OUT if (root / name).exists()]
    written = [name for name in REQUIRED if (root / name).is_file()]
    if (root / ".claude/CLAUDE.md").is_file():
        written.append(".claude/CLAUDE.md")
        lines = text(root / ".claude/CLAUDE.md").splitlines()
        problems += [f"missing import in .claude/CLAUDE.md: {line}" for line in IMPORTS if line not in lines]
        if not (root / ".claude/settings.json").is_file():
            problems.append("missing: .claude/settings.json")
    for name in written:
        content = text(root / name)
        if ABSOLUTE_PATH.search(URL.sub("", content)):
            problems.append(f"absolute path in {name}")
        if PLACEHOLDER.search(CODE.sub("", content)):
            problems.append(f"unfilled placeholder in {name}")
    if "AGENTS.md" in written:
        agents = text(root / "AGENTS.md")
        if not MARKER.search(agents):
            problems.append("no version marker in AGENTS.md")
        if len(agents.splitlines()) > MAX_AGENTS_LINES:
            problems.append(f"AGENTS.md is over {MAX_AGENTS_LINES} lines")
    if ".ai/memory/MEMORY.md" in written:
        entries = [line for line in text(root / ".ai/memory/MEMORY.md").splitlines() if line.startswith("- [")]
        if len(entries) > MAX_MEMORIES:
            problems.append(f"memory index is over {MAX_MEMORIES} entries")
    return {"ok": not problems, "problems": problems}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    for command in (scan, init, check):
        sub = commands.add_parser(command.__name__, help=command.__doc__)
        sub.add_argument("folder", nargs="?", default=".", type=Path)
        sub.set_defaults(run=command)
        if command is init:
            sub.add_argument("--claude", action="store_true", help="add the Claude Code adapter")
            sub.add_argument("--git", action="store_true", help="run git init and add .gitignore lines")
            sub.add_argument("--dry-run", action="store_true", help="report without changing anything")
    args = parser.parse_args(argv)
    try:
        if not args.folder.is_dir():
            raise Abort(f"not a folder: {args.folder}")
        result = args.run(args.folder.resolve(), args)
    except (Abort, OSError, ValueError, AttributeError, subprocess.CalledProcessError) as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    sys.exit(main())
