# Changelog

## 1.4.0 - 2026-11-11

- Model routing is now one question at setup, and the default is no.
- With a yes, AGENTS.md gets a `Delegation` section: give each piece of work to the lowest model tier that gets it right, keep judgment in the main session, check what was delegated, redo a weak result one tier up, and ask a tier above when stuck.
  - Tiers are relative to the model running the session, so the text names no model, works in any agent that reads AGENTS.md, and holds when you switch models.
  - It is an instruction, not a setting: nothing is written to `.claude/settings.json` for it.
- A new eval, `routing-accepted`, covers a yes; `evals/README.md` says how to run the evals and where they can't run.
- The Claude Code adapter no longer includes the `scout` agent, and the close suggests `/advisor` only with routing. Folders set up earlier keep their `scout.md`; nothing is removed.

## 1.3.0 - 2026-11-11

- The AGENTS.md template is written for models that follow instructions literally:
  - Each rule states its own scope. The handoff's own next step no longer needs an OK, and memory is checked before anything hard to undo, not before every use.
  - Only the main session rewrites the handoff, in plain words.
  - The secrets rule no longer covers addresses.
  - The template stays the same size.
- The `advisor` subagent is gone: Claude Code's built-in `/advisor` replaces it, sees the whole conversation and is called on its own at dead ends. When it isn't on, the close suggests turning it on once per machine. Folders set up earlier can delete `.claude/agents/advisor.md`. `scout` runs at high effort and tells the main model to re-read any value a decision depends on. Both leave the folder in the next version; see `ROADMAP.md`.
- Setup no longer invents a `Done when` checklist, and old instructions shown for approval are marked keep or drop, so only kept items reach AGENTS.md.
- `scan` lists shallow folders first and caps each folder, so one big folder can't hide the rest. It also names `.cursor/hooks.json`, `.vscode/mcp.json` and `.windsurfrules`.
- The script refuses any folder that contains the home folder.
- Rewritten files keep their line endings and BOM.
- `check` finds the adapter by its imports, tolerates trailing spaces and no longer mistakes a longer home name for this machine's.
- A new eval, `resume-from-handoff`, tests the next session.

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
