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
STATE = ("HANDOFF.md", "memory", "plans", "decisions", "scratch")
REWRITTEN = ("AGENTS.md", ".ai/HANDOFF.md", ".claude/CLAUDE.md", ".claude/settings.json", ".gitignore")
SKIPPED_DIRS = {".git", "node_modules", ".venv", "__pycache__", "dist", "build"}
MAX_FILES = 300
MAX_AGENTS_LINES = 120

OLD_PATH = re.compile(r"\.agents/(?!skills\b)")
ABSOLUTE_PATH = re.compile(r"\b[A-Za-z]:[\\/]|/Users/|/home/")
MARKER = re.compile(r"<!-- coldstart (\S+) -->")
PLACEHOLDER = re.compile(r"<[A-Za-z][^<>\n]*>")
CODE = re.compile(r"```.*?```|`[^`\n]*`", re.S)


class Abort(Exception):
    """A condition that stops the command before it changes anything."""


def text(path):
    return path.read_text(encoding="utf-8", errors="replace")


def tree(root):
    """Relative file names under root, without opening any of them."""
    names = []
    for folder, subfolders, files in os.walk(root):
        subfolders[:] = sorted(set(subfolders) - SKIPPED_DIRS)
        names += [(Path(folder) / name).relative_to(root).as_posix() for name in sorted(files)]
    return names


def layout(root):
    if (root / ".agents/HANDOFF.md").exists():
        return "old"
    return "current" if (root / ".ai/HANDOFF.md").exists() else "none"


def package_scripts(root):
    try:
        return json.loads(text(root / "package.json")).get("scripts", {})
    except (OSError, ValueError, AttributeError):
        return {}


def scan(root, args):
    """Report what is in the folder. Opens only package.json and AGENTS.md, never documents."""
    manifests = [name for name in MANIFESTS if (root / name).exists()]
    is_code = bool(manifests) or (root / ".git").exists() or (root / "src").is_dir()
    marker = MARKER.search(text(root / "AGENTS.md")) if (root / "AGENTS.md").is_file() else None
    files = tree(root)
    return {
        "kind": "code" if is_code else "personal",
        "git": (root / ".git").exists(),
        "layout": layout(root),
        "version": marker.group(1) if marker else None,
        "instructions": [name for name in INSTRUCTIONS if (root / name).exists()],
        "manifests": manifests,
        "scripts": package_scripts(root),
        "files": files[:MAX_FILES],
        "truncated": len(files) > MAX_FILES,
    }


def merge_settings(path, dry_run):
    """Add the template's settings to an existing file, keeping what is already there."""
    current = json.loads(text(path))
    template = json.loads(text(ASSETS / "settings.json"))
    deny = current.setdefault("permissions", {}).setdefault("deny", [])
    deny += [rule for rule in template["permissions"]["deny"] if rule not in deny]
    current.update({key: value for key, value in template.items() if key != "permissions"})
    if not dry_run:
        path.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")


def merge_gitignore(root, dry_run):
    path = root / ".gitignore"
    present = text(path).splitlines() if path.exists() else []
    missing = [line for line in text(ASSETS / "gitignore").splitlines() if line not in present]
    if missing and not dry_run:
        path.write_text("\n".join(present + missing) + "\n", encoding="utf-8")
    return missing


def init(root, args):
    """Create .ai/memory/, and on request the Claude adapter and git. Never overwrites a file."""
    created, kept = [], []
    if not (root / ".ai/memory").is_dir():
        created.append(".ai/memory/")
        if not args.dry_run:
            (root / ".ai/memory").mkdir(parents=True)
    adapter = ADAPTER.items() if args.claude else ()
    for asset, target in adapter:
        path = root / target
        if path.exists():
            kept.append(target)
            if asset == "settings.json":
                merge_settings(path, args.dry_run)
            continue
        created.append(target)
        if not args.dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ASSETS / asset, path)
    if args.git:
        if merge_gitignore(root, args.dry_run):
            created.append(".gitignore")
        if not (root / ".git").exists():
            created.append(".git/")
            if not args.dry_run:
                subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)
    return {"created": created, "kept": kept, "dry_run": args.dry_run}


def upgrade(root, args):
    """Move the earlier layout's state from .agents/ to .ai/ and rewrite its paths."""
    old, new = root / ".agents", root / ".ai"
    if layout(root) != "old":
        raise Abort("no earlier layout here: .agents/HANDOFF.md not found")
    moved = [name for name in STATE if (old / name).exists()]
    clashes = [name for name in moved if (new / name).exists()]
    if clashes:
        raise Abort("already in .ai/: " + ", ".join(clashes))
    rewritten = [name for name in REWRITTEN if has_old_path(root / name.replace(".ai/", ".agents/"))]
    if not args.dry_run:
        new.mkdir(exist_ok=True)
        for name in moved:
            (old / name).rename(new / name)
        if not any(old.iterdir()):
            old.rmdir()
        for name in rewritten:
            (root / name).write_text(OLD_PATH.sub(".ai/", text(root / name)), encoding="utf-8")
    return {"moved": moved, "rewritten": rewritten, "dry_run": args.dry_run}


def has_old_path(path):
    return path.is_file() and bool(OLD_PATH.search(text(path)))


def check(root, args):
    """List what is missing or wrong in a finished folder."""
    problems = [f"missing: {name}" for name in REQUIRED if not (root / name).is_file()]
    problems += [f"should have moved to .ai/scratch/: {name}" for name in ("CLAUDE.md", "AGENTS.override.md")
                 if (root / name).exists()]
    if (root / ".claude").is_dir():
        problems += [f"missing: {target}" for target in ADAPTER.values() if not (root / target).is_file()]
    written = [name for name in REQUIRED + (".claude/CLAUDE.md",) if (root / name).is_file()]
    for name in written:
        content = text(root / name)
        if ABSOLUTE_PATH.search(content):
            problems.append(f"absolute path in {name}")
        if OLD_PATH.search(content):
            problems.append(f"reference to .agents/ in {name}")
        if name != ".ai/memory/MEMORY.md" and PLACEHOLDER.search(CODE.sub("", content)):
            problems.append(f"unfilled placeholder in {name}")
    if "AGENTS.md" in written:
        agents = text(root / "AGENTS.md")
        if not MARKER.search(agents):
            problems.append("no version marker in AGENTS.md")
        if len(agents.splitlines()) > MAX_AGENTS_LINES:
            problems.append(f"AGENTS.md is over {MAX_AGENTS_LINES} lines")
    return {"ok": not problems, "problems": problems}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    for command in (scan, init, upgrade, check):
        sub = commands.add_parser(command.__name__, help=command.__doc__)
        sub.add_argument("folder", nargs="?", default=".", type=Path)
        sub.set_defaults(run=command)
        if command in (init, upgrade):
            sub.add_argument("--dry-run", action="store_true", help="report without changing anything")
        if command is init:
            sub.add_argument("--claude", action="store_true", help="add the Claude Code adapter")
            sub.add_argument("--git", action="store_true", help="run git init and add .gitignore lines")
    args = parser.parse_args(argv)
    try:
        if not args.folder.is_dir():
            raise Abort(f"not a folder: {args.folder}")
        result = args.run(args.folder.resolve(), args)
    except (Abort, OSError, ValueError, subprocess.CalledProcessError) as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    sys.exit(main())
