#!/usr/bin/env python3
"""The mechanical half of the coldstart skill.

Standard library only: no network, no prompts, and it launches no other program.
Prints JSON to stdout. Exit codes: 0 done, 1 problems found, 2 could not run.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"
INSTRUCTIONS = (
    "AGENTS.md", "AGENTS.override.md", "CLAUDE.md", ".claude/CLAUDE.md", ".claude/rules", ".claude/agents",
    ".claude/settings.json", ".mcp.json", ".cursorrules", ".cursor/rules", ".cursor/mcp.json", ".clinerules",
    ".github/copilot-instructions.md", ".github/instructions", "GEMINI.md", ".agents/rules",
    ".agents/mcp_config.json", ".codex/config.toml", ".codex/hooks.json", ".cursor/hooks.json", ".vscode/mcp.json",
    ".windsurfrules",
)
ADAPTER = {
    "CLAUDE.md": ".claude/CLAUDE.md",
    "settings.json": ".claude/settings.json",
    "scout.md": ".claude/agents/scout.md",
}
ADAPTER_CORE = (".claude/CLAUDE.md", ".claude/settings.json")
REQUIRED = ("AGENTS.md", ".ai/HANDOFF.md", ".ai/memory/MEMORY.md")
IMPORTS = ("@../AGENTS.md", "@../.ai/HANDOFF.md", "@../.ai/memory/MEMORY.md")
SKIPPED_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".next", "target", ".cache"}
MAX_FILES, MAX_PER_FOLDER, MAX_AGENTS_LINES, MAX_MEMORIES = 300, 50, 120, 50
BOM = b"\xef\xbb\xbf"

PLACEHOLDER = re.compile(r"(?<!\w)<[^\W\d_][^<>=\n]* [^<>=\n]*>")
CODE = re.compile(r"```.*?```|`[^`\n]*`", re.S)


def text(path):
    return path.read_text(encoding="utf-8-sig")


def encoded(content, path):
    """Content as bytes, in the line endings and BOM the existing file uses, so a rewrite isn't a whole-file diff."""
    old = path.read_bytes() if path.is_file() else b""
    content = content.replace("\r\n", "\n")
    if b"\r\n" in old:
        content = content.replace("\n", "\r\n")
    return (BOM if old.startswith(BOM) else b"") + content.encode()


def tree(root):
    """Relative file names under root, shallow folders first, without opening any of them.

    A folder with more than MAX_PER_FOLDER files shows that many, then a "<folder>/ (+N more files)" line.
    """
    names, queue = [], [root]
    while queue and len(names) <= MAX_FILES:
        folder = queue.pop(0)
        try:
            entries = sorted(os.scandir(folder), key=lambda entry: entry.name)
        except OSError:
            continue
        files = []
        for entry in entries:
            if entry.is_dir():
                if entry.name not in SKIPPED_DIRS and not entry.is_symlink():
                    queue.append(Path(entry.path))
            else:
                files.append(Path(entry.path).relative_to(root).as_posix())
        names += files[:MAX_PER_FOLDER]
        if len(files) > MAX_PER_FOLDER:
            names.append(f"{folder.relative_to(root).as_posix()}/ (+{len(files) - MAX_PER_FOLDER} more files)")
    return names


def scan(root, args):
    """Report what is in the folder, by name only. Opens no file."""
    files = tree(root)
    return {
        "git": next((str(folder) for folder in (root, *root.parents) if (folder / ".git").exists()), None),
        "configured": all((root / name).is_file() for name in REQUIRED),
        "instructions": [name for name in INSTRUCTIONS if (root / name).exists()],
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
    """New lines go first, so a negation the user already has still wins."""
    existing = text(path) if path.exists() else ""
    missing = [line for line in text(ASSETS / "gitignore").splitlines() if line not in existing.splitlines()]
    return "\n".join(missing) + "\n" + existing if missing else None


def init(root, args):
    """Create .ai/memory/, and on request the Claude adapter and .gitignore lines.

    It only adds: it fills gaps in .claude/settings.json and .gitignore and replaces nothing else.
    Never run it in the home folder, and never write through a link that leads outside the folder.
    """
    writes, kept = {}, []
    if args.claude:
        for asset, target in ADAPTER.items():
            if not (root / target).exists():
                writes[target] = text(ASSETS / asset)
                continue
            merged = merged_settings(root / target) if asset == "settings.json" else None
            if merged is not None and merged != json.loads(text(root / target)):
                writes[target] = json.dumps(merged, indent=2, ensure_ascii=False) + "\n"
            else:
                kept.append(target)
    if args.gitignore:
        gitignore = gitignore_with_template(root / ".gitignore")
        if gitignore:
            writes[".gitignore"] = gitignore
    for name in (".ai/memory", *writes):
        if not (root / name).resolve().is_relative_to(root):
            raise ValueError(f"{name} leads outside the folder")
    created = [name for name in writes if not (root / name).exists()]
    (root / ".ai/memory").mkdir(parents=True, exist_ok=True)
    for name, content in writes.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_bytes(encoded(content, root / name))
    return {"created": created, "merged": [name for name in writes if name not in created], "kept": kept}


def check(root, args):
    """List what is missing or wrong in a finished folder."""
    problems = [f"missing: {name}" for name in REQUIRED if not (root / name).is_file()]
    written = [name for name in REQUIRED if (root / name).is_file()]
    if (root / "AGENTS.override.md").exists():
        problems.append("move to .ai/archive/: AGENTS.override.md")
    adapter = root / ".claude/CLAUDE.md"
    lines = [line.strip() for line in text(adapter).splitlines()] if adapter.is_file() else []
    if any(line in IMPORTS for line in lines):
        written.append(".claude/CLAUDE.md")
        problems += [f"missing: {target}" for target in ADAPTER_CORE if not (root / target).is_file()]
        problems += [f"missing import in .claude/CLAUDE.md: {line}" for line in IMPORTS if line not in lines]
        if (root / "CLAUDE.md").exists():
            problems.append("move to .ai/archive/: CLAUDE.md")
    local = {path.as_posix().split(":")[-1].casefold() for path in (root, Path.home()) if len(path.parts) > 2}
    machine = re.compile("|".join(re.escape(path) + r"(?![\w.-])" for path in local)) if local else None
    for name in written:
        content = text(root / name)
        if machine and machine.search(content.replace("\\", "/").casefold()):
            problems.append(f"path from this machine in {name}")
        if PLACEHOLDER.search(CODE.sub("", content)):
            problems.append(f"unfilled placeholder in {name}")
    if "AGENTS.md" in written:
        agents = text(root / "AGENTS.md")
        if ".ai/HANDOFF.md" not in agents:
            problems.append("AGENTS.md does not point to .ai/HANDOFF.md")
        if len(agents.splitlines()) > MAX_AGENTS_LINES:
            problems.append(f"AGENTS.md is over {MAX_AGENTS_LINES} lines")
    if ".ai/memory/MEMORY.md" in written:
        entries = [line for line in text(root / ".ai/memory/MEMORY.md").splitlines() if line.startswith("- ")]
        if len(entries) > MAX_MEMORIES:
            problems.append(f"MEMORY.md is over {MAX_MEMORIES} entries")
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
            sub.add_argument("--gitignore", action="store_true", help="add the template's .gitignore lines")
    args = parser.parse_args(argv)
    try:
        root = args.folder.resolve()
        if not root.is_dir():
            raise ValueError(f"not a folder: {args.folder}")
        if Path.home().resolve().is_relative_to(root):
            raise ValueError("this is or contains your home folder, not a project: pick a project folder")
        result = args.run(root, args)
    except Exception as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    sys.exit(main())
