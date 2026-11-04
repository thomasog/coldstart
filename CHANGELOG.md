# Changelog

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
