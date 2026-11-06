# Changelog

## 1.2.0 - 2026-11-05

- `scan` works by name only and opens no file; it reports the enclosing git repository and active config such as `.mcp.json`, hooks and `.agents/rules`.
- The script launches no other program: `--git` becomes `--gitignore`, and the agent runs `git init`.
- Runs on Python 3.9, refuses the home folder and links that lead outside the folder, and returns a clean error on malformed settings.
- `check` compares against this machine's real paths, verifies the adapter only where it exists, and no longer needs a version marker.
- The template loses `## Models`, `## Map` and the marker, and gains a rule against storing secrets. Memory facts are single lines in `MEMORY.md`.
- `scout` is the default for images and has no network tools. `advisor` runs on `best`, the strongest model available, which can bill usage credits.
- Evals move to one `case.yaml` per case, with mechanical graders and two new cases.
- Folders already set up keep their files: `init` never overwrites them.

## 1.1.0 - 2026-11-04

- Stops at a check in a folder that is already set up, so the live handoff can't be overwritten.
- Keeps the user's settings when merging, and stops before writing if git is missing or a file can't be read safely.
- Removes false alarms from `check`, which now also verifies the Claude imports.
- Moves old instructions to `.ai/archive/`, and gives agent-made tools a place in `.ai/tools/`.
- Tells agents to read the handoff before their first action.
- Ships only the skill in the Claude Code plugin, from `plugin/`.
- Removes the `upgrade` command.

## 1.0.1 - 2026-11-04

- Tells agents to look for the real Python on Windows when the usual commands are shortcuts that fail.

## 1.0.0 - 2026-11-04

First public version.

- Sets up `AGENTS.md`, `.ai/HANDOFF.md` and `.ai/memory/`, plus a Claude Code adapter when used.
- Adds `coldstart.py` with `scan`, `init` and `check`.
